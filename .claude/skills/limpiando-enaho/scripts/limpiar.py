# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "pyarrow"]
# ///
"""Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI.

Arma una base con los miembros del hogar tal como los cuenta el INEI (p204 = 1,
los mismos de mieperho), la condición de pobreza de su hogar y los factores de
expansión, y la valida contra la cifra oficial.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Lee los zip de datos/ sin descomprimirlos y escribe:
    salidas/personas_<anio>.parquet   solo si la validación pasa
    salidas/validacion.txt            siempre
Sale con código 1 si alguna validación falla.
"""

import argparse
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

# Código del portal de microdatos del INEI y cifras oficiales por año.
ANIOS = {
    2024: {"codigo": 966, "pobreza": 27.6, "extrema": 5.5, "miembros": 109_842},
}
TOLERANCIA = 0.1  # puntos porcentuales frente al INEI

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
COLS_SUMARIA = LLAVES_HOGAR + ["pobreza", "mieperho", "factor07"]
COLS_MIEMBROS = LLAVES_PERSONA + [
    "anio", "mes", "ubigeo", "dominio", "estrato",
    "p203", "p205", "p207", "p208a", "facpob07",
]
NOMBRES = {"p203": "parentesco", "p207": "sexo", "p208a": "edad"}


def normalizar(nombre: str) -> str:
    """'aÑo' -> 'anio'; el resto, en minúscula y sin tildes."""
    nombre = unicodedata.normalize("NFKD", nombre.strip().lower().replace("ñ", "ni"))
    return "".join(c for c in nombre if not unicodedata.combining(c))


def leer_dta(zip_path: Path, patron: str, llaves: list[str], peso: str) -> pd.DataFrame:
    """Lee el .dta del zip con códigos (no etiquetas), llaves como texto y peso en float64."""
    if not zip_path.exists():
        sys.exit(f"Falta {zip_path}. Usa la skill descargando-enaho.")
    with zipfile.ZipFile(zip_path) as z:
        candidatos = [n for n in z.namelist() if re.search(patron, n, re.IGNORECASE)]
        if len(candidatos) != 1:
            sys.exit(f"Esperaba un .dta que coincida con {patron!r} en {zip_path}: {candidatos}")
        with z.open(candidatos[0]) as f:
            df = pd.read_stata(f, convert_categoricals=False)
    df.columns = [normalizar(c) for c in df.columns]
    for c in llaves + ["ubigeo"]:  # como número se pierden los ceros a la izquierda
        df[c] = df[c].astype("string").str.strip()
    df[peso] = df[peso].astype("float64")  # en float32 las sumas pierden precisión
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
        sys.exit(f"Año {args.anio} sin configurar. Disponibles: {sorted(ANIOS)}.")
    ref = ANIOS[args.anio]
    cod = ref["codigo"]

    # 1-2. Leer y normalizar
    sumaria = leer_dta(args.datos / f"{cod}-Modulo34.zip", rf"/sumaria-{args.anio}\.dta$",
                       LLAVES_HOGAR, "factor07")
    modulo_200 = leer_dta(args.datos / f"{cod}-Modulo02.zip", rf"/enaho01-{args.anio}-200\.dta$",
                          LLAVES_PERSONA, "facpob07")

    # 3. Miembros del hogar según el INEI: p204 == 1, presentes o ausentes.
    #    Son las personas de mieperho, entre las que el INEI reparte el gasto del hogar.
    personas = modulo_200.loc[modulo_200["p204"] == 1, COLS_MIEMBROS]

    # 4. Unir cada persona con su hogar; muchos a uno o falla
    base = personas.merge(sumaria[COLS_SUMARIA], on=LLAVES_HOGAR,
                          how="left", validate="m:1", indicator=True)
    sin_hogar = int((base.pop("_merge") != "both").sum())

    # 5. Construir variables
    base = base.rename(columns=NOMBRES)
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = (base["estrato"] <= 5).astype("int8")
    base["pobre"] = (base["pobreza"] <= 2).astype("int8")
    base["pobre_extremo"] = (base["pobreza"] == 1).astype("int8")

    # 6. Validar
    por_hogar = base.groupby(LLAVES_HOGAR).size().reindex(
        pd.MultiIndex.from_frame(sumaria[LLAVES_HOGAR]), fill_value=0)
    hogares_distintos = int((por_hogar.to_numpy() != sumaria["mieperho"].to_numpy()).sum())
    peso_hogar = sumaria["factor07"] * sumaria["mieperho"]
    pob_sumaria = pct(sumaria["pobreza"] <= 2, peso_hogar)
    ext_sumaria = pct(sumaria["pobreza"] == 1, peso_hogar)
    pob_personas = pct(base["pobre"], base["facpob07"])

    chequeos = [
        ("Llaves de persona únicas", not personas.duplicated(LLAVES_PERSONA).any(), ""),
        ("Unión sin perder ni duplicar filas", len(base) == len(personas),
         f"{len(base):,} vs {len(personas):,}"),
        ("Toda persona tiene hogar en la sumaria", sin_hogar == 0, f"{sin_hogar} sin hogar"),
        ("Miembros por hogar iguales a mieperho", hogares_distintos == 0,
         f"{hogares_distintos} hogares distintos"),
        ("Miembros del hogar", len(base) == ref["miembros"],
         f"{len(base):,} (esperado {ref['miembros']:,}; el módulo 200 trae {len(modulo_200):,})"),
        ("Pobreza (sumaria, factor07 × mieperho)", abs(pob_sumaria - ref["pobreza"]) < TOLERANCIA,
         f"{pob_sumaria:.2f} % (INEI {ref['pobreza']} %)"),
        ("Pobreza (personas, facpob07) igual a la sumaria", abs(pob_personas - pob_sumaria) < 0.01,
         f"{pob_personas:.2f} % vs {pob_sumaria:.2f} %"),
        ("Pobreza extrema (sumaria)", abs(ext_sumaria - ref["extrema"]) < TOLERANCIA,
         f"{ext_sumaria:.2f} % (INEI {ref['extrema']} %)"),
    ]
    ok = all(paso for _, paso, _ in chequeos)

    lineas = [f"Validación ENAHO {args.anio} (código INEI {cod})", ""]
    lineas += [f"[{'OK' if paso else 'FALLA'}] {nombre}" + (f": {det}" if det else "")
               for nombre, paso, det in chequeos]
    lineas += ["", "Pobreza = % de personas que viven en hogares pobres.",
               f"Población representada: {base['facpob07'].sum():,.0f} personas",
               "", "RESULTADO: " + ("VÁLIDA" if ok else "NO VÁLIDA, no usar la base")]

    # 7. Guardar
    args.salidas.mkdir(parents=True, exist_ok=True)
    (args.salidas / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    destino = args.salidas / f"personas_{args.anio}.parquet"
    if ok:
        base.to_parquet(destino, index=False)
        lineas.append(f"Base guardada en {destino} ({len(base):,} filas, {base.shape[1]} columnas)")
    else:
        destino.unlink(missing_ok=True)  # no dejar una base vieja que parezca válida
    print("\n".join(lineas))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
