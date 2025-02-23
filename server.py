from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import re
from ai_agent import (
    generate_blog_post,
    generate_step_by_step_guide,
    generate_summary,
    generate_educator_plus,
)
import requests
import base64
import os
import json  # Make sure to import the json module

app = Flask(__name__)
CORS(app)

# --- Configuration for uploads (still needed for image handling)---
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_video_id(url):
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@app.route("/transcript", methods=["POST"])
def get_transcript():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"success": False, "error": "URL is required"})

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"success": False, "error": "Invalid YouTube URL"})

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join(item["text"] for item in transcript_list)

        format_type = request.json.get("format")
        model = request.json.get("model")

        if format_type == "blog":
            result = generate_blog_post(transcript_text, model)
        elif format_type == "guide":
            result = generate_step_by_step_guide(transcript_text, model)
        elif format_type == "summary":
            result = generate_summary(transcript_text, model)
        elif format_type == "educator_plus":
            result = generate_educator_plus(transcript_text, model)
        else:
            result = transcript_text  # Default: raw transcript

        return jsonify({"success": True, "transcript": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/post-to-wordpress", methods=["POST"])
def post_to_wordpress():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        site_url = data.get("siteURL")
        title = data.get("title")
        content = data.get("content")  # Get the content (could be JSON or HTML)
        status = data.get("status", "draft")
        image_data = data.get("image")

        if not all([username, password, site_url, title, content]):
            return jsonify({"success": False, "error": "Missing required data"}), 400

        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode(
            "utf-8"
        )

        # --- Image Upload (if image data is provided) ---
        featured_media_id = None
        if image_data:
            try:
                media_api_url = f"{site_url}/wp-json/wp/v2/media"
                headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Disposition": f'attachment; filename="{image_data["filename"]}"',
                    "Content-Type": image_data["mime_type"],
                }
                image_binary = base64.b64decode(image_data["data"])
                media_response = requests.post(
                    media_api_url, headers=headers, data=image_binary
                )
                media_response.raise_for_status()
                featured_media_id = media_response.json().get("id")
            except requests.exceptions.RequestException as e:
                print(f"Image Upload Error: {e}")
                return (
                    jsonify({"success": False, "error": f"Image upload failed: {e}"}),
                    500,
                )

        # --- WordPress Post Creation ---
        post_api_url = f"{site_url}/wp-json/wp/v2/posts"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",  # Always send JSON to the WP API
        }

        # Prepare post data.  Crucially, 'content' is now handled correctly.
        post_data = {
            "title": title,
            "status": status,
            "featured_media": featured_media_id,
        }

        # Check if content is JSON (from blog or guide)
        if isinstance(content, str):
            try:
                content_json = json.loads(content)  # Try to parse as JSON
                if "blocks" in content_json:
                    # Convert blocks to serialized string format
                    serialized_blocks = ""
                    for block in content_json["blocks"]:
                        serialized_blocks += block_to_html_comment(block) + "\n"
                    post_data["content"] = serialized_blocks
                else:
                    post_data["content"] = content  # It was probably plain text
            except json.JSONDecodeError:
                post_data["content"] = content  # It wasn't JSON, treat as HTML
        else:  #If not string format, assume its plain text
             post_data["content"] = content

        response = requests.post(post_api_url, headers=headers, json=post_data)
        response.raise_for_status()

        post_id = response.json().get("id")
        return jsonify({"success": True, "postId": post_id}), 201

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


def block_to_html_comment(block):
    """Converts a single block to the WordPress HTML comment format."""
    block_type = block["type"]
    attributes = block.get("attributes", {})
    inner_html = ""

    if block_type == "core/paragraph":
        inner_html = attributes.get("content", "")
    elif block_type == "core/heading":
        level = attributes.get("level", 2)  # Default to h2
        inner_html = f"<h{level}>{attributes.get('content', '')}</h{level}>"
    elif block_type == "core/list":
        ordered = attributes.get("ordered", False)
        list_tag = "ol" if ordered else "ul"
        inner_html = f"<{list_tag}>"
        for list_item in block.get("innerBlocks", []):
            inner_html += f"<li>{list_item.get('attributes', {}).get('content', '')}</li>"
        inner_html += f"</{list_tag}>"
    elif block_type == "core/group":
        # Handle the group block (usually just wraps other content)
        inner_blocks_html = ""
        for inner_block in block.get("innerBlocks", []):
            inner_blocks_html += block_to_html_comment(inner_block)
        inner_html = inner_blocks_html
    else:
        return ""  # Skip unsupported block types.  IMPORTANT.

    # Construct the HTML comment.  Very important for WordPress.
    attributes_str = " ".join(
        f'{key}="{value}"'
        for key, value in attributes.items()
        if key != "content" and key != "level" and key != "ordered"
    )  # Exclude content, level and ordered

    if attributes_str:
        return f"{inner_html}"
    else:
        return f"{inner_html}"

if __name__ == '__main__':
    app.run(port=5000, debug=True)