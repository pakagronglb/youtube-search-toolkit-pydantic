# YouTube Search Toolkit

---

<img width="519" alt="Screenshot 2025-03-28 at 07 57 11" src="https://github.com/user-attachments/assets/5433608e-3736-4ea1-b1be-a9ff62235d00" />

<img width="1021" alt="Screenshot 2025-03-28 at 07 57 25" src="https://github.com/user-attachments/assets/7c4a2b21-4df0-44af-9abe-8b5b3e497463" />

<img width="549" alt="Screenshot 2025-03-28 at 07 57 51" src="https://github.com/user-attachments/assets/5bcdfda0-0716-4674-8421-31fde4d26220" />

<img width="849" alt="Screenshot 2025-03-28 at 08 12 15" src="https://github.com/user-attachments/assets/2b19b4f8-1020-45bd-9c01-6a98801b3e3b" />

---

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-black.svg?logo=openai&logoColor=white)
![YouTube](https://img.shields.io/badge/YouTube-API-FF0000.svg?logo=youtube&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-AI-blue.svg)
![Rich](https://img.shields.io/badge/Rich-CLI-purple.svg)

An advanced YouTube search toolkit powered by AI that allows you to search for YouTube channels, videos, and playlists with natural language queries through an interactive CLI.

This project builds upon the tutorial by [Jie Jenn](https://www.youtube.com/c/JieJenn) on [Building a YouTube Search Tool with AI](https://www.youtube.com/watch?v=sulqJjJ0GmU).

## Features

- 🔍 Search for YouTube channels, videos, and playlists using natural language
- 📊 Get detailed information about YouTube videos and channels
- 📝 Download video transcripts
- 🤖 AI-powered responses using OpenAI's models
- ⏱️ Rate limit handling to respect YouTube API quotas

## Prerequisites

- Python 3.9+
- YouTube Data API credentials
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pakagronglb/youtube-search-toolkit-pydantic.git
   cd youtube-search-toolkit-pydantic
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

## Configuration

1. Set up YouTube API credentials:
   - Go to the [Google Developer Console](https://console.developers.google.com/)
   - Create a new project and enable the YouTube Data API v3
   - Create OAuth credentials and download the client secret JSON file
   - Save the file as `client-secret.json` in the project root directory

2. Configure OpenAI API:
   - Create a `.env` file in the project root with your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

## Usage

Run the main script to start the interactive CLI:

```bash
python test_youtube_tool.py
```

### Example Commands

- Search for a channel:
  ```
  Search for channel "Tesla"
  ```

- Find recent videos from a channel:
  ```
  Get the latest videos from the Tesla channel
  ```

- Search for videos about a specific topic:
  ```
  Find videos about "Python AI development"
  ```

- Get video information:
  ```
  Get details for video "URL_or_ID"
  ```

- Download transcript:
  ```
  Download the transcript for video "URL_or_ID"
  ```

## Project Structure

- `test_youtube_tool.py` - Main script with CLI interface
- `tools/google/youtube_tools.py` - YouTube API integration
- `tools/google/google_apis.py` - Google API authentication helpers
- `token files/` - YouTube API token storage (gitignored)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project is based on the tutorial by [Jie Jenn](https://www.youtube.com/watch?v=sulqJjJ0GmU)
- Uses the [YouTube Data API v3](https://developers.google.com/youtube/v3)
- Powered by [OpenAI](https://openai.com/) and [Pydantic AI](https://github.com/pydantic/pydantic-ai) 
