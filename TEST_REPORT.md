# Verification report

## v1.0.1 update

- 22 automated tests pass, including immediate font-size saving and restoration
  after closing/reopening, black current-sentence text, removed subtitle shadow,
  saved sound-output selection, and clear errors for disconnected outputs.
- AirPods playback diagnostic reported nonzero Windows output levels. The user
  subsequently confirmed that sound was audible again.
- Online playback now refreshes the selected/default output device and logs the
  output route without logging the article text.

## v1.0.0 verification

Dates: 2026-09-18 and 2026-09-20. Development host: Windows 11 x64, Python 3.13.8, PySide6 6.11.2.

## Passed

- 18 pytest / pytest-qt tests against actual Qt widgets and a deterministic speech
  transport: 20-sentence document, click sentence 5 and advance, double-click sentence
  10 only, repeat double-click, rapid jump to sentence 3, stale completion/error/audio
  rejection, practice Space/R, pause during download/playback, speed applied to the
  next sentence, preview position and paused-state restoration, mode switching,
  background highlighting, smooth scrolling/manual-scroll suppression, voice fallback,
  text/settings recovery, malformed settings, literal editing keys, and resizing.
- Transparent frameless subtitles: hover-only chrome, transparent current-sentence
  highlight, return to normal window, and window destruction without stale event filters.
- Actual Edge TTS voice discovery: 17 en-US voices returned.
- Actual synthesis: AndrewMultilingualNeural, AriaNeural, AvaMultilingualNeural,
  BrianMultilingualNeural all produced nonempty MP3 audio at -10% rate.
- Actual Qt MP3 playback reached EndOfMedia successfully.
- Actual Windows SAPI offline speech reached its completed state successfully.
- Complete window + background Neural worker + playback integration: sentence 5
  continuous advance, jump to 10, interrupt to 3, one-sentence completion, preview
  restoration, then offline sentence completion. This passed when run independently;
  an earlier attempt overlapped installer testing and was interrupted, so is not counted.
- Source application launched and closed successfully.
- Normal, dark and Mini Mode window renders inspected.
- PyInstaller bundle and Inno Setup installer compiled successfully locally.

## Packaging and publishing validation

- Local installer installation, application launch and uninstall all returned exit 0.
- Extracted portable application launched successfully with Python removed from PATH.
- Both installed and portable smoke reports confirmed a visible Qt window and a
  frozen bundled Python runtime.
- Initial GitHub Actions Windows build, 17 tests and bundled-runtime check passed:
  https://github.com/mzl1216-coder/EnglishReader/actions/runs/35328095025
- The cloud-built portable ZIP was downloaded and successfully launched locally.
- A local build issue was traced to an incompatible ICU DLL supplied by another
  tool on PATH. The build script now restricts DLL search paths; corrected local
  installer and portable packages passed the installation/runtime checks above.
- Final transparent-subtitle build: 18 tests, installer build, portable build,
  installation/launch/uninstall and portable launch all passed on GitHub's Windows runner:
  https://github.com/mzl1216-coder/EnglishReader/actions/runs/35480797205
- The final locally built transparent portable package also passed independent launch.
- Pixel-alpha verification confirmed the idle subtitle surface has alpha 1/255
  (visually transparent, while retaining reliable mouse interaction); hover chrome
  appears without changing text layout.
- v1.0.0 tag workflow passed all 18 tests, built both packages, tested installation,
  portable launch and uninstall, and automatically published the release:
  https://github.com/mzl1216-coder/EnglishReader/actions/runs/35481007947
- Both release assets were downloaded from GitHub; SHA256 hashes matched the
  published digests. The downloaded portable passed a local frozen-runtime/window
  smoke test with Python removed from PATH.
- Installed locally to `C:\Program Files\English Reader` after the user's Windows
  UAC confirmation. The desktop shortcut was verified at
  `C:\Users\Public\Desktop\English Reader.lnk`, targeting the installed executable.
  The installed application passed its smoke test and was opened for normal use.

Release: https://github.com/mzl1216-coder/EnglishReader/releases/tag/v1.0.0

## Limits of the evidence

- Network failure/recovery is tested by injecting speech-service failures and stale
  responses; the host's physical network adapter was not disabled.
- Actual voice synthesis and playback completion are verified. These checks cannot
  objectively certify a voice's perceived naturalness; Preview lets the user compare.
- A genuinely clean Windows machine without Python has not been provisioned here.
  Bundled-runtime tests with Python removed from PATH and GitHub hosted-runner smoke
  tests are useful checks, but do not substitute for that separate machine test.
- Sentence splitting is heuristic. Titles, decimal numbers and common initialisms
  are handled; ambiguous abbreviations at sentence boundaries can still need editing.
- Binaries are unsigned. Edge's online service availability and Windows installed
  offline voices vary between machines. Offline preview restores sentence position;
  the current offline sentence may restart because SAPI does not expose an audio offset.
