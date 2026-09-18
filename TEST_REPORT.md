# Verification report

Date: 2026-09-18. Development host: Windows 11 x64, Python 3.13.8, PySide6 6.11.2.

## Passed

- 17 pytest / pytest-qt tests against actual Qt widgets and a deterministic speech
  transport: 20-sentence document, click sentence 5 and advance, double-click sentence
  10 only, repeat double-click, rapid jump to sentence 3, stale completion/error/audio
  rejection, practice Space/R, pause during download/playback, speed applied to the
  next sentence, preview position and paused-state restoration, mode switching,
  background highlighting, smooth scrolling/manual-scroll suppression, voice fallback,
  text/settings recovery, malformed settings, literal editing keys, and resizing.
- Actual Edge TTS voice discovery: 17 en-US voices returned.
- Actual synthesis: AndrewMultilingualNeural, AriaNeural, AvaMultilingualNeural,
  BrianMultilingualNeural all produced nonempty MP3 audio at -10% rate.
- Actual Qt MP3 playback reached EndOfMedia successfully.
- Actual Windows SAPI offline speech reached its completed state successfully.
- Source application launched and closed successfully.
- Normal, dark and Mini Mode window renders inspected.
- PyInstaller bundle and Inno Setup installer compiled successfully locally.

## Packaging and publishing validation

Installer execution, final bundled-runtime checks and GitHub Actions results are
recorded here after they complete. The initial source commit does not assert that
a release has already been published.

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
