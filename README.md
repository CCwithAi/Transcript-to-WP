# YouTube Transcript Scraper - MVP

## Overview
A simple, lightweight YouTube transcript extraction tool built with Python and HTML.

## Features
- Extract transcripts from YouTube videos
- Simple, no-framework frontend
- Lightweight Python backend
- Easy to set up and use

## Prerequisites
- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-transcript-scraper.git
cd youtube-transcript-scraper
```

2. Install required dependencies:
```bash
pip install flask flask-cors youtube-transcript-api
```

## Running the Application

1. Start the Python backend server:
```bash
python server.py
```

2. Open `index.html` in your web browser

## How It Works
- Frontend: Pure HTML/JavaScript with embedded UI
- Backend: Flask server using `youtube-transcript-api`
- Simple POST endpoint handles transcript extraction
- Supports various YouTube URL formats

## Dependencies
- Flask
- Flask-CORS
- youtube-transcript-api

## Limitations
- Requires transcripts to be available for the video
- Works best with English language videos

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
MIT License
