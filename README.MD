banner

video link

Description
Fourio is a command-line implementation of a music recognition system inspired by Shazam.
It analyzes song fingerprints, detects matches from local or downloaded tracks, and integrates with Spotify and YouTube for metadata and previews.

This version is fully written in Python, powered by:

⚡ FastAPI (backend API)

🧠 Typer (CLI)

🧩 uv (ultra-fast dependency manager)

🎵 ffmpeg (audio conversion)

☁️ Spotify API (metadata integration)

Project Struture
fourio/
├── app/
│   ├── api/             # FastAPI endpoints
│   ├── utils/           # Logging, file handling, fingerprint logic
│   ├── db/           # Logging, file handling, fingerprint logic
│   ├── models/           # Logging, file handling, fingerprint logic
│   ├── services/           # Logging, file handling, fingerprint logic
│   ├── core/           # Logging, file handling, fingerprint logic
│   └── main.py              # FastAPI entry point
|── .env
├── pyproject.toml       # uv dependencies
├── cli_logic.py                 
├── cli.py               # Typer CLI entry point
├── .gitignore
├── README.md
└── LICENSE

## Installation :desktop_computer:
### Prerequisites
Python 3.10+

FFmpeg (verify via ffmpeg -version)

uv — install guide


### Steps

# Clone the repo
git clone https://github.com/yourname/fourio.git
cd fourio/backend

# Create virtual environment (using uv)
uv venv

# Activate it
uv run bash  # or PowerShell: uv run powershell

# Install dependencies
uv sync



🎵 Environment Setup

Create a .env file in your backend folder:

SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
SONGS_DIR=songs
TMP_DIR=tmp


You can generate Spotify credentials from the Spotify Developer Dashboard





🧠 Usage
Run CLI
uv run python cli.py --help

🎧 Commands
Command	Description
find <path_to_wav>	Find matching song fingerprints
download <spotify_url>	Download and process a Spotify song
save <path_or_dir> [--force/-f]	Save and fingerprint local songs
erase	Clear all stored songs and fingerprints
serve --proto http --port 8000	Start FastAPI backend
💡 Examples
▶ Download a Spotify track
uv run python cli.py download https://open.spotify.com/track/4pqwGuGu34g8KtfN8LDGZm

🔎 Find a song match
uv run python cli.py find songs/Voila.wav

💾 Save local songs
uv run python cli.py save ./local_songs/ --force

🧹 Erase all data
uv run python cli.py erase

🚀 Serve backend
uv run python cli.py serve --proto http --port 8000




📚 Resources

How does Shazam work - Toptal

Song recognition using audio fingerprinting (U. Rochester)

Creating Shazam in Java - Roy van Rijn




🧑‍💻 Author

Rudra Narayan
🎵 Building Fourio – a calm, minimal take on music recognition.
GitHub
 • LinkedIn



🚀 Future Roadmap

Fourio is evolving from a CLI tool into a full-stack, Shazam-inspired audio recognition system. Here’s what’s ahead:

🎧 Frontend (React + Web Audio)

Capture live microphone input

Convert audio to PCM samples and generate fingerprints client-side

Visualize waveform and match confidence in real time

⚙️ Backend (FastAPI)

Implement REST endpoints:

POST /find → Match uploaded fingerprints

POST /download → Fetch and index tracks from external sources

GET /songs → Retrieve indexed database entries

Add async fingerprint matching engine and optimized caching

🧠 Fingerprint Engine

Migrate core hashing and matching logic into a reusable service layer

Add configurable fingerprint density, threshold tuning, and duplicate detection

Enable incremental indexing and background updates

☁️ DevOps & Deployment

Containerize the entire system with Docker

Provide optional GPU/FFmpeg accelerated pipeline

Auto-sync fingerprints and metadata to a remote MongoDB instance

🧩 Long-Term

Browser-based “Music Finder” mode

User library for saved recordings and results

WebAssembly (WASM) experimentation for client-side matching


📜 License

This project is licensed under the MIT License.