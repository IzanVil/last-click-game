class_name Dificultad
extends RefCounted

const PRESETS := {
	"facil": {"huecos": 10, "marcas": 4},
	"normal": {"huecos": RuletaEstado.HUECOS, "marcas": Farol.MARCAS_INICIALES},
	"dificil": {"huecos": 6, "marcas": 2},
}

const ORDEN: Array[String] = ["facil", "normal", "dificil"]

const ETIQUETAS := {
	"facil": "Facil (10 huecos, 4 marcas)",
	"normal": "Normal (8 huecos, 3 marcas)",
	"dificil": "Dificil (6 huecos, 2 marcas)",
}


static func huecos_de(dificultad: String) -> int:
	assert(PRESETS.has(dificultad), "Dificultad desconocida: %s" % dificultad)
	return PRESETS[dificultad]["huecos"]


static func marcas_de(dificultad: String) -> int:
	assert(PRESETS.has(dificultad), "Dificultad desconocida: %s" % dificultad)
	return PRESETS[dificultad]["marcas"]


static func etiqueta_de(dificultad: String) -> String:
	assert(ETIQUETAS.has(dificultad), "Dificultad desconocida: %s" % dificultad)
	return ETIQUETAS[dificultad]
