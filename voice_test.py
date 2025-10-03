import pyttsx3
import time

def demonstrate_voices():
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    
    # Get all available voices
    voices = engine.getProperty('voices')
    
    # Text to be spoken in each voice
    demo_text = "Hello! This is a demonstration of this voice. My name is {name} and I'm ready to help you."
    
    print(f"Found {len(voices)} voices on this system:\n")
    
    # Loop through each voice
    for i, voice in enumerate(voices, 1):
        print(f"Voice {i}:")
        print(f"  ID: {voice.id}")
        print(f"  Name: {voice.name}")
        print(f"  Languages: {voice.languages}")
        print(f"  Gender: {voice.gender if hasattr(voice, 'gender') else 'Unknown'}")
        print(f"  Age: {voice.age if hasattr(voice, 'age') else 'Unknown'}")
        print("-" * 50)
        
        # Set the voice
        engine.setProperty('voice', voice.id)
        
        # Optionally adjust speech rate (words per minute)
        engine.setProperty('rate', 200)  # Default is usually around 200
        
        # Optionally adjust volume (0.0 to 1.0)
        engine.setProperty('volume', 0.9)
        
        # Create personalized text with the voice name
        personalized_text = demo_text.format(name=voice.name.split(' - ')[0])
        
        print(f"Now speaking with: {voice.name}")
        print(f"Text: {personalized_text}")
        
        # Speak the text
        engine.say(personalized_text)
        engine.runAndWait()  # Wait for speech to complete
        
        # Pause between voices for clarity
        time.sleep(1)
        
        print("\n" + "="*60 + "\n")
    
    print("Voice demonstration complete!")

def interactive_voice_selector():
    """Allow user to select and test specific voices interactively"""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print("\nInteractive Voice Selector")
    print("="*30)
    
    while True:
        print("\nAvailable voices:")
        for i, voice in enumerate(voices):
            print(f"{i+1}. {voice.name}")
        
        print(f"{len(voices)+1}. Exit")
        
        try:
            choice = int(input(f"\nSelect a voice (1-{len(voices)+1}): ")) - 1
            
            if choice == len(voices):
                break
            elif 0 <= choice < len(voices):
                selected_voice = voices[choice]
                engine.setProperty('voice', selected_voice.id)
                
                custom_text = input("Enter text to speak (or press Enter for default): ")
                if not custom_text.strip():
                    custom_text = f"Hello! This is {selected_voice.name} speaking."
                
                print(f"\nSpeaking with {selected_voice.name}...")
                engine.say(custom_text)
                engine.runAndWait()
            else:
                print("Invalid selection. Please try again.")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break

def get_voice_info():
    """Display detailed information about available voices"""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print("Detailed Voice Information")
    print("="*40)
    
    for i, voice in enumerate(voices, 1):
        print(f"\nVoice {i}:")
        print(f"  ID: {voice.id}")
        print(f"  Name: {voice.name}")
        
        # Handle languages (can be None or a list)
        if voice.languages:
            if isinstance(voice.languages, list):
                langs = ', '.join([str(lang) for lang in voice.languages])
            else:
                langs = str(voice.languages)
            print(f"  Languages: {langs}")
        else:
            print(f"  Languages: Not specified")
            
        # Handle optional attributes
        if hasattr(voice, 'gender'):
            print(f"  Gender: {voice.gender}")
        if hasattr(voice, 'age'):
            print(f"  Age: {voice.age}")

def main():
    print("Text-to-Speech Voice Demonstration")
    print("="*40)
    
    try:
        while True:
            print("\nChoose an option:")
            print("1. Demonstrate all voices")
            print("2. Interactive voice selector")
            print("3. Show voice information only")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                demonstrate_voices()
            elif choice == '2':
                interactive_voice_selector()
            elif choice == '3':
                get_voice_info()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-4.")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure pyttsx3 is installed: pip install pyttsx3")

if __name__ == "__main__":
    main()