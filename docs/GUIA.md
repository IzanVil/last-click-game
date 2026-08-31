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
   sobrevividos, faroles lanzados/acertados, eventos sufridos) y se cierra
   con un **epílogo**: uno de ocho finales alternativos elegido a partir de
   esos mismos números (`ambiente.epilogo()`), sin azar de por medio, de
   modo que la misma partida siempre acaba con el mismo texto.
   En la terminal, además, hay un **modo a oscuras** opcional
   (`--oscuridad`) en el que el tambor solo muestra los huecos que el
   jugador ha disparado o faroleado él mismo; los candidatos que dejan las
   pistas no se resaltan.
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

- Archivos, en tres capas:
  - **Lógica pura** (sin `input()`/`print()`, igual de fácil de testear que
    `RuletaEstado.gd` en la versión Godot): `terminal/estado.py`,
    `terminal/pistas.py`, `terminal/apuestas.py`, `terminal/farol.py`,
    `terminal/eventos.py`, `terminal/historial.py`, `terminal/records.py`
    y `terminal/ambiente.py` (texto narrativo: frases de ambiente,
    carteles y finales alternativos).
  - **Primitivas de terminal**, que no saben nada del juego:
    `terminal/efectos.py` (pantalla, cursor, pausas, tecleo letra a letra,
    timbre, repintado de un bloque en el sitio) y `terminal/entrada.py`
    (teclado en crudo con `termios`/`msvcrt`).
  - **Interfaz**: `terminal/ruleta.py`, que orquesta las otras dos y no
    lleva ninguna regla del juego.
- Dependencias: **ninguna** (solo la librería estándar de Python 3.11+).
- Ejecución: `./run.sh`, o directamente `python3 terminal/ruleta.py`. Admite
  `--dificultad {facil,normal,dificil}`, `--huecos N`/`--marcas N` (pisan
  al preset), `--duelo` (modo duelo, ver `jugar_duelo()`), `--oscuridad`
  (modo a oscuras), `--sin-animaciones` y `--sin-sonido` (ver `efectos.py`),
  `--records` (muestra los récords guardados y no juega) y `--version`.
  `main()` es el entry point real (`ruleta = "terminal.ruleta:main"` en
  `pyproject.toml`), que envuelve `jugar()`/`jugar_duelo()` para capturar
  Ctrl+C y configura los efectos según los flags.
- Interactúa por entrada/salida estándar con interfaz en colores y tambor
  ASCII, animado y con teclado en crudo cuando hay una terminal delante.

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
  `elegir_hueco`/`impacto`/`retirada` tal cual (con los datos del
  jugador activo en cada turno); lo único propio del modo duelo es
  `escena_duelo()` (añade de quién es el turno y el estado del rival) y
  `resultado_duelo()` (compara días y, en empate, puntos).

`ruleta.py` importa estos módulos con un `try/except` (relativo si se
usa como paquete instalado, absoluto si se ejecuta como script suelto): si
añades un módulo de lógica más, sigue el mismo patrón de import.

### Cómo modificar la presentación

- `efectos.AJUSTES` (un dataclass `Ajustes` con `animaciones` y `sonido`)
  es el interruptor global; `main()` lo fija una sola vez con
  `efectos.configurar()` a partir de `--sin-animaciones`/`--sin-sonido`.
  **Todo lo que duerme, parpadea o suena pasa por ahí**: con las
  animaciones apagadas `pausa()`, `repintar()` y `limpiar()` no hacen nada
  y `escribir()` imprime la línea de una vez, así que la partida se
  convierte en un registro que va bajando (lo que quieren los tests, CI y
  un *pipe*). El sonido se apaga solo si la salida no es una terminal.
- `efectos.limpiar()` usa códigos ANSI (`ir arriba` + `borrar hacia
  abajo`) en vez de lanzar `clear`/`cls`: se llama en cada fotograma, y
  así no parpadea ni levanta un proceso hijo por frame.
- `efectos.repintar(fotogramas, retardo, factor)` es la única animación:
  pisa en el sitio el bloque que ya hay en pantalla (todos los fotogramas
  deben medir lo mismo de alto, y el último es el estado en reposo).
  `factor` por debajo de 1 acelera (el latido) y por encima frena (el
  giro). `ruleta.latido()` y `ruleta.animar_giro()` solo montan los
  fotogramas con `ruleta.bloque_tablero()`.
- `efectos.PATRONES_SONIDO` define cada sonido como la lista de esperas
  entre pitidos: el timbre de la terminal (BEL) no tiene tono, así que lo
  que distingue un sonido de otro es el ritmo.
- `entrada.seleccionar(huecos, pintar)` es el selector con flechas; recibe
  una función que dibuja la pantalla con un hueco resaltado. Si
  `entrada.modo_tecla_disponible()` dice que no (no hay terminal, o falta
  `termios`/`msvcrt`), `ruleta.elegir_hueco()` cae a `elegir_posicion()`,
  el número tecleado de siempre. Añadir una tecla es una rama más en el
  bucle de `seleccionar()` y, si es una secuencia de escape, una entrada
  en `_FLECHAS_UNIX`/`_FLECHAS_WINDOWS`.
- `ambiente.MENSAJES_DIA` son las frases de ambiente (la primera se
  reserva para el día 1), `ambiente.TITULOS_EVENTO` los títulos de los
  carteles y `ambiente.epilogo()` elige el final: sus ramas van de lo más
  específico a lo más general, así que un final nuevo se inserta por
  encima de los cierres genéricos. `ambiente.cartel()` monta cualquier
  cartel enmarcado.
- `ruleta.Tablero` agrupa lo que hace falta para pintar un turno (huecos,
  estados, pistas, bitácora y el hueco resaltado); `ruleta.tambor_ascii()`
  lo dibuja y `ruleta.bloque_tablero()` le añade la bitácora, que siempre
  ocupa el mismo alto para poder repintarse en el sitio.
  `ruleta.ANCHO_PANEL`, `ruleta.HUECOS_LATIDO` (cuántos huecos sin probar
  encienden el latido) y `ruleta.VUELTAS_GIRO` afinan el resto.
- `historial.Historial.registrar_accion()` alimenta la bitácora; el `tipo`
  de cada `Accion` es solo una etiqueta que `ruleta.COLORES_ACCION`
  traduce a un color, y `historial.MAX_ACCIONES` cuántas se conservan.

### Tests

Hay una batería de pruebas por módulo (`test_estado.py`, `test_pistas.py`,
`test_apuestas.py`, `test_farol.py`, `test_eventos.py`, `test_historial.py`,
`test_records.py`, `test_ambiente.py`, `test_efectos.py`, `test_entrada.py`,
`test_ruleta.py`). Tres cosas que hay que respetar al escribir tests
nuevos de la interfaz:

- Cualquier test que llame a `jugar()`/`jugar_duelo()` debe parchear
  `ruleta.records.cargar` y `ruleta.records.guardar` (ver el decorador
  `_parchear_records` en `test_ruleta.py`): si no, leerían/escribirían el
  archivo de récords real del usuario que ejecuta los tests.
- `test_ruleta.setUpModule()` apaga los efectos con
  `efectos.configurar(animaciones=False, sonido=False)` —el mismo
  interruptor que `--sin-animaciones`— para que ningún test duerma ni
  escriba códigos de escape en la terminal de quien los lanza, y parchea
  `entrada.modo_tecla_disponible` a `False`. Ese segundo parche importa:
  `sys.stdin` **sí** es una terminal cuando los tests se lanzan a mano, así
  que sin él el selector se quedaría esperando una flecha que no llega.
  Un test que llame a `ruleta.main()` vuelve a encender los efectos (main
  los configura según los flags), así que `TestMain` los reapaga en su
  `tearDown`.
- Los tests que comprueban texto en pantalla parchean `builtins.print`; con
  las animaciones apagadas, `efectos.escribir()` y `efectos.pintar_bloque()`
  también salen por ahí, así que se capturan igual.

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
- Aspecto: `2d/Paleta.gd` (los cinco colores del juego) y `2d/Icono.gd`
  (los cuatro iconos del HUD, dibujados con `_draw()`).
- Ajustes: `2d/Ajustes.gd` (efectos reducidos, texto grande, alto
  contraste, sonido, volúmenes y pantalla completa, en
  `user://ajustes.json`).

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

### Las cuatro pantallas

`MainGame.gd` no cambia de escena: mantiene cuatro `VBoxContainer` dentro
del mismo panel y enseña uno cada vez, desde un único sitio
(`_mostrar(Pantalla)`), que además ajusta lo que las acompaña (el rótulo,
la música, el foco del teclado). Un solo camino para cambiar de pantalla
es lo que evita que la interfaz se quede a medias.

- **Menú** — título, subtítulo, dificultad, duelo y los botones de nueva
  partida y récords.
- **Récords** — la tabla de las cinco mejores partidas (`Records.mejores`,
  con su fecha) más el resumen de siempre. Las columnas se alinean
  rellenando con espacios porque la tipografía es monoespaciada: para cinco
  filas no hace falta un `Tree`.
- **Partida** — HUD arriba, tambor, pistas, campo y botones, y la bitácora
  de las últimas cinco acciones abajo.
- **Final** — rótulo (`HAS MUERTO` o `TE RETIRAS CON VIDA`), resumen
  narrativo y los botones de reintentar (repite dificultad y nombres, sin
  pasar por el menú) y volver.

Sobre todo eso hay dos paneles superpuestos, la **ayuda** (tecla H) y los
**ajustes** (tecla Escape). Se atienden en `_unhandled_input` y no en
`_input` a propósito: así escribir una "h" en el campo del número no abre
nada, porque el `LineEdit` se queda el evento antes. El panel de ajustes no
detiene el árbol (`get_tree().paused`): aquí no corre ningún reloj contra
el jugador, así que lo único que hace falta congelar es el decorado.

### El tambor

`TamborView.gd` dibuja un cilindro visto en ángulo, no un disco plano: las
posiciones de los huecos se aplastan en vertical (`PERSPECTIVA`) y por
debajo se pinta el canto con sus estrías (`PROFUNDIDAD`). Tres detalles que
no son evidentes:

- Lo que gira es `_giro` (el ángulo de los huecos), **no** `rotation` del
  nodo. Si girase el nodo, giraría también el escorzo y los números: lo que
  rueda es el tambor dentro de su marco, no la cámara alrededor.
- Los huecos se dibujan ordenados por su `y`, de atrás hacia delante, para
  que los de abajo tapen a los de arriba. Sin eso se lee como un dibujo
  plano.
- El giro da siempre un número **entero** de vueltas, así que cada hueco
  acaba donde empezó. Es dramatismo, no un sorteo: la bala se mueve por su
  patrón (`TamborJuicio`), y eso no lo decide una animación.

El ratón entra por `_gui_input`: al pasar por encima se ilumina el hueco,
al hacer clic se emite `hueco_pulsado`, y quien decide qué significa ese
clic es `MainGame.gd` (escribe el número en el campo, que es el mismo sitio
donde acaba si se teclea a mano).

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
qué, y todo pasa por `_sonar()`, que respeta el ajuste de sonido.

La música son **dos pistas de la misma duración** que se lanzan a la vez y
en fase (`musica_base` y `musica_tension`): la primera suena siempre y la
segunda entra por encima cuando quedan tres huecos o menos por probar. Las
dos suben de volumen al empezar la partida y aceleran (`pitch_scale`)
conforme el tambor se vacía, en `_ajustar_musica()`. Van por un bus de
audio propio, separado del de los efectos, que es lo que permite los dos
deslizadores del menú de ajustes; los buses se crean por código en
`_preparar_buses()` para que quede a la vista de quien lea el archivo.

En **headless** la música no se lanza siquiera: no hay dispositivo de audio
y una reproducción en bucle no termina nunca por sí sola, así que seguiría
viva al cerrarse el motor y Godot avisaría de recursos sin liberar — un
`ERROR:` en el log que la CI toma, con razón, por un fallo.

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
- **Sonido** — efectos y música.
- **Música** y **Efectos** — un deslizador por bus de audio. A 0 el bus se
  silencia en vez de bajarse: `linear_to_db(0)` sería `-inf`.
- **Pantalla completa** — ventana o pantalla completa.

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
  completas (menú, récords, ajustes, ayuda, dificultad, elección con el
  ratón, marcar acierto y fallo, disparo seguro, retirada, duelo entero,
  impacto y reintento), esperando a que terminen los `Tween` y las pausas
  entre una acción y la siguiente: cubre el cableado de señales y el paso
  entre pantallas de `MainGame.gd`, que el anterior no toca. Las esperas se
  calculan a partir de las constantes de `MainGame` (`DURACION_GIRO`,
  `PAUSA_FIN_PARTIDA`...) para que no se descuadren si alguna cambia.

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

### Las capturas del README

Las imágenes de `docs/img/` las genera `2d/tools/capturas.gd`, que juega una
partida guionizada y fotografía cada pantalla. **No es un test** (no
comprueba nada) y por eso vive fuera de `2d/tests/`, aunque la CI lo parsea
igual con `--check-only`:

```bash
godot --resolution 1728x1296 --fixed-fps 60 \
    --script res://tools/capturas.gd --path 2d
```

Los tres detalles que importan, y que están explicados también en la
cabecera del propio script: se pide una **ventana más grande** que la de
juego (el proyecto escala el lienzo, así que la interfaz sale con el doble
de píxeles y el recorte queda nítido), se fuerza un **delta fijo**
(`--fixed-fps`, porque una ventana sin foco no avanza al mismo ritmo que
los temporizadores del script y las capturas pillarían animaciones a
medias) y cada imagen se **recorta al panel** de su pantalla, para que no
sea cuatro quintas partes de fondo negro. El script deja los PNG en
`user://`; de ahí se copian a `docs/img/`.

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
│   ├── GUIA.md
│   └── img/
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
│   ├── ambiente.py
│   ├── efectos.py
│   ├── entrada.py
│   ├── test_ruleta.py
│   ├── test_estado.py
│   ├── test_pistas.py
│   ├── test_apuestas.py
│   ├── test_farol.py
│   ├── test_eventos.py
│   ├── test_historial.py
│   ├── test_records.py
│   ├── test_ambiente.py
│   ├── test_efectos.py
│   └── test_entrada.py
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
    ├── Paleta.gd
    ├── Icono.gd
    ├── tests/
    │   ├── test_logica.gd
    │   └── test_escena.gd
    ├── tools/
    │   └── capturas.gd
    ├── scenes/
    │   └── MainGame.tscn
    └── assets/
        ├── audio/          (sintetizado con synth_sfx.py)
        ├── fonts/          (Courier Prime + Special Elite, con licencias)
        └── tema/           (juicio.tres: tipografía + chapa de la interfaz)
```
