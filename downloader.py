import os
import sys
import yt_dlp
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

# Default download directories
DEFAULT_DIRS = {
    '1': ('~/Music', 'Music folder'),
    '2': ('/mnt/Data/Tantara/', 'Tantara folder'),
    '3': ('.', 'Current directory'),
    '4': ('custom', 'Custom path')
}

def get_output_directory():
    """Let user choose output directory"""
    console.print("\n[bold cyan]Choose output directory:[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Directory", style="green")
    table.add_column("Description", style="yellow")
    
    for key, (path, desc) in DEFAULT_DIRS.items():
        display_path = path if path != 'custom' else '(Enter custom path)'
        # Check if directory exists
        if path not in ['.', 'custom']:
            expanded = os.path.expanduser(path)
            exists = os.path.exists(expanded)
            status = "✓" if exists else "✗"
            table.add_row(key, f"{status} {display_path}", desc)
        else:
            table.add_row(key, display_path, desc)
    
    console.print(table)
    
    choice = Prompt.ask("\n[bold]Select option[/bold]", choices=list(DEFAULT_DIRS.keys()), default="1")
    
    selected_path, _ = DEFAULT_DIRS[choice]
    
    if selected_path == 'custom':
        custom_path = Prompt.ask("[bold]Enter custom directory path[/bold]")
        selected_path = custom_path
    
    # Expand and create directory if needed
    output_dir = os.path.expanduser(selected_path)
    
    if not os.path.exists(output_dir):
        if Confirm.ask(f"[yellow]Directory doesn't exist. Create it?[/yellow]"):
            try:
                os.makedirs(output_dir, exist_ok=True)
                console.print(f"[green]✓ Created directory: {output_dir}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Error creating directory: {e}[/red]")
                return None
        else:
            console.print("[red]Download cancelled.[/red]")
            return None
    
    return output_dir

def list_formats(url):
    """List all available formats for a given YouTube URL."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            print(f"\nTitle: {info['title']}")
            print(f"Duration: {info['duration']}s")
            print("\nAvailable formats:")
            print("-" * 80)
            print(f"{'ID':<8} {'Extension':<12} {'Resolution':<12} {'FPS':<8} {'Size':<15} {'Note'}")
            print("-" * 80)

            for f in info['formats']:
                format_id = f.get('format_id', 'N/A')
                ext = f.get('ext', 'N/A')
                resolution = f.get('resolution', 'audio only' if f.get('vcodec') == 'none' else 'N/A')
                fps = f.get('fps', 'N/A')
                filesize = f.get('filesize') or f.get('filesize_approx')
                size = f"{filesize / (1024*1024):.1f} MB" if filesize else "Unknown"
                note = f.get('format_note', '')
                
                print(f"{format_id:<8} {ext:<12} {resolution:<12} {str(fps):<8} {size:<15} {note}")
            
            return info['formats']

    except Exception as e:
        print(f"Error: {e}")
        return None


def download_video(url, format_id=None):
    """Download video with specified format"""
    ydl_opts = {
        'format': format_id if format_id else 'best',
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nDownloading...")
            ydl.download([url])
            print("\nDownload complete!")
    
    except Exception as e:
        print(f"Error downloading: {e}")

def progress_hook(d):
    """Display download progress"""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        print(f"\rProgress: {percent} | Speed: {speed} | ETA: {eta}", end='')
    elif d['status'] == 'finished':
        print("\nProcessing...")

def main():
    print("=" * 80)
    print("YouTube Video Downloader")
    print("=" * 80)
    
    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter YouTube URL: ").strip()
    
    if not url:
        print("No URL provided!")
        return
    
    # List formats
    formats = list_formats(url)
    if not formats:
        return
    
    # Get user choice
    print("\n" + "=" * 80)
    print("Options:")
    print("  - Enter format ID to download specific format")
    print("  - Press Enter for best quality")
    print("  - Type 'q' to quit")
    print("=" * 80)
    
    choice = input("\nYour choice: ").strip()
    
    if choice.lower() == 'q':
        print("Cancelled.")
        return
    
    # Download
    if choice:
        download_video(url, choice)
    else:
        download_video(url)

if __name__ == "__main__":
    main()
    