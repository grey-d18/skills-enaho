---
name: mapeando-enaho
description: Mapea el porcentaje de personas que viven en hogares pobres según la ENAHO del INEI por departamento, uniendo por código de ubigeo con los límites de los 25 departamentos del Perú. Úsala cuando pidan un mapa de la pobreza, la pobreza por departamento o región en un mapa, o comparar departamentos geográficamente.
argument-hint: [año]
---

# Mapear la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Corre exactamente, desde la raíz del repositorio (sin año, usa 2024):
   `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --anio $0`
   El script baja los límites departamentales a `datos/` si faltan. No dibujes el mapa con otro código ni cambies su diseño.
3. Si el script termina con error, muestra el mensaje y detente. Nunca entregues un mapa con departamentos en blanco.
4. Responde con la ruta del mapa (`mapas/pobreza_departamento_2024.png`) y las cifras que imprimió el script. No recalcules las cifras por tu cuenta.
5. La pobreza es del hogar. Escribe "X % de las personas de Cajamarca vive en hogares pobres", nunca "Cajamarca tiene 45 % de pobres" sin aclarar que es el porcentaje de personas.
6. Esta skill solo mapea la pobreza monetaria por departamento. Si piden otro nivel (provincia, distrito) u otro indicador, dilo y no improvises. Las reglas están en [reference.md](reference.md).
