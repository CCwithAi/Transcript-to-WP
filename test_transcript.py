from youtube_transcript_api import YouTubeTranscriptApi

# Video ID from the link https://www.youtube.com/watch?v=YoeNwp9je6E
video_id = 'YoeNwp9je6E'

try:
    # Fetch the transcript
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    
    # Print each subtitle entry
    for entry in transcript:
        print(f"Text: {entry['text']}")
        print(f"Start Time: {entry['start']}")
        print(f"Duration: {entry['duration']}")
        print("---")

except Exception as e:
    print(f"Error fetching transcript: {e}")
