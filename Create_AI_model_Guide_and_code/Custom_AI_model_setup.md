# VTuber AI Model Training System

Complete pipeline for training a custom 1B parameter AI model on VTuber and gaming content, optimized for dual GPU setup (Intel Arc B580 + Nvidia RTX 5060 Ti).

## Hardware Requirements

- **GPUs**: Intel Arc B580 (12GB) + Nvidia RTX 5060 Ti (16GB)
- **RAM**: 32GB minimum
- **Storage**: 200GB+ free space
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows with WSL2

## Quick Start

### 1. Initial Setup

```bash
# Clone or download all files to a directory
cd vtuber-model-training

# Make scripts executable (Linux/Mac)
chmod +x setup_environment.sh run_pipeline.sh

# Run setup
bash setup_environment.sh
```

### 2. Configure Data Sources

Edit the data source URLs in the scraping scripts:

**1_scrape_youtube.py**:
```python
channels = [
    "https://www.youtube.com/@YourFavoriteVTuber",
]

playlists = [
    "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID",
]
```

**2_scrape_guides.py**:
```python
guide_urls = [
    "https://gamewiki.example.com/Guide1",
    "https://gamewiki.example.com/Guide2",
]
```

### 3. Run the Pipeline

```bash
# Activate environment
source vtuber_env/bin/activate

# Run complete pipeline
bash run_pipeline.sh

# OR run steps individually:
python 1_scrape_youtube.py
python 2_scrape_guides.py
python 3_preprocess_data.py
python 4_train_model.py
python 5_test_model.py
python 6_convert_to_gguf.py
python 7_create_ollama_model.py
```

### 4. Use Your Model

```bash
# With Ollama CLI
ollama run vtuber-model

# With Python interface
python 8_ollama_integration.py
```

## Project Structure

```
vtuber-model-training/
├── data/
│   ├── raw/              # Scraped transcripts and guides
│   └── processed/        # Preprocessed training data
├── models/
│   ├── checkpoints/      # Training checkpoints
│   ├── final/            # Final trained model
│   └── gguf/             # GGUF format models
├── logs/                 # Training logs
├── llama.cpp/            # GGUF conversion tools
├── 1_scrape_youtube.py
├── 2_scrape_guides.py
├── 3_preprocess_data.py
├── 4_train_model.py
├── 5_test_model.py
├── 6_convert_to_gguf.py
├── 7_create_ollama_model.py
├── 8_ollama_integration.py
├── requirements.txt
├── config.yaml
├── setup_environment.sh
├── run_pipeline.sh
└── README.md
```

## Detailed Instructions

### Data Collection

**Minimum dataset size**: 10,000+ text samples (aim for 50MB+ of text)

**Sources**:
- VTuber livestream transcripts
- Gaming guide wikis
- Twitch VOD transcriptions
- Gaming forum discussions

### Training

The training script uses:
- **Base model**: microsoft/phi-2 (2.7B parameters)
- **Method**: LoRA fine-tuning (efficient, ~1B effective parameters)
- **Training time**: 4-8 hours on dual GPU setup
- **Memory usage**: ~20GB VRAM total

**Monitor training**:
```bash
tensorboard --logdir models/checkpoints/logs
```

### GPU Configuration

The system automatically uses both GPUs:
- PyTorch's `device_map="auto"` distributes model layers
- Uses 8-bit quantization to fit in memory
- Supports mixed precision (FP16) training

**If you encounter OOM errors**:
1. Reduce `per_device_batch_size` in `4_train_model.py` to 1
2. Increase `gradient_accumulation_steps` to 16
3. Reduce `max_sequence_length` to 512

### Model Selection

You can change the base model in `4_train_model.py`:

```python
trainer = VTuberModelTrainer(
    base_model="microsoft/phi-2"  # Change this
)
```

**Options**:
- `"microsoft/phi-2"` - 2.7B params, best quality (recommended)
- `"TinyLlama/TinyLlama-1.1B-Chat-v1.0"` - 1.1B params, faster
- `"stabilityai/stablelm-2-1_6b"` - 1.6B params, good balance

## Troubleshooting

### CUDA Out of Memory
- Reduce batch size to 1
- Increase gradient accumulation
- Use smaller base model
- Enable CPU offloading

### Slow Training
- Check GPU utilization: `nvidia-smi`
- Ensure both GPUs are being used
- Verify FP16 is enabled
- Use faster storage (NVMe SSD)

### Poor Model Quality
- Collect more training data (50MB+ text minimum)
- Increase training epochs to 5
- Clean data more thoroughly
- Adjust temperature during inference

### Intel Arc GPU Not Detected
The Arc B580 may need specific drivers for PyTorch:
```bash
# Install Intel Extension for PyTorch
pip install intel-extension-for-pytorch
```

If issues persist, training will default to the Nvidia GPU only.

## Legal & Ethical Considerations

1. **Copyright**: Only scrape content you have rights to use
2. **Terms of Service**: Respect YouTube, Twitch, and website ToS
3. **Rate Limiting**: Scripts include delays to avoid overwhelming servers
4. **Attribution**: Keep track of data sources
5. **Content Filtering**: Review outputs for inappropriate content

## Performance Optimization

### For Faster Training:
- Use NVMe SSD for data storage
- Increase `dataloader_num_workers` in training args
- Enable gradient checkpointing
- Use DeepSpeed for advanced optimization

### For Better Quality:
- Collect 100MB+ of high-quality text
- Train for 5-10 epochs
- Use larger base model (7B) if you have more VRAM
- Fine-tune learning rate based on loss curves

## Integration with VTuber Software

Use the Ollama API to integrate with:
- OBS Studio (via browser source + web server)
- VTube Studio (via WebSocket)
- Custom TTS systems
- Chat platforms (Twitch, YouTube, Discord)

Example integration code in `8_ollama_integration.py`.

## Expected Training Timeline

1. **Data Collection**: 2-4 hours (depending on amount of content)
2. **Data Preprocessing**: 10-30 minutes
3. **Model Training**: 4-8 hours
4. **Testing**: 10 minutes
5. **GGUF Conversion**: 5-10 minutes
6. **Ollama Setup**: 2 minutes

**Total**: ~6-12 hours for complete pipeline

## File Sizes

- Raw data: 50-500MB (text)
- Processed data: 50-500MB
- Training checkpoints: 2-5GB
- Final model: 2-3GB
- GGUF models: 800MB-2GB (depending on quantization)

## Support & Resources

- **Ollama**: https://ollama.ai
- **Transformers**: https://huggingface.co/docs/transformers
- **PEFT/LoRA**: https://huggingface.co/docs/peft
- **llama.cpp**: https://github.com/ggerganov/llama.cpp

## Tips for Best Results

1. **Quality over Quantity**: 50MB of high-quality, on-topic data beats 500MB of mixed content
2. **Clean Transcripts**: Remove music lyrics, off-topic segments, and errors
3. **Diverse Sources**: Mix different VTubers and game types for versatility
4. **Test Early**: Run `5_test_model.py` after just 1 epoch to check progress
5. **Save Checkpoints**: Training crashes happen - checkpoints are automatic
6. **Monitor Logs**: Watch TensorBoard to catch issues early

## Common Questions

**Q: Can I use only one GPU?**  
A: Yes! The code will work with a single GPU. Just slower training.

**Q: How much data do I really need?**  
A: Minimum 10,000 samples (~50MB text). More is better, but quality matters most.

**Q: Can I pause and resume training?**  
A: Yes! Training automatically saves checkpoints. Restart `4_train_model.py` to continue.

**Q: Will this work on Windows?**  
A: Yes, but WSL2 is recommended. Native Windows works but may have issues with some scripts.

**Q: How do I update the model with new data?**  
A: Add new data to `data/raw/`, run `3_preprocess_data.py`, then resume training from last checkpoint.

## License

This training pipeline is provided as-is. Ensure you have appropriate rights to all training data.

## Advanced Configuration

### Custom System Prompts

Edit the system prompt in `7_create_ollama_model.py` or the Modelfile to customize personality:

```python
SYSTEM """You are [your custom personality here]..."""
```

### Hyperparameter Tuning

Key parameters to adjust in `4_train_model.py`:

```python
# For better quality (slower training)
lora_config = LoraConfig(
    r=64,  # Increase from 32
    lora_alpha=128,  # Double the r value
)

training_args = TrainingArguments(
    num_train_epochs=5,  # More epochs
    learning_rate=1e-4,  # Lower learning rate
)

# For faster training (may sacrifice quality)
lora_config = LoraConfig(
    r=16,  # Decrease from 32
    lora_alpha=32,
)

training_args = TrainingArguments(
    num_train_epochs=2,
    per_device_batch_size=4,  # If you have VRAM
)
```

### Multi-Language Support

To train on multi-language content, ensure your tokenizer supports the languages:

```python
# In 4_train_model.py, use multilingual base models:
base_model = "bigscience/bloom-1b7"  # Supports 46 languages
# or
base_model = "facebook/xglm-1.7B"  # Multilingual
```

## Deployment Options

### Option 1: Local Ollama (Recommended)
```bash
ollama run vtuber-model
```

### Option 2: Python API Server
```python
# Create simple_api.py
from flask import Flask, request, jsonify
from 8_ollama_integration import OllamaVTuberInterface

app = Flask(__name__)
vtuber = OllamaVTuberInterface()

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    response = vtuber.generate_response(user_input)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Option 3: Discord Bot Integration
```python
# Create discord_bot.py
import discord
from 8_ollama_integration import OllamaVTuberInterface

client = discord.Client(intents=discord.Intents.default())
vtuber = OllamaVTuberInterface()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!vtuber'):
        prompt = message.content[8:]  # Remove '!vtuber '
        response = vtuber.generate_response(prompt)
        await message.channel.send(response)

client.run('YOUR_BOT_TOKEN')
```

### Option 4: OBS Studio Integration
```python
# Create obs_websocket.py
from obswebsocket import obsws, requests
from 8_ollama_integration import OllamaVTuberInterface
import time

vtuber = OllamaVTuberInterface()
ws = obsws("localhost", 4444, "your_password")
ws.connect()

def update_text_source(text):
    ws.call(requests.SetTextFreetype2Properties(
        source="VTuber_Text",
        text=text
    ))

# Your chat integration logic here
# Read chat -> generate response -> update OBS text
```

## Performance Benchmarks

Expected performance on your hardware (Arc B580 + RTX 5060 Ti):

| Task | Time | Notes |
|------|------|-------|
| Scraping 1000 videos | 2-3 hours | With Whisper transcription |
| Preprocessing 100MB text | 5-10 min | Single-threaded |
| Training 1 epoch | 1.5-2.5 hours | Depends on dataset size |
| Full 3-epoch training | 4-8 hours | ~50MB dataset |
| GGUF conversion | 5-10 min | All quantization levels |
| Inference (Q4_K_M) | 20-40 tokens/sec | On single GPU |

## Troubleshooting Guide

### Issue: Training Loss Not Decreasing

**Symptoms**: Loss stays high or increases
**Solutions**:
1. Lower learning rate to 1e-4
2. Increase warmup steps to 200
3. Check data quality - may have too much noise
4. Ensure tokenizer is working correctly

### Issue: Model Outputs Gibberish

**Symptoms**: Nonsensical or repetitive text
**Solutions**:
1. Train for more epochs (5-10)
2. Increase LoRA rank (r=64)
3. Add more diverse training data
4. Adjust inference parameters (temperature, top_p)

### Issue: GPU Memory Errors

**Symptoms**: CUDA out of memory
**Solutions**:
```python
# In 4_train_model.py, modify:
per_device_batch = 1  # Reduce from 2
gradient_accumulation = 16  # Increase from 8
max_length = 512  # Reduce from 1024
```

### Issue: Slow Inference

**Symptoms**: Takes >5 seconds per response
**Solutions**:
1. Use Q4_K_M quantization (fastest)
2. Reduce `num_ctx` in Modelfile to 1024
3. Lower `max_tokens` in inference settings
4. Ensure model is loaded on GPU, not CPU

### Issue: Model Lacks Personality

**Symptoms**: Generic responses, doesn't sound like VTuber
**Solutions**:
1. Need more VTuber-specific training data
2. Strengthen system prompt
3. Train for more epochs on focused data
4. Post-process with personality-enhancing prompts

## Data Collection Best Practices

### YouTube Scraping Strategy

1. **Target specific VTuber types**:
   - Gaming-focused VTubers
   - English-speaking (or your target language)
   - Regular streamers (more consistent style)

2. **Prioritize quality**:
   - Videos with good audio quality
   - Clear speech without heavy background music
   - Gaming commentary over music streams

3. **Verify captions**:
   - Auto-generated captions have ~10-20% errors
   - Manual captions are much better
   - Whisper transcription is most accurate

### Web Scraping Ethics

```python
# Good practices in your scrapers:

# 1. Respect robots.txt
from urllib.robotparser import RobotFileParser
rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()
can_fetch = rp.can_fetch("*", url)

# 2. Rate limiting (already in scripts)
time.sleep(1)  # Wait between requests

# 3. Use proper User-Agent
headers = {
    'User-Agent': 'VTuberModelTraining/1.0 (Educational; your@email.com)'
}

# 4. Cache responses to avoid re-scraping
import requests_cache
requests_cache.install_cache('scraper_cache')
```

## Expanding the Model

### Adding More Data Sources

1. **Twitch VODs**: Modify `1_scrape_youtube.py` for Twitch
2. **Reddit/Forums**: Add scraper for gaming subreddits
3. **Game Wikis**: Expand `2_scrape_guides.py` for more sites
4. **Stream Chats**: Include chat logs for natural conversation

### Continuous Training

```bash
# After collecting new data:
python 3_preprocess_data.py  # Reprocess all data
python 4_train_model.py --resume_from_checkpoint models/checkpoints/checkpoint-XXXX
```

### Model Merging

Combine multiple specialized models:
```bash
# Using mergekit (install separately)
mergekit-merge config.yml output_dir
```

## Production Deployment Checklist

- [ ] Test model thoroughly with diverse prompts
- [ ] Set up content filtering for inappropriate outputs
- [ ] Implement rate limiting for API endpoints
- [ ] Add logging and monitoring
- [ ] Create backup of trained model
- [ ] Document model behavior and limitations
- [ ] Set up automated testing pipeline
- [ ] Consider model versioning system
- [ ] Prepare rollback strategy
- [ ] Monitor GPU/CPU usage in production

## Community & Support

For issues specific to this training pipeline:
1. Check this README first
2. Review error messages carefully
3. Search common issues in Troubleshooting section
4. Check GPU memory with `nvidia-smi`
5. Verify all dependencies are installed

For general ML/LLM questions:
- HuggingFace forums: https://discuss.huggingface.co/
- r/LocalLLaMA subreddit
- Ollama Discord server

## What's Next?

After successfully training your model:

1. **Experiment with different prompts** to find the best personality
2. **Collect user feedback** to improve training data
3. **Fine-tune on specific games** for specialized knowledge
4. **Integrate with TTS** for voice output
5. **Add RAG (Retrieval-Augmented Generation)** for real-time game info
6. **Create a web interface** for easy access
7. **Train emotion classifiers** for dynamic responses

## Credits & Acknowledgments

This training pipeline uses:
- **Transformers** by HuggingFace
- **PEFT** (Parameter-Efficient Fine-Tuning)
- **llama.cpp** by Georgi Gerganov
- **Ollama** for model deployment
- **yt-dlp** for YouTube downloads
- **Whisper** by OpenAI for transcription

---

**Happy Training! 🎮🎙️**

Remember: The key to a great VTuber AI is not just the model architecture, but the quality and relevance of your training data. Start small, iterate often, and have fun with it!