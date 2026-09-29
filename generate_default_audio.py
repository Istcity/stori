import math
import struct
import wave
import numpy as np
from pathlib import Path

SAMPLE_RATE = 44100

def write_wav(filename: Path, samples: np.ndarray):
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(str(filename), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_samples.tobytes())

def generate_whoosh(out_path: Path):
    duration = 0.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Filtered white noise with pitch and amplitude envelope
    noise = np.random.uniform(-1, 1, len(t))
    # Bandpass filter simulation via modulated sine + noise
    freq = np.linspace(200, 1200, len(t))
    sweep = np.sin(2 * np.pi * freq * t)
    env = np.sin(np.pi * (t / duration)) ** 2
    samples = (noise * 0.6 + sweep * 0.4) * env
    write_wav(out_path, samples)

def generate_pop(out_path: Path):
    duration = 0.12
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.exp(np.linspace(np.log(800), np.log(120), len(t)))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    env = np.exp(-t * 40)
    samples = np.sin(phase) * env
    write_wav(out_path, samples)

def generate_punch(out_path: Path):
    duration = 0.35
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Low frequency thump + burst of noise
    sub = np.sin(2 * np.pi * 65 * t) * np.exp(-t * 15)
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 30)
    samples = sub * 0.7 + noise * 0.5
    write_wav(out_path, samples)

def generate_record_scratch(out_path: Path):
    duration = 0.6
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Rapid frequency modulation + vinyl grit
    freq = 600 + 400 * np.sin(2 * np.pi * 8 * t) * np.linspace(1, 0.1, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    grit = np.random.choice([0, 0, 0, 1, -1], len(t)) * 0.3
    env = np.clip(1.0 - t / duration, 0, 1)
    samples = (np.sin(phase) * 0.6 + grit) * env
    write_wav(out_path, samples)

def generate_cricket(out_path: Path):
    duration = 1.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    carrier = np.sin(2 * np.pi * 4500 * t)
    pulse = (np.sin(2 * np.pi * 25 * t) > 0.3).astype(float)
    chirp_gate = np.sin(2 * np.pi * 2.5 * t) > 0
    samples = carrier * pulse * chirp_gate * 0.4
    write_wav(out_path, samples)

def generate_dramatic_boom(out_path: Path):
    duration = 1.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    sub = np.sin(2 * np.pi * np.linspace(80, 25, len(t)) * t) * np.exp(-t * 2.5)
    noise = np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-t * 6.0)
    samples = sub * 0.8 + noise * 0.4
    write_wav(out_path, samples)

def generate_bgm_loop(out_path: Path):
    # Cheerful, clean storytime acoustic/lo-fi progression (C - G - Am - F)
    # 16 bars ~ 12 seconds
    bpm = 110
    beat_dur = 60.0 / bpm
    bar_dur = beat_dur * 4
    total_bars = 4
    total_dur = bar_dur * total_bars
    t_total = np.linspace(0, total_dur, int(SAMPLE_RATE * total_dur), endpoint=False)
    song = np.zeros_like(t_total)

    # Chords (frequencies in Hz)
    # C major: C4 (261.63), E4 (329.63), G4 (392.00)
    # G major: B3 (246.94), D4 (293.66), G4 (392.00)
    # A minor: A3 (220.00), C4 (261.63), E4 (329.63)
    # F major: F3 (174.61), A3 (220.00), C4 (261.63)
    chord_seq = [
        ([261.63, 329.63, 392.00, 523.25], 130.81),
        ([246.94, 293.66, 392.00, 493.88], 98.00),
        ([220.00, 261.63, 329.63, 440.00], 110.00),
        ([174.61, 220.00, 261.63, 349.23], 87.31)
    ]

    for i, (notes, bass_freq) in enumerate(chord_seq):
        start_idx = int(i * bar_dur * SAMPLE_RATE)
        end_idx = int((i + 1) * bar_dur * SAMPLE_RATE)
        t_bar = np.linspace(0, bar_dur, end_idx - start_idx, endpoint=False)

        # Arpeggiate notes on quarter beats
        bar_audio = np.zeros_like(t_bar)
        # Bass note
        bass_env = np.exp(-t_bar * 1.5)
        bar_audio += np.sin(2 * np.pi * bass_freq * t_bar) * bass_env * 0.35

        for b in range(4):
            t_note_start = b * beat_dur
            note = notes[b % len(notes)]
            idx1 = int(t_note_start * SAMPLE_RATE)
            idx2 = min(len(t_bar), int((t_note_start + beat_dur * 1.2) * SAMPLE_RATE))
            t_n = np.linspace(0, (idx2 - idx1)/SAMPLE_RATE, idx2 - idx1, endpoint=False)
            # Soft pluck harmonics
            pluck = (np.sin(2 * np.pi * note * t_n) * 0.5 + 
                     np.sin(2 * np.pi * note * 2 * t_n) * 0.25) * np.exp(-t_n * 4.0)
            bar_audio[idx1:idx2] += pluck * 0.35

        song[start_idx:end_idx] = bar_audio

    # Normalize gently
    song = song / (np.max(np.abs(song)) + 1e-6) * 0.5
    write_wav(out_path, song)

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    sfx_dir = base_dir / "assets" / "sfx"
    bgm_dir = base_dir / "assets" / "bgm"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    bgm_dir.mkdir(parents=True, exist_ok=True)

    generate_whoosh(sfx_dir / "whoosh.wav")
    generate_pop(sfx_dir / "pop.wav")
    generate_punch(sfx_dir / "punch.wav")
    generate_record_scratch(sfx_dir / "record_scratch.wav")
    generate_cricket(sfx_dir / "cricket.wav")
    generate_dramatic_boom(sfx_dir / "dramatic_boom.wav")
    generate_bgm_loop(bgm_dir / "storytime_acoustic_loop.wav")
    print("Audio assets generated successfully!")
