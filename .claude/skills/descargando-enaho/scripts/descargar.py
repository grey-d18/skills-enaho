# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Descarga los módulos de la ENAHO del portal de microdatos del INEI.

Uso (desde la raíz del repositorio):
    uv run .claude/skills/descargando-enaho/scripts/descargar.py --anio 2024
    uv run .claude/skills/descargando-enaho/scripts/descargar.py --anio 2024 --solo-verificar

Baja a datos/ los zip de los módulos que usa el repositorio, no vuelve a bajar
los que ya están sanos, verifica que traigan los .dta esperados e imprime qué
archivo usar de cada módulo. Sale con código 1 si falta algo o un zip está dañado.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip"

# Código del portal de microdatos del INEI por año (solo años verificados).
CODIGOS = {2024: 966}

# Módulos que usa el repositorio y el .dta que se usa de cada uno.
# Para la sumaria se usa la versión de 8 grupos de gasto, no la -12g (ver reference.md).
MODULOS = {
    "34": {"nombre": "Sumaria (una fila por hogar)", "dta": r"/sumaria-{anio}\.dta$"},
    "02": {"nombre": "Miembros del hogar (una fila por persona)", "dta": r"/enaho01-{anio}-200\.dta$"},
}


def revisar(zip_path: Path, patron: str) -> tuple[bool, str, list[str]]:
    """Devuelve (sano, archivo a usar o motivo del problema, todos los .dta)."""
    if not zip_path.exists():
        return False, "no existe", []
    try:
        with zipfile.ZipFile(zip_path) as z:
            if z.testzip() is not None:
                return False, "zip dañado", []
            dtas = [n for n in z.namelist() if n.lower().endswith(".dta")]
    except zipfile.BadZipFile:
        return False, "no es un zip válido", []
    elegidos = [n for n in dtas if re.search(patron, n, re.IGNORECASE)]
    if len(elegidos) != 1:
        return False, f"esperaba un .dta que coincida con {patron!r}", dtas
    return True, elegidos[0], dtas


def descargar(url: str, destino: Path) -> None:
    temporal = destino.with_suffix(".zip.part")
    print(f"Descargando {url}")
    pedido = urllib.request.Request(url, headers={"User-Agent": "skills-enaho"})
    with urllib.request.urlopen(pedido, timeout=120) as r, open(temporal, "wb") as f:
        while bloque := r.read(1 << 20):
            f.write(bloque)
    temporal.replace(destino)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--anio", type=int, default=2024)
    parser.add_argument("--datos", type=Path, default=Path("datos"))
    parser.add_argument("--solo-verificar", action="store_true",
                        help="no descarga; solo informa qué falta")
    parser.add_argument("--forzar", action="store_true",
                        help="vuelve a descargar aunque el zip esté sano")
    args = parser.parse_args()

    if args.anio not in CODIGOS:
        sys.exit(f"Año {args.anio} sin verificar. Disponibles: {sorted(CODIGOS)}. "
                 "Agrega su código del portal de microdatos del INEI en CODIGOS.")
    codigo = CODIGOS[args.anio]
    args.datos.mkdir(parents=True, exist_ok=True)

    lineas = [f"ENAHO {args.anio} (código INEI {codigo}) en {args.datos}/", ""]
    ok = True
    for modulo, info in MODULOS.items():
        zip_path = args.datos / f"{codigo}-Modulo{modulo}.zip"
        patron = info["dta"].format(anio=args.anio)
        sano, detalle, dtas = revisar(zip_path, patron)
        if (not sano or args.forzar) and not args.solo_verificar:
            try:
                descargar(URL.format(codigo=codigo, modulo=modulo), zip_path)
            except OSError as e:
                detalle = f"falló la descarga: {e}"
            else:
                sano, detalle, dtas = revisar(zip_path, patron)
        ok &= sano
        if sano:
            lineas.append(f"[OK] Módulo {modulo} · {info['nombre']}: usar {detalle}")
            otros = [d for d in dtas if d != detalle]
            if otros:
                lineas.append(f"     También trae: {', '.join(otros)}")
        else:
            lineas.append(f"[FALTA] Módulo {modulo} · {info['nombre']}: {zip_path} {detalle}")

    lineas += ["", "Sumaria: la de 8 grupos de gasto (la que usa el INEI en sus series). "
               "No usar la -12g: sus variables de gasto por grupo se llaman igual "
               "y miden otra cosa (ver reference.md).",
               "", "RESULTADO: " + ("DATOS COMPLETOS" if ok else "FALTAN DATOS")]
    print("\n".join(lineas))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
