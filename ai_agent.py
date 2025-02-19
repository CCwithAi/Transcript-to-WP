import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

load_dotenv()

# Load API keys
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Define system prompts
SYSTEM_PROMPTS = {
    "blog_post": """Convert the given YouTube transcript and any provided context into a first-person blog post.

Remove all branding, broadcaster names, YouTube-specific references, and calls to action such as 'subscribe' or 'like the video.'

Maintain a casual, conversational tone, using 'I,' 'my,' 'we,' and 'our' to create a personal connection with the reader.

Structure the blog post to be at least 800 words, following best SEO practices based on Google guidelines, and include:

- Introduction: An engaging hook, overview of the topic, and thesis statement.
- Main Content: Key points, personal anecdotes, and actionable insights.
- Conclusion: Summary, call-to-action, and final thoughts.

Optimize for SEO:

- Use natural keyword placement.
- Include subheadings (H2, H3) for better readability.
- Ensure content is people-first, focusing on user intent and value.
- Avoid jargon and overly technical language.

Ensure the blog post is free of errors, flows naturally, uses UK English spelling and grammar throughout, and adds a personal touch with a relatable and engaging tone.
""",

    "step_by_step_guide": """You are a helpful assistant that generates step-by-step guides from YouTube transcripts. Focus on extracting actionable steps and providing clear, concise instructions. Use numbered lists and headings to organize the guide effectively. Do not include ` or display your thoughts in the output.""",

    "summary": """You are a helpful assistant that summarizes YouTube video transcripts. Summarize the transcript into three bullet points to sum up what the video is about and why someone should watch it.""",

    "educator_plus": '''You are a helpful assistant designed to create educational materials from YouTube transcripts.

Tasks:

1. Create a Fill-in-the-Blank Worksheet from the transcript, focusing on key concepts. Provide answers at the end.
2. Create a Quiz (multiple choice or short answer) based on the transcript. Provide answers at the end.
3. Find three supplemental resources (links) related to the video's topic.
4. Combine the worksheet, quiz, and resources in markdown format.'''
}

# Define model configurations
MODEL_CONFIGS = {
    "gpt-4o": {
        "client": "openai",
        "model": "gpt-4o",
    },
    "deepseek-r1-distill-llama-70b": {
        "client": "groq",
        "model": "deepseek-r1-distill-llama-70b",
        "temperature": 0.1,
        "max_completion_tokens": 4096,
        "top_p": 0.95,
        "stream": False,
        "stop": None,
    },
    "gemini": {
        "client": "gemini",
        "model": "gemini-2.0-pro-exp-02-05",
    },
    "llama-3-70b-versatile": {
            "client": "groq",
            "model": "llama3-70b-8192",
            "temperature": 0.1,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": False,
            "stop": None,
        },
}

def _call_api(prompt_name: str, transcript: str, model: str = "gpt-4o") -> str:
    """
    Helper function to call different AI models based on the specified configuration.
    
    Args:
        prompt_name: Name of the system prompt to use
        transcript: YouTube transcript text
        model: Name of the model to use (default: "gpt-4o")
    
    Returns:
        Generated content from the AI model
    """
    try:
        # Get model configuration
        print(f"Model received by _call_api: {model=}")
        config = MODEL_CONFIGS.get(model)
        if not config:
            return "Invalid model selected."

        # Get system prompt
        prompt = SYSTEM_PROMPTS.get(prompt_name)
        if not prompt:
            return "Invalid prompt name."

        # Call the appropriate API based on client type
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
            completion = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": transcript},
                ],
                temperature=config.get("temperature"),
                max_completion_tokens=config.get("max_completion_tokens"),
                top_p=config.get("top_p"),
                stream=config.get("stream"),
                stop=config.get("stop"),
            )
            if config.get("stream"):
                full_response = ""
                for chunk in completion:
                    full_response += chunk.choices[0].delta.content or ""
                return full_response
            else:
                return completion.choices[0].message.content

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
    """Generates a blog post from the given transcript using the specified model."""
    return _call_api("blog_post", transcript, model)

def generate_step_by_step_guide(transcript: str, model: str = "gpt-4o") -> str:
    """Generates a step-by-step guide from the given transcript using the specified model."""
    return _call_api("step_by_step_guide", transcript, model)

def generate_summary(transcript: str, model: str = "gpt-4o") -> str:
    """Summarizes the transcript into three bullet points."""
    return _call_api("summary", transcript, model)

def generate_educator_plus(transcript: str, model: str = "gpt-4o") -> str:
    """Generates YouTube Educator Plus output from the given transcript using the specified model."""
    return _call_api("educator_plus", transcript, model)

def get_youtube_transcript(video_id: str) -> str:
    """Fetches transcript text from YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ' '.join(item['text'] for item in transcript_list)
        return transcript_text
    except Exception as e:
        raise ValueError(f"Failed to get transcript for video {video_id}: {str(e)}")