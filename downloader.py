import yt_dlp
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import questionary
from questionary import Style

console = Console()

# Custom style for questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#00ff00 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#00ff00'),
    ('separator', 'fg:#cc5454'),
    ('instruction', 'fg:#858585'),
])

# Default download directories
DEFAULT_DIRS = [
    {'name': '🎵 Music', 'path': '~/Music'},
    {'name': '💾 Tantara', 'path': '/mnt/Data/Tantara/'},
    {'name': '📁 Current directory', 'path': '.'},
    {'name': '✏️  Custom path...', 'path': 'custom'},
]

def get_output_directory():
    """Let user choose output directory"""
    console.print("\n[bold cyan]Choose output directory:[/bold cyan]\n")
    
    # Create choices with status indicators
    choices = []
    for dir_info in DEFAULT_DIRS:
        path = dir_info['path']
        name = dir_info['name']
        
        if path not in ['.', 'custom']:
            expanded = os.path.expanduser(path)
            exists = os.path.exists(expanded)
            status = "✓" if exists else "✗"
            display = f"{status} {name} [{path}]"
        else:
            display = name
        
        choices.append(questionary.Choice(title=display, value=path))
    
    selected_path = questionary.select(
        "Use arrow keys to navigate, Enter to select:",
        choices=choices,
        style=custom_style,
        use_indicator=True,
        use_shortcuts=True
    ).ask()
    
    if selected_path is None:  # User pressed Ctrl+C
        return None
    
    if selected_path == 'custom':
        custom_path = questionary.text(
            "Enter custom directory path:",
            style=custom_style
        ).ask()
        
        if not custom_path:
            console.print("[red]No path provided![/red]")
            return None
        
        selected_path = custom_path
    
    # Expand and create directory if needed
    output_dir = os.path.expanduser(selected_path)
    
    if not os.path.exists(output_dir):
        create = questionary.confirm(
            f"Directory doesn't exist. Create it?",
            default=True,
            style=custom_style
        ).ask()
        
        if create:
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
        
        return info['formats'], info['title']
    
    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        return None, None

def select_format(formats):
    """Let user select format with arrow keys"""
    console.print("\n[bold cyan]Select download format:[/bold cyan]\n")
    
    # Separate formats
    combined_formats = []
    video_formats = []
    audio_formats = []
    
    for f in formats:
        has_video = f.get('vcodec') != 'none'
        has_audio = f.get('acodec') != 'none'
        
        if has_video and has_audio:
            combined_formats.append(f)
        elif has_video:
            video_formats.append(f)
        elif has_audio:
            audio_formats.append(f)
    
    # Build choices
    choices = []
    
    # Add quick options
    choices.append(questionary.Choice(
        title="⭐ Best quality (automatic)",
        value="best"
    ))
    choices.append(questionary.Choice(
        title="🎬 Best video + audio (merged)",
        value="bestvideo+bestaudio"
    ))
    choices.append(questionary.Choice(
        title="🎵 Best audio only",
        value="bestaudio"
    ))
    choices.append(questionary.Separator("─── Combined Formats ───"))
    
    # Add combined formats
    for f in combined_formats[:8]:
        title = format_to_choice(f)
        choices.append(questionary.Choice(title=title, value=f.get('format_id')))
    
    # Add video-only formats
    if video_formats:
        choices.append(questionary.Separator("─── Video Only ───"))
        for f in video_formats[:8]:
            title = format_to_choice(f)
            choices.append(questionary.Choice(title=title, value=f.get('format_id')))
    
    # Add audio-only formats
    if audio_formats:
        choices.append(questionary.Separator("─── Audio Only ───"))
        for f in audio_formats[:8]:
            title = format_to_choice(f)
            choices.append(questionary.Choice(title=title, value=f.get('format_id')))
    
    selected_format = questionary.select(
        "Use arrow keys to navigate, Enter to select:",
        choices=choices,
        style=custom_style,
        use_indicator=True,
        instruction=" (↑↓ to move, Enter to select)"
    ).ask()
    
    return selected_format

def format_to_choice(f):
    """Convert format dict to readable choice string"""
    format_id = f.get('format_id', 'N/A')
    ext = f.get('ext', 'N/A')
    resolution = f.get('resolution', 'audio only' if f.get('vcodec') == 'none' else 'N/A')
    fps = f.get('fps', '')
    fps_str = f"{fps}fps" if fps else ""
    filesize = f.get('filesize') or f.get('filesize_approx')
    size = f"{filesize / (1024*1024):.1f}MB" if filesize else "?"
    note = f.get('format_note', '')
    
    # Build display string
    parts = [f"[{format_id}]", ext, resolution]
    if fps_str:
        parts.append(fps_str)
    parts.append(f"({size})")
    if note:
        parts.append(f"- {note}")
    
    return " ".join(parts)

def download_video(url, format_id, output_dir, title):
    """Download video with specified format"""
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_template,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            console.print(f"\n[bold green]Starting download...[/bold green]")
            console.print(f"[cyan]Format:[/cyan] {format_id}")
            console.print(f"[cyan]Output:[/cyan] {output_dir}")
            ydl.download([url])
            console.print(f"\n[bold green]✓ Download complete![/bold green]")
    
    except Exception as e:
        console.print(f"[bold red]✗ Error downloading: {e}[/bold red]")

def show_menu():
    """Display main menu"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]YouTube Video Downloader[/bold cyan]\n"
        "[dim]Download videos in your preferred format and location[/dim]",
        border_style="cyan"
    ))

def main():
    show_menu()
    
    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        console.print(f"[green]Using URL from arguments[/green]\n")
    else:
        url = questionary.text(
            "Enter YouTube URL:",
            style=custom_style
        ).ask()
    
    if not url:
        console.print("[red]No URL provided![/red]")
        return
    
    # List formats
    formats, title = list_formats(url)
    if not formats:
        return
    
    # Select format with arrow keys
    selected_format = select_format(formats)
    if not selected_format:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    # Get output directory with arrow keys
    output_dir = get_output_directory()
    if not output_dir:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    # Download
    download_video(url, selected_format, output_dir, title)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")