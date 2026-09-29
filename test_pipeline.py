import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.orchestrator import StoryTimeOrchestrator

async def main():
    root = Path(__file__).resolve().parent
    orch = StoryTimeOrchestrator(root)

    print("--- CREATING TEST PROJECT ---")
    story = (
        "O gün hayatımın en büyük rezilliğini yaşayacağımdan tamamen habersizdim. "
        "Sabah erkenden kalkıp okula doğru yola çıktım. "
        "Birden pantolonumun arkasının boydan boya yırtık olduğunu fark ettim!"
    )
    orch.create_project("demo_story", "My Most Chaotic Day", story, character_name="Sinan")

    def progress(msg):
        print(f"[PROGRESS] {msg}")

    print("--- RUNNING FULL PIPELINE ---")
    final_video = await orch.run_full_pipeline("demo_story", voice_name="tr-TR-AhmetNeural", progress_cb=progress)
    print(f"--- SUCCESS! Final Video Rendered: {final_video} (Size: {final_video.stat().st_size} bytes) ---")

if __name__ == "__main__":
    asyncio.run(main())
