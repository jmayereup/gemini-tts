# Gemini TTS Studio

A Python application for generating high-quality speech using the Gemini TTS models. It features a graphical user interface and automatic conversion to small, high-quality VBR MP3 files.

## Features

- **Tkinter GUI**: Easy-to-use interface for entering transcripts and selecting settings.
- **Customizable Speech**: Select from various voices, scenes, and audio profiles to tailor the output.
- **MP3 VBR Encoding**: Automatically intercepts raw PCM audio and encodes it to a space-efficient Variable Bitrate MP3.
- **Dev Mode**: Offline testing support via a `.env` flag to bypass API calls.
- **Persistent Settings**: Add and remove custom voices, scenes, and audio profiles directly in the GUI. These are saved to `settings.json` and persist between sessions.
- **System Integration**: Native "Save As" dialog for file management.

## Installation

### Prerequisites

- Python 3.10+
- A Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd gemini-tts
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Copy `.env.example` to `.env` and add your API key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `GEMINI_API_KEY`.

## Usage

Run the application with:

```bash
python run.py
```

### Development Mode

To test the UI and encoding flow without making API requests, set `DEV_MODE=True` in your `.env` file. This will generate silent audio buffers locally.

## Project Structure

- `run.py`: Application entry point.
- `src/gui.py`: UI implementation.
- `src/tts_client.py`: Gemini API integration.
- `src/audio_encoder.py`: MP3 encoding logic.
- `requirements.txt`: Project dependencies.
