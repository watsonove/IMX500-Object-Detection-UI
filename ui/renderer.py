# imx500_gui/ui/renderer.py

from typing import Tuple, List, Optional
import pygame
import pygame.surfarray as surfarray

from .theme import Theme


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


class Renderer:
    """Zeichnet alle Panels, Texte, Balken und Video-Overlays."""

    def __init__(self, theme: Theme):
        self.t = theme

    def conf_color(self, conf: float) -> Tuple[int, int, int]:
        return self.t.GOOD if conf >= 0.60 else self.t.WARN

    def draw_card(self, surface, rect, fill=None, outline=None, radius=None):
        fill = self.t.PANEL if fill is None else fill
        outline = self.t.LINE if outline is None else outline
        radius = self.t.RADIUS if radius is None else radius
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
        pygame.draw.rect(surface, outline, rect, width=1, border_radius=radius)

    def draw_text(self, surface, font, text, pos, color=None):
        color = self.t.TEXT if color is None else color
        surface.blit(font.render(text, True, color), pos)

    def draw_button(self, surface, rect, label, font, primary=False, border_width=1):
        """Einheitliche Button-Darstellung."""
        if primary:
            fill = self.t.BTN_PRIMARY_FILL
            outline = self.t.BTN_PRIMARY_BORDER
            text_col = self.t.BTN_PRIMARY_BORDER
        else:
            fill = self.t.PANEL_2
            outline = self.t.LINE
            text_col = self.t.TEXT

        pygame.draw.rect(surface, fill, rect, border_radius=self.t.RADIUS)
        pygame.draw.rect(surface, outline, rect, width=border_width, border_radius=self.t.RADIUS)

        txt_surf = font.render(label, True, text_col)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)

    def draw_pill(self, surface, font, text, pos, bg=(20, 20, 20, 180), fg=None):
        fg = self.t.TEXT if fg is None else fg
        txt = font.render(text, True, fg)
        w, h = txt.get_size()
        pill_rect = pygame.Rect(pos[0], pos[1], w + 16, h + 8)
        
        # Draw translucent background
        s = pygame.Surface((pill_rect.w, pill_rect.h), pygame.SRCALPHA)
        s.fill(bg)
        surface.blit(s, pill_rect.topleft)
        
        surface.blit(txt, (pos[0] + 8, pos[1] + 4))

    def rect_in_video_coords(self, box, src_size, video_rect) -> pygame.Rect:
        """
        Transformiert eine Box (x,y,w,h) von src_size (Kamera-Auflösung)
        in die Koordinaten des Video-Panels auf dem Screen.
        """
        sx, sy, sw, sh = box
        src_w, src_h = src_size
        
        scale_x = video_rect.w / src_w
        scale_y = video_rect.h / src_h
        
        rx = video_rect.x + int(sx * scale_x)
        ry = video_rect.y + int(sy * scale_y)
        rw = int(sw * scale_x)
        rh = int(sh * scale_y)
        return pygame.Rect(rx, ry, rw, rh)

    def draw_step_indicator(self, surface, rect, step, total_steps, font_small):
        # Background rail
        pygame.draw.rect(surface, self.t.PANEL_2, rect, border_radius=rect.height // 2)
        
        if total_steps < 1:
            return

        # Width of one segment
        seg_w = rect.w / total_steps
        
        # Fill active steps
        if step > 0:
            fill_w = step * seg_w
            fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.h)
            pygame.draw.rect(surface, self.t.ACCENT, fill_rect, border_radius=rect.height // 2)
        
        # Draw segment separators
        for i in range(1, total_steps):
            x = rect.x + i * seg_w
            pygame.draw.line(surface, self.t.BG, (x, rect.y), (x, rect.bottom), 2)
            
        # Draw Text Indicator above
        # Hier wurde das Padding erhöht (rect.y - 12 statt -4)
        label = f"{step} / {total_steps}"
        txt = font_small.render(label, True, self.t.TEXT_MUTED)
        txt_rect = txt.get_rect(centerx=rect.centerx, bottom=rect.y - 12)
        surface.blit(txt, txt_rect)

    def draw_pixel_grid(self, surface, rect, spacing=20):
        """Simuliert Pixel-Raster."""
        col = (255, 255, 255, 30)  # sehr transparent
        
        # Vertikale Linien
        for x in range(rect.x, rect.right, spacing):
            pygame.draw.line(surface, col, (x, rect.y), (x, rect.bottom))
            
        # Horizontale Linien
        for y in range(rect.y, rect.bottom, spacing):
            pygame.draw.line(surface, col, (rect.x, y), (rect.right, y))

    def draw_bar_chart(self, surface, rect, top3: List[Tuple[str, float]], threshold: float, title_font, body_font):
        """Zeichnet Balkendiagramm für Top-3 Predictions."""
        
        pad_top = title_font.get_linesize() + 10
        pad_left = 14
        pad_right = 14

        row_h = 28
        gap = 12

        chart_x = rect.x + pad_left
        chart_y = rect.y + pad_top
        chart_w = rect.w - pad_left - pad_right
        chart_h = 3 * row_h + 2 * gap

        # Threshold Line
        thr_x = chart_x + int(chart_w * clamp01(threshold))
        pygame.draw.line(surface, self.t.ACCENT, (thr_x, chart_y - 8), (thr_x, chart_y + chart_h + 8), 2)

        if not top3:
            # self.draw_text(surface, body_font, "...", (chart_x, chart_y), self.t.TEXT_MUTED)
            return

        for i, (lab, conf) in enumerate(top3[:3]):
            y = chart_y + i * (row_h + gap)
            
            # Hintergrund
            pygame.draw.rect(surface, (28, 31, 37), pygame.Rect(chart_x, y, chart_w, row_h), border_radius=10)
            
            # Balken
            bar_col = self.conf_color(conf)
            bw = int(chart_w * clamp01(conf))
            pygame.draw.rect(surface, bar_col, pygame.Rect(chart_x, y, bw, row_h), border_radius=10)
            
            # Label Text
            lbl_surf = body_font.render(f"{lab} {int(conf*100)}%", True, self.t.TEXT)
            surface.blit(lbl_surf, (chart_x + 8, y + (row_h - lbl_surf.get_height()) // 2))
