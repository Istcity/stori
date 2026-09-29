# 🎬 StoryTime Studio (Local & Hybrid AI Storytime Animation Studio)

**StoryTime Studio** is an end-to-end, production-grade desktop application that converts real-life personal stories (via raw text or microphone audio) into fully rendered, expressive, 2D YouTube storytime animation videos in the iconic style of **Jaiden Animations** and **TheOdd1sOut**.

The engine operates on a modular **Model Context Protocol (MCP)** architecture coordinating local tools (FFmpeg, ComfyUI, Whisper/Edge-TTS, LivePortrait, OpenCV) with automated cloud/API fallbacks (Recraft, Kling, ElevenLabs) for non-GPU or portable environments.

---

## 🚀 Key Features & Pipeline Architecture

```
[Raw Story / Voice Recording]
          │
          ▼
┌───────────────────────────────────────────────┐
│ 1. Scene Decomposition & Script Engine (LLM)  │ ──> Slices story into episodic beats, emotional
│    (OpenAI / Ollama / Intelligent Rules)      │     cues, visual prompts, SFX tags & camera moves
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 2. Consistent Character & Scene Engine        │ ──> Generates Character Model Anchor Sheet,
│    (ComfyUI 127.0.0.1:8188 / Recraft / Local) │     custom palettes & 16:9 1080p scene compositions
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 3. Voice & Audio Processing (Voice MCP)       │ ──> Word-level timestamp alignments (Whisper/Edge-TTS)
│    (Edge-TTS / ElevenLabs / Noise Filter)     │     and viseme cues (closed, open_a, open_o, wide_e)
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 4. 2D Puppet Lip-Sync & Motion Engine         │ ──> 30fps animation clips with dynamic mouth flaps,
│    (LivePortrait / OpenCV / Ken Burns)        │     subtle character bounce & camera shakes
└───────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────┐
│ 5. Video Assembly & Caption Engine (FFmpeg)   │ ──> Multi-track audio (voiceover + SFX + BGM loop)
│    (FFmpeg / ASS Kinetic Subtitles)           │     + Word-by-word kinetic pop highlight subtitles
└───────────────────────────────────────────────┘
          │
          ▼
   [Final 1080p 30fps YouTube-Ready MP4 Video]
```

---

## 📂 Project Directory Structure

```
storytime_studio/
├── baslat.bat                 # One-click Windows desktop launcher
├── server.py                  # FastAPI + WebSocket backend orchestrator
├── mcp_hub.py                 # Standard JSON-RPC MCP Server (stdio)
├── test_pipeline.py           # End-to-end command-line pipeline runner
├── generate_default_audio.py  # Procedural SFX & BGM synthesis script
├── core/
│   ├── storyboard.py          # Unified data contract (storyboard.json schema)
│   └── orchestrator.py        # Central multi-stage pipeline coordinator
├── mcp_servers/
│   ├── script_mcp.py          # Scene Decomposition & Script Engine (LLM MCP)
│   ├── character_mcp.py       # Consistent Character & Scene Engine (ComfyUI / Recraft / 2D Artist)
│   ├── audio_mcp.py           # Audio Synthesis & Word Timestamp Engine (Voice MCP)
│   ├── animation_mcp.py       # 2D Storytime Puppet Lip-Sync & Motion Engine
│   └── ffmpeg_mcp.py          # FFmpeg Multi-track Audio & Kinetic ASS Subtitle Engine
├── assets/
│   ├── sfx/                   # whoosh.wav, pop.wav, punch.wav, record_scratch.wav, cricket.wav, dramatic_boom.wav
│   ├── bgm/                   # storytime_acoustic_loop.wav
│   └── characters/            # Default anchor model sheets & emotion plates
├── static/
│   ├── index.html             # High aesthetic desktop web UI
│   ├── css/style.css          # Glassmorphism dark mode design system
│   └── js/app.js              # Client state, timeline interactivity & WebSocket telemetry
└── projects/                  # Local projects and rendered videos
```

---

## 💻 Quick Start & Usage

### Option 1: Desktop GUI Launcher
Simply double-click:
```bat
baslat.bat
```
This automatically boots the FastAPI orchestrator and opens the studio UI in your browser at `http://127.0.0.1:8000`.

### Option 2: Command Line
```powershell
# Activate virtual environment
C:\Users\sinan.nergiz\.gemini\antigravity-ide\scratch\.venv\Scripts\activate

# Run Web Studio
python storytime_studio\server.py

# Or run the headless pipeline test
python storytime_studio\test_pipeline.py
```

### Option 3: Model Context Protocol (MCP Server Mode)
StoryTime Studio implements standard JSON-RPC 2.0 stdio protocol. You can connect it to Antigravity IDE, Claude Desktop, or any MCP client:
```json
{
  "mcpServers": {
    "storytime_studio": {
      "command": "C:\\Users\\sinan.nergiz\\.gemini\\antigravity-ide\\scratch\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\sinan.nergiz\\.gemini\\antigravity-ide\\scratch\\storytime_studio\\mcp_hub.py"]
    }
  }
}
```

Available MCP Tools:
- `decompose_story_script`: Slices raw narration into episodic beats with emotions and camera moves.
- `generate_character_model_sheet`: Creates a 2D model anchor sheet with specified palette.
- `assemble_final_storytime_video`: Executes full audio mix, kinetic subtitle burn, and 1080p MP4 render.
- `get_pipeline_status`: Probes ComfyUI (8188), FFmpeg, and audio engines.

---

## 🎨 Unified Project Contract (`storyboard.json`)

All project states adhere strictly to the unified specification:
```json
{
  "project_id": "demo_story",
  "project_title": "My Most Chaotic Day",
  "render_settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "subtitle_style": "kinetic_pop",
    "highlight_color": "#FFDE59"
  },
  "character_profile": {
    "name": "Sinan",
    "style_tag": "2d_minimalist_vector_storytime_cartoon",
    "description": "Young adult, messy dark brown hair, oversized blue hoodie, expressive facial features",
    "anchor_image_path": "projects/demo_story/anchor.png",
    "palette": {
      "hair": "#2D1B18",
      "skin": "#FFE0BD",
      "hoodie": "#2563EB",
      "line": "#1E293B"
    }
  },
  "scenes": [
    {
      "scene_id": 1,
      "order": 1,
      "duration_sec": 4.8,
      "narration_text": "O gün hayatımın en büyük rezilliğini yaşayacağımdan tamamen habersizdim.",
      "character_emotion": "happy_oblivious",
      "visual_prompt": "2D minimalist cartoon, young man with messy hair and blue hoodie smiling walking down street",
      "animation_mode": "lip_sync",
      "sfx_cue": "whoosh",
      "sfx_offset_sec": 0.2,
      "camera_motion": "slow_zoom_in",
      "assets": {
        "audio_clip": "projects/demo_story/scenes/audio/s1.wav",
        "image_plate": "projects/demo_story/scenes/images/s1.png",
        "video_clip": "projects/demo_story/scenes/clips/s1.mp4"
      },
      "status": "ready"
    }
  ]
}
```

---

## 🔌 Hardware & Local ComfyUI Integration
- **Zero-GPU Fallback (Active by default):** If ComfyUI is offline, the studio uses its high-aesthetic procedural vector cartoon engine and Edge-TTS to render 1080p 30fps animation videos instantly without needing a dedicated GPU.
- **Local ComfyUI (Automatic Detection):** When ComfyUI is running at `http://127.0.0.1:8188`, the top status indicator turns green, allowing workflows with SDXL / Flux + IP-Adapter to generate photorealistic or custom 2D illustrations.
- **Cloud Fallbacks:** Set your `OPENAI_API_KEY`, `RECRAFT_API_KEY`, `ELEVENLABS_API_KEY`, or `KLING_API_KEY` for instant cloud generation.
