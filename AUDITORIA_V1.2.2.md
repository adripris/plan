# Auditoría de YO SOY UN ASESINO — V1.2.2

**Documentos auditados:** 01 Reglamento completo, 02 Biblia de cartas y diseño, 03 Dossier de
creación y 04 Playset y kit de playtest (todos V1.2.2).

**Método:** lectura de los cuatro documentos más simulación. El simulador implementa V1.2.2 en
Modo Normal y se ha jugado así:

- 3.000 partidas por tamaño de mesa.
- 14 estrategias forzadas para buscar jugadas dominantes.
- Ventaja por asiento.
- Variantes de una sola variable.
- Prueba de robustez cambiando los supuestos sobre cómo juegan las personas.

Todo se reproduce con `simulador/asesino.py --variante V1.2.2` y `simulador/auditoria.py`.

> Como dice el propio Dossier (§6), los jugadores simulados son herramientas comparativas, no
> evidencia de comportamiento humano. Esta auditoría sirve para decidir **qué mirar** en las 20
> partidas físicas.

**Severidad:**

- 🔴 Bloquea una partida o invalida el playtest.
- 🟠 Afecta al equilibrio o a la experiencia.
- 🟡 Pulido.

---

## Resumen ejecutivo

La V1.2.2 resuelve casi todo lo que señaló la auditoría anterior. Quedan resueltos:

- Mazo agotado.
- Revelar con 5 cartas.
- Revelación inválida.
- Estado Bloqueado.
- Contra-acusación muerta.
- Incentivos de la puntuación.
- Afirmación de las 1.296 combinaciones.
- Índice de abanico.
- Moderador en la verificación.

Pero los cambios de identidad (3 cartas y 4.ª libre) y el nuevo Cazador **han dado la vuelta al
equilibrio**:

| | Hallazgo | Sev. |
|---|---|---|
| 1 | **El juego se ha vuelto muy permisivo:** sobrevive el 85–88%. Con 4 jugadores, el **58% de las partidas termina sin ningún Nadie**. La amenaza de Nadie, que da la tensión, casi desaparece. | 🟠 |
| 2 | **Cómplice domina (34%) y Testigo es la segunda (26%). Asesino, el papel del título, baja al 17%.** El riesgo que el propio Dossier señala (§8) se confirma. | 🟠 |
| 3 | **Las acusaciones casi desaparecen:** 0,1–0,35 por partida (antes 0,8–1,9). Cazador ya no salva, así que acusar no ayuda a sobrevivir y solo arriesga la mano. | 🟠 |
| 4 | **Contradicción en el orden del turno:** para Revelar hace falta tener 4 cartas (§12), pero en el paso ACTUAR tienes 5 (§9). O no se puede revelar nunca, o el límite de mano inmediato rompe los Especiales. | 🔴 |
| 5 | **La Contra-acusación no tiene riesgo real:** si la acusación es correcta, ya quedas Bloqueado, y descartar 1 carta más no te cuesta nada. Siempre conviene jugarla. | 🟠 |
| 6 | **El plan de 20 partidas no puede responder sus propias preguntas** sobre acusaciones y Contra-acusación: en el bloque C (5 partidas) se esperan ~1–2 acusaciones y **ninguna** Contra-acusación. | 🔴 |
| 7 | **Hay una mano vacía posible sin regla:** una Formal fallida con Contra-acusación hace descartar 4 de 5 cartas, y con una Declaración encima te quedas con 0. Entonces la Reconversión no se puede usar. | 🟡 |
| 8 | **Ventaja de asiento: ninguna** (≤ 2 puntos). La mano inicial pesa poco. ✅ | ✅ |
| 9 | **Reconversión cumple pero aporta poco:** completa identidad en ~29% de los usos y baja Nadie solo 0,1–0,2 por partida. | 🟡 |

---

## 1. Lo que la V1.2.2 ha corregido ✅

| Problema anterior | Respuesta V1.2.2 | Veredicto |
|---|---|---|
| Contra-acusación sin efecto | Reacción que duplica la penalización o cuesta 1 carta | Tiene efecto, pero ver §4 |
| Quedarse con 3 cartas tras acusar | Límite explícito y sin reposición | ✅ |
| Mazo agotado | Se baraja el descarte | ✅ |
| Revelar con 5 cartas | Solo con 4 cartas | Choca con el orden del turno (ver §2) |
| Revelación falsa sin consecuencia clara | Bloqueado | ✅ |
| Bloqueado ambiguo | Estado final y conserva Cazador | ✅ |
| Puntuación con incentivos perversos | Suspendida (Modo Normal) | ✅ Resuelto. Pero ver §3: sin puntos, «fijar» no cuesta nada |
| Atributos tapados en abanico | Índice compacto en la esquina | ✅ Hay que validarlo en físico |
| «1.296 combinaciones» | La Biblia lo corrige: 32 casos | ✅ (el Dossier V1.2.2 ya no lo dice) |
| Errores de verificación | Moderador que confirma Sí/No | ✅ |
| Detective inalcanzable (1%) | 2 Evidencias + Declaración | ✅ Detective sale en el 7–8% |

## 2. Reglas: huecos y contradicciones

### 🔴 2.1 Orden del turno frente a Revelar y frente al límite de mano

Hay dos lecturas posibles y ninguna funciona tal como está escrita:

- **El límite de mano NO se aplica tras robar:** en ACTUAR tienes 5 cartas y §12 exige tener 4
  para revelar. Entonces **solo podrías revelar tras una Reconversión**, que es la única forma de
  llegar a ACTUAR con 4 cartas.
- **El límite de mano SÍ se aplica tras robar** (§9: «tras resolver cualquier efecto»): el paso 3
  DESCARTAR sobra. Además, Cómplice te deja con 3 cartas: juegas Cómplice (3), robas (4) y
  entregas (3).

Redacción propuesta:

> «En rondas 9–10, si quieres Revelar, primero descarta hasta 4 y después revela. El límite de
> mano inmediato se aplica a los efectos de otros jugadores (acusaciones, Contra-acusación), no a
> tu propio robo.»

El simulador usa esta lectura.

### 🟠 2.2 Otros huecos

| Regla | Duda que surgirá en mesa | Propuesta |
|---|---|---|
| §12 / §5 | Mi mano forma Testigo y Cómplice a la vez. Si anuncio «Cómplice», ¿quedo Bloqueado? La mano *puede* formarlo legalmente, pero la prioridad dice que soy Testigo. | «Anuncias la identidad de mayor prioridad que forma tu mano; si anuncias otra válida, se corrige sin penalización.» |
| §13.2 | La misma mano (Testigo + Cómplice) es Testigo por prioridad, pero «puede formar Cómplice». ¿La Acusación de Cómplice acierta? | Decidir y escribirlo. El simulador da acierto. |
| §12 «Sigues participando socialmente» | ¿El jugador que ha fijado identidad sigue jugando turnos? ¿Se le puede robar con Cómplice o mirar con Testigo? Si sí, su mano es un **banco gratuito**: robar a un Asesino fijado no le cuesta nada. | «Quien fija identidad sale del orden de turno y su mano es intocable.» |
| §13.3 | «Tú robas 1»: ¿además del robo normal del acusado tras una Formal fallida (2 en total) o es el mismo? | Aclarar. El simulador roba 1. |
| §13.2 | Acusación de Cómplice fallida: «descartas 1 carta», ¿al azar o elegida? (en la Formal es al azar). | Aclarar. El simulador la deja elegir. |
| §13.3 | Una Formal fallida con Contra-acusación son 4 descartes al azar de 5 cartas. Si después pierdes otra, te quedas con 0. ¿Puedes Reconvertir con la mano vacía? | «Si no tienes cartas, la Reconversión empieza robando 2.» |
| §10 Testigo | «Durante unos segundos». | «Cuenta hasta 5 en voz alta.» |
| §10 Declaración | ¿Se nombra la categoría y vale la Escena con el **valor del Crimen**? Si el jugador no tiene ninguna, ¿lo dice en voz alta? | Aclarar las dos cosas: lo segundo es información para toda la mesa. |
| §11 | ¿Puede reconvertir un Bloqueado? | «Sí» (no le salva, pero mueve cartas) o «No». Decidirlo. |

## 3. Equilibrio de identidades (V1.2.2, 3.000 partidas por tamaño)

| | 4 jug. | 6 jug. | 8 jug. |
|---|---|---|---|
| Sobreviven | 86% | 85% | 84% |
| Nadie + Bloqueados por partida | 0,56 | 0,91 | 1,26 |
| **Partidas sin ningún perdedor** | **58%** | 38% | 26% |
| Asesino | 17,8% | 17,5% | 17,0% |
| Detective | 8,1% | 7,5% | 7,2% |
| **Cómplice** | **34,4%** | **34,1%** | **34,4%** |
| Testigo | 25,6% | 25,7% | 25,7% |
| Acusaciones por partida | 0,11 | 0,22 | 0,35 |
| Contra-acusaciones jugadas por partida | 0,02 | 0,05 | 0,07 |
| Reconversiones por partida (y % que completan identidad) | 0,73 (29%) | 1,21 (30%) | 1,68 (29%) |
| De quienes pudieron revelar, cuántos revelaron | 67% | 66% | 66% |
| Calculador frente a novato (supervivencia) | 90% / 79% | 90% / 76% | 90% / 75% |
| Duración estimada | 18 min | 28 min | 37 min |

**Lectura:**

- **Cómplice es la «válvula de rescate dominante»** que el Dossier temía. Necesita 1 Cómplice
  (hay 6) y 2 Escenas de 3 atributos posibles, que con la 4.ª carta libre es muy flexible.
- **Testigo** (Asesino + Lugar + Testigo) también es muy accesible.
- **Asesino** es la única identidad de 4 cartas y queda relegada al tercer puesto. Es un problema
  de tema: el juego se llama *Yo soy un asesino*.
- **Nadie ya no es una amenaza:** a 4 jugadores, en más de la mitad de las partidas nadie pierde.
  El Dossier V1.2.2 renuncia a perseguir un porcentaje y lo acepto. Pero la versión anterior decía
  que «Nadie es la amenaza que da tensión al juego» y el cuestionario pregunta «¿Nadie se siente
  justo?». Con este reparto habrá muy pocos Nadie para responderlo.
- **Las acusaciones pasan de 1–2 por partida a 0,1–0,35:** las rondas 9–10 pierden su pico
  dramático. El 43–45% de los jugadores sigue teniendo una decisión tensa, pero casi siempre es
  «revelo o espero», no «acuso o no».

## 4. Contra-acusación: el «doble riesgo» es ilusorio 🟠

- **Si te acusan en falso,** jugarla duplica el castigo del acusador. Gana siempre.
- **Si te acusan con razón,** quedas Bloqueado igualmente. Ya no puedes sobrevivir y conservas tu
  Cazador si lo tenías. **Descartar 1 carta extra no te cuesta nada.**

Conclusión: **jugarla siempre es lo correcto**. El Reglamento ya lo intuye en §20 («¿reacción
demasiado obvia?»): la respuesta es sí, por construcción.

Para que el riesgo exista, la penalización por usarla siendo culpable tiene que tocar algo que
un Bloqueado aún valora:

- «…pierdes cualquier Cazador y el acusador roba 2», o
- «…tu siguiente turno lo juega el acusador con tu mano» (saboteo inverso, más temático).

Además, con 0,02–0,07 usos por partida **no se va a ver en el playtest** (ver §7).

## 5. Estrategias dominantes / explotables

*(se completa con la batería de estrategias más abajo)*

## 6. Variantes de una sola variable (2.000 partidas por fila)

Respetando el criterio del Dossier (§11): cambiar una variable principal por serie.

| Variante sobre V1.2.2 | Nadie 4/6/8 j | Sin perdedores (4j) | Asesino | Cómplice | Testigo | Acusaciones (6j) |
|---|---|---|---|---|---|---|
| **V1.2.2 tal cual** | 0,54 / 0,91 / 1,27 | 58% | 17% | 35% | 25% | 0,21 |
| Sin Reconversión | 0,64 / 1,05 / 1,46 | 52% | 17% | 34% | 25% | 0,24 |
| Cómplice: sus 2 Escenas deben incluir el Asesino | 0,76 / 1,24 / 1,73 | 46% | 18% | 29% | 26% | 0,25 |
| **Cómplice = Cómplice + Asesino + Arma + Lugar** | **1,19 / 1,80 / 2,51** | **27%** | **22%** | **14%** | 24% | 0,35 |
| Testigo vuelve a pedir Declaración | 0,66 / 1,08 / 1,51 | 51% | 24% | **47%** | 2% | 0,28 |
| Cazador vuelve a salvar a un Nadie | 0,56 / 0,91 / 1,28 | 56% | 17% | 34% | 26% | **0,48** |
| Cómplice con Asesino + Cazador salva | 0,75 / 1,26 / 1,71 | 45% | 16% | 28% | 26% | 0,64 |

**Conclusiones:**

1. **Si el playtest confirma que Cómplice domina, la palanca es Cómplice de 3 atributos (4
   cartas).** Es el único cambio que devuelve Nadie a ~1 con 4 jugadores y 2–3 con 8, y además
   sube Asesino al primer puesto. Toca un «requisito de identidad», así que según el propio
   Dossier es materia de V1.3, no del playtest actual.
2. **No hay que volver a pedir Declaración para Testigo:** mata a Testigo (2%) y dispara Cómplice
   (47%).
3. **Si se quiere recuperar el drama de las acusaciones, Cazador debe volver a salvar a un
   Nadie:** las acusaciones se duplican sin cambiar Nadie.
4. **Reconversión vale como red de seguridad,** pero su efecto es pequeño (−0,1 a −0,2 Nadie). Su
   valor real será psicológico («me devolvió opciones»), que es justo lo que mide la pregunta 4
   del cuestionario.

## 7. Plan de playtest 🔴

Con la V1.2.2, el número de eventos esperados en el **plan de 20 partidas** (supuesto de unas 6
jugadores por partida) es este:

| Pregunta del Dossier | Eventos por partida | En su bloque (5 partidas) | ¿Se puede responder? |
|---|---|---|---|
| ¿Nadie se siente justo? (bloque B) | ~0,9 Nadie | ~4–5 Nadie | Apenas |
| ¿Contra-acusación funciona? (bloque C) | 0,05 usos | **~0,25 usos** | **No** |
| Acusaciones (bloque C) | 0,22 | ~1 | **No** |
| ¿Cómplice domina? | 2 Cómplices | ~40 en 20 partidas | Sí |
| ¿Revelar es una decisión? | ~3,5 jugadores pueden revelar | ~70 casos | Sí |
| Duración | 1 dato por partida | 20 datos | Sí |

**Recomendación:** para las preguntas de acusación y Contra-acusación, añadir **escenarios
guiados**: partidas que arrancan en la ronda 9 con manos preparadas, por ejemplo un Asesino
completo, un Cómplice y dos jugadores perdidos con Formal y Contra. Así se observan decenas de
acusaciones en una tarde.

**Añadir a la hoja de registro:**

- Asiento de cada jugador.
- Para cada Nadie, cuántas cartas le faltaban.
- Si quien fijó identidad podía haber fijado otra.

## 8. Producción (Biblia) 🟡

- **El listado maestro de las 72 Escenas no existe** (lo reconoce la propia Biblia, §3.2), y
  bloquea la impresión.
- **Al crearlo, controlar las cartas «dobles».** En la simulación, el nº de Escenas que coinciden
  con 2 o más elementos de un mismo Crimen varía entre 4 y 16 (media 9,5). El efecto es pequeño:
  Asesino pasa del 19,3% con ≤6 dobles al 16,2% con ≥13, y Nadie no cambia.
- **Recomendación:** al cerrar el listado, comprobar contra los 32 Crímenes que cada caso tenga
  entre 7 y 12 Escenas dobles, para que ningún caso sea notablemente distinto.
- **Fundas opacas, tamaños e impresión al 100%:** correcto ✅.
- **Índice de abanico:** correcto como especificación ✅. Hay que medirlo con la pregunta 11 del
  cuestionario.

## 9. Robustez

*(se completa más abajo)*

## 10. Plan de acción

*(se completa más abajo)*
