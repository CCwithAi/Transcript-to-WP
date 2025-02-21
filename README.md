# CCwithAI YouTube Transcript Repurposing

This application repurposes YouTube transcripts into various formats, such as raw transcript, blog posts, step-by-step guides, summaries, and educator plus materials. It also includes a feature to post generated content directly to WordPress.

## Features

- **Transcript Fetching:** Extracts YouTube transcripts using the YouTube Transcript API.
- **Content Generation:** Uses AI models to generate formatted blog posts, guides, summaries, and educational materials.
- **HTML Sanitization:** Cleans generated content using Bleach.
- **WordPress Integration:** Posts generated content to WordPress as drafts using API credentials.
- **Options to Select Models and Formats:** Choose from different AI models and content formats.

## Files and Application Structure

- **server.py:** Implements a Flask server with endpoints for transcript fetching and WordPress posting.
- **ai_agent.py:** Contains logic for interfacing with various AI APIs (OpenAI, Groq, and Google Generative AI).
- **index.html:** Frontend interface integrated with Quill editor for interactive transcript manipulation and posting.
- **requirements.txt:** Lists the required Python packages for the project.

## Setup Instructions

1. **Clone the Repository**

2. **Install Dependencies:**

   ```
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**

   Create a `.env` file in the project root with the following keys:
   - OPENAI_API_KEY
   - GEMINI_API_KEY
   - GROQ_API_KEY

4. **Run the Flask Server:**

   ```
   python server.py
   ```

5. **Open `index.html` in your browser to interact with the application.**

## Updates and Improvements

Recent updates include:
- Enhanced transcript extraction and processing.
- Improved AI content generation logic.
- Sanitization and HTML cleaning enhancements.
- Added feature to directly post content to WordPress.

## License

Specify your license information here.
