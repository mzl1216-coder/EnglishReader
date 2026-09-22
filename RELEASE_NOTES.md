English Reader v1.0.3 adds protection against clipped sentence beginnings.

- Decode the complete sentence before playback and prepend 750 ms of silence in
  the same audio stream, giving Windows/headphones time to wake before speech.
- Apply the same startup protection on resume, preserving the original speech
  position and all remaining samples.
- Avoid reassigning the unchanged audio output device on every sentence.
- This mitigates device startup clipping; the reported intermittent AirPods symptom
  still needs confirmation by listening on the affected device.

Includes the v1.0.2 features:

- After manual scrolling stops for 15 seconds, return smoothly to the currently
  playing sentence without restarting speech.
- Hover words to show Chinese meanings and phonetics, with bundled business
  vocabulary, asynchronous online lookup and a local dictionary cache.

Includes the v1.0.1 improvements:

- Dark gray subtitle text, bold black current sentence, and no white glow.
- Font size is saved immediately when changed and restored on the next launch.
- Sound output selection and a Test sound command in the right-click menu.
- Saved headphone selection, refreshed audio routing when devices change, and clear
  output-device errors instead of incorrectly reporting a network problem.

- Single-click continuous reading; double-click and R repeat just one sentence.
- Andrew / Aria / Ava / Brian Neural voices with live voice discovery and fallback selection.
- Formal American preset (0.9x), voice preview, TTS-generated speed changes.
- Sentence highlighting, smooth following, manual-scroll grace period, practice mode.
- Mini Mode, always on top, themes, font sizes, automatic text and settings saving.
- Transparent subtitle window by default, hover-only thin frame and controls,
  drag handle, edge resizing and a desktop shortcut option in the installer.
- Explicit Windows offline voice fallback, retry and rotating application logs.

Download **EnglishReader-Setup-x64.exe** to install, or extract the complete
**EnglishReader-Portable-x64.zip** and run EnglishReader.exe. No Python or API key needed.
Windows 10 1809+ / Windows 11 x64. Online voices require internet. Packages are unsigned;
SmartScreen or organizational policy may flag unknown publishers.

See the repository's TEST_REPORT.md for test evidence and environmental limitations.
