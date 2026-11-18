"""Small numpy synthesis toolkit shared by music.py and sfx.py."""
import numpy as np
import pygame


def ensure_mixer():
    """Init the mixer once. Returns (sample_rate, channels) or None if there is no audio."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        freq, _fmt, channels = pygame.mixer.get_init()
        return freq, channels
    except pygame.error:
        return None


def midi_to_freq(note):
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def time_axis(n, sr):
    return np.arange(n) / sr


def saw(freq, n, sr, harmonics=8):
    """Band-limited sawtooth (additive), so it never aliases."""
    t = time_axis(n, sr)
    top = max(1, min(harmonics, int(sr / 2 / freq)))
    out = np.zeros(n)
    for k in range(1, top + 1):
        out += np.sin(2 * np.pi * k * freq * t) / k
    return out * (2 / np.pi)


def square(freq, n, sr, harmonics=6):
    """Band-limited square wave (odd harmonics only)."""
    t = time_axis(n, sr)
    top = max(1, min(harmonics * 2, int(sr / 2 / freq)))
    out = np.zeros(n)
    for k in range(1, top + 1, 2):
        out += np.sin(2 * np.pi * k * freq * t) / k
    return out * (4 / np.pi)


def envelope(n, sr, attack=0.005, release=0.04, decay=0.0):
    """Linear attack/release, optional exponential decay (for plucks)."""
    env = np.ones(n)
    a = max(1, min(n // 2, int(attack * sr)))
    r = max(1, min(n // 2, int(release * sr)))
    env[:a] = np.linspace(0.0, 1.0, a)
    env[-r:] *= np.linspace(1.0, 0.0, r)
    if decay:
        env *= np.exp(-time_axis(n, sr) * decay)
    return env


def to_sound(data, channels):
    """float array (n,) or (n, 2) in [-1, 1] -> pygame Sound that matches the mixer."""
    data = np.clip(np.asarray(data, dtype=np.float64), -1.0, 1.0)
    if data.ndim == 1:
        data = np.column_stack([data, data])
    if channels == 1:
        pcm = (data.mean(axis=1) * 32767).astype(np.int16)
    else:
        pcm = (data[:, :2] * 32767).astype(np.int16)
        if channels > 2:
            pcm = np.repeat(pcm[:, :1], channels, axis=1)
    return pygame.sndarray.make_sound(np.ascontiguousarray(pcm))
