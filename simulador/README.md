# Simulador de playtest — YO SOY UN ASESINO

Simulador Monte Carlo del Reglamento V1.0 y sus variantes. Las partidas las juegan agentes
que se comportan como personas, no como ordenadores perfectos. Solo usa la biblioteca
estándar de Python 3.8+.

## Uso

```bash
python3 asesino.py                              # informe V1.0 con 4, 6 y 8 jugadores
python3 asesino.py --variante V1.1              # informe de la propuesta V1.1
python3 asesino.py --variante V1.2.2            # Reglamento consolidado V1.2.2 (Modo Normal)
python3 asesino.py --comparar                   # tabla con todas las variantes
python3 asesino.py --mesa familia               # mesa de familia (o: jugones, mixta)
python3 asesino.py --jugadores 5 --partidas 5000
python3 asesino.py --cronica --jugadores 5 --semilla 7   # narra una partida turno a turno
```

Para añadir una variante, añade una entrada a `VARIANTES` con los parámetros de
`REGLAS_V10` que cambian. Los parámetros disponibles son:

- Composición del mazo: `escenas`, `declaracion`, `complice`, `testigo`.
- Rondas: `construccion`, `sospecha`.
- Robo y mano: `mercado`, `robo_ciego`, `mano`, `draft`.
- Identidades y acusaciones: `det_tipos`, `contra`, `fallo_formal`.
- Puntuación: `revelar_temprano_bonus`.

## Auditoría

```bash
python3 auditoria.py                 # componentes, asientos, estrategias, puntuación y robustez
python3 auditoria.py --solo estrategias --partidas 2000
python3 auditoria.py --variantes V1.2.2 --solo estrategias
python3 auditoria.py --solo robustez_v12
```

Resultados en `resultados/auditoria.txt` y conclusiones en `../AUDITORIA.md`.

## Cómo juegan los "humanos"

Cada jugador recibe un perfil: novato, casual, calculador, agresivo, prudente, farsante,
codicioso u observador. Cada perfil combina estos rasgos:

| Rasgo | Efecto en la partida |
|---|---|
| Habilidad | Valora su mano estimando cuántas cartas útiles quedan y cuántos robos le quedan, con ruido según su nivel. |
| Memoria | Recuerda solo parte del descarte y de lo visto con Testigo («unos segundos, sin notas»), y olvida con las rondas. |
| Error de regla | Algunos novatos cuentan una carta doble dos veces (§4), se creen con identidad y revelan una mano falsa. |
| Terquedad | Le cuesta cambiar de objetivo. |
| Lectura / cara de póker | Los jugadores transparentes dan pistas y los buenos lectores las captan. Así se estiman las acusaciones. |
| Farol | El farsante coge y guarda cartas «de Asesino» para atraer acusaciones falsas. |
| Riesgo / prudencia / codicia | Deciden cuándo revelarse, cuándo acusar y qué identidad perseguir. |
| Rencor | Un jugador Bloqueado acapara cartas del crimen y ataca al líder con los especiales. |

Las reglas se aplican de forma estricta. La regla «una carta = un atributo» se comprueba
con un emparejamiento real entre cartas y huecos de la identidad. Las acusaciones son
privadas: el acusador ve la mano del acusado y los demás solo ven el resultado.

## Indicadores de «¿engancha?»

| Indicador | Por qué importa |
|---|---|
| Nadie por partida | Objetivo del reglamento (§18). |
| % de Nadie a 1 carta | La promesa del dossier: perder debe sentirse como «me faltó una carta». |
| Cambios de objetivo | Mide si la identidad emergente ocurre de verdad. |
| Decisión tensa en 9–10 | Rondas finales con dilema real entre revelar, acusar o esperar. |
| Variedad (entropía) | Que no gane siempre la misma identidad. |
| Acusaciones y su acierto | Interacción y faroleo. |
| Partidas con Cazador | Que la salida de emergencia exista, pero no sea gratis. |
| Peso de la mano inicial | Suerte frente a decisiones. |
| Duración estimada | Objetivo de 20–30 min. |

Los umbrales están en `semaforo()`. Son propuestas de diseño, no verdades. Ajústalos con
los datos del playtest físico.

## Limitaciones

- Los perfiles no están calibrados con partidas reales.
- La duración es un modelo aproximado de segundos por acción.
- Sirve para comparar variantes entre sí, no para predecir números exactos de mesa.

Las interpretaciones de las reglas ambiguas están documentadas en `../REVISION_REGLAS.md`, §3.
