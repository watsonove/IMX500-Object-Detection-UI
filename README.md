# IMX500-Object-Detection-UI
Eine interaktive, didaktische Anwendung für den Raspberry Pi 4/5 mit der Sony IMX500 AI Camera. Diese Software visualisiert Schritt für Schritt wie Objekterkennung funktioniert. Von der Rohdatenerfassung bis zum fertigen Ergebnis.

Die Anwendung bietet zwei Lernniveaus ("Schüler:innen" und "Student:innen") und ist für den Einsatz auf Messen, in Schulen oder Universitäten konzipiert.  

## 🚀 Features  

1. **Live-Objektdetektion:** Nutzt den Hardware-Beschleuniger des IMX500 Sensors.

2. **Zwei Lern-Niveaus:**
  
* **Schüler:** 4 vereinfachte Schritte, spielerischer Zugang.
    
* **Student:** 7 detaillierte Schritte mit technischer Tiefe (Pre-Processing, Tensoren, NMS).

3. **Interaktiver Workflow:**
  
* *Live-Modus:* Echtzeit-Erkennung.
    
* *Analyse-Modus:* Einfrieren eines Bildes und schrittweise Durchleuchtung der KI-Pipeline.

4. **Pixel-Inspektor:** In Schritt 1 können einzelne Pixel mit der Maus untersucht werden (RGB-Werte), um das Konzept der "Matrix" zu verdeutlichen.

5. **Gate-Animationen:** Zwischen den Analyseschritten werden animierte Erklärungen (Bildsequenzen) abgespielt.

6. **Bilingual & Audio:** Vollständig in Deutsch und Englisch verfügbar, inklusive Sprachausgabe für Erklärtexte.

7. **Didaktische Visualisierung:**
   
* Simulation von Auflösungsreduzierung (Pixelation).

* Visualisierung von Feature-Maps (Sobel-Filter).
  
* Darstellung von Bounding Boxes und Confidence Scores.

## 🛠 Hardware-Voraussetzungen 

* **Raspberry Pi 4 oder 5**

* **Betriebssystem:** Raspberry Pi OS **Bookworm (64-bit)** (Desktop-Version empfohlen für GUI).

* **Kamera:** Raspberry Pi AI Camera (Sony IMX500).

* **Display:** Monitor + Maus/Tastatur.

* **Audio:** Lautsprecher oder Kopfhörer (für die Sprachausgabe).

## 📦 Installation 

1.  **Repository klonen / Dateien kopieren:**

```bash
git clone https://github.com/watsonove/IMX500-Object-Detection-UI/
```

Stelle sicher, dass alle Projektdateien (`app.py`, `detector.py`, `steps.py`, Ordner `ui/` und `assets/`) vorhanden sind. 

2.  **Abhängigkeiten installieren:**

Alle Befehle werden im Terminal ausgeführt.
    
Das System benötigt Python 3, `picamera2` (vorinstalliert auf Bookworm) und `pygame`, sowie die IMX500 firmware `imx500`.
    
Zuerst sicher gehen, dass der Raspberry PI die aktuelle Software hat:

```bash
sudo apt update && sudo apt full-upgrade  
```

Dann die Abhängigkeiten installieren:

```bash
sudo apt install python3-libcamera python3-kms++ python3-pygame
```

Sowie

```bash
sudo apt install imx500-all
```
  
Falls numpy fehlt:

```bash
sudo apt install python3-numpy
```

Nachdem du nun die Voraussetzungen installiert hast, starte den Raspberry Pi neu:
  
```bash
sudo reboot
```
 
3.  **Assets prüfen:**

Stelle sicher, dass die Ordnerstruktur korrekt ist (siehe unten "Projektstruktur"). Besonders wichtig sind die Bildsequenzen in `assets/schritt_X_experte/`.

## ▶️ Starten der Anwendung  

Starte die Anwendung über das Terminal. Du musst den Pfad zu deiner Model-Datei angeben (z. B. ein MobileNet oder EfficientDet Modell, das für den IMX500 kompiliert ist).  

```bash

python3 app.py --model=/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk

```

## 🎮 Steuerung
  

Die Anwendung ist für Tastatur- und Mausbedienung optimiert.

| Taste / Aktion     | Funktion                                                                |
| :----------------- | :---------------------------------------------------------------------- |
| **LEERTASTE**      | **Freeze / Unfreeze:** Wechselt zwischen Live-Kamera und Analyse-Modus. |
| **ENTER**          | **Weiter:** Geht zum nächsten Schritt oder bestätigt das "Gate".        |
| **BACKSPACE**      | **Zurück:** Geht zum vorherigen Schritt oder zurück zum Gate.           |
| **Mausklick**      | Bedienung der UI-Buttons (Sprache, Home, Audio, Level-Wahl).            |
| **Mausbewegung**   | Im "Schritt 1" (Analyse): Zeigt RGB-Werte unter dem Mauszeiger an.      |
| **Q** oder **ESC** | Beendet das Programm.                                                   |

## 📂 Projektstruktur

  imx500_gui/
├── app.py                 # Hauptprogramm (Controller, Event-Loop)\
├── detector.py            # Hardware-Interface (Kamera, IMX500 Post-Processing)\
├── steps.py               # Texte und Bild-Transformationen (Logik)\
├── README.md              # Dokumentation\
├── ui/                    # UI-Modul (View)\
│   ├── __init__.py\
│   ├── renderer.py        # Zeichenfunktionen (Balken, Overlay, Pixel-Grid)\
│   ├── textlayout.py      # Textumbruch und -formatierung\
│   └── theme.py           # Farben und Design-Konstanten\
└── assets/                # Medien-Dateien\
    ├── Kanit-Bold.ttf     # Schriftart\
    ├── landingpagebg.jpg  # Hintergrundbild\
    ├── audio/             # MP3 Sprachdateien (DE & EN)\
    ├── schritt_1_experte/ # Bildsequenz Animation Schritt 1\
    ├── schritt_2_experte/ # Bildsequenz Animation Schritt 2\
    ├── ...                # (weitere Ordner bis schritt_7)\
    └── schritt_7_experte/\

## 🌍 Sprache & Audio  

1. Sprachwechsel: Klicke oben rechts auf den Button DE / EN, um die Sprache der Texte und des Audios zu wechseln.  

2. Audio-Dateien:
  
* Deutsch: schueler_step_X.mp3

* Englisch: schueler_step_X_english.mp3

* Die Dateien müssen im Ordner assets/audio/ liegen.

## 📝 Lizenz  

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
