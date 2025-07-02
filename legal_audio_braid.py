# coding: utf-8
"""Unified audio transcription and analysis pipeline.

This script orchestrates local transcription with Whisper, enhanced analysis with
AssemblyAI, and optional Rev.ai formatting. It produces a consolidated
transcript suitable for legal workflows.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Any, Dict, Optional

import requests
import whisper
from dotenv import load_dotenv


load_dotenv()
ASSEMBLY_KEY = os.getenv("ASSEMBLYAI_API_KEY")
REVAI_KEY = os.getenv("REVAI_API_KEY")

# Default wait time between polling attempts
POLL_INTERVAL = 10


def transcribe_whisper(audio_path: str, model_size: str = "medium") -> str:
    """Transcribe audio locally using Whisper."""
    model = whisper.load_model(model_size)
    print("Whisper: Transcribing audio...")
    result = model.transcribe(audio_path)
    text = result.get("text", "")
    with open("whisper_transcript.txt", "w", encoding="utf-8") as file:
        file.write(text)
    return text


def upload_to_assemblyai(audio_path: str) -> str:
    """Upload the audio file to AssemblyAI and return the upload URL."""
    if not ASSEMBLY_KEY:
        raise EnvironmentError("ASSEMBLYAI_API_KEY not set")
    headers = {"authorization": ASSEMBLY_KEY}
    upload_url = "https://api.assemblyai.com/v2/upload"
    with open(audio_path, "rb") as handle:
        response = requests.post(upload_url, headers=headers, files={"file": handle})
    response.raise_for_status()
    return response.json()["upload_url"]


def start_assemblyai_transcription(upload_url: str) -> str:
    """Start AssemblyAI transcription and return the transcript ID."""
    if not ASSEMBLY_KEY:
        raise EnvironmentError("ASSEMBLYAI_API_KEY not set")
    endpoint = "https://api.assemblyai.com/v2/transcript"
    headers = {"authorization": ASSEMBLY_KEY, "content-type": "application/json"}
    data = {
        "audio_url": upload_url,
        "speaker_labels": True,
        "iab_categories": True,
        "auto_highlights": True,
        "sentiment_analysis": True,
    }
    response = requests.post(endpoint, json=data, headers=headers)
    response.raise_for_status()
    return response.json()["id"]


def poll_transcription_status(
    transcript_id: str, poll_interval: int = POLL_INTERVAL
) -> Dict[str, Any]:
    """Poll AssemblyAI until transcription is complete."""
    if not ASSEMBLY_KEY:
        raise EnvironmentError("ASSEMBLYAI_API_KEY not set")
    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    headers = {"authorization": ASSEMBLY_KEY}
    while True:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        result = response.json()
        status = result.get("status")
        if status == "completed":
            return result
        if status == "error":
            raise RuntimeError(f"AssemblyAI error: {result.get('error')}")
        print("Polling AssemblyAI status...")
        time.sleep(poll_interval)


def request_rev_ai_transcript(
    audio_path: str,
    poll_interval: int = POLL_INTERVAL,
) -> str:
    """Send audio to Rev.ai for formatted transcription."""
    if not REVAI_KEY:
        raise EnvironmentError("REVAI_API_KEY not set")
    headers = {"Authorization": f"Bearer {REVAI_KEY}"}
    upload_url = "https://api.rev.ai/speechtotext/v1/jobs"
    with open(audio_path, "rb") as handle:
        data = {"media": handle}
        response = requests.post(upload_url, headers=headers, files=data)
    response.raise_for_status()
    job_id = response.json()["id"]

    # Poll for completion
    result_url = f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}/transcript"
    result_url += "?accept=text/plain"
    while True:
        status_resp = requests.get(
            f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}",
            headers=headers,
        )
        status_resp.raise_for_status()
        if status_resp.json().get("status") == "transcribed":
            break
        print("Polling Rev.ai status...")
        time.sleep(poll_interval)
    rev_resp = requests.get(result_url, headers=headers)
    rev_resp.raise_for_status()
    return rev_resp.text


def write_output_files(
    whisper_text: str,
    assembly_data: Dict[str, Any],
    rev_text: Optional[str] = None,
) -> None:
    """Write combined output files for legal use."""
    with open("legal_motion_transcript.txt", "w", encoding="utf-8") as file:
        file.write("=== WHISPER TRANSCRIPT ===\n")
        file.write(whisper_text + "\n\n")
        file.write("=== ASSEMBLYAI HIGHLIGHTS ===\n")
        highlights = assembly_data.get("auto_highlights_result", {}).get("results", [])
        for highlight in highlights:
            text = highlight["text"]
            confidence = highlight["confidence"]
            file.write(f"- Highlight: {text} (confidence: {confidence})\n")
        file.write("\n=== SENTIMENT ===\n")
        for sentiment in assembly_data.get("sentiment_analysis_results", []):
            file.write(f"[{sentiment['text']}] -> {sentiment['sentiment']}\n")
        if rev_text:
            file.write("\n=== REV.AI TRANSCRIPT ===\n")
            file.write(rev_text)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Unified audio transcription pipeline")
    parser.add_argument("audio_file", help="Path to the audio file")
    parser.add_argument(
        "--whisper-model",
        default="medium",
        help="Whisper model size to use",
    )
    parser.add_argument(
        "--use-rev", action="store_true", help="Send audio to Rev.ai for formatting"
    )
    args = parser.parse_args()

    whisper_text = transcribe_whisper(args.audio_file, args.whisper_model)
    uploaded_url = upload_to_assemblyai(args.audio_file)
    transcript_id = start_assemblyai_transcription(uploaded_url)
    assembly_output = poll_transcription_status(transcript_id)
    rev_text = request_rev_ai_transcript(args.audio_file) if args.use_rev else None
    write_output_files(whisper_text, assembly_output, rev_text)
    print("Transcription complete. Output written to legal_motion_transcript.txt")


if __name__ == "__main__":
    main()
