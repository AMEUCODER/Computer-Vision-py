"""
music.py - procedural "night drive" theme for the car game (numpy + pygame only).

A 16-bar synthwave loop (32 s @ 120 BPM): four-on-the-floor kick with sidechain
"pumping", offbeat hats, claps, a saw bass, a warm detuned pad, a plucky stereo
arpeggio and a lead melody with ping-pong delay. Everything is generated in code.

The track is built in a background thread (so the menu never freezes) and loops
seamlessly because every note/effect wraps around the end of the buffer.

Usage:
    import music
    music.preload()        # optional: start building early (game.py does this)
    music.toggle_music()   # music button -> returns True when playing
    music.update()         # call once per frame (starts playback when the build is done)
    music.is_music_on() / music.is_loading() / music.set_volume(0.6) / music.stop_music()
"""
import threading
from functools import lru_cache

import numpy as np

from synth import (
    ensure_mixer, midi_to_freq, time_axis, saw, square, envelope, to_sound,
)

# ------------------------------------------------------------------ song data
BPM = 120
BARS = 16
BASE_VOLUME = 0.55

# name -> (bass note, four arpeggio tones). Pad uses the first three tones, one octave down.
CHORDS = {
    "Am": (45, [60, 64, 69, 72]),
    "F":  (41, [60, 65, 69, 72]),
    "C":  (48, [60, 64, 67, 72]),
    "G":  (43, [62, 67, 71, 74]),
    "E":  (40, [59, 64, 68, 71]),
}

# four 4-bar blocks
PROGRESSIONS = [
    ["Am", "F", "C", "G"],     # intro  (no lead)
    ["Am", "F", "C", "G"],     # verse
    ["F", "G", "Am", "C"],     # lift
    ["Am", "F", "G", "E"],     # finale, ends on E so it falls back into Am
]

# lead lines: per bar a list of (16th-step, midi note, length in 16ths)
LEAD_A = [
    [(0, 76, 3), (3, 74, 1), (4, 72, 2), (6, 74, 2), (8, 76, 4), (12, 69, 4)],
    [(0, 77, 3), (3, 76, 1), (4, 74, 2), (6, 76, 2), (8, 77, 4), (12, 72, 4)],
    [(0, 79, 3), (3, 76, 1), (4, 79, 2), (6, 81, 2), (8, 79, 4), (12, 76, 4)],
    [(0, 71, 2), (2, 74, 2), (4, 79, 4), (8, 77, 2), (10, 74, 2), (12, 71, 4)],
]
LEAD_B = [
    [(0, 72, 2), (2, 77, 2), (4, 81, 3), (7, 79, 1), (8, 77, 4), (12, 72, 2), (14, 74, 2)],
    [(0, 74, 2), (2, 79, 2), (4, 81, 3), (7, 79, 1), (8, 74, 4), (12, 71, 2), (14, 74, 2)],
    [(0, 76, 2), (2, 81, 2), (4, 84, 3), (7, 83, 1), (8, 81, 4), (12, 76, 4)],
    [(0, 79, 2), (2, 76, 2), (4, 72, 4), (8, 76, 2), (10, 79, 2), (12, 84, 4)],
]
LEAD_C = [
    LEAD_A[0],
    LEAD_A[1],
    [(0, 74, 3), (3, 79, 1), (4, 83, 2), (6, 81, 2), (8, 79, 4), (12, 74, 4)],
    [(0, 71, 2), (2, 76, 2), (4, 80, 2), (6, 83, 2), (8, 83, 2), (10, 80, 2), (12, 76, 4)],
]
LEADS = [None, LEAD_A, LEAD_B, LEAD_C]

BASS_STEPS = [0, 2, 3, 4, 6, 8, 10, 11, 12, 14]          # galloping bass rhythm
ARP_PATTERN = [0, 2, 1, 3, 2, 1, 3, 2, 0, 2, 1, 3, 2, 1, 3, 1]

# ------------------------------------------------------------------ voices (cached)
@lru_cache(maxsize=None)
def _bass_note(midi, n, sr):
    f = midi_to_freq(midi)
    t = time_axis(n, sr)
    wave = saw(f, n, sr, 9) + 0.6 * np.sin(2 * np.pi * f * t)
    return wave * envelope(n, sr, 0.004, 0.03, decay=2.0)


@lru_cache(maxsize=None)
def _pad_note(midi, n, sr):
    f = midi_to_freq(midi)
    wave = 0.5 * (saw(f * 0.997, n, sr, 6) + saw(f * 1.003, n, sr, 6))
    return wave * envelope(n, sr, 0.30, 0.40)


@lru_cache(maxsize=None)
def _arp_note(midi, n, sr):
    return square(midi_to_freq(midi), n, sr, 5) * envelope(n, sr, 0.002, 0.02, decay=15.0)


@lru_cache(maxsize=None)
def _lead_note(midi, n, sr):
    f = midi_to_freq(midi)
    t = time_axis(n, sr)
    vibrato = 1.0 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1.0, t * 4)
    phase = 2 * np.pi * np.cumsum(f * vibrato) / sr
    wave = np.zeros(n)
    for k in range(1, 8):
        wave += np.sin(k * phase) / k
    wave = wave * (2 / np.pi) + 0.35 * np.sin(phase * 2.002)
    return wave * envelope(n, sr, 0.012, 0.09)


def _kick(sr):
    n = int(0.28 * sr)
    t = time_axis(n, sr)
    freq = 150.0 * np.exp(-t * 32) + 46.0
    phase = 2 * np.pi * np.cumsum(freq) / sr
    click = np.exp(-t * 400) * 0.4
    ramp = np.minimum(1.0, t / 0.002)               # 2 ms fade-in: no click where the loop restarts
    return (np.sin(phase) * np.exp(-t * 13) + click) * ramp


def _clap(sr, rng):
    n = int(0.24 * sr)
    t = time_axis(n, sr)
    noise = rng.uniform(-1, 1, n)
    noise[1:] -= 0.6 * noise[:-1]                          # brighten
    env = np.exp(-t * 16) * 0.55
    for off in (0.0, 0.011, 0.022):                        # three quick slaps
        m = t >= off
        env[m] += np.exp(-(t[m] - off) * 150) * 0.8
    return noise * env


def _hat(sr, rng, length, decay):
    n = int(length * sr)
    t = time_axis(n, sr)
    noise = rng.uniform(-1, 1, n)
    noise = np.diff(noise, prepend=0.0)
    noise = np.diff(noise, prepend=0.0)                    # 2x differentiate = high-pass
    return noise * np.exp(-t * decay) * 0.5


# ------------------------------------------------------------------ mixing helpers
def _place(bus, start, wave, gain=1.0, pan=0.0):
    """Add `wave` into a (total, 2) bus at `start`, wrapping past the end (seamless loop)."""
    angle = (pan + 1.0) * np.pi / 4.0
    gl, gr = np.cos(angle) * gain, np.sin(angle) * gain
    total = len(bus)
    start %= total
    end = start + len(wave)
    if end <= total:
        bus[start:end, 0] += wave * gl
        bus[start:end, 1] += wave * gr
    else:
        cut = total - start
        bus[start:, 0] += wave[:cut] * gl
        bus[start:, 1] += wave[:cut] * gr
        bus[:end - total, 0] += wave[cut:] * gl
        bus[:end - total, 1] += wave[cut:] * gr


def _build(sr):
    """Render the whole loop -> float array (n, 2) in [-1, 1]."""
    rng = np.random.default_rng(11)
    beat = int(round(60.0 / BPM * sr))
    step = beat // 4
    bar = beat * 4
    total = bar * BARS

    drums = np.zeros((total, 2))
    bass = np.zeros((total, 2))
    pad = np.zeros((total, 2))
    arp = np.zeros((total, 2))
    lead = np.zeros((total, 2))

    kick, clap = _kick(sr), _clap(sr, rng)
    hat_c, hat_o = _hat(sr, rng, 0.05, 90), _hat(sr, rng, 0.20, 22)

    for b in range(BARS):
        block, bar_in_block = divmod(b, 4)
        root, tones = CHORDS[PROGRESSIONS[block][bar_in_block]]
        t0 = b * bar
        last_bar = b == BARS - 1

        # ---- drums
        for beat_i in range(4):
            if last_bar and beat_i == 3:
                continue                                    # gap before the loop restarts
            _place(drums, t0 + beat_i * beat, kick, 0.95)
        if block >= 1 or bar_in_block >= 2:
            for s in (4, 12):
                _place(drums, t0 + s * step, clap, 0.50)
        for s in range(16):
            if s % 4 == 2:
                _place(drums, t0 + s * step, hat_o if (block >= 2 and s == 14) else hat_c, 0.30, 0.15)
            elif s % 2 == 1:
                _place(drums, t0 + s * step, hat_c, 0.10, -0.15)
        if last_bar:                                         # snare-style roll fill
            for i, s in enumerate(range(8, 16)):
                _place(drums, t0 + s * step, clap, 0.25 + 0.07 * i)

        # ---- bass
        for s in BASS_STEPS:
            note = root + (12 if s in (3, 11) else 0) + (7 if s == 14 else 0)
            _place(bass, t0 + s * step, _bass_note(note, int(step * 1.8), sr), 0.45)

        # ---- pad (long notes, overlap into the next bar for smooth chord changes)
        for tone, pan in zip(tones[:3], (-0.5, 0.0, 0.5)):
            _place(pad, t0, _pad_note(tone - 12, bar + int(0.45 * sr), sr), 0.20, pan)

        # ---- arpeggio, ping-ponging left/right
        for s, idx in enumerate(ARP_PATTERN):
            _place(arp, t0 + s * step, _arp_note(tones[idx] + 12, int(step * 1.6), sr), 0.075,
                   -0.6 if s % 2 == 0 else 0.6)

        # ---- lead
        line = LEADS[block]
        if line:
            for s, note, dur in line[bar_in_block]:
                _place(lead, t0 + s * step, _lead_note(note, dur * step, sr), 0.16)

    # sidechain: everything but the drums ducks on each beat -> the "pump"
    pos = (np.arange(total) % beat) / sr
    duck = (1.0 - 0.72 * np.exp(-pos * 11.0))[:, None]
    bed = (bass + pad + arp) * duck

    # ping-pong delay on the lead (circular roll keeps the loop seamless)
    wet = np.zeros_like(lead)
    wet[:, 0] = 0.34 * np.roll(lead[:, 0], 3 * step) + 0.16 * np.roll(lead[:, 0], 6 * step)
    wet[:, 1] = 0.34 * np.roll(lead[:, 1], 4 * step) + 0.16 * np.roll(lead[:, 1], 8 * step)

    mix = drums + bed + lead + wet
    mix = np.tanh(mix * 1.25)                                # gentle glue / soft clip
    mix *= 0.92 / max(1e-9, np.max(np.abs(mix)))
    return mix


# ------------------------------------------------------------------ public API
_data = None
_sound = None
_channels = 2
_thread = None
_failed = False
_music_on = False
_playing = False


def _worker(sr):
    global _data, _failed
    try:
        _data = _build(sr)
    except Exception:                    # never crash the game because of audio
        _failed = True


def preload():
    """Start building the track in the background (safe to call many times)."""
    global _thread, _channels, _failed
    if _thread is not None or _sound is not None:
        return
    cfg = ensure_mixer()
    if cfg is None:
        _failed = True
        return
    sr, _channels = cfg
    _thread = threading.Thread(target=_worker, args=(sr,), daemon=True)
    _thread.start()


def is_loading():
    return _music_on and not _playing and not _failed


def is_music_on():
    return _music_on


def update():
    """Call every frame: starts playback as soon as the background build has finished."""
    global _sound, _playing
    if not _music_on or _playing or _failed:
        return
    if _sound is None:
        if _data is None:
            return
        _sound = to_sound(_data, _channels)
        _sound.set_volume(BASE_VOLUME)
    _sound.play(loops=-1)
    _playing = True


def start_music():
    global _music_on
    _music_on = True
    preload()
    update()


def stop_music():
    global _music_on, _playing
    _music_on = False
    _playing = False
    if _sound is not None:
        _sound.stop()


def toggle_music():
    """Switch music on/off. Returns True when it is (going to be) playing."""
    if _music_on:
        stop_music()
    else:
        start_music()
    return _music_on


def set_volume(volume):
    global BASE_VOLUME
    BASE_VOLUME = max(0.0, min(1.0, float(volume)))
    if _sound is not None:
        _sound.set_volume(BASE_VOLUME)
