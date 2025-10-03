import json
import re
import unicodedata
from typing import List, Dict, Any
import requests

class EmbeddingCleaner:
    def __init__(self, ollama_url: str = 'http://localhost:11434'):
        """
        Initialize the embedding cleaner with Ollama's nomic-embed-text model.
        
        Args:
            ollama_url: URL of the Ollama server
        """
        self.ollama_url = ollama_url
        self.model_name = 'nomic-embed-text'
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing emojis and extraneous special characters.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned text with only plain text characters
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove emojis using unicode categories
        # Emojis are typically in these unicode categories
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+", 
            flags=re.UNICODE
        )
        
        # Remove emojis
        text = emoji_pattern.sub('', text)
        
        # Remove other problematic unicode characters but keep basic punctuation
        # Keep: letters, numbers, basic punctuation, whitespace
        cleaned_chars = []
        for char in text:
            cat = unicodedata.category(char)
            # Keep letters (L*), numbers (N*), punctuation (P*), whitespace (Z*), and symbols (S*) that are common
            if (cat.startswith('L') or  # Letters
                cat.startswith('N') or  # Numbers
                cat.startswith('Z') or  # Whitespace
                char in '.,!?;:()[]{}"\'-/\\@#$%^&*+=<>|`~_'):  # Common punctuation and symbols
                cleaned_chars.append(char)
        
        text = ''.join(cleaned_chars)
        
        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove any remaining control characters
        text = ''.join(char for char in text if unicodedata.category(char) != 'Cc')
        
        return text
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text using Ollama's nomic-embed-text model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        if not text.strip():
            # Return zero embedding for empty text (nomic-embed-text has 768 dimensions)
            return [0.0] * 768
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/embeddings',
                json={
                    'model': self.model_name,
                    'prompt': text
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['embedding']
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating embedding: {e}")
            # Return zero embedding on error
            return [0.0] * 768
    
    def process_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single entry by cleaning text and re-embedding.
        
        Args:
            entry: Dictionary containing the entry data
            
        Returns:
            Processed entry with cleaned text and new embedding
        """
        processed_entry = entry.copy()
        
        # Clean the main text field
        if 'text' in entry:
            original_text = entry['text']
            cleaned_text = self.clean_text(original_text)
            processed_entry['text'] = cleaned_text
            
            # Generate new embedding for cleaned text
            new_embedding = self.generate_embedding(cleaned_text)
            processed_entry['embedding'] = new_embedding
            
            # Add metadata about the cleaning process
            if 'metadata' not in processed_entry:
                processed_entry['metadata'] = {}
            
            processed_entry['metadata']['cleaned'] = True
            processed_entry['metadata']['original_length'] = len(original_text)
            processed_entry['metadata']['cleaned_length'] = len(cleaned_text)
        
        return processed_entry
    
        
    def process_file(self, input_file: str, output_file: str) -> None:
        """
        Process the entire embeddings file.
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output JSON file
        """
        try:
            # Read the input file
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"Loaded {len(data) if isinstance(data, list) else 1} entries from {input_file}")
            
            # Process the data
            if isinstance(data, list):
                # Handle array of entries
                processed_data = []
                for i, entry in enumerate(data):
                    print(f"Processing entry {i + 1}/{len(data)}...")
                    processed_entry = self.process_entry(entry)
                    processed_data.append(processed_entry)
            else:
                # Handle single entry
                print("Processing single entry...")
                processed_data = self.process_entry(data)
            
            # Write to output file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully processed and saved to {output_file}")
            
        except FileNotFoundError:
            print(f"Error: Could not find input file {input_file}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {input_file}: {e}")
        except Exception as e:
            print(f"Error processing file: {e}")


def main():
    """
    Main function to run the embedding cleaner.
    """
    # Initialize the cleaner
    cleaner = EmbeddingCleaner()
    
    # Process the file
    input_file = 'embeddings.json'
    output_file = 'cleanEmbeddings.json'
    
    print("Starting embedding cleaning process...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Using model: {cleaner.model_name}")
    print("-" * 50)
    
    cleaner.process_file(input_file, output_file)


if __name__ == "__main__":
    main()