from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import re
from ai_agent import generate_blog_post, generate_step_by_step_guide, generate_summary, generate_educator_plus
import requests
import base64
import bleach

app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'success': False, 'error': 'Invalid YouTube URL'})

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = ' '.join(item['text'] for item in transcript_list)

        format = request.json.get('format')
        model = request.json.get('model')
        if format == 'blog':
            transcript_text = generate_blog_post(transcript_text, model)
        elif format == 'guide':
            transcript_text = generate_step_by_step_guide(transcript_text, model)
        elif format == 'summary':
            transcript_text = generate_summary(transcript_text, model)
        elif format == 'educator_plus':
            transcript_text = generate_educator_plus(transcript_text, model)

        # --- HTML Cleaning (Added) ---
        allowed_tags = ['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'em', 'blockquote', 'a']
        allowed_attributes = {'a': ['href', 'title', 'target']}
        cleaned_transcript = bleach.clean(transcript_text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        cleaned_transcript = re.sub(r'\n\s*\n', '\n', cleaned_transcript) # Remove extra newlines
        cleaned_transcript = re.sub(r' +', ' ', cleaned_transcript) # Remove multiple spaces
        cleaned_transcript = cleaned_transcript.replace("<p></p>", "") # Remove empty p tags

        return jsonify({
            'success': True,
            'transcript': cleaned_transcript  # Return the cleaned HTML
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/post-to-wordpress', methods=['POST'])
def post_to_wordpress():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        site_url = data.get('siteURL')
        title = data.get('title')
        content = data.get('content')
        status = data.get('status', 'draft')  # Default to draft

        if not all([username, password, site_url, title, content]):
            return jsonify({'success': False, 'error': 'Missing required data'}), 400

        # --- HTML Validation and Sanitization (using bleach) ---
        allowed_tags = ['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'em', 'blockquote', 'a']
        allowed_attributes = {'a': ['href', 'title', 'target']}  # Allow href and title on <a> tags
        cleaned_content = bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        cleaned_content = re.sub(r'\n\s*\n', '\n', cleaned_content) # Remove extra newlines - IMPORTANT
        cleaned_content = re.sub(r' +', ' ', cleaned_content) # remove multiple spaces
        cleaned_content = cleaned_content.replace("<p></p>", "") # Remove empty p tags

        # --- WordPress API Interaction ---
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        api_url = f"{site_url}/wp-json/wp/v2/posts"
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        post_data = {
            'title': title,
            'content': cleaned_content,  # Use the cleaned content
            'status': status
        }
        response = requests.post(api_url, headers=headers, json=post_data)

        if response.status_code == 201:
            post_id = response.json().get('id')
            return jsonify({'success': True, 'postId': post_id}), 201
        else:
            return jsonify({'success': False, 'error': response.text}), response.status_code

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)