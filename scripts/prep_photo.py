"""
Prepare the dp (a flat illustration) for clean ASCII conversion:
  1. remove the background (rembg) so the subject is isolated
  2. bilateral-smooth away the paper texture (otherwise skin turns to `::::`
     noise and the eyes drown in it) while keeping the drawn lines sharp
  3. crop a square around the head and collar so clothing doesn't dominate
  4. boost local contrast (CLAHE) and stretch tones so hair stays dark
     while the face keeps its features
  5. darken thin strokes (difference-of-gaussians) so glasses and eyelids
     survive the downscale, then composite onto white

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py <input.png> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "image.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = 0.6     # how hard drawn lines are pushed toward black


def crop_bust(gray, smooth, alpha):
    """Square crop around the head and collar.

    A full-length photo's box is mostly clothing. Stretching tones across that
    box blows the face out to white and leaves a shirt silhouette. Crop to the
    head first, then stretch.
    """
    subject = alpha > 20
    row_w = subject.sum(axis=1)
    if row_w.max() == 0:
        raise SystemExit("no subject found after background removal")
    present = np.where(row_w > 8)[0]
    top = int(present.min())
    max_w = int(row_w.max())
    shoulder_y = int(present.max())
    for y in range(top, subject.shape[0]):
        if row_w[y] > max_w * 0.45:
            shoulder_y = y
            break
    head = subject[top:shoulder_y]
    xs = np.where(head.any(axis=0))[0] if head.size else np.array([], dtype=int)
    if len(xs) == 0:
        xs = np.where(subject.any(axis=0))[0]
    x0, x1 = int(xs.min()), int(xs.max())
    head_w = x1 - x0 + 1
    side = int(max(head_w * 1.55, (shoulder_y - top) + head_w * 0.35))
    cx = (x0 + x1) // 2
    x_left = cx - side // 2
    y_top = top - int(side * 0.06)

    h, w = alpha.shape
    canvas_g = np.full((side, side), 255, np.uint8)
    canvas_s = np.full((side, side), 255, np.uint8)
    canvas_a = np.zeros((side, side), np.uint8)

    sx0, sy0 = max(x_left, 0), max(y_top, 0)
    sx1, sy1 = min(x_left + side, w), min(y_top + side, h)
    dx0, dy0 = sx0 - x_left, sy0 - y_top
    dh, dw = sy1 - sy0, sx1 - sx0
    canvas_g[dy0:dy0 + dh, dx0:dx0 + dw] = gray[sy0:sy1, sx0:sx1]
    canvas_s[dy0:dy0 + dh, dx0:dx0 + dw] = smooth[sy0:sy1, sx0:sx1]
    canvas_a[dy0:dy0 + dh, dx0:dx0 + dw] = alpha[sy0:sy1, sx0:sx1]
    return canvas_g, canvas_s, canvas_a


# 1. cut out the subject
cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])                 # 0 = background
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. smooth texture, keep edges
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. head-and-shoulders crop before tone stretch
gray, smooth, alpha = crop_bust(gray, smooth, alpha)

# 4. local contrast on the bust, then tone stretch over the subject only.
#    A flat ID photo otherwise washes the face out to blank ASCII.
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
smooth = clahe.apply(smooth)
subject_px = smooth[alpha > 128]
lo, hi = np.percentile(subject_px, [2, 97])
tone = np.clip((smooth.astype(np.float32) - lo) / max(hi - lo, 1), 0, 1)

# 5. dark-on-light ridges -> darken
fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

# 6. paste onto white (feathered a hair to avoid a halo)
mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = out * mask + 255.0 * (1.0 - mask)

Image.fromarray(out.astype(np.uint8), mode="L").save(OUT)
print("wrote", OUT, out.shape)
