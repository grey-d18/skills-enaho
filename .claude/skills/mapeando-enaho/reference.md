# Referencia: mapeando-enaho

## Reglas (fijas en `scripts/mapear.py`)

- **Unión por código, nunca por nombre.** `departamento` (= `ubigeo[:2]`, texto con cero a la izquierda) se une con `FIRST_IDDP` del GeoJSON, con `validate="1:1"`. Los nombres del GeoJSON vienen en mayúsculas y sin tildes («APURIMAC»), y la ENAHO no trae nombres.
- **Exige los 25 departamentos con dato.** Si falta un departamento en cualquiera de los dos lados, el script se detiene y no genera el mapa.
- Lima (15) y Callao (07) van separados.
- Se pondera con `facpob07`.
- **Escala:** cinco clases de 10 puntos (0–10, 10–20, 20–30, 30–40, 40–50 %), un solo tono azul de claro a oscuro, desde 0. Nunca arcoíris. Si algún valor sale de 0–50 %, el script se detiene.
- La leyenda lleva la unidad: «% de personas que viven en hogares pobres».
- Se rotulan solo los 3 departamentos más altos y los 3 más bajos. Las 25 cifras van en la tabla que imprime el script.
- El título dice qué y cuándo: «Personas en hogares pobres por departamento, Perú 2024».
- Al pie, solo «Fuente: INEI, ENAHO 2024.»
- PNG a 200 dpi en `mapas/pobreza_departamento_<año>.png`.

## Límites departamentales

`datos/peru_departamental_simple.geojson` (140 KB, EPSG:4326), del repositorio del curso:

`https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson`

Trae 25 departamentos con `FIRST_IDDP` de «01» a «25». Se descarga la primera vez y no se sube a git.

## Cifras esperadas, ENAHO 2024

% de personas que viven en hogares pobres:

| Más alto | | Más bajo | |
|---|---|---|---|
| Cajamarca | 45.0 % | Ica | 6.0 % |
| Loreto | 43.0 % | Moquegua | 11.0 % |
| Puno | 39.9 % | Madre de Dios | 11.1 % |

Si un departamento sale en blanco, la unión falló, casi siempre porque se unió por nombre o porque el código perdió el cero.
