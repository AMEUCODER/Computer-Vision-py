"""
Core outpainting logic (no UI here).

Extends the plain / white studio background of a picture to a target resolution.

How it works
------------
1. Only the outermost pixels of the photo are used as the "known" background, so a
   product sitting close to the edge can never leak into the new area.
2. A smooth background field is solved over the new area (harmonic / Laplace fill on a
   small grid): colors and gradients flow outward from the edge without streaks.
3. The tiny mismatch left along the photo edge is carried outward and faded away, so
   the join between the original and the new area is invisible.
4. Grain matching plus dithering keeps smooth gradients free of banding.

Only the new area is computed (in cache-friendly chunks) and the original pixels are
copied untouched.
"""
import math
import threading
from pathlib import Path

import cv2
import numpy as np

ANCHORS = ("center", "top", "bottom", "left", "right")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


# ----------------------------------------------------------------------------- I/O
def read_image(path):
    """Read an image from disk (works with Arabic / non-ASCII paths on Windows)."""
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def write_image(path, img):
    """Write an image to disk (works with Arabic / non-ASCII paths on Windows)."""
    path = Path(path)
    ext = path.suffix.lower() or ".png"
    if ext in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, 98]
        if hasattr(cv2, "IMWRITE_JPEG_SAMPLING_FACTOR"):      # keep full color detail
            params += [cv2.IMWRITE_JPEG_SAMPLING_FACTOR,
                       getattr(cv2, "IMWRITE_JPEG_SAMPLING_FACTOR_444", 0x111111)]
    elif ext == ".png":
        params = [cv2.IMWRITE_PNG_COMPRESSION, 3]             # much faster than the default
    else:
        params = []
    ok, buf = cv2.imencode(ext, img, params)
    if not ok and params:
        ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise ValueError(f"Could not encode image as {ext}")
    buf.tofile(str(path))


# ------------------------------------------------------------------- harmonic solver
def _relax(u, known, V, sweeps):
    """Jacobi sweeps of the Laplace equation. Known cells stay fixed, outer border is Neumann."""
    h, w = known.shape
    p = np.empty((h + 2, w + 2, 3), np.float32)
    p[1:-1, 1:-1] = u
    kn = known[..., None]
    for _ in range(sweeps):
        p[0, 1:-1] = p[1, 1:-1]
        p[-1, 1:-1] = p[-2, 1:-1]
        p[1:-1, 0] = p[1:-1, 1]
        p[1:-1, -1] = p[1:-1, -2]
        avg = p[:-2, 1:-1] + p[2:, 1:-1]
        avg += p[1:-1, :-2]
        avg += p[1:-1, 2:]
        avg *= 0.25
        np.copyto(avg, V, where=kn)
        p[1:-1, 1:-1] = avg
    return p[1:-1, 1:-1].copy()


def _harmonic_fill(V, known, sweeps=30):
    """Smoothly fill the unknown cells of V from the known ones (coarse-to-fine solve)."""
    levels = [(V, known)]
    while min(levels[-1][1].shape) > 10:
        Vf, kf = levels[-1]
        ph, pw = kf.shape[0] % 2, kf.shape[1] % 2
        if ph or pw:
            Vf = np.pad(Vf, ((0, ph), (0, pw), (0, 0)), mode="edge")
            kf = np.pad(kf, ((0, ph), (0, pw)), mode="edge")
        kk = kf.astype(np.float32)
        s = Vf * kk[..., None]
        S = s[0::2, 0::2] + s[1::2, 0::2] + s[0::2, 1::2] + s[1::2, 1::2]
        K = kk[0::2, 0::2] + kk[1::2, 0::2] + kk[0::2, 1::2] + kk[1::2, 1::2]
        kc = K > 0
        Vc = np.where(kc[..., None], S / np.maximum(K, 1)[..., None], 0).astype(np.float32)
        levels.append((Vc, kc))

    u = None
    for lvl in range(len(levels) - 1, -1, -1):
        Vl, kl = levels[lvl]
        if u is None:
            mean = Vl[kl].mean(axis=0) if kl.any() else np.zeros(3, np.float32)
            u = np.where(kl[..., None], Vl, mean).astype(np.float32)
            n = 300
        else:
            u = cv2.resize(u, (kl.shape[1], kl.shape[0]), interpolation=cv2.INTER_LINEAR)
            n = sweeps
        u = _relax(u, kl, Vl, n)
    return u


def _robust_smooth(a, sigma_space, sigma_color):
    """Edge-preserving smoothing of a profile a (n, 3): removes blotches and grain but keeps
    real jumps (e.g. where a product touches the photo edge)."""
    n = len(a)
    sigma_space = max(1.0, min(sigma_space, n / 4.0))
    r = max(2, int(3 * sigma_space))
    pad = np.pad(a, ((r, r), (0, 0)), mode="edge")
    num = np.zeros_like(a)
    den = np.zeros((n, 1), np.float32)
    inv_c = 1.0 / (2.0 * sigma_color ** 2)
    for o in range(-r, r + 1):
        sh = pad[r + o:r + o + n]
        d2 = ((sh - a) ** 2).sum(axis=1, keepdims=True) / 3.0
        wgt = (math.exp(-o * o / (2.0 * sigma_space ** 2)) * np.exp(-d2 * inv_c)).astype(np.float32)
        num += wgt * sh
        den += wgt
    return num / den


# ----------------------------------------------------------------- background model
class _BackgroundModel:
    """Smooth model of the background around the photo, matched to the photo's outer edge."""

    def __init__(self, img, x0, y0, W, H, tau):
        h, w = img.shape[:2]
        self.x0, self.y0, self.w, self.h, self.W, self.H = x0, y0, w, h, W, H
        self.tau = tau                          # how far the smooth edge residual is carried
        self.tau_fine = max(1.0, 0.3 * tau)     # fine edge detail fades much faster

        # Thin strips along the four edges (the only pixels the model trusts)
        t = max(1, min(3, h // 4, w // 4))
        raw = {"top": img[:t].astype(np.float32).mean(axis=0),
               "bottom": img[h - t:].astype(np.float32).mean(axis=0),
               "left": img[:, :t].astype(np.float32).mean(axis=1),
               "right": img[:, w - t:].astype(np.float32).mean(axis=1)}
        # what the join must match (grain removed only)
        edge = {k: cv2.GaussianBlur(v[None], (0, 0), 1.5, borderType=cv2.BORDER_REPLICATE)[0]
                for k, v in raw.items()}
        self.noise_sigma = _noise_sigma(img)

        # Coarse grid aligned with the photo: the photo covers cw x ch cells exactly
        kt = max(1.0, max(W, H) / 128.0)
        cw, ch = max(2, int(round(w / kt))), max(2, int(round(h / kt)))
        kx, ky = w / cw, h / ch
        nl, nr = math.ceil(x0 / kx - 1e-6), math.ceil((W - x0 - w) / kx - 1e-6)
        nt, nb = math.ceil(y0 / ky - 1e-6), math.ceil((H - y0 - h) / ky - 1e-6)
        gw, gh = nl + cw + nr, nt + ch + nb

        def ring(side, n, cell):               # edge profile -> n smoothed coarse cells
            c = cv2.resize(raw[side][None], (n, 1), interpolation=cv2.INTER_AREA)[0]
            return _robust_smooth(c, 20.0 / cell, 12.0)

        V = np.zeros((gh, gw, 3), np.float32)
        cnt = np.zeros((gh, gw), np.float32)
        V[nt, nl:nl + cw] += ring("top", cw, kx);               cnt[nt, nl:nl + cw] += 1
        V[nt + ch - 1, nl:nl + cw] += ring("bottom", cw, kx);   cnt[nt + ch - 1, nl:nl + cw] += 1
        V[nt:nt + ch, nl] += ring("left", ch, ky);              cnt[nt:nt + ch, nl] += 1
        V[nt:nt + ch, nl + cw - 1] += ring("right", ch, ky);    cnt[nt:nt + ch, nl + cw - 1] += 1
        known = cnt > 0                         # only the ring of cells along the photo edge
        V[known] /= cnt[known][:, None]

        u = _harmonic_fill(V, known)
        np.clip(u, V[known].min(axis=0) - 1.0, V[known].max(axis=0) + 1.0, out=u)

        # Resample the coarse solution onto a finer grid once (cubic, smooth); every band
        # is then cut out of it with a cheap linear warp.
        self.q = int(max(1, min(4, min(kx, ky) // 4)))
        q = self.q
        if q == 1:
            self.field = u
            self.f_scale = 1.0
            self.f_off = (0.5 - x0) / kx + nl - 0.5, (0.5 - y0) / ky + nt - 0.5
            self.f_mul = 1.0 / kx, 1.0 / ky
            self.flags = cv2.INTER_CUBIC
        else:
            M = np.array([[q / kx, 0.0, (0.5 * q - x0) / kx + nl - 0.5],
                          [0.0, q / ky, (0.5 * q - y0) / ky + nt - 0.5]], np.float64)
            self.field = cv2.warpAffine(u, M, (math.ceil(W / q), math.ceil(H / q)),
                                        flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                                        borderMode=cv2.BORDER_REPLICATE)
            self.flags = cv2.INTER_LINEAR

        # Residual between the real edge pixels and the model at the first new pixel
        first = {}
        if y0 > 0:
            first["top"] = self.smooth(x0, y0 - 1, x0 + w, y0)[0]
        if y0 + h < H:
            first["bottom"] = self.smooth(x0, y0 + h, x0 + w, y0 + h + 1)[0]
        if x0 > 0:
            first["left"] = self.smooth(x0 - 1, y0, x0, y0 + h)[:, 0]
        if x0 + w < W:
            first["right"] = self.smooth(x0 + w, y0, x0 + w + 1, y0 + h)[:, 0]
        # split into a smooth part (carried far) and fine detail (fades within a few px)
        self.res = {}
        for side, m1 in first.items():
            r = edge[side] - m1
            low = cv2.GaussianBlur(r[None], (0, 0), 24.0, borderType=cv2.BORDER_REPLICATE)[0]
            self.res[side] = (low, r - low)

    def smooth(self, xa, ya, xb, yb):
        """Smooth model for the canvas rectangle [xa, xb) x [ya, yb) as float32 (rows, cols, 3)."""
        if self.q == 1:
            ax, ay = self.f_mul
            cx, cy = self.f_off
            M = np.array([[ax, 0.0, ax * xa + cx], [0.0, ay, ay * ya + cy]], np.float64)
        else:
            s = 1.0 / self.q
            M = np.array([[s, 0.0, (xa + 0.5) * s - 0.5], [0.0, s, (ya + 0.5) * s - 0.5]], np.float64)
        return cv2.warpAffine(self.field, M, (xb - xa, yb - ya),
                              flags=self.flags | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REPLICATE)

    def bands(self):
        x0, y0, w, h, W, H = self.x0, self.y0, self.w, self.h, self.W, self.H
        out = []
        if y0 > 0:
            out.append(("top", 0, 0, W, y0))
        if y0 + h < H:
            out.append(("bottom", 0, y0 + h, W, H))
        if x0 > 0:
            out.append(("left", 0, y0, x0, y0 + h))
        if x0 + w < W:
            out.append(("right", x0 + w, y0, W, y0 + h))
        return out

    def render(self, side, xa, ya, xb, yb):
        """Background for a rectangle inside one band of the new area (float32, no noise yet)."""
        x0, y0, w, h = self.x0, self.y0, self.w, self.h
        out = self.smooth(xa, ya, xb, yb)

        # Only a thin zone next to the photo needs the edge residual
        reach = int(7 * self.tau) + 2
        sx0, sy0, sx1, sy1 = xa, ya, xb, yb
        if side == "top":
            sy0 = max(ya, y0 - reach)
        elif side == "bottom":
            sy1 = min(yb, y0 + h + reach)
        elif side == "left":
            sx0 = max(xa, x0 - reach)
        else:
            sx1 = min(xb, x0 + w + reach)
        if sx1 <= sx0 or sy1 <= sy0:
            return out

        xs = np.arange(sx0, sx1, dtype=np.float32)[None, :]
        ys = np.arange(sy0, sy1, dtype=np.float32)[:, None]
        dx = np.maximum(np.maximum(x0 - xs, xs - (x0 + w - 1)), 0)
        dy = np.maximum(np.maximum(y0 - ys, ys - (y0 + h - 1)), 0)
        dist = np.hypot(dx, dy) - 1.0
        decay_low = np.exp(-dist / self.tau).astype(np.float32)
        decay_fine = np.exp(-dist / self.tau_fine).astype(np.float32)

        low, fine = self.res[side]
        dst = out[sy0 - ya:sy1 - ya, sx0 - xa:sx1 - xa]
        if side in ("top", "bottom"):
            idx = np.clip(np.arange(sx0, sx1) - x0, 0, w - 1)
            dst += decay_low[..., None] * low[idx][None, :, :]
            dst += decay_fine[..., None] * fine[idx][None, :, :]
        else:
            idx = np.clip(np.arange(sy0, sy1) - y0, 0, h - 1)
            dst += decay_low[..., None] * low[idx][:, None, :]
            dst += decay_fine[..., None] * fine[idx][:, None, :]
        return out


# -------------------------------------------------------------------- grain / dither
def _noise_sigma(img):
    """Robust estimate of the grain level of the background along the photo border."""
    h, w = img.shape[:2]
    r = max(2, min(24, h // 4, w // 4))
    vals = []
    for strip in (img[:r], img[h - r:], img[:, :r], img[:, w - r:]):
        g = cv2.cvtColor(np.ascontiguousarray(strip), cv2.COLOR_BGR2GRAY).astype(np.float32)
        vals.append((g - cv2.GaussianBlur(g, (0, 0), 1.5, borderType=cv2.BORDER_REPLICATE)).ravel())
    v = np.concatenate(vals)
    mad = 1.4826 * float(np.median(np.abs(v - np.median(v))))    # ignores sparse edges / blotches
    return float(min(mad, 6.0))


_TILE_H, _TILE_W = 512, 2048
_tile = None
_tile_lock = threading.Lock()


def _noise_tile():
    """A reusable tile of soft, unit-variance noise (built once, much faster than per-pixel RNG)."""
    global _tile
    if _tile is None:
        with _tile_lock:
            if _tile is None:
                rng = np.random.default_rng(7)
                n = rng.standard_normal((_TILE_H + 8, _TILE_W + 8), dtype=np.float32)
                n = cv2.GaussianBlur(n, (0, 0), 0.5)[4:-4, 4:-4]       # photo grain is slightly soft
                _tile = np.ascontiguousarray(n / n.std())
    return _tile


def _noise_block(rows, cols, rng):
    """(rows, cols) cut-out of the noise tile at a random position (rows <= tile height)."""
    T = _noise_tile()
    oy = int(rng.integers(0, _TILE_H - rows + 1))
    parts, left = [], cols
    while left > 0:
        n = min(left, _TILE_W)
        ox = int(rng.integers(0, _TILE_W - n + 1))
        parts.append(T[oy:oy + rows, ox:ox + n])
        left -= n
    return parts[0] if len(parts) == 1 else np.concatenate(parts, axis=1)


# --------------------------------------------------------------------------- public
def _layout(w, h, width, height, anchor):
    """Scale and top-left position of the photo on the canvas."""
    scale = min(1.0, width / w, height / h)
    nw, nh = (max(1, int(w * scale)), max(1, int(h * scale))) if scale < 1.0 else (w, h)
    x0, y0 = (width - nw) // 2, (height - nh) // 2
    if anchor == "top":
        y0 = 0
    elif anchor == "bottom":
        y0 = height - nh
    elif anchor == "left":
        x0 = 0
    elif anchor == "right":
        x0 = width - nw
    return nw, nh, x0, y0


def outpaint(img, width, height, anchor="center", feather=12, grain=True):
    """Return `img` placed on a width x height canvas with the background extended.

    feather: how far (in px) the smooth part of the photo's edge colour is carried into
             the new area before it fades into the plain background.
    grain:   add noise that matches the photo's own grain (a little dither is always added).
    """
    h, w = img.shape[:2]
    nw, nh, x0, y0 = _layout(w, h, width, height, anchor)
    if (nw, nh) != (w, h):                     # never crop: shrink only if it doesn't fit
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    img = np.ascontiguousarray(img)
    if (nw, nh) == (width, height):
        return img.copy()

    canvas = np.empty((height, width, 3), np.uint8)
    canvas[y0:y0 + nh, x0:x0 + nw] = img

    model = _BackgroundModel(img, x0, y0, width, height, tau=max(1.0, 1.5 * float(feather)))
    # rounding to 8 bit already adds ~0.29 of noise; the floor keeps gradients free of banding
    sigma = np.float32(max(model.noise_sigma if grain else 0.0, 0.3))
    rng = np.random.default_rng(2024)

    for side, xa, ya, xb, yb in model.bands():
        bw = xb - xa
        step = int(min(_TILE_H, max(8, 262144 // bw)))       # small chunks stay in the CPU cache
        for y in range(ya, yb, step):
            y2 = min(y + step, yb)
            blk = model.render(side, xa, y, xb, y2)
            blk += (_noise_block(y2 - y, bw, rng) * sigma)[..., None]
            canvas[y:y2, xa:xb] = cv2.convertScaleAbs(blk)   # round + clip to 0..255
    return canvas


def edge_contact(img, width, height, anchor="center"):
    """Sides that get extended although something other than plain background touches the
    photo edge there (the missing part of such an object cannot be invented)."""
    h, w = img.shape[:2]
    nw, nh, x0, y0 = _layout(w, h, width, height, anchor)
    if (nw, nh) != (w, h):
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_BGR2GRAY).astype(np.float32)
    t = max(1, min(3, nh // 4, nw // 4))
    sides = {"top": (y0 > 0, g[:t].mean(axis=0)),
             "bottom": (y0 + nh < height, g[nh - t:].mean(axis=0)),
             "left": (x0 > 0, g[:, :t].mean(axis=1)),
             "right": (x0 + nw < width, g[:, nw - t:].mean(axis=1))}
    hit = []
    for side, (extended, prof) in sides.items():
        if not extended or len(prof) < 16:
            continue
        p = cv2.GaussianBlur(prof[None], (0, 0), 2.0, borderType=cv2.BORDER_REPLICATE)[0]
        lag = max(3, len(p) // 200)
        if np.abs(p[lag:] - p[:-lag]).max() > 30:           # a sharp, strong jump along the edge
            hit.append(side)
    return hit


def process_file(src, out_dir, width, height, anchor="center", feather=12, grain=True):
    """Outpaint one file and save it in `out_dir`. Returns the saved path."""
    src = Path(src)
    img = read_image(src)
    if img is None:
        raise ValueError("cannot read image")
    result = outpaint(img, width, height, anchor, feather, grain)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{src.stem}_{width}x{height}{src.suffix}"
    write_image(out_path, result)
    return out_path
