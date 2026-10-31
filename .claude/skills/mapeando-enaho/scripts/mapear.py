# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow", "geopandas", "matplotlib"]
# ///
"""Mapea el % de personas que viven en hogares pobres (ENAHO) por departamento.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024

Lee salidas/personas_<anio>.parquet (de limpiando-enaho), pondera con facpob07,
une con los límites departamentales por código (ubigeo[:2] = FIRST_IDDP), exige
los 25 departamentos con dato, imprime la tabla y guarda
mapas/pobreza_departamento_<anio>.png a 200 dpi.
"""

import argparse
import sys
import urllib.request
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
               "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson")

# Nombres solo para las etiquetas; la unión es siempre por código
DEPARTAMENTOS = {
    "01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
    "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
    "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
    "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
    "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali",
}

# Cinco clases de 10 puntos, un solo tono de claro a oscuro, desde 0
CLASES = [0, 10, 20, 30, 40, 50]
COLORES = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
DPI = 200
EXTREMOS = 3  # se rotulan los 3 más altos y los 3 más bajos


def leer_limites(ruta: Path) -> gpd.GeoDataFrame:
    if not ruta.exists():
        print(f"Descargando límites departamentales a {ruta}")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL_GEOJSON, ruta)
    return gpd.read_file(ruta)[["FIRST_IDDP", "geometry"]]


def tabular(base: pd.DataFrame) -> pd.DataFrame:
    """% de personas que viven en hogares pobres por departamento, ponderado con facpob07."""
    t = (base.assign(pobres=base["pobre"] * base["facpob07"])
         .groupby("departamento")
         .agg(pobres=("pobres", "sum"), poblacion=("facpob07", "sum")))
    t["pobreza"] = t["pobres"] / t["poblacion"] * 100
    t["nombre"] = t.index.map(DEPARTAMENTOS)
    return t.sort_values("pobreza", ascending=False)


def mapear(mapa: gpd.GeoDataFrame, anio: int, destino: Path) -> None:
    mapa = mapa.assign(clase=pd.cut(mapa["pobreza"], CLASES, labels=False, include_lowest=True))
    fig, ax = plt.subplots(figsize=(6.5, 8.2))
    mapa.plot(ax=ax, color=[COLORES[c] for c in mapa["clase"]], edgecolor="white", linewidth=0.6)
    ax.set_axis_off()

    orden = mapa.sort_values("pobreza", ascending=False)
    for _, fila in pd.concat([orden.head(EXTREMOS), orden.tail(EXTREMOS)]).iterrows():
        punto = fila.geometry.representative_point()
        ax.annotate(f"{fila['nombre']}\n{fila['pobreza']:.1f} %", (punto.x, punto.y),
                    ha="center", va="center", fontsize=8, fontweight="bold", color=TINTA,
                    path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])

    leyenda = [Patch(facecolor=c, edgecolor="none", label=f"{a}–{b}")
               for c, a, b in zip(COLORES, CLASES, CLASES[1:])]
    ax.legend(handles=leyenda, title="% de personas que viven\nen hogares pobres",
              loc="lower left", frameon=False, fontsize=8, title_fontsize=8,
              labelcolor=TINTA_2, alignment="left")

    fig.suptitle(f"Personas en hogares pobres por departamento, Perú {anio}",
                 x=0.03, ha="left", fontsize=12, fontweight="bold", color=TINTA)
    fig.text(0.03, 0.01, f"Fuente: INEI, ENAHO {anio}.",
             ha="left", va="bottom", fontsize=8, color=TINTA_2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=DPI, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anio", type=int, default=2024)
    parser.add_argument("--datos", type=Path, default=Path("datos"))
    parser.add_argument("--salidas", type=Path, default=Path("salidas"))
    parser.add_argument("--mapas", type=Path, default=Path("mapas"))
    args = parser.parse_args()

    ruta = args.salidas / f"personas_{args.anio}.parquet"
    if not ruta.exists():
        sys.exit(f"Falta {ruta}. Usa primero la skill limpiando-enaho.")
    base = pd.read_parquet(ruta, columns=["departamento", "pobre", "facpob07"])
    tabla = tabular(base)

    # Unión por código, nunca por nombre; exige 25 departamentos con dato
    limites = leer_limites(args.datos / "peru_departamental_simple.geojson")
    mapa = limites.merge(tabla, left_on="FIRST_IDDP", right_index=True,
                         how="outer", validate="1:1", indicator=True)
    problemas = []
    if len(limites) != 25:
        problemas.append(f"El GeoJSON trae {len(limites)} departamentos, no 25")
    if (sin_dato := mapa.loc[mapa["_merge"] == "left_only", "FIRST_IDDP"].tolist()):
        problemas.append(f"Departamentos sin dato de la ENAHO: {sin_dato}")
    if (sin_limite := mapa.loc[mapa["_merge"] == "right_only", "FIRST_IDDP"].tolist()):
        problemas.append(f"Códigos de la ENAHO sin límite en el GeoJSON: {sin_limite}")
    if not mapa["pobreza"].between(CLASES[0], CLASES[-1]).all():
        problemas.append(f"Hay valores fuera de la escala {CLASES[0]}–{CLASES[-1]} %")
    if problemas:
        sys.exit("No se mapeó:\n  " + "\n  ".join(problemas))

    destino = args.mapas / f"pobreza_departamento_{args.anio}.png"
    mapear(mapa.drop(columns="_merge"), args.anio, destino)

    print(f"% de personas que viven en hogares pobres por departamento, {args.anio}:")
    for codigo, r in tabla.iterrows():
        print(f"  {codigo} {r['nombre']:<14} {r['pobreza']:5.1f} %")
    print(f"\nMapa: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
