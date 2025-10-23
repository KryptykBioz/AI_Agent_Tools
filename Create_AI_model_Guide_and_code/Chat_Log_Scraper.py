# ============================================================================
# FILE: 1b_scrape_chat_logs.py
# Scrape chat logs alongside video transcripts
# ============================================================================

import json
from pathlib import Path
from tqdm import tqdm
import time
from datetime import datetime

# YouTube Chat Scraping
try:
    from chat_downloader import ChatDownloader
    CHAT_DOWNLOADER_AVAILABLE = True
except ImportError:
    CHAT_DOWNLOADER_AVAILABLE = False
    print("Warning: chat-downloader not installed. Install with: pip install chat-downloader")

# Twitch Chat Scraping
try:
    from TwitchDownloaderPython import TwitchDownloader
    TWITCH_DOWNLOADER_AVAILABLE = True
except ImportError:
    TWITCH_DOWNLOADER_AVAILABLE = False
    print("Warning: TwitchDownloaderPython not installed")


class ChatLogScraper:
    def __init__(self, output_dir="data/raw/chats"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def scrape_youtube_chat(self, video_id, output_file=None):
        """
        Scrape YouTube live chat replay
        Requires: pip install chat-downloader
        """
        if not CHAT_DOWNLOADER_AVAILABLE:
            print("chat-downloader not available. Skipping chat scraping.")
            return None
        
        if output_file is None:
            output_file = self.output_dir / f"yt_{video_id}_chat.json"
        
        try:
            url = f'https://youtube.com/watch?v={video_id}'
            chat = ChatDownloader().get_chat(url)
            
            messages = []
            for message in chat:
                messages.append({
                    'timestamp': message.get('time_in_seconds', 0),
                    'author': message.get('author', {}).get('name', 'Unknown'),
                    'message': message.get('message', ''),
                    'time_text': message.get('time_text', '')
                })
            
            # Save chat log
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            print(f"Scraped {len(messages)} chat messages for {video_id}")
            return messages
            
        except Exception as e:
            print(f"Error scraping chat for {video_id}: {e}")
            return None
    
    def scrape_twitch_chat(self, video_id, output_file=None):
        """
        Scrape Twitch VOD chat
        Requires: TwitchDownloader CLI
        """
        if output_file is None:
            output_file = self.output_dir / f"twitch_{video_id}_chat.json"
        
        try:
            import subprocess
            
            # Using TwitchDownloader CLI
            cmd = [
                'TwitchDownloaderCLI',
                'chatdownload',
                '--id', video_id,
                '--output', str(output_file),
                '--format', 'json'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Load and parse
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = []
            for comment in data.get('comments', []):
                messages.append({
                    'timestamp': comment.get('content_offset_seconds', 0),
                    'author': comment.get('commenter', {}).get('display_name', 'Unknown'),
                    'message': comment.get('message', {}).get('body', ''),
                    'time_text': str(comment.get('content_offset_seconds', 0))
                })
            
            print(f"Scraped {len(messages)} chat messages for Twitch VOD {video_id}")
            return messages
            
        except Exception as e:
            print(f"Error scraping Twitch chat for {video_id}: {e}")
            return None
    
    def align_chat_with_transcript(self, chat_messages, transcript_data, time_window=10):
        """
        Align chat messages with transcript segments
        Creates conversational pairs: chat -> streamer response
        
        Args:
            chat_messages: List of chat messages with timestamps
            transcript_data: Transcript with timestamps
            time_window: Seconds to look ahead for streamer response
        """
        conversations = []
        
        # Sort both by timestamp
        chat_sorted = sorted(chat_messages, key=lambda x: x['timestamp'])
        
        for i, chat_msg in enumerate(chat_sorted):
            chat_time = chat_msg['timestamp']
            chat_text = chat_msg['message'].strip()
            
            # Skip very short messages
            if len(chat_text) < 5:
                continue
            
            # Find transcript segments within time window after this chat
            response_candidates = []
            
            for transcript_segment in transcript_data:
                seg_time = transcript_segment.get('timestamp', 0)
                
                # Look for responses within time_window seconds after chat
                if chat_time < seg_time <= chat_time + time_window:
                    response_candidates.append(transcript_segment['text'])
            
            if response_candidates:
                # Combine responses in time window
                streamer_response = ' '.join(response_candidates).strip()
                
                conversations.append({
                    'chat_message': chat_text,
                    'chat_author': chat_msg['author'],
                    'streamer_response': streamer_response,
                    'timestamp': chat_time
                })
        
        return conversations
    
    def create_conversational_dataset(self, video_ids, transcript_dir="data/raw"):
        """
        Create a dataset of chat->response pairs
        """
        transcript_dir = Path(transcript_dir)
        all_conversations = []
        
        for video_id in tqdm(video_ids, desc="Processing videos"):
            # Scrape chat
            chat_messages = self.scrape_youtube_chat(video_id)
            
            if not chat_messages:
                continue
            
            # Load transcript
            transcript_file = transcript_dir / f"{video_id}_transcript.json"
            if not transcript_file.exists():
                print(f"Transcript not found for {video_id}")
                continue
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
            
            # Align chat with transcript
            conversations = self.align_chat_with_transcript(
                chat_messages,
                transcript_data
            )
            
            all_conversations.extend(conversations)
            
            time.sleep(1)  # Rate limiting
        
        # Save conversational dataset
        output_file = self.output_dir.parent / "conversational_data.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in all_conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        print(f"\nCreated {len(all_conversations)} conversational pairs")
        print(f"Saved to: {output_file}")
        
        return all_conversations


class ConversationalFormatter:
    """
    Format conversational data for training
    """
    
    @staticmethod
    def format_as_chat(conversation):
        """Format as chat-style training data"""
        return {
            'text': f"Chat: {conversation['chat_message']}\nStreamer: {conversation['streamer_response']}",
            'source': 'conversational'
        }
    
    @staticmethod
    def format_as_instruction(conversation):
        """Format as instruction-following data"""
        return {
            'instruction': conversation['chat_message'],
            'response': conversation['streamer_response'],
            'source': 'conversational'
        }
    
    @staticmethod
    def format_with_system_prompt(conversation, system_prompt):
        """Format with system prompt for chat models"""
        return {
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': conversation['chat_message']},
                {'role': 'assistant', 'content': conversation['streamer_response']}
            ],
            'source': 'conversational'
        }


# ============================================================================
# FILE: 1c_enhanced_scraper.py  
# Enhanced version that gets both transcript AND chat in one pass
# ============================================================================

class EnhancedStreamScraper:
    """
    Scrapes both transcript and chat, then aligns them
    """
    
    def __init__(self, output_dir="data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chat_scraper = ChatLogScraper(output_dir=output_dir / "chats")
    
    def scrape_complete_stream(self, video_id, platform='youtube'):
        """
        Scrape both transcript and chat for a stream
        """
        print(f"\nProcessing {platform} video: {video_id}")
        
        # 1. Get transcript (using methods from 1_scrape_youtube.py)
        transcript = self._get_transcript(video_id, platform)
        
        if not transcript:
            print(f"Failed to get transcript for {video_id}")
            return None
        
        # 2. Get chat log
        if platform == 'youtube':
            chat_messages = self.chat_scraper.scrape_youtube_chat(video_id)
        elif platform == 'twitch':
            chat_messages = self.chat_scraper.scrape_twitch_chat(video_id)
        else:
            print(f"Unknown platform: {platform}")
            return None
        
        if not chat_messages:
            print(f"No chat messages found for {video_id}")
            return None
        
        # 3. Align chat with transcript
        conversations = self.chat_scraper.align_chat_with_transcript(
            chat_messages,
            transcript
        )
        
        print(f"Created {len(conversations)} conversational pairs")
        
        return {
            'video_id': video_id,
            'platform': platform,
            'transcript': transcript,
            'chat_messages': chat_messages,
            'conversations': conversations
        }
    
    def _get_transcript(self, video_id, platform):
        """Get transcript with timestamps"""
        if platform == 'youtube':
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Format with timestamps
                return [{
                    'timestamp': entry['start'],
                    'text': entry['text'],
                    'duration': entry['duration']
                } for entry in transcript_list]
                
            except Exception as e:
                print(f"Error getting transcript: {e}")
                return None
        
        return None
    
    def batch_scrape_with_chat(self, video_ids, platform='youtube'):
        """
        Scrape multiple videos with both transcript and chat
        """
        all_data = []
        
        for video_id in tqdm(video_ids, desc=f"Scraping {platform} streams"):
            data = self.scrape_complete_stream(video_id, platform)
            if data:
                all_data.append(data)
            time.sleep(2)  # Rate limiting
        
        # Save combined dataset
        output_file = self.output_dir / f"{platform}_complete_data.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\nSaved complete data for {len(all_data)} videos")
        return all_data


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Install required packages first:
    # pip install chat-downloader
    # For Twitch: Download TwitchDownloader CLI from GitHub
    
    # Method 1: Scrape chat logs for existing transcripts
    print("=== Method 1: Chat Log Scraping ===")
    scraper = ChatLogScraper()
    
    video_ids = [
        # Add your video IDs here
    ]
    
    conversations = scraper.create_conversational_dataset(video_ids)
    
    # Method 2: Complete scraping (transcript + chat together)
    print("\n=== Method 2: Enhanced Scraping ===")
    enhanced_scraper = EnhancedStreamScraper()
    
    complete_data = enhanced_scraper.batch_scrape_with_chat(
        video_ids,
        platform='youtube'
    )
    
    # Format for training
    formatter = ConversationalFormatter()
    
    training_examples = []
    for item in complete_data:
        for conv in item['conversations']:
            # Choose your preferred format
            example = formatter.format_as_chat(conv)
            # or: example = formatter.format_as_instruction(conv)
            training_examples.append(example)
    
    # Save formatted training data
    with open('data/processed/conversational_training.jsonl', 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\nCreated {len(training_examples)} training examples with chat context!")