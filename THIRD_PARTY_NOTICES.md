# Third-party notices

English Reader's application code and original geometric icon use the MIT license.
Bundled dependencies retain their respective licenses. This application is not
affiliated with or endorsed by Microsoft or The Qt Company.

- Python: PSF License, https://docs.python.org/3/license.html
- PySide6 / Qt: LGPL v3 (and applicable third-party module licenses),
  https://doc.qt.io/qtforpython-6/licenses.html and https://www.qt.io/licensing/open-source-lgpl-obligations
- Qt source: https://download.qt.io/official_releases/qt/6.11/
- PySide source: https://download.qt.io/official_releases/QtForPython/pyside6/
- edge-tts: LGPL v3, https://github.com/rany2/edge-tts
- aiohttp: Apache 2.0 / MIT, https://github.com/aio-libs/aiohttp
- PyInstaller bootloader: GPL with distribution exception, https://pyinstaller.org/en/stable/license.html

Qt is dynamically linked. The portable distribution keeps shared libraries under
`_internal`; users may replace compatible LGPL libraries and debug modifications
as permitted by their licenses. Additional dependency license texts are bundled
in `_internal/licenses` by the build script. No Microsoft voices are redistributed:
online audio is requested from Microsoft's service, and offline speech uses voices
already installed on Windows.
