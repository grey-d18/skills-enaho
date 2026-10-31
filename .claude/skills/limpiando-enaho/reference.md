# Referencia: ENAHO para limpiando-enaho

## Base de salida: `salidas/personas_<año>.parquet`

Una fila por residente habitual (108,664 en 2024).

| Columna | Qué es |
|---|---|
| `conglome`, `vivienda`, `hogar`, `codperso` | Llaves (texto, con ceros a la izquierda) |
| `anio`, `mes` | Año y mes de la encuesta (texto) |
| `ubigeo` | Distrito, 6 dígitos (texto) |
| `departamento` | `ubigeo[:2]`. Lima es 15 y Callao 07; van separados |
| `dominio` | 1–3 costa, 4–6 sierra, 7 selva, 8 Lima Metropolitana |
| `estrato` | 1–5 urbano, 6–8 rural |
| `urbano` | 1 si `estrato <= 5` |
| `parentesco` | p203: 1 jefe, 2 cónyuge, 3 hijo/a… |
| `p204`, `p205`, `p206` | Preguntas de residencia (usadas en el filtro) |
| `sexo` | p207: 1 hombre, 2 mujer |
| `edad` | p208a, años cumplidos |
| `pobreza` | Del hogar: 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre`, `pobre_extremo` | 1 si `pobreza <= 2` / `pobreza == 1` |
| `mieperho` | Miembros del hogar |
| `factor07` | Factor de expansión del hogar |
| `facpob07` | Factor de expansión de la persona: úsalo para toda cifra de personas |

## Decisiones fijas (están en el script)

- Se leen los `.dta` con `convert_categoricals=False`, así que se trabaja con los códigos y no con las etiquetas.
- Los nombres de columna pasan a minúsculas y sin tildes; `aÑo` queda como `anio`.
- Residente habitual: `(p204==1 & p205==2) | (p204==2 & p206==1)`.
- Personas y hogares se unen con `validate="m:1"`.
- Se usa `sumaria-<año>.dta`, no `sumaria-<año>-12g.dta` (la versión de 12 grupos de gasto). El porqué está en el reference.md de `descargando-enaho`.

## Cifras de control, ENAHO 2024

| Pedido | Cifra |
|---|---|
| Pobreza nacional | 27.6 % (sumaria 27.58 %, personas 27.53 %) |
| Pobreza extrema | 5.5 % |
| Cusco | 18.5 % |
| Urbano / rural | 24.8 % / 39.3 % con la sumaria (24.7 % / 39.4 % con personas) |
| Departamentos | Cajamarca 45.0 %, Loreto 43.0 %, Puno 39.9 %, Ica 6.0 %, Moquegua 11.0 %, Madre de Dios 11.1 % |

Las cifras de hogar se calculan con la sumaria, ponderando con `factor07 × mieperho`. Las diferencias de unas décimas frente a la base de personas son esperables.

## Otras variables

Si piden una variable que no está en la base (gasto, ingreso, educación, empleo):

- La sumaria (módulo 34) trae `gashog2d` (gasto) e `inghog2d` (ingreso), anuales y por hogar. `linea` y `linpe` son las líneas de pobreza per cápita mensuales.
- Educación es el módulo 03 (`enaho01a-<año>-300.dta`) y empleo el 05 (`enaho01a-<año>-500.dta`). Se unen por las cuatro llaves de persona con `validate="1:1"`.
- Verifica los nombres en el `Diccionario<año>.pdf` que viene en cada zip. No los adivines.
- Si una variable debe quedar en la base de forma permanente, propón el cambio en `scripts/limpiar.py` en vez de calcularla aparte cada vez.
