import asyncio
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.storyboard import StoryboardProject, SceneItem
from core.orchestrator import StoryTimeOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("StoryTimeServer")

app = FastAPI(title="StoryTime Studio", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = StoryTimeOrchestrator(BASE_DIR)

# Mount static folders
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")
app.mount("/projects_files", StaticFiles(directory=str(BASE_DIR / "projects")), name="projects_files")

class CreateProjectRequest(BaseModel):
    project_id: str
    project_title: str
    raw_story_text: str
    character_name: str = "MainProtagonist"

class DecomposeRequest(BaseModel):
    pacing: str = "medium"

class RenderRequest(BaseModel):
    voice_name: str = "tr-TR-AhmetNeural"

# Active WebSocket connections for live render telemetry
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str, step: Optional[int] = None, total: int = 5):
        payload = json.dumps({"message": message, "step": step, "total": total, "timestamp": time.time()})
        for conn in list(self.active_connections):
            try:
                await conn.send_text(payload)
            except Exception:
                self.disconnect(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "static" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Index HTML not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

@app.get("/api/status")
async def get_system_status():
    comfy_ok = orchestrator.character_engine.comfy.check_connection()
    return {
        "status": "online",
        "engines": {
            "orchestrator": True,
            "llm_mcp": True,
            "comfyui": comfy_ok,
            "audio_mcp": True,
            "motion_mcp": True,
            "ffmpeg_mcp": True
        },
        "available_sfx": [p.stem for p in (BASE_DIR / "assets" / "sfx").glob("*.wav")],
        "available_voices": [
            {"id": "tr-TR-AhmetNeural", "name": "Turkish - Ahmet (Expressive Male)", "lang": "tr"},
            {"id": "tr-TR-EmelNeural", "name": "Turkish - Emel (Animated Female)", "lang": "tr"},
            {"id": "en-US-GuyNeural", "name": "English - Guy (Storytime Male)", "lang": "en"},
            {"id": "en-US-JennyNeural", "name": "English - Jenny (Friendly Female)", "lang": "en"},
            {"id": "en-US-ChristopherNeural", "name": "English - Christopher (Excited Male)", "lang": "en"}
        ]
    }

@app.get("/api/projects")
async def list_projects():
    projects_dir = BASE_DIR / "projects"
    results = []
    if projects_dir.exists():
        for d in projects_dir.iterdir():
            if d.is_dir() and (d / "storyboard.json").exists():
                try:
                    p = StoryboardProject.load_from_file(d / "storyboard.json")
                    results.append({
                        "project_id": p.project_id,
                        "project_title": p.project_title,
                        "scene_count": len(p.scenes),
                        "output_video": p.output_video_path,
                        "created_at": p.created_at,
                        "updated_at": p.updated_at
                    })
                except Exception as e:
                    logger.warning(f"Error loading {d}: {e}")
    return results

@app.post("/api/projects")
async def create_project(req: CreateProjectRequest):
    p = orchestrator.create_project(
        project_id=req.project_id,
        title=req.project_title,
        raw_story=req.raw_story_text,
        character_name=req.character_name
    )
    return p.model_dump()

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    try:
        p = orchestrator.load_project(project_id)
        return p.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")

@app.post("/api/projects/{project_id}/save")
async def save_project(project_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        project = StoryboardProject(**payload)
        orchestrator.save_project(project)
        return {"success": True, "project": project.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/projects/{project_id}/decompose")
async def decompose_project(project_id: str, req: DecomposeRequest = Body(default=DecomposeRequest())):
    try:
        p = orchestrator.run_scene_decomposition(project_id, pacing=req.pacing)
        return p.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/character-sheet")
async def generate_character_sheet(project_id: str):
    try:
        anchor_path = orchestrator.run_character_sheet_generation(project_id)
        return {"success": True, "anchor_path": f"/projects_files/{project_id}/anchor.png"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/render-all")
async def render_all(project_id: str, req: RenderRequest = Body(default=RenderRequest())):
    try:
        loop = asyncio.get_running_loop()

        def sync_progress(msg: str):
            asyncio.run_coroutine_threadsafe(manager.broadcast(msg), loop)

        final_path = await orchestrator.run_full_pipeline(
            project_id=project_id,
            voice_name=req.voice_name,
            progress_cb=sync_progress
        )
        return {
            "success": True,
            "video_url": f"/projects_files/{project_id}/output/final_storytime.mp4",
            "file_size": final_path.stat().st_size
        }
    except Exception as e:
        logger.error(f"Render all failed: {e}", exc_info=True)
        await manager.broadcast(f"Render Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/render-progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
