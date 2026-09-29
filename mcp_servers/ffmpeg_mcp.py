import json
import logging
import math
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("FFmpegMCP")

class SubtitleEngine:
    """
    Generates animated, kinetic ASS (Advanced SubStation Alpha) subtitles
    with word-by-word pop highlight and custom stroke/shadow styling.
    """
    @staticmethod
    def hex_to_ass_color(hex_str: str) -> str:
        """Converts #RRGGBB to ASS &H00BBGGRR& format."""
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 6:
            r = hex_clean[0:2]
            g = hex_clean[2:4]
            b = hex_clean[4:6]
            return f"&H00{b}{g}{r}&"
        return "&H0059DEFF&" # Default electric yellow

    @classmethod
    def generate_kinetic_ass(
        cls,
        scene_word_groups: List[Tuple[float, List[Dict[str, Any]]]],
        out_ass_path: Path,
        font_name: str = "Arial",
        font_size: int = 68,
        highlight_hex: str = "#FFDE59"
    ) -> Path:
        """
        Creates ASS subtitle file where each spoken word bursts with highlight color
        and subtle scale pop as it is spoken.
        scene_word_groups: list of (scene_start_offset, [ {word, start, end}, ... ])
        """
        out_ass_path.parent.mkdir(parents=True, exist_ok=True)
        highlight_color = cls.hex_to_ass_color(highlight_hex)

        header = f"""[Script Info]
Title: StoryTime Studio Kinetic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: KineticBase,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H000F172A,&H90000000,-1,0,0,0,100,100,1,0,1,6,2,2,40,40,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        def format_ass_time(sec: float) -> str:
            hrs = int(sec // 3600)
            mins = int((sec % 3600) // 60)
            s = int(sec % 60)
            cs = int((sec - int(sec)) * 100)
            return f"{hrs:01d}:{mins:02d}:{s:02d}.{cs:02d}"

        # Group words into chunks of 3-5 words for readable storytime subtitles
        for scene_offset, words in scene_word_groups:
            if not words:
                continue

            chunk_size = 4
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                chunk_start = scene_offset + chunk[0]["start"]
                chunk_end = scene_offset + chunk[-1]["end"] + 0.15

                # For each word in chunk, emit a frame where that word is highlighted
                for current_idx, current_word in enumerate(chunk):
                    word_start = scene_offset + current_word["start"]
                    # If this is the last word in chunk, keep it visible until chunk_end
                    word_end = scene_offset + current_word["end"] if current_idx < len(chunk) - 1 else chunk_end
                    word_end = max(word_start + 0.15, word_end)

                    line_parts = []
                    for w_idx, w in enumerate(chunk):
                        w_text = w["word"].upper()
                        if w_idx == current_idx:
                            # Highlighted active word: Pop color + scale 115%
                            line_parts.append(f"{{\\c{highlight_color}\\fscx112\\fscy112\\b1}}{w_text}{{\\r}}")
                        else:
                            # Regular white word
                            line_parts.append(f"{{\\c&H00FFFFFF&\\b1}}{w_text}{{\\r}}")

                    dialogue_text = " ".join(line_parts)
                    start_str = format_ass_time(word_start)
                    end_str = format_ass_time(word_end)
                    events.append(f"Dialogue: 0,{start_str},{end_str},KineticBase,,0,0,0,,{dialogue_text}")

        content = header + "\n".join(events) + "\n"
        with open(out_ass_path, "w", encoding="utf-8") as f:
            f.write(content)

        return out_ass_path

class VideoAssemblyEngine:
    def __init__(self):
        pass

    def mix_scene_audio(
        self,
        scene_audio_clips: List[Tuple[float, Path]], # (start_time, path)
        sfx_cues: List[Tuple[float, Path]], # (timestamp, path)
        bgm_path: Optional[Path],
        total_duration: float,
        bgm_volume: float,
        sfx_volume: float,
        voice_volume: float,
        out_mixed_audio: Path
    ) -> Path:
        """
        Combines voiceovers, SFX, and ducked background music into a single master audio track.
        Uses FFmpeg complex_filter with amix, adelay, and volume filters.
        """
        out_mixed_audio.parent.mkdir(parents=True, exist_ok=True)
        inputs = []
        filter_parts = []
        input_count = 0

        # Base silent channel of exact total_duration to ensure timeline integrity
        # anullsrc
        filter_parts.append(f"aevalsrc=0:d={total_duration}:s=44100:c=stereo[base_silence]")

        mix_inputs = ["[base_silence]"]

        # 1. Voiceover clips
        for start_sec, clip_path in scene_audio_clips:
            if clip_path.exists():
                inputs.extend(["-i", str(clip_path)])
                delay_ms = int(start_sec * 1000)
                pad_label = f"voice_{input_count}"
                filter_parts.append(f"[{input_count}:a]volume={voice_volume},adelay={delay_ms}|{delay_ms}[{pad_label}]")
                mix_inputs.append(f"[{pad_label}]")
                input_count += 1

        # 2. SFX cues
        for timestamp, sfx_path in sfx_cues:
            if sfx_path.exists():
                inputs.extend(["-i", str(sfx_path)])
                delay_ms = int(timestamp * 1000)
                pad_label = f"sfx_{input_count}"
                filter_parts.append(f"[{input_count}:a]volume={sfx_volume},adelay={delay_ms}|{delay_ms}[{pad_label}]")
                mix_inputs.append(f"[{pad_label}]")
                input_count += 1

        # 3. BGM loop
        if bgm_path and bgm_path.exists() and bgm_volume > 0.01:
            inputs.extend(["-stream_loop", "-1", "-i", str(bgm_path)])
            pad_label = f"bgm_{input_count}"
            filter_parts.append(f"[{input_count}:a]volume={bgm_volume},atrim=0:{total_duration}[{pad_label}]")
            mix_inputs.append(f"[{pad_label}]")
            input_count += 1

        # Final mix
        filter_parts.append(f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[outa]")

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[outa]",
            "-ac", "2",
            "-ar", "44100",
            str(out_mixed_audio)
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return out_mixed_audio

    def concatenate_scene_videos(self, scene_video_paths: List[Path], out_concatenated: Path) -> Path:
        """Stitches rendered scene MP4 clips seamlessly using FFmpeg concat demuxer."""
        out_concatenated.parent.mkdir(parents=True, exist_ok=True)
        list_file = out_concatenated.parent / "_concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in scene_video_paths:
                # Escape backslashes for FFmpeg concat file
                norm_path = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{norm_path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-an", # Drop intermediate audio; master audio will be merged in final pass
            str(out_concatenated)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if list_file.exists():
            list_file.unlink()
        return out_concatenated

    def assemble_final_video(
        self,
        concatenated_video: Path,
        master_audio: Path,
        ass_subtitles: Optional[Path],
        out_final_mp4: Path
    ) -> Path:
        """
        Merges video, master audio, and burns kinetic subtitles into high-definition 1080p MP4.
        """
        out_final_mp4.parent.mkdir(parents=True, exist_ok=True)

        cmd = ["ffmpeg", "-y", "-i", str(concatenated_video), "-i", str(master_audio)]

        if ass_subtitles and ass_subtitles.exists():
            # In Windows FFmpeg libass filter requires escaped path:
            escaped_ass = str(ass_subtitles.resolve()).replace("\\", "/").replace(":", "\\:")
            vf = f"subtitles='{escaped_ass}'"
            cmd.extend(["-vf", vf])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "256k",
            "-shortest",
            str(out_final_mp4)
        ])

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return out_final_mp4

if __name__ == "__main__":
    print("FFmpeg Video Assembly & Caption Engine ready.")
