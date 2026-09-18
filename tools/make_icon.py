"""Build the original geometric reading + sound application icon."""
from pathlib import Path
from PIL import Image, ImageDraw

target = Path(__file__).resolve().parents[1] / 'assets' / 'icons'
target.mkdir(parents=True, exist_ok=True)
im = Image.new('RGBA', (256, 256))
d = ImageDraw.Draw(im)
d.rounded_rectangle((8, 8, 248, 248), radius=52, fill='#24496c')
d.rounded_rectangle((48, 48, 146, 205), radius=12, fill='#f4f8fb')
d.rounded_rectangle((61, 175, 142, 196), radius=5, fill='#bdd1e1')
d.line((70, 142, 94, 75, 117, 142), fill='#24496c', width=11)
d.line((81, 116, 107, 116), fill='#24496c', width=9)
d.polygon([(150, 109), (166, 109), (184, 93), (184, 162), (166, 147), (150, 147)], fill='#72ded2')
d.arc((167, 88, 213, 169), -66, 66, fill='#72ded2', width=8)
d.arc((164, 69, 237, 187), -57, 57, fill='#72ded2', width=7)
im.save(target / 'app.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
im.save(target / 'app.png')
