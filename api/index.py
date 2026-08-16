from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
from mangum import Mangum

app = FastAPI()

# CORS configuration taake frontend theek tarah connect ho sakay
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIRequest(BaseModel):
    url: str

@app.post("/extract")
def extract_media(data: AIRequest):
    if not data.url or not data.url.strip():
        raise HTTPException(status_code=400, detail="Media URL is required!")
    
    try:
        # yt-dlp options (download=False taake server par file save na ho)
        ydl_opts = {
            'format': 'best',
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=False)
            
            title = info.get('title', 'Unknown Title')
            formats = info.get('formats', [])
            
            format_list = []
            for f in formats:
                if f.get('url'):
                    format_list.append({
                        "format_id": f.get('format_id'),
                        "ext": f.get('ext'),
                        "resolution": f.get('resolution') or f.get('format_note', 'HD'),
                        "url": f.get('url')
                    })
            
            return {
                "status": "success",
                "data": {
                    "title": title,
                    "type": "downloader",
                    "formats": format_list
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction Error: {str(e)}")
handler = Mangum(app)
