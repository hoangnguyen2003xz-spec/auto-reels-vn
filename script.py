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
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Dựa trên tin: {title}. 
    Viết kịch bản tin tức khoảng 120 chữ. 
    Chia kịch bản thành 4 phần. Với mỗi phần, hãy cho 1 từ khóa tiếng Anh miêu tả hình ảnh.
    Trả về định dạng: 
    Kịch bản 1 | Từ khóa 1
    Kịch bản 2 | Từ khóa 2
    Kịch bản 3 | Từ khóa 3
    Kịch bản 4 | Từ khóa 4
    """
    response = model.generate_content(prompt)
    return [line for line in response.text.strip().split('\n') if "|" in line]

def create_voice(full_text):
    subprocess.run(f'edge-tts --voice vi-VN-HoaiMyNeural --text "{full_text}" --write-media voice.mp3', shell=True)

def download_video(keyword, filename):
    headers = {"Authorization": PEXELS_KEY}
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait"
    r = requests.get(url, headers=headers).json()
    if r.get('videos'):
        video_url = r['videos'][0]['video_files'][0]['link']
        with open(filename, 'wb') as f:
            f.write(requests.get(video_url).content)
        return True
    return False

def make_multi_clip_video(segments):
    audio = AudioFileClip("voice.mp3")
    duration_per_clip = audio.duration / len(segments)
    clips = []
    
    for i in range(len(segments)):
        fname = f"part_{i}.mp4"
        if os.path.exists(fname):
            clip = VideoFileClip(fname)
            # Nếu clip ngắn hơn thời gian cần thiết, lặp lại clip
            if clip.duration < duration_per_clip:
                clip = clip.fx(vfx.loop, duration=duration_per_clip)
            else:
                clip = clip.subclip(0, duration_per_clip)
            clip = clip.resize(height=1920) # Chuẩn dọc TikTok
            clips.append(clip)
    
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio)
    final_video.write_videofile("final_video.mp4", fps=24, codec="libx264")

try:
    print("--- Bat dau quy trinh ghep nhieu canh ---")
    title, desc = get_news()
    segments = ask_gemini(title, desc)
    
    full_script = ""
    for i, seg in enumerate(segments):
        parts = seg.split("|")
        script_part = parts[0].strip()
        keyword_part = parts[1].strip()
        full_script += script_part + " "
        print(f"Dang tai canh {i+1} cho: {keyword_part}")
        download_video(keyword_part, f"part_{i}.mp4")
    
    create_voice(full_script)
    make_multi_clip_video(segments)
    print("THANH CONG!")
except Exception as e:
    print(f"Loi: {e}")
