text
# IMX500 Object Detection GUI (OOP)

Eine modulare, objektorientierte Python-Anwendung, die den Sony IMX500 auf dem Raspberry Pi nutzt, um Objekt­detektion in einer didaktisch aufbereiteten, schrittweisen Pygame-GUI zu visualisieren. Die Anwendung ist so strukturiert, dass Lesbarkeit, Wartbarkeit und Erweiterbarkeit im Vordergrund stehen (OOP, klare Verantwortlichkeiten, modulare Architektur, Typannotationen, Docstrings, sprechende Namen). [web:410][web:415][web:418]

---

## Überblick

Diese Anwendung demonstriert:

- Live-Objektdetektion mit dem IMX500-Sensor (über Picamera2). [web:397][web:403]
- Einfrieren eines Frames und Analyse in **4 Schritten**:
  1. Vorverarbeitung (Originalbild + Pixel-Grid, „RGB Pixel“-Badge).
  2. Threshold-/Binarisierungsansicht.
  3. Merkmalsextraktion (Kanten/Konturen mit Sobel).
  4. Lokalisierung (Bounding Boxes + Top‑3 Labels mit Score).
- Darstellung in einer minimalen, fullscreen Pygame-GUI. [web:396][web:405]

Die komplette Logik ist in Klassen gekapselt, um eine saubere Trennung von **Hardware**, **Datenmodellen**, **Bildtransformationen**, **Rendering** und **Steuerlogik** zu erreichen.

---

## Projektstruktur

```text
imx500_gui/
├─ app.py              # Haupt-Controller, Event-Loop, Layout, verbindet alle Komponenten
├─ detector.py         # IMX500Detector, Det, FrameSnapshot (Hardware + Parsing)
├─ steps.py            # StepTransformer + STEP_TEXT (fachliche Schritte)
├─ ui/
│  ├─ __init__.py
│  ├─ theme.py         # Theme (Farben, Radii, Styles)
│  ├─ textlayout.py    # TextLayout (Wrap, Font-Fitting)
│  └─ renderer.py      # Renderer (alle Zeichenoperationen)

Zentrale Design-Idee:
Jede Datei/Klasse hat genau eine Hauptverantwortung (Single Responsibility Principle). [web:410] Der Code lässt sich so leicht lesen, testen und in Unterricht/Präsentationen verwenden.
Installation & Voraussetzungen

    Raspberry Pi mit IMX500-Kamera.

    Python 3.10+.

    Bibliotheken:

        Picamera2 (inkl. IMX500-Unterstützung). [web:397][web:403]

        Pygame (für GUI und Event-Handling). [web:392][web:405]

Beispiel (vereinfachte Installation, kann je nach System abweichen):

bash
sudo apt update
sudo apt install python3-picamera2 python3-pygame
# IMX500-spezifische Pakete laut Hersteller/Distribution installieren

Ausführen

Im Projektverzeichnis (wo imx500_gui/ liegt):

bash
python3 -m imx500_gui.app \
  --model=/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk

Wichtige Optionen:

    --model: Pfad zum IMX500-Modell (.rpk).

    --threshold: Konfidenzschwelle für Detections (Standard: 0.55).

    --iou: IOU-Schwelle für NMS (Standard: 0.65).

    --max-detections: Maximale Anzahl an Boxen.

    --cam-width, --cam-height: Auflösung des Kamera-Streams.

Beispiel:

bash
python3 -m imx500_gui.app \
  --model=/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk \
  --threshold=0.55 --iou=0.65 --max-detections=10

Bedienung der GUI

    SPACE

        In LIVE: friert ein Frame ein und wechselt nach ANALYSE, Step 1.

        In ANALYSE: beendet die Analyse und kehrt zu LIVE zurück.

    ENTER

        In ANALYSE: zum nächsten Schritt (max. Step 4).

    BACKSPACE

        In ANALYSE: zum vorherigen Schritt (min. Step 1).

    ESC oder q

        Anwendung beenden.

Im LIVE-Modus läuft kontinuierlich die Kamera, Detections werden über dem Videobild als Boxen angezeigt, während im ANALYSE-Modus ein Snapshot in den vier didaktischen Schritten visualisiert wird.
Architektur & Klassen
detector.py

Klassen: Det, FrameSnapshot, IMX500Detector

    Det
    Reine Datenklasse für ein einzelnes Objekt (label, conf, box).

    FrameSnapshot
    Kapselt einen eingefrorenen Frame inklusive Metadaten:

        frame_rgb: letzter RGB‑Frame.

        src_size: Originalgröße des Frames (Breite, Höhe).

        dets: Liste aller Detections.

        top_dets: Top‑3 Detections (für Box-Overlay).

        top3: Top‑3 Labels + Scores (für Score-Panel).

    IMX500Detector

        Konfiguration des IMX500 (Netzwerk, Labels, Postprocessing). [web:397]

        Initialisierung und Betrieb von Picamera2 (Preview-Stream).

        capture_snapshot(): Ein Frame + Detections → FrameSnapshot.

        parse_detections(): Postprocessing der Netzwerkoutputs (inkl. NMS, Koordinaten-Konvertierung).

steps.py

Klassen/Strukturen: StepInfo, STEP_TEXT, StepTransformer

    StepInfo
    Titel + Body-Text eines Schritts (für das rechte Panel).

    STEP_TEXT
    Mapping von Schrittindex (1–4) auf StepInfo, beschreibt in natürlicher Sprache:

        Vorverarbeitung.

        Merkmalsextraktion (Kanten/Konturen).

        Klassifizierung (Scores).

        Lokalisierung (Bounding Boxes).

    StepTransformer

        Implementiert die Bildtransformationen für das linke Video-Panel:

            Step 1: Originalbild (Overlays im Renderer).

            Step 2: Binarisierte, vignettiert verstärkte Grauansicht.

            Step 3: Kanten/Konturen mit Sobel, invertiert.

            Step 4: Originalbild (Overlays im Renderer).

Die Logik ist vollständig von Pygame entkoppelt und nutzt ausschließlich NumPy-Operationen.
ui/theme.py

Klasse: Theme

    Zentraler Ort für:

        Hintergrundfarbe, Panel-Farben, Linien.

        Text-Farben (normal/muted).

        Akzentfarben (Scores).

        Border-Radius (RADIUS).

    Anpassungen am Look & Feel erfolgen hier, ohne Logikcode zu berühren.

ui/textlayout.py

Klasse: TextLayout

    Zuständig für:

        wrap_lines(...): Wortweise Zeilenumbrüche basierend auf font.size() und Panelbreite. [web:254]

        fit_title_and_body(...): Binäre Suche auf Fontgröße, bis Titel und Body in die vorgesehene Fläche passen.

        draw_wrapped_lines(...): Zeichnet umbrochene Texte auf eine Oberfläche (inkl. Zeilenabstand).

Die Klasse ist bewusst generisch gehalten, so dass sie auch in anderen Pygame-Projekten wiederverwendbar ist. [web:411][web:416]
ui/renderer.py

Klasse: Renderer

    Rendering-Layer für alles, was gezeichnet wird:

        Karten/Panels (abgerundete Rechtecke, Outlines).

        Text-Rendering (Labels, Überschriften).

        Pills (Boxen hinter Labels).

        Pixel-Grid (für Step 1 „RGB Pixel“).

        Step-Indikator (4 Kreise + Fortschrittslinie).

        Score-Balkendiagramm (inkl. Threshold-Linie). [web:405]

Wichtige Methoden:

    draw_card(...), draw_text(...)

    draw_pixel_grid(...), draw_pill(...)

    rect_in_video_coords(...): rechnet Boxen von Quellgröße auf Video-Panel um.

    draw_step_indicator(...)

    draw_bar_chart(...)

app.py

Klasse: App

    Orchestriert alle Komponenten:

        Instanziiert IMX500Detector, StepTransformer, TextLayout, Renderer, Theme.

        Verwaltet den Zustand:

            mode: "LIVE" oder "ANALYSE".

            step: 0–4.

            snapshot: aktueller FrameSnapshot.

        Implementiert den Event-Loop (Pygame):

            handle_events(): Tastatur-Eingaben verarbeiten. [web:392][web:396]

            update(): im LIVE-Modus Snapshot aktualisieren.

            draw(): Layout berechnen und Rendering in drei klar getrennte Bereiche aufteilen:

                _draw_left_view(...)

                _draw_header(...)

                _draw_right_panel(...)

Ablauf:

    LIVE: kontinuierliches Capturing über IMX500Detector.

    SPACE: Snapshot einfrieren, in ANALYSE wechseln (Step 1).

    ENTER / BACKSPACE: Steps 1–4 durchlaufen (verschiedene Visualisierungen).

    SPACE: zurück zu LIVE.

UML-Diagramm (Textform)

Für den Projektbericht oder die Dokumentation kann folgende UML-Klassenübersicht genutzt werden (vereinfachte Darstellung):

text
+----------------------+
|      IMX500Detector  |
+----------------------+
| - args               |
| - imx500             |
| - intrinsics         |
| - picam2             |
+----------------------+
| + capture_snapshot() |
| + parse_detections() |
| + stop()             |
+----------------------+

+----------------------+
|        Det           |
+----------------------+
| + label: str         |
| + conf: float        |
| + box: (x,y,w,h)     |
+----------------------+

+------------------------------+
|       FrameSnapshot          |
+------------------------------+
| + frame_rgb: np.ndarray?     |
| + src_size: (int,int)        |
| + dets: List[Det]            |
| + top3: List[(str,float)]    |
| + top_dets: List[Det]        |
+------------------------------+

+----------------------+
|    StepTransformer   |
+----------------------+
| + apply(frame,step)  |
+----------------------+

+----------------------+
|       StepInfo       |
+----------------------+
| + title: str         |
| + body: str          |
+----------------------+

+----------------------+
|        Theme         |
+----------------------+
| + BG                 |
| + PANEL              |
| + ...                |
+----------------------+

+---------------------------+
|        TextLayout         |
+---------------------------+
| + wrap_lines(...)         |
| + draw_wrapped_lines(...) |
| + fit_title_and_body(...) |
+---------------------------+

+----------------------+
|       Renderer       |
+----------------------+
| - t: Theme           |
+----------------------+
| + draw_card(...)     |
| + draw_text(...)     |
| + draw_pixel_grid()  |
| + draw_pill(...)     |
| + rect_in_video_...  |
| + draw_step_...      |
| + draw_bar_chart()   |
+----------------------+

+------------------------------+
|            App               |
+------------------------------+
| - args                       |
| - theme: Theme               |
| - detector: IMX500Detector   |
| - transformer: StepTransformer|
| - text_layout: TextLayout    |
| - renderer: Renderer         |
| - mode: str                  |
| - step: int                  |
| - snapshot: FrameSnapshot    |
| - ...                        |
+------------------------------+
| + run()                      |
| - handle_events()            |
| - update()                   |
| - draw()                     |
| - _draw_left_view(...)       |
| - _draw_header(...)          |
| - _draw_right_panel(...)     |
+------------------------------+

Beziehungen:
- App → IMX500Detector (Komposition)
- App → StepTransformer
- App → TextLayout
- App → Renderer
- App verwendet FrameSnapshot und Det als Datenmodelle
- Renderer verwendet Theme
- StepTransformer nutzt STEP_TEXT indirekt über App (für Beschreibung) und NumPy für Transformationen

Dieses Diagramm kannst du entweder direkt übernehmen oder in ein Grafiktool (PlantUML, draw.io, etc.) übertragen und dort als Grafik ausgeben.
Design-Entscheidungen (Clean Code / OOP)

    Single Responsibility: Jede Klasse hat genau eine Hauptaufgabe (Detector vs. Schritte vs. Rendering vs. Layout). [web:410]

    Abstraktionsebenen trennen:

        Hardware-Zugriff in detector.py.

        Fachliche Verarbeitung der Schritte in steps.py.

        UI-spezifische Darstellung in ui/.

        Steuerlogik in app.py. [web:417]

    Lesbare Struktur:
    Der Hauptloop in App.run() ist kurz, komplexere Aufgaben sind in kleine, gut benannte Methoden ausgelagert. [web:396][web:405]

    Wiederverwendbarkeit:
    TextLayout und Renderer sind ausreichend generisch, um in anderen Pygame-Projekten genutzt zu werden. [web:411][web:416]

Mögliche Erweiterungen

    Demo-Mode ohne Hardware:

        DummyDetector implementieren, der statt der Kamera ein Beispielbild lädt.

        Ideal für Präsentationen oder Entwicklung auf einem Laptop ohne IMX500.

    Konfigurationsdatei:

        Thresholds, Farben, Texte aus einer .toml/.yaml laden, um Code-Anpassungen zu minimieren.

    Testbarkeit:

        Unit-Tests für StepTransformer (Form, Wertebereiche).

        Tests für TextLayout-Funktionen (Zeilenumbrüche, Fontgrößen).

    Logging:

        FPS, Anzahl Detections, aktuelle Step-Nummer per Logging-Modul ausgeben.

Lizenz und Autorenschaft

    Lizenz (z.B. MIT/Apache‑2.0) in einer separaten LICENSE-Datei definieren.

    In README.md und am Kopf der Python-Dateien können Autor:in, Datum, Projektkontext und Versionsstand dokumentiert werden.
