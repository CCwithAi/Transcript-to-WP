import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import re  # Import the regular expression module

load_dotenv()

# Load API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Define system prompts (Simplified - No Block Instructions)
SYSTEM_PROMPTS = {
    "blog_post": """Convert the given YouTube transcript into a first-person blog post.

Remove all branding, broadcaster names, YouTube-specific references, and calls to action.

Maintain a casual, conversational tone. Structure the post with:

- An introduction (1-2 paragraphs).
- Several main sections, each with a clear heading (like an H2) and 2-4 paragraphs.
- A conclusion (1-2 paragraphs).

Use UK English spelling and grammar.  Output plain text, well-formatted with paragraphs and headings. Do *not* output JSON or Markdown. Focus on the *content*; do not include any HTML tags.
""",

    "step_by_step_guide": """Create a step-by-step guide from the YouTube transcript.

Focus on actionable steps and clear instructions. Use numbered lists and headings to organize the guide. Output plain text, with headings clearly indicating sections, and numbered lists where appropriate. Do *not* output JSON or Markdown. Focus on the *content*; do not include any HTML tags.
""",

    "summary": """Summarize the YouTube video transcript into three bullet points. Output plain text using '-' to denote bullet points. Do *not* output JSON or HTML.""",

    "educator_plus": '''You are a helpful assistant to create educational materials from YouTube transcripts.

Tasks:

1. Create a Fill-in-the-Blank Worksheet. Provide answers.
2. Create a Quiz (multiple choice/short answer). Provide answers.
3. Find three supplemental resources (links).
4. Combine the worksheet, quiz, and resources in markdown format. Output plain text/markdown, not JSON.''',
}

# Define model configurations (Simplified)
MODEL_CONFIGS = {
    "gpt-4o": {"client": "openai", "model": "gpt-4o"},
    "deepseek-r1-distill-llama-70b": {"client": "groq", "model": "deepseek-r1-distill-llama-70b"},
    "gemini": {"client": "gemini", "model": "gemini-2.0-pro-exp-02-05"}, # CORRECTED MODEL
    "llama-3-70b-versatile": {"client": "groq", "model": "llama3-70b-8192"},
}


def _call_api(prompt_name: str, transcript: str, model: str = "gpt-4o") -> str:
    """Helper function to call AI models (simplified)."""
    config = MODEL_CONFIGS.get(model)
    if not config:
        return "Invalid model selected."

    prompt = SYSTEM_PROMPTS.get(prompt_name)
    if not prompt:
        return "Invalid prompt name."

    try:
        if config["client"] == "openai":
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript},
                ],
            )
            return response.choices[0].message.content

        elif config["client"] == "groq":
            client = Groq(api_key=groq_api_key)
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript},
                ],
            )
            return response.choices[0].message.content

        elif config["client"] == "gemini":
            genai.configure(api_key=gemini_api_key)
            gemini_model = genai.GenerativeModel(model_name=config["model"])
            response = gemini_model.generate_content([prompt, transcript])
            return response.text

        else:
            return "Invalid client configuration."
    except Exception as e:
        return f"API call failed: {str(e)}"

def generate_blog_post(transcript: str, model: str = "gpt-4o") -> str:
    """Generates a blog post (plain text)."""
    return _call_api("blog_post", transcript, model)

def generate_step_by_step_guide(transcript: str, model: str = "gpt-4o") -> str:
    """Generates a step-by-step guide (plain text)."""
    return _call_api("step_by_step_guide", transcript, model)

def generate_summary(transcript: str, model: str = "gpt-4o") -> str:
    """Generates a summary (plain text)."""
    return _call_api("summary", transcript, model)

def generate_educator_plus(transcript: str, model: str = "gpt-4o") -> str:
    """Generates educator materials (plain text)."""
    return _call_api("educator_plus", transcript, model)

def get_youtube_transcript(video_id: str) -> str:
    """Fetches transcript text from YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join(item["text"] for item in transcript_list)
        return transcript_text
    except Exception as e:
        raise ValueError(f"Failed to get transcript for video {video_id}: {str(e)}")