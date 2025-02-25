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
        url = request.json.get('url')
        format_type = request.json.get('format', 'raw')  # Get format selection
        model = request.json.get('model', 'gpt-4o')  # Get model selection
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid YouTube URL'})

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ' '.join(item['text'] for item in transcript_list)

        # Process the transcript based on format selection
        if format_type == 'raw':
            processed_text = transcript_text
        elif format_type == 'blog':
            processed_text = generate_blog_post(transcript_text, model)
        elif format_type == 'guide':
            processed_text = generate_step_by_step_guide(transcript_text, model)
        elif format_type == 'summary':
            processed_text = generate_summary(transcript_text, model)
        elif format_type == 'educator_plus':
            processed_text = generate_educator_plus(transcript_text, model)
        else:
            processed_text = transcript_text

        return jsonify({
            'success': True,
            'transcript': processed_text
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route("/post-to-wordpress", methods=["POST"])
def post_to_wordpress():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        site_url = data.get("siteURL")
        title = data.get("title")
        content = data.get("content")
        status = data.get("status", "draft")
        image_data = data.get("image")
        categories = data.get("categories", [])
        tags = data.get("tags", [])
        scheduled_date = data.get("date")

        if not all([username, password, site_url, title, content]):
            return jsonify({"success": False, "error": "Missing required data"}), 400

        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        # --- WordPress Post Creation ---
        post_api_url = f"{site_url}/wp-json/wp/v2/posts"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        # Prepare post data with proper format for WordPress API
        post_data = {
            "title": {"rendered": title, "raw": title},
            "content": {"rendered": content, "raw": content},
            "status": status,
        }

        # Add featured media if available
        if image_data:
            try:
                media_api_url = f"{site_url}/wp-json/wp/v2/media"
                media_headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Disposition": f'attachment; filename="{image_data["filename"]}"',
                    "Content-Type": image_data["mime_type"],
                }
                image_binary = base64.b64decode(image_data["data"])
                media_response = requests.post(media_api_url, headers=media_headers, data=image_binary)
                media_response.raise_for_status()
                post_data["featured_media"] = media_response.json().get("id")
            except Exception as e:
                print(f"Image Upload Error: {e}")

        # Add categories if provided
        if categories:
            try:
                categories_api_url = f"{site_url}/wp-json/wp/v2/categories"
                category_ids = []
                for category_name in categories:
                    # Try to find existing category
                    response = requests.get(
                        f"{categories_api_url}?search={category_name}",
                        headers=headers
                    )
                    existing_categories = response.json()
                    if existing_categories:
                        category_ids.append(existing_categories[0]['id'])
                    else:
                        # Create new category
                        response = requests.post(
                            categories_api_url,
                            headers=headers,
                            json={"name": category_name}
                        )
                        if response.ok:
                            category_ids.append(response.json()['id'])
                if category_ids:
                    post_data["categories"] = category_ids
            except Exception as e:
                print(f"Category Error: {e}")

        # Add tags if provided
        if tags:
            try:
                tags_api_url = f"{site_url}/wp-json/wp/v2/tags"
                tag_ids = []
                for tag_name in tags:
                    # Try to find existing tag
                    response = requests.get(
                        f"{tags_api_url}?search={tag_name}",
                        headers=headers
                    )
                    existing_tags = response.json()
                    if existing_tags:
                        tag_ids.append(existing_tags[0]['id'])
                    else:
                        # Create new tag
                        response = requests.post(
                            tags_api_url,
                            headers=headers,
                            json={"name": tag_name}
                        )
                        if response.ok:
                            tag_ids.append(response.json()['id'])
                if tag_ids:
                    post_data["tags"] = tag_ids
            except Exception as e:
                print(f"Tag Error: {e}")

        # Add scheduled date if provided
        if scheduled_date:
            post_data["date"] = scheduled_date

        # Create the post
        response = requests.post(post_api_url, headers=headers, json=post_data)
        
        # Print response for debugging
        print("WordPress API Response:", response.text)
        
        response.raise_for_status()
        post_id = response.json().get("id")
        
        return jsonify({"success": True, "postId": post_id}), 201

    except requests.exceptions.RequestException as e:
        print(f"WordPress API Error: {str(e)}")
        return jsonify({"success": False, "error": f"WordPress API Error: {str(e)}"}), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/post-to-wordpress/<int:post_id>", methods=["PUT"])
def update_wordpress_post(post_id):
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")
        site_url = data.get("siteURL")
        title = data.get("title")
        content = data.get("content")
        status = data.get("status", "draft")

        if not all([username, password, site_url, title, content]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Create the credentials
        encoded_credentials = base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()

        # Update the post
        post_api_url = f"{site_url}/wp-json/wp/v2/posts/{post_id}"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
        }

        post_data = {
            "title": title,
            "content": content,
            "status": status
        }

        response = requests.post(post_api_url, headers=headers, json=post_data)
        response.raise_for_status()

        return jsonify({
            "success": True,
            "postId": response.json().get("id")
        }), 200

    except requests.exceptions.RequestException as e:
        print(f"WordPress API Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to update WordPress post: {str(e)}"
        }), 500
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


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