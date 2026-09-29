import asyncio
import json
import logging
import os
import re
import subprocess
import wave
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests

logger = logging.getLogger("AudioMCP")

class AudioProcessingEngine:
    def __init__(self, sfx_dir: Path, bgm_dir: Path, elevenlabs_key: Optional[str] = None):
        self.sfx_dir = sfx_dir
        self.bgm_dir = bgm_dir
        self.elevenlabs_key = elevenlabs_key
        # Common storytime voices
        self.default_voices = {
            "tr": "tr-TR-AhmetNeural", # Turkish male expressive
            "tr_female": "tr-TR-EmelNeural",
            "en": "en-US-GuyNeural", # English storytime male
            "en_female": "en-US-JennyNeural"
        }

    async def synthesize_speech(self, text: str, voice_name: str = "tr-TR-AhmetNeural", out_wav: Path = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Synthesizes speech with word-level timestamps using edge-tts.
        Returns: (duration_seconds, list_of_word_timestamps)
        """
        import edge_tts

        out_wav.parent.mkdir(parents=True, exist_ok=True)
        temp_mp3 = out_wav.with_suffix(".mp3")

        communicate = edge_tts.Communicate(text, voice_name)
        word_timestamps = []

        with open(temp_mp3, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # offset and duration in 100ns units (ticks)
                    start_sec = chunk["offset"] / 10000000.0
                    dur_sec = chunk["duration"] / 10000000.0
                    word_timestamps.append({
                        "word": chunk["text"],
                        "start": round(start_sec, 3),
                        "end": round(start_sec + dur_sec, 3)
                    })

        # Convert MP3 to standard 44.1kHz 16-bit Mono WAV using FFmpeg
        cmd = [
            "ffmpeg", "-y", "-i", str(temp_mp3),
            "-ar", "44100", "-ac", "1",
            str(out_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if temp_mp3.exists():
            temp_mp3.unlink()

        # Get accurate WAV duration
        with wave.open(str(out_wav), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)

        # If no word boundaries received (fallback estimation)
        if not word_timestamps:
            words = text.split()
            step = duration / max(1, len(words))
            for i, w in enumerate(words):
                word_timestamps.append({
                    "word": w,
                    "start": round(i * step, 3),
                    "end": round((i + 1) * step, 3)
                })

        return round(duration, 2), word_timestamps

    def generate_viseme_cues(self, word_timestamps: List[Dict[str, Any]], total_duration: float) -> List[Dict[str, Any]]:
        """
        Converts word timestamps into second-by-second mouth viseme cues for dynamic 2D puppet lip-sync.
        Visemes: 'closed', 'open_a', 'open_o', 'wide_e'
        """
        cues = []
        for item in word_timestamps:
            word = item["word"].lower()
            start = item["start"]
            end = item["end"]
            dur = max(0.08, end - start)

            # Analyze vowels in word to assign viseme progression
            vowels = [ch for ch in word if ch in "aeıioöuü"]
            if not vowels:
                cues.append({"time": start, "viseme": "open_a", "duration": dur * 0.8})
            else:
                sub_step = dur / len(vowels)
                for vi, v in enumerate(vowels):
                    t = start + vi * sub_step
                    if v in "aı":
                        viseme = "open_a"
                    elif v in "oöuü":
                        viseme = "open_o"
                    else:
                        viseme = "wide_e"
                    cues.append({"time": round(t, 3), "viseme": viseme, "duration": round(sub_step, 3)})

        # Ensure mouth closes after speaking
        if cues:
            last_end = max(c["time"] + c["duration"] for c in cues)
            if last_end < total_duration:
                cues.append({"time": round(last_end + 0.05, 3), "viseme": "closed", "duration": total_duration - last_end})
        
        return cues

    def cleanup_microphone_audio(self, raw_audio_path: Path, clean_audio_path: Path):
        """
        Native noise suppression, de-humming, and highpass/lowpass normalization via FFmpeg.
        """
        clean_audio_path.parent.mkdir(parents=True, exist_ok=True)
        filter_str = "highpass=f=75,lowpass=f=9500,afftdn=nf=-25,volume=1.8"
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_audio_path),
            "-af", filter_str,
            "-ar", "44100", "-ac", "1",
            str(clean_audio_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return clean_audio_path

    def get_sfx_path(self, sfx_name: Optional[str]) -> Optional[Path]:
        if not sfx_name or sfx_name == "none":
            return None
        candidate = self.sfx_dir / f"{sfx_name}.wav"
        if candidate.exists():
            return candidate
        return None

    def get_bgm_path(self) -> Optional[Path]:
        for candidate in self.bgm_dir.glob("*.wav"):
            return candidate
        return None

# MCP tool helper
def mcp_synthesize_voice(text: str, voice: str, out_path: Path) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]:
    base_dir = Path(__file__).resolve().parent.parent
    engine = AudioProcessingEngine(base_dir / "assets" / "sfx", base_dir / "assets" / "bgm")
    duration, words = asyncio.run(engine.synthesize_speech(text, voice, out_path))
    cues = engine.generate_viseme_cues(words, duration)
    return duration, words, cues

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    engine = AudioProcessingEngine(base / "assets" / "sfx", base / "assets" / "bgm")
    test_out = base / "assets" / "test_voice.wav"
    dur, words = asyncio.run(engine.synthesize_speech("Merhaba, StoryTime Studio ses motoru başarıyla çalışıyor!", out_wav=test_out))
    cues = engine.generate_viseme_cues(words, dur)
    print(f"Generated voice: {dur}s, {len(words)} words, {len(cues)} viseme cues.")
