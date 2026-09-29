import re
import json
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger("ScriptMCP")

class ScriptDecompositionEngine:
    def __init__(self, api_base: Optional[str] = None, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model

    def decompose(self, raw_text: str, character_name: str = "MainProtagonist", style_tag: str = "2d_minimalist_vector_storytime_cartoon", pacing: str = "medium") -> List[Dict[str, Any]]:
        """
        Decomposes raw story text into ACTION-FIRST episodic scenes.
        Bans stationary talking heads; every scene depicts physical action, slapstick, or dynamic reactions.
        """
        if self.api_key or (self.api_base and "ollama" in self.api_base.lower()):
            try:
                return self._decompose_with_llm(raw_text, character_name, style_tag)
            except Exception as e:
                logger.warning(f"LLM decomposition failed ({e}), falling back to Action-First rule parser.")
        
        return self._decompose_action_first_heuristic(raw_text, character_name, style_tag, pacing)

    def _decompose_with_llm(self, raw_text: str, character_name: str, style_tag: str) -> List[Dict[str, Any]]:
        system_prompt = f"""You are the Action-First Cinematic Director for StoryTime Studio (Jaiden Animations / TheOdd1sOut / Domics style).
CRITICAL DIRECTION:
1. STRICTLY FORBIDDEN: Stationary 'talking head' narrator sequences! Audio narration is DECOUPLED from visual action.
2. Every scene MUST depict dynamic physical interactions, exaggerated slapstick gags, cartoon physics, physical falls, or dramatic environmental reactions.
3. Use exaggerated animation principles: squash & stretch, cartoon smear frames, crash zooms, impact lines, flying objects.

Return ONLY a valid JSON array of objects conforming to:
[
  {{
    "scene_id": 1,
    "order": 1,
    "narration_text": "...",
    "scene_type": "physical_action" | "slapstick" | "environmental_gag" | "reaction_shot",
    "character_action": "hyper-specific physical cartoon action (e.g. trips over a skateboard, items flying out of hands)",
    "camera_shot": "dynamic_low_angle_crash_zoom" | "whip_pan_reveal" | "extreme_close_up_shock" | "wide_slapstick_view",
    "animation_guidance": "exaggerated squash-and-stretch motion, 2D cartoon smear frames",
    "character_emotion": "happy_oblivious|shocked|panicked|embarrassed|angry|laughing",
    "visual_prompt": "2D minimalist cartoon, dynamic action shot of ..., 16:9 cinematic framing",
    "animation_mode": "action" | "slapstick_squash" | "crash_zoom" | "smear_tumble",
    "sfx_cue": "whoosh|pop|punch|record_scratch|cricket|dramatic_boom",
    "sfx_offset_sec": 0.2,
    "camera_motion": "camera_shake|crash_zoom_in|pan_left|pan_right|bounce"
  }}
]
"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        url = self.api_base or "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Protagonist: {character_name}\nStyle: {style_tag}\n\nStory:\n{raw_text}"}
            ],
            "temperature": 0.7
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        match = re.search(r"\[\s*\{.*\}\s*\]", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(content)

    def _decompose_action_first_heuristic(self, raw_text: str, character_name: str, style_tag: str, pacing: str) -> List[Dict[str, Any]]:
        """
        Intelligent Action-First narrative generator.
        Transforms passive narration into lively physical cartoon beats.
        """
        clean_text = raw_text.strip().replace("...", ".").replace("…", ".")
        raw_sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 3]

        if not sentences:
            sentences = [clean_text]

        target_words = 12 if pacing == "fast" else (16 if pacing == "medium" else 22)
        merged_chunks = []
        curr = ""
        for s in sentences:
            if not curr:
                curr = s
            elif len((curr + " " + s).split()) < target_words:
                curr += " " + s
            else:
                merged_chunks.append(curr)
                curr = s
        if curr:
            merged_chunks.append(curr)

        scenes = []
        for idx, text in enumerate(merged_chunks, start=1):
            lower = text.lower()
            words_count = len(text.split())
            est_dur = max(3.0, round(words_count / 2.4, 1))

            # Detect story context and invent dynamic physical slapstick action
            if any(w in lower for w in ["yırtık", "pantolon", "pants", "rip", "arka", "rezillik", "fark ettim"]):
                scene_type = "slapstick"
                action = f"{character_name} freezes in terror, reaching behind in frantic disbelief as cold wind blows through a massive cartoon tear in trousers"
                camera_shot = "dynamic_low_angle_crash_zoom"
                guidance = "sudden freeze-frame pop, exaggerated cartoon shock lines and sweat burst"
                emotion = "shocked"
                sfx = "record_scratch"
                camera = "camera_shake"
                anim_mode = "crash_zoom"
                prompt_action = "dramatic low angle slapstick cartoon shot, young man in blue hoodie realizing his pants are torn, eyes bulging out in comic shock, wind gust lines, dynamic comic impact"

            elif any(w in lower for w in ["utandım", "kızardım", "rezil", "embarrassed", "shame", "eyvah"]):
                scene_type = "reaction_shot"
                action = f"{character_name}'s face turns completely tomato-red, sinking into oversized hoodie collar like a cartoon turtle while smoke billows from ears"
                camera_shot = "extreme_close_up_shock"
                guidance = "squash into hoodie collar, red blush expansion with steam particles"
                emotion = "embarrassed"
                sfx = "cricket"
                camera = "slow_zoom_in"
                anim_mode = "slapstick_squash"
                prompt_action = "hilarious cartoon reaction shot, young man sinking completely into oversized blue hoodie, face glowing bright red with cartoon steam poofs coming from ears"

            elif any(w in lower for w in ["koştum", "kaçtım", "panik", "yetiş", "çabuk", "run", "panic", "scream"]):
                scene_type = "physical_action"
                action = f"{character_name} sprints at sonic speed, legs churning into a blurry cartoon wheel of smoke and dust, backpack bouncing violently"
                camera_shot = "tracking_run"
                guidance = "sonic leg-wheel smear frames, trailing cartoon dust clouds and speed streaks"
                emotion = "panicked"
                sfx = "whoosh"
                camera = "pan_right"
                anim_mode = "action"
                prompt_action = "dynamic side-scrolling cartoon action shot, young man sprinting at extreme speed, legs spinning in a cartoon smoke wheel, flying dust clouds"

            elif any(w in lower for w in ["düştüm", "çarptım", "takıldım", "fall", "trip", "slip"]):
                scene_type = "slapstick"
                action = f"{character_name} trips violently, doing a 360-degree aerial flip, shoes flying in opposite directions before faceplanting"
                camera_shot = "dynamic_low_angle_crash_zoom"
                guidance = "aerial smear tumble, comic impact squash and bouncing stars"
                emotion = "shocked"
                sfx = "punch"
                camera = "camera_shake"
                anim_mode = "smear_tumble"
                prompt_action = "hilarious cartoon slapstick accident, young man flipping mid-air after tripping, shoes flying off, comic impact stars and dust poof"

            elif idx == 1:
                scene_type = "physical_action"
                action = f"{character_name} struts triumphantly down the sunny street with exaggerated confidence, swinging arms cartoonishly high, oblivious to what awaits"
                camera_shot = "wide_slapstick_view"
                guidance = "bouncy exaggerated character walk cycle, rhythmic step bobbing"
                emotion = "happy_oblivious"
                sfx = "whoosh"
                camera = "slow_zoom_in"
                anim_mode = "action"
                prompt_action = "colorful 2D vector cartoon wide shot, young man in oversized blue hoodie strutting down sunny street with hilarious overconfidence, swinging arms high, birds chirping"

            else:
                scene_type = "environmental_gag"
                action = f"{character_name} gesticulates wildly, flailing arms in cartoon agitation while background objects wobble"
                camera_shot = "dynamic_low_angle_crash_zoom"
                guidance = "exaggerated body gesture snaps, dynamic arm smears"
                emotion = "panicked" if (idx % 2 == 1) else "happy_oblivious"
                sfx = "pop" if (idx % 2 == 1) else "dramatic_boom"
                camera = "camera_shake" if (idx % 2 == 1) else "slow_zoom_in"
                anim_mode = "action"
                prompt_action = f"expressive 2D storytime cartoon action illustration, {character_name} reacting dynamically, flailing arms with comic emotion lines, vibrant 16:9 scene"

            # Context-Aware Scenario Detection for Per-Scene Dynamic Animation
            lower_text = text.lower()
            if any(w in lower_text for w in ["sahil", "plaj", "deniz", "tatil", "kum", "yüzme", "beach", "summer", "ocean", "güneş"]):
                anim_preset = "authentic_beach_with_boy"
            elif any(w in lower_text for w in ["aile", "akraba", "selam", "arap", "merhaba", "el salla", "wave"]):
                anim_preset = "authentic_beach_family"
            elif any(w in lower_text for w in ["sokak", "cadde", "okul", "yol", "otobüs", "yürü", "koş", "ilerle", "street", "city"]):
                anim_preset = "city_street_boy"
            elif any(w in lower_text for w in ["ev", "oda", "sabah", "kalktım", "hazırlandım", "uyandım", "home", "room", "morning"]):
                anim_preset = "modern_room_boy"
            elif any(w in lower_text for w in ["yeşil", "stüdyo", "tanıtım", "sunum", "green"]):
                anim_preset = "authentic_green_screen_boy"
            else:
                presets_sequence = ["modern_room_boy", "city_street_boy", "authentic_beach_with_boy", "storytime_cartoon"]
                anim_preset = presets_sequence[(idx - 1) % len(presets_sequence)]

            if style_tag == "vyond_beach_family":
                prompt_action = f"Vyond Business-Friendly vector explainer scene, tropical beach with waving family and Arab gentleman: {action}"
            elif style_tag == "green_screen_modern_boy":
                prompt_action = f"Modern 2.5D shaded vector mascot boy with red glasses and polo shirt on chroma key green screen: {action}"

            scenes.append({
                "scene_id": idx,
                "order": idx,
                "duration_sec": est_dur,
                "narration_text": text,
                "scene_type": scene_type,
                "character_action": action,
                "camera_shot": camera_shot,
                "animation_guidance": guidance,
                "character_emotion": emotion,
                "visual_prompt": prompt_action,
                "animation_mode": anim_mode,
                "animation_preset": anim_preset,
                "sfx_cue": sfx,
                "sfx_offset_sec": 0.25,
                "camera_motion": camera,
                "assets": {
                    "audio_clip": f"projects/demo_story/scenes/audio/s{idx}.wav",
                    "image_plate": f"projects/demo_story/scenes/images/s{idx}.png",
                    "video_clip": f"projects/demo_story/scenes/clips/s{idx}.mp4"
                },
                "status": "ready"
            })

        return scenes

# Standalone helper
def mcp_decompose_script(story_text: str, character_name: str = "MainProtagonist", style_tag: str = "2d_minimalist_vector_storytime_cartoon") -> List[Dict[str, Any]]:
    engine = ScriptDecompositionEngine()
    return engine.decompose(story_text, character_name, style_tag)
