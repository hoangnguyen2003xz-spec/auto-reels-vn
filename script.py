import feedparser
import google.generativeai as genai
import requests
import os
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, vfx

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

def get_news():
    url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
    feed = feedparser.parse(url)
    return feed.entries[0].title, feed.entries[0].description

def ask_gemini(title, desc):
    try:
        genai.configure(api_key=GEMINI_KEY)
        # SỬA Ở ĐÂY: Dùng model flash cơ bản để tránh lỗi 404
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Tin: {title}. Viết kịch bản 100 chữ, chia 4 đoạn. Mỗi đoạn kèm 1 từ khóa tiếng Anh. Trả về: Kịch bản | Từ khóa"
        response = model.generate_content(prompt)
        return [line for line in response.text.strip().split('\n') if "|" in line]
    except:
        return ["Chào mừng bạn đến với bản tin hôm nay | news", "Cập nhật tin tức mới nhất | city"]

def download_video(keyword, filename):
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait"
    r = requests.get(url, headers=headers).json()
    if r.get('videos'):
        video_url = r['videos'][0]['video_files'][0]['link']
        with open(filename, 'wb') as f: f.write(requests.get(video_url).content)
        return True
    return False

try:
    print("--- Bat dau quy trinh ghep nhieu canh ---")
    title, desc = get_news()
    segments = ask_gemini(title, desc)
    
    full_script = ""
    clips = []
    
    # Bước này sẽ tải từng clip một
    for i, seg in enumerate(segments[:4]): # Lấy tối đa 4 cảnh
        parts = seg.split("|")
        full_script += parts[0].strip() + " "
        print(f"Dang tai canh {i+1}...")
        download_video(parts[1].strip(), f"p{i}.mp4")

    # Tạo giọng nói
    subprocess.run(f'edge-tts --voice vi-VN-HoaiMyNeural --text "{full_script}" --write-media voice.mp3', shell=True)
    audio = AudioFileClip("voice.mp3")
    dur = audio.duration / len(segments)

    # Ghép các clip lại
    for i in range(len(segments)):
        if os.path.exists(f"p{i}.mp4"):
            c = VideoFileClip(f"p{i}.mp4").resize(height=1920).set_duration(dur)
            clips.append(c)
    
    final = concatenate_videoclips(clips).set_audio(audio)
    final.write_videofile("final_video.mp4", fps=24, codec="libx264")
    print("THANH CONG!")
except Exception as e:
    print(f"Loi: {e}")
