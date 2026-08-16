import asyncio
import os
import re
import urllib.parse
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="QUANTUM AI Engine")

# Full CORS permission to avoid network/fetch blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class AIRequest(BaseModel):
    url: str
    tool_type: str = "auto"

def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>QUANTUM AI: index.html file not found in root directory!</h1>"

@app.get("/download")
async def download_media(url: str, is_audio: bool = False, background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        file_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(DOWNLOAD_DIR, f"quantum_{file_id}.%(ext)s")
        
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best' if not is_audio else 'bestaudio/best',
            'extractor_args': {
                'youtube': {'player_client': ['android', 'ios']},
                'tiktok': {'app_name': 'trill'}
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            }
        }

        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await asyncio.to_thread(run_dl)

        if not os.path.exists(filename):
            matching_files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if file_id in f]
            if matching_files:
                filename = matching_files[0]
            else:
                raise HTTPException(status_code=500, detail="Downloaded media file not found on server.")

        background_tasks.add_task(cleanup_file, filename)
        return FileResponse(
            path=filename,
            filename=os.path.basename(filename),
            media_type='application/octet-stream'
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download Core Error: {str(e)}")

def generate_ai_metadata(title: str, description: str = ""):
    words = [w for w in re.sub(r'[^\w\s]', '', title).split() if len(w) > 3]
    main_keywords = words[:5] if words else ["viral", "trending", "video"]
    
    tags = [f"#{kw.lower()}" for kw in main_keywords] + ["#viral", "#trending", "#fyp", "#shorts", "#reels"]
    viral_caption = f"🔥 MUST WATCH: {title}!\n\nTag someone who needs to see this! 👇\n\n" + " ".join(tags)
    
    summary = [
        f"🎯 Core Subject: Video covers key details regarding '{title}'.",
        f"⚡ High Engagement: Structure optimized for short-form retention.",
        f"💡 Key Takeaway: Essential content intelligence extracted for creators."
    ]
    
    prompt = f"Cyberpunk 8k unreal engine render of {title}, hyper-realistic dramatic lighting, vibrant neon colors, cinematic composition --ar 16:9 --v 6.0"

    return {
        "captions": viral_caption,
        "tags": " ".join(tags),
        "summary": summary,
        "prompt": prompt
    }

def process_quantum_media(url: str, tool_type: str):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extractor_args': {
            'youtube': {'player_client': ['android', 'ios']},
            'tiktok': {'app_name': 'trill'}
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'QUANTUM AI Extracted Stream')
        description = info.get('description', '')

        ai_data = generate_ai_metadata(title, description)

        if tool_type == "ai_summary":
            return {"title": title, "type": "ai_summary", "data": ai_data["summary"]}
        
        if tool_type == "ai_captions":
            return {"title": title, "type": "ai_captions", "caption": ai_data["captions"], "tags": ai_data["tags"]}
        
        if tool_type == "ai_prompt":
            return {"title": title, "type": "ai_prompt", "prompt": ai_data["prompt"]}

        encoded_url = urllib.parse.quote(url, safe='')
        video_download_link = f"/download?url={encoded_url}&is_audio=false"
        audio_download_link = f"/download?url={encoded_url}&is_audio=true"

        if tool_type == "mp3":
            format_list = [{"label": "🎵 High-Bitrate Master Audio (.mp3)", "url": audio_download_link, "badge": "HQ AUDIO"}]
        else:
            format_list = [
                {"label": "⚡ Full HD Video PureStream (.mp4)", "url": video_download_link, "badge": "PURE MP4"},
                {"label": "🎧 Extracted Audio Track (.mp3)", "url": audio_download_link, "badge": "AUDIO"}
            ]

        return {
            "title": title,
            "type": "downloader",
            "formats": format_list
        }

@app.post("/extract")
async def get_quantum_data(data: AIRequest):
    if not data.url.strip():
        raise HTTPException(status_code=400, detail="Media URL is required!")
    try:
        result = await asyncio.to_thread(process_quantum_media, data.url, data.tool_type)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantum Engine Error: {str(e)}")
    from mangum import Mangum
handler = Mangum(app)