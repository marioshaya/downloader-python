## YouTube Downloader (Interactive CLI)

Small interactive CLI for downloading YouTube videos using `yt-dlp`. Prompts guide you through choosing the URL, picking the format (best, bestvideo+bestaudio, audio-only, or specific formats), and selecting the output directory.

### Features
- Lists available formats with human-readable labels (resolution, fps, size, notes).
- Quick presets: best, bestvideo+bestaudio, or bestaudio.
- Interactive folder picker with common defaults and custom path support (creates the folder if needed).
- Rich, styled prompts for a clearer flow.

### Requirements
- Python 3.8+.
- `ffmpeg` on your `PATH` (needed for merging video+audio).

### Setup
```bash
cd /home/qamardo/Projects/downloader
python -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
pip install --upgrade pip
pip install -e .
# or: pip install -r requirements.txt   # once populated
```

### Usage
With the virtualenv active:
```bash
dwn                      # entry point installed via setup.py
# or
python downloader.py     # optionally pass a URL: python downloader.py "<url>"
```

Flow:
1) Enter/paste a YouTube URL (or provide it as the first CLI argument).  
2) Choose a format from the interactive list or use a quick preset.  
3) Pick a download location: Music, Tantara, current directory, or a custom path (will prompt to create if missing).  
4) Download starts and files are written as `%(title)s.%(ext)s` in the chosen directory.

### Updating dependencies
After adding/upgrading packages in your venv:
```bash
pip freeze > requirements.txt
```

### Troubleshooting
- If merging fails, ensure `ffmpeg` is installed and on `PATH`.
- If the format list is empty, check the URL or network access.
- If `pip` is missing inside the venv, run `python -m ensurepip --upgrade` then `pip install --upgrade pip`.
