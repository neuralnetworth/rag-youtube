# FAISS-RAG Setup Guide

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 1GB for code + space for video captions
- **CPU**: Any modern processor (GPU not required for FAISS setup)

### Required API Keys

1. **OpenAI API Key**
   - Sign up at https://platform.openai.com
   - Create API key in dashboard
   - Requires payment method for usage

2. **Google API Key** (YouTube Data API v3)
   - Go to https://console.cloud.google.com
   - Create new project or select existing
   - Enable "YouTube Data API v3"
   - Create credentials (API Key)

## Installation Steps

### 1. Install UV Package Manager

UV is a fast Python package manager used by this project:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Clone and Setup Repository

```bash
# Clone repository
git clone [repository-url] rag-youtube
cd rag-youtube

# Create virtual environment and install dependencies
uv sync
```

### 3. Configure Environment

Create `.env` file from template:

```bash
cp .env.sample .env
```

Edit `.env`:
```bash
OPENAI_API_KEY=sk-...your-key-here...
GOOGLE_API_KEY=AIza...your-key-here...
```

### 4. Configure System

The `rag-youtube.conf` file controls system behavior:

```ini
[General]
llm=openai
openai_model=gpt-4.1-2025-04-14
port=8000

[Embeddings]
model=openai:text-embedding-3-small

[Search]
search_type=similarity
document_count=4
chunk_size=2500
chunk_overlap=500
```

## Data Preparation

### 1. List Channel Videos

```bash
# Using any video ID from the target channel
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/list_videos.py VIDEO_ID

# Example with SpotGamma video
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/list_videos.py jssb-yhL1R0
```

This creates:
- `channel_info.json`: Channel metadata
- `videos.json`: List of all channel videos

### 2. Download Video Captions

```bash
uv run python src/data_pipeline/download_captions.py
```

This:
- Downloads available transcripts/captions
- Saves to `captions/` directory
- Skips videos without captions
- May take 10-30 minutes for large channels

### 3. (Optional) Fetch Playlist Data

For playlist-based filtering:

```bash
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/playlist_fetcher.py
```

Creates:
- `playlists.json`: Channel playlists
- `video_playlist_mapping.json`: Video-to-playlist associations

### 4. Build FAISS Index

```bash
uv run python src/data_pipeline/document_loader_faiss.py
```

This process:
1. Reads all caption files
2. Chunks text into segments
3. Enhances metadata (categories, quality scores)
4. Generates embeddings via OpenAI
5. Builds FAISS index
6. Saves to `db/` directory

Expected output:
```
[loader] embeddings model = openai:text-embedding-3-small
[loader] splitter size/overlap = 2500/500
[loader][1/192] adding VIDEO_ID to database...
  Category: educational
  Quality: high
  Playlists: SG Options Concepts
Generating embeddings for 4 texts...
Saving FAISS index to db/faiss.index
Added 4 documents to vector store
```

## Verification

### 1. Test Basic Functionality

```bash
uv run python test/test_basic_functionality_fastapi.py
```

Expected output:
```
Testing Basic RAG Functionality (FastAPI Implementation)
================================================================
Question: What is gamma in options trading?
================================================================

Found 3 relevant documents:

1. Understanding Options Greeks (score: 0.872)
   Source: https://www.youtube.com/watch?v=...
   Preview: Gamma measures the rate of change of delta...

Answer: Gamma is the rate of change of delta with respect to...
```

### 2. Start Web Server

```bash
# Linux/macOS
./run_fastapi.sh

# Windows
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Any platform
uv run uvicorn src.api.main:app --reload
```

### 3. Verify Endpoints

Check system health:
```bash
curl http://localhost:8000/api/health
# {"status": "healthy"}
```

Check statistics:
```bash
curl http://localhost:8000/api/stats
# {
#   "total_documents": 2413,
#   "index_size": "9.5 MB",
#   "model": "gpt-4.1-2025-04-14",
#   "embeddings_model": "text-embedding-3-small"
# }
```

### 4. Test Web Interface

Open http://localhost:8000 in your browser and try:
- "What is gamma in options trading?"
- "How do gamma squeezes work?"
- "Explain 0DTE options"

## Troubleshooting

### Common Issues

#### "No module named 'faiss'"

```bash
# Ensure FAISS is installed
uv pip install faiss-cpu
```

#### "OpenAI API key not found"

Check `.env` file exists and contains:
```bash
OPENAI_API_KEY=sk-...
```

#### "No documents found"

Verify index exists:
```bash
ls -la db/
# Should show: faiss.index, documents.json, metadata.json
```

#### Slow embedding generation

- OpenAI API rate limits
- Consider batching in document loader
- Check API usage dashboard

#### High memory usage

Reduce chunk size in config:
```ini
[Search]
chunk_size=1000
chunk_overlap=200
```

### Debug Mode

Enable detailed logging:

```python
# In src/api/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Reset and Rebuild

To start fresh:

```bash
# Clear existing index
rm -rf db/

# Clear loaded tracking
rm loaded.json

# Rebuild
uv run python src/data_pipeline/document_loader_faiss.py
```

## Performance Tuning

### Chunk Size Optimization

Larger chunks:
- ✅ More context per chunk
- ✅ Fewer API calls
- ❌ May exceed token limits
- ❌ Less precise retrieval

Smaller chunks:
- ✅ More precise retrieval
- ✅ Better for specific facts
- ❌ More API calls (cost)
- ❌ May lose context

### Embedding Model Selection

`text-embedding-3-small` (default):
- 1536 dimensions
- Good balance of quality/cost
- Fast generation

`text-embedding-3-large`:
- 3072 dimensions
- Higher quality
- More expensive

### Search Parameters

```ini
[Search]
# Number of documents to retrieve
document_count=4  # Increase for more context

# Search type
search_type=similarity  # or 'mmr' for diversity

# Score threshold (if using threshold search)
score_threshold=0.7
```

## Production Deployment

### Environment Variables

Set in production:
```bash
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=AIza...
export RAG_ENV=production
```

### Process Management

Use systemd or supervisor:

```ini
# /etc/systemd/system/rag-youtube.service
[Unit]
Description=RAG YouTube API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/rag-youtube
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Reverse Proxy

Nginx configuration:
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

## Maintenance

### Regular Updates

1. **Refresh video list** (weekly):
   ```bash
   GOOGLE_API_KEY=... uv run python src/data_pipeline/list_videos.py VIDEO_ID
   ```

2. **Download new captions** (weekly):
   ```bash
   uv run python src/data_pipeline/download_captions.py
   ```

3. **Rebuild index** (monthly or after significant updates):
   ```bash
   uv run python src/data_pipeline/document_loader_faiss.py
   ```

### Backup

Important files to backup:
- `db/` - FAISS index and metadata
- `captions/` - Downloaded video transcripts
- `videos.json` - Channel video list
- `rag-youtube.conf` - Configuration
- `.env` - API keys (secure storage)

### Monitoring

Track:
- API usage (OpenAI dashboard)
- Response times
- Error rates
- Disk space (index growth)