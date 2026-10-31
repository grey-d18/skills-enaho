# skills-enaho

Skills de Claude Code para trabajar con la ENAHO del INEI de forma reproducible. Cualquiera que clone el repositorio obtiene la misma base, con la pobreza oficial replicada.

| Skill | Qué hace | Estado |
|---|---|---|
| [`descargando-enaho`](.claude/skills/descargando-enaho/SKILL.md) | Baja los módulos 34 y 02 del INEI y decide qué archivo usar, incluida la sumaria | ✅ |
| [`limpiando-enaho`](.claude/skills/limpiando-enaho/SKILL.md) | Une los módulos 34 y 02 en una base de personas y la valida contra el INEI | ✅ |

## Requisitos

- [Claude Code](https://claude.com/claude-code)
- [uv](https://docs.astral.sh/uv/)

## Datos

Los microdatos no se suben al repositorio. Pídele a Claude «descarga la ENAHO 2024», o corre:

```bash
uv run .claude/skills/descargando-enaho/scripts/descargar.py --anio 2024
```

Esto baja `966-Modulo34.zip` y `966-Modulo02.zip` a `datos/`. 966 es el código de la ENAHO 2024 en el portal de microdatos del INEI. No hace falta descomprimirlos.

**Qué sumaria se usa:** `sumaria-2024.dta`, con el gasto en 8 grupos. El repositorio no usa la `-12g`: da la misma pobreza, pero desglosa el gasto en 12 grupos con variables que se llaman igual y miden otra cosa. Detalle en [reference.md](.claude/skills/descargando-enaho/reference.md).

## Uso

Con Claude Code, en la raíz del repositorio:

```
/limpiando-enaho 2024
¿Cuál fue la pobreza en Cusco en 2024?
```

La skill también se activa sola cuando pides algo sobre la ENAHO o la pobreza.

Para limpiar sin Claude:

```bash
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
```

Esto genera:

- `salidas/personas_2024.parquet`: 108,664 residentes habituales, con pobreza y factores de expansión
- `salidas/validacion.txt`: los chequeos. Si alguno falla, el script termina con error y no guarda la base

## Validación (ENAHO 2024)

| Chequeo | Resultado | INEI |
|---|---|---|
| Pobreza monetaria | 27.58 % | 27.6 % |
| Pobreza extrema | 5.50 % | 5.5 % |
| Residentes habituales | 108,664 | — |
| Llaves únicas, unión sin perder ni duplicar filas | OK | — |

Fuente: INEI, ENAHO 2024, módulos 34 y 02.
