---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, departamento, área, sexo o edad.
argument-hint: [año]
---

# Limpiar la ENAHO

1. Si faltan `datos/966-Modulo34.zip` o `datos/966-Modulo02.zip`, usa primero la skill `descargando-enaho`.
2. Desde la raíz del repositorio, corre exactamente, con el año que pidió el usuario o 2024 si no pidió ninguno:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio <año>`
   No modifiques el script ni repliques la limpieza a mano.
3. Lee `salidas/validacion.txt`. Si dice NO VÁLIDA o la pobreza difiere del INEI en más de 0.1 puntos, detente y muestra el archivo al usuario; no respondas con cifras.
4. Responde con `salidas/personas_<año>.parquet`. Toda cifra de personas va ponderada con `facpob07`; nunca cuentes filas como si fueran personas.
5. La pobreza es del hogar: todos sus miembros comparten la misma condición. Escribe siempre "X % de las personas vive en hogares pobres". Por sexo o edad, di "X % de las mujeres vive en hogares pobres", nunca "las mujeres son más pobres".
6. Pobre es `pobre == 1` (`pobreza <= 2`), nunca un promedio de `pobreza`. Une con otras fuentes por código (`departamento`, `ubigeo`) como texto, nunca por nombre.
7. Antes de usar una variable que no está en la base, o de comparar con cifras del INEI, lee [reference.md](reference.md).
