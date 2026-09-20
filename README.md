# English Reader

A lightweight Windows desktop reader for English listening and shadowing practice.

## Download

**[Latest Release](https://github.com/mzl1216-coder/EnglishReader/releases/latest)**

- **EnglishReader-Setup-x64.exe** — recommended installer.
- **EnglishReader-Portable-x64.zip** — extract and run `EnglishReader.exe`.

Windows 10 (1809 or later) / Windows 11, x64. **No Python, pip, or API key required.**
Online Neural voices require an internet connection. Windows offline voices are
available explicitly as a lower-quality fallback.

## Features

- Click a sentence to start reading continuously
- Double-click to read only one sentence
- Natural American Neural voices: Andrew, Aria, Ava, Brian, plus live available voices
- Current sentence highlighting and automatic scrolling
- Sentence Practice Mode and repeat current sentence
- Adjustable speed, generated naturally by TTS
- Always-on-top mini window
- Transparent desktop subtitles; thin border and controls appear on hover
- Hover an English word for Chinese meanings and phonetics
- Automatic text saving, settings and reading position restoration
- Voice preview without losing the article position
- Light and dark themes

## Installation

Download the installer from Releases, open it, choose an installation folder and
optionally create a desktop shortcut. The default is `C:\Program Files\English Reader`.
For portable use, extract the **entire ZIP** before opening `EnglishReader.exe`.
Keep the `_internal` folder beside the executable. Portable refers to no-install
operation; preferences are stored in your Windows user profile.

This personal release is not code-signed. Windows SmartScreen may show an unknown
publisher warning. Verify the release source and follow your organization's security
policy. Do not disable Windows Defender or change security policies. If your device
blocks unsigned apps, ask its administrator; code signing is planned for a future release.

## Usage

1. Paste English text with **Ctrl+V** (replaces the current article in reading mode).
2. Single-click a sentence to read from there to the end. A short delay uses your
   Windows double-click interval; existing audio stops on the first click.
3. Double-click a sentence to hear only that sentence. Its highlight remains.
4. Choose **Sentence Practice** for one sentence at a time; Space advances after it ends.
5. Choose a voice and use **Preview**. Preview temporarily interrupts the article and
   restores its sentence, playback position and paused/playing state afterward.
6. Change **Speed** for the next sentence. **Formal American** in Settings selects
   the first available preferred US voice, 0.9x, neutral pitch and full volume.
7. The default **transparent subtitle window** floats over the desktop with no solid
   background or title bar. Move the pointer over it to reveal a thin border, drag
   handle, close button and playback controls. Drag its edges to resize. Text is
   dark gray without a glow; the current sentence is bold black. **Ctrl+M** switches to the
   full normal window. Right-click the text for Settings; Ctrl+L toggles always-on-top.
8. **Ctrl+E** toggles editing. While editing, spaces and R type normally. Return to
   reading mode to use click-to-read. Ctrl+V inserts normally while editing.

Manual wheel/scrollbar/keyboard scrolling pauses automatic following. After **15
seconds without scrolling**, the view smoothly returns to the sentence currently
being played, even if that sentence has not finished. Scrolling again restarts the
countdown. Paused/stopped reading is not moved automatically.

Hover over a word for about half a second to see Chinese meanings and phonetics.
Common business vocabulary is bundled for offline use. Other words are looked up
online through Youdao and successful results are cached locally. Only the hovered
word is sent, not the article. Online lookup requires internet and can be unavailable;
hover tips show a short retry message instead of interrupting speech. This is a word
dictionary, not full-sentence translation. US phonetics are preferred when supplied;
some entries may only have another pronunciation or none.

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| Space | Pause/resume; next sentence after a practice sentence finishes |
| R | Repeat the current sentence once |
| Ctrl+↑ / Ctrl+↓ | Previous / next sentence |
| Esc | Stop |
| Ctrl+M | Normal / transparent subtitles |
| Ctrl+L | Always on top |
| Ctrl+E | Edit / read text |
| Ctrl++ / Ctrl+- / Ctrl+wheel | Adjust font size |
| Ctrl+V | Paste text |

## Troubleshooting

**Online neural voice unavailable:** Check your connection and choose **Retry**.
Or choose **Use Offline Voice**. The status explicitly shows Online Neural Voice
or Offline Windows Voice. Offline quality is lower and it is never the default
on a new launch. To return online, use Retry or Settings → Use online voice.
Edge TTS is an online service without an availability guarantee and its upstream
behavior may change. An unavailable preferred voice is replaced using the live US
Neural catalog when available. The app continues opening even if discovery fails.

**No offline voice:** Add English (United States) speech in Windows language settings.
**No sound:** Right-click → **Sound output** to select headphones/speakers or follow
Windows' default. Use **Test sound** to preview. The selected output is saved and
reconnected as devices change. An explicitly selected disconnected device shows an
error rather than silently playing elsewhere. Offline speech uses Windows' default.
Also check Windows output volume and the per-app volume mixer.
**Text editing:** Use Ctrl+E; reading mode prioritizes sentence selection.
**Network privacy:** Text sent for online reading/preview is transmitted to Microsoft's
speech service. Offline mode does not send the article for synthesis. Voice discovery
on startup contacts the online service but does not include your article.
**Data:** Settings and your article: `%APPDATA%\EnglishReader\settings.json`.
Audio cache: `%LOCALAPPDATA%\EnglishReader\cache`.
Logs: `%LOCALAPPDATA%\EnglishReader\logs\app.log`.
Uninstalling preserves these user files. Delete them manually if you want to remove
saved text and cached audio. Do not paste sensitive material unless you accept online processing.

## Development

Install Python 3.13 x64, then run `setup_dev.bat`. Dependencies are isolated in `.venv`.
Run `.venv\Scripts\python.exe src\main.py`. Test with `.venv\Scripts\python.exe -m pytest -q`.
Code is separated into UI, playback model, speech/audio services and persistence.
An optional `ENGLISHREADER_DATA_DIR` environment variable isolates test data.

## Build from Source

Install Inno Setup 6 or 7, then run `build.bat`. Or set `ISCC` to your compiler path.
The output folder `dist` contains the installer and portable ZIP. PyInstaller includes
Python and Qt; end users install no development tools. Source and binaries use the
licenses described in `LICENSE` and `THIRD_PARTY_NOTICES.md`.

GitHub Actions tests and builds on pushes to main. Pushing a version tag such as
`v1.0.0` builds both packages and publishes a GitHub Release automatically.
See [TEST_REPORT.md](TEST_REPORT.md) for actual verification and remaining limitations.
