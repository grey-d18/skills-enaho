# Referencia: graficando-enaho

## Reglas de diseño (fijas en `scripts/graficar.py`)

- Siempre se pondera con `facpob07`: es el porcentaje de personas, no de encuestados.
- Título, eje y pie usan la terminología de hogar: «Personas en hogares pobres por …».
- Barras horizontales que empiezan en cero.
- Área y sexo se ordenan de mayor a menor. La edad mantiene el orden de los grupos.
- Un solo color para todas las barras (`#2a78d6`). El texto va en tinta oscura, nunca del color de la barra.
- El valor va escrito al final de cada barra y no hay grilla, porque chocaría con los valores.
- El título dice qué y cuándo: «Personas en hogares pobres por …, Perú 2024».
- Al pie, solo: «Fuente: INEI, ENAHO 2024.»
- PNG a 200 dpi en `figuras/pobreza_por_<corte>_<año>.png`.

## Cortes

| Corte | Variable | Grupos |
|---|---|---|
| `area` | `urbano` (estrato ≤ 5) | Urbano, Rural |
| `sexo` | `sexo` (p207) | Hombre (1), Mujer (2) |
| `edad` | `edad` (p208a) | 0–14, 15–29, 30–44, 45–64, 65+ |

## Cifras esperadas, ENAHO 2024 (método del INEI, facpob07)

% de personas que viven en hogares pobres:

| Corte | Valor |
|---|---|
| Área | Rural 39.3 %, Urbano 24.8 % |
| Sexo | Mujer 27.8 %, Hombre 27.4 % |
| Edad | 0–14: 37.7 %, 15–29: 25.9 %, 30–44: 28.0 %, 45–64: 21.2 %, 65+: 22.8 % |

La base de personas cuenta a los mismos miembros que el INEI (`mieperho`), así que estas cifras coinciden con las de la sumaria y con la tabla de evaluación del curso.

## Terminología y límites

- La pobreza monetaria es una condición del **hogar**: todos sus miembros comparten la misma. Se escribe "X % de las mujeres vive en hogares pobres", nunca "las mujeres son más pobres".
- La medición no capta la desigualdad dentro del hogar. La diferencia entre hombres y mujeres (0.4 puntos) solo refleja en qué hogares viven unos y otras.
- El INEI reparte el gasto en partes iguales entre los miembros, sin distinguir adultos de niños. Los hogares con muchos niños tienen menos gasto por persona, y eso explica en parte el 37.7 % de 0–14 años.
- Las cifras no llevan margen de error. Una diferencia pequeña entre grupos puede no ser estadísticamente significativa.

## Antes de graficar

- La base solo existe si pasó la validación de `limpiando-enaho`, que ya compara la pobreza con la cifra oficial del INEI.
- El script se detiene si alguna persona queda sin grupo.
