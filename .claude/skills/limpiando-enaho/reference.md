# Referencia: ENAHO para limpiando-enaho

## Base de salida: `salidas/personas_<año>.parquet`

Una fila por miembro del hogar según el INEI (109,842 en 2024, igual a la suma de `mieperho`).

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
| `p205` | ¿Estuvo ausente 30 días o más? (1 sí, 2 no). Todos son miembros (`p204 = 1`), presentes o ausentes |
| `sexo` | p207: 1 hombre, 2 mujer |
| `edad` | p208a, años cumplidos |
| `pobreza` | Del hogar: 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre`, `pobre_extremo` | 1 si `pobreza <= 2` / `pobreza == 1` |
| `mieperho` | Miembros del hogar según el INEI (coincide con las filas de cada hogar) |
| `factor07` | Factor de expansión del hogar |
| `facpob07` | Factor de expansión de la persona: úsalo para toda cifra de personas |

## Decisiones fijas (están en el script)

- Se leen los `.dta` con `convert_categoricals=False`, así que se trabaja con los códigos y no con las etiquetas.
- Los nombres de columna pasan a minúsculas y sin tildes; `aÑo` queda como `anio`.
- **Método del INEI:** la base incluye a toda persona con `p204 == 1` (miembro del hogar), esté presente o ausente. Son exactamente las personas que el INEI cuenta en `mieperho` y entre las que reparte el gasto del hogar para decidir si es pobre. El script lo verifica hogar por hogar.
- No se usa el filtro de residentes habituales `(p204==1 & p205==2) | (p204==2 & p206==1)`: deja fuera a miembros ausentes que el INEI sí cuenta y da 108,664 personas, con una pobreza de 27.53 % en vez de 27.58 %.
- Personas y hogares se unen con `validate="m:1"`.
- Se usa `sumaria-<año>.dta`, no `sumaria-<año>-12g.dta` (la versión de 12 grupos de gasto). El porqué está en el reference.md de `descargando-enaho`.

## Cifras de control, ENAHO 2024

| Pedido | Cifra |
|---|---|
| Pobreza nacional | 27.6 % (27.58 % con la sumaria y con la base de personas) |
| Pobreza extrema | 5.5 % |
| Cusco | 18.5 % |
| Urbano / rural | 24.8 % / 39.3 % |
| Departamentos | Cajamarca 45.0 %, Loreto 43.0 %, Puno 39.9 %, Ica 6.0 %, Moquegua 11.0 %, Madre de Dios 11.1 % |

Ponderar la base de personas con `facpob07` da lo mismo que la sumaria con `factor07 × mieperho`: cada persona hereda el factor de su hogar y cada hogar tiene `mieperho` filas.

**Terminología:** la pobreza es del hogar. Las cifras son el "% de personas que viven en hogares pobres". Por sexo o edad: "X % de las mujeres vive en hogares pobres", nunca "las mujeres son más pobres", porque la medición no capta la desigualdad dentro del hogar.

## Otras variables

Si piden una variable que no está en la base (gasto, ingreso, educación, empleo):

- La sumaria (módulo 34) trae `gashog2d` (gasto) e `inghog2d` (ingreso), anuales y por hogar. `linea` y `linpe` son las líneas de pobreza per cápita mensuales.
- Educación es el módulo 03 (`enaho01a-<año>-300.dta`) y empleo el 05 (`enaho01a-<año>-500.dta`). Se unen por las cuatro llaves de persona con `validate="1:1"`.
- Verifica los nombres en el `Diccionario<año>.pdf` que viene en cada zip. No los adivines.
- Si una variable debe quedar en la base de forma permanente, propón el cambio en `scripts/limpiar.py` en vez de calcularla aparte cada vez.
