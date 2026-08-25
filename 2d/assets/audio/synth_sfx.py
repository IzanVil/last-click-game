#!/usr/bin/env python3
"""Sintetiza los 3 efectos de sonido del juego (disparo, victoria, derrota)
como .wav mono de 16 bits, usando solo la libreria estandar. Son sonidos
generados por codigo (sin banco externo, sin licencia que gestionar):
placeholders limpios que se pueden sustituir mas adelante por SFX grabados
sin tocar nada del lado de Godot (mismos nombres de archivo).
"""
import math
import random
import struct
import wave

SAMPLE_RATE = 44100


def _write_wav(path: str, samples: list[float]) -> None:
    """samples: floats en [-1, 1]."""
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in samples
        )
        f.writeframes(frames)


def _envelope_exp(n: int, decay: float) -> list[float]:
    return [math.exp(-decay * i / SAMPLE_RATE) for i in range(n)]


def disparo() -> list[float]:
    """Disparo: chasquido de percusion (ruido con caida rapida) + golpe
    grave (seno de baja frecuencia con caida algo mas lenta), sumados."""
    duracion = 0.3
    n = int(SAMPLE_RATE * duracion)
    random.seed(1)
    crack = [random.uniform(-1, 1) for _ in range(n)]
    env_crack = _envelope_exp(n, 28.0)
    body_freq = 90.0
    env_body = _envelope_exp(n, 10.0)
    out = []
    for i in range(n):
        c = crack[i] * env_crack[i] * 0.6
        b = math.sin(2 * math.pi * body_freq * i / SAMPLE_RATE) * env_body[i] * 0.8
        out.append(c + b)
    peak = max(abs(x) for x in out) or 1.0
    return [x / peak * 0.95 for x in out]


def derrota() -> list[float]:
    """Derrota: barrido descendente de onda cuadrada (tipico "wah-wah" de
    fallo), de 300 Hz a 70 Hz en 0.7s, con caida suave al final."""
    duracion = 0.7
    n = int(SAMPLE_RATE * duracion)
    f_start, f_end = 300.0, 70.0
    out = []
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = f_start + (f_end - f_start) * t
        phase += 2 * math.pi * freq / SAMPLE_RATE
        square = 1.0 if math.sin(phase) >= 0 else -1.0
        env = 1.0 - t * 0.85  # se apaga hacia el final, no corta en seco
        out.append(square * env * 0.5)
    return out


def victoria() -> list[float]:
    """Victoria: arpegio ascendente (Do-Mi-Sol-Do agudo) con envolvente
    de pulso corto por nota, superpuestas un poco entre si."""
    notas = [523.25, 659.25, 783.99, 1046.50]  # C5 E5 G5 C6
    dur_nota = 0.22
    solape = 0.06
    n_nota = int(SAMPLE_RATE * dur_nota)
    paso = int(SAMPLE_RATE * (dur_nota - solape))
    total = paso * (len(notas) - 1) + n_nota
    out = [0.0] * total
    for idx, freq in enumerate(notas):
        inicio = idx * paso
        for i in range(n_nota):
            t = i / SAMPLE_RATE
            env = math.exp(-4.5 * t) * (1.0 - math.exp(-80.0 * t))  # ataque rapido, caida suave
            out[inicio + i] += math.sin(2 * math.pi * freq * t) * env * 0.5
    peak = max(abs(x) for x in out) or 1.0
    return [x / peak * 0.9 for x in out]


if __name__ == "__main__":
    import os

    out_dir = os.environ.get("OUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    _write_wav(os.path.join(out_dir, "disparo.wav"), disparo())
    _write_wav(os.path.join(out_dir, "derrota.wav"), derrota())
    _write_wav(os.path.join(out_dir, "victoria.wav"), victoria())
    print("Generados disparo.wav, derrota.wav, victoria.wav en", out_dir)
