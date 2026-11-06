"""Touch Grass plugin icon: pixel grass, blue sky, a corner of sun.
16x16 grid so it still reads at favicon size, scaled 64x to 1024px."""
import math, sys
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "icon.png"
N, SCALE = 16, 64
SKY = [(51, 148, 253), (92, 186, 253), (148, 214, 254)]
SUN, SUN_HI, RAY = (255, 204, 48), (255, 242, 170), (255, 222, 96)
G_DARK, G_MID, G_LITE, G_TIP = (30, 104, 50), (56, 152, 60), (96, 190, 68), (164, 228, 96)

im = Image.new("RGB", (N, N))
px = im.load()
for y in range(N):
    for x in range(N):
        band = 0 if y < 5 else 1 if y < 9 else 2
        if y in (5, 9) and x % 2:      # dithered seam between bands
            band -= 1
        px[x, y] = SKY[band]

for y in range(N):                      # sun: quarter disc tucked in the top-right corner
    for x in range(N):
        r = math.hypot(x + 0.5 - N, y + 0.5)
        if r <= 5.6:
            px[x, y] = SUN_HI if r <= 3.4 else SUN
for x, y in [(8, 1), (9, 1), (10, 5), (9, 6), (14, 7), (14, 8)]:   # three short rays
    px[x, y] = RAY

GROUND = 12                             # grass: blades of mixed height over a solid field
heights = [2, 4, 1, 3, 5, 2, 0, 3, 1, 4, 2, 5, 1, 3, 2, 1]
for x, h in enumerate(heights):
    for k in range(1, h + 1):
        px[x, GROUND - k] = G_MID
    if h:
        px[x, GROUND - h] = G_TIP if h >= 3 else G_LITE
for y in range(GROUND, N):
    for x in range(N):
        px[x, y] = G_MID
for x in range(N):
    px[x, GROUND] = G_LITE if x % 3 == 0 else G_MID
    px[x, 14] = G_DARK if x % 2 else G_MID
    px[x, 15] = G_DARK

im.resize((N * SCALE, N * SCALE), Image.NEAREST).save(OUT, optimize=True)
print("saved", OUT)
