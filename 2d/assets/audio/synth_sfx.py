#!/usr/bin/env python3
"""Sintetiza los efectos de sonido y el ambiente del juego como .wav mono
de 16 bits, usando solo la libreria estandar. Son sonidos generados por
codigo (sin banco externo, sin licencia que gestionar): placeholders limpios
que se pueden sustituir mas adelante por SFX grabados sin tocar nada del lado
de Godot (mismos nombres de archivo).

Los efectos cortos (disparo, derrota, victoria, engranaje, marca, fallo,
clic, calor) van a 44100 Hz. Las dos capas de musica, que suenan en bucle
todo el rato y son graves y oscuras, van a 22050 Hz: ahi no se pierde nada
audible y el archivo ocupa la mitad en el repositorio.

La musica son dos pistas de la misma duracion que se reproducen a la vez y
en fase: `musica_base` suena siempre, y `musica_tension` entra por encima
cuando quedan pocos huecos por probar. Que sean dos ficheros y no uno con
mas notas es justo lo que permite que la tension aparezca y desaparezca sin
cortar la musica.
"""

import math
import random
import struct
import wave

SAMPLE_RATE = 44100

# La musica en bucle usa su propia frecuencia de muestreo (ver docstring).
SAMPLE_RATE_MUSICA = 22050

# Compas de la musica: 70 pulsos por minuto, cuatro por compas, ocho
# compases de bucle. En segundos sale un numero feo (27.428571...), pero en
# muestras es exacto: 22050 * 32 * 60 / 70 = 604800.
BPM = 70
PULSOS_POR_COMPAS = 4
COMPASES = 8
PULSO = 60.0 / BPM
DURACION_MUSICA = PULSO * PULSOS_POR_COMPAS * COMPASES


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


def clic() -> list[float]:
    """Cartucho vacio: el clic hueco del percutor al caer sobre nada. Un
    golpecito de ruido muy corto sobre dos resonancias metalicas que se
    apagan enseguida; suena hueco justo porque no tiene cuerpo grave."""
    duracion = 0.18
    n = int(SAMPLE_RATE * duracion)
    random.seed(23)
    env = _envelope_exp(n, 45.0)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        percutor = random.uniform(-1, 1) * math.exp(-260.0 * t)
        resonancia = math.sin(2 * math.pi * 720.0 * t) * math.exp(-30.0 * t)
        cuerpo = math.sin(2 * math.pi * 265.0 * t) * math.exp(-22.0 * t) * 0.5
        out.append((percutor + resonancia * 0.6 + cuerpo) * env[i] * 0.6)
    return _normalizar(out, 0.8)


def calor() -> list[float]:
    """Tambor caliente: un zumbido que sube de tono y se queda vibrando, con
    el temblor de algo que se dilata. Acompana al evento que hace dudar de
    la pista siguiente, asi que no golpea: incomoda."""
    duracion = 0.9
    n = int(SAMPLE_RATE * duracion)
    f_inicio, f_final = 90.0, 235.0
    out = []
    fase = 0.0
    for i in range(n):
        t = i / n
        freq = f_inicio + (f_final - f_inicio) * t
        fase += 2 * math.pi * freq / SAMPLE_RATE
        # Diente de sierra pobre (dos armonicos): mas aspero que un seno.
        onda = math.sin(fase) + 0.45 * math.sin(2 * fase)
        temblor = 0.75 + 0.25 * math.sin(2 * math.pi * 11.0 * i / SAMPLE_RATE)
        env = math.sin(math.pi * t) ** 0.7  # entra y sale sin cortes
        out.append(onda * temblor * env * 0.5)
    return _normalizar(out, 0.75)


def _frecuencia_de_bucle(freq: float, duracion: float) -> float:
    """Ajusta `freq` a la frecuencia mas cercana que cabe un numero entero de
    ciclos en `duracion`. Solo hace falta para los sonidos sostenidos (el
    bordon de fondo): si un ciclo se corta a medias en el punto de bucle, al
    repetirse se oye un chasquido."""
    ciclos = max(1, round(freq * duracion))
    return ciclos / duracion


def _sumar_con_vuelta(destino: list[float], inicio: int, muestras: list[float]) -> None:
    """Suma `muestras` en `destino` a partir de `inicio`, dando la vuelta al
    llegar al final.

    Asi la cola de la ultima nota de un compas reaparece al principio del
    bucle, que es exactamente lo que se oiria si la musica siguiera sonando:
    la repeticion no corta ninguna nota a medias.
    """
    n = len(destino)
    for i, muestra in enumerate(muestras):
        destino[(inicio + i) % n] += muestra


def _nota_piano(freq: float, duracion: float, rate: int) -> list[float]:
    """Nota de piano de pobres: la fundamental y tres armonicos, cada uno
    apagandose mas rapido que el anterior (como en una cuerda de verdad), con
    un ataque de un par de milisegundos para que no chasquee al empezar."""
    n = int(rate * duracion)
    pesos = [(1.0, 1.0, 3.2), (2.0, 0.5, 4.6), (3.0, 0.25, 6.0), (4.0, 0.12, 7.4)]
    out = []
    for i in range(n):
        t = i / rate
        ataque = 1.0 - math.exp(-120.0 * t)
        muestra = 0.0
        for armonico, peso, caida in pesos:
            parcial = math.sin(2 * math.pi * freq * armonico * t)
            muestra += peso * parcial * math.exp(-caida * t)
        out.append(muestra * ataque * 0.25)
    return out


def musica_base() -> list[float]:
    """Capa que suena siempre: un bordon grave de La menor y un arpegio lento
    de piano, un acorde por compas, a 70 pulsos por minuto.

    Todo esta calculado para encadenar: el bordon usa frecuencias que caben
    un numero entero de veces en el bucle y las colas de las notas dan la
    vuelta al principio (ver _sumar_con_vuelta).
    """
    rate = SAMPLE_RATE_MUSICA
    n = int(rate * DURACION_MUSICA)
    out = [0.0] * n

    # Bordon: La1 y su quinta, mas un temblor lento de lampara.
    grave = _frecuencia_de_bucle(55.0, DURACION_MUSICA)
    quinta = _frecuencia_de_bucle(82.5, DURACION_MUSICA)
    tremolo = _frecuencia_de_bucle(0.14, DURACION_MUSICA)
    for i in range(n):
        t = i / rate
        respira = 0.7 + 0.3 * math.sin(2 * math.pi * tremolo * t)
        bordon = math.sin(2 * math.pi * grave * t) * 0.55
        bordon += math.sin(2 * math.pi * quinta * t) * 0.25
        out[i] += bordon * respira

    # Arpegio: La menor -> Fa -> Do -> Sol, dos compases cada acorde en el
    # bajo y una nota suelta por cada dos pulsos encima.
    acordes = [
        [220.00, 261.63, 329.63],  # Am
        [174.61, 220.00, 261.63],  # F
        [261.63, 329.63, 392.00],  # C
        [196.00, 246.94, 293.66],  # G
    ]
    pulsos = PULSOS_POR_COMPAS * COMPASES
    for pulso in range(0, pulsos, 2):
        compas = pulso // PULSOS_POR_COMPAS
        acorde = acordes[(compas // 2) % len(acordes)]
        freq = acorde[(pulso // 2) % len(acorde)]
        inicio = int(pulso * PULSO * rate)
        _sumar_con_vuelta(out, inicio, _nota_piano(freq, 2.6, rate))

    return _normalizar(out, 0.55)


def musica_tension() -> list[float]:
    """Capa que se superpone a la base cuando quedan pocos huecos: un latido
    en cada pulso y una nota alta a distancia de tritono, el intervalo que
    lleva desde la Edad Media llamandose "el diablo en la musica".

    Misma duracion y mismo tempo que musica_base, y se lanza a la vez, asi
    que las dos van en fase mientras compartan `pitch_scale`.
    """
    rate = SAMPLE_RATE_MUSICA
    n = int(rate * DURACION_MUSICA)
    out = [0.0] * n

    # Latido: un golpe grave por pulso, mas fuerte al empezar cada compas.
    n_golpe = int(rate * 0.26)
    env = _envelope_exp(n_golpe, 16.0, rate)
    for pulso in range(PULSOS_POR_COMPAS * COMPASES):
        fuerza = 1.0 if pulso % PULSOS_POR_COMPAS == 0 else 0.55
        golpe = []
        for i in range(n_golpe):
            t = i / rate
            ataque = 1.0 - math.exp(-140.0 * t)
            # El tono cae mientras suena: un latido, no una nota.
            freq = 62.0 * math.exp(-6.0 * t) + 38.0
            onda = math.sin(2 * math.pi * freq * t)
            golpe.append(onda * env[i] * ataque * fuerza * 0.8)
        _sumar_con_vuelta(out, int(pulso * PULSO * rate), golpe)

    # Tritono sostenido (La y Mi bemol), muy bajo y con temblor: no se
    # escucha como melodia, se nota como desasosiego.
    la = _frecuencia_de_bucle(440.0, DURACION_MUSICA)
    mi_bemol = _frecuencia_de_bucle(622.25, DURACION_MUSICA)
    vaiven = _frecuencia_de_bucle(0.5, DURACION_MUSICA)
    for i in range(n):
        t = i / rate
        temblor = 0.35 + 0.3 * (0.5 + 0.5 * math.sin(2 * math.pi * vaiven * t))
        tritono = math.sin(2 * math.pi * la * t) + math.sin(2 * math.pi * mi_bemol * t)
        out[i] += tritono * temblor * 0.09

    return _normalizar(out, 0.6)


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
    _write_wav(os.path.join(out_dir, "clic.wav"), clic())
    _write_wav(os.path.join(out_dir, "calor.wav"), calor())
    for nombre, generador in (
        ("musica_base.wav", musica_base),
        ("musica_tension.wav", musica_tension),
    ):
        _write_wav(os.path.join(out_dir, nombre), generador(), SAMPLE_RATE_MUSICA)
    efectos = "disparo, derrota, victoria, engranaje, marca, fallo, clic y calor"
    print(f"Generados {efectos}, y las dos capas de musica (.wav), en {out_dir}")
