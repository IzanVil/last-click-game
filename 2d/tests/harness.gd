extends RefCounted
## Aserciones minimas compartidas por los tests de 2d/tests/.
##
## Sin addons a proposito, igual que terminal/ usa solo unittest de la
## stdlib: un contador de comprobaciones, una lista de fallos y un
## resumen que devuelve el exit code que espera la CI.

var _fallos: Array[String] = []
var _pasadas := 0


func ok(condicion: bool, que: String) -> void:
	if condicion:
		_pasadas += 1
	else:
		_fallos.append(que)


func igual(obtenido: Variant, esperado: Variant, que: String) -> void:
	ok(obtenido == esperado, "%s | obtenido: %s | esperado: %s" % [que, obtenido, esperado])


## Compara floats con tolerancia, para las comprobaciones de geometria.
func cerca(obtenido: float, esperado: float, que: String, tolerancia := 0.001) -> void:
	ok(
		absf(obtenido - esperado) <= tolerancia,
		"%s | obtenido: %f | esperado: %f (+-%f)" % [que, obtenido, esperado, tolerancia]
	)


## Imprime el resultado y devuelve el exit code (0 si paso todo).
func resumen(num_tests: int) -> int:
	if _fallos.is_empty():
		print("\nOK: %d comprobaciones en %d tests." % [_pasadas, num_tests])
		return 0

	print("\nFALLOS (%d):" % _fallos.size())
	for fallo in _fallos:
		print("  - %s" % fallo)
	print("\n%d comprobaciones pasaron, %d fallaron." % [_pasadas, _fallos.size()])
	return 1
