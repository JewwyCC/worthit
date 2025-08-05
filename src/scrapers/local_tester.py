from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()
fetched_transcript = ytt_api.fetch("dQw4w9WgXcQ")

for snippet in fetched_transcript:
    print(snippet.text)