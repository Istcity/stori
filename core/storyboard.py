from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
from pathlib import Path

class RenderSettings(BaseModel):
    resolution: str = Field(default="1920x1080")
    fps: int = Field(default=30)
    subtitle_style: str = Field(default="kinetic_pop") # kinetic_pop, bold_stroke, minimal_glow
    bgm_volume: float = Field(default=0.18)
    sfx_volume: float = Field(default=0.85)
    voice_volume: float = Field(default=1.0)
    include_subtitles: bool = Field(default=True)
    highlight_color: str = Field(default="#FFDE59") # Electric Yellow
    subtitle_font: str = Field(default="Arial")

class CharacterProfile(BaseModel):
    name: str = Field(default="MainProtagonist")
    style_tag: str = Field(default="2d_minimalist_vector_storytime_cartoon")
    description: str = Field(default="Young adult, messy dark brown hair, oversized blue hoodie, expressive facial features")
    anchor_image_path: str = Field(default="character_refs/anchor.png")
    palette: Dict[str, str] = Field(default_factory=lambda: {
        "hair": "#2D1B18",
        "skin": "#FFE0BD",
        "hoodie": "#2563EB",
        "line": "#1E293B"
    })

class SceneAssets(BaseModel):
    audio_clip: Optional[str] = None
    image_plate: Optional[str] = None
    video_clip: Optional[str] = None
    mouth_cues: Optional[List[Dict[str, Any]]] = None # timestamp & viseme pairs
    word_timestamps: Optional[List[Dict[str, Any]]] = None # Whisper or TTS word alignments

class SceneItem(BaseModel):
    scene_id: int
    order: int
    duration_sec: float = Field(default=4.0)
    narration_text: str
    scene_type: str = Field(default="physical_action") # physical_action, slapstick, environmental_gag, reaction_shot
    character_action: str = Field(default="dynamic physical cartoon action")
    camera_shot: str = Field(default="dynamic_low_angle_crash_zoom")
    animation_guidance: str = Field(default="exaggerated squash-and-stretch motion, 2D cartoon smear frames")
    character_emotion: str = Field(default="shocked")
    visual_prompt: str = Field(default="")
    animation_mode: str = Field(default="action") # action, slapstick_squash, crash_zoom, character_bounce, lip_sync
    sfx_cue: Optional[str] = Field(default=None) # whoosh, pop, punch, record_scratch, cricket, dramatic_boom
    sfx_offset_sec: float = Field(default=0.0)
    camera_motion: str = Field(default="camera_shake")
    animation_preset: str = Field(default="authentic_beach_with_boy") # authentic_beach_with_boy, authentic_beach_family, city_street_boy, modern_room_boy, authentic_green_screen_boy, storytime_cartoon
    assets: SceneAssets = Field(default_factory=SceneAssets)
    status: str = Field(default="draft")

class StoryboardProject(BaseModel):
    project_id: str = Field(default="proj_story_001")
    project_title: str = Field(default="My Most Chaotic Day")
    raw_story_text: Optional[str] = Field(default="")
    render_settings: RenderSettings = Field(default_factory=RenderSettings)
    character_profile: CharacterProfile = Field(default_factory=CharacterProfile)
    scenes: List[SceneItem] = Field(default_factory=list)
    output_video_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def save_to_file(self, file_path: Path):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, file_path: Path) -> "StoryboardProject":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cls(**data)
