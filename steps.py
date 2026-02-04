# -*- coding: utf-8 -*-
# imx500_gui_v4/steps.py

from dataclasses import dataclass
from typing import Dict
import numpy as np


@dataclass(frozen=True)
class StepInfo:
    title: str
    body: str


# -------------------------
# SCHUELER (DE) - 4 Steps
# -------------------------
STEP_TEXT_SCHUELER_DE: Dict[int, StepInfo] = {
    1: StepInfo(
        title="1. Input & Vorverarbeitung: Das digitale Auge",
        body=(
            "Bevor die KI loslegt, muss das Bild „vorbereitet“ werden. Die Kamera liefert Millionen bunter Pixel, "
            "doch das KI-Gehirn hat einen Tunnelblick. Es schneidet unwichtige Bereiche weg und verkleinert das Bild "
            "(Aspect-Ratio), damit die Berechnungen blitzschnell in Echtzeit funktionieren. Schönheit spielt hier keine Rolle – "
            "nur Effizienz zählt!\n\n"
            "Was passiert: Zuschneiden, Verkleinern, Farbanpassung.\n"
            "Die Sicht der KI: Ein etwas verzerrtes, pixeliges Quadrat."
        ),
    ),
    2: StepInfo(
        title="2. Feature Extraction: Muster erkennen",
        body=(
            "Jetzt sucht der KI-Chip (wie der IMX500) nach markanten Merkmalen. Anstatt das ganze Bild auf einmal zu verstehen, "
            "zerlegt die KI es in Bausteine. Sie sucht nach Kanten, Rundungen oder Farbübergängen.\n\n"
            "Der Prozess: Mathematische Filter gleiten über das Bild.\n"
            "Das Ziel: Aus einfachen Linien werden komplexe Formen (z. B. „zwei Kreise über einer geraden Linie“ könnten die Räder eines Autos sein)."
        ),
    ),
    3: StepInfo(
        title="3. Localization: Wo ist das Objekt?",
        body=(
            "Sobald die KI interessante Muster gefunden hat, zeichnet sie virtuelle Rahmen, die sogenannten Bounding Boxes. "
            "Da die KI anfangs nur rät, entstehen oft hunderte überlappende Rahmen. Jeder Rahmen wird durch ein mathematisches "
            "Koordinatensystem definiert:\n\n"
            "[x, y, width, height]\n"
            "x, y: Der Startpunkt des Rahmens (meist oben links).\n"
            "width/height: Wie breit und hoch die Box ist."
        ),
    ),
    4: StepInfo(
        title="4. Classification & Confidence: Was ist es und wie sicher sind wir?",
        body=(
            "Im letzten Schritt wird aufgeräumt. Die KI vergleicht die gefundenen Muster in den Boxen mit ihrem Training "
            "und gibt dem Objekt einen Namen (Label) und eine Sicherheit (Confidence).\n\n"
            "Classification: Jedem Rahmen wird ein Label (Name) zugeordnet.\n"
            "Confidence Scoring: Die KI gibt einen Prozentwert an (z. B. 0.95 für 95%). Alles, was unter einem Schwellenwert liegt "
            "(z. B. unter 50%), wird gelöscht. Übrig bleibt nur das sauber markierte Endergebnis.\n\n"
            "Merksatz: Die KI „sieht“ keine Bilder, sie berechnet Wahrscheinlichkeiten in Rahmen!"
        ),
    ),
}


# -------------------------
# STUDIS (DE) - 7 Steps
# -------------------------
STEP_TEXT_STUDIS_DE: Dict[int, StepInfo] = {
    1: StepInfo(
        title="1. Data Acquisition & RGB-Input",
        body=(
            "Der Prozess beginnt mit der Rohdatenerfassung. Der IMX500-Sensor liefert einen Videostream im RGB-Farbraum. "
            "Was für uns wie ein semantisches Bild aussieht, ist für den Algorithmus zunächst nur eine unstrukturierte Matrix "
            "aus Pixelwerten (Intensitäten von 0 bis 255 pro Farbkanal).\n\n"
            "Didaktischer Hinweis: KI beginnt nicht mit ‚Verstehen‘, sondern mit statistischer Signalverarbeitung. "
            "Die Qualität dieses Inputs (Belichtung, Rauschen) bestimmt maßgeblich die spätere Erkennungsleistung "
            "(‚Garbage In, Garbage Out‘-Prinzip)."
        ),
    ),
    2: StepInfo(
        title="2. Input Normalization & Resizing",
        body=(
            "Neuronale Netze haben eine fixe Eingangsgröße (Input Layer), hier z. B. 300x300 Pixel. "
            "Das hochauflösende Bild muss daher herunterskaliert und normalisiert werden. Dabei entstehen zwangsläufig "
            "Informationsverluste und Verzerrungen (Aliasing). Der Algorithmus sieht also nie die Realität, sondern nur "
            "eine stark komprimierte Abstraktion davon.\n\n"
            "Dies ist ein kritischer Flaschenhals: Kleine Objekte verschwinden hier oft bereits, bevor die eigentliche Analyse beginnt."
        ),
    ),
    3: StepInfo(
        title="3. Convolutional Neural Network (CNN)",
        body=(
            "Nun erfolgt die Inferenz (Schlussfolgerung) auf dem AI-Accelerator. Ein Convolutional Neural Network (CNN) extrahiert "
            "hierarchische Merkmale. In den ersten Schichten (Layers) erkennen Filter einfache Geometrien wie Kanten und Ecken. "
            "In tieferen Schichten werden diese zu komplexen Mustern (z. B. ‚Auge‘, ‚Rad‘) kombiniert.\n\n"
            "Dies ist keine Magie, sondern reine Matrixmultiplikation: Der Input wird durch gewichtete Filtermatrizen transformiert, "
            "um relevante Features hervorzuheben."
        ),
    ),
    4: StepInfo(
        title="4. Raw Output Tensor",
        body=(
            "Das Ergebnis der Inferenz ist kein Bild, sondern ein Tensor (ein mehrdimensionales Array). Dieser Vektor enthält "
            "tausende numerische Werte, die codierte Informationen über Box-Koordinaten, Klassen-Wahrscheinlichkeiten und Objekt-Scores enthalten. "
            "Das Modell ‚weiß‘ zu diesem Zeitpunkt noch nicht, was ein Objekt ist – es liefert lediglich eine Wahrscheinlichkeitsverteilung "
            "über den gesamten Bildraum zurück."
        ),
    ),
    5: StepInfo(
        title="5. Bounding Box Regression",
        body=(
            "Der Output-Tensor wird decodiert (geparst). Das Modell generiert basierend auf gelernten ‚Anchor Boxes‘ hunderte von Hypothesen, "
            "wo sich Objekte befinden könnten. Da das Netz probabilistisch arbeitet, wird für fast jeden Bildbereich eine Vermutung geäußert – "
            "auch für den Hintergrund (Rauschen).\n\n"
            "Wir sehen hier die ‚Unsicherheit‘ der KI: Sie diskriminiert noch nicht zwischen relevantem Objekt und statistischem Rauschen."
        ),
    ),
    6: StepInfo(
        title="6. Non-Maximum Suppression (NMS)",
        body=(
            "Um aus dem Chaos valide Ergebnisse zu filtern, werden zwei Algorithmen angewandt:\n\n"
            "Confidence Thresholding: Alle Hypothesen unter einem Schwellenwert (z. B. 50%) werden verworfen.\n\n"
            "Non-Maximum Suppression (NMS): Überlappen sich mehrere Boxen für dasselbe Objekt (hohe ‚Intersection over Union‘), "
            "wird nur diejenige mit der höchsten Wahrscheinlichkeit behalten.\n\n"
            "Dies ist der Entscheidungsschritt, bei dem die KI ‚auswählt‘."
        ),
    ),
    7: StepInfo(
        title="7. Final Output & Bias Check",
        body=(
            "Die normalisierten Koordinaten werden auf die Originalauflösung zurückgerechnet (Upscaling). Kritische Reflexion: "
            "Das Label (z. B. ‚Person‘) stammt aus dem Trainingsdatensatz (z. B. COCO). Kennt das Modell ein Objekt nicht, wird es das "
            "optisch ähnlichste Label wählen (Fehlklassifikation). KI ist also nie objektiv, sondern immer abhängig von den Daten, "
            "mit denen sie trainiert wurde.\n\n"
            "Interesse an der Technik? Infos zu unseren Informatik-Modulen gibt es am Stand XY."
        ),
    ),
}


# -------------------------
# STUDIS Gate texts (DE)
# -------------------------
GATE_TEXT_STUDIS_DE: Dict[int, StepInfo] = {
    1: StepInfo(
        title="Schritt 1 – Camera Capture (Datenerfassung)",
        body=(
            "Bevor ein System Objekte erkennen kann, muss zuerst ein Bild aufgenommen werden. Die Kamera liefert dabei nicht sofort eine „Szene“, "
            "wie wir Menschen sie wahrnehmen, sondern nur eine große Menge an Zahlen: eine Matrix aus Pixelwerten. In der Animation siehst du, "
            "wie das aufgenommene Bild in Pixel unterteilt wird. Jedes Pixel enthält Intensitäten für Rot, Grün und Blau.\n\n"
            "Für die KI ist dieses Rohbild also kein „Hund“ oder „Mensch“, sondern reine Sensordaten. Deshalb ist dieser Schritt grundlegend: "
            "Alles, was später erkannt werden soll, hängt davon ab, wie gut die Daten am Anfang sind.\n\n"
            "Wenn das Bild zum Beispiel unscharf ist oder stark rauscht, kann das Modell später kaum noch zuverlässige Ergebnisse liefern. "
            "Dieses Prinzip nennt man oft „Garbage In, Garbage Out“: Schlechte Eingaben führen zu schlechten Ausgaben."
        ),
    ),
    2: StepInfo(
        title="Schritt 2 – Pre-Processing (Skalierung)",
        body=(
            "Nach der Aufnahme muss das Bild für das neuronale Netz vorbereitet werden. Der Sensor liefert ein großes Rohbild, das anschließend "
            "skaliert wird. Dies wird über Skalierer festgestellt, danach wird ein Ausschnitt ausgewählt.\n\n"
            "Denn die Modelle arbeiten nicht mit beliebigen Bildgrößen, sondern erwarten einen festen Input, beispielsweise 300 × 300 Pixel. "
            "Deshalb wird das Bild, wie in der Animation veranschaulicht, auf einen bestimmten Bereich skaliert.\n\n"
            "Dabei gehen jedoch oft Informationen verloren. Feine Details oder kleinere Objekte können verschwinden. Dieser Effekt ist in der "
            "Bildverarbeitung bekannt und wird oft als Aliasing bezeichnet.\n\n"
            "Wichtig ist: Das Modell sieht nicht die Realität, sondern nur eine komprimierte Version davon. Der Schritt des Pre-Processing wird "
            "daher als kritisch betrachtet, da alles, was hierbei verloren geht, später nicht mehr zurückgeholt werden kann."
        ),
    ),
    3: StepInfo(
        title="Schritt 3 – Inferenz (Feature Extraction)",
        body=(
            "Jetzt beginnt die eigentliche Analyse. Das neuronale Netz verarbeitet das Bild mit sogenannten Convolutional Neural Networks, den CNNs. "
            "Diese extrahieren Merkmale in mehreren Schichten.\n\n"
            "Hier wird dargestellt, wie das Netz in den ersten Layern einfache Muster wie Kanten oder Kontraste erkennt. In tieferen Schichten "
            "entstehen daraus komplexere Strukturen – etwa Objektteile wie „Rad“ oder „Auge“.\n\n"
            "Dieser Prozess wirkt oft „intelligent“, basiert aber mathematisch auf Faltungen und Matrixmultiplikationen. Faltung bedeutet: "
            "Ein kleines Muster-Prüfwerkzeug wird über das Bild geschoben, um wichtige Bildmerkmale wie Kanten, Formen oder Texturen herauszufiltern. "
            "Das Netz versteht also nicht wie ein Mensch, sondern transformiert Bilddaten statistisch, um relevante Features hervorzuheben.\n\n"
            "Dieser Schritt ist entscheidend, weil hier visuelle Information erstmals in eine interne Repräsentation für die KI übersetzt wird."
        ),
    ),
    4: StepInfo(
        title="Schritt 4 – Tensor Readout (Abstrakter Output)",
        body=(
            "Nach der Inferenz entsteht kein neues Bild, sondern ein Tensor: ein mehrdimensionales Zahlenfeld. Dieser Tensor enthält tausende Werte, "
            "die mögliche Objektpositionen, Klassenwahrscheinlichkeiten und Scores codieren.\n\n"
            "Das Modell „sieht“ also keine Objekte, sondern berechnet Wahrscheinlichkeiten. Es liefert keine symbolische Aussage wie "
            "„Hier ist ein Mensch“, sondern mathematische Hinweise darauf, wo etwas sein könnte.\n\n"
            "Dieser Moment zeigt besonders gut: KI arbeitet nicht mit Bedeutung, sondern mit Statistik. Erst in den nächsten Schritten wird aus diesem "
            "abstrakten Output wieder etwas, das für uns als Ergebnis interpretierbar ist."
        ),
    ),
    5: StepInfo(
        title="Schritt 5 – Decoding & Proposals (Hypothesen)",
        body=(
            "Nun wird der Tensor decodiert. Das Modell erzeugt eine große Anzahl an Vorschlägen, wo sich Objekte befinden könnten. Diese sogenannten "
            "Proposals basieren oft auf Anchor Boxes, die viele Positionen und Größen abdecken, wie du in der Animation sehen kannst.\n\n"
            "Dabei ist das System bewusst großzügig: Lieber entstehen zu viele Hypothesen als zu wenige, damit kein Objekt übersehen wird. Deshalb "
            "sieht man in dieser Phase oft ein „Chaos“ aus Rahmen – viele davon sind falsch oder unsicher.\n\n"
            "Objekterkennung ist also kein deterministischer Prozess, sondern ein probabilistisches Raten: Das Modell stellt Vermutungen auf, bevor es "
            "auswählen kann."
        ),
    ),
    6: StepInfo(
        title="Schritt 6 – NMS & Thresholding (Filterung)",
        body=(
            "Damit aus den vielen Hypothesen ein sinnvolles Ergebnis entsteht, werden die Vorschläge jetzt gefiltert.\n\n"
            "Zuerst werden alle Boxen entfernt, deren Wahrscheinlichkeit unter einem bestimmten Schwellenwert, also einem Confidence Threshold, liegt. "
            "Danach folgt die Non-Maximum Suppression (NMS): Wenn mehrere Boxen dasselbe Objekt markieren und sich stark überlappen, bleibt nur die "
            "wahrscheinlichste übrig. So bleiben in unserem Beispiel die gelben und grünen Boxen erhalten.\n\n"
            "Hier entscheidet das System also, welche Detektion tatsächlich relevant ist. Dieser Schritt ist notwendig, weil moderne Detektionsmodelle "
            "systematisch mehrere Vorschläge für ein einzelnes Objekt erzeugen.\n\n"
            "Erst durch diese Filterung entsteht eine klare, interpretierbare Auswahl."
        ),
    ),
    7: StepInfo(
        title="Schritt 7 – Coordinate Mapping & Reflexion (Ergebnis)",
        body=(
            "Wie du siehst, werden im letzten Schritt die finalen Boxen auf die ursprüngliche Bildgröße zurückgerechnet und sichtbar angezeigt. Erst jetzt entsteht das "
            "Ergebnis, das wir als Objekterkennung wahrnehmen: Bounding Box, Label und Confidence Score.\n\n"
            "Doch dieser Schritt ist auch ein Punkt für kritische Reflexion: Die Labels stammen aus dem Trainingsdatensatz des Modells. Erkennt die KI "
            "ein Objekt nicht, wählt sie oft das ähnlichste bekannte Label – das kann zu Fehlklassifikationen führen.\n\n"
            "Modelle sind also nicht objektiv, sondern abhängig von den Daten, mit denen sie trainiert wurden. Die Visualisierung ist deshalb nicht nur "
            "ein technischer Abschluss, sondern auch eine Einladung, die Grenzen der algorithmischen Wahrnehmung zu hinterfragen."
        ),
    ),
}


# -------------------------
# STUDIS Gate texts (EN)
# -------------------------
GATE_TEXT_STUDIS_EN: Dict[int, StepInfo] = {
    1: StepInfo(
        title="Step 1 – Camera Capture (Data acquisition)",
        body=(
            "Before a system can detect objects, it first has to capture an image. The camera does not deliver a “scene” the way humans perceive it, "
            "but a large set of numbers: a matrix of pixel values. In the animation you can see how the captured image is divided into pixels. "
            "Each pixel contains intensities for red, green, and blue.\n\n"
            "For the AI, this raw image is not a “dog” or a “person” yet—it is purely sensor data. That is why this step is fundamental: everything "
            "the model can detect later depends on the quality of the initial data.\n\n"
            "If the image is blurry or very noisy, the model will hardly be able to produce reliable results afterwards. This is often summarized as "
            "“Garbage In, Garbage Out”: poor inputs lead to poor outputs."
        ),
    ),
    2: StepInfo(
        title="Step 2 – Pre-processing (Normalization)",
        body=(
            "After capturing the image, it must be prepared for the neural network. Models do not accept arbitrary image sizes; they expect a fixed input, "
            "for example 300×300 pixels.\n\n"
            "That is why the image is downscaled and normalized (as shown in the animation). However, this always causes information loss: fine details "
            "or small objects can disappear. In image processing this effect is often described as aliasing.\n\n"
            "The key point is: the model does not see reality—it only sees a compressed version of it. Pre-processing is therefore a critical bottleneck: "
            "whatever is lost here cannot be recovered later."
        ),
    ),
    3: StepInfo(
        title="Step 3 – Inference (Feature extraction)",
        body=(
            "Now the actual analysis begins. The neural network processes the image using Convolutional Neural Networks (CNNs), which extract features "
            "across multiple layers.\n\n"
            "The visualization illustrates how early layers detect simple patterns such as edges or contrasts. Deeper layers combine these into more complex "
            "structures—object parts like a “wheel” or an “eye”.\n\n"
            "This can look “intelligent”, but mathematically it is based on convolutions and matrix multiplications. Convolution means sliding a small "
            "pattern-checking tool over the image to highlight important visual cues like edges, shapes, or textures. The network does not understand like a human; "
            "it transforms image data statistically to emphasize relevant features.\n\n"
            "This step is crucial because it is where visual information is translated into the AI’s internal representation."
        ),
    ),
    4: StepInfo(
        title="Step 4 – Tensor readout (Abstract output)",
        body=(
            "After inference, the result is not a new image, but a tensor: a multi-dimensional field of numbers. This tensor contains thousands of values "
            "encoding potential object locations, class probabilities, and scores.\n\n"
            "The model does not “see” objects—it computes probabilities. It does not output a symbolic statement like “There is a person here”, but rather "
            "mathematical hints about where something might be.\n\n"
            "This step makes it especially clear: AI does not operate on meaning, but on statistics. Only in the next steps does this abstract output become "
            "something we can interpret as a result."
        ),
    ),
    5: StepInfo(
        title="Step 5 – Decoding & proposals (Hypotheses)",
        body=(
            "Next, the tensor is decoded. The model produces a large number of proposals for where objects might be. These proposals often rely on anchor boxes "
            "covering many positions and sizes.\n\n"
            "The system is intentionally generous at this stage: it prefers too many hypotheses over too few, to avoid missing objects. That is why this phase "
            "often looks like “chaos” with many boxes—many of them are wrong or uncertain.\n\n"
            "Object detection is therefore not deterministic; it is probabilistic guessing. The model generates hypotheses before it can select the most plausible ones."
        ),
    ),
    6: StepInfo(
        title="Step 6 – NMS & thresholding (Filtering)",
        body=(
            "To turn many hypotheses into a meaningful result, the proposals are filtered.\n\n"
            "First, all boxes with a probability below a certain threshold (a confidence threshold) are removed. Then Non-Maximum Suppression (NMS) is applied: "
            "if multiple boxes mark the same object and overlap strongly, only the most probable one remains.\n\n"
            "This is where the system decides which detections are actually relevant. The step is necessary because modern detectors systematically create multiple "
            "proposals for a single object.\n\n"
            "Only after this filtering do we get a clear and interpretable selection."
        ),
    ),
    7: StepInfo(
        title="Step 7 – Coordinate mapping & reflection (Result)",
        body=(
            "In the final step, the selected boxes are mapped back to the original image size and displayed. Only now do we see what we perceive as object detection: "
            "bounding box, label, and confidence score.\n\n"
            "But this is also a point for critical reflection: labels come from the model’s training dataset. If the AI has never learned an object, it will often choose "
            "the most similar known label—leading to misclassifications.\n\n"
            "Models are not objective; they depend on the data they were trained on. The visualization is therefore not only a technical conclusion, but also an invitation "
            "to reflect on the limits of algorithmic perception."
        ),
    ),
}


def total_steps_for_level(level: str) -> int:
    lv = (level or "").upper()
    if lv in ("SCHUELER", "SCHÜLER", "PUPIL", "SCHOOL", "SCHOOLER"):
        return 4
    if lv in ("STUDENT", "STUDIS", "STUDI", "STUDENTS"):
        return 7
    return 7


def build_step_text(level: str, lang: str = "DE", debug: object | None = None, **kwargs) -> Dict[int, StepInfo]:
    _ = (lang, debug, kwargs)
    lv = (level or "").upper()
    if lv in ("SCHUELER", "SCHÜLER", "PUPIL", "SCHOOL", "SCHOOLER"):
        return STEP_TEXT_SCHUELER_DE
    return STEP_TEXT_STUDIS_DE


def build_gate_text(level: str, lang: str = "DE", debug: object | None = None, **kwargs) -> Dict[int, StepInfo]:
    """
    Black intermediate screens shown between analysis steps.
    Defined for STUDENT (DE/EN). Others return empty dict.
    """
    _ = (debug, kwargs)
    lv = (level or "").upper()
    lg = (lang or "DE").upper()
    is_student = lv in ("STUDENT", "STUDIS", "STUDI", "STUDENTS")

    if not is_student:
        return {}

    if lg.startswith("EN"):
        return GATE_TEXT_STUDIS_EN
    return GATE_TEXT_STUDIS_DE


# -------------------------
# StepTransformer (Visual simulation)
# -------------------------
class StepTransformer:
    @staticmethod
    def to_gray(rgb: np.ndarray) -> np.ndarray:
        r = rgb[:, :, 0].astype(np.float32)
        g = rgb[:, :, 1].astype(np.float32)
        b = rgb[:, :, 2].astype(np.float32)
        y = 0.299 * r + 0.587 * g + 0.114 * b
        return y.astype(np.uint8)

    @staticmethod
    def sobel_edges(gray: np.ndarray) -> np.ndarray:
        g = gray.astype(np.int16)
        gx = (np.roll(g, -1, axis=1) - np.roll(g, 1, axis=1))
        gy = (np.roll(g, -1, axis=0) - np.roll(g, 1, axis=0))
        mag = np.clip(np.abs(gx) + np.abs(gy), 0, 255).astype(np.uint8)
        return mag

    @staticmethod
    def pixelate_and_square(rgb: np.ndarray, size: int = 300) -> np.ndarray:
        h, w, _ = rgb.shape
        ys = (np.linspace(0, h - 1, size)).astype(np.int32)
        xs = (np.linspace(0, w - 1, size)).astype(np.int32)
        small = rgb[ys][:, xs]
        ys2 = (np.linspace(0, size - 1, h)).astype(np.int32)
        xs2 = (np.linspace(0, size - 1, w)).astype(np.int32)
        up = small[ys2][:, xs2]
        return up.astype(np.uint8)

    @staticmethod
    def fake_feature_map(rgb: np.ndarray) -> np.ndarray:
        g = StepTransformer.to_gray(rgb)
        e = StepTransformer.sobel_edges(g).astype(np.float32)
        if e.max() > 0:
            e = (e / e.max()) * 255.0
        e = e.astype(np.uint8)
        r = np.clip(e * 0.25, 0, 255).astype(np.uint8)
        gg = np.clip(e * 0.85, 0, 255).astype(np.uint8)
        b = np.clip(e * 1.10, 0, 255).astype(np.uint8)
        return np.stack([r, gg, b], axis=2)

    @staticmethod
    def dim(rgb: np.ndarray, factor: float) -> np.ndarray:
        return np.clip(rgb.astype(np.float32) * factor, 0, 255).astype(np.uint8)

    @staticmethod
    def matrix_like_overlay(rgb: np.ndarray) -> np.ndarray:
        out = StepTransformer.dim(rgb, 0.12)
        h, w, _ = out.shape
        rng = np.random.default_rng(1)
        for y in range(30, h, max(22, h // 28)):
            x0 = rng.integers(0, max(1, w - 200))
            length = rng.integers(140, 360)
            x1 = int(min(w - 1, x0 + length))
            out[y:y + 2, x0:x1, :] = np.array([220, 240, 210], dtype=np.uint8)
        for _ in range(30):
            y = rng.integers(0, h)
            x = rng.integers(0, w)
            out[y:y + 1, x:x + 1, :] = np.array([227, 217, 191], dtype=np.uint8)
        return out

    def apply(self, frame_rgb: np.ndarray, step: int, level: str | None = None) -> np.ndarray:
        if frame_rgb is None:
            return frame_rgb

        lv = (level or "").upper()

        # -------- SCHUELER (4 steps) visuals --------
        if lv in ("SCHUELER", "SCHÜLER", "PUPIL", "SCHOOL", "SCHOOLER"):
            if step == 1:
                return self.pixelate_and_square(frame_rgb, size=300)
            if step == 2:
                return self.fake_feature_map(frame_rgb)
            if step == 3:
                return self.dim(frame_rgb, 0.55)
            return frame_rgb

        # -------- STUDIS (7 steps) visuals --------
        if step == 1:
            # Change: Pixelated via 300x300 bottleneck, matches Step 2 visuals but displayed in 16:9
            return self.pixelate_and_square(frame_rgb, size=300)
        if step == 2:
            return self.pixelate_and_square(frame_rgb, size=300)
        if step == 3:
            return self.fake_feature_map(frame_rgb)
        if step == 4:
            return self.matrix_like_overlay(frame_rgb)
        if step == 5:
            return self.dim(frame_rgb, 0.35)
        if step == 6:
            return self.dim(frame_rgb, 0.70)
        return frame_rgb
