import feedparser
import google.generativeai as genai
import requests
import os
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

def get_news():
    url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
    feed = feedparser.parse(url)
    return feed.entries[0].title, feed.entries[0].description

def ask_gemini(title, desc):
    try:
        genai.configure(api_key=GEMINI_KEY)
        # Sử dụng gemini-1.5-flash-latest là bản ổn định nhất hiện tại
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"Dựa trên tin: {title}. Viết 1 câu kịch bản ngắn dưới 20 từ và 1 từ khóa tiếng Anh. Trả về: Kịch bản | Từ khóa"
        response = model.generate_content(prompt)
        return response.text.replace("*", "").split("|")
    except:
        return ["Chào mừng bạn đến với bản tin hôm nay", "news"]

def create_voice(text):
    subprocess.run(f'edge-tts --voice vi-VN-HoaiMyNeural --text "{text}" --write-media voice.mp3', shell=True)

def download_video(keyword):
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait"
    r = requests.get(url, headers=headers).json()
    video_url = r['videos'][0]['video_files'][0]['link']
    with open("bg.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

def make_final_video():
    video = VideoFileClip("bg.mp4")
    audio = AudioFileClip("voice.mp3")
    final = video.set_audio(audio).set_duration(audio.duration)
    final.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)

try:
    print("--- Bat dau lam lai tu dau ---")
    title, desc = get_news()
    res = ask_gemini(title, desc)
    create_voice(res[0].strip())
    download_video(res[1].strip() if len(res)>1 else "nature")
    make_final_video()
    print("THANH CONG!")
except Exception as e:
print(f"Loi: {e}")
