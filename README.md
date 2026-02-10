<img 
  src="https://raw.githubusercontent.com/watsonove/IMX500-Object-Detection-UI/main/logo.png" 
  alt="logo" 
  style="width:500px; float: left;"
/>
# IMX500-Object-Detection-UI
Diese Anwendung ist eine interaktive Bildungssoftware für den Raspberry Pi 4/5 und die Sony IMX500 AI Camera. Ihr primäres Ziel ist die didaktische Aufbereitung von Objekterkennung.

Wo Standard-Anwendungen die Objekterkennung oft als Blackbox behandeln, bricht diese Software die komplexen Prozesse auf und visualisiert sie verständlich. Der Nutzer wird Schritt für Schritt durch die Pipeline geführt – beginnend bei der Rohdatenerfassung des IMX500-Sensors bis hin zur grafischen Darstellung der Erkennungsergebnisse. Um unterschiedlichen Wissensständen gerecht zu werden, bietet die UI zwei Modi ("Schüler:innen" und "Student:innen"), was sie zu einem idealen Werkzeug für Lehrende an Schulen, Universitäten sowie für Exponate auf Fachmessen macht. 

Einen ausführlichen Projektbericht finden Sie unter: [Projektbericht](https://github.com/watsonove/IMX500-Object-Detection-UI/blob/main/M2_Projektbericht_Interaktive_Visualisierung_Objekterkennung.pdf).

## 🚀 Features  

1. **Live-Objektdetektion:** Nutzt den Hardware-Beschleuniger des IMX500 Sensors.

2. **Zwei Lern-Niveaus:**
  
* **Schüler:in:** 4 vereinfachte Schritte, spielerischer Zugang.
    
* **Student:in:** 7 detaillierte Schritte mit technischer Tiefe (Pre-Processing, Tensoren, NMS).

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

## 📹 Walkthrough

Durch Anklicken des Bildes können Sie einen Walkthrough der Anwendung abrufen.

[![Video-Titel](https://img.youtube.com/vi/wMuOgq-UNXw/0.jpg)](https://www.youtube.com/watch?v=wMuOgq-UNXw)


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
    
Das System benötigt `Python 3.11`, `picamera2` (vorinstalliert auf Bookworm) und `pygame`, sowie die IMX500 firmware `imx500`.
    
Zuerst sicher gehen, dass der Raspberry PI die aktuelle Software hat:

```bash
sudo apt update && sudo apt full-upgrade  
```

Dann die Abhängigkeiten installieren:

```bash
sudo apt install python3-libcamera python3-kms++ python3-pygame
```

Sowie die IMX500 firmware:

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

Hier mit mobilenetv2:

```bash

python3 app.py --model=/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk

```


## 🎮 Steuerung
  

Die Anwendung ist für Tastatur- und Mausbedienung optimiert.

| Taste / Aktion     | Funktion                                                                |
| :----------------- | :---------------------------------------------------------------------- |
| **LEERTASTE**      | **Freeze / Unfreeze:** Wechselt zwischen Live-Kamera und Analyse-Modus. |
| **ENTER**          | **Weiter:** Geht zum nächsten Schritt oder bestätigt das Gate.        |
| **BACKSPACE**      | **Zurück:** Geht zum vorherigen Schritt oder zurück zum Gate.           |
| **Mausklick**      | Bedienung der UI-Buttons (Sprache, Home, Audio, Level-Wahl).            |
| **Mausbewegung**   | Im "Schritt 1" (Analyse): Zeigt RGB-Werte unter dem Mauszeiger an.      |
| **Q** oder **ESC** | Beendet das Programm.                                                   |

## 📂 Projektstruktur

```text
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
```

## 🌍 Sprache & Audio  

1. Sprachwechsel: Klicke oben rechts auf den Button DE / EN, um die Sprache der Texte und des Audios zu wechseln.  

2. Audio-Dateien:
  
* Deutsch: schueler_step_X.mp3

* Englisch: schueler_step_X_english.mp3

* Die Dateien müssen im Ordner assets/audio/ liegen.

## 📊 Ablaufdiagramm app.py

Visualisiert den User Flow.

Zeigt, wie der Nutzer durch die "Gates" (Erklärbildschirme) in die tiefere Analyse geführt wird und wie er jederzeit durch Tastendruck (Space) den Zustand wechseln kann.

[![](https://mermaid.ink/img/pako:eNp9VN1u2jAUfhXLV-0EjBB-Si4mBUorVJQhYJ3WMSEPDkkEcZBjtxuIt-ExdseLzXb-CIXmIoq_H845n212eB4uAFs44oTDvU9cRoLya21KkXx-fvqFyuUvaNB_7vWdyeirhcacMB6zGRprbOe-7zxa6Gntz1eIiCXqTuxYGb91iVSHdjF4WsYW0Rvx1jmRAJrshnTpu-O5J2ANzEIdwXlI0RRL6PhPQlP8oZGLBVB-6ouR1Laf0mSspEHlHX1zHD3UAF5hjVx4Ox68NU-l8USJ6NJEKqIczb-SKCR76jp1jjkDEvjULdIZrEVSLHdkaHd7aEIiDrk2mybdKK1_tCe91HDzwAC2cHu9PaW-1p5N_YBwP6Qv4LtAi6IzUhu-y2MD1BbLPt0IXtQXuXyynjPpjdDnZMuuDKe71C059uDHWM7XgYgfD9x3hUrvfKpEdj132Nh0qxo_Tz4jtNA5HuaezJwpIun1Y8dzyDxgcpVYOnb3Se9F0VZcxU0rwyB0_dV522kdY3Yh15SszYYMhiycQxS9O1GpyJw9AOGCQfSer1QqRXB_ZTPScPPDlsWE5D1lPufoJrl4t5dt6rCq-8a3p6bfAHQByXx7XMIu8xfY4kxACQfAAqKWWKczxdyDAKbYkp8LwlbqiivPhtCXMAxSGwuF62FrSdaRXInNIv8HzCSqKuuGgnJsmTX9E9ja4T_YMlpmpWE279qNVsNoN0xDsn8lbDQqNaPerLZq5l2rKYl9CW911WqlZVSr1WatXa-bRsOo1_f_AVlGh5o?type=png)](https://mermaid.live/edit#pako:eNp9VN1u2jAUfhXLV-0EjBB-Si4mBUorVJQhYJ3WMSEPDkkEcZBjtxuIt-ExdseLzXb-CIXmIoq_H845n212eB4uAFs44oTDvU9cRoLya21KkXx-fvqFyuUvaNB_7vWdyeirhcacMB6zGRprbOe-7zxa6Gntz1eIiCXqTuxYGb91iVSHdjF4WsYW0Rvx1jmRAJrshnTpu-O5J2ANzEIdwXlI0RRL6PhPQlP8oZGLBVB-6ouR1Laf0mSspEHlHX1zHD3UAF5hjVx4Ox68NU-l8USJ6NJEKqIczb-SKCR76jp1jjkDEvjULdIZrEVSLHdkaHd7aEIiDrk2mybdKK1_tCe91HDzwAC2cHu9PaW-1p5N_YBwP6Qv4LtAi6IzUhu-y2MD1BbLPt0IXtQXuXyynjPpjdDnZMuuDKe71C059uDHWM7XgYgfD9x3hUrvfKpEdj132Nh0qxo_Tz4jtNA5HuaezJwpIun1Y8dzyDxgcpVYOnb3Se9F0VZcxU0rwyB0_dV522kdY3Yh15SszYYMhiycQxS9O1GpyJw9AOGCQfSer1QqRXB_ZTPScPPDlsWE5D1lPufoJrl4t5dt6rCq-8a3p6bfAHQByXx7XMIu8xfY4kxACQfAAqKWWKczxdyDAKbYkp8LwlbqiivPhtCXMAxSGwuF62FrSdaRXInNIv8HzCSqKuuGgnJsmTX9E9ja4T_YMlpmpWE279qNVsNoN0xDsn8lbDQqNaPerLZq5l2rKYl9CW911WqlZVSr1WatXa-bRsOo1_f_AVlGh5o)

## 📝 Lizenz  

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
