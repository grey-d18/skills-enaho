# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow"]
# ///
"""Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI.

Arma una base de personas (residentes habituales) con la condición de pobreza
de su hogar y los factores de expansión, y la valida contra la cifra oficial.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Lee los zip directamente de datos/ (no hace falta descomprimirlos) y escribe:
    salidas/personas_<anio>.parquet   solo si la validación pasa
    salidas/validacion.txt            siempre
Sale con código 1 si alguna validación falla.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

# Código del portal de microdatos del INEI y cifras oficiales por año.
# Para agregar un año: su código, y las cifras publicadas por el INEI.
ANIOS = {
    2024: {
        "codigo": 966,
        "pobreza": 27.6,  # % de personas en pobreza monetaria
        "extrema": 5.5,  # % de personas en pobreza extrema
        "residentes": 108_664,  # filas esperadas en la base de personas
    },
}
TOLERANCIA = 0.1  # puntos porcentuales

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]

COLS_SUMARIA = LLAVES_HOGAR + ["pobreza", "mieperho", "factor07"]
COLS_MIEMBROS = LLAVES_PERSONA + [
    "anio", "mes", "ubigeo", "dominio", "estrato",
    "p203", "p204", "p205", "p206", "p207", "p208a", "facpob07",
]


def normalizar(nombre: str) -> str:
    """'aÑo' -> 'anio'; el resto, en minúscula y sin tildes."""
    nombre = nombre.strip().lower().replace("ñ", "ni")
    nombre = unicodedata.normalize("NFKD", nombre)
    return "".join(c for c in nombre if not unicodedata.combining(c))


def leer_dta(zip_path: Path, patron: str) -> pd.DataFrame:
    """Paso 1 y 2: lee el .dta del zip con códigos (no etiquetas) y normaliza columnas."""
    if not zip_path.exists():
        sys.exit(f"Falta {zip_path}. Descárgalo del portal de microdatos del INEI.")
    with zipfile.ZipFile(zip_path) as z:
        candidatos = [n for n in z.namelist() if re.search(patron, n, re.IGNORECASE)]
        if len(candidatos) != 1:
            sys.exit(f"Esperaba un archivo que coincida con {patron!r} en {zip_path}, "
                     f"encontré {candidatos}")
        with z.open(candidatos[0]) as f:
            df = pd.read_stata(f, convert_categoricals=False)
    df.columns = [normalizar(c) for c in df.columns]
    return df


def a_texto(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Llaves y ubigeo como texto: nunca como número, o se pierden los ceros."""
    for c in columnas:
        df[c] = df[c].astype("string").str.strip()
    return df


def pct(indicador: pd.Series, peso: pd.Series) -> float:
    return float((indicador * peso).sum() / peso.sum() * 100)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anio", type=int, default=2024)
    parser.add_argument("--datos", type=Path, default=Path("datos"))
    parser.add_argument("--salidas", type=Path, default=Path("salidas"))
    args = parser.parse_args()

    if args.anio not in ANIOS:
        sys.exit(f"Año {args.anio} sin configurar. Disponibles: {sorted(ANIOS)}. "
                 "Agrega su código del INEI y sus cifras oficiales en ANIOS.")
    ref = ANIOS[args.anio]
    cod = ref["codigo"]

    # 1-2. Leer y normalizar
    sumaria = leer_dta(args.datos / f"{cod}-Modulo34.zip", rf"/sumaria-{args.anio}\.dta$")
    miembros = leer_dta(args.datos / f"{cod}-Modulo02.zip", rf"/enaho01-{args.anio}-200\.dta$")
    sumaria = a_texto(sumaria, LLAVES_HOGAR + ["ubigeo"])
    miembros = a_texto(miembros, LLAVES_PERSONA + ["ubigeo"])

    # Cifra oficial con la sumaria: personas = hogares × miembros
    peso_hogar = sumaria["factor07"] * sumaria["mieperho"]
    pob_sumaria = pct(sumaria["pobreza"] <= 2, peso_hogar)
    ext_sumaria = pct(sumaria["pobreza"] == 1, peso_hogar)

    # 3. Residentes habituales (definición del INEI):
    #    miembros no ausentes 30+ días, o no miembros presentes 30+ días
    filas_200 = len(miembros)
    residente = ((miembros["p204"] == 1) & (miembros["p205"] == 2)) | (
        (miembros["p204"] == 2) & (miembros["p206"] == 1)
    )
    personas = miembros.loc[residente, COLS_MIEMBROS].copy()

    # 4. Unir personas con su hogar; muchos a uno o falla
    base = personas.merge(sumaria[COLS_SUMARIA], on=LLAVES_HOGAR,
                          how="left", validate="m:1", indicator=True)
    sin_hogar = int((base.pop("_merge") != "both").sum())

    # 5. Construir variables
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = (base["estrato"] <= 5).astype("int8")
    base["pobre"] = (base["pobreza"] <= 2).astype("int8")
    base["pobre_extremo"] = (base["pobreza"] == 1).astype("int8")
    base = base.rename(columns={"p207": "sexo", "p208a": "edad", "p203": "parentesco"})

    # 6. Validar
    pob_personas = pct(base["pobre"], base["facpob07"])
    ext_personas = pct(base["pobre_extremo"], base["facpob07"])
    chequeos = [
        ("Llaves de persona únicas", not personas.duplicated(LLAVES_PERSONA).any(), ""),
        ("Unión sin perder ni duplicar filas", len(base) == len(personas),
         f"{len(base):,} vs {len(personas):,}"),
        ("Toda persona tiene hogar en la sumaria", sin_hogar == 0, f"{sin_hogar} sin hogar"),
        ("Residentes habituales", len(base) == ref["residentes"],
         f"{len(base):,} (esperado {ref['residentes']:,}; módulo 200 trae {filas_200:,})"),
        ("Pobreza (sumaria, factor07 × mieperho)",
         abs(pob_sumaria - ref["pobreza"]) < TOLERANCIA,
         f"{pob_sumaria:.2f} % (INEI {ref['pobreza']} %)"),
        ("Pobreza (personas, facpob07)",
         abs(pob_personas - ref["pobreza"]) < TOLERANCIA,
         f"{pob_personas:.2f} % (INEI {ref['pobreza']} %)"),
        ("Pobreza extrema (sumaria)",
         abs(ext_sumaria - ref["extrema"]) < TOLERANCIA,
         f"{ext_sumaria:.2f} % (INEI {ref['extrema']} %)"),
    ]
    ok = all(c[1] for c in chequeos)

    lineas = [f"Validación ENAHO {args.anio} (código INEI {cod})", ""]
    lineas += [f"[{'OK' if paso else 'FALLA'}] {nombre}" + (f": {det}" if det else "")
               for nombre, paso, det in chequeos]
    lineas += ["", f"Pobreza extrema (personas, facpob07): {ext_personas:.2f} %",
               f"Población representada: {base['facpob07'].sum():,.0f} personas",
               "", "RESULTADO: " + ("VÁLIDA" if ok else "NO VÁLIDA, no usar la base")]

    # 7. Guardar
    args.salidas.mkdir(parents=True, exist_ok=True)
    (args.salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    destino = args.salidas / f"personas_{args.anio}.parquet"
    if ok:
        base.to_parquet(destino, index=False)
        lineas.append(f"Base guardada en {destino} ({len(base):,} filas, {base.shape[1]} columnas)")
    elif destino.exists():
        destino.unlink()  # no dejar una base vieja que parezca válida
    print("\n".join(lineas))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
