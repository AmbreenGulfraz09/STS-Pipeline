# STS Pipeline

An AI-powered interview pipeline built with Python and Pipecat. The app creates a real-time voice interview experience using speech-to-text, large-language-model prompting, text-to-speech, and voice activity detection with smart turn handling.

## Overview

This project runs an automated interviewer that:

- listens to the candidate through a live audio pipeline
- transcribes speech using Deepgram STT
- evaluates interruptions and turn boundaries with VAD and smart turn detection
- generates interview responses with OpenAI
- speaks back responses with Deepgram TTS
- supports browser-based or telephony-style deployment via Pipecat runners

## Key files

- `pipeline.py` — core interview bot pipeline and conversation logic
- `runner.py` — Pipecat development runner for local/web transport setup
- `vad_config.py` — VAD and smart-turn transport configuration
- `requirements.txt` — Python dependencies

## Features

- Real-time AI interview flow
- Live voice interaction for candidate interviews
- Deepgram conversational STT with interim results
- OpenAI GPT-based interviewer logic
- Deepgram TTS for spoken responses
- VAD tuning with Silero and Smart Turn detection
- Interrupt handling for user interjections
- Browser/WebRTC transport support
- Daily or telephony-friendly runner support

## Tech stack

- Python 3
- Pipecat
- Deepgram STT/TTS
- OpenAI API
- FastAPI / Uvicorn
- WebRTC support via Pipecat runners
- Loguru for logging

## Requirements

Before running the project, make sure you have:

- Python 3.10+
- A Deepgram API key
- An OpenAI API key
- Optional: Koala API key used by the configured audio filter stack
- Access to a browser for local WebRTC testing

## Environment setup

Create a `.env` file in the project root with the following values:

```env
DEEPGRAM_API_KEY=your_deepgram_api_key
OPENAI_API_KEY=your_openai_api_key
Koala_API_KEY=your_koala_api_key
```

## Installation

```bash
git clone https://github.com/AmbreenGulfraz09/STS-Pipeline.git
cd STS-Pipeline
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the project

Start the bot using the runner and WebRTC transport:

```bash
python pipeline.py --transport webrtc
```

Or run it with the default local runner flow:

```bash
python pipeline.py
```

For a direct Daily room connection:

```bash
python pipeline.py --direct
```

The app is designed to discover a `bot(runner_args)` entry point automatically, so the Pipecat runner handles local app startup and transport setup.

## Example workflow

1. Launch the app locally.
2. Open the local WebRTC client in the browser.
3. The bot introduces itself and asks the candidate to introduce themselves.
4. The interview proceeds conversationally, with interruptions and turn transitions handled automatically.

## Notes

- The interviewer prompt is configured in `pipeline.py` and can be customized to match a specific hiring process or tone.
- VAD and smart-turn behavior are tuned in `vad_config.py` for responsive conversational timing.
- The project uses a Pipecat pipeline architecture where audio input, STT, LLM, and TTS are chained together.

## License

This project is provided as-is for educational and prototype use. Please check repository licensing details before production deployment or redistribution.

## Repository status

This repository is a Python-based AI conversational interview prototype built around Pipecat, Deepgram, and OpenAI services.
