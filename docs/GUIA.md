# Guía del proyecto

Este documento describe la mecánica y las reglas de los dos juegos del
repositorio, además de cómo ampliarlos y modificarlos.

## Mecánica de la ruleta rusa

Las dos versiones juegan la misma mecánica: "El Tambor del Juicio" (ver la
hoja de ruta del `README.md`). Está descrita una sola vez aquí porque el
diseño es idéntico en ambas; donde cambia el nombre de algo entre Python y
GDScript se indica entre paréntesis.

### El Tambor del Juicio

1. El tambor tiene **8 huecos** y una única bala colocada al azar. La
   partida no termina en la primera muerte: el objetivo es acumular **días
   de vida** (cada día son 3 disparos sobrevividos, `DISPAROS_POR_DIA`).
2. Cada turno el jugador elige entre **disparar**, **retirarse** o, si le
   quedan, **marcar**:
   - Retirarse cobra los puntos que hay en juego (la partida empieza con
     100) y termina la partida.
   - Disparar y fallar (cartucho vacío) dobla los puntos en juego, mueve la
     bala a otro hueco según un patrón oculto y revela una pista sobre su
     nueva posición.
   - Disparar y acertar la bala es un **BOOM**: se pierden todos los puntos
     en juego y termina la partida.
   - Marcar declara un hueco "seguro" sin disparar, gastando una de las **3
     marcas** de la partida (se gasta acierte o falle). Acertar da un bono
     de puntos sin doblar; fallar solo cuesta la marca, sin mover la bala
     ni terminar la partida.
3. El patrón de movimiento (avanza, retrocede, salta de dos en dos o
   espejo) se sortea al empezar la partida y no se le dice al jugador: se
   deduce comparando las pistas de varios disparos.
4. Tras un disparo fallido puede ocurrir un **evento aleatorio**:
   `clic_metalico` desplaza la bala un paso extra (fuera del patrón normal)
   y `tambor_caliente` hace que la siguiente pista sea mentirosa (afirma lo
   contrario de la posición real, con el mismo aspecto que una veraz).
5. El tambor ASCII colorea cada hueco según lo que se sabe de él: **verde**
   si un farol confirmó que estaba vacío, **rojo** si un farol reveló la
   bala ahí, **amarillo** si es un candidato que cumple con el cruce de
   *todas* las pistas vigentes, **gris** si ya se disparó ahí alguna vez.
   Si el cruce de pistas se queda sin candidatos, es señal de que alguna
   pista reciente mentía.
6. Al terminar la partida se resume en una frase lo ocurrido (días
   sobrevividos, faroles lanzados/acertados, eventos sufridos).
7. La dificultad tiene tres presets (fácil/normal/difícil) que ajustan
   huecos y marcas a la vez; huecos y marcas también se pueden fijar por
   separado. Cada partida actualiza unos récords persistidos entre
   ejecuciones (días máximos, puntos máximos, faroles acertados/usados).
8. **Modo duelo**: dos jugadores se turnan en el mismo tambor —bala,
   patrón y pistas compartidos—, cada uno con su propia apuesta y sus
   propias marcas. Marcar también consume turno. La partida termina en
   cuanto el turno de uno de los dos acaba en BOOM o en retirada (el otro
   no sigue jugando en solitario después, y se queda con los puntos que
   tuviera en juego); gana quien sobrevivió más días o, en caso de
   empate, quien tenga más puntos.

Cada versión ofrece esos ajustes a su manera: la terminal por línea de
comandos (`--dificultad`, `--duelo`, `--records`) y Godot en un menú
previo a la partida. Los récords se guardan en
`~/.tambor_del_juicio/records.json` (terminal) y en `user://records.json`
(Godot, el equivalente idiomático del motor). En la versión gráfica,
además, el tambor se ve girar al empezar la partida, pulsa con tensión
antes de revelar un disparo o un farol, y la pantalla vibra al morir; ver
"Versión gráfica (Godot)" más abajo.

## Versión de terminal (Python)

- Archivos: `terminal/ruleta.py` (interfaz, sin lógica propia) +
  `terminal/estado.py`, `terminal/pistas.py`, `terminal/apuestas.py`,
  `terminal/farol.py`, `terminal/eventos.py`, `terminal/historial.py`,
  `terminal/records.py` (lógica pura, sin `input()`/`print()`, igual de
  fácil de testear que `RuletaEstado.gd` en la versión Godot).
- Dependencias: **ninguna** (solo la librería estándar de Python 3.11+).
- Ejecución: `./run.sh`, o directamente `python3 terminal/ruleta.py`. Admite
  `--dificultad {facil,normal,dificil}`, `--huecos N`/`--marcas N` (pisan
  al preset), `--duelo` (modo duelo, ver `jugar_duelo()`), `--records`
  (muestra los récords guardados y no juega) y `--version`. `main()` es el
  entry point real (`ruleta = "terminal.ruleta:main"` en `pyproject.toml`),
  que envuelve `jugar()`/`jugar_duelo()` para capturar Ctrl+C.
- Interactúa por entrada/salida estándar con interfaz en colores y tambor ASCII.

### Cómo modificar la lógica

- `estado.HUECOS` (por defecto 8), `estado.PATRONES` y
  `estado.DISPAROS_POR_DIA` (por defecto 3) controlan el tamaño del tambor,
  los patrones de movimiento disponibles y la duración de un "día". Añadir
  un patrón nuevo implica sumarlo a `PATRONES` y a la función `_mover()` en
  `estado.py`.
- `pistas.TIPOS_PISTA` en `pistas.py` define los tipos de pista disponibles
  (`paridad`, `mitad`, `relativa`); cada uno es una rama de
  `generar_pista()`, que acepta `mentir=True` para invertir la respuesta
  (lo usa el evento `tambor_caliente`) y devuelve una `Pista(texto,
  candidatos)`: `candidatos` son los huecos consistentes con esa
  afirmación. `pistas.interseccion()` los cruza para pintar el tambor.
- `ruleta.APUESTA_BASE` (por defecto 100) es la apuesta inicial de cada
  partida y `ruleta.BONO_MARCA_ACERTADA` (por defecto 50) el bono de un
  farol acertado; la lógica de doblar/perder/retirarse/sumar bono vive en
  `apuestas.Apuesta`.
- `farol.MARCAS_INICIALES` (por defecto 3) son las marcas por partida;
  `farol.Farol` resuelve si un hueco marcado estaba vacío.
- `eventos.PROBABILIDAD` (por defecto 0.25) y `eventos.TIPOS_EVENTO`
  controlan cuánto y qué tan a menudo interfieren los eventos aleatorios
  tras un disparo fallido.
- `historial.Historial` acumula faroles y eventos de la partida;
  `historial.resumen()` genera la frase final. `ruleta.calcular_estados()`
  combina marcadas/resultados de farol/candidatos en el diccionario que
  colorea el tambor (`ruleta.COLORES_ESTADO`, `ruleta.GLIFOS_ESTADO`).
- `ruleta.DIFICULTADES` define los tres presets (huecos + marcas); añadir
  uno nuevo es sumar una entrada a ese diccionario, que ya
  aparece automáticamente en `--dificultad` (`choices=sorted(DIFICULTADES)`).
- `records.Records` es un dataclass con los contadores acumulados;
  `records.cargar()`/`records.guardar()` leen/escriben
  `records.ruta_por_defecto()` (`~/.tambor_del_juicio/records.json`) y
  aceptan una `ruta` explícita para tests. Un archivo ausente o corrupto
  no rompe la partida: `cargar()` devuelve `Records()` vacío.
- `ruleta.JugadorDuelo` (dataclass) lleva la apuesta/marca/historial/
  disparos de un jugador dentro de `jugar_duelo()`; su propiedad `dias`
  deriva de `disparos` igual que `estado.dias_sobrevividos()`.
  `jugar_duelo()` reutiliza `escena`/`cabecera`/`elegir_accion`/
  `elegir_posicion`/`impacto`/`retirada` tal cual (con los datos del
  jugador activo en cada turno); lo único propio del modo duelo es
  `escena_duelo()` (añade de quién es el turno y el estado del rival) y
  `resultado_duelo()` (compara días y, en empate, puntos).

`ruleta.py` importa estos siete módulos con un `try/except` (relativo si se
usa como paquete instalado, absoluto si se ejecuta como script suelto): si
añades un módulo de lógica más, sigue el mismo patrón de import.

### Tests

Hay una batería de pruebas por módulo (`test_estado.py`, `test_pistas.py`,
`test_apuestas.py`, `test_farol.py`, `test_eventos.py`, `test_historial.py`,
`test_records.py`, `test_ruleta.py`). Cualquier test que llame a
`jugar()`/`jugar_duelo()` debe parchear `ruleta.records.cargar` y
`ruleta.records.guardar` (ver el decorador `_parchear_records` en
`test_ruleta.py`): si no, leerían/escribirían el archivo de récords real
del usuario que ejecuta los tests.

```bash
cd terminal && python3 -m unittest discover -s . -v
```

## Versión gráfica (Godot)

- Carpeta: `2d/`
- Motor: **Godot 4.7+**
- Escena principal: `2d/scenes/MainGame.tscn`
- Lógica del juego (sin UI): `2d/RuletaEstado.gd` (orquestador) +
  `TamborJuicio.gd`, `Pista.gd`, `Pistas.gd`, `Apuesta.gd`, `Farol.gd`,
  `Eventos.gd`, `Historial.gd`, `Jugador.gd`, `Dificultad.gd`,
  `Records.gd` (lógica pura, sin nodos ni Tween — hermanas 1 a 1 de
  `terminal/estado.py` y compañía, mismo vocabulario en español).
- Vista: `2d/MainGame.gd` (menú + Label/Button/Tween) + `2d/TamborView.gd`
  (dibuja el tambor con `_draw()`).
- Ambientación (decorado puro, sin reglas): `2d/FondoTaller.gd`
  (engranajes y luz del fondo), `2d/Vineta.gd` (viñeta, resplandores de
  evento y cierre en iris) y `2d/Maquina.gd` (texto tecleado letra a letra).
- Ajustes de accesibilidad: `2d/Ajustes.gd` (efectos reducidos, texto
  grande, alto contraste y sonido, guardados en `user://ajustes.json`).

Ningún script de lógica conoce nodos ni UI: `RuletaEstado.gd` orquesta los
demás y emite señales (`partida_iniciada`, `entrada_invalida`,
`evento_ocurrido`, `pista_nueva`, `disparo_sobrevivido`, `dia_completado`,
`farol_resuelto`, `impacto`, `retirada`, `turno_cambiado`,
`duelo_terminado`) cuando pasa algo relevante. `MainGame.gd` se limita a
escucharlas y traducirlas a texto, colores y animaciones; `TamborView.gd`
ni siquiera sabe que existen: solo pinta el diccionario de estados que le
pasa `MainGame.gd` via `aplicar_estados()`, espejo de
`calcular_estados()`/`dibujar_tambor()` en `terminal/ruleta.py`.

`RuletaEstado` tampoco toca disco: persistir los récords es cosa de la
vista, que reacciona a `impacto`/`retirada` (igual que en la terminal, donde
lo hace `jugar()`, no los módulos de lógica).

Todos los scripts de lógica llevan `class_name` (`TamborJuicio`, `Pista`,
`Pistas`, `Apuesta`, `Farol`, `Eventos`, `Historial`, `Jugador`,
`Dificultad`, `Records`, `Ajustes`, `RuletaEstado`): se usan directamente
por su nombre desde cualquier script del proyecto, sin `preload()`. Lo
mismo vale para los de vista que se referencian desde la escena o desde
`MainGame.gd` (`TamborView`, `FondoTaller`, `Vineta`, `Maquina`).

### Solitario y duelo: la misma lógica

Una partida en solitario es **un duelo de un solo jugador**.
`RuletaEstado` lleva un `Array[Jugador]` y un índice `turno`; el tambor y
las pistas son de la partida (compartidos), mientras que apuesta, marcas,
historial y disparos son de cada `Jugador`. Los atajos
`RuletaEstado.apuesta`/`farol`/`historial`/`disparos` son *properties* que
apuntan al jugador activo, así que la vista y los tests escritos antes de
existir el duelo siguen funcionando sin cambios.

`iniciar_juego(huecos, marcas, nombres)` decide el modo: con `nombres`
vacío hay un jugador anónimo (solitario), y con dos o más, un duelo.
`es_duelo()` distingue los dos casos, y `turno_cambiado`/`duelo_terminado`
solo se emiten en duelo. El desempate (`Jugador.ganadores()`) es una
función estática pura, testeable sin montar una partida.

### Cómo modificar la lógica

- `RuletaEstado.HUECOS` (por defecto 8) y `RuletaEstado.DISPAROS_POR_DIA`
  (por defecto 3) controlan el tamaño del tambor y la duración de un
  "día". `TamborJuicio.PATRONES` define los patrones de movimiento de la
  bala; añadir uno implica sumarlo ahí y a `TamborJuicio._mover()`.
- `Pistas.TIPOS_PISTA` define los tipos de pista disponibles (`paridad`,
  `mitad`, `relativa`); `Pistas.generar_pista()` acepta `mentir = true`
  para invertir la respuesta (lo usa el evento `tambor_caliente`) y
  devuelve una `Pista` (`texto` + `candidatos`); `Pistas.interseccion()`
  los cruza para pintar el tambor.
- `RuletaEstado.APUESTA_BASE` (100) y `RuletaEstado.BONO_MARCA_ACERTADA`
  (50) son las mismas constantes que `ruleta.APUESTA_BASE`/
  `BONO_MARCA_ACERTADA` en la terminal; la lógica de doblar/perder/
  retirarse/sumar bono vive en `Apuesta.gd`.
- `Farol.MARCAS_INICIALES` (3) son las marcas por partida; `Eventos.
  PROBABILIDAD` (0.25) y `Eventos.TIPOS_EVENTO` controlan los eventos
  aleatorios. `RuletaEstado.probabilidad_eventos` existe *además* de
  `Eventos.PROBABILIDAD` solo para poder desactivar los eventos en tests
  deterministas (poniéndola a `0.0`): GDScript no tiene un equivalente a
  `unittest.mock.patch` para sustituir `Eventos.tirar_evento()` por fuera.
- `Historial.gd` acumula faroles y eventos y genera el resumen final;
  `MainGame._calcular_estados()` combina huecos ya disparados, resultados
  de farol y candidatos de `Pistas.interseccion()` en el diccionario que
  pinta `TamborView.aplicar_estados()`.
- `Dificultad.PRESETS` define los tres presets (huecos + marcas) y
  `Dificultad.ORDEN` en qué orden se ofrecen en el menú (que no es el
  alfabético). Añadir uno es sumar su entrada a `PRESETS`, `ORDEN` y
  `ETIQUETAS`, y aparece solo en el desplegable.
- `Records.gd` guarda y carga `user://records.json`. Un archivo ausente o
  corrupto no rompe la partida: `cargar()` devuelve unos récords vacíos.
  Usa `JSON.new().parse()` y no `JSON.parse_string()` a propósito: el
  segundo, además de devolver `null`, imprime un `ERROR:` en el log, y un
  archivo corrupto aquí es un caso previsto, no un fallo. Ojo también con
  que **un JSON devuelve todos los números como `float`**, de ahí el
  `int()` al recargar cada campo.
- `MainGame.ruta_records` existe (en vez de usar
  `Records.RUTA_POR_DEFECTO` directamente) para que los tests puedan
  redirigirla y no pisar los récords reales de quien los ejecuta — mismo
  motivo que `RuletaEstado.probabilidad_eventos`.

### Cómo modificar la vista

- La paleta noir/steampunk (`COLOR_DESCONOCIDO`, `COLOR_CANDIDATO`,
  `COLOR_SEGURO`, `COLOR_PELIGRO`, `COLOR_PROBADO`, `COLOR_ANILLO`,
  `COLOR_TEXTO`...) está al principio de `TamborView.gd`.
- La **tipografía y la chapa** salen de `assets/tema/juicio.tres`, un
  `Theme` con Courier Prime como `default_font` y con los `StyleBoxFlat`
  (metal oscuro con filete de latón) de botones, campos, desplegables y del
  panel que enmarca la interfaz, asignado al nodo raíz de la escena:
  toda la interfaz lo hereda sin overrides nodo por nodo, `TamborView`
  incluido (dibuja sus números con `get_theme_default_font()`). El título
  es la única excepción, con Special Elite en un `theme_override_fonts`.
  Para cambiar la fuente o el aspecto de los controles de todo el juego
  basta con tocar ese `.tres`.
  Ojo con dos cosas: las licencias de ambas fuentes obligan a
  redistribuir su texto (ver `assets/fonts/README.md`), y como solo
  cubren alfabeto latino, `MainGame._encadenar_respaldo_de_fuentes()`
  encadena la del motor por detrás para los nombres de jugador que se
  salgan de ahí.
- El feedback de fondo (flash de color tras cada acción) se gestiona en
  `MainGame.gd`, en `_flash(color)`; los colores (`COLOR_BOOM`,
  `COLOR_SUPERVIVENCIA`, `COLOR_FAROL_ACIERTO`/`_FALLO`, `COLOR_RETIRADA`)
  están al principio del archivo.
- La vibración de pantalla al morir es `MainGame._vibrar_pantalla()`
  (sacude `rotation`, no `position`: con los anchors a pantalla completa
  de `Centro`, mover `position` deformaría el layout en vez de
  desplazarlo — el mismo motivo por el que `TamborView.girar()` rota en
  vez de mover).
- El tambor **ya no gira en cada disparo** (a diferencia de la mecánica
  de 8 rondas anterior): la bala no se re-sortea en cada turno, solo se
  desplaza según su patrón, así que un giro completo por turno sugeriría
  un azar que no existe. Solo gira una vez, al empezar la partida
  (`TamborView.girar()` desde `MainGame._on_partida_iniciada()`); antes de
  revelar un disparo o un farol se usa `TamborView.tension()` en su lugar.

### La ambientación

Tres nodos de decorado, ninguno de los cuales sabe nada del juego: reciben
órdenes de `MainGame.gd` igual que las recibe un `Label`.

- `FondoTaller.gd` dibuja los engranajes del fondo (a distinta velocidad y
  tono según la profundidad, para dar sensación de máquina viva) y la luz
  cálida sobre el tambor. `calentar()` la vuelve rojiza y nerviosa mientras
  dura el evento «tambor caliente», y se enfría sola.
- `Vineta.gd` va **por encima** de la interfaz (el orden entre hermanos
  manda al dibujar) y no captura el ratón. Aporta la viñeta de los bordes,
  `resplandor(color)` para teñirlos en un evento y `cerrar()`/`abrir()`,
  el cierre en iris con el que termina una partida. El iris es un arco
  negro de trazo grueso cuyo radio mengua, con la viñeta encima para
  suavizarle el borde.
- `Maquina.gd` teclea el texto letra a letra animando `visible_ratio`. El
  `text` de la etiqueta se pone entero desde el primer fotograma (solo se
  anima cuánto se ve), y por eso los tests pueden leerlo sin esperar. El
  `Tween` en curso se guarda en un meta de la propia etiqueta para poder
  cancelarlo si llega un mensaje nuevo antes de terminar el anterior.

Los sonidos siguen el mismo reparto: `MainGame.gd` decide cuándo suena
qué, y todo pasa por `_sonar()`, que respeta el ajuste de sonido. El
bordón de ambiente sube de volumen al empezar la partida y acelera
(`pitch_scale`) mientras el tambor está caliente.

### Accesibilidad

`Ajustes.gd` es hermano de `Records.gd` en forma (mismo JSON en `user://`,
misma tolerancia a un archivo ausente o corrupto) y equivale a las opciones
`--sin-animaciones`/`--sin-sonido` de la versión de terminal, salvo que
aquí se recuerdan entre partidas. Son cuatro casillas del menú:

- **Efectos visuales reducidos** — para en seco todo lo que se mueve solo:
  engranajes, latido de los huecos candidatos, parpadeo de la luz,
  vibración de pantalla y tecleo del texto (que pasa a salir de golpe). El
  flash de fondo no desaparece, porque informa, pero entra y sale despacio
  en vez de parpadear. De paso es la opción para una máquina modesta: con
  ella no se repinta nada por fotograma.
- **Texto grande** — sube `theme.default_font_size` y, con él, los
  `theme_override_font_sizes` que la escena traía.
- **Alto contraste** — acerca al blanco cada color de texto (mezcla, no
  sustitución, para no perder el código de color) y cambia la paleta del
  tambor por `TamborView.PALETA_CONTRASTE`.
- **Sonido** — efectos y ambiente.

`MainGame._recordar_estilos()` recorre el árbol una sola vez al arrancar y
se apunta el color y el cuerpo de letra que cada nodo trae de la escena;
así los dos ajustes de texto se pueden deshacer sin que la escena tenga que
enumerarse a sí misma en una lista que envejecería mal.

Las casillas cambian el cuadradito del motor por una marca escrita
(`[X]`/`[ ]`, ver `MainGame._vestir_casillas()`): el icono por defecto es un
gris oscuro que sobre esta penumbra no se ve, y el color de un icono solo
puede multiplicarse, así que no hay forma de aclararlo desde el tema.

### Tests

Godot no trae un framework de tests instalado en el proyecto (ni
[GUT](https://github.com/bitwes/Gut) ni similar); en su lugar hay dos
scripts headless en `2d/tests/`:

- `test_logica.gd` — prueba `RuletaEstado` y los módulos que orquesta
  (incluidos `Dificultad`, `Records` y el desempate de `Jugador`), sin
  nodos ni escena, igual que `terminal/test_estado.py` y compañía.
- `test_escena.gd` — carga `MainGame.tscn` de verdad y simula partidas
  completas (menú y dificultad, marcar acierto y fallo, disparo seguro,
  retirada, duelo entero, impacto), esperando a que terminen los `Tween`
  y las pausas entre una acción y la siguiente: cubre el cableado de
  señales de `MainGame.gd` que el anterior no toca.

```bash
cd 2d
godot --headless --script res://tests/test_logica.gd --path .
godot --headless --script res://tests/test_escena.gd --path .
```

Ambos imprimen qué test ha fallado y por qué, y salen con exit code 1 si
algo falla (0 si todo pasa) — es el criterio que usa la CI para marcar el
job en rojo, igual que hace `coverage report --fail-under=90` en Python.

Los tests que tocan récords o ajustes escriben en archivos aparte (ver
`RUTA_RECORDS_TEST` y `RUTA_AJUSTES_TEST` en cada uno) y los borran al
terminar: **no pisan los récords ni los ajustes reales** de quien los
ejecute. Si añades un test que llame a `Records.guardar()`/`Ajustes.guardar()`
o instancie `MainGame.tscn`, redirige las rutas igual.

`test_escena.gd` desmonta la escena al terminar (`_main.free()`) y deja
pasar un rato de reloj para que el servidor de audio descarte los sonidos
que quedaran sonando: sin eso, Godot avisaría al salir de instancias sin
liberar.

## Lanzadores

| Archivo | Plataforma | Acción |
|---------|-----------|--------|
| `run.sh` | Linux / macOS | Juego en terminal (`-g` abre Godot) |
| `run.bat` | Windows | Juego en terminal (`-g` abre Godot) |

## Ampliaciones sugeridas

Consulta la **Hoja de ruta** del `README.md` para el detalle completo:
las cuatro fases de «El Tambor del Juicio» (mecánica, farol y eventos,
ambientación, y dificultad/récords/duelo) ya están en las dos versiones.
Quedan ideas sueltas como el modo «borracho» o empaquetar la versión de
terminal en un ejecutable único.

## Estructura de carpetas

```
russian-roulette-2d/
├── README.md
├── LICENSE
├── pyproject.toml
├── instalar.sh
├── instalar.bat
├── run.sh
├── run.bat
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── GUIA.md
├── terminal/
│   ├── __init__.py
│   ├── ruleta.py
│   ├── estado.py
│   ├── pistas.py
│   ├── apuestas.py
│   ├── farol.py
│   ├── eventos.py
│   ├── historial.py
│   ├── records.py
│   ├── test_ruleta.py
│   ├── test_estado.py
│   ├── test_pistas.py
│   ├── test_apuestas.py
│   ├── test_farol.py
│   ├── test_eventos.py
│   ├── test_historial.py
│   └── test_records.py
└── 2d/
    ├── project.godot
    ├── RuletaEstado.gd
    ├── TamborJuicio.gd
    ├── Pista.gd
    ├── Pistas.gd
    ├── Apuesta.gd
    ├── Farol.gd
    ├── Eventos.gd
    ├── Historial.gd
    ├── Jugador.gd
    ├── Dificultad.gd
    ├── Records.gd
    ├── Ajustes.gd
    ├── MainGame.gd
    ├── TamborView.gd
    ├── FondoTaller.gd
    ├── Vineta.gd
    ├── Maquina.gd
    ├── tests/
    │   ├── test_logica.gd
    │   └── test_escena.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
        ├── audio/          (sintetizado con synth_sfx.py)
        ├── fonts/          (Courier Prime + Special Elite, con licencias)
        └── tema/           (juicio.tres: tipografía + chapa de la interfaz)
```
