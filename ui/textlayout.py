# imx500_gui/ui/textlayout.py
from typing import List, Tuple
import pygame


class TextLayout:
    """Word-Wrap + Font-Fitting fuer Step-Beschreibungen."""

    @staticmethod
    def wrap_lines(text: str, font: pygame.font.Font, max_w: int) -> List[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = text.split("\n")
        lines: List[str] = []

        for p in paragraphs:
            if p.strip() == "":
                lines.append("")
                continue

            words = p.split(" ")
            cur = ""
            for w in words:
                test = (cur + " " + w).strip()
                if font.size(test)[0] <= max_w:  # [web:177]
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
        return lines

    @staticmethod
    def draw_wrapped_lines(surface, lines, font, color, x, y, line_spacing=4) -> int:
        line_h = font.get_linesize() + line_spacing  # [web:177]
        for ln in lines:
            if ln == "":
                y += line_h
                continue
            surface.blit(font.render(ln, True, color), (x, y))  # [web:177]
            y += line_h
        return y

    @staticmethod
    def split_title_body(title: str, body: str) -> Tuple[str, str]:
        # In der neuen Struktur bekommst du Titel und Body getrennt aus STEP_TEXT.
        return title.strip(), body.strip()

    @staticmethod
    def fit_title_and_body(title: str, body: str, rect: pygame.Rect,
                           min_body=18, max_body=40, title_ratio=1.30, line_spacing=4):
        title = title.strip()
        body = body.strip()

        best_body = pygame.font.Font(None, min_body)
        best_title = pygame.font.Font(None, int(min_body * title_ratio))

        lo, hi = min_body, max_body
        while lo <= hi:
            body_size = (lo + hi) // 2
            title_size = max(body_size + 4, int(body_size * title_ratio))

            f_body = pygame.font.Font(None, body_size)
            f_title = pygame.font.Font(None, title_size)

            title_lines = TextLayout.wrap_lines(title, f_title, rect.w)
            body_lines = TextLayout.wrap_lines(body, f_body, rect.w) if body else []

            needed_h = 0
            needed_h += len(title_lines) * (f_title.get_linesize() + line_spacing)  # [web:177]
            if body_lines:
                needed_h += (f_body.get_linesize() + line_spacing)
                needed_h += len(body_lines) * (f_body.get_linesize() + line_spacing)

            if needed_h <= rect.h:
                best_body, best_title = f_body, f_title
                lo = body_size + 1
            else:
                hi = body_size - 1

        return best_title, best_body
