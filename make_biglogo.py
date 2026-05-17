"""
Same flat circular orbit, just upscaled canvas and a much larger ASE logo.
"""

import os
import math
import numpy as np
from PIL import Image
from scipy import ndimage

# ============================================================
# KNOBS
# ============================================================
UPLOADS  = "/mnt/user-data/uploads"
OUT_DIR  = "/mnt/user-data/outputs"
OUT_NAME = "ase_flags_rotation_slow.gif"
LOGO_FILE = "1778935316071_image.png"   # newer logo

CANVAS_SIZE  = 1600
LOGO_WIDTH   = 560

FLAG_BOX_W   = 170
FLAG_BOX_H   = 115

ORBIT_RADIUS = 620

N_FRAMES     = 60
FRAME_MS     = 320                      # ~19s per full rotation
DIRECTION    = +1

KEY = (255, 0, 255)
# ============================================================


def _smart_crop(cell_rgba, threshold=30):
    """
    Crop background black from a cell while keeping intentional dark stripes.

    Default behavior: tight crop to the bright bounding box.
    Exception: if one margin is *substantially* dark (≥ ~25% of the bright
    extent) AND the opposite margin is much smaller, treat the dark margin
    as a flag stripe (e.g. Germany's black band) and extend the bbox there.
    A near-zero margin on the opposite side doesn't trigger this — that just
    means the bright content sits flush with the cell edge, not that there's
    a dark stripe.
    """
    arr = np.array(cell_rgba)
    H, W = arr.shape[:2]
    bright = arr[..., :3].sum(axis=2) > threshold
    if not bright.any():
        return cell_rgba

    ys, xs = np.where(bright)
    yt, yb = int(ys.min()), int(ys.max()) + 1
    xl, xr = int(xs.min()), int(xs.max()) + 1

    top_m, bot_m   = yt,       H - yb
    left_m, right_m = xl,      W - xr
    bright_h = yb - yt
    bright_w = xr - xl

    def is_stripe(big, small, bright_extent):
        # Big enough to be a real stripe AND notably larger than the opposite side.
        return big > max(15, bright_extent * 0.25) and big > small * 3 + 5

    if is_stripe(top_m, bot_m, bright_h):
        yt = max(0, bot_m)
    elif is_stripe(bot_m, top_m, bright_h):
        yb = min(H, H - top_m)

    if is_stripe(left_m, right_m, bright_w):
        xl = max(0, right_m)
    elif is_stripe(right_m, left_m, bright_w):
        xr = min(W, W - left_m)

    return cell_rgba.crop((xl, yt, xr, yb))


def _runs(mask, value):
    """Return list of [start, end) runs of cells equal to `value` in `mask`."""
    segs, in_s, s = [], False, 0
    for i, v in enumerate(mask):
        if v == value and not in_s:
            s, in_s = i, True
        elif v != value and in_s:
            segs.append((s, i)); in_s = False
    if in_s:
        segs.append((s, len(mask)))
    return segs


def extract_flags_from_grid(path, n_rows=4, n_cols=4):
    """
    Extract flags by detecting the regular grid structure.

    Treating black as background fails for flags that contain large black
    regions (e.g. the German flag's top stripe). Instead, we:
      1. Find vertical dark bands → column boundaries (works globally).
      2. Inside each column band, find the per-column row segments
         (gaps between rows can be hidden by a tall flag in another column,
         so per-column detection is essential).
      3. Union the per-column row segments → true row extents that include
         dark stripes on the inside of the flag.
      4. The flag at (r, c) is the full rectangular cell defined by these
         extents — no further cropping, so dark interior stripes survive.
    """
    grid = np.array(Image.open(path).convert("RGB"))
    H, W = grid.shape[:2]

    # 1. Column gaps (global) — vertical bands where the entire column is dark.
    col_max = grid.max(axis=(0, 2))
    col_segs = _runs(col_max >= 30, True)
    # Keep the n_cols widest segments
    col_segs = sorted(col_segs, key=lambda s: -(s[1] - s[0]))[:n_cols]
    col_segs.sort(key=lambda s: s[0])
    assert len(col_segs) == n_cols, f"Found {len(col_segs)} cols, expected {n_cols}"

    # 2. Per-column row detection.
    per_col_rows = []
    for x0, x1 in col_segs:
        band = grid[:, x0:x1]
        bright = (band.sum(axis=2) > 30).any(axis=1)
        segs = _runs(bright, True)
        segs = sorted(segs, key=lambda s: -(s[1] - s[0]))[:n_rows]
        segs.sort(key=lambda s: s[0])
        per_col_rows.append(segs)

    # 3. For each cell (r, c), define its y-range as the union row extent
    #    (so dark stripes survive), clipped by the per-column boundaries of
    #    the previous and next row in that column (so we never bleed into
    #    an adjacent flag).
    H = grid.shape[0]
    union_extents = []
    for r in range(n_rows):
        starts = [per_col_rows[c][r][0] for c in range(n_cols)]
        ends   = [per_col_rows[c][r][1] for c in range(n_cols)]
        union_extents.append((min(starts), max(ends)))

    # 4. Build flags from the clipped cells, then smart-crop residual padding.
    flags = []
    for r in range(n_rows):
        u_start, u_end = union_extents[r]
        for c in range(n_cols):
            cx0, cx1 = col_segs[c]
            top_clip = per_col_rows[c][r - 1][1] if r > 0 else 0
            bot_clip = per_col_rows[c][r + 1][0] if r < n_rows - 1 else H
            y0 = max(top_clip, u_start)
            y1 = min(bot_clip, u_end)
            cell = grid[y0:y1, cx0:cx1]
            img = Image.fromarray(cell).convert("RGBA")
            flags.append(_smart_crop(img))
    return flags


def load_logo_transparent(path):
    """
    Load logo and flatten to a single solid color with a hard alpha mask.

    Why flatten: GIF transparency is binary and the palette is shared with the
    flags, so smooth anti-aliasing on a dark-blue logo would get quantized into
    noisy mid-tone pixels. By forcing every non-background pixel to one solid
    color, the logo collapses to just two palette entries (color + transparent)
    and renders crisply.
    """
    rgb = np.array(Image.open(path).convert("RGB"))
    mask = rgb.sum(axis=2) > 25

    # Average the colored pixels to pick a representative dark-blue
    if mask.any():
        avg = rgb[mask].mean(axis=0).astype(np.uint8)
    else:
        avg = np.array([0, 0, 120], dtype=np.uint8)  # fallback navy

    out = np.zeros((*rgb.shape[:2], 4), dtype=np.uint8)
    out[mask, 0] = avg[0]
    out[mask, 1] = avg[1]
    out[mask, 2] = avg[2]
    out[mask, 3] = 255

    img = Image.fromarray(out, "RGBA")
    return img.crop(img.getbbox())


def fit_into_box(rgba_img, box_w, box_h):
    w, h = rgba_img.size
    scale = min(box_w / w, box_h / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    resized = rgba_img.resize((nw, nh), Image.LANCZOS)
    box = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    box.paste(resized, ((box_w - nw) // 2, (box_h - nh) // 2), resized)
    return box


def to_gif_frame(rgba, key=KEY):
    arr = np.array(rgba)
    mask = arr[..., 3] < 128
    rgb = arr[..., :3].copy()
    rgb[mask] = key
    flat = Image.fromarray(rgb, "RGB").convert(
        "P", palette=Image.ADAPTIVE, colors=255, dither=Image.NONE
    )
    pal = flat.getpalette()
    triples = [(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]
    dists = [(t[0]-key[0])**2 + (t[1]-key[1])**2 + (t[2]-key[2])**2
             for t in triples]
    flat.info["transparency"] = int(np.argmin(dists))
    return flat


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    flags = extract_flags_from_grid(f"{UPLOADS}/1778870292404_image.png")
    logo  = load_logo_transparent(f"{UPLOADS}/{LOGO_FILE}")
    print(f"Logo source size: {logo.size}")

    tiles = [fit_into_box(f, FLAG_BOX_W, FLAG_BOX_H) for f in flags]
    lw, lh = logo.size
    logo_r = logo.resize(
        (LOGO_WIDTH, int(lh * LOGO_WIDTH / lw)), Image.LANCZOS
    )
    print(f"Logo render size: {logo_r.size}")

    center = CANVAS_SIZE // 2
    n = len(tiles)
    frames = []

    for k in range(N_FRAMES):
        canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
        base = DIRECTION * 2 * math.pi * k / N_FRAMES

        for i, tile in enumerate(tiles):
            theta = base + 2 * math.pi * i / n
            cx = center + ORBIT_RADIUS * math.cos(theta)
            cy = center + ORBIT_RADIUS * math.sin(theta)
            canvas.alpha_composite(
                tile,
                (int(cx - FLAG_BOX_W / 2), int(cy - FLAG_BOX_H / 2)),
            )

        canvas.alpha_composite(
            logo_r,
            (center - logo_r.size[0] // 2, center - logo_r.size[1] // 2),
        )
        frames.append(to_gif_frame(canvas))

    out = os.path.join(OUT_DIR, OUT_NAME)
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_MS,
        loop=0,
        disposal=2,
        transparency=frames[0].info["transparency"],
        optimize=False,
    )
    print(f"Saved {out}  ({CANVAS_SIZE}x{CANVAS_SIZE}, "
          f"{N_FRAMES} frames, {os.path.getsize(out)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
