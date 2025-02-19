from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import re
from ai_agent import generate_blog_post, generate_step_by_step_guide, generate_summary, generate_educator_plus


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

        return jsonify({
            'success': True,
            'transcript': transcript_text
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(port=5000)
