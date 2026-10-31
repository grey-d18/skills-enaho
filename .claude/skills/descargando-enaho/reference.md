# Referencia: descargando-enaho

## Años y módulos

| Año | Código INEI | URL |
|---|---|---|
| 2024 | 966 | `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo{34,02}.zip` |

| Módulo | Contenido | Archivo a usar | Una fila por |
|---|---|---|---|
| 34 | Sumaria: gasto, ingreso y pobreza | `sumaria-2024.dta` | hogar (33,691) |
| 02 | Características de los miembros | `enaho01-2024-200.dta` | persona (117,721) |

Cada zip trae además el `Diccionario2024.pdf` y la ficha técnica. El 02 incluye también las tablas de ocupaciones (`enaho_tabla_ciuo_88.dta` y `enaho_tabla_cno_2015.dta`).

Para agregar un año, verifica su código en el portal de microdatos del INEI, súmalo a `CODIGOS` en `scripts/descargar.py` y prueba que el script descargue y encuentre los `.dta`.

## Qué sumaria usar

El módulo 34 trae dos sumarias. Esto es lo que se comprobó con los datos de 2024:

| | `sumaria-2024.dta` | `sumaria-2024-12g.dta` |
|---|---|---|
| Hogares | 33,691 | 33,691 (los mismos) |
| Columnas | 163 | 242 |
| Pobreza / extrema | 27.58 % / 5.50 % | 27.58 % / 5.50 % (`pobreza` idéntica hogar por hogar) |
| Gasto e ingreso totales | `gashog*`, `inghog*` | Diferencias menores a 1 sol (redondeo) |
| Gasto por grupos | 8 grupos clásicos | 12 grupos más detallados |

**Regla:** se usa siempre `sumaria-AAAA.dta`. Sirve para pobreza, gasto o ingreso total y series entre años. Es la que usa el do-file oficial del INEI para el gasto real de 2014 a 2024, que viene dentro del zip (`ConstVarGasto-Metodologia actualizada.zip`). Este repositorio no usa `sumaria-AAAA-12g.dta`.

**El riesgo de la 12g:** 44 variables tienen el mismo nombre en las dos versiones pero distinta etiqueta. En 25 de ellas (los `gru*hd*`) los valores también cambian. Por ejemplo:

| Variable | En `sumaria-2024.dta` | En `sumaria-2024-12g.dta` |
|---|---|---|
| `gru11hd` | alimentos | alimentos dentro del hogar |
| `gru21hd` | vestido y calzado | bebidas alcohólicas y estupefacientes |
| `gru81hd` | otros bienes y servicios | comunicaciones |

Un código escrito para la sumaria de 8 grupos y corrido por error sobre la 12g no falla: da cifras equivocadas sin avisar. Con `gru21hd`, el gasto promedio por hogar sale 862.3 soles en vestido (8 grupos) y 20.9 soles en bebidas alcohólicas (12g). Al unir las dos sin cuidado, pandas crea `gru21hd_x` y `gru21hd_y`, que no dicen de qué archivo viene cada una. Por eso el script solo acepta `sumaria-AAAA.dta`.
