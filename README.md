# Student Browser Monitor with AI Agent

A comprehensive Python system that monitors student browser activity and provides intelligent guidance using AI. The system consists of a Firefox browser monitor that logs activity, takes screenshots, and an AI agent that analyzes behavior and takes appropriate actions.

## Features

### Browser Monitor (`browser_monitor.py`)
- Launches Firefox browser in normal window mode
- Logs current URL and timestamp every 5 seconds to `logs.csv`
- Takes screenshots and saves them in `screenshots/` folder
- Performs OCR on screenshots to extract page content
- Provides functions to open new tabs, close tabs, and show notifications
- Tracks tab count and page titles

### AI Agent (`ai_agent.py`)
- Uses LangChain and OpenAI to analyze student behavior
- Categorizes websites as educational, distracting, or inappropriate
- Provides encouragement for good study habits
- Warns students spending too much time on distracting sites
- Intervenes for inappropriate content by redirecting to educational sites
- Uses web search to find appropriate educational alternatives
- Logs all agent decisions to `agent_logs.csv`

### Combined System (`student_monitor.py`)
- Runs both browser monitor and AI agent together
- Multi-threaded architecture for concurrent monitoring and AI analysis
- Configurable monitoring intervals
- Graceful shutdown handling

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install system dependencies:**
   - **Firefox**: Download from [Mozilla Firefox](https://www.mozilla.org/firefox/)
   - **GeckoDriver**: Download from [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
   - **Tesseract OCR**: 
     - macOS: `brew install tesseract`
     - Ubuntu: `sudo apt-get install tesseract-ocr`
     - Windows: Download from [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

3. **Set up OpenAI API key:**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## Usage

### Quick Start (Recommended)
Run the combined system:
```bash
python student_monitor.py
```

### Individual Components

**Browser Monitor Only:**
```bash
python browser_monitor.py --url https://www.google.com --interval 5
```

**AI Agent Only:**
```bash
python ai_agent.py --interval 30
```

### Command Line Options

**Student Monitor:**
```bash
python student_monitor.py [OPTIONS]
```

Options:
- `--headless`: Launch browser in headless mode
- `--url`, `-u`: Starting URL (default: https://www.google.com)
- `--monitor-interval`, `-m`: Browser monitoring interval in seconds (default: 5)
- `--agent-interval`, `-a`: AI agent check interval in seconds (default: 30)
- `--api-key`, `-k`: OpenAI API key

**Browser Monitor:**
```bash
python browser_monitor.py [OPTIONS]
```

Options:
- `--headless`: Launch browser in headless mode
- `--url`, `-u`: Starting URL (default: https://www.google.com)
- `--interval`, `-i`: Monitoring interval in seconds (default: 5)

**AI Agent:**
```bash
python ai_agent.py [OPTIONS]
```

Options:
- `--interval`, `-i`: Agent check interval in seconds (default: 30)
- `--api-key`, `-k`: OpenAI API key

## How It Works

### 1. Browser Monitoring
- Firefox browser launches in normal window mode
- Every 5 seconds (configurable), the system:
  - Logs current URL, timestamp, and page title
  - Takes a screenshot of the current page
  - Performs OCR to extract text content
  - Saves all data to `logs.csv`

### 2. AI Analysis
- Every 30 seconds (configurable), the AI agent:
  - Reads recent activity from `logs.csv`
  - Categorizes the current website
  - Analyzes time spent on the site
  - Determines appropriate action

### 3. AI Actions

**Encouragement (Educational Sites):**
- Triggers after 5+ minutes on educational sites
- Shows positive notifications like "Great work! You've been studying for 5 minutes."

**Warnings (Distracting Sites):**
- Triggers after 10+ minutes on distracting sites
- Shows gentle reminders like "You've been on this site for 10 minutes. Consider getting back to your studies."

**Intervention (Inappropriate Sites):**
- Triggers after 30+ seconds on inappropriate sites
- Closes the current tab
- Searches for educational alternatives
- Opens a new tab with appropriate content

## File Structure

```
├── browser_monitor.py      # Browser monitoring script
├── ai_agent.py            # AI agent script
├── student_monitor.py     # Combined system
├── requirements.txt       # Python dependencies
├── logs.csv              # Browser activity logs
├── agent_logs.csv        # AI agent decision logs
└── screenshots/          # Screenshot storage folder
    ├── screenshot_1234567890.png
    └── ...
```

## Log Files

### `logs.csv` (Browser Activity)
- `timestamp`: Human-readable timestamp
- `timestamp_seconds`: Unix timestamp
- `url`: Current page URL
- `title`: Page title
- `screenshot_path`: Path to screenshot file
- `ocr_summary`: Extracted text from screenshot
- `tab_count`: Number of open tabs

### `agent_logs.csv` (AI Decisions)
- `timestamp`: Decision timestamp
- `current_url`: URL being analyzed
- `site_category`: Site classification
- `time_on_site`: Time spent on site
- `recommendation`: AI recommendation
- `message`: Action message
- `encouragement_count`: Total encouragements given
- `warning_count`: Total warnings given
- `intervention_count`: Total interventions

## Site Categories

### Educational Sites
- IXL, Khan Academy, Duolingo, Codecademy
- Brilliant, Coursera, edX, Udemy
- Wikipedia, Wolfram Alpha, Desmos, GeoGebra
- Scratch, Typing.com, Mathway, Symbolab

### Distracting Sites
- YouTube, Facebook, Instagram, TikTok
- Twitter, Reddit, Netflix, Hulu
- Twitch, Discord, Snapchat, Pinterest

### Inappropriate Sites
- Sites containing: porn, gambling, violence, drugs, alcohol, dating, adult, mature, explicit

## Customization

### Adding New Sites
Edit the site lists in `ai_agent.py`:
```python
self.educational_sites = [
    'ixl.com', 'khanacademy.org', 
    # Add your sites here
]

self.distracting_sites = [
    'youtube.com', 'facebook.com',
    # Add your sites here
]
```

### Adjusting Thresholds
Modify action thresholds in `ai_agent.py`:
```python
self.encouragement_threshold = 300  # 5 minutes
self.distraction_threshold = 600    # 10 minutes
self.inappropriate_threshold = 30   # 30 seconds
```

### Custom Notifications
Modify notification messages in `ai_agent.py`:
```python
analysis['message'] = "Your custom encouragement message here!"
```

## Troubleshooting

### Common Issues

1. **GeckoDriver not found:**
   - Download GeckoDriver and add to PATH
   - Or place in the same directory as scripts

2. **Tesseract not found:**
   - Install Tesseract OCR for your system
   - Ensure it's in your system PATH

3. **OpenAI API key error:**
   - Set `OPENAI_API_KEY` environment variable
   - Or pass with `--api-key` argument

4. **Firefox not launching:**
   - Ensure Firefox is installed
   - Check GeckoDriver version compatibility

5. **Permission errors:**
   - Make scripts executable: `chmod +x *.py`
   - Check file permissions for logs and screenshots

### Debug Mode
Run with verbose output:
```bash
python student_monitor.py --monitor-interval 10 --agent-interval 60
```

## Security and Privacy

- All data is stored locally
- Screenshots are saved locally in `screenshots/` folder
- No data is sent to external servers except OpenAI API calls
- OCR processing is done locally
- Web search uses DuckDuckGo (privacy-focused)

## License

This project is provided as-is for educational and personal use. Please ensure compliance with local laws and regulations regarding student monitoring.

## Contributing

Feel free to submit issues and enhancement requests! 