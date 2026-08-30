#!/usr/bin/env python3
"""Sintetiza los efectos de sonido y el ambiente del juego como .wav mono
de 16 bits, usando solo la libreria estandar. Son sonidos generados por
codigo (sin banco externo, sin licencia que gestionar): placeholders limpios
que se pueden sustituir mas adelante por SFX grabados sin tocar nada del lado
de Godot (mismos nombres de archivo).

Los cortos (disparo, derrota, victoria, engranaje, marca, fallo) van a 44100
Hz; el ambiente, que es un bordon de frecuencias graves pensado para sonar en
bucle todo el rato, va a 22050 Hz: a esas frecuencias no se pierde nada
audible y el archivo ocupa la mitad en el repositorio.
"""

import math
import random
import struct
import wave

SAMPLE_RATE = 44100

# El ambiente en bucle usa su propia frecuencia de muestreo (ver docstring).
SAMPLE_RATE_AMBIENTE = 22050

# Duracion del bucle de ambiente. Todas las frecuencias que suenan en el
# deben caber un numero entero de veces en estos segundos: asi el final
# encaja con el principio y el bucle no da un chasquido al repetirse.
DURACION_AMBIENTE = 6.0


def _write_wav(path: str, samples: list[float], rate: int = SAMPLE_RATE) -> None:
    """samples: floats en [-1, 1]."""
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", max(-32768, min(32767, int(s * 32767)))) for s in samples
        )
        f.writeframes(frames)


def _envelope_exp(n: int, decay: float, rate: int = SAMPLE_RATE) -> list[float]:
    return [math.exp(-decay * i / rate) for i in range(n)]


def _normalizar(samples: list[float], pico: float = 0.95) -> list[float]:
    maximo = max(abs(x) for x in samples) or 1.0
    return [x / maximo * pico for x in samples]


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
            env = math.exp(-4.5 * t) * (
                1.0 - math.exp(-80.0 * t)
            )  # ataque rapido, caida suave
            out[inicio + i] += math.sin(2 * math.pi * freq * t) * env * 0.5
    peak = max(abs(x) for x in out) or 1.0
    return [x / peak * 0.9 for x in out]


def engranaje() -> list[float]:
    """Engranaje: la rueda dentada del tambor girando. Doce trinquetes
    (ruido corto y muy seco, como un diente saltando) sobre un zumbido
    metalico de fondo que sube y baja de tono, para que la tanda suene a
    mecanismo y no a una lista de clics sueltos."""
    duracion = 0.55
    n = int(SAMPLE_RATE * duracion)
    random.seed(7)
    out = [0.0] * n

    zumbido_freq = 220.0
    for i in range(n):
        t = i / SAMPLE_RATE
        # Vibrato lento: el mecanismo "arrastra" al girar.
        freq = zumbido_freq * (1.0 + 0.06 * math.sin(2 * math.pi * 3.0 * t))
        env = math.sin(math.pi * t / duracion) ** 2  # entra y sale sin cortes
        out[i] += math.sin(2 * math.pi * freq * t) * env * 0.18

    dientes = 12
    n_diente = int(SAMPLE_RATE * 0.035)
    for d in range(dientes):
        inicio = int(d * (n - n_diente) / (dientes - 1))
        # Los ultimos dientes suenan mas flojos: el tambor pierde impulso.
        fuerza = 1.0 - 0.55 * d / (dientes - 1)
        env = _envelope_exp(n_diente, 90.0)
        for i in range(n_diente):
            ruido = random.uniform(-1, 1)
            timbre = math.sin(2 * math.pi * 1800.0 * i / SAMPLE_RATE)
            out[inicio + i] += (ruido * 0.6 + timbre * 0.4) * env[i] * fuerza * 0.7

    return _normalizar(out)


def marca() -> list[float]:
    """Farol acertado: campanilla corta y aguda (dos senos en quinta) con
    caida limpia. Un "clic" agudo de acierto, sin la fanfarria de
    victoria.wav, que se reserva para retirarse con el dinero."""
    duracion = 0.35
    n = int(SAMPLE_RATE * duracion)
    env = _envelope_exp(n, 12.0)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        ataque = 1.0 - math.exp(-200.0 * t)
        fundamental = math.sin(2 * math.pi * 1320.0 * t)
        quinta = math.sin(2 * math.pi * 1980.0 * t)
        out.append((fundamental + 0.5 * quinta) * env[i] * ataque * 0.5)
    return _normalizar(out, 0.85)


def fallo() -> list[float]:
    """Farol fallido: golpe seco y grave (madera contra metal). Ni mata ni
    premia, asi que dura poco y no lleva tono definido: solo el "toc" de
    haber gastado una marca para nada."""
    duracion = 0.25
    n = int(SAMPLE_RATE * duracion)
    random.seed(11)
    env = _envelope_exp(n, 32.0)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        golpe = math.sin(2 * math.pi * 130.0 * t) * 0.8
        madera = random.uniform(-1, 1) * math.exp(-120.0 * t) * 0.5
        out.append((golpe + madera) * env[i])
    return _normalizar(out, 0.85)


def ambiente() -> list[float]:
    """Ambiente en bucle: un bordon grave (La1 y su quinta, ligeramente
    desafinada entre si para que "respire") con un tremolo lento y cuatro
    latidos de corazon repartidos por el bucle.

    Todo esta elegido para que el final empalme con el principio: las
    frecuencias caben un numero entero de ciclos en DURACION_AMBIENTE y los
    latidos se apagan del todo antes de llegar al corte.
    """
    rate = SAMPLE_RATE_AMBIENTE
    n = int(rate * DURACION_AMBIENTE)
    out = [0.0] * n

    # 55 Hz = 330 ciclos en 6 s; 82.5 Hz = 495; el tremolo, 3. Todos enteros.
    for i in range(n):
        t = i / rate
        tremolo = 0.75 + 0.25 * math.sin(2 * math.pi * 0.5 * t)
        grave = math.sin(2 * math.pi * 55.0 * t)
        quinta = math.sin(2 * math.pi * 82.5 * t) * 0.45
        out[i] += (grave + quinta) * tremolo * 0.5

    # Latidos: cada 1.5 s (4 en el bucle), dos golpes por latido.
    n_golpe = int(rate * 0.18)
    env = _envelope_exp(n_golpe, 22.0, rate)
    for latido in range(4):
        base = latido * 1.5
        for retardo, fuerza in ((0.0, 1.0), (0.22, 0.6)):
            inicio = int((base + retardo) * rate)
            for i in range(n_golpe):
                if inicio + i >= n:
                    break
                t = i / rate
                ataque = 1.0 - math.exp(-150.0 * t)
                golpe = math.sin(2 * math.pi * 48.0 * t)
                out[inicio + i] += golpe * env[i] * ataque * fuerza * 0.7

    return _normalizar(out, 0.7)


if __name__ == "__main__":
    import os

    out_dir = os.environ.get("OUT_DIR", ".")
    os.makedirs(out_dir, exist_ok=True)
    _write_wav(os.path.join(out_dir, "disparo.wav"), disparo())
    _write_wav(os.path.join(out_dir, "derrota.wav"), derrota())
    _write_wav(os.path.join(out_dir, "victoria.wav"), victoria())
    _write_wav(os.path.join(out_dir, "engranaje.wav"), engranaje())
    _write_wav(os.path.join(out_dir, "marca.wav"), marca())
    _write_wav(os.path.join(out_dir, "fallo.wav"), fallo())
    _write_wav(os.path.join(out_dir, "ambiente.wav"), ambiente(), SAMPLE_RATE_AMBIENTE)
    generados = "disparo, derrota, victoria, engranaje, marca, fallo y ambiente"
    print(f"Generados {generados} (.wav) en {out_dir}")
