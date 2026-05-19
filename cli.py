import sys
import typer
from dotenv import load_dotenv 

import cli_logic 

from app.utils.logger_setup import GetLogger
from app.utils.file_io import CreateFolder 

# --- Configuration ---
app = typer.Typer(
  name="Fourio",
  help="Shazam-style audio fingerprinting and music management CLI.", 
)
logger = GetLogger()
SONGS_DIR = "songs" 
TMP_DIR = "tmp"

def main():
    """Entry point handler that runs before any command."""
    
    load_dotenv() 
        
    err = CreateFolder(TMP_DIR)
    if err:
        logger.error(f"Failed to create directory {TMP_DIR}: {err}")
        sys.exit(1)
        
    err = CreateFolder(SONGS_DIR)
    if err:
        logger.error(f"Failed to create directory {SONGS_DIR}: {err}")
        sys.exit(1)

    app()


# ----------------------------------------------------------------------
# --- CLI Subcommand Definitions (@app.command) ---
# ----------------------------------------------------------------------

@app.command(name="find", help="Analyzes any audio file and searches for matching songs in the database.")
def find_command(file_path: str = typer.Argument(..., help="Path to the WAV file to analyze (e.g., audio.wav).")):
    
  cli_logic.find(file_path)


@app.command(name="download", help="Downloads and fingerprints a resource from Spotify or YouTube URL.")
def download_command(url: str = typer.Argument(..., help="Spotify or YouTube URL (track, playlist, album, or video link).")):
    
  cli_logic.download(url)


@app.command(name="erase", help="Deletes all indexed songs and fingerprints from the database.")
def erase_command():
    
  cli_logic.erase(SONGS_DIR)


@app.command(name="save", help="Saves (fingerprints) a local WAV file or directory of files to the database.")
def save_command(
    file_path: str = typer.Argument(..., help="Path to the WAV file or directory containing files to index."),
    
    force: bool = typer.Option(
        False, 
        "-f", 
        "--force", 
        help="Force saving even if the required metadata (like YouTube ID) is missing."
    )
):
    
  cli_logic.save(file_path, force)


# @app.command(name="serve", help="Starts the FastAPI web server for API access (HTTP/HTTPS).")
# def serve_command(
#     protocol: str = typer.Option(
#         "http", 
#         "--proto", 
#         help="Protocol to use (http or https)."
#     ),
#     port: str = typer.Option(
#         "5000", 
#         "-p", 
#         help="Port to use."
#     )
# ):
#     """Corresponds to the Go 'serve' case: serve(*protocol, *port)."""
    
#     # Delegate logic to the cmd.py module
#     cli_logic.serve(protocol, port)


if __name__ == "__main__":
  main()