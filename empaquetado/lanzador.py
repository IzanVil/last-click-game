"""Punto de entrada para el ejecutable de un solo fichero (pyinstaller).

Existe porque pyinstaller no puede partir de `terminal/ruleta.py` a
secas: lo analizaria como script suelto, el `from . import ...` de
arriba del modulo fallaria por no haber paquete, y el fallback
`import ambiente` tampoco se resolveria en tiempo de analisis, asi que
el binario saldria sin los modulos hermanos dentro.

Importando el paquete se arrastra todo lo que `terminal.ruleta` usa. Es
el mismo `main()` que llama el comando `ruleta` de pyproject.toml.
"""

import sys

from terminal.ruleta import main

if __name__ == "__main__":
    sys.exit(main())
