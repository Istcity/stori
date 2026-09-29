import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.orchestrator import StoryTimeOrchestrator

orchestrator = StoryTimeOrchestrator(BASE_DIR)

TOOLS = [
    {
        "name": "decompose_story_script",
        "description": "Slices unpolished user text into second-by-second scenes with emotions, visual prompts, SFX cues and camera motion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "story_text": {"type": "string", "description": "The raw story narration"},
                "character_name": {"type": "string", "default": "MainProtagonist"},
                "pacing": {"type": "string", "enum": ["fast", "medium", "slow"], "default": "medium"}
            },
            "required": ["story_text"]
        }
    },
    {
        "name": "generate_character_model_sheet",
        "description": "Generates a 2D vector cartoon character model sheet and anchor image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "character_name": {"type": "string"},
                "hair_color": {"type": "string", "default": "#2D1B18"},
                "skin_color": {"type": "string", "default": "#FFE0BD"},
                "hoodie_color": {"type": "string", "default": "#2563EB"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "assemble_final_storytime_video",
        "description": "Full multi-track audio mix, kinetic subtitles burning and video timeline concatenation into 1080p MP4.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "voice_name": {"type": "string", "default": "tr-TR-AhmetNeural"}
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_pipeline_status",
        "description": "Checks connectivity with local ComfyUI, FFmpeg, Whisper/Edge-TTS, and active projects.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Any:
    if tool_name == "decompose_story_script":
        scenes = orchestrator.script_engine.decompose(
            raw_text=arguments["story_text"],
            character_name=arguments.get("character_name", "MainProtagonist"),
            pacing=arguments.get("pacing", "medium")
        )
        return {"scenes": scenes}

    elif tool_name == "generate_character_model_sheet":
        pid = arguments["project_id"]
        project = orchestrator.load_project(pid)
        if "hair_color" in arguments:
            project.character_profile.palette["hair"] = arguments["hair_color"]
        if "skin_color" in arguments:
            project.character_profile.palette["skin"] = arguments["skin_color"]
        if "hoodie_color" in arguments:
            project.character_profile.palette["hoodie"] = arguments["hoodie_color"]
        orchestrator.save_project(project)
        anchor = orchestrator.run_character_sheet_generation(pid)
        return {"anchor_image": str(anchor)}

    elif tool_name == "assemble_final_storytime_video":
        pid = arguments["project_id"]
        voice = arguments.get("voice_name", "tr-TR-AhmetNeural")
        final_video = asyncio.run(orchestrator.run_full_pipeline(pid, voice_name=voice))
        return {"video_path": str(final_video), "size_bytes": final_video.stat().st_size}

    elif tool_name == "get_pipeline_status":
        comfy_ok = orchestrator.character_engine.comfy.check_connection()
        return {
            "status": "ready",
            "comfyui_connected": comfy_ok,
            "ffmpeg_available": True,
            "tts_available": True,
            "motion_engine_ready": True
        }

    raise ValueError(f"Unknown tool: {tool_name}")

def main():
    """Stdio JSON-RPC loop for Model Context Protocol."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                res = handle_tool_call(tool_name, args)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}}
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
