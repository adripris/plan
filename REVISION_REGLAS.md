# YO SOY UN ASESINO — Revisión del Reglamento V1.0 y propuesta V1.1

Basado en el *Reglamento V1.0 (prototipo de playtest)*, el *Dossier de presentación* y
**3.000 partidas simuladas por configuración** con jugadores que imitan a personas
reales (ver `simulador/README.md`). Los resultados completos están en
`simulador/resultados/`.

> Aviso honesto: un simulador no sustituye a una mesa real. Los perfiles humanos
> son razonables pero **no están calibrados** con partidas físicas, y la duración es
> una estimación (≈22–32 s por turno más el tiempo de acciones). Úsalo para decidir
> **qué probar** en las 20 partidas registradas, no para cerrar el diseño.

---

## 1. Diagnóstico en una frase

La V1.0 funciona como juego de lectura de mesa, pero **pierde demasiada gente** (≈45%
entre Nadie y Bloqueados) y **dos de las cuatro identidades casi no existen**:
Detective sale en el 1% de los jugadores y Testigo en el 3–4%. El núcleo funciona y no hay
que tocarlo. Hay que abrir el flujo de cartas y desatascar la Declaración.

## 2. Resultados V1.0 frente a lo que piden el reglamento y el dossier

| Indicador | 4 jug. | 6 jug. | 8 jug. | Objetivo |
|---|---|---|---|---|
| Nadie (incl. Bloqueados) por partida | **1.74** | **2.71** | **3.65** | ~1 (4j) · 2–3 (8j) |
| Asesino / Cómplice | 32% / 14% | 30% / 13% | 29% / 13% | — |
| **Detective / Testigo** | **1.2% / 3.9%** | **1.0% / 3.5%** | **0.8% / 3.4%** | «alcanzable» |
| Nadie que se quedó a 1 carta | 39% | 37% | 37% | «me faltó una carta» |
| Jugadores con decisión tensa en rondas 9–10 | 38% | 37% | 36% | rondas finales con dilema |
| Acusaciones por partida / acierto Formal | 0.8 / 41% | 1.4 / 42% | 1.9 / 43% | — |
| Revelaciones falsas (error de §4) por partida | 0.06 | 0.08 | 0.11 | 0 |
| Duración estimada | 19 min | 29 min | **39 min** | 20–30 min |

Lo que **sí funciona**:

- La habilidad pesa, pero no lo decide todo: los jugadores calculadores u observadores
  sobreviven ~63% y el novato ~45%. Un novato gana a menudo.
- La mano inicial pesa poco (+8 a +12 puntos de supervivencia entre una buena salida y
  una mala).
- Las acusaciones aciertan alrededor del 40%: son apuestas reales, ni seguras ni absurdas.
- Cazador aparece en el 22–50% de las partidas y funciona como salida de emergencia.

## 3. Problemas de reglas (ambigüedades que la mesa va a preguntar)

| # | Regla | Problema | Propuesta de redacción |
|---|---|---|---|
| 1 | §12 Contra-acusación | Tal como está escrita **no hace nada**: una acusación falsa ya penaliza al acusador. 2 de las 8 cartas de Acusación son cartas muertas. | «Si la acusación era incorrecta, **el acusador queda Bloqueado** además de su penalización.» (V1.1) |
| 2 | §12 Formal fallida + §8 | En el paso 2 tienes 5 cartas; si descartas 2 al azar te quedas con 3 y **no puedes "terminar con 4"**. | «Si te quedas con menos de 4, terminas el turno así y recuperas en tu siguiente robo.» En la ronda 10 eso equivale a perder: dilo. |
| 3 | §12 «el acusado roba 1» | Roba fuera de turno y se queda con 5. Si pasa en la ronda 10 tras su turno, llega a la Revelación con 5. | «En la Revelación Forzada eliges 4 de tus cartas.» |
| 4 | §11 Revelar | En el paso 2 tienes 5 cartas, pero la regla dice «enseñas tus cuatro cartas». | «Elige 4, descarta la quinta y enséñalas.» |
| 5 | §11 Revelación incorrecta | El jugador pasa a ser Nadie, pero ¿sigue en la mesa? | Igual que Bloqueado: sigue jugando sin poder sobrevivir (lo da por hecho el simulador). |
| 6 | §9 Declaración | «Nombra un atributo concreto (asesino, arma…)»: ¿la categoría o el valor? | «Nombra una categoría; el objetivo debe tener una Escena con **el valor del Crimen** en esa categoría.» |
| 7 | §13 Bloqueado | ¿Puede acusar? ¿Puede ser objetivo de especiales un jugador a salvo? | Bloqueado no acusa. Un jugador a salvo no puede ser objetivo de nada. |
| 8 | §8 Mazo agotado | Con 8 jugadores quedan 79 cartas para 80 robos. No hay regla. | «Si el mazo se acaba, baraja el descarte salvo la carta superior.» |
| 9 | §5 Una carta = un atributo | Es la regla que más se rompe: un 30% de los novatos la malinterpreta y **revela manos falsas** (0.06–0.11 por partida). | Ponla en la carta de ayuda con un ejemplo visual de «carta doble que solo vale una vez». |

## 4. Problemas de diseño (los números)

1. **Revelarse siempre es lo mejor.** En la V1.0 no hay motivo para seguir fingiendo:
   quien tiene identidad se revela y se acabó. La promesa del dossier («puedes tener una
   identidad completa y seguir fingiendo») no tiene recompensa.
2. **La Declaración es un cuello de botella.** Hacen falta para Detective y para Testigo,
   solo hay 5 y además se queman como ataque: **1.8 por partida con 4 jugadores y 3.7 de 5
   con 8 jugadores.** Por eso Detective y Testigo casi no aparecen.
3. **Detective exige demasiado.** Necesita 3 tipos distintos de entre 12 Evidencias
   compatibles, más 1 Declaración. Además es la identidad que más puntos da (6). Hoy es casi
   imposible.
4. **No hay suficientes cartas útiles con muchos jugadores.** Con 8 jugadores todos compiten
   por las mismas 12 cartas de cada atributo y por el mismo descarte (una sola carta visible).
5. **Las variables previstas en §18 tienen efectos secundarios.**
   - *96 Escenas* baja Nadie (3.65 → 3.22 con 8 jugadores) pero diluye Evidencias y
     especiales: Detective desaparece y la variedad cae (entropía 0.66 → 0.55).
   - *10 rondas de Construcción* baja Nadie (→ 2.96 con 8 jugadores) pero alarga la partida
     unos 7 minutos.
6. **Duración con 7–8 jugadores.** Son 80 turnos, unos 38–39 min estimados. Hay que
   cronometrarlo en mesa. Bajar a 7+2 rondas solo ahorra ~3 min y añade +0.4 Nadie, así que
   no compensa.

## 5. Variantes probadas (1.500 partidas cada una, mesa mixta)

| Variante | Nadie 4j | Nadie 6j | Nadie 8j | Variedad | Tensión 9–10 | Indicadores OK (4/6/8j) |
|---|---|---|---|---|---|---|
| V1.0 | 1.73 | 2.70 | 3.68 | 0.67 | 38% | 5 / 6 / 4 |
| 96 Escenas (§18) | 1.58 | 2.36 | 3.22 | 0.54 | 36% | 5 / 6 / 4 |
| 10 rondas de Construcción (§18) | 1.34 | 2.10 | 2.96 | 0.62 | 37% | 6 / 6 / 5 |
| **Mercado de 2** | 1.40 | 2.10 | 2.82 | 0.71 | 39% | 6 / 7 / 5 |
| Roba 2 del mazo | 1.02 | 1.98 | 3.70 | 0.52 | 41% | 6 / 6 / 4 |
| Mano de 5 | 1.55 | 2.34 | 3.29 | 0.60 | 40% | 5 / 6 / 4 |
| **Detective con 2 tipos** | 1.64 | 2.59 | 3.54 | 0.76 | 39% | 6 / 6 / 4 |
| 7 Declaraciones + 6 Testigos | 1.79 | 2.85 | 3.89 | 0.76 | 37% | 6 / 6 / 4 |
| Contra-acusación que bloquea | 1.74 | 2.71 | 3.70 | 0.67 | 39% | 5 / 6 / 4 |
| **V1.1 (combinación)** | **1.29** | **1.99** | **2.79** | **0.84** | **58%** | **7 / 8 / 6** |

Algunas pruebas salieron peor de lo esperado:

- *Roba 2* funciona con 4 jugadores pero empeora con 8, porque se acaban las cartas útiles.
- *Más Declaraciones* por sí solas suben Nadie, porque también hay más ataques.
- *Draft inicial* (6 → 4, probado sobre la V1.1) reduce los cambios de objetivo (0.64 → 0.50): cada jugador se casa antes con su identidad.

## 6. Propuesta V1.1 (5 cambios, el núcleo intacto)

1. **Mercado de 2.** En el paso ROBAR puedes tomar **cualquiera de las 2 cartas superiores
   del descarte**. El descarte se coloca en escalera para que se vean. Más información
   pública, más lectura de mesa y menos «era imposible».
2. **Detective = 3 Evidencias compatibles con al menos 2 tipos distintos + Declaración.**
3. **6 Declaraciones** en lugar de 5. El mazo principal pasa a 113 cartas.
4. **La Contra-acusación bloquea al acusador en falso.** Así deja de ser una carta muerta y
   acusar se convierte en una apuesta.
5. **Sangre fría (con puntuación).** Quien sobrevive en la Revelación Forzada **sin haberse
   revelado antes** gana **+2 puntos**. Esto da sentido a seguir fingiendo.

Resultados V1.1 (3.000 partidas, mesa mixta):

| Indicador | 4 jug. | 6 jug. | 8 jug. |
|---|---|---|---|
| Nadie (incl. Bloqueados) por partida | **1.29** ✅ | **2.00** ✅ | **2.80** ✅ |
| Detective / Testigo | 8.1% / 6.3% | 7.5% / 6.4% | 6.6% / 6.3% |
| Variedad de identidades | 0.84 ✅ | 0.84 ✅ | 0.84 ✅ |
| Jugadores con decisión tensa en 9–10 | 58% ✅ | 57% ✅ | 56% ✅ |
| Acierto de la Acusación Formal | 52% | 55% | 57% |
| Supervivencia del calculador frente al novato | 73% vs 59% | 74% vs 56% | 73% vs 52% |
| Mesa «familia» / mesa «jugones» (Nadie) | 1.38 / 1.33 | 2.08 / 2.01 | 2.85 / 2.73 |

La V1.1 funciona igual en mesas familiares y en mesas de jugones expertos.

## 7. Lo que sigue sin resolver (para el playtest físico)

- **«Me faltó una carta»:** solo el ~43% de los Nadie se queda a 1 carta; el resto está a 2
  o más. Ideas a probar: descarte visible completo (en abanico); una *Última oportunidad* en
  la que, antes de la Revelación Forzada, cada jugador activo puede cambiar 1 carta con el
  descarte.
- **Cambios de objetivo:** 0.64 por jugador. La identidad emergente existe, pero los
  jugadores cambian menos de lo que promete el dossier. Habría que comprobar en mesa si se
  percibe.
- **Duración con 7–8 jugadores** (~38 min estimados). Hay que cronometrarla. Si se
  confirma, se puede probar un temporizador de turno o anunciar el juego como «4–6
  jugadores, ampliable a 8».
- **Cazador con 8 jugadores** aparece en ~45% de las partidas. Hay que vigilar si se
  siente como un premio barato.

## 8. Qué anotar en las 20 partidas registradas

Para poder comparar la mesa real con el simulador, registra en cada partida:

- Número de jugadores y si alguno era novato.
- Identidad final de cada jugador y cuántas cartas le faltaban a cada Nadie.
- Especiales jugados, revelaciones (y si alguna fue falsa) y acusaciones (tipo y si acertó).
- Duración en minutos.
- Una pregunta a cada perdedor: «¿te faltó poco o era imposible?».
