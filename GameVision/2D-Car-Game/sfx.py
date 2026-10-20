"""Sound effects: looping engine hum and a crash. Generated with numpy, no files."""
import numpy as np

from synth import ensure_mixer, time_axis, to_sound

_engine = None
_crash = None
_enabled = True
_engine_on = False


def _build_engine(sr):
    n = int(2.0 * sr)                         # 2 s * 70 Hz = 140 whole cycles -> seamless loop
    t = time_axis(n, sr)
    rumble = 1.0 + 0.08 * np.sin(2 * np.pi * 3.0 * t)
    phase = 2 * np.pi * 70.0 * t
    wave = sum(np.sin(k * phase) / k ** 1.1 for k in range(1, 10)) * 0.35 * rumble
    rng = np.random.default_rng(5)
    noise = np.convolve(rng.normal(0, 1, n), np.ones(10) / 10, mode="same") * 0.18
    return wave + noise


def _build_crash(sr):
    n = int(0.9 * sr)
    t = time_axis(n, sr)
    rng = np.random.default_rng(9)
    crunch = rng.uniform(-1, 1, n) * np.exp(-t * 7)
    thud = np.sin(2 * np.pi * np.cumsum(130 * np.exp(-t * 6) + 35) / sr) * np.exp(-t * 5)
    glass = np.diff(rng.uniform(-1, 1, n), prepend=0.0) * np.exp(-t * 14) * 0.6
    return 0.55 * crunch + 0.9 * thud + 0.35 * glass


def init():
    """Build the sounds (call once after pygame.init)."""
    global _engine, _crash
    cfg = ensure_mixer()
    if cfg is None:
        return
    sr, channels = cfg
    _engine = to_sound(_build_engine(sr), channels)
    _engine.set_volume(0.20)
    _crash = to_sound(_build_crash(sr), channels)
    _crash.set_volume(0.8)


def set_enabled(on):
    global _enabled
    _enabled = bool(on)
    if not _enabled:
        engine_off()


def engine_on():
    """Idempotent - safe to call every frame."""
    global _engine_on
    if _enabled and _engine is not None and not _engine_on:
        _engine.play(loops=-1)
        _engine_on = True


def engine_off():
    global _engine_on
    if _engine is not None and _engine_on:
        _engine.stop()
    _engine_on = False


def crash():
    if _enabled and _crash is not None:
        _crash.play()
