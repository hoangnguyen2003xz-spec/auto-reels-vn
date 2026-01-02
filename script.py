import feedparser
import google.generativeai as genai
import requests
import os
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip

# Lấy mã từ GitHub Secrets
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

def get_news():
    url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
    feed = feedparser.parse(url)
    return feed.entries[0].title, feed.entries[0].description

def ask_gemini(title, desc):
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Dựa trên tin: {title}. Hãy viết 1 câu kịch bản ngắn dưới 20 từ và 1 từ khóa tiếng Anh về chủ đề này. Trả về đúng dạng: Kịch bản | Từ khóa (Không thêm ký tự khác)"
    response = model.generate_content(prompt)
    content = response.text.replace("*", "") # Xóa bỏ các dấu sao nếu có
    return content.split("|")

def create_voice(text):
    # Tạo giọng đọc Hoài Mỹ
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
    # Đảm bảo video dài bằng đúng đoạn âm thanh
    final = video.set_audio(audio).set_duration(audio.duration)
    # Xuất file với tên chính xác để GitHub tìm thấy
    final.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)

try:
    print("--- Bat dau quy trinh ---")
    title, desc = get_news()
    res = ask_gemini(title, desc)
    
    # Đảm bảo res có ít nhất 2 phần tử
    script = res[0].strip() if len(res) > 0 else "Tin nóng trong ngày"
    keyword = res[1].strip() if len(res) > 1 else "news"
    
    print(f"Kịch bản: {script} | Từ khóa: {keyword}")
    
    create_voice(script)
    download_video(keyword)
    make_final_video()
    
    if os.path.exists("final_video.mp4"):
        print("THANH CONG: Da tao xong file final_video.mp4")
    else:
        print("LOI: Khong tim thay file sau khi ghep")
except Exception as e:
    print(f"Loi roi: {e}")
