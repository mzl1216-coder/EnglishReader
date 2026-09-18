import os
from pathlib import Path
import shutil
import subprocess
import sys
import importlib.metadata

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
subprocess.run([sys.executable, 'tools/make_icon.py'], check=True)
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir',
                '--name', 'EnglishReader', '--icon', 'assets/icons/app.ico', '--add-data', 'assets;assets',
                '--add-data', 'LICENSE;.', '--add-data', 'THIRD_PARTY_NOTICES.md;.',
                '--copy-metadata', 'edge-tts', '--copy-metadata', 'PySide6', 'src/main.py'], check=True)
shutil.copy2('README.md', 'dist/EnglishReader/README.md')
shutil.copy2('LICENSE', 'dist/EnglishReader/LICENSE')
shutil.copy2('THIRD_PARTY_NOTICES.md', 'dist/EnglishReader/THIRD_PARTY_NOTICES.md')
licenses = ROOT / 'dist/EnglishReader/_internal/licenses'
shutil.copytree(ROOT / 'assets/licenses', licenses, dirs_exist_ok=True)
for distribution in importlib.metadata.distributions():
    name = distribution.metadata['Name']
    for file in distribution.files or []:
        if any(part.lower().startswith(('license', 'copying', 'notice')) for part in file.parts) and str(file).lower().endswith(('.txt', '.md', 'license', 'copying', 'notice')):
            source = Path(distribution.locate_file(file))
            if source.is_file():
                destination = licenses / name / Path(str(file)).name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.exists():
    shutil.copy2(python_license, licenses / 'Python-LICENSE.txt')
shutil.make_archive('dist/EnglishReader-Portable-x64', 'zip', 'dist/EnglishReader')
compiler = os.environ.get('ISCC') or shutil.which('ISCC')
if not compiler:
    for path in [Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Inno Setup 6/ISCC.exe',
                 Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Inno Setup 7/ISCC.exe',
                 ROOT.parent / '.tools/inno/ISCC.exe']:
        if path.exists():
            compiler = str(path)
            break
if not compiler:
    raise SystemExit('Portable ZIP built. Install Inno Setup 6/7 or set ISCC to ISCC.exe to build the installer.')
subprocess.run([compiler, 'installer/EnglishReader.iss'], check=True)
