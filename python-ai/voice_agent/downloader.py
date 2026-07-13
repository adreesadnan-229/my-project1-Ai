import os
import re

import requests
import yt_dlp

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

URL_PATTERN = re.compile(r"https?://\S+")


def extract_url(text):
    match = URL_PATTERN.search(text or "")
    return match.group(0) if match else None


def download_from_youtube(query):
    """Searches YouTube for `query` and downloads the top result (best
    pre-combined video+audio format, no ffmpeg needed) into Downloads.
    Returns the saved file path, or None on failure."""
    outtmpl = os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if "entries" in info:
                info = info["entries"][0]
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"YouTube download error: {e}")
        return None


def download_from_url(url):
    """Streams a direct file URL into Downloads. Returns the saved file path,
    or None on failure."""
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()

        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
        dest = os.path.join(DOWNLOADS_DIR, filename)

        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return dest
    except Exception as e:
        print(f"URL download error: {e}")
        return None
