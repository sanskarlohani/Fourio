banner

video link

## Description

**Fourio** is a command-line implementation of a music recognition system inspired by **Shazam**.The name Fourio is a portmanteau of **"Fourier"** and **"Audio"** named after the [**Fourier Transform**](https://en.wikipedia.org/wiki/Fourier_transform).It analyzes song fingerprints, detects matches from local or downloaded tracks, and integrates with Spotify and YouTube for metadata and previews.  

This version of **Fourio** is fully written in **Python**, powered by:
- ⚡ **FastAPI** — backend API framework for high-performance web services  
- 🧠 **Typer** — command-line interface (CLI) for intuitive developer experience  
- 🧩 **uv** — ultra-fast dependency manager and environment tool  
- 🎵 **ffmpeg** — audio conversion and processing utility  
- ☁️ **Spotify API** — metadata integration for tracks, albums, and playlists
- 🎞️ **YouTube API** — for fetching song previews and additional metadata

## Project Struture
  ```bash
  fourio/
  ├── app/
  │   ├── api/             # Web API endpoints
  │   ├── utils/           # Logging, file handling, general utilities
  │   ├── db/              # Database connection and operations
  │   ├── models/          # Data models
  │   ├── services/        # Different services like Spotify, YouTube and WAV conversion
  │   ├── core/            # Core fingerprinting, Spectrogram and matching logic
  │   └── main.py          # FastAPI entry point
  |── .env                 # Environment variables
  ├── pyproject.toml       # uv dependencies
  ├── requirements.txt     # Python dependencies  (Optional)
  ├── cli_logic.py         # CLI logic        
  ├── cli.py               # Typer CLI entry point
  ├── .gitignore
  ├── README.md
  └── LICENSE
  ```

### Prerequisites
Python 3.10+

FFmpeg (verify via ffmpeg -version)

uv — install guide

## Installation

### ✔ Prerequisites

#### 🔹 Python 3.10+  
- [Download Python](https://www.python.org/downloads/)


#### 🔹 FFmpeg (required for audio decoding)  

  **Install FFmpeg:**

  - **Windows (Chocolatey — Recommended)**  
    ```bash
    choco install ffmpeg
    ```

      [Chocolatey install guide](https://chocolatey.org/install)

  - **macOS (Homebrew)**
    ```bash
      brew install ffmpeg
    ```
  - **Linux (Ubuntu/Debian)**
    ```bash
      sudo apt update
      sudo apt install ffmpeg
    ```


  - [**Official FFmpeg download page**](https://ffmpeg.org/download.html)

  **Verify installation:**
  ```bash
    ffmpeg -version
  ```

🔹 uv — ultra-fast Python environment & dependency manager

Install guide:
https://github.com/astral-sh/uv

---
### 🚀 Steps



#### **1. Clone the repository and create a virtual environment using uv**

```bash
# Clone the repo
git clone https://github.com/RudraNarayan94/Fourio.git
cd fourio

# Create virtual environment (using uv)
uv venv

# Activate it
uv run bash          # On PowerShell → uv run powershell

# Install dependencies
uv sync
```

#### **2. (Optional) Setup using Python venv + requirements.txt**
```bash
  # Clone the repo
git clone https://github.com/RudraNarayan94/Fourio.git
cd fourio

# Create virtual environment (using venv)
python -m venv venv

# Activate it
source venv/bin/activate     # macOS/Linux
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---


### 🎵 Environment Setup

Create a `.env` file inside folder.

Use the structure defined in the sample file:  
👉 **See `.env.example`** ([link](https://github.com/RudraNarayan94/Fourio/.env.example))

The `.env` file should include keys for:
- Spotify API access  
- Database configuration  
- Backend settings  
- YouTube API key (optional)

You can generate **Spotify credentials** by creating an app at the  
👉 Spotify Developer Dashboard:  
https://developer.spotify.com/dashboard/

Once created, copy your:
```bash
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
```

These credentials allow Fourio to access track metadata, album details, and playlist information.

---



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

This project is licensed under the [**MIT License**](https://github.com/RudraNarayan94/Fourio/blob/main/LICENSE).