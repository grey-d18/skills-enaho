# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow", "matplotlib"]
# ///
"""Grafica el % de personas que viven en hogares pobres (ENAHO) por área, sexo o edad.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area --anio 2024

Lee salidas/personas_<anio>.parquet (de limpiando-enaho, que solo la guarda si
pasó la validación), pondera con facpob07, imprime la tabla y guarda
figuras/pobreza_por_<por>_<anio>.png a 200 dpi.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

COLOR = "#2a78d6"  # un solo color para todas las barras
TINTA = "#0b0b0b"  # título, grupos y valores
TINTA_2 = "#52514e"  # ejes y fuente
DPI = 200

CORTES = {
    "area": {"titulo": "por área", "ordenar": True},
    "sexo": {"titulo": "por sexo", "ordenar": True},
    "edad": {"titulo": "por grupo de edad", "ordenar": False},  # orden natural de edad
}


def grupo(base: pd.DataFrame, por: str) -> pd.Series:
    if por == "area":
        return base["urbano"].map({1: "Urbano", 0: "Rural"})
    if por == "sexo":
        return base["sexo"].map({1: "Hombre", 2: "Mujer"})
    return pd.cut(base["edad"], [-1, 14, 29, 44, 64, float("inf")],
                  labels=["0–14", "15–29", "30–44", "45–64", "65+"])


def tabular(base: pd.DataFrame, por: str) -> pd.DataFrame:
    """% de personas que viven en hogares pobres por grupo, ponderado con facpob07."""
    t = (base.assign(grupo=grupo(base, por), pobres=base["pobre"] * base["facpob07"])
         .groupby("grupo", observed=True)
         .agg(pobres=("pobres", "sum"), poblacion=("facpob07", "sum"),
              encuestados=("pobre", "size")))
    t["pobreza"] = t["pobres"] / t["poblacion"] * 100
    return t.sort_values("pobreza", ascending=False) if CORTES[por]["ordenar"] else t


def graficar(tabla: pd.DataFrame, titulo: str, anio: int, destino: Path) -> None:
    """Barras horizontales desde cero, un color, el valor escrito en cada barra."""
    alto = 1.15 + 0.55 * len(tabla)
    fig, ax = plt.subplots(figsize=(7, alto))
    etiquetas = [str(g) for g in tabla.index][::-1]  # el primero queda arriba
    valores = tabla["pobreza"].to_numpy()[::-1]
    ax.barh(etiquetas, valores, height=0.6, color=COLOR)
    tope = max(valores.max() * 1.18, 10)
    ax.set_xlim(0, tope)
    for y, v in enumerate(valores):
        ax.text(v + tope * 0.012, y, f"{v:.1f} %", va="center", ha="left",
                fontsize=10, color=TINTA, fontweight="bold")

    # Sin grilla: chocaría con los valores escritos
    for lado in ["top", "right", "bottom"]:
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(TINTA_2)
    ax.tick_params(colors=TINTA_2, length=0, labelsize=10)
    ax.tick_params(axis="y", labelcolor=TINTA)
    ax.set_xlabel("% de personas que viven en hogares pobres", color=TINTA_2, fontsize=9)

    fig.suptitle(f"Personas en hogares pobres {titulo}, Perú {anio}",
                 x=0.02, ha="left", fontsize=13, fontweight="bold", color=TINTA)
    fig.text(0.02, 0.01, f"Fuente: INEI, ENAHO {anio}.",
             ha="left", va="bottom", fontsize=8, color=TINTA_2)
    fig.tight_layout(rect=(0, 0.16 / alto, 1, 1))

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=DPI, facecolor="white")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--por", choices=list(CORTES), required=True)
    parser.add_argument("--anio", type=int, default=2024)
    parser.add_argument("--salidas", type=Path, default=Path("salidas"))
    parser.add_argument("--figuras", type=Path, default=Path("figuras"))
    args = parser.parse_args()

    ruta = args.salidas / f"personas_{args.anio}.parquet"
    if not ruta.exists():
        sys.exit(f"Falta {ruta}. Usa primero la skill limpiando-enaho.")
    base = pd.read_parquet(ruta, columns=["pobre", "facpob07", "urbano", "sexo", "edad"])

    tabla = tabular(base, args.por)
    if tabla["encuestados"].sum() != len(base):
        sys.exit("Hay personas sin grupo; revisa la base antes de graficar.")

    titulo = CORTES[args.por]["titulo"]
    destino = args.figuras / f"pobreza_por_{args.por}_{args.anio}.png"
    graficar(tabla, titulo, args.anio, destino)

    print(f"% de personas que viven en hogares pobres {titulo}, {args.anio}:")
    for g, r in tabla.iterrows():
        print(f"  {str(g):<8} {r.pobreza:5.1f} %   ({int(r.encuestados):,} encuestados)")
    print(f"\nFigura: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
