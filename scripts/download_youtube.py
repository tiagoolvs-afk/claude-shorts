#!/usr/bin/env python3
"""Download a single YouTube video for local processing by claude-shorts.

Use only for videos you own, have permission to download, or that are otherwise
available for downloading under applicable terms and law. This script intentionally
rejects playlists and does not accept cookies or bypass access controls.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtube-nocookie.com",
    "youtube-nocookie.com",
}


def validate_url(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in ALLOWED_HOSTS:
        raise ValueError("Please provide a valid youtube.com or youtu.be URL.")
    if parsed.path.rstrip("/") in {"", "/"} and host not in {"youtu.be"}:
        raise ValueError("The URL does not appear to point to a video.")
    if "list" in dict(__import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(parsed.query)):
        raise ValueError("Playlist URLs are not supported. Provide a single video URL.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Download one YouTube video for claude-shorts.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output-dir", default="source-videos", help="Folder to save the source video (default: ./source-videos)")
    args = parser.parse_args()

    try:
        url = validate_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    try:
        import yt_dlp
    except ImportError:
        print("ERROR: yt-dlp is not installed. Run setup.sh or install it in the claude-shorts virtual environment.", file=sys.stderr)
        return 3

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    template = str(output_dir / "%(title).120B [%(id)s].%(ext)s")
    options = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "nooverwrites": True,
        "continuedl": True,
        "retries": 3,
        "quiet": False,
        "noprogress": False,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = Path(ydl.prepare_filename(info))
            if filename.suffix.lower() not in {".mp4", ".mkv", ".webm"}:
                mp4_candidate = filename.with_suffix(".mp4")
                if mp4_candidate.exists():
                    filename = mp4_candidate
            if not filename.exists():
                candidates = sorted(output_dir.glob(f"*[{info.get('id', '')}]*"))
                if candidates:
                    filename = candidates[0]
                else:
                    raise FileNotFoundError("Download finished but the output file could not be located.")
            print("\nDOWNLOAD_COMPLETE")
            print(f"TITLE: {info.get('title', 'Unknown title')}")
            print(f"FILE: {filename}")
            print(f"DURATION_SECONDS: {info.get('duration', 'unknown')}")
            return 0
    except Exception as exc:
        print(f"ERROR: Download failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
