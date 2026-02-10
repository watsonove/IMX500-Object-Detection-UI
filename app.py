#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

import pygame
import pygame.surfarray as surfarray

from detector import IMX500Detector, FrameSnapshot
from steps import StepTransformer, build_step_text, build_gate_text, total_steps_for_level
from ui.theme import Theme
from ui.textlayout import TextLayout
from ui.renderer import Renderer


@dataclass(frozen=True)
class StepInfo:
    title: str
    body: str


class App:
    def __init__(self, args: argparse.Namespace):
        self.args = args

        # UI services
        self.theme = Theme()
        self.text_layout = TextLayout()
        self.renderer = Renderer(self.theme)

        # Pygame setup
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        
        self.screen = self._set_fullscreen()
        self.win_w, self.win_h = self.screen.get_size()
        pygame.display.set_caption("IMX500 GUI")

        # Assets paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.landing_bg_path = "assets/landingpagebg.jpg"
        self.font_path = "assets/Kanit-Bold.ttf"
        self.audio_dir = os.path.join(self.base_dir, "assets", "audio")
        self.qr_path = os.path.join(self.base_dir, "assets", "qr.png")

        # Background & Image caches
        self._landing_bg_original = None
        self._landing_bg_scaled = None
        self._landing_bg_scaled_size = None
        self._qr_code_img = None
        
        self._load_landing_bg()
        self._load_qr_code()

        # Application State
        self.running = True
        self.state = "LIVEINTRO"  # LIVEINTRO / LANDING / RUNNING / GATE
        self.mode = "LIVE"        # LIVE / ANALYSE
        self.step = 0             # 0=LIVE, 1..N=Analyse
        self.clock = pygame.time.Clock()

        # User Configuration
        self.lang = "DE"
        self.level = None  # "SCHUELER" / "STUDENT"

        # Logic Components
        self.detector: IMX500Detector | None = None
        self.transformer: StepTransformer | None = None
        self.snapshot: FrameSnapshot | None = None

        # Simulation / Rendering Caches
        self.sim_surface = None
        self.sim_step_cached: int | None = None

        # Gate Text Caches
        self.gate_cached_step: int | None = None
        self.gate_cached_title_font = None
        self.gate_cached_body_font = None
        self.gate_cached_title_lines = None
        self.gate_cached_body_lines = None

        # Gate Animation
        self.gate_anim_frames: list[pygame.Surface] | None = None
        self.gate_anim_key: str | None = None
        self.gate_anim_idx: int = 0
        self.gate_anim_last_ms: int = 0
        self.gate_anim_frame_ms: int = 55

        # Hitboxes (General)
        self.lang_button_rect = pygame.Rect(0, 0, 0, 0)
        self.home_button_rect = pygame.Rect(0, 0, 0, 0)
        self.level_left_rect = pygame.Rect(0, 0, 0, 0)
        self.level_right_rect = pygame.Rect(0, 0, 0, 0)
        self.cta_button_rect = pygame.Rect(0, 0, 0, 0)
        
        # Hitboxes (Gate)
        self.gate_prev_rect = pygame.Rect(0, 0, 0, 0)
        self.gate_next_rect = pygame.Rect(0, 0, 0, 0)
        
        # Hitboxes (Navigation/Audio)
        self.nav_prev_rect = pygame.Rect(0, 0, 0, 0)
        self.nav_next_rect = pygame.Rect(0, 0, 0, 0)
        self.nav_action_rect = pygame.Rect(0, 0, 0, 0)
        self.nav_audio_rect = pygame.Rect(0, 0, 0, 0)
        
        # Audio State
        self.current_audio_file: str | None = None
        self.audio_is_paused = False

        # Gate Logic
        self.gate_next_step: int | None = None

        # Text Resources
        self.UI = {
            "DE": {
                "landing_title": "KI OBJEKTERKENNUNG",
                "landing_sub": "wähle hier dein Niveau",
                "level_left": "Schüler:in",
                "level_right": "Student:in",
                "hint": "ESC/q zum Beenden",
                "live_hint": "SPACE: Analyse",
                "quit_hint": "ESC/q: Quit",
                "analyse_hint": "ENTER next | BACKSPACE prev | SPACE end",
                "workflow": "Workflow",
                "workflow_hint": "SPACE friert ein & wechselt zu Analyse.",
                "lang_label": "DE",
                "liveintro_cta": "Was erkennt die KI? / What does the AI detect?",
                "home": "Home",
                "gate_btn": "Weiter",
                "back": "Zurück"
            },
            "EN": {
                "landing_title": "AI OBJECT DETECTION",
                "landing_sub": "choose your level",
                "level_left": "Pupil",
                "level_right": "Student",
                "hint": "ESC/q to quit",
                "live_hint": "SPACE: Analyse",
                "quit_hint": "ESC/q: Quit",
                "analyse_hint": "ENTER next | BACKSPACE prev | SPACE end",
                "workflow": "Workflow",
                "workflow_hint": "SPACE freezes & switches to Analyse.",
                "lang_label": "EN",
                "liveintro_cta": "Was erkennt die KI? / What does the AI detect?",
                "home": "Home",
                "gate_btn": "Continue",
                "back": "Back"
            },
        }

        self._recompute_responsive()

    # ---------------- Responsive System ----------------
    def _scale(self) -> float:
        s_w = self.win_w / 1920.0
        s_h = self.win_h / 1080.0
        return max(0.6, min(1.6, (s_w + s_h) * 0.5))

    def _fsize(self, px: float) -> int:
        return max(12, int(px * self._scale()))

    def _load_font(self, size: int) -> pygame.font.Font:
        try:
            return pygame.font.Font(self.font_path, size)
        except Exception:
            return pygame.font.Font(None, size)

    def _recompute_responsive(self) -> None:
        self.win_w, self.win_h = self.screen.get_size()

        self.font_ui = self._load_font(self._fsize(22))
        self.font_small = self._load_font(self._fsize(20))
        self.font_header = self._load_font(self._fsize(28))
        self.font_title = self._load_font(self._fsize(38))
        self.font_landing_title = self._load_font(self._fsize(86))
        self.font_landing_sub = self._load_font(self._fsize(44))
        self.font_landing_btn = self._load_font(self._fsize(44))

        self.pad = max(12, int(18 * self._scale()))
        
        # Button sizes
        self.lang_btn_w = max(72, int(92 * self._scale()))
        self.lang_btn_h = max(36, int(44 * self._scale()))
        self.home_btn_w = max(int(96 * self._scale()), 80)
        self.home_btn_h = max(int(44 * self._scale()), 34)
        
        self.level_radius = max(18, int(28 * self._scale()))
        self.level_border_w = max(2, int(4 * self._scale()))

        self._landing_bg_scaled = None
        self._landing_bg_scaled_size = None

    # ---------------- Helpers ----------------
    def _t(self, key: str) -> str:
        return self.UI[self.lang][key]

    def _total_steps(self) -> int:
        return total_steps_for_level(self.level or "SCHUELER")

    def _step_map(self) -> Dict[int, object]:
        assert self.snapshot is not None
        assert self.level is not None
        return build_step_text(lang=self.lang, level=self.level, debug=self.snapshot.debug)

    def _gate_map(self) -> Dict[int, object]:
        assert self.snapshot is not None
        assert self.level is not None
        return build_gate_text(lang=self.lang, level=self.level, debug=self.snapshot.debug)

    def _set_fullscreen(self) -> pygame.Surface:
        info = pygame.display.Info()
        return pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)

    def _invalidate_caches(self) -> None:
        self.sim_step_cached = None
        self.gate_cached_step = None
        self._stop_audio()

    def _ensure_camera(self) -> None:
        if self.detector is None:
            self.detector = IMX500Detector(self.args)
        if self.snapshot is None:
            self.snapshot = FrameSnapshot(src_size=(self.args.cam_width, self.args.cam_height))

    def _go_home(self) -> None:
        self.state = "LIVEINTRO"
        self.mode = "LIVE"
        self.step = 0
        self.level = None
        self.gate_next_step = None
        self._invalidate_caches()

    def _is_student(self) -> bool:
        return self.level == "STUDENT"

    def _load_landing_bg(self) -> None:
        try:
            path = os.path.join(self.base_dir, self.landing_bg_path)
            self._landing_bg_original = pygame.image.load(path).convert()
        except Exception:
            self._landing_bg_original = None
        self._landing_bg_scaled = None
        self._landing_bg_scaled_size = None

    def _load_qr_code(self) -> None:
        try:
            self._qr_code_img = pygame.image.load(self.qr_path).convert_alpha()
        except Exception as e:
            print(f"Warning: QR Code not found at {self.qr_path} ({e})")
            self._qr_code_img = None

    def _get_landing_bg_scaled(self) -> pygame.Surface | None:
        if self._landing_bg_original is None:
            return None
        size = (self.win_w, self.win_h)
        if self._landing_bg_scaled is None or self._landing_bg_scaled_size != size:
            self._landing_bg_scaled = pygame.transform.smoothscale(self._landing_bg_original, size)
            self._landing_bg_scaled_size = size
        return self._landing_bg_scaled

    # ---------------- Audio Logic ----------------
    def _get_audio_filename(self) -> str | None:
        """Ermittelt den Dateinamen basierend auf Level und Step."""
        # STRIKTE REGEL: Audio NUR fuer SCHUELER
        if self.level != "SCHUELER":
            return None
            
        if self.lang == "EN":
             filename = f"schueler_step_{self.step}_english.mp3"
        else:
             filename = f"schueler_step_{self.step}.mp3"

        path = os.path.join(self.audio_dir, filename)
        if os.path.exists(path):
            return path
        return None

    def _toggle_audio(self) -> None:
        if self.audio_is_paused:
            pygame.mixer.music.unpause()
            self.audio_is_paused = False
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.audio_is_paused = True
            return

        path = self._get_audio_filename()
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self.current_audio_file = path
                self.audio_is_paused = False
            except Exception as e:
                print(f"Audio error: {e}")

    def _stop_audio(self) -> None:
        pygame.mixer.music.stop()
        self.audio_is_paused = False
        self.current_audio_file = None

    # ---------------- Layout Calculation ----------------
    def make_layout(self) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect, Optional[pygame.Rect]]:
        pad = self.pad
        
        # 1. Panel Decision
        show_panel = False
        if self.mode == "ANALYSE":
            if self.level == "SCHUELER":
                show_panel = (self.step >= 3)
            else:
                show_panel = (self.step >= 6)
        
        # 2. Vertical Grid
        title_h = max(60, int(80 * self._scale()))
        nav_h = max(80, int(100 * self._scale()))
        available_h = self.win_h - title_h - nav_h - 4 * pad
        y_title = pad
        y_content = y_title + title_h + pad
        y_nav = y_content + available_h + pad

        # 3. Horizontal Grid
        # Change: Force 1:1 Aspect Ratio (Square) ONLY for Student Steps 2-6
        target_ar = 16 / 9
        if self.level == "STUDENT" and (2 <= self.step <= 6):
            target_ar = 1.0  # 9:9 Aspect Ratio (Square)

        if show_panel:
            panel_w = max(int(350 * self._scale()), int(self.win_w * 0.28))
            max_video_w = self.win_w - panel_w - 3 * pad
            video_w = int(available_h * target_ar)
            if video_w > max_video_w:
                video_w = max_video_w
            
            video_rect = pygame.Rect(pad, y_content, video_w, available_h)
            panel_x = video_rect.right + pad
            panel_w_actual = self.win_w - panel_x - pad
            panel_rect = pygame.Rect(panel_x, y_content, panel_w_actual, available_h)
        else:
            panel_rect = None
            max_video_w = self.win_w - 2 * pad
            video_w = int(available_h * target_ar)
            if video_w < max_video_w:
                x_video = pad + (max_video_w - video_w) // 2
            else:
                x_video = pad
                video_w = max_video_w
            video_rect = pygame.Rect(x_video, y_content, video_w, available_h)

        title_rect = pygame.Rect(pad, y_title, self.win_w - 2*pad, title_h)
        nav_rect = pygame.Rect(video_rect.x, y_nav, video_rect.w, nav_h)
        
        return video_rect, title_rect, nav_rect, panel_rect

    # ---------------- UI Drawing ----------------

    def _draw_title_area(self, rect: pygame.Rect) -> None:
        if self.mode == "LIVE":
            text = "Live Workflow"
        else:
            step_map = self._step_map()
            info = step_map.get(self.step)
            text = info.title if info else f"Schritt {self.step}"
        self.renderer.draw_text(self.screen, self.font_title, text, (rect.x, rect.centery - self.font_title.get_height()//2), self.theme.TEXT)

    def _draw_step_indicator_global(self) -> None:
        buttons_w = self.home_btn_w + self.lang_btn_w + 3 * self.pad
        ind_w = int(self.win_w * 0.25)
        ind_h = int(26 * self._scale())
        gap = int(50 * self._scale())
        x = self.win_w - buttons_w - ind_w - gap
        title_h = max(60, int(80 * self._scale()))
        y = self.pad + (title_h - ind_h) // 2
        
        rect = pygame.Rect(x, y, ind_w, ind_h)
        self.renderer.draw_step_indicator(self.screen, rect, step=self.step, total_steps=self._total_steps(), font_small=self.font_small)

    def _draw_navigation_area(self, rect: pygame.Rect) -> None:
        self.nav_prev_rect = pygame.Rect(0,0,0,0)
        self.nav_next_rect = pygame.Rect(0,0,0,0)
        self.nav_action_rect = pygame.Rect(0,0,0,0)
        self.nav_audio_rect = pygame.Rect(0,0,0,0)
        
        if self.mode == "LIVE":
            btn_w = min(rect.w, int(600 * self._scale()))
            btn_h = rect.h
            btn_x = rect.centerx - btn_w // 2
            self.nav_action_rect = pygame.Rect(btn_x, rect.y, btn_w, btn_h)
            lbl = "Analyse starten" if self.lang == "DE" else "Start Analysis"
            self.renderer.draw_button(self.screen, self.nav_action_rect, lbl, self.font_ui, primary=True)
            
        else:
            # Audio Check
            audio_path = self._get_audio_filename()
            has_audio = (audio_path is not None)
            
            gap = int(20 * self._scale())
            
            if has_audio:
                btn_w = (rect.w - 2 * gap) // 3
                btn_h = rect.h
                
                self.nav_prev_rect = pygame.Rect(rect.x, rect.y, btn_w, btn_h)
                self.nav_audio_rect = pygame.Rect(rect.x + btn_w + gap, rect.y, btn_w, btn_h)
                self.nav_next_rect = pygame.Rect(rect.x + 2*btn_w + 2*gap, rect.y, btn_w, btn_h)
                
                is_playing = pygame.mixer.music.get_busy() and not self.audio_is_paused
                audio_lbl = "Audio ||" if is_playing else "Audio ▶"
                
                self.renderer.draw_button(self.screen, self.nav_audio_rect, audio_lbl, self.font_ui, primary=True)
                
            else:
                btn_w = (rect.w - gap) // 2
                btn_h = rect.h
                self.nav_prev_rect = pygame.Rect(rect.x, rect.y, btn_w, btn_h)
                self.nav_next_rect = pygame.Rect(rect.x + btn_w + gap, rect.y, btn_w, btn_h)
            
            lbl_prev = "Zurück" if self.lang == "DE" else "Back"
            is_last = self.step >= self._total_steps()
            lbl_next = ("Beenden" if self.lang == "DE" else "Finish") if is_last else ("Weiter" if self.lang == "DE" else "Next")
            
            self.renderer.draw_button(self.screen, self.nav_prev_rect, lbl_prev, self.font_ui, primary=False)
            self.renderer.draw_button(self.screen, self.nav_next_rect, lbl_next, self.font_ui, primary=True)

    def _draw_right_panel_content(self, panel_rect: pygame.Rect) -> None:
        self.renderer.draw_card(self.screen, panel_rect, fill=self.theme.PANEL_2, outline=self.theme.LINE, radius=self.theme.RADIUS)
        header_h = int(60 * self._scale())
        self.renderer.draw_text(self.screen, self.font_header, "Ergebnisse", (panel_rect.x + 20, panel_rect.y + 20), self.theme.TEXT)
        
        # 1. Definiere den Bereich für das Diagramm
        chart_top_y = panel_rect.y + header_h
        # Wir reservieren ca. 35% der Panel-Höhe für das Diagramm (oder fix 160px skalierbar)
        chart_height = int(160 * self._scale())
        
        content_rect = pygame.Rect(
            panel_rect.x + 14, 
            chart_top_y, 
            panel_rect.w - 28, 
            chart_height
        )
        
        # Zeichne Diagramm
        chart_font = self._load_font(self._fsize(26))
        self.renderer.draw_bar_chart(self.screen, content_rect, self.snapshot.top3, self.args.threshold, chart_font, self.font_ui)

        # Draw QR Code & Bias Info only in Student Step 7
        if self.level == "STUDENT" and self.step == 7:
            # Layout Cursor: Wo sind wir jetzt? (Unterhalb des Diagramms)
            cursor_y = content_rect.bottom + int(30 * self._scale())
            
            # 1. Info Text (Bias/Fehler)
            bias_text = "Hinweis: KI ist nicht objektiv (Bias). Fehler sind möglich!" if self.lang == "DE" else "Note: AI is not objective (Bias). Errors are possible!"
            txt_surf = self.font_small.render(bias_text, True, self.theme.WARN)
            txt_rect = txt_surf.get_rect(centerx=panel_rect.centerx, top=cursor_y)
            self.screen.blit(txt_surf, txt_rect)
            
            # Update Cursor (Text-Höhe + Padding)
            cursor_y = txt_rect.bottom + int(20 * self._scale())

            # 2. QR Code (Nur wenn Platz ist)
            if self._qr_code_img:
                available_h = panel_rect.bottom - cursor_y - 20
                
                if available_h > 80:
                    # Maximal verfügbare Breite/Höhe nutzen, aber nicht riesig werden
                    size = min(content_rect.w - 40, available_h)
                    size = min(size, int(300 * self._scale())) # Cap size
                    
                    # Label above QR
                    lbl = self.font_small.render("Source Code (GitHub)", True, self.theme.TEXT_MUTED)
                    lbl_rect = lbl.get_rect(centerx=panel_rect.centerx, top=cursor_y)
                    self.screen.blit(lbl, lbl_rect)
                    
                    cursor_y = lbl_rect.bottom + 5
                    
                    # Draw QR Code
                    scaled_qr = pygame.transform.smoothscale(self._qr_code_img, (int(size), int(size)))
                    qr_rect = scaled_qr.get_rect(centerx=panel_rect.centerx, top=cursor_y)
                    
                    self.screen.blit(scaled_qr, qr_rect)

    def _draw_home_button(self) -> None:
        pad = self.pad
        w, h = self.home_btn_w, self.home_btn_h
        self.home_button_rect = pygame.Rect(self.win_w - w - pad, pad, w, h)
        self.renderer.draw_button(self.screen, self.home_button_rect, self._t("home"), self.font_ui, primary=False)

    def _draw_lang_button(self) -> None:
        w, h = self.lang_btn_w, self.lang_btn_h
        pad = self.pad
        x = self.win_w - self.home_btn_w - 2 * pad - w
        self.lang_button_rect = pygame.Rect(x, pad, w, h)
        self.renderer.draw_card(self.screen, self.lang_button_rect, fill=self.theme.PANEL_2, outline=self.theme.LINE, radius=max(10, int(12 * self._scale())))
        pygame.draw.rect(self.screen, self.theme.ACCENT, self.lang_button_rect, width=max(1, int(2 * self._scale())), border_radius=max(10, int(12 * self._scale())))
        txt = self.font_ui.render(self._t("lang_label"), True, self.theme.TEXT)
        self.screen.blit(txt, txt.get_rect(center=self.lang_button_rect.center))

    def _toggle_lang(self) -> None:
        self.lang = "EN" if self.lang == "DE" else "DE"
        self._invalidate_caches()

    # ---------------- Live Intro / Landing / Gate ----------------
    def _liveintro_button_layout(self) -> None:
        btn_w = int(self.win_w * 0.60)
        btn_w = max(int(520 * self._scale()), min(btn_w, int(1400 * self._scale())))
        btn_h = max(int(90 * self._scale()), int(self.win_h * 0.11))
        btn_x = (self.win_w - btn_w) // 2
        btn_y = int(self.win_h * 0.72)
        self.cta_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    def _draw_liveintro(self) -> None:
        self._recompute_responsive()
        self.screen.fill(self.theme.BG)
        if self.snapshot is not None and self.snapshot.frame_rgb is not None:
            surf = surfarray.make_surface(self.snapshot.frame_rgb.swapaxes(0, 1))
            self.screen.blit(pygame.transform.smoothscale(surf, (self.win_w, self.win_h)), (0, 0))
            if self.snapshot.dets:
                for d in self.snapshot.dets:
                    r = self.renderer.rect_in_video_coords(d.box, self.snapshot.src_size, pygame.Rect(0, 0, self.win_w, self.win_h))
                    pygame.draw.rect(self.screen, self.renderer.conf_color(d.conf), r, width=2)
        self._liveintro_button_layout()
        self.renderer.draw_button(self.screen, self.cta_button_rect, self._t("liveintro_cta"), self.font_landing_btn, primary=True)
        pygame.display.flip()
        self.clock.tick(30)

    def _landing_layout(self) -> None:
        bw = int(self.win_w * 0.30)
        bh = int(self.win_h * 0.18)
        bw = max(int(300 * self._scale()), min(bw, int(720 * self._scale())))
        bh = max(int(120 * self._scale()), min(bh, int(240 * self._scale())))
        y = int(self.win_h * 0.62)
        gap = max(int(self.win_w * 0.06), int(100 * self._scale()))
        left_x = (self.win_w // 2) - (gap // 2) - bw
        right_x = (self.win_w // 2) + (gap // 2)
        self.level_left_rect = pygame.Rect(left_x, y, bw, bh)
        self.level_right_rect = pygame.Rect(right_x, y, bw, bh)

    def _draw_level_button(self, rect: pygame.Rect, label: str) -> None:
        self.renderer.draw_button(self.screen, rect, label, self.font_landing_btn, primary=True, border_width=self.level_border_w)

    def _draw_landing(self) -> None:
        self._recompute_responsive()
        bg = self._get_landing_bg_scaled()
        if bg is not None: self.screen.blit(bg, (0, 0))
        else: self.screen.fill((7, 14, 26))
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        self.screen.blit(overlay, (0, 0))
        self._landing_layout()
        col = self.theme.BTN_PRIMARY_BORDER
        title_surf = self.font_landing_title.render(self._t("landing_title"), True, col)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.win_w // 2, int(self.win_h * 0.22))))
        sub_surf = self.font_landing_sub.render(self._t("landing_sub"), True, col)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.win_w // 2, int(self.win_h * 0.36))))
        self._draw_level_button(self.level_left_rect, self._t("level_left"))
        self._draw_level_button(self.level_right_rect, self._t("level_right"))
        hint_surf = self.font_ui.render(self._t("hint"), True, col)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(self.win_w // 2, int(self.win_h * 0.92))))
        self._draw_home_button()
        self._draw_lang_button()
        pygame.display.flip()
        self.clock.tick(30)

    def _start_detection(self, level: str) -> None:
        self.level = level
        self._ensure_camera()
        if self.transformer is None: self.transformer = StepTransformer()
        self.mode = "LIVE"
        self.step = 0
        self.gate_next_step = None
        self._invalidate_caches()
        self.state = "RUNNING"

    def _gate_layout(self) -> None:
        btn_w_total = int(self.win_w * 0.35)
        btn_w_total = max(int(320 * self._scale()), min(btn_w_total, int(800 * self._scale())))
        btn_h = max(int(90 * self._scale()), int(self.win_h * 0.11))
        
        y = int(self.win_h * 0.80)
        gap = int(20 * self._scale())
        
        # Two buttons side by side
        single_btn_w = (btn_w_total - gap) // 2
        
        start_x = (self.win_w - btn_w_total) // 2
        
        self.gate_prev_rect = pygame.Rect(start_x, y, single_btn_w, btn_h)
        self.gate_next_rect = pygame.Rect(start_x + single_btn_w + gap, y, single_btn_w, btn_h)

    def _enter_gate_for_step(self, target_step: int) -> None:
        self.gate_next_step = target_step
        self.state = "GATE"
        self._invalidate_caches()

    def _accept_gate(self) -> None:
        if self.gate_next_step is None: self.state = "RUNNING"; return
        self.mode = "ANALYSE"
        self.step = self.gate_next_step
        self.gate_next_step = None
        self.state = "RUNNING"
        self._invalidate_caches()

    def _gate_back(self) -> None:
        # Wenn wir bei Step 1 sind, geht es zurück zu LIVE
        if self.gate_next_step == 1:
            self.mode = "LIVE"
            self.step = 0
            self.state = "RUNNING"
            self.gate_next_step = None
            self._invalidate_caches()
        else:
            # Ansonsten zurück zum vorherigen Analyse-Schritt (ohne Gate)
            target = (self.gate_next_step or 2) - 1
            self.mode = "ANALYSE"
            self.step = target
            self.state = "RUNNING"
            self.gate_next_step = None
            self._invalidate_caches()

    def _load_gate_animation_frames(self, step_n: int) -> None:
        sequences = {
            1: dict(folder="schritt_1_experte", prefix="schritt1experte", start=1, end=62),
            2: dict(folder="schritt_2_experte", prefix="schritt2experte", start=1, end=101),
            3: dict(folder="schritt_3_experte", prefix="schritt3experte", start=1, end=48),
            4: dict(folder="schritt_4_experte", prefix="schritt4experte", start=1, end=78),
            5: dict(folder="schritt_5_experte", prefix="schritt5experte", start=1, end=29),
            6: dict(folder="schritt_6_experte", prefix="schritt6experte", start=1, end=68),
            7: dict(folder="schritt_7_experte", prefix="schritt7experte", start=1, end=80),
        }
        seq = sequences.get(step_n)
        if seq is None:
            self.gate_anim_frames = None; self.gate_anim_key = None; return
        folder = os.path.join(self.base_dir, "assets", seq["folder"])
        prefix = seq["prefix"]; start = seq["start"]; end = seq["end"]
        key = f"{folder}:{prefix}:{start}:{end}"
        if self.gate_anim_key == key and self.gate_anim_frames is not None: return
        frames = []
        for i in range(start, end + 1):
            path = os.path.join(folder, f"{prefix}{i}.jpg")
            try: 
                frames.append(pygame.image.load(path).convert())
            except Exception as e:
                if i == start: 
                    print(f"DEBUG: Konnte {path} nicht laden. Grund: {e}")
                    
        self.gate_anim_frames = frames if frames else None
        self.gate_anim_key = key
        self.gate_anim_idx = 0
        self.gate_anim_last_ms = pygame.time.get_ticks()

    def _draw_gate(self) -> None:
        self._recompute_responsive()
        bg = self._get_landing_bg_scaled()
        if bg is not None: self.screen.blit(bg, (0, 0))
        else: self.screen.fill((0, 0, 0))
        overlay = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 85))
        self.screen.blit(overlay, (0, 0))
        self._gate_layout()

        assert self.snapshot is not None
        gate_map = self._gate_map()
        step_n = self.gate_next_step or 1
        info = gate_map.get(step_n)
        if info is None: info = StepInfo(title=f"Zwischenschritt {step_n}", body="")

        outer = pygame.Rect(int(self.win_w * 0.06), int(self.win_h * 0.10), int(self.win_w * 0.88), int(self.win_h * 0.62))
        gap = max(12, int(18 * self._scale()))
        text_w = int(outer.w * (2 / 3)) - gap // 2
        anim_w = outer.w - text_w - gap
        text_rect = pygame.Rect(outer.x, outer.y, text_w, outer.h)
        anim_rect = pygame.Rect(text_rect.right + gap, outer.y, anim_w, outer.h)
        target_w, target_h = 720, 405
        anim_frame_rect = pygame.Rect(0, 0, target_w, target_h)
        anim_frame_rect.center = anim_rect.center
        if anim_frame_rect.w > anim_rect.w or anim_frame_rect.h > anim_rect.h:
            scale = min(anim_rect.w / target_w, anim_rect.h / target_h)
            anim_frame_rect.size = (max(1, int(target_w * scale)), max(1, int(target_h * scale)))
            anim_frame_rect.center = anim_rect.center

        if self.gate_cached_step != step_n:
            title, body = self.text_layout.split_title_body(info.title, info.body)
            self.gate_cached_title_font, self.gate_cached_body_font = self.text_layout.fit_title_and_body(
                title, body, text_rect, min_body=self._fsize(18), max_body=self._fsize(34),
                title_ratio=1.25, line_spacing=max(2, int(4 * self._scale())),
            )
            self.gate_cached_title_lines = self.text_layout.wrap_lines(title, self.gate_cached_title_font, text_rect.w)
            self.gate_cached_body_lines = self.text_layout.wrap_lines(body, self.gate_cached_body_font, text_rect.w) if body else []
            self.gate_cached_step = step_n

        y = text_rect.y
        y = self.text_layout.draw_wrapped_lines(self.screen, self.gate_cached_title_lines, self.gate_cached_title_font, (235, 235, 235), text_rect.x, y, line_spacing=max(2, int(6 * self._scale())))
        if self.gate_cached_body_lines:
            y += self.gate_cached_body_font.get_linesize()
            self.text_layout.draw_wrapped_lines(self.screen, self.gate_cached_body_lines, self.gate_cached_body_font, (200, 200, 200), text_rect.x, y, line_spacing=max(2, int(6 * self._scale())))

        self._load_gate_animation_frames(step_n)
        self.renderer.draw_card(self.screen, anim_frame_rect, fill=(10, 10, 10), outline=(60, 60, 60), radius=max(12, int(16 * self._scale())))
        if self.gate_anim_frames:
            now = pygame.time.get_ticks()
            if now - self.gate_anim_last_ms >= self.gate_anim_frame_ms:
                self.gate_anim_idx = (self.gate_anim_idx + 1) % len(self.gate_anim_frames)
                self.gate_anim_last_ms = now
            frame = self.gate_anim_frames[self.gate_anim_idx]
            new_size = (max(1, int(frame.get_width() * min(anim_frame_rect.w / frame.get_width(), anim_frame_rect.h / frame.get_height()))),
                        max(1, int(frame.get_height() * min(anim_frame_rect.w / frame.get_width(), anim_frame_rect.h / frame.get_height()))))
            frame_s = pygame.transform.smoothscale(frame, new_size)
            self.screen.blit(frame_s, frame_s.get_rect(center=anim_frame_rect.center).topleft)

        # Draw Buttons
        self.renderer.draw_button(self.screen, self.gate_prev_rect, self._t("back"), self.font_landing_btn, primary=False)
        self.renderer.draw_button(self.screen, self.gate_next_rect, self._t("gate_btn"), self.font_landing_btn, primary=True)
        
        self._draw_home_button()
        self._draw_lang_button()
        pygame.display.flip()
        self.clock.tick(30)

    # ---------------- Events ----------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE): self.running = False
                if self.state == "GATE":
                    if event.key == pygame.K_RETURN: self._accept_gate(); return
                    if event.key == pygame.K_BACKSPACE: self._gate_back(); return
                if self.state == "RUNNING":
                    if event.key == pygame.K_SPACE:
                        if self.mode == "LIVE":
                            if self._is_student(): self._enter_gate_for_step(1)
                            else: self.mode, self.step = "ANALYSE", 1; self._invalidate_caches()
                        else: self.mode, self.step = "LIVE", 0; self._invalidate_caches()
                    elif self.mode == "ANALYSE":
                        if event.key == pygame.K_RETURN:
                            nxt = min(self._total_steps(), self.step + 1)
                            if nxt != self.step:
                                if self._is_student(): self._enter_gate_for_step(nxt)
                                else: self.step = nxt; self._invalidate_caches()
                        elif event.key == pygame.K_BACKSPACE:
                            if self._is_student():
                                # CHANGE: Im Student-Mode geht BACKSPACE jetzt zum Gate des AKTUELLEN Steps zurück
                                self._enter_gate_for_step(self.step)
                            else:
                                prv = max(1, self.step - 1)
                                if prv != self.step:
                                    self.step = prv; self._invalidate_caches()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "LIVEINTRO":
                    if self.cta_button_rect.collidepoint(event.pos): self.state = "LANDING"; return
                if self.state in ("LANDING", "RUNNING", "GATE"):
                    if self.home_button_rect.collidepoint(event.pos): self._go_home(); return
                    if self.lang_button_rect.collidepoint(event.pos): self._toggle_lang(); return
                if self.state == "LANDING":
                    if self.level_left_rect.collidepoint(event.pos): self._start_detection("SCHUELER"); return
                    if self.level_right_rect.collidepoint(event.pos): self._start_detection("STUDENT"); return
                if self.state == "GATE":
                    if self.gate_next_rect.collidepoint(event.pos): self._accept_gate(); return
                    if self.gate_prev_rect.collidepoint(event.pos): self._gate_back(); return
                if self.state == "RUNNING":
                    # Audio Button Check
                    if self.nav_audio_rect.collidepoint(event.pos):
                        self._toggle_audio()
                        return
                    
                    if self.mode == "LIVE":
                        if self.nav_action_rect.collidepoint(event.pos):
                            if self._is_student(): self._enter_gate_for_step(1)
                            else: self.mode, self.step = "ANALYSE", 1; self._invalidate_caches()
                    elif self.mode == "ANALYSE":
                        if self.nav_next_rect.collidepoint(event.pos):
                            if self.step == self._total_steps():
                                self.mode, self.step = "LIVE", 0; self._invalidate_caches()
                            else:
                                nxt = min(self._total_steps(), self.step + 1)
                                if nxt != self.step:
                                    if self._is_student(): self._enter_gate_for_step(nxt)
                                    else: self.step = nxt; self._invalidate_caches()
                        if self.nav_prev_rect.collidepoint(event.pos):
                            if self._is_student():
                                # CHANGE: Im Student-Mode geht der ZURÜCK-Button jetzt zum Gate des AKTUELLEN Steps zurück
                                self._enter_gate_for_step(self.step)
                            else:
                                prv = max(1, self.step - 1)
                                if prv != self.step:
                                    self.step = prv; self._invalidate_caches()

    def update(self) -> None:
        if self.state == "LIVEINTRO":
            self._ensure_camera()
            self.snapshot = self.detector.capture_snapshot()
        elif self.state == "RUNNING" and self.mode == "LIVE":
            self.snapshot = self.detector.capture_snapshot()

    # ---------------- Left overlays helpers ----------------
    def _draw_hud_lines(self, video_rect: pygame.Rect, lines: List[str]) -> None:
        x, y = video_rect.x + self.pad, video_rect.y + self.pad
        for line in lines:
            self.renderer.draw_pill(self.screen, self.font_small, line, (x, y), fg=self.theme.TEXT)
            y += self.font_small.get_linesize() + 6

    def _draw_roi_overlay(self, video_rect: pygame.Rect) -> None:
        if not self.snapshot or not self.snapshot.debug.get("roi"): return
        r = self.renderer.rect_in_video_coords(self.snapshot.debug["roi"], self.snapshot.src_size, video_rect)
        pygame.draw.rect(self.screen, (80, 160, 255), r, width=2)

    def _draw_det_list(self, video_rect: pygame.Rect, dets, color=None, draw_label=False) -> None:
        if not self.snapshot: return
        for d in dets:
            r = self.renderer.rect_in_video_coords(d.box, self.snapshot.src_size, video_rect)
            col = color if color else self.renderer.conf_color(d.conf)
            pygame.draw.rect(self.screen, col, r, width=2)
            if draw_label:
                label = f"{d.label} {d.conf*100:.0f}%"
                txt = self.font_ui.render(label, True, self.theme.TEXT)
                pill = pygame.Surface((txt.get_width()+16, txt.get_height()+10), pygame.SRCALPHA)
                pill.fill((15, 16, 20, 180))
                self.screen.blit(pill, (r.x, max(video_rect.y+6, r.y-txt.get_height()-16)))
                self.screen.blit(txt, (r.x+8, max(video_rect.y+10, r.y-txt.get_height()-12)))

    def _draw_pixel_inspector(self, video_rect: pygame.Rect) -> None:
        if self.step != 1: return

        mx, my = pygame.mouse.get_pos()
        if not video_rect.collidepoint(mx, my): return

        # Hole die Farbe direkt vom Bildschirm (genau das Pixel unter der Maus)
        try:
            col = self.screen.get_at((mx, my))
        except Exception:
            return

        r, g, b, _ = col

        # Tooltip Text
        text = f"R:{r} G:{g} B:{b}"
        font = self.font_ui
        txt_surf = font.render(text, True, (255, 255, 255)) # Weißer Text
        
        # Positionierung (etwas versetzt, damit die Maus nicht verdeckt wird)
        tip_x = mx + 20
        tip_y = my + 20
        
        # Am Bildschirmrand? Nach links/oben schieben
        if tip_x + txt_surf.get_width() > self.win_w:
            tip_x = mx - txt_surf.get_width() - 15
        if tip_y + txt_surf.get_height() > self.win_h:
            tip_y = my - txt_surf.get_height() - 15
        
        bg_rect = pygame.Rect(tip_x - 6, tip_y - 6, txt_surf.get_width() + 12, txt_surf.get_height() + 12)
        
        # Zeichnen
        pygame.draw.rect(self.screen, (20, 20, 20), bg_rect, border_radius=6) # Dunkler Hintergrund
        pygame.draw.rect(self.screen, (r, g, b), bg_rect, width=2, border_radius=6) # Rahmen in Pixelfarbe
        self.screen.blit(txt_surf, (tip_x, tip_y))

    # ---------------- Draw Main ----------------
    def draw(self) -> None:
        if self.state == "LIVEINTRO": self._draw_liveintro(); return
        if self.state == "LANDING": self._draw_landing(); return
        if self.state == "GATE": self._draw_gate(); return

        self._recompute_responsive()
        assert self.snapshot is not None
        
        video_rect, title_rect, nav_rect, panel_rect = self.make_layout()

        self.screen.fill(self.theme.BG)
        
        # 1. Video
        self.renderer.draw_card(self.screen, video_rect, fill=(12, 13, 16), outline=self.theme.LINE, radius=self.theme.RADIUS)
        self._draw_left_view(video_rect)
        self._draw_pixel_inspector(video_rect)
        
        # 2. Title
        self._draw_title_area(title_rect)
        
        # 3. Nav Buttons
        self._draw_navigation_area(nav_rect)
        
        # 4. Optional Panel (Scores)
        if panel_rect:
            self._draw_right_panel_content(panel_rect)
        
        # 5. Global Elements
        self._draw_step_indicator_global()
        self._draw_home_button()
        self._draw_lang_button()

        pygame.display.flip()
        self.clock.tick(30)

    def _draw_left_view(self, video_rect: pygame.Rect) -> None:
        if self.snapshot.frame_rgb is None: return
        if self.mode == "LIVE":
            surf = surfarray.make_surface(self.snapshot.frame_rgb.swapaxes(0, 1))
            self.screen.blit(pygame.transform.smoothscale(surf, (video_rect.w, video_rect.h)), video_rect.topleft)
            for d in self.snapshot.dets:
                r = self.renderer.rect_in_video_coords(d.box, self.snapshot.src_size, video_rect)
                pygame.draw.rect(self.screen, self.renderer.conf_color(d.conf), r, width=2)
            self._draw_hud_lines(video_rect, [f"Stream: {self.snapshot.debug.get('src_size', (0,0))}"])
        else:
            if self.sim_step_cached != self.step:
                sim_rgb = self.transformer.apply(self.snapshot.frame_rgb, self.step, self.level)
                self.sim_surface = surfarray.make_surface(sim_rgb.swapaxes(0, 1))
                self.sim_step_cached = self.step
            if self.sim_surface:
                self.screen.blit(pygame.transform.smoothscale(self.sim_surface, (video_rect.w, video_rect.h)), video_rect.topleft)
        
        dbg = self.snapshot.debug
        if self.level == "SCHUELER":
            if self.step == 1:
                self.renderer.draw_pixel_grid(self.screen, video_rect, spacing=max(18, int(26*self._scale())))
                self.renderer.draw_pill(self.screen, self.font_ui, "RGB Pixel", (video_rect.x+self.pad, video_rect.y+self.pad), fg=self.theme.TEXT)
            if self.step == 3:
                self._draw_det_list(video_rect, self.snapshot.raw_dets, color=(120, 120, 120))
                self._draw_det_list(video_rect, self.snapshot.dets[:10])
            if self.step == 4 and self.snapshot.top_dets: self._draw_det_list(video_rect, self.snapshot.top_dets, draw_label=True)
        else:
            if self.step == 1: self._draw_hud_lines(video_rect, ["Step1 Capture"])
            elif self.step == 2:
                self._draw_roi_overlay(video_rect)
                self._draw_hud_lines(video_rect, ["Step2 ROI/Aspect", f"ROI: {dbg.get('roi')}"])
            elif self.step == 3: self._draw_hud_lines(video_rect, ["Step3 Inference (IMX500)"])
            elif self.step == 4:
                lines = ["Step4 Read tensors"]
                if dbg.get("output_shapes"): lines.extend([f"out{i}: {s}" for i, s in enumerate(dbg["output_shapes"][:2])])
                self._draw_hud_lines(video_rect, lines)
            elif self.step == 5:
                self._draw_det_list(video_rect, self.snapshot.raw_dets, color=(255, 220, 80))
                self._draw_hud_lines(video_rect, ["Step5 Parse candidates"])
            elif self.step == 6:
                self._draw_det_list(video_rect, self.snapshot.raw_dets, color=(120, 120, 120))
                self._draw_det_list(video_rect, self.snapshot.dets[:10])
                self._draw_hud_lines(video_rect, ["Step6 Filter/Rank"])
            elif self.step == 7:
                self._draw_det_list(video_rect, self.snapshot.top_dets, draw_label=True)
                self._draw_hud_lines(video_rect, ["Step7 Render"])

    # ---------------- Main Loop ----------------
    def run(self) -> None:
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
        finally:
            pygame.quit()
            if self.detector: self.detector.stop()


def get_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--threshold", type=float, default=0.55)
    p.add_argument("--iou", type=float, default=0.65)
    p.add_argument("--max-detections", type=int, default=10)
    p.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--bbox-order", choices=["yx", "xy"], default="yx")
    p.add_argument("--postprocess", choices=["", "nanodet"], default=None)
    p.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--labels", type=str, default=None)
    p.add_argument("--cam-width", type=int, default=1280)
    p.add_argument("--cam-height", type=int, default=720)
    return p.parse_args()


def main() -> None:
    args = get_args()
    App(args).run()


if __name__ == "__main__":
    main()
