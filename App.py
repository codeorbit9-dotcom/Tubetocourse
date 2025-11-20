# main.py — ONLY TRANSCRIPT EXTRACTION (yt-dlp only, no LLM)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import yt_dlp
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TubeToCourse Transcript Only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: HttpUrl

@app.post("/transcript")
async def get_transcript(request: URLRequest):
    url = str(request.url)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', '.en', 'en-US'],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            transcripts = []

            # PLAYLIST SUPPORT
            if info.get('entries'):
                for i, entry in enumerate(info['entries']):
                    if not entry: continue
                    trans = extract_single(entry)
                    if trans:
                        transcripts.append(f"[Video {i+1}: {entry.get('title', 'No title')}]\n{trans.strip()}")
                final = "\n\n".join(transcripts)
            else:
                final = extract_single(info)

            if not final or len(final) < 50:
                return {"transcript": "", "error": "No English transcript found."}

            return {"transcript": final[:500000], "length": len(final)}  # limit 500k chars

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_single(info):
    # Auto captions first
    if info.get('automatic_captions'):
        for lang in ['en', 'en-US', 'en-GB']:
            caps = info['automatic_captions'].get(lang)
            if caps and isinstance(caps, list):
                return " ".join([c.get('text', '') for c in caps if c.get('text')])
    
    # Manual subtitles
    if info.get('subtitles'):
        for lang in ['en', 'en-US']:
            subs = info['subtitles'].get(lang)
            if subs and isinstance(subs, list):
                return " ".join([c.get('text', '') for c in subs if c.get('text')])
    return ""
