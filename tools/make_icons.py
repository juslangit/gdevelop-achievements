"""Draw the example's achievement icons (128 x 128 PNG). Made here, so they are free to use like the rest of the repo."""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "example" / "assets"
S = 4  # draw 4x bigger, then shrink: smooth edges
W = 128 * S


def canvas(bg):
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, W - 1], radius=28 * S, fill=bg)
    return im, d


def save(im, name):
    im.resize((128, 128), Image.LANCZOS).save(OUT / name)


def p(*pts):
    return [(x * S, y * S) for x, y in pts]


WHITE = (255, 255, 255, 255)

im, d = canvas((76, 175, 80, 255))          # first step: a footprint
d.ellipse(p((42, 50), (86, 108)), fill=WHITE)
for x, y, r in [(40, 34, 8), (54, 26, 8), (68, 24, 8), (82, 30, 7), (92, 42, 6)]:
    d.ellipse(p((x - r, y - r), (x + r, y + r)), fill=WHITE)
save(im, "icon_first_step.png")

im, d = canvas((33, 150, 243, 255))         # jumper: an up arrow over a line
d.polygon(p((64, 18), (100, 58), (78, 58), (78, 92), (50, 92), (50, 58), (28, 58)), fill=WHITE)
d.rounded_rectangle(p((26, 100), (102, 110)), radius=5 * S, fill=WHITE)
save(im, "icon_jumper.png")

im, d = canvas((255, 160, 0, 255))          # coin hunter: a coin
d.ellipse(p((24, 24), (104, 104)), fill=(255, 224, 120, 255))
d.ellipse(p((36, 36), (92, 92)), outline=(200, 120, 0, 255), width=6 * S)
d.rounded_rectangle(p((58, 44), (70, 84)), radius=4 * S, fill=(200, 120, 0, 255))
save(im, "icon_coin_hunter.png")

im, d = canvas((156, 39, 176, 255))         # patience: an hourglass
d.rounded_rectangle(p((34, 20), (94, 30)), radius=4 * S, fill=WHITE)
d.rounded_rectangle(p((34, 98), (94, 108)), radius=4 * S, fill=WHITE)
d.polygon(p((40, 32), (88, 32), (68, 64), (88, 96), (40, 96), (60, 64)), fill=WHITE)
d.polygon(p((50, 88), (78, 88), (64, 72)), fill=(156, 39, 176, 255))
save(im, "icon_patience.png")

im, d = canvas((244, 67, 54, 255))          # completionist: a crown
d.polygon(p((24, 92), (24, 40), (46, 62), (64, 30), (82, 62), (104, 40), (104, 92)), fill=WHITE)
d.rounded_rectangle(p((24, 96), (104, 106)), radius=4 * S, fill=WHITE)
save(im, "icon_completionist.png")
print("icons:", sorted(f.name for f in OUT.glob("icon_*.png")))
