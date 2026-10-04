# Auditoría de YO SOY UN ASESINO (Reglamento V1.0 + Dossier)

**Alcance.** Revisión del texto del reglamento y del dossier más simulación. Las pruebas son:

- 3.000 partidas por configuración.
- 12 estrategias forzadas para buscar jugadas dominantes.
- Ventaja por asiento.
- Análisis de la puntuación.
- Prueba de robustez: se repite todo cambiando los supuestos sobre cómo juegan las personas.

Los datos completos están en `simulador/resultados/auditoria.txt` y se reproducen con
`python3 simulador/auditoria.py`.

**Severidad:**

- 🔴 Rompe el juego o el playtest.
- 🟠 Afecta al equilibrio o a la experiencia.
- 🟡 Pulido.

---

## Resumen ejecutivo

| | Hallazgo | Sev. |
|---|---|---|
| 1 | Pierde demasiada gente: 1,7 Nadie por partida con 4 jugadores y 3,7 con 8 (objetivo ~1 y 2–3). | 🔴 |
| 2 | Detective (1%) y Testigo (3–4%) prácticamente no existen; jugar solo a Detective cuesta 17 puntos de supervivencia. | 🔴 |
| 3 | La Contra-acusación, tal como está escrita, no tiene efecto. | 🔴 |
| 4 | Hay 5 huecos de reglas que bloquean una partida real (cartas tras acusar, revelar con 5 cartas, mazo agotado…). | 🔴 |
| 5 | **Revelarse en cuanto puedes es la estrategia dominante** (+6 a +9 puntos de supervivencia). Seguir fingiendo nunca compensa sin la puntuación. | 🟠 |
| 6 | La puntuación premia mal: un Cazador (2+2 = 4) suma más que un Cómplice construido (3), y Asesino, la identidad más fácil, paga 5. | 🟠 |
| 7 | Las cartas especiales benefician más a la mesa que a quien las juega: guardarlas siempre rinde igual o mejor. | 🟠 |
| 8 | La Acusación de Cómplice tiene valor esperado negativo (−0,26 puntos) y no da Cazador. | 🟠 |
| 9 | Lectura en abanico: con un abanico normal solo se ve una esquina de cada carta, así que los atributos de la derecha y de abajo quedan tapados. | 🟠 |
| 10 | El dossier promete «1.296 combinaciones», pero solo hay 32 Crímenes; y 20–30 min es poco creíble con 8 jugadores (80 turnos). | 🟡 |

**Lo que está sano** (no tocar):

- No hay estrategia de negación rentable: acaparar cartas del crimen cuesta −1 a −2 puntos.
- Acusar con criterio rinde y no acusar nunca penaliza (−3 a −6 puntos).
- Ir siempre a por Asesino penaliza (−7 a −11 puntos), así que la identidad emergente sí se premia.
- La ventaja por asiento es pequeña (≤ 8 puntos).
- La mano inicial pesa poco.
- La habilidad cuenta sin ser determinante (calculador ~63% frente a novato ~45%).
- Las conclusiones no cambian aunque los humanos sean más o menos hábiles, olviden más o no lean la mesa.

---

## 1. Componentes 🟡/🟠

- **Los conteos cuadran:** 72 + 24 + 16 = 112. Hay 12 Escenas por valor y categoría (10,7% por robo). Las Evidencias están perfectamente equilibradas: 12 compatibles con cada expediente, 3 por tipo.
- **El 51,8% de las Escenas coincide con al menos un elemento del crimen y el 13,2% con dos o más.** Más de la mitad de las cartas «parecen útiles», así que la regla «una carta = un atributo» se pone a prueba en casi todos los turnos. Es la fuente del error más común: un 30% de los novatos simulados revela manos falsas.
- **Escasez:** solo hay 5 Testigos y 5 Declaraciones. Como mucho 5 jugadores pueden ser Detective o Testigo, y cada Declaración usada como ataque baja ese techo. Con 8 jugadores se gastan 3,7 Declaraciones por partida.
- **Mazo con 8 jugadores:** quedan 79 cartas para 80 robos. Sin regla de rebarajar, en teoría el mazo se agota. En la práctica no pasa, porque se roba mucho del descarte, pero la regla debe existir.
- **Acusaciones con 4 jugadores:** solo se reparten 4 de 8. Hay un 1,4% de partidas sin ninguna Formal en mesa; es aceptable.
- 🟠 **Lectura en abanico (no verificable en simulación, es ergonomía de cartas).** El dossier dice que el diseño en 4 bordes «permite leer las cartas en abanico». En un abanico normal se ve la esquina superior izquierda de cada carta. El borde derecho (Arma) y el inferior (Víctima) quedan tapados salvo en la última carta. **Recomendación:** repetir los 4 atributos como índice compacto en la esquina superior izquierda, como en una baraja de póker, y probarlo con el prototipo físico.
- 🟡 **Marketing:** «1.296 combinaciones» (6⁴) no es cierto para el producto: hay 32 Crímenes, el 2,5% de ese espacio. Mejor decir «32 casos» o «miles de partidas distintas».

## 2. Huecos de reglas que bloquean una partida 🔴

1. **Acusación Formal fallida.** Descartas 2 al azar con 5 cartas y te quedas con 3, pero §8 dice que terminas «obligatoriamente con 4».
2. **Acusado en falso.** Roba 1 fuera de turno y puede llegar a la Revelación Forzada con 5 cartas.
3. **Revelar.** En el paso de acción tienes 5 cartas y la regla dice «enseñas tus cuatro cartas».
4. **Contra-acusación.** Su efecto («la penalización recae sobre el acusador») ya ocurre siempre que se acusa en falso.
5. **Mazo agotado.** No hay regla.

Las redacciones propuestas para estos cinco puntos están en `REVISION_REGLAS.md`, §3.

**Otros huecos detectados en esta auditoría** 🟠:

- **Revelación con nombre equivocado.** ¿Qué pasa si digo «YO SOY ASESINO» y mi mano es de Cómplice? La regla dice que si la combinación es incorrecta eres Nadie. Debe aclararse si cuenta lo que anuncias o lo que enseñas. Recomendación: cuenta lo que enseñas.
- **Bloqueado y puntos.** §13 dice «su resultado final será 0», pero §16 da +2 por Acusación Formal correcta. ¿Un Bloqueado que acertó antes conserva el +2? ¿Puede la puntuación ser negativa? (Nadie con una acusación fallida termina con −1.) Recomendación: mínimo 0.
- **Declaración sin carta válida.** ¿Se dice en voz alta «no tengo»? Es información para toda la mesa; hay que fijarlo.
- **Testigo: «durante unos segundos».** Hay que fijar un tiempo, por ejemplo «cuenta hasta 5 en voz alta».
- **Contra-acusación frente a la Acusación de Cómplice.** ¿También sirve? La lógica dice que sí; hay que escribirlo.
- **Objetivos válidos.** Un jugador a salvo no puede ser acusado (está escrito), pero ¿puede ser objetivo de especiales? ¿Y un Bloqueado puede ser acusado o acusar? Recomendación: los jugadores a salvo son intocables y los Bloqueados no acusan.
- **§14:** «Si ningún jugador llegó a completar Asesino, ninguna Acusación Formal puede generar Cazador» es redundante con «acusación correcta». Se puede eliminar.

## 3. Estrategias dominantes y explotables 🟠

Prueba: un jugador calculador con una estrategia fija, frente al mismo jugador jugando con normalidad, durante 3.000 partidas. La diferencia (Δ) está en puntos de supervivencia; las diferencias de ±2 puntos o menos son ruido.

| Estrategia | V1.0 4j | V1.0 6j | V1.1 4j | V1.1 6j | Lectura |
|---|---|---|---|---|---|
| **Se revela en cuanto puede** | **+6,2** | **+5,6** | **+8,4** | **+8,8** | 🟠 Dominante en supervivencia. |
| Nunca se revela | −10,3 | −10,2 | −4,2 (+0,31 pts) | −4,4 (+0,26 pts) | V1.1 crea un dilema real, pero solo si se juega a puntos. |
| Nunca juega especiales | +1,6 | +2,3 | +1,1 | +1,6 | 🟠 Atacar no compensa al atacante. |
| Juega cada especial al robarlo | −6,8 | −8,5 | −12,1 | −8,8 | Bien: usarlos sin criterio se castiga. |
| Solo Asesino | −6,6 | −6,8 | −11,4 | −10,6 | ✅ La terquedad se castiga. |
| Solo Cómplice | +2,5 (−0,57 pts) | +2,1 | +0,1 (−1,03 pts) | +1,4 | Ruta segura y barata. Correcto. |
| Solo Detective | **−16,2** | **−17,3** | −4,6 (**+0,49 pts**) | −3,3 (+0,55 pts) | 🔴 en V1.0 es inviable; ✅ en V1.1 es riesgo alto con premio alto. |
| Solo Testigo | −8,7 | −10,1 | −6,1 | −1,5 | V1.1 lo hace viable con 6 jugadores. |
| Acapara cartas del crimen | −0,6 | −1,5 | −2,4 | −2,4 | ✅ La negación no es rentable. |
| Nunca acusa | −3,4 | −6,0 | −3,7 | −5,0 | ✅ Acusar aporta. |
| Acusa siempre | −4,2 | −4,9 | −12,0 | −8,9 | ✅ Acusar a ciegas se castiga. |

**Conclusiones:**

- **Revelarse ya es dominante si se juega a sobrevivir.** La promesa «puedes tener una identidad completa y seguir fingiendo» solo tiene sentido con puntuación. En V1.1, «Sangre fría» crea el dilema (más puntos frente a más riesgo), pero la puntuación es opcional (§16). **Recomendación:** que la puntuación sea la regla estándar, o dar a la supervivencia oculta una ventaja que no sea de puntos. Por ejemplo: quien sobrevive sin revelarse elige el Crimen de la siguiente partida, o desempata.
- **Los especiales son «take-that» con coste propio.** Quien ataca pierde una carta y una acción, y el beneficio se reparte entre todos los demás. **Propuesta a probar:**
  - **Declaración:** quien la juega puede quedarse la carta descartada por el objetivo en lugar de que vaya al descarte.
  - **Testigo:** además de mirar, puedes intercambiar 1 carta de tu mano con el mazo.

## 4. Puntuación 🟠

| Resultado (V1.0, 6j) | Frecuencia | Puntos base | Puntos medios reales |
|---|---|---|---|
| Detective | 0,9% | 6 | 6,0 |
| **Asesino** | **30,8%** | 5 | 5,1 |
| Testigo | 3,5% | 4 | 4,1 |
| Cómplice | 13,2% | 3 | 3,1 |
| **Cazador** | 6,8% | 2 | **4,0** (siempre lleva el +2 de la acusación) |
| Nadie | 35,2% | 0 | −0,36 |

- 🟠 **Un Cazador (4) puntúa más que un Cómplice construido (3).** Deducir pesa más que construir, lo que contradice que Cazador sea una «salida de emergencia». Corrección: Cazador vale 2 en total (sin el +2), o la Acusación Formal correcta suma +1.
- 🟠 **Los puntos no siguen a la dificultad.** Asesino es 2–5 veces más frecuente que Testigo y paga más (5 frente a 4). En V1.1, Testigo (6,3%) es tan raro como Detective (7,1%) y paga 2 puntos menos. Escala propuesta: Detective 6 · Testigo 5 · Asesino 4 · Cómplice 3 · Cazador 2. Si Asesino debe ser el «premio estrella» por tema, que sea 5 y Testigo también 5.
- 🟠 **La Acusación de Cómplice tiene valor esperado negativo:** −0,26 puntos en V1.0 y −0,11 en V1.1 (acierto del 37–44%, +1 si aciertas, −1 si fallas) y no da Cazador. Es una carta de rencor. Corrección: si aciertas, +2 y Cazador como en la Formal.

## 5. Asiento y orden de turno ✅

Supervivencia por asiento (el asiento 1 es el jugador inicial):

| | Asiento 1 → último | Diferencia |
|---|---|---|
| V1.0 4j | 58 · 56 · 57 · 54 | 5 pts |
| V1.0 8j | 58 · 57 · 57 · 55 · 54 · 54 · 52 · 51 | 7 pts |
| V1.1 4j | 63 · 66 · 68 · 70 | 7 pts |
| V1.1 8j | 65 · 64 · 65 · 64 · 67 · 65 · 65 · 67 | 3 pts |

- En la V1.0, los primeros asientos tienen algo de ventaja con 8 jugadores: roban antes las cartas del crimen y acusan antes en la ronda 9.
- En la V1.1 con 4 jugadores la ventaja se invierte: los últimos ven más descarte con el Mercado de 2.
- En ambos casos es moderado. Si el playtest lo confirma, el último jugador puede empezar con 5 cartas y descartar 1.

## 6. Experiencia y ritmo 🟡

- **Eliminación de jugadores:**
  - Quien se revela pierde 1–2 turnos. Es aceptable.
  - Quien queda Bloqueado juega hasta el final como saboteador: se destruyen 1,5–2,6 identidades por partida. Da drama, pero un jugador sin nada que ganar decide quién pierde (*kingmaking*). Hay que vigilarlo en mesa. Opción: que un Bloqueado puntúe +1 si ayuda a bloquear o destruir a otro.
- **Duración:** 80 turnos con 8 jugadores. Con ~25 s por turno son unos 38 min estimados. Hay que cronometrarlo; si se confirma, comunicar «4–6 jugadores (hasta 8)».
- **Errores de §4:** hay 0,06–0,11 revelaciones falsas por partida en mesas mixtas. Cada una elimina a un jugador por no entender una regla, y es la peor frustración posible para un novato. Recomendaciones:
  - Un ejemplo visual en la carta de ayuda.
  - Para la primera partida, una regla de cortesía: «si revelas mal, recuperas tus cartas y pierdes el turno».

## 7. Robustez del propio simulador

Las conclusiones se mantienen con todos los supuestos sobre cómo juegan las personas:

| Supuesto | Nadie V1.0→V1.1 (4j) | Nadie V1.0→V1.1 (8j) | Detective+Testigo V1.0→V1.1 |
|---|---|---|---|
| Base | 1,74 → 1,31 | 3,65 → 2,79 | 4,5% → 13,1% |
| Más hábiles | 1,72 → 1,24 | 3,69 → 2,69 | 4,4% → 14,0% |
| Menos hábiles | 1,89 → 1,50 | 3,93 → 3,10 | 4,3% → 12,6% |
| Sin lectura de mesa | 1,70 → 1,31 | 3,57 → 2,71 | 4,9% → 13,2% |
| Peor memoria | 1,71 → 1,31 | 3,68 → 2,69 | 4,3% → 12,7% |
| Sin errores de regla | 1,69 → 1,22 | 3,51 → 2,60 | 4,6% → 13,5% |

**Auditoría del simulador:**

- He corregido un fallo propio: al decidir si acusar, el agente valoraba 4 cartas cualquiera de sus 5. Los resultados no cambian.
- Hay comprobación de que ninguna carta se duplica ni se pierde en ninguna variante.
- La duración sigue siendo un modelo, no una medida.

## 8. Plan de acción recomendado

1. 🔴 Antes de imprimir: reescribir los 5 huecos de reglas (`REVISION_REGLAS.md` §3) y la Contra-acusación.
2. 🔴 Adoptar la V1.1 para el playtest: Mercado de 2, Detective con 2 tipos, 6 Declaraciones, Contra-acusación que bloquea y Sangre fría.
3. 🟠 Corregir la puntuación: Cazador 2 en total, revisar Asesino/Testigo, mejorar la Acusación de Cómplice, mínimo 0 puntos.
4. 🟠 Hacer que la puntuación sea la regla estándar, o dar otra recompensa a seguir oculto.
5. 🟠 Añadir el índice de esquina en las Escenas y probarlo físicamente.
6. 🟡 En las 20 partidas registradas: cronometrar, anotar el asiento, las revelaciones falsas y preguntar a los perdedores «¿te faltó poco?».
