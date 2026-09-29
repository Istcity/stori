import json
import logging
import math
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import requests
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("CharacterMCP")

class CinematicActionArtist:
    """
    Cinematic 2D Storytime Action Scene Engine (Jaiden / Odd1sOut / Domics style).
    Renders FULL-BODY dynamic slapstick scenes, environmental gags, and dramatic reactions.
    NO stationary talking heads!
    """
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def render_anchor_sheet(self, character_name: str, palette: Dict[str, str], out_path: Path):
        """Generates a 2D Action Model Sheet with dynamic poses, not just busts."""
        sheet = Image.new("RGBA", (self.width, self.height), (245, 247, 250, 255))
        draw = ImageDraw.Draw(sheet)

        # Header Title
        draw.rectangle([(0, 0), (self.width, 90)], fill=(15, 23, 42, 255))
        title = f"CINEMATIC 2D ACTION MODEL SHEET: {character_name.upper()} (ACTION-FIRST PIPELINE)"
        draw.text((60, 32), title, fill=(255, 255, 255, 255))

        poses = [
            ("STRUT / WALK", "walk_swagger", 280, 520),
            ("SLAPSTICK REAR RIP", "pants_rip_shock", 760, 520),
            ("PANIC SPRINT", "sonic_sprint", 1240, 520),
            ("MELTDOWN BLUSH", "hoodie_sink", 1680, 520)
        ]

        for label, pose_type, cx, cy in poses:
            draw.rounded_rectangle([(cx - 200, cy - 360), (cx + 200, cy + 380)], radius=24, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=3)
            self._render_pose_figure(draw, cx, cy + 60, scale=0.78, pose_type=pose_type, palette=palette, frame_phase=0.0)
            draw.rounded_rectangle([(cx - 160, cy + 310), (cx + 160, cy + 355)], radius=12, fill=(241, 245, 249, 255))
            draw.text((cx - 80, cy + 324), label, fill=(30, 41, 59, 255))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(str(out_path), "PNG")
        return out_path

    def render_cinematic_action_scene(
        self,
        scene_id: int,
        scene_type: str,
        character_action: str,
        camera_shot: str,
        emotion: str,
        palette: Dict[str, str],
        out_path: Path,
        frame_phase: float = 0.0
    ):
        """
        Renders a full 16:9 cinematic cartoon action plate.
        Depicts physical slapstick, environmental interaction, and comic VFX.
        """
        img = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 1. Determine Pose based on action & scene_type
        act_lower = character_action.lower()
        if "rip" in act_lower or "pantolon" in act_lower or "tear" in act_lower or "behind" in act_lower:
            pose = "pants_rip_shock"
            bg_theme = "street_perspective"
        elif "sprint" in act_lower or "run" in act_lower or "koş" in act_lower or "panic" in act_lower:
            pose = "sonic_sprint"
            bg_theme = "speed_hallway"
        elif "blush" in act_lower or "utand" in act_lower or "sink" in act_lower or "red" in act_lower:
            pose = "hoodie_sink"
            bg_theme = "dramatic_spotlight"
        elif "walk" in act_lower or "strut" in act_lower or scene_id == 1:
            pose = "walk_swagger"
            bg_theme = "sunny_sidewalk"
        else:
            pose = "exaggerated_flail"
            bg_theme = "comic_burst"

        # 2. Render Cinematic Dynamic Background
        self._render_cinematic_background(draw, bg_theme, camera_shot)

        # 3. Render Full-Body Action Character Figure
        self._render_pose_figure(draw, cx=self.width // 2, cy=int(self.height * 0.58), scale=1.15, pose_type=pose, palette=palette, frame_phase=frame_phase)

        # 4. Render Cartoon Slapstick FX (Impact stars, wind gusts, comic symbols)
        self._render_action_vfx(draw, pose, camera_shot, frame_phase)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out_path), "PNG")
        return out_path

    def _render_cinematic_background(self, draw: ImageDraw.ImageDraw, theme: str, camera_shot: str):
        W, H = self.width, self.height

        if theme == "sunny_sidewalk" or theme == "street_perspective":
            # Stylized vibrant sunny avenue with dramatic perspective
            # Sky gradient
            for y in range(0, int(H * 0.65)):
                r = int(125 + 110 * (y / (H * 0.65)))
                g = int(211 + 35 * (y / (H * 0.65)))
                b = 252
                draw.line([(0, y), (W, y)], fill=(r, g, b, 255))
            
            # Stylized urban sidewalk & road
            ground_y = int(H * 0.65)
            draw.rectangle([(0, ground_y), (W, ground_y + 40)], fill=(74, 222, 128, 255)) # Green park strip
            draw.rectangle([(0, ground_y + 40), (W, H)], fill=(203, 213, 225, 255)) # Paved sidewalk
            
            # Perspective sidewalk slabs
            for x in range(-200, W + 400, 240):
                draw.line([(x, ground_y + 40), (x - 140, H)], fill=(148, 163, 184, 255), width=5)

            # Background cartoon buildings & telephone poles
            draw.rectangle([(120, int(H * 0.35)), (380, ground_y)], fill=(254, 205, 211, 255), outline=(244, 63, 94, 255), width=4)
            draw.rectangle([(1400, int(H * 0.28)), (1750, ground_y)], fill=(199, 210, 254, 255), outline=(99, 102, 241, 255), width=4)

            # Fluffy cartoon clouds
            for cx, cy in [(320, 160), (1050, 130), (1600, 190)]:
                draw.ellipse([(cx - 110, cy - 35), (cx + 110, cy + 35)], fill=(255, 255, 255, 240))
                draw.ellipse([(cx - 40, cy - 65), (cx + 40, cy + 25)], fill=(255, 255, 255, 240))

        elif theme == "speed_hallway":
            # Dynamic speed corridor with converging lines
            draw.rectangle([(0, 0), (W, H)], fill=(30, 27, 75, 255))
            cx, cy = W // 2, H // 2
            # Radiant speed streak polygons
            for angle in range(0, 360, 20):
                rad = math.radians(angle)
                x = cx + math.cos(rad) * 1400
                y = cy + math.sin(rad) * 1400
                draw.line([(cx, cy), (x, y)], fill=(99, 102, 241, 100), width=6)

        elif theme == "dramatic_spotlight":
            # Dark theatrical backdrop with single harsh overhead spotlight
            draw.rectangle([(0, 0), (W, H)], fill=(15, 23, 42, 255))
            # Glowing yellow cone spotlight
            cone_pts = [(W // 2 - 100, 0), (W // 2 + 100, 0), (W // 2 + 550, H), (W // 2 - 550, H)]
            draw.polygon(cone_pts, fill=(254, 240, 138, 70))
            draw.ellipse([(W // 2 - 500, H - 240), (W // 2 + 500, H - 20)], fill=(254, 240, 138, 120))

        else: # Comic burst
            draw.rectangle([(0, 0), (W, H)], fill=(254, 243, 199, 255))
            cx, cy = W // 2, H // 2
            for a in range(0, 360, 12):
                rad = math.radians(a)
                x1 = cx + math.cos(rad) * 1500
                y1 = cy + math.sin(rad) * 1500
                draw.line([(cx, cy), (x1, y1)], fill=(245, 158, 11, 80), width=8)

    def _render_pose_figure(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, pose_type: str, palette: Dict[str, str], frame_phase: float):
        """Renders authentic 2D Storytime dynamic physical poses."""
        hoodie_color = palette.get("hoodie", "#2563EB")
        hair_color = palette.get("hair", "#2D1B18")
        skin_color = palette.get("skin", "#FFE0BD")
        line_color = palette.get("line", "#0F172A")
        pants_color = "#1E293B"
        shoe_color = "#E2E8F0"
        lw = max(4, int(7 * scale))

        if pose_type == "walk_swagger":
            # 1. Full-body walking swagger: one leg forward, one leg back, arms swinging high, head tilted confidently
            bob = int(math.sin(frame_phase * math.pi * 2) * 15 * scale)
            head_y = cy - int(240 * scale) + bob

            # Legs (Striding wide apart)
            # Left leg (forward)
            draw.line([(cx - int(30 * scale), cy + int(100 * scale) + bob), (cx - int(90 * scale), cy + int(240 * scale))], fill=pants_color, width=int(32 * scale))
            draw.ellipse([(cx - int(120 * scale), cy + int(230 * scale)), (cx - int(50 * scale), cy + int(270 * scale))], fill=shoe_color, outline=line_color, width=lw)
            # Right leg (back)
            draw.line([(cx + int(30 * scale), cy + int(100 * scale) + bob), (cx + int(100 * scale), cy + int(245 * scale))], fill=pants_color, width=int(32 * scale))
            draw.ellipse([(cx + int(70 * scale), cy + int(235 * scale)), (cx + int(140 * scale), cy + int(275 * scale))], fill=shoe_color, outline=line_color, width=lw)

            # Torso / Hoodie (Tilted forward with swag)
            draw.ellipse([(cx - int(110 * scale), cy - int(70 * scale) + bob), (cx + int(110 * scale), cy + int(140 * scale) + bob)], fill=hoodie_color, outline=line_color, width=lw)

            # Left Arm (Swinging high forward)
            arm_pts = [(cx - int(90 * scale), cy - int(30 * scale) + bob), (cx - int(140 * scale), cy + int(40 * scale) + bob), (cx - int(180 * scale), cy - int(20 * scale) + bob)]
            draw.line(arm_pts, fill=hoodie_color, width=int(26 * scale))
            draw.ellipse([(cx - int(195 * scale), cy - int(35 * scale) + bob), (cx - int(160 * scale), cy + bob)], fill=skin_color, outline=line_color, width=lw)

            # Right Arm (Back)
            arm_pts_r = [(cx + int(90 * scale), cy - int(30 * scale) + bob), (cx + int(150 * scale), cy + int(70 * scale) + bob)]
            draw.line(arm_pts_r, fill=hoodie_color, width=int(26 * scale))

            # Head (Tilted with sunglasses / swagger smile)
            self._draw_head_with_expression(draw, cx, head_y, scale, hair_color, skin_color, line_color, lw, emotion="happy_oblivious", sunglasses=True)

        elif pose_type == "pants_rip_shock":
            # 2. THE TORN PANTS DISASTER GAG:
            # Character seen in 3/4 REAR profile, looking back over shoulder in catastrophic horror!
            # Hands clutching torn trousers, cartoon blush, icy breeze whistling through tear!
            shake_x = int(math.sin(frame_phase * 15) * 8)
            cx_s = cx + shake_x

            # Legs (Knocked-knees in sheer panic)
            draw.line([(cx_s - int(60 * scale), cy + int(80 * scale)), (cx_s - int(40 * scale), cy + int(170 * scale)), (cx_s - int(75 * scale), cy + int(250 * scale))], fill=pants_color, width=int(32 * scale))
            draw.line([(cx_s + int(60 * scale), cy + int(80 * scale)), (cx_s + int(40 * scale), cy + int(170 * scale)), (cx_s + int(75 * scale), cy + int(250 * scale))], fill=pants_color, width=int(32 * scale))
            draw.ellipse([(cx_s - int(105 * scale), cy + int(240 * scale)), (cx_s - int(35 * scale), cy + int(275 * scale))], fill=shoe_color, outline=line_color, width=lw)
            draw.ellipse([(cx_s + int(35 * scale), cy + int(240 * scale)), (cx_s + int(105 * scale), cy + int(275 * scale))], fill=shoe_color, outline=line_color, width=lw)

            # Torso & Torn Rear:
            draw.ellipse([(cx_s - int(130 * scale), cy - int(90 * scale)), (cx_s + int(130 * scale), cy + int(120 * scale))], fill=hoodie_color, outline=line_color, width=lw)
            # Rear pants section:
            draw.ellipse([(cx_s - int(100 * scale), cy + int(30 * scale)), (cx_s + int(100 * scale), cy + int(120 * scale))], fill=pants_color, outline=line_color, width=lw)

            # THE MASSIVE CARTOON JAGGED TEAR:
            rip_pts = [
                (cx_s - int(25 * scale), cy + int(40 * scale)),
                (cx_s + int(5 * scale), cy + int(65 * scale)),
                (cx_s - int(15 * scale), cy + int(85 * scale)),
                (cx_s + int(20 * scale), cy + int(105 * scale)),
                (cx_s - int(5 * scale), cy + int(120 * scale))
            ]
            draw.line(rip_pts, fill="#FFFFFF", width=int(14 * scale))
            draw.line(rip_pts, fill="#FF69B4", width=int(6 * scale)) # Bright polka-dot boxer reveal!

            # Both hands frantically clutching behind in comic desperation!
            draw.ellipse([(cx_s - int(80 * scale), cy + int(70 * scale)), (cx_s - int(30 * scale), cy + int(115 * scale))], fill=skin_color, outline=line_color, width=lw)
            draw.ellipse([(cx_s + int(30 * scale), cy + int(70 * scale)), (cx_s + int(80 * scale), cy + int(115 * scale))], fill=skin_color, outline=line_color, width=lw)

            # Head whipped around 180 degrees looking backward in absolute shock
            head_y = cy - int(210 * scale)
            self._draw_head_with_expression(draw, cx_s, head_y, scale, hair_color, skin_color, line_color, lw, emotion="shocked", sunglasses=False)

        elif pose_type == "sonic_sprint":
            # 3. Sonic Speed Sprint: Body pitched forward at 45 degrees, legs in spinning smoke wheel
            cx_sp = cx + int(math.sin(frame_phase * 20) * 12)
            cy_sp = cy + 40

            # Cartoon spinning dust wheel of legs
            dust_center = (cx_sp - int(80 * scale), cy_sp + int(160 * scale))
            draw.ellipse([(dust_center[0] - int(110 * scale), dust_center[1] - int(60 * scale)), (dust_center[0] + int(110 * scale), dust_center[1] + int(60 * scale))], fill=(241, 245, 249, 200), outline=(203, 213, 225, 255), width=lw)
            # Spinning legs streaks
            for a in range(0, 360, 45):
                rad = math.radians(a + frame_phase * 180)
                lx = dust_center[0] + math.cos(rad) * 90 * scale
                ly = dust_center[1] + math.sin(rad) * 45 * scale
                draw.line([dust_center, (lx, ly)], fill=pants_color, width=int(16 * scale))

            # Pitched Torso
            torso_box = [(cx_sp - int(120 * scale), cy_sp - int(120 * scale)), (cx_sp + int(140 * scale), cy_sp + int(70 * scale))]
            draw.ellipse(torso_box, fill=hoodie_color, outline=line_color, width=lw)

            # Flailing Arms
            draw.line([(cx_sp + int(60 * scale), cy_sp - int(40 * scale)), (cx_sp + int(170 * scale), cy_sp - int(110 * scale))], fill=hoodie_color, width=int(24 * scale))
            draw.line([(cx_sp - int(60 * scale), cy_sp - int(40 * scale)), (cx_sp - int(160 * scale), cy_sp - int(90 * scale))], fill=hoodie_color, width=int(24 * scale))

            head_y = cy_sp - int(220 * scale)
            self._draw_head_with_expression(draw, cx_sp + int(70 * scale), head_y, scale, hair_color, skin_color, line_color, lw, emotion="panicked", sunglasses=False)

        elif pose_type == "hoodie_sink":
            # 4. Embarrassment: Sinking completely into oversized hoodie collar like a turtle, tomato red face
            draw.ellipse([(cx - int(170 * scale), cy - int(60 * scale)), (cx + int(170 * scale), cy + int(240 * scale))], fill=hoodie_color, outline=line_color, width=lw)
            # Giant raised hoodie collar swallowing face
            draw.ellipse([(cx - int(130 * scale), cy - int(120 * scale)), (cx + int(130 * scale), cy + int(40 * scale))], fill=hoodie_color, outline=line_color, width=lw)

            # Blushing red face peeking out barely
            peek_y = cy - int(100 * scale)
            draw.ellipse([(cx - int(80 * scale), peek_y - int(70 * scale)), (cx + int(80 * scale), peek_y + int(50 * scale))], fill=(248, 113, 113, 255), outline=line_color, width=lw) # Bright red blush skin!
            
            # Squeezed shut embarrassment eyes > <
            draw.line([(cx - int(45 * scale), peek_y - int(30 * scale)), (cx - int(25 * scale), peek_y - int(15 * scale)), (cx - int(45 * scale), peek_y)], fill=line_color, width=lw)
            draw.line([(cx + int(45 * scale), peek_y - int(30 * scale)), (cx + int(25 * scale), peek_y - int(15 * scale)), (cx + int(45 * scale), peek_y)], fill=line_color, width=lw)

            # Hair
            draw.ellipse([(cx - int(85 * scale), peek_y - int(110 * scale)), (cx + int(85 * scale), peek_y - int(50 * scale))], fill=hair_color, outline=line_color, width=lw)

        else: # Exaggerated Flail
            draw.ellipse([(cx - int(120 * scale), cy - int(70 * scale)), (cx + int(120 * scale), cy + int(150 * scale))], fill=hoodie_color, outline=line_color, width=lw)
            self._draw_head_with_expression(draw, cx, cy - int(210 * scale), scale, hair_color, skin_color, line_color, lw, emotion="shocked", sunglasses=False)

    def _draw_head_with_expression(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, hair_color: str, skin_color: str, line_color: str, lw: int, emotion: str, sunglasses: bool = False):
        head_r = int(115 * scale)
        # Head base
        draw.ellipse([(cx - head_r, cy - head_r), (cx + head_r, cy + head_r)], fill=skin_color, outline=line_color, width=lw)

        # Hair bangs
        hair_pts = [
            (cx - head_r - int(10 * scale), cy + int(10 * scale)),
            (cx - head_r, cy - head_r - int(20 * scale)),
            (cx - int(50 * scale), cy - head_r - int(35 * scale)),
            (cx, cy - head_r - int(20 * scale)),
            (cx + int(60 * scale), cy - head_r - int(40 * scale)),
            (cx + head_r + int(10 * scale), cy - head_r - int(15 * scale)),
            (cx + head_r, cy + int(10 * scale)),
            (cx + int(40 * scale), cy - int(40 * scale)),
            (cx - int(20 * scale), cy - int(30 * scale)),
            (cx - int(60 * scale), cy - int(50 * scale))
        ]
        draw.polygon(hair_pts, fill=hair_color, outline=line_color)

        if sunglasses:
            # Cool black sunglasses for walk swagger
            draw.rounded_rectangle([(cx - int(75 * scale), cy - int(25 * scale)), (cx - int(10 * scale), cy + int(20 * scale))], radius=6, fill="#0F172A")
            draw.rounded_rectangle([(cx + int(10 * scale), cy - int(25 * scale)), (cx + int(75 * scale), cy + int(20 * scale))], radius=6, fill="#0F172A")
            draw.line([(cx - int(10 * scale), cy - int(5 * scale)), (cx + int(10 * scale), cy - int(5 * scale))], fill="#0F172A", width=max(3, int(5 * scale)))
            # Smug grin
            draw.arc([(cx - int(35 * scale), cy + int(25 * scale)), (cx + int(35 * scale), cy + int(65 * scale))], start=10, end=170, fill=line_color, width=lw)
        elif emotion == "shocked":
            # Giant cartoon bulging eyes popping out of skull!
            for ex in [cx - int(50 * scale), cx + int(50 * scale)]:
                draw.ellipse([(ex - int(35 * scale), cy - int(45 * scale)), (ex + int(35 * scale), cy + int(25 * scale))], fill="#FFFFFF", outline=line_color, width=lw)
                # Tiny pinprick pupil
                draw.ellipse([(ex - int(5 * scale), cy - int(10 * scale)), (ex + int(5 * scale), cy)], fill=line_color)
            # Arched surprised eyebrows high in the air
            draw.line([(cx - int(75 * scale), cy - int(70 * scale)), (cx - int(25 * scale), cy - int(80 * scale))], fill=line_color, width=lw + 2)
            draw.line([(cx + int(25 * scale), cy - int(80 * scale)), (cx + int(75 * scale), cy - int(70 * scale))], fill=line_color, width=lw + 2)
            # Wide jaw-dropped open mouth
            draw.chord([(cx - int(30 * scale), cy + int(35 * scale)), (cx + int(30 * scale), cy + int(95 * scale))], start=0, end=180, fill="#991B1B", outline=line_color, width=lw)
        elif emotion == "panicked":
            for ex in [cx - int(45 * scale), cx + int(45 * scale)]:
                draw.ellipse([(ex - int(30 * scale), cy - int(40 * scale)), (ex + int(30 * scale), cy + int(20 * scale))], fill="#FFFFFF", outline=line_color, width=lw)
                draw.ellipse([(ex - int(8 * scale), cy - int(10 * scale)), (ex + int(8 * scale), cy + int(6 * scale))], fill=line_color)
            # Screaming mouth
            draw.ellipse([(cx - int(35 * scale), cy + int(30 * scale)), (cx + int(35 * scale), cy + int(80 * scale))], fill="#991B1B", outline=line_color, width=lw)

    def _render_action_vfx(self, draw: ImageDraw.ImageDraw, pose: str, camera_shot: str, frame_phase: float):
        """Draws impactful 2D cartoon visual effects (wind gusts, comic exclamation, speed streaks)."""
        W, H = self.width, self.height
        cx, cy = W // 2, H // 2

        if pose == "pants_rip_shock":
            # 1. Giant cartoon red Exclamation Mark '!' hovering above head
            ex_x, ex_y = cx + 180, cy - 340
            draw.rounded_rectangle([(ex_x - 18, ex_y - 80), (ex_x + 18, ex_y + 10)], radius=8, fill="#EF4444", outline="#7F1D1D", width=4)
            draw.ellipse([(ex_x - 18, ex_y + 25), (ex_x + 18, ex_y + 60)], fill="#EF4444", outline="#7F1D1D", width=4)

            # 2. Cold icy wind swirl lines coming through the pants rip
            wind_pts = [(cx - 280, cy + 90), (cx - 100, cy + 70), (cx + 10, cy + 90), (cx + 140, cy + 60)]
            draw.line(wind_pts, fill=(56, 189, 248, 220), width=6)
            draw.line([(cx - 220, cy + 120), (cx - 50, cy + 105), (cx + 80, cy + 120)], fill=(56, 189, 248, 180), width=4)

            # 3. Cartoon sweat explosion drops flying outward
            for dx, dy in [(-180, -220), (220, -200), (280, -100), (-250, -80)]:
                draw.ellipse([(cx + dx - 12, cy + dy - 12), (cx + dx + 12, cy + dy + 12)], fill=(56, 189, 248, 240), outline="#0284C7", width=3)

        elif pose == "sonic_sprint":
            # Speed streaks trailing behind
            for y_line in [cy - 80, cy, cy + 80, cy + 160]:
                x_start = cx - 750 + int(frame_phase * 200) % 300
                draw.line([(x_start, y_line), (x_start + 450, y_line)], fill=(255, 255, 255, 180), width=7)

        elif pose == "hoodie_sink":
            # Cartoon steam puffs coming from ears
            for side in [-1, 1]:
                sx = cx + side * 140
                sy = cy - 200
                draw.ellipse([(sx - 20, sy - 20), (sx + 20, sy + 20)], fill=(255, 255, 255, 200))
                x_a = sx + side * 20
                x_b = sx + side * 60
                draw.ellipse([(min(x_a, x_b), sy - 50), (max(x_a, x_b), sy - 10)], fill=(255, 255, 255, 160))

class CharacterSceneEngine:
    def __init__(self, comfy_host: str = "127.0.0.1", comfy_port: int = 8188):
        self.action_artist = CinematicActionArtist()

    def generate_character_anchor(self, character_name: str, palette: Dict[str, str], out_path: Path) -> Path:
        return self.action_artist.render_anchor_sheet(character_name, palette, out_path)

    def generate_scene_image(
        self,
        scene_id: int,
        scene_type: str,
        character_action: str,
        camera_shot: str,
        visual_prompt: str,
        emotion: str,
        palette: Dict[str, str],
        out_path: Path
    ) -> Path:
        return self.action_artist.render_cinematic_action_scene(
            scene_id=scene_id,
            scene_type=scene_type,
            character_action=character_action,
            camera_shot=camera_shot,
            emotion=emotion,
            palette=palette,
            out_path=out_path
        )

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    engine = CharacterSceneEngine()
    palette = {"hair": "#2D1B18", "skin": "#FFE0BD", "hoodie": "#2563EB", "line": "#0F172A"}
    test_scene = base / "assets" / "characters" / "action_scene_test.png"
    engine.generate_scene_image(
        scene_id=2,
        scene_type="slapstick",
        character_action="freezes in terror discovering pants are torn",
        camera_shot="dynamic_low_angle_crash_zoom",
        visual_prompt="slapstick rear torn pants shock shot",
        emotion="shocked",
        palette=palette,
        out_path=test_scene
    )
    print("Action scene test rendered successfully!")
