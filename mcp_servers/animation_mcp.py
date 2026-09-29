import json
import logging
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image, ImageDraw
import cv2

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_servers.character_mcp import CinematicActionArtist

logger = logging.getLogger("AnimationMCP")

class CinematicActionMotionEngine:
    """
    Cinematic 2D Action Motion Engine (Jaiden / Odd1sOut animation physics).
    Implements:
    - Exaggerated Squash & Stretch
    - Crash Zooms on SFX impact
    - Cartoon Smear Frames & Speed Streaks
    - Dynamic Walk Cycles & Sonic Leg-Wheel Spins
    - Screen Shakes & Comic Vibrations
    Outputs high quality 30fps H.264 MP4.
    """
    def __init__(self, fps: int = 30, width: int = 1920, height: int = 1080):
        self.fps = fps
        self.width = width
        self.height = height
        self.artist = CinematicActionArtist(width, height)

    def render_action_scene_video(
        self,
        scene_id: int,
        scene_type: str,
        character_action: str,
        camera_shot: str,
        animation_guidance: str,
        emotion: str,
        palette: Dict[str, str],
        duration_sec: float,
        animation_mode: str,
        camera_motion: str,
        audio_clip_path: Optional[Path],
        out_mp4: Path
    ) -> Path:
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        total_frames = max(20, int(duration_sec * self.fps))

        # Pre-render 8 distinct animation phase plates for smooth cyclical motion (walk, sprint, vibration)
        phase_plates = []
        num_phases = 8
        for p_idx in range(num_phases):
            phase_val = p_idx / float(num_phases)
            temp_path = out_mp4.parent / f"_temp_phase_{p_idx}.png"
            self.artist.render_cinematic_action_scene(
                scene_id=scene_id,
                scene_type=scene_type,
                character_action=character_action,
                camera_shot=camera_shot,
                emotion=emotion,
                palette=palette,
                out_path=temp_path,
                frame_phase=phase_val
            )
            img = Image.open(temp_path).convert("RGB")
            phase_plates.append(np.array(img))
            if temp_path.exists():
                temp_path.unlink()

        # Write frames directly using OpenCV VideoWriter
        temp_avi = out_mp4.with_suffix(".avi")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        vw = cv2.VideoWriter(str(temp_avi), fourcc, float(self.fps), (self.width, self.height))

        try:
            for f_idx in range(total_frames):
                # Phase cycles at 2 cycles per second for brisk cartoon tempo
                phase_idx = int((f_idx / self.fps * 2.5 * num_phases)) % num_phases
                base_plate = phase_plates[phase_idx]

                # Apply Cinematic Action Physics (Crash Zoom, Squash & Stretch, Camera Shakes)
                frame_arr = self._apply_action_physics(
                    base_arr=base_plate,
                    frame_idx=f_idx,
                    total_frames=total_frames,
                    animation_mode=animation_mode,
                    camera_motion=camera_motion,
                    camera_shot=camera_shot
                )

                # Convert to BGR for OpenCV
                bgr = cv2.cvtColor(frame_arr, cv2.COLOR_RGB2BGR)
                vw.write(bgr)

            vw.release()

            # Encode to MP4 with FFmpeg
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_avi)
            ]
            if audio_clip_path and audio_clip_path.exists():
                ffmpeg_cmd.extend(["-i", str(audio_clip_path), "-c:a", "aac", "-b:a", "192k"])

            ffmpeg_cmd.extend([
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                "-crf", "19",
                str(out_mp4)
            ])
            subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        finally:
            if temp_avi.exists():
                try:
                    temp_avi.unlink()
                except Exception:
                    pass

        return out_mp4

    def _apply_action_physics(
        self,
        base_arr: np.ndarray,
        frame_idx: int,
        total_frames: int,
        animation_mode: str,
        camera_motion: str,
        camera_shot: str
    ) -> np.ndarray:
        """
        Applies genuine 2D cartoon physical transformations:
        - Crash Zoom: Snaps into 145% zoom on realization beat
        - Squash and Stretch: Harmonic oscillator deform
        - Camera Shake: Violent impact decay
        - Tracking pan
        """
        progress = frame_idx / max(1, total_frames)
        scale_x = 1.0
        scale_y = 1.0
        dx = 0
        dy = 0

        # 1. Crash Zoom on realization (e.g. discovering torn pants)
        if "crash_zoom" in animation_mode or "crash_zoom" in camera_shot:
            # First 25% normal view, then instant snap zoom to 140%
            snap_point = 0.22
            if progress < snap_point:
                scale_x = scale_y = 1.0 + 0.05 * (progress / snap_point)
            else:
                # Snap in with dramatic overshoot
                t_after = (progress - snap_point) / (1.0 - snap_point)
                overshoot = math.exp(-t_after * 8) * math.sin(t_after * 25) * 0.15
                scale_x = scale_y = 1.35 + overshoot
                # Violent comic vibration for the first 10 frames after snap
                if t_after < 0.25:
                    dx = int(math.sin(frame_idx * 2.8) * 18 * (1.0 - t_after / 0.25))
                    dy = int(math.cos(frame_idx * 3.1) * 14 * (1.0 - t_after / 0.25))

        # 2. Squash & Stretch Slapstick
        elif "squash" in animation_mode or "slapstick" in animation_mode:
            # Rhythmic bouncing squash & stretch
            osc = math.sin(frame_idx * 0.35)
            scale_y = 1.0 + osc * 0.10 # squashes down and stretches up
            scale_x = 1.0 - osc * 0.08 # inverse volume preservation
            dy = int(-osc * 20)

        # 3. Sonic Sprint Tracking Pan
        elif "pan" in camera_motion or "tracking" in camera_shot:
            dx = int(-140 * progress) # Fast horizontal camera sweep
            dy = int(math.sin(frame_idx * 0.6) * 8) # Step rhythm

        # 4. Impact Camera Shake
        if "camera_shake" in camera_motion:
            decay = max(0.1, 1.0 - progress * 0.8)
            dx += int(math.sin(frame_idx * 2.2) * 14 * decay)
            dy += int(math.cos(frame_idx * 2.5) * 10 * decay)

        if scale_x == 1.0 and scale_y == 1.0 and dx == 0 and dy == 0:
            return base_arr

        # Perform 2D affine / crop-resize transformation
        h, w, c = base_arr.shape
        new_w = max(100, int(w / scale_x))
        new_h = max(100, int(h / scale_y))

        cx = w // 2 + dx
        cy = h // 2 + dy

        x1 = max(0, min(w - new_w, cx - new_w // 2))
        y1 = max(0, min(h - new_h, cy - new_h // 2))
        x2 = x1 + new_w
        y2 = y1 + new_h

        cropped = base_arr[y1:y2, x1:x2]
        resized = Image.fromarray(cropped).resize((w, h), Image.Resampling.BILINEAR)
        return np.array(resized)

if __name__ == "__main__":
    print("Cinematic Action Motion Engine ready.")
