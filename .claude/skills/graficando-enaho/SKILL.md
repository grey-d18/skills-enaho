---
name: graficando-enaho
description: Grafica el porcentaje de personas que viven en hogares pobres según la ENAHO del INEI, por área (urbano y rural), sexo o grupo de edad, en barras ponderadas con el factor de expansión. Úsala cuando pidan graficar, un gráfico o barras de la pobreza, o comparar la pobreza urbana y rural, entre hombres y mujeres o por edad.
argument-hint: [area|sexo|edad]
---

# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Elige el corte según el pedido: `area` (urbano y rural), `sexo` o `edad`. Si piden varios, corre el script una vez por cada uno. Usa el año que pidió el usuario, o 2024 si no pidió ninguno.
3. Corre exactamente, desde la raíz del repositorio:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <corte> --anio <año>`
   No dibujes el gráfico con otro código ni cambies su diseño.
4. Si el script termina con error, muestra el mensaje y detente.
5. Responde con la ruta de la figura (`figuras/pobreza_por_<corte>_<año>.png`) y las cifras que imprimió el script. No recalcules las cifras por tu cuenta.
6. La pobreza es del hogar. Escribe "X % de las mujeres vive en hogares pobres" o "pertenece a hogares pobres", nunca "las mujeres son más pobres" ni "los niños son más pobres".
7. Esta skill solo grafica la pobreza monetaria por área, sexo o edad. Si piden otro indicador u otro corte (por ejemplo, departamentos), dilo y no improvises un gráfico. Las reglas de diseño están en [reference.md](reference.md).
