# Transcript to WP

A web application that converts YouTube transcripts into professional blog posts and publishes them directly to WordPress, powered by AI.

## Features

- **YouTube Integration**: Automatically fetch transcripts from YouTube videos
- **AI Processing**: Convert transcripts into various formats using multiple AI models:
  - GPT-4
  - Gemini
  - DeepSeek
  - Llama 3
- **Multiple Output Formats**:
  - Blog Posts
  - Step-by-Step Guides
  - Summaries
  - Educational Materials
- **WordPress Integration**:
  - Multiple account management
  - Post scheduling
  - Draft/publish control
  - Categories and tags support
  - Featured image support
- **Content Management**:
  - Template system
  - Post management interface
  - Bulk actions
  - Search and filtering

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Transcript-to-WP.git
cd Transcript-to-WP
```
1A. create a virtual environment and run it
python -m venv venv
then venv\Scripts\activate
 
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

4. Start the servers:
- Backend: `python server.py` (runs on port 5000)
- Frontend: `python -m http.server 8000`

5. Access the application at `http://localhost:8000`

## WordPress Setup

1. In your WordPress site:
   - Go to Users → Profile
   - Scroll to Application Passwords
   - Add new application password
   - Copy the generated password

2. In the application:
   - Click "Manage WP Accounts"
   - Add your WordPress site URL
   - Enter your username
   - Enter the application password
   - (Optional) Add to a folder for organization

## Usage

1. Enter a YouTube URL
2. Select desired format:
   - Blog Post
   - Step-by-Step Guide
   - Summary
   - Educator Plus
3. Choose AI model
4. Generate content
5. Edit as needed in the rich text editor
6. Add title, categories, tags
7. Select WordPress account
8. Publish or schedule

## Project Structure

```
Transcript-to-WP/
├── server.py           # Flask backend server
├── ai_agent.py        # AI processing logic
├── requirements.txt   # Python dependencies
├── .env              # API keys (not in repo)
└── static/           # Frontend files
    ├── index.html
    ├── wordpress_management.html
    ├── wordpress_posts.html
    ├── sent_posts.html
    └── images/
```

## Security Notes

- Never commit your `.env` file
- Use application passwords for WordPress
- Store credentials securely
- Follow WordPress security best practices

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
