# fonts

Tipografías de máquina de escribir que dan la ambientación noir/steampunk
de la versión gráfica. Las dos son **de terceros** y se redistribuyen aquí
al amparo de sus licencias, cuyo texto completo está en esta misma carpeta.

| Archivo | Familia | Uso en el juego | Licencia |
|---------|---------|-----------------|----------|
| `CourierPrime-Regular.ttf` | Courier Prime | Toda la interfaz (fuente por defecto del tema) | [SIL Open Font License 1.1](CourierPrime-OFL.txt) |
| `SpecialElite-Regular.ttf` | Special Elite | Solo el título | [Apache License 2.0](SpecialElite-LICENSE.txt) |

- **Courier Prime** — © 2015 The Courier Prime Project Authors,
  <https://github.com/quoteunquoteapps/CourierPrime>. Máquina de escribir
  limpia y monoespaciada, pensada para guiones: legible en textos largos y
  con los dígitos bien alineados en el tambor.
- **Special Elite** — © 2010 Brian J. Bonislawsky DBA Astigmatic (AOETI).
  Tipografía «golpeada», con la tinta irregular de una máquina real:
  perfecta para un rótulo, incómoda para leer números pequeños. De ahí que
  se use **solo en el título**.

Ambas se obtuvieron del repositorio oficial de [Google
Fonts](https://github.com/google/fonts) (`ofl/courierprime` y
`apache/specialelite`).

> ⚖️ Al redistribuir el juego, estos dos archivos de licencia deben viajar
> con las fuentes. La OFL 1.1 además reserva el nombre de la familia: se
> puede usar y redistribuir Courier Prime tal cual, pero una versión
> **modificada** no puede seguir llamándose así.

## Cómo se aplican

`tipografia.tres` es un `Theme` con Courier Prime como `default_font`, y se
asigna al nodo raíz de `scenes/MainGame.tscn`, así que **toda** la interfaz
la hereda sin tocar nodo por nodo (`Label`, `Button`, `LineEdit`,
`OptionButton`, `CheckBox`... y también `TamborView`, que dibuja los números
del tambor con `get_theme_default_font()`).

El título es la única excepción: lleva Special Elite en un
`theme_override_fonts/font`.

Como ninguna de las dos cubre más allá del alfabeto latino y el nombre de
un jugador es texto libre, `MainGame._encadenar_respaldo_de_fuentes()`
encadena la fuente por defecto del motor como respaldo: sin ella, un
nombre en cirílico o con emoji se vería como recuadros.

`tests/test_escena.gd` comprueba todo lo anterior (que el tema esté puesto,
que los nodos lo hereden, que el título sea la excepción y que el respaldo
esté encadenado), porque un fallo de tipografía **no da error**: la
interfaz simplemente saldría con la fuente por defecto de Godot.
