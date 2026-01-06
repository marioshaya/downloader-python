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
    """List all available formats for a video"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with console.status("[bold green]Fetching video information...", spinner="dots"):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        
        # Display video info
        console.print(Panel(
            f"[bold white]{info['title']}[/bold white]\n"
            f"[cyan]Duration:[/cyan] {info['duration']}s | "
            f"[cyan]Uploader:[/cyan] {info.get('uploader', 'N/A')}",
            title="[bold magenta]Video Information[/bold magenta]",
            border_style="magenta"
        ))
        
        # Create formats table
        table = Table(show_header=True, header_style="bold cyan", title="\n[bold]Available Formats[/bold]")
        table.add_column("ID", style="yellow", width=8)
        table.add_column("Ext", style="green", width=8)
        table.add_column("Resolution", style="cyan", width=15)
        table.add_column("FPS", style="blue", width=6)
        table.add_column("Size", style="magenta", width=12)
        table.add_column("Type", style="white", width=20)
        
        # Separate video and audio formats
        video_formats = []
        audio_formats = []
        combined_formats = []
        
        for f in info['formats']:
            has_video = f.get('vcodec') != 'none'
            has_audio = f.get('acodec') != 'none'
            
            if has_video and has_audio:
                combined_formats.append(f)
            elif has_video:
                video_formats.append(f)
            elif has_audio:
                audio_formats.append(f)
        
        # Add combined formats
        if combined_formats:
            table.add_row("[bold]--- Combined (Video + Audio) ---[/bold]", "", "", "", "", "", style="bold green")
            for f in combined_formats[:10]:  # Limit to avoid clutter
                add_format_row(table, f)
        
        # Add video-only formats
        if video_formats:
            table.add_row("[bold]--- Video Only ---[/bold]", "", "", "", "", "", style="bold blue")
            for f in video_formats[:10]:
                add_format_row(table, f)
        
        # Add audio-only formats
        if audio_formats:
            table.add_row("[bold]--- Audio Only ---[/bold]", "", "", "", "", "", style="bold magenta")
            for f in audio_formats[:10]:
                add_format_row(table, f)
        
        console.print(table)
        
        return info['formats'], info['title']
    
    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        return None, None

def add_format_row(table, f):
    """Add a format row to the table"""
    format_id = f.get('format_id', 'N/A')
    ext = f.get('ext', 'N/A')
    resolution = f.get('resolution', 'audio only' if f.get('vcodec') == 'none' else 'N/A')
    fps = str(f.get('fps', '-'))
    filesize = f.get('filesize') or f.get('filesize_approx')
    size = f"{filesize / (1024*1024):.1f} MB" if filesize else "Unknown"
    note = f.get('format_note', '')
    
    table.add_row(format_id, ext, resolution, fps, size, note)

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
    