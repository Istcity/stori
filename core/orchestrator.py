import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from core.storyboard import StoryboardProject, SceneItem, RenderSettings, CharacterProfile
from mcp_servers.script_mcp import ScriptDecompositionEngine
from mcp_servers.character_mcp import CharacterSceneEngine
from mcp_servers.audio_mcp import AudioProcessingEngine
from mcp_servers.animation_mcp import CinematicActionMotionEngine
from mcp_servers.ffmpeg_mcp import VideoAssemblyEngine, SubtitleEngine

logger = logging.getLogger("StoryTimeOrchestrator")

class StoryTimeOrchestrator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.projects_dir = workspace_root / "projects"
        self.assets_dir = workspace_root / "assets"
        self.sfx_dir = self.assets_dir / "sfx"
        self.bgm_dir = self.assets_dir / "bgm"
        self.char_refs_dir = self.assets_dir / "characters"

        # Initialize engines
        self.script_engine = ScriptDecompositionEngine()
        self.character_engine = CharacterSceneEngine()
        self.audio_engine = AudioProcessingEngine(self.sfx_dir, self.bgm_dir)
        self.motion_engine = CinematicActionMotionEngine()
        self.video_engine = VideoAssemblyEngine()

    def get_project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def load_project(self, project_id: str) -> StoryboardProject:
        json_path = self.get_project_dir(project_id) / "storyboard.json"
        if not json_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found at {json_path}")
        return StoryboardProject.load_from_file(json_path)

    def save_project(self, project: StoryboardProject):
        proj_dir = self.get_project_dir(project.project_id)
        proj_dir.mkdir(parents=True, exist_ok=True)
        json_path = proj_dir / "storyboard.json"
        project.save_to_file(json_path)

    def create_project(self, project_id: str, title: str, raw_story: str, character_name: str = "MainProtagonist", style_tag: str = "vyond_beach_family") -> StoryboardProject:
        proj_dir = self.get_project_dir(project_id)
        (proj_dir / "scenes" / "audio").mkdir(parents=True, exist_ok=True)
        (proj_dir / "scenes" / "images").mkdir(parents=True, exist_ok=True)
        (proj_dir / "scenes" / "clips").mkdir(parents=True, exist_ok=True)
        (proj_dir / "output").mkdir(parents=True, exist_ok=True)

        anchor_ref = f"projects/{project_id}/anchor.png"
        project = StoryboardProject(
            project_id=project_id,
            project_title=title,
            raw_story_text=raw_story,
            character_profile=CharacterProfile(
                name=character_name,
                style_tag=style_tag,
                anchor_image_path=anchor_ref
            ),
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        self.save_project(project)
        return project

    def run_scene_decomposition(self, project_id: str, pacing: str = "medium") -> StoryboardProject:
        project = self.load_project(project_id)
        raw_text = project.raw_story_text or "O gün hayatımın en unutulmaz günlerinden biriydi."
        char_name = project.character_profile.name
        style_tag = project.character_profile.style_tag

        scenes_data = self.script_engine.decompose(raw_text, char_name, style_tag, pacing=pacing)
        
        project.scenes = [SceneItem(**s) for s in scenes_data]
        self.save_project(project)
        return project

    def run_character_sheet_generation(self, project_id: str) -> Path:
        project = self.load_project(project_id)
        proj_dir = self.get_project_dir(project_id)
        anchor_path = proj_dir / "anchor.png"
        style_tag = project.character_profile.style_tag

        stock_dir = self.workspace_root / "assets" / "stock_animations"
        if style_tag in ["authentic_beach_with_boy", "hybrid_beach_boy"]:
            src = stock_dir / "thumb_composite_beach_boy.png"
            if src.exists():
                shutil.copy(src, anchor_path)
        elif style_tag in ["authentic_beach_family", "vyond_beach_family"]:
            src = stock_dir / "thumb_beach_family.png"
            if src.exists():
                shutil.copy(src, anchor_path)
        elif style_tag in ["authentic_green_screen_boy", "green_screen_modern_boy"]:
            src = stock_dir / "thumb_boy_green_screen.png"
            if src.exists():
                shutil.copy(src, anchor_path)
        else:
            self.character_engine.generate_character_anchor(
                character_name=project.character_profile.name,
                palette=project.character_profile.palette,
                out_path=anchor_path,
                style_tag=style_tag
            )

        project.character_profile.anchor_image_path = f"projects/{project_id}/anchor.png"
        self.save_project(project)
        return anchor_path

    async def run_audio_synthesis(self, project_id: str, voice_name: str = "tr-TR-AhmetNeural", progress_cb: Optional[Callable[[str], None]] = None) -> StoryboardProject:
        project = self.load_project(project_id)
        proj_dir = self.get_project_dir(project_id)

        for scene in project.scenes:
            if progress_cb:
                progress_cb(f"Synthesizing voice for Scene {scene.scene_id}...")
            
            audio_out = proj_dir / "scenes" / "audio" / f"s{scene.scene_id}.wav"
            duration, word_timestamps = await self.audio_engine.synthesize_speech(
                scene.narration_text,
                voice_name=voice_name,
                out_wav=audio_out
            )
            # Add a slight padding to duration for breathing room
            scene.duration_sec = duration + 0.35
            scene.assets.audio_clip = f"projects/{project_id}/scenes/audio/s{scene.scene_id}.wav"
            scene.assets.word_timestamps = word_timestamps
            scene.assets.mouth_cues = self.audio_engine.generate_viseme_cues(word_timestamps, scene.duration_sec)

        self.save_project(project)
        return project

    def run_scene_rendering(self, project_id: str, progress_cb: Optional[Callable[[str], None]] = None) -> StoryboardProject:
        project = self.load_project(project_id)
        proj_dir = self.get_project_dir(project_id)
        palette = project.character_profile.palette
        style_tag = project.character_profile.style_tag
        stock_dir = self.workspace_root / "assets" / "stock_animations"

        beach_video = stock_dir / "scene_beach_family.mp4"
        boy_video = stock_dir / "character_boy_green_screen.mp4"

        for scene in project.scenes:
            if progress_cb:
                progress_cb(f"Rendering Authentic Scene {scene.scene_id} [{style_tag}]: {scene.character_action[:40]}...")

            plate_path = proj_dir / "scenes" / "images" / f"s{scene.scene_id}.png"
            clip_path = proj_dir / "scenes" / "clips" / f"s{scene.scene_id}.mp4"
            audio_clip_path = proj_dir / "scenes" / "audio" / f"s{scene.scene_id}.wav"

            # 1. Authentic Video Animation Pipeline matching user downloaded reference movies
            if style_tag in ["authentic_beach_with_boy", "hybrid_beach_boy"] and beach_video.exists() and boy_video.exists():
                thumb_src = stock_dir / "thumb_composite_beach_boy.png"
                if thumb_src.exists():
                    shutil.copy(thumb_src, plate_path)

                self.video_engine.render_chroma_composite(
                    bg_source=beach_video,
                    character_source=boy_video,
                    duration_sec=scene.duration_sec,
                    out_mp4=clip_path,
                    audio_clip_path=audio_clip_path if audio_clip_path.exists() else None,
                    char_scale_height=520,
                    pos_x=140 + (scene.scene_id * 80) % 400
                )

            elif style_tag in ["authentic_beach_family", "vyond_beach_family"] and beach_video.exists():
                thumb_src = stock_dir / "thumb_beach_family.png"
                if thumb_src.exists():
                    shutil.copy(thumb_src, plate_path)

                self.video_engine.render_looped_scene_video(
                    scene_source=beach_video,
                    duration_sec=scene.duration_sec,
                    out_mp4=clip_path,
                    audio_clip_path=audio_clip_path if audio_clip_path.exists() else None
                )

            elif style_tag in ["authentic_green_screen_boy", "green_screen_modern_boy"] and boy_video.exists():
                thumb_src = stock_dir / "thumb_boy_green_screen.png"
                if thumb_src.exists():
                    shutil.copy(thumb_src, plate_path)

                self.video_engine.render_looped_scene_video(
                    scene_source=boy_video,
                    duration_sec=scene.duration_sec,
                    out_mp4=clip_path,
                    audio_clip_path=audio_clip_path if audio_clip_path.exists() else None
                )

            else:
                # Procedural Action Storytime Fallback
                self.character_engine.generate_scene_image(
                    scene_id=scene.scene_id,
                    scene_type=scene.scene_type,
                    character_action=scene.character_action,
                    camera_shot=scene.camera_shot,
                    visual_prompt=scene.visual_prompt,
                    emotion=scene.character_emotion,
                    palette=palette,
                    out_path=plate_path,
                    style_tag=style_tag
                )
                self.motion_engine.render_action_scene_video(
                    scene_id=scene.scene_id,
                    scene_type=scene.scene_type,
                    character_action=scene.character_action,
                    camera_shot=scene.camera_shot,
                    animation_guidance=scene.animation_guidance,
                    emotion=scene.character_emotion,
                    palette=palette,
                    duration_sec=scene.duration_sec,
                    animation_mode=scene.animation_mode,
                    camera_motion=scene.camera_motion,
                    audio_clip_path=audio_clip_path if audio_clip_path.exists() else None,
                    out_mp4=clip_path
                )

            scene.assets.image_plate = f"projects/{project_id}/scenes/images/s{scene.scene_id}.png"
            scene.assets.video_clip = f"projects/{project_id}/scenes/clips/s{scene.scene_id}.mp4"
            scene.status = "ready"

        self.save_project(project)
        return project

    def run_final_assembly(self, project_id: str, progress_cb: Optional[Callable[[str], None]] = None) -> Path:
        project = self.load_project(project_id)
        proj_dir = self.get_project_dir(project_id)

        if progress_cb:
            progress_cb("Assembling multi-track audio and SFX cues...")

        # 1. Calculate timeline offsets and collect audio & SFX
        current_offset = 0.0
        scene_audio_clips = []
        sfx_cues = []
        scene_word_groups = []
        scene_clips = []

        for scene in project.scenes:
            audio_p = proj_dir / "scenes" / "audio" / f"s{scene.scene_id}.wav"
            clip_p = proj_dir / "scenes" / "clips" / f"s{scene.scene_id}.mp4"

            scene_audio_clips.append((current_offset, audio_p))
            scene_clips.append(clip_p)

            # Check SFX cue
            if scene.sfx_cue:
                sfx_file = self.audio_engine.get_sfx_path(scene.sfx_cue)
                if sfx_file:
                    sfx_cues.append((current_offset + scene.sfx_offset_sec, sfx_file))

            # Word timestamps for kinetic subtitles
            if scene.assets.word_timestamps:
                scene_word_groups.append((current_offset, scene.assets.word_timestamps))

            current_offset += scene.duration_sec

        total_duration = round(current_offset, 2)
        master_audio = proj_dir / "output" / "master_audio.wav"
        bgm_file = self.audio_engine.get_bgm_path()

        self.video_engine.mix_scene_audio(
            scene_audio_clips=scene_audio_clips,
            sfx_cues=sfx_cues,
            bgm_path=bgm_file,
            total_duration=total_duration,
            bgm_volume=project.render_settings.bgm_volume,
            sfx_volume=project.render_settings.sfx_volume,
            voice_volume=project.render_settings.voice_volume,
            out_mixed_audio=master_audio
        )

        # 2. Generate kinetic ASS subtitles
        ass_path = None
        if project.render_settings.include_subtitles and scene_word_groups:
            if progress_cb:
                progress_cb("Generating kinetic animated subtitles (.ass)...")
            ass_path = proj_dir / "output" / "subtitles.ass"
            SubtitleEngine.generate_kinetic_ass(
                scene_word_groups=scene_word_groups,
                out_ass_path=ass_path,
                font_name=project.render_settings.subtitle_font,
                highlight_hex=project.render_settings.highlight_color
            )

        # 3. Concatenate video clips
        if progress_cb:
            progress_cb("Concatenating video timeline clips...")
        concat_video = proj_dir / "output" / "video_timeline.mp4"
        self.video_engine.concatenate_scene_videos(scene_clips, concat_video)

        # 4. Final render pass (Video + Master Audio + Subtitles)
        if progress_cb:
            progress_cb("Finalizing 1080p MP4 master render...")
        final_mp4 = proj_dir / "output" / "final_storytime.mp4"
        self.video_engine.assemble_final_video(
            concatenated_video=concat_video,
            master_audio=master_audio,
            ass_subtitles=ass_path,
            out_final_mp4=final_mp4
        )

        project.output_video_path = f"projects/{project_id}/output/final_storytime.mp4"
        project.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.save_project(project)

        if progress_cb:
            progress_cb(f"Render complete! Video saved to {final_mp4.name}")

        return final_mp4

    async def run_full_pipeline(self, project_id: str, voice_name: str = "tr-TR-AhmetNeural", progress_cb: Optional[Callable[[str], None]] = None) -> Path:
        """Executes the complete pipeline end-to-end."""
        if progress_cb:
            progress_cb("Stage 1/5: Decomposing script into episodic scenes...")
        self.run_scene_decomposition(project_id)

        if progress_cb:
            progress_cb("Stage 2/5: Generating Character Anchor Model Sheet...")
        self.run_character_sheet_generation(project_id)

        if progress_cb:
            progress_cb("Stage 3/5: Synthesizing voiceover with word timestamps...")
        await self.run_audio_synthesis(project_id, voice_name=voice_name, progress_cb=progress_cb)

        if progress_cb:
            progress_cb("Stage 4/5: Rendering 2D animation plates & dynamic lip-sync...")
        self.run_scene_rendering(project_id, progress_cb=progress_cb)

        if progress_cb:
            progress_cb("Stage 5/5: Multi-track audio mixing & kinetic subtitle mastering...")
        return self.run_final_assembly(project_id, progress_cb=progress_cb)
