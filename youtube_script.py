import json
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from typing import List, Dict
import spacy
from textblob import TextBlob
import re
from collections import defaultdict
import time

class ShoeReviewAnalyzer:
    def __init__(self, youtube_api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.nlp = spacy.load("en_core_web_lg")
        self.processed_videos = set()
        
        # Define keywords for different aspects
        self.aspect_keywords = {
            'traction': ['grip', 'traction', 'bite', 'court feel', 'outdoor', 'indoor'],
            'cushioning': ['cushion', 'impact', 'responsive', 'bounce', 'springy', 'bottom out'],
            'fit': ['fit', 'lockdown', 'heel slip', 'toe box', 'width', 'true to size'],
            'durability': ['durability', 'outsole', 'wear', 'last', 'break down']
        }
        
        # Define play style keywords
        self.play_style_keywords = {
            'guard': ['guard', 'quick', 'agile', 'shifty'],
            'forward': ['forward', 'power', 'strong'],
            'center': ['center', 'big', 'post'],
            'indoor': ['indoor', 'court'],
            'outdoor': ['outdoor', 'street', 'blacktop']
        }

    def search_youtube_videos(self, shoe_name: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for shoe review videos."""
        try:
            query = f"{shoe_name} basketball shoe review"
            request = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response['items']:
                video_id = item['id']['videoId']
                if video_id not in self.processed_videos:
                    videos.append({
                        'video_id': video_id,
                        'title': item['snippet']['title'],
                        'channel': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt']
                    })
            return videos
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []

    def get_transcript(self, video_id: str) -> str:
        """Get video transcript."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([t['text'] for t in transcript])
        except Exception as e:
            print(f"Error getting transcript: {e}")
            return ""

    def extract_entities(self, text: str) -> Dict:
        """Extract named entities from text."""
        doc = self.nlp(text)
        entities = defaultdict(list)
        
        for ent in doc.ents:
            if ent.label_ in ['PRODUCT', 'PERSON', 'ORG']:
                entities[ent.label_].append(ent.text)
        
        return dict(entities)

    def analyze_aspect_sentiment(self, text: str) -> Dict:
        """Analyze sentiment for different aspects of the shoe."""
        aspects = {}
        
        for aspect, keywords in self.aspect_keywords.items():
            aspect_sentences = []
            for sentence in text.split('.'):
                if any(keyword in sentence.lower() for keyword in keywords):
                    aspect_sentences.append(sentence)
            
            if aspect_sentences:
                sentiment = TextBlob(' '.join(aspect_sentences)).sentiment.polarity
                aspects[aspect] = {
                    'sentiment': sentiment,
                    'description': ' '.join(aspect_sentences[:2])  # Take first two relevant sentences
                }
        
        return aspects

    def identify_play_styles(self, text: str) -> List[str]:
        """Identify play styles mentioned in the review."""
        play_styles = set()
        
        for style, keywords in self.play_style_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                play_styles.add(style)
        
        return list(play_styles)

    def chunk_transcript(self, text: str) -> Dict:
        """Split transcript into topic-based chunks."""
        chunks = defaultdict(list)
        current_topic = 'general'
        
        for sentence in text.split('.'):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Simple topic detection based on keywords
            if any(keyword in sentence.lower() for keyword in self.aspect_keywords['traction']):
                current_topic = 'traction'
            elif any(keyword in sentence.lower() for keyword in self.aspect_keywords['cushioning']):
                current_topic = 'cushioning'
            elif any(keyword in sentence.lower() for keyword in self.aspect_keywords['fit']):
                current_topic = 'fit'
            elif any(keyword in sentence.lower() for keyword in self.aspect_keywords['durability']):
                current_topic = 'durability'
            
            chunks[current_topic].append(sentence)
        
        return dict(chunks)

    def generate_summary(self, chunks: Dict) -> str:
        """Generate a concise summary from the chunks."""
        summary_parts = []
        
        for topic, sentences in chunks.items():
            if topic != 'general' and sentences:
                # Take the first sentence that contains sentiment
                for sentence in sentences:
                    sentiment = TextBlob(sentence).sentiment.polarity
                    if sentiment != 0:
                        summary_parts.append(sentence)
                        break
        
        return " ".join(summary_parts)

    def analyze_review(self, shoe_name: str, video_data: Dict) -> Dict:
        """Analyze a single shoe review video."""
        transcript = self.get_transcript(video_data['video_id'])
        if not transcript:
            return None

        # Extract entities
        entities = self.extract_entities(transcript)
        
        # Analyze aspects
        aspects = self.analyze_aspect_sentiment(transcript)
        
        # Identify play styles
        play_styles = self.identify_play_styles(transcript)
        
        # Chunk transcript
        chunks = self.chunk_transcript(transcript)
        
        # Generate summary
        summary = self.generate_summary(chunks)
        
        # Calculate overall sentiment
        overall_sentiment = TextBlob(transcript).sentiment.polarity
        
        return {
            "shoe": shoe_name,
            "reviewer": video_data['channel'],
            "categories": {
                aspect: data['description']
                for aspect, data in aspects.items()
            },
            "play_style_tags": play_styles,
            "sentiment_score": (overall_sentiment + 1) / 2,  # Normalize to 0-1
            "summary": summary,
            "entities": entities
        }

def main():
    # Load shoe data
    with open('basketball_shoes.json', 'r') as f:
        shoes_data = json.load(f)
    
    # Initialize analyzer
    YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your API key
    analyzer = ShoeReviewAnalyzer(YOUTUBE_API_KEY)
    
    # Process each shoe
    results = []
    for shoe in shoes_data:
        print(f"Processing {shoe['name']}...")
        
        # Search for videos
        videos = analyzer.search_youtube_videos(shoe['name'])
        
        for video in videos:
            # Analyze review
            analysis = analyzer.analyze_review(shoe['name'], video)
            if analysis:
                results.append(analysis)
                analyzer.processed_videos.add(video['video_id'])
            
            time.sleep(1)  # Be nice to the API
        
        time.sleep(2)  # Be nice to the API
    
    # Save results
    with open('shoe_reviews_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
