import math
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2

class VyondVectorArtist:
    """
    Production-Grade 2D Vector Explainer & Puppet Animation Engine.
    Accurately reproduces the visual aesthetics of:
    - Reference Image 1: Modern 2D shaded character with red glasses on green screen.
    - Reference Image 2: Multi-character beach scene with waving family & Arab gentleman.
    """
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def render_scene(
        self,
        theme: str = "tropical_beach",
        characters: Optional[List[Dict[str, Any]]] = None,
        time_sec: float = 0.0,
        green_screen: bool = False,
        out_path: Optional[Path] = None
    ) -> Image.Image:
        W, H = self.width, self.height
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if green_screen or theme == "green_screen":
            # Chroma key #00b050 as in Image 1
            draw.rectangle([(0, 0), (W, H)], fill=(0, 176, 80, 255))
        elif theme == "tropical_beach":
            self._draw_tropical_beach_background(draw, W, H, time_sec)
        elif theme == "modern_office":
            self._draw_office_background(draw, W, H)
        else:
            self._draw_gradient_backdrop(draw, W, H)

        # Default cast if none specified
        if characters is None:
            if green_screen or theme == "green_screen":
                characters = [{"type": "modern_boy_red_glasses", "x": W // 2, "y": int(H * 0.92), "scale": 1.45, "action": "idle"}]
            else:
                characters = [
                    {"type": "woman_purple_top", "x": 380, "y": int(H * 0.88), "scale": 1.05, "action": "wave"},
                    {"type": "girl_yellow_shirt", "x": 620, "y": int(H * 0.88), "scale": 0.95, "action": "wave"},
                    {"type": "arab_man_thobe", "x": 920, "y": int(H * 0.88), "scale": 1.15, "action": "wave"},
                    {"type": "man_blue_polo", "x": 1200, "y": int(H * 0.88), "scale": 1.10, "action": "wave"},
                    {"type": "boy_green_sweater", "x": 1440, "y": int(H * 0.88), "scale": 0.90, "action": "wave"}
                ]

        # Draw characters
        for char_info in characters:
            self._render_character(
                draw=draw,
                char_type=char_info.get("type", "modern_boy_red_glasses"),
                cx=char_info.get("x", W // 2),
                cy=char_info.get("y", int(H * 0.88)),
                scale=char_info.get("scale", 1.0),
                action=char_info.get("action", "wave"),
                time_sec=time_sec
            )

        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(out_path), "PNG")

        return img

    def _draw_tropical_beach_background(self, draw: ImageDraw.ImageDraw, W: int, H: int, time_sec: float):
        # 1. Sky with subtle gradient
        for y in range(0, int(H * 0.35)):
            r = int(70 + 35 * (y / (H * 0.35)))
            g = int(160 + 35 * (y / (H * 0.35)))
            b = 250
            draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

        # Drifting geometric flat clouds (Vyond style)
        cloud_offsets = [(200, 60, 120), (550, 140, 160), (1600, 120, 220)]
        for cx_base, cy, cw in cloud_offsets:
            cx = (cx_base + int(time_sec * 12)) % (W + 200) - 100
            draw.rounded_rectangle([(cx - cw//2, cy - 14), (cx + cw//2, cy + 14)], radius=14, fill=(255, 255, 255, 245))
            draw.rounded_rectangle([(cx - cw//4, cy - 26), (cx + cw//4, cy + 8)], radius=14, fill=(255, 255, 255, 245))

        # 2. Azure Ocean
        draw.rectangle([(0, int(H * 0.35)), (W, int(H * 0.69))], fill=(24, 144, 255, 255))
        draw.line([(0, int(H * 0.35)), (W, int(H * 0.35))], fill=(16, 120, 220, 255), width=3)
        # Gentle wave ripples
        for wy in range(int(H * 0.38), int(H * 0.68), 35):
            wave_shift = int(math.sin(time_sec * 2.0 + wy) * 20)
            for wx in range(0, W, 180):
                draw.line([(wx + wave_shift, wy), (wx + wave_shift + 70, wy)], fill=(40, 160, 255, 180), width=2)

        # 3. Sandy Shore
        shore_pts = [(0, int(H * 0.68)), (W, int(H * 0.70)), (W, H), (0, H)]
        draw.polygon(shore_pts, fill=(254, 226, 155, 255))

        # Sand dots
        for sx, sy in [(300, 780), (550, 820), (840, 760), (1150, 800), (1480, 830), (260, 940), (900, 960), (1350, 950)]:
            draw.ellipse([(sx - 3, sy - 2), (sx + 3, sy + 2)], fill=(225, 185, 120, 255))

        # 4. Red Beach Towel
        towel_pts = [(int(W * 0.52), int(H * 0.82)), (int(W * 0.75), int(H * 0.82)), (int(W * 0.74), int(H * 0.94)), (int(W * 0.51), int(H * 0.94))]
        draw.polygon(towel_pts, fill=(239, 68, 68, 255))

        # 5. Beach Umbrella (Red & White alternating)
        ux, uy = int(W * 0.80), int(H * 0.74)
        draw.line([(ux, uy - 120), (ux - 70, uy + 110)], fill=(160, 110, 60, 255), width=12)
        cx_u, cy_u = ux, uy - 120
        r_u = 145
        box = [(cx_u - r_u, cy_u - r_u), (cx_u + r_u, cy_u + r_u)]
        draw.pieslice(box, start=170, end=215, fill=(239, 68, 68, 255), outline=(220, 38, 38, 255), width=2)
        draw.pieslice(box, start=215, end=260, fill=(255, 255, 255, 255), outline=(220, 220, 220, 255), width=2)
        draw.pieslice(box, start=260, end=305, fill=(239, 68, 68, 255), outline=(220, 38, 38, 255), width=2)
        draw.pieslice(box, start=305, end=350, fill=(255, 255, 255, 255), outline=(220, 220, 220, 255), width=2)

        # 6. Lifesaver Ring
        lx, ly = int(W * 0.40), int(H * 0.78)
        draw.ellipse([(lx - 48, ly - 48), (lx + 48, ly + 48)], fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=3)
        for a in [0, 90, 180, 270]:
            draw.pieslice([(lx - 48, ly - 48), (lx + 48, ly + 48)], start=a - 20, end=a + 20, fill=(239, 68, 68, 255))
        draw.ellipse([(lx - 24, ly - 24), (lx + 24, ly + 24)], fill=(254, 226, 155, 255), outline=(220, 38, 38, 255), width=2)

        # 7. Coconut
        cox, coy = int(W * 0.77), int(H * 0.92)
        draw.ellipse([(cox - 22, coy - 18), (cox + 22, coy + 18)], fill=(120, 65, 30, 255))
        draw.ellipse([(cox - 14, coy - 12), (cox + 16, coy + 14)], fill=(255, 255, 255, 255))
        draw.ellipse([(cox - 6, coy - 5), (cox + 8, coy + 7)], fill=(254, 226, 155, 255))

        # 8. Left Palm Tree & Right Palm Tree
        self._draw_palm_tree(draw, -30, int(H * 0.78), scale=1.35, mirror=False)
        self._draw_palm_tree(draw, W - 20, int(H * 0.80), scale=1.25, mirror=True)

    def _draw_palm_tree(self, draw: ImageDraw.ImageDraw, x: int, y: int, scale: float, mirror: bool = False):
        sign = -1 if mirror else 1
        trunk_pts = []
        for i in range(12):
            t = i / 11.0
            tx = x + sign * int(math.sin(t * 1.4) * 110 * scale)
            ty = y - int(t * 460 * scale)
            trunk_pts.append((tx, ty))

        for i in range(len(trunk_pts) - 1):
            w = int((38 - i * 1.8) * scale)
            draw.line([trunk_pts[i], trunk_pts[i+1]], fill=(125, 105, 90, 255), width=w)
            draw.line([trunk_pts[i], trunk_pts[i+1]], fill=(95, 75, 65, 255), width=max(2, w // 4))

        top_x, top_y = trunk_pts[-1]
        for fa in [-140, -100, -60, -20, 20, 60, 100, 140]:
            rad = math.radians(fa)
            fx = top_x + math.cos(rad) * 220 * scale
            fy = top_y + math.sin(rad) * 120 * scale + (60 * scale if fa > 0 or fa < -90 else 0)
            mid_x = (top_x + fx) / 2 + math.cos(rad) * 40 * scale
            mid_y = (top_y + fy) / 2 - 40 * scale
            blade_pts = [(top_x, top_y), (int(mid_x), int(mid_y) - int(35 * scale)), (int(fx), int(fy)), (int(mid_x), int(mid_y) + int(20 * scale))]
            draw.polygon(blade_pts, fill=(34, 197, 94, 255), outline=(22, 163, 74, 255))

    def _draw_office_background(self, draw: ImageDraw.ImageDraw, W: int, H: int):
        # Modern glass corporate office
        draw.rectangle([(0, 0), (W, int(H * 0.75))], fill=(241, 245, 249, 255))
        draw.rectangle([(0, int(H * 0.75)), (W, H)], fill=(71, 85, 105, 255)) # Grey carpet
        # Skyscraper window
        draw.rectangle([(int(W * 0.1), int(H * 0.1)), (int(W * 0.9), int(H * 0.65))], fill=(224, 242, 254, 255), outline=(148, 163, 184, 255), width=4)
        for wx in range(int(W * 0.1), int(W * 0.9), int(W * 0.2)):
            draw.line([(wx, int(H * 0.1)), (wx, int(H * 0.65))], fill=(148, 163, 184, 255), width=4)

    def _draw_gradient_backdrop(self, draw: ImageDraw.ImageDraw, W: int, H: int):
        for y in range(H):
            r = int(15 + 25 * (y / H))
            g = int(23 + 45 * (y / H))
            b = int(42 + 65 * (y / H))
            draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    def _render_character(
        self,
        draw: ImageDraw.ImageDraw,
        char_type: str,
        cx: int,
        cy: int,
        scale: float,
        action: str,
        time_sec: float
    ):
        wave_angle = math.sin(time_sec * 6.5) * 26.0 if action == "wave" else 0.0

        if char_type == "modern_boy_red_glasses":
            self._render_modern_boy(draw, cx, cy, scale, wave_angle, action, time_sec)
        elif char_type == "arab_man_thobe":
            self._render_arab_man(draw, cx, cy, scale, wave_angle)
        elif char_type == "woman_purple_top":
            self._render_woman(draw, cx, cy, scale, wave_angle)
        elif char_type == "girl_yellow_shirt":
            self._render_girl(draw, cx, cy, scale, wave_angle)
        elif char_type == "boy_green_sweater":
            self._render_boy(draw, cx, cy, scale, wave_angle)
        else: # man_blue_polo
            self._render_tall_man(draw, cx, cy, scale, wave_angle)

    def _render_modern_boy(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float, action: str, time_sec: float):
        """High-definition puppet matching Image 1: Styled dark hair, red glasses, polo shirt, jeans, sneakers."""
        base_y = cy
        h_legs = int(200 * scale)
        h_torso = int(150 * scale)
        head_cy = base_y - h_legs - h_torso - int(65 * scale)

        # 1. Slim blue jeans with natural stance (Image 1)
        # Left leg (straight)
        draw.line([(cx - int(24 * scale), base_y - h_legs), (cx - int(32 * scale), base_y - int(12 * scale))], fill=(65, 125, 185, 255), width=int(26 * scale))
        # Right leg (relaxed ankle cross like Image 1)
        draw.line([(cx + int(24 * scale), base_y - h_legs), (cx + int(12 * scale), base_y - int(90 * scale)), (cx - int(12 * scale), base_y - int(18 * scale))], fill=(65, 125, 185, 255), width=int(24 * scale))

        # Sneakers (Black body, white thick soles, white laces)
        for sx in [cx - int(36 * scale), cx - int(6 * scale)]:
            draw.rounded_rectangle([(sx - int(18 * scale), base_y - int(24 * scale)), (sx + int(18 * scale), base_y)], radius=6, fill=(35, 35, 40, 255))
            draw.line([(sx - int(16 * scale), base_y - int(2 * scale)), (sx + int(16 * scale), base_y - int(2 * scale))], fill=(255, 255, 255, 255), width=int(5 * scale))
            # White lace stripes
            for ly in range(int(base_y - int(18 * scale)), int(base_y - int(6 * scale)), int(4 * scale)):
                draw.line([(sx - int(8 * scale), ly), (sx + int(8 * scale), ly)], fill=(255, 255, 255, 255), width=2)

        # 2. Torso (Lavender/White collared polo shirt)
        torso_box = [(cx - int(45 * scale), base_y - h_legs - h_torso), (cx + int(45 * scale), base_y - h_legs + int(8 * scale))]
        draw.rounded_rectangle(torso_box, radius=14, fill=(238, 240, 250, 255), outline=(210, 215, 235, 255), width=2)
        # Collar wings
        draw.polygon([(cx - int(24 * scale), base_y - h_legs - h_torso), (cx, base_y - h_legs - h_torso + int(28 * scale)), (cx - int(6 * scale), base_y - h_legs - h_torso)], fill=(255, 255, 255, 255))
        draw.polygon([(cx + int(24 * scale), base_y - h_legs - h_torso), (cx, base_y - h_legs - h_torso + int(28 * scale)), (cx + int(6 * scale), base_y - h_legs - h_torso)], fill=(255, 255, 255, 255))
        # Button placket line & small buttons
        draw.line([(cx, base_y - h_legs - h_torso + int(26 * scale)), (cx, base_y - h_legs - h_torso + int(60 * scale))], fill=(200, 205, 225, 255), width=2)
        draw.ellipse([(cx - int(2 * scale), base_y - h_legs - h_torso + int(36 * scale)), (cx + int(2 * scale), base_y - h_legs - h_torso + int(40 * scale))], fill=(180, 185, 205, 255))

        # 3. Arms & Hands
        # Left arm
        draw.line([(cx - int(45 * scale), base_y - h_legs - h_torso + int(24 * scale)), (cx - int(64 * scale), base_y - h_legs - int(30 * scale))], fill=(255, 218, 195, 255), width=int(18 * scale))
        draw.ellipse([(cx - int(74 * scale), base_y - h_legs - int(35 * scale)), (cx - int(54 * scale), base_y - h_legs - int(15 * scale))], fill=(255, 218, 195, 255))

        # Right arm (Waving or hanging)
        if action == "wave":
            shoulder = (cx + int(45 * scale), base_y - h_legs - h_torso + int(24 * scale))
            elbow = (cx + int(76 * scale), base_y - h_legs - h_torso - int(22 * scale))
            hand_rad = math.radians(wave_angle)
            hand = (elbow[0] + math.sin(hand_rad) * 48 * scale, elbow[1] - math.cos(hand_rad) * 48 * scale)
            draw.line([shoulder, elbow], fill=(255, 218, 195, 255), width=int(18 * scale))
            draw.line([elbow, hand], fill=(255, 218, 195, 255), width=int(16 * scale))
            draw.ellipse([(hand[0] - int(12 * scale), hand[1] - int(12 * scale)), (hand[0] + int(12 * scale), hand[1] + int(12 * scale))], fill=(255, 218, 195, 255))
        else:
            draw.line([(cx + int(45 * scale), base_y - h_legs - h_torso + int(24 * scale)), (cx + int(64 * scale), base_y - h_legs - int(30 * scale))], fill=(255, 218, 195, 255), width=int(18 * scale))
            draw.ellipse([(cx + int(54 * scale), base_y - h_legs - int(35 * scale)), (cx + int(74 * scale), base_y - h_legs - int(15 * scale))], fill=(255, 218, 195, 255))

        # 4. Head & Face
        draw.ellipse([(cx - int(46 * scale), head_cy - int(54 * scale)), (cx + int(46 * scale), head_cy + int(54 * scale))], fill=(255, 218, 195, 255))

        # Styled dark hair with layered brush volume
        hair_pts = [
            (cx - int(50 * scale), head_cy - int(10 * scale)),
            (cx - int(56 * scale), head_cy - int(60 * scale)),
            (cx - int(32 * scale), head_cy - int(92 * scale)),
            (cx + int(12 * scale), head_cy - int(96 * scale)),
            (cx + int(54 * scale), head_cy - int(68 * scale)),
            (cx + int(50 * scale), head_cy - int(10 * scale)),
            (cx + int(36 * scale), head_cy - int(32 * scale)),
            (cx - int(12 * scale), head_cy - int(48 * scale)),
            (cx - int(36 * scale), head_cy - int(32 * scale))
        ]
        draw.polygon(hair_pts, fill=(35, 30, 32, 255))

        # Big Blue Expressive Eyes with Highlights (Image 1 style)
        for ex in [cx - int(22 * scale), cx + int(22 * scale)]:
            draw.ellipse([(ex - int(15 * scale), head_cy - int(15 * scale)), (ex + int(15 * scale), head_cy + int(15 * scale))], fill=(255, 255, 255, 255), outline=(210, 180, 160, 255))
            draw.ellipse([(ex - int(9 * scale), head_cy - int(9 * scale)), (ex + int(9 * scale), head_cy + int(9 * scale))], fill=(30, 144, 255, 255))
            draw.ellipse([(ex - int(4 * scale), head_cy - int(4 * scale)), (ex + int(4 * scale), head_cy + int(4 * scale))], fill=(15, 23, 42, 255))
            draw.ellipse([(ex - int(4 * scale), head_cy - int(7 * scale)), (ex + int(2 * scale), head_cy - int(2 * scale))], fill=(255, 255, 255, 255))

        # THICK RED GLASSES (Image 1 Signature)
        for gx in [cx - int(22 * scale), cx + int(22 * scale)]:
            draw.rounded_rectangle([(gx - int(21 * scale), head_cy - int(19 * scale)), (gx + int(21 * scale), head_cy + int(19 * scale))], radius=6, outline=(225, 29, 72, 255), width=max(2, int(4 * scale)))
        draw.line([(cx - int(5 * scale), head_cy - int(2 * scale)), (cx + int(5 * scale), head_cy - int(2 * scale))], fill=(225, 29, 72, 255), width=max(2, int(4 * scale)))

        # Smile
        draw.arc([(cx - int(16 * scale), head_cy + int(16 * scale)), (cx + int(16 * scale), head_cy + int(34 * scale))], start=15, end=165, fill=(180, 70, 70, 255), width=max(2, int(3 * scale)))

    def _render_arab_man(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float):
        """Replica of Arab gentleman in Image 2: White thobe, red-checked keffiyeh, neat black beard, waving."""
        base_y = cy
        h_robe = int(320 * scale)
        head_cy = base_y - h_robe - int(45 * scale)

        # White Thobe
        thobe_pts = [(cx - int(42 * scale), base_y - h_robe), (cx + int(42 * scale), base_y - h_robe), (cx + int(60 * scale), base_y), (cx - int(60 * scale), base_y)]
        draw.polygon(thobe_pts, fill=(248, 250, 252, 255), outline=(226, 232, 240, 255))
        draw.line([(cx, base_y - h_robe), (cx, base_y - int(140 * scale))], fill=(203, 213, 225, 255), width=2)

        # Left arm
        draw.line([(cx - int(42 * scale), base_y - h_robe + int(30 * scale)), (cx - int(55 * scale), base_y - int(140 * scale))], fill=(248, 250, 252, 255), width=int(20 * scale))
        draw.ellipse([(cx - int(62 * scale), base_y - int(145 * scale)), (cx - int(46 * scale), base_y - int(125 * scale))], fill=(234, 185, 145, 255))

        # Right arm waving high
        shoulder = (cx + int(42 * scale), base_y - h_robe + int(30 * scale))
        elbow = (cx + int(70 * scale), base_y - h_robe - int(40 * scale))
        hand = (elbow[0] + math.sin(math.radians(wave_angle)) * 45 * scale, elbow[1] - math.cos(math.radians(wave_angle)) * 45 * scale)
        draw.line([shoulder, elbow], fill=(248, 250, 252, 255), width=int(20 * scale))
        draw.line([elbow, hand], fill=(234, 185, 145, 255), width=int(16 * scale))
        draw.ellipse([(hand[0] - int(12 * scale), hand[1] - int(12 * scale)), (hand[0] + int(12 * scale), hand[1] + int(12 * scale))], fill=(234, 185, 145, 255))

        # Head & Beard
        draw.ellipse([(cx - int(38 * scale), head_cy - int(45 * scale)), (cx + int(38 * scale), head_cy + int(45 * scale))], fill=(234, 185, 145, 255))
        beard_pts = [
            (cx - int(34 * scale), head_cy + int(5 * scale)), (cx - int(30 * scale), head_cy + int(42 * scale)),
            (cx, head_cy + int(50 * scale)), (cx + int(30 * scale), head_cy + int(42 * scale)),
            (cx + int(34 * scale), head_cy + int(5 * scale)), (cx + int(24 * scale), head_cy + int(25 * scale)),
            (cx, head_cy + int(30 * scale)), (cx - int(24 * scale), head_cy + int(25 * scale))
        ]
        draw.polygon(beard_pts, fill=(30, 27, 24, 255))

        # Eyes & Smile
        draw.ellipse([(cx - int(16 * scale), head_cy - int(8 * scale)), (cx - int(8 * scale), head_cy)], fill=(30, 27, 24, 255))
        draw.ellipse([(cx + int(8 * scale), head_cy - int(8 * scale)), (cx + int(16 * scale), head_cy)], fill=(30, 27, 24, 255))
        draw.arc([(cx - int(10 * scale), head_cy + int(12 * scale)), (cx + int(10 * scale), head_cy + int(22 * scale))], start=10, end=170, fill=(30, 27, 24, 255), width=2)

        # Keffiyeh & Agal
        draw.rounded_rectangle([(cx - int(44 * scale), head_cy - int(52 * scale)), (cx + int(44 * scale), head_cy - int(38 * scale))], radius=6, fill=(15, 15, 15, 255))
        keffiyeh_pts = [
            (cx - int(48 * scale), head_cy - int(40 * scale)), (cx - int(65 * scale), base_y - h_robe + int(70 * scale)),
            (cx - int(35 * scale), base_y - h_robe + int(50 * scale)), (cx - int(35 * scale), head_cy - int(20 * scale)),
            (cx + int(35 * scale), head_cy - int(20 * scale)), (cx + int(35 * scale), base_y - h_robe + int(50 * scale)),
            (cx + int(65 * scale), base_y - h_robe + int(70 * scale)), (cx + int(48 * scale), head_cy - int(40 * scale))
        ]
        draw.polygon(keffiyeh_pts, fill=(244, 63, 94, 255))
        for ky in range(int(head_cy - int(35 * scale)), int(base_y - h_robe + int(65 * scale)), int(10 * scale)):
            draw.line([(cx - int(55 * scale), ky), (cx + int(55 * scale), ky)], fill=(255, 255, 255, 140), width=2)

    def _render_woman(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float):
        base_y = cy
        head_cy = base_y - int(320 * scale)
        draw.line([(cx - int(12 * scale), base_y - int(120 * scale)), (cx - int(12 * scale), base_y)], fill=(234, 185, 145, 255), width=int(14 * scale))
        draw.line([(cx + int(12 * scale), base_y - int(120 * scale)), (cx + int(12 * scale), base_y)], fill=(234, 185, 145, 255), width=int(14 * scale))
        draw.polygon([(cx - int(32 * scale), base_y - int(210 * scale)), (cx + int(32 * scale), base_y - int(210 * scale)), (cx + int(36 * scale), base_y - int(120 * scale)), (cx - int(36 * scale), base_y - int(120 * scale))], fill=(78, 140, 180, 255))
        draw.polygon([(cx - int(28 * scale), base_y - int(290 * scale)), (cx + int(28 * scale), base_y - int(290 * scale)), (cx + int(32 * scale), base_y - int(210 * scale)), (cx - int(32 * scale), base_y - int(210 * scale))], fill=(155, 75, 130, 255))
        shoulder = (cx + int(28 * scale), base_y - int(280 * scale))
        elbow = (cx + int(55 * scale), base_y - int(310 * scale))
        hand = (elbow[0] + math.sin(math.radians(wave_angle)) * 40 * scale, elbow[1] - math.cos(math.radians(wave_angle)) * 40 * scale)
        draw.line([shoulder, elbow], fill=(234, 185, 145, 255), width=int(14 * scale))
        draw.line([elbow, hand], fill=(234, 185, 145, 255), width=int(12 * scale))
        draw.ellipse([(cx - int(40 * scale), head_cy - int(45 * scale)), (cx + int(40 * scale), head_cy + int(25 * scale))], fill=(85, 50, 40, 255))
        draw.ellipse([(cx - int(28 * scale), head_cy - int(30 * scale)), (cx + int(28 * scale), head_cy + int(32 * scale))], fill=(234, 185, 145, 255))

    def _render_girl(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float):
        base_y = cy
        head_cy = base_y - int(260 * scale)
        draw.line([(cx - int(10 * scale), base_y - int(80 * scale)), (cx - int(10 * scale), base_y)], fill=(245, 205, 175, 255), width=int(12 * scale))
        draw.line([(cx + int(10 * scale), base_y - int(80 * scale)), (cx + int(10 * scale), base_y)], fill=(245, 205, 175, 255), width=int(12 * scale))
        draw.polygon([(cx - int(25 * scale), base_y - int(160 * scale)), (cx + int(25 * scale), base_y - int(160 * scale)), (cx + int(28 * scale), base_y - int(80 * scale)), (cx - int(28 * scale), base_y - int(80 * scale))], fill=(160, 65, 30, 255))
        draw.polygon([(cx - int(24 * scale), base_y - int(230 * scale)), (cx + int(24 * scale), base_y - int(160 * scale)), (cx + int(25 * scale), base_y - int(160 * scale)), (cx - int(25 * scale), base_y - int(160 * scale))], fill=(245, 185, 45, 255))
        shoulder = (cx - int(24 * scale), base_y - int(220 * scale))
        elbow = (cx - int(45 * scale), base_y - int(250 * scale))
        hand = (elbow[0] - math.sin(math.radians(wave_angle)) * 30 * scale, elbow[1] - math.cos(math.radians(wave_angle)) * 30 * scale)
        draw.line([shoulder, elbow], fill=(245, 185, 45, 255), width=int(12 * scale))
        draw.line([elbow, hand], fill=(245, 205, 175, 255), width=int(10 * scale))
        draw.ellipse([(cx - int(28 * scale), head_cy - int(30 * scale)), (cx + int(28 * scale), head_cy + int(30 * scale))], fill=(245, 205, 175, 255))
        draw.polygon([(cx - int(34 * scale), head_cy - int(35 * scale)), (cx + int(34 * scale), head_cy - int(35 * scale)), (cx + int(38 * scale), head_cy + int(10 * scale)), (cx - int(38 * scale), head_cy + int(10 * scale))], fill=(175, 110, 65, 255))

    def _render_tall_man(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float):
        base_y = cy
        head_cy = base_y - int(360 * scale)
        draw.line([(cx - int(16 * scale), base_y - int(160 * scale)), (cx - int(18 * scale), base_y)], fill=(110, 65, 35, 255), width=int(22 * scale))
        draw.line([(cx + int(16 * scale), base_y - int(160 * scale)), (cx + int(18 * scale), base_y)], fill=(110, 65, 35, 255), width=int(22 * scale))
        draw.rounded_rectangle([(cx - int(38 * scale), base_y - int(310 * scale)), (cx + int(38 * scale), base_y - int(160 * scale))], radius=8, fill=(25, 118, 210, 255))
        shoulder = (cx + int(38 * scale), base_y - int(295 * scale))
        elbow = (cx + int(70 * scale), base_y - int(335 * scale))
        hand = (elbow[0] + math.sin(math.radians(wave_angle)) * 40 * scale, elbow[1] - math.cos(math.radians(wave_angle)) * 40 * scale)
        draw.line([shoulder, elbow], fill=(25, 118, 210, 255), width=int(18 * scale))
        draw.line([elbow, hand], fill=(234, 185, 145, 255), width=int(14 * scale))
        draw.ellipse([(cx - int(30 * scale), head_cy - int(38 * scale)), (cx + int(30 * scale), head_cy + int(38 * scale))], fill=(234, 185, 145, 255))
        draw.polygon([(cx - int(32 * scale), head_cy - int(25 * scale)), (cx - int(34 * scale), head_cy - int(55 * scale)), (cx + int(15 * scale), head_cy - int(65 * scale)), (cx + int(35 * scale), head_cy - int(35 * scale)), (cx + int(25 * scale), head_cy - int(15 * scale))], fill=(135, 75, 45, 255))

    def _render_boy(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, wave_angle: float):
        base_y = cy
        head_cy = base_y - int(220 * scale)
        draw.line([(cx - int(12 * scale), base_y - int(90 * scale)), (cx - int(12 * scale), base_y)], fill=(100, 116, 139, 255), width=int(16 * scale))
        draw.line([(cx + int(12 * scale), base_y - int(90 * scale)), (cx + int(12 * scale), base_y)], fill=(100, 116, 139, 255), width=int(16 * scale))
        draw.rounded_rectangle([(cx - int(30 * scale), base_y - int(185 * scale)), (cx + int(30 * scale), base_y - int(90 * scale))], radius=8, fill=(45, 125, 95, 255))
        shoulder = (cx - int(30 * scale), base_y - int(170 * scale))
        elbow = (cx - int(55 * scale), base_y - int(210 * scale))
        hand = (elbow[0] - math.sin(math.radians(wave_angle)) * 30 * scale, elbow[1] - math.cos(math.radians(wave_angle)) * 30 * scale)
        draw.line([shoulder, elbow], fill=(45, 125, 95, 255), width=int(14 * scale))
        draw.line([elbow, hand], fill=(245, 205, 175, 255), width=int(12 * scale))
        draw.ellipse([(cx - int(28 * scale), head_cy - int(30 * scale)), (cx + int(28 * scale), head_cy + int(30 * scale))], fill=(245, 205, 175, 255))
        draw.polygon([(cx - int(32 * scale), head_cy - int(15 * scale)), (cx - int(38 * scale), head_cy - int(45 * scale)), (cx, head_cy - int(55 * scale)), (cx + int(38 * scale), head_cy - int(35 * scale)), (cx + int(25 * scale), head_cy - int(10 * scale))], fill=(160, 95, 55, 255))

    def render_vyond_video(
        self,
        theme: str = "tropical_beach",
        duration_sec: float = 4.0,
        audio_clip_path: Optional[Path] = None,
        out_mp4: Optional[Path] = None,
        characters: Optional[List[Dict[str, Any]]] = None,
        green_screen: bool = False,
        fps: int = 30
    ) -> Path:
        """
        Renders a full 30fps animation MP4 with continuous bone/arm waving, drifting clouds,
        and ocean ripples.
        """
        if out_mp4 is None:
            out_mp4 = Path("vyond_output.mp4")
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        total_frames = max(20, int(duration_sec * fps))

        temp_avi = out_mp4.with_suffix(".avi")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        vw = cv2.VideoWriter(str(temp_avi), fourcc, float(fps), (self.width, self.height))

        try:
            for f_idx in range(total_frames):
                time_sec = f_idx / float(fps)
                frame_pil = self.render_scene(
                    theme=theme,
                    characters=characters,
                    time_sec=time_sec,
                    green_screen=green_screen
                )
                frame_arr = np.array(frame_pil.convert("RGB"))
                bgr = cv2.cvtColor(frame_arr, cv2.COLOR_RGB2BGR)
                vw.write(bgr)
            vw.release()

            # Encode to MP4 with FFmpeg
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(temp_avi)
            ]
            if audio_clip_path and Path(audio_clip_path).exists():
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

