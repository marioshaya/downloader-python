import os
import sys
import yt_dlp
import questionary

from pathlib import Path
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

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

def download_video(url, format_id, output_dir, title):
    """Download video with specified format"""
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': format_id if format_id else 'best',
        'outtmpl': output_template,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            console.print(f"\n[bold green]Starting download...[/bold green]")
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
        "[dim]Qamardo SHAYA[/dim]",
        border_style="cyan"
    ))

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
    show_menu()
    
    # Get URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        console.print(f"[green]Using URL from arguments[/green]")
    else:
        url = Prompt.ask("\n[bold cyan]Enter YouTube URL[/bold cyan]").strip()
    
    if not url:
        console.print("[red]No URL provided![/red]")
        return
    
    # List formats
    formats, title = list_formats(url)
    if not formats:
        return
    
     # Format selection menu
    console.print("\n" + "─" * 80)
    console.print("[bold yellow]Download Options:[/bold yellow]")
    console.print("  • Enter [bold]format ID[/bold] for specific format")
    console.print("  • Press [bold]Enter[/bold] for best quality")
    console.print("  • Type [bold]'bestvideo+bestaudio'[/bold] for best video+audio merge")
    console.print("  • Type [bold]'bestaudio'[/bold] for audio only")
    console.print("  • Type [bold]'q'[/bold] to quit")
    console.print("─" * 80)
    
    choice = Prompt.ask("\n[bold]Your choice[/bold]", default="").strip()
    
    if choice.lower() == 'q':
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    # Get output directory
    output_dir = get_output_directory()
    if not output_dir:
        return
    
    # Download
    format_id = choice if choice else 'best'
    download_video(url, format_id, output_dir, title)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")

    