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
|-── cli_logic.py                 
├── cli.py               # Typer CLI entry point
├── .gitignore
├── README.md
└── LICENSE

## Installation :desktop_computer:
### Prerequisites


### Steps

