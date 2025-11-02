# Vinted Fashion Recommender Chrome Extension

An AI-powered Chrome extension that uses CLIP embeddings to provide semantic fashion search on Vinted.fr. Users can describe what they're looking for in natural language and find visually similar items.

## 🚀 Features

- **AI-Powered Search**: Uses CLIP model to understand both text queries and product images
- **Real-time Results**: Search through thousands of fashion items with instant results
- **Natural Language**: Describe what you want in plain English (e.g., "red floral summer dress")
- **Visual Similarity**: Find items that look similar to your description
- **Seamless Integration**: Works directly on Vinted.fr pages
- **Daily Updates**: Automatically refreshes database with new items

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chrome        │    │   FastAPI       │    │   ChromaDB      │
│   Extension     │◄──►│   Backend       │◄──►│   Vector Store  │
│                 │    │                 │    │                 │
│ • Popup UI      │    │ • Search API    │    │ • Embeddings   │
│ • Content Script│    │ • Health Check  │    │ • Metadata     │
│ • Background    │    │ • CORS Support  │    │ • Persistence  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   CLIP Model    │
                       │                 │
                       │ • Text Encoder  │
                       │ • Image Encoder │
                       │ • Similarity    │
                       └─────────────────┘
```

## 📁 Project Structure

```
ai-search-extension/
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI app with search endpoints
│   ├── scraper.py             # Vinted scraping and embedding logic
│   ├── scrapper.py            # Original scraping functions
│   ├── config.py              # Configuration settings
│   ├── refresh_database.py    # Daily refresh script
│   ├── setup_cron.sh          # Cron setup script
│   ├── requirements.txt        # Python dependencies
│   └── data/                  # ChromaDB storage
├── extension/                 # Chrome extension
│   ├── manifest.json          # Extension manifest
│   ├── popup.html             # Extension popup UI
│   ├── popup.js               # Popup functionality
│   ├── content.js             # Content script for Vinted pages
│   ├── content.css            # Styling for injected UI
│   ├── background.js          # Service worker
│   └── icons/                 # Extension icons
├── model/                     # CLIP model files
└── README.md                  # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.9+
- Chrome browser
- 4GB+ RAM (for CLIP model)
- 2GB+ disk space (for model and embeddings)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download CLIP model (if not already present)
# The model should be in ./model/ directory
# You can download it from Hugging Face or use your existing model

# Test the scraper
python scraper.py --search "red dress" --top-k 3

# Populate database with initial data
python scraper.py --refresh --catalog-ids 10 --max-pages 5

# Start the API server
python main.py
```

The API will be available at `http://localhost:8000`

### 2. Chrome Extension Setup

```bash
# Navigate to extension directory
cd extension

# Add your extension icons to the icons/ directory:
# - icon16.png (16x16)
# - icon32.png (32x32) 
# - icon48.png (48x48)
# - icon128.png (128x128)
```

**Load Extension in Chrome:**

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/` directory
5. The extension should appear in your extensions list

### 3. Daily Refresh Setup

```bash
# Navigate to backend directory
cd backend

# Run the cron setup script
./setup_cron.sh

# Or manually add to crontab:
# 0 2 * * * cd /path/to/backend && python refresh_database.py
```

## 🚀 Usage

### For Users

1. **Install the Extension**: Load the unpacked extension in Chrome
2. **Visit Vinted**: Go to any page on vinted.fr
3. **Search**: 
   - Click the floating search button (🔍) in bottom-right corner
   - Or use the extension popup (click extension icon in toolbar)
4. **Describe**: Enter your search in natural language:
   - "red floral summer dress"
   - "vintage denim jacket"
   - "black leather boots"
   - "casual white sneakers"
5. **Browse Results**: Click on results to open them in new tabs

### For Developers

**API Endpoints:**

```bash
# Health check
curl http://localhost:8000/api/health

# Search for items
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "red dress", "top_k": 5}'

# Get database stats
curl http://localhost:8000/api/stats
```

**Manual Database Refresh:**

```bash
# Dry run (see what would be done)
python refresh_database.py --dry-run

# Full refresh
python refresh_database.py --catalog-ids 10 11 12 --max-pages 10

# Check logs
tail -f logs/refresh.log
```

## 🔧 Configuration

### Backend Configuration (`backend/config.py`)

```python
# Model and Database
MODEL_PATH = "./model"
CHROMA_DB_PATH = "./data/chroma"

# Vinted API
CATALOG_IDS = {
    "dresses": 10,
    "tops": 11,
    "skirts": 12,
    "pants": 13,
    "shoes": 14,
    "accessories": 15
}

# Scraping Settings
MAX_PAGES_PER_SCRAPE = 20
BATCH_SIZE = 6
```

### Extension Configuration

The extension settings can be modified in the popup:
- Backend URL (default: http://localhost:8000)
- Max results per search (default: 5)

## 📊 Performance

- **Model Loading**: ~2-3 seconds on first startup
- **Search Speed**: ~100-500ms per query
- **Database Size**: ~1-2GB for 10,000 items
- **Memory Usage**: ~2-4GB with model loaded
- **Daily Refresh**: ~5-15 minutes depending on items

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check if model directory exists
ls -la model/

# Check Python dependencies
pip list | grep -E "(sentence-transformers|chromadb|fastapi)"

# Check logs
python main.py 2>&1 | tee backend.log
```

**Extension not working:**
- Check if backend is running: `curl http://localhost:8000/api/health`
- Check browser console for errors
- Verify extension permissions in Chrome
- Check if backend URL is correct in extension settings

**Search returns no results:**
- Check if database has items: `curl http://localhost:8000/api/stats`
- Run manual refresh: `python refresh_database.py`
- Check if model is loaded properly

**Daily refresh not working:**
- Check cron job: `crontab -l`
- Check logs: `tail -f logs/refresh.log`
- Test manually: `python refresh_database.py --dry-run`

### Logs

- **Backend logs**: Check console output or redirect to file
- **Refresh logs**: `logs/refresh.log`
- **Cron logs**: `logs/cron.log`
- **Extension logs**: Chrome DevTools Console

## 🔒 Security & Privacy

- **No Data Collection**: Extension doesn't collect user data
- **Local Processing**: All AI processing happens on your server
- **No Tracking**: No analytics or user tracking
- **Open Source**: Full source code available for review

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and demonstration purposes. Please respect Vinted's Terms of Service when scraping their data.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test individual components (backend API, extension, database)
4. Create an issue with detailed error information

## 🎯 Future Enhancements

- [ ] Multi-language support (Vinted operates in multiple countries)
- [ ] Advanced filters (price range, size, brand)
- [ ] "More like this" feature for individual items
- [ ] User preferences and search history
- [ ] Mobile app version
- [ ] Real-time notifications for new similar items
