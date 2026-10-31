---
name: descargando-enaho
description: Descarga los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del portal de microdatos del INEI y decide qué archivo usar de cada uno, incluida qué sumaria (8 o 12 grupos de gasto). Úsala cuando pidan bajar, descargar o actualizar la ENAHO, cuando falten sus zip en datos/, o cuando haya dudas sobre qué sumaria usar.
argument-hint: [año]
---

# Descargar la ENAHO

1. Si te pidieron explícitamente descargar o bajar la ENAHO, corre directamente (sin año, usa 2024):
   `uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --anio $0`
2. Si llegaste aquí porque faltan datos para otra tarea, primero corre:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --anio $0 --solo-verificar`
   Si dice FALTAN DATOS, pregunta al usuario si descargas los zip (de 6 a 16 MB cada uno) y descarga solo si acepta.
3. Lee la salida. Si dice FALTAN DATOS después de descargar, muestra el error y detente.
4. Usa exactamente el `.dta` que el script indica para cada módulo. La sumaria es `sumaria-AAAA.dta`, con el gasto en 8 grupos.
5. No uses `sumaria-AAAA-12g.dta`: este repositorio no la usa. Da la misma pobreza, pero sus variables de gasto por grupo se llaman igual que en la sumaria de 8 grupos y miden otra cosa. Si alguien pide el gasto en 12 grupos, explícale el riesgo y detente. Detalle en [reference.md](reference.md).
6. Solo 2024 está verificado (código 966). Si piden otro año, dilo y no adivines el código.
7. Los datos van en `datos/`, que no se sube a git.
