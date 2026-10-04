#!/usr/bin/env python3
"""
Auditoría de YO SOY UN ASESINO.

  1. Comprobaciones estáticas de componentes (conteos, equilibrio, probabilidades).
  2. Ventaja por asiento / orden de turno.
  3. Estrategias dominantes o explotables: un jugador "calculador" con una estrategia
     fija frente al mismo jugador jugando con normalidad (control).
  4. Puntuación: puntos medios por identidad y valor esperado de acusar.
  5. Robustez: ¿se mantienen las conclusiones si los humanos son más/menos hábiles,
     no leen la mesa, olvidan más o no cometen errores de reglas?

Uso:  python3 auditoria.py [--partidas 3000]
"""
import argparse
import copy
import math
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from multiprocessing import Pool

import asesino as A


def correr(R, n, partidas, estr=None, seed=7, mesa='mixta'):
    tareas = [(R, n, seed * 100003 + i, mesa) + ((estr,) if estr else ()) for i in range(partidas)]
    with Pool(4) as pool:
        return pool.map(A.jugar_partida, tareas, chunksize=max(1, partidas // 32))


def pct(x):
    return f"{x * 100:5.1f}%"


# ------------------------------------------------------------------
def estaticas():
    print("\n## 1. Componentes y probabilidades básicas\n")
    R = A.reglas('V1.0')
    total = R['escenas'] + 24 + R['complice'] + R['testigo'] + R['declaracion']
    print(f"- Mazo principal: {R['escenas']} Escenas + 24 Evidencias + "
          f"{R['complice'] + R['testigo'] + R['declaracion']} Especiales = {total} (reglamento: 112)")
    per = R['escenas'] // R['simbolos']
    print(f"- Cada valor de cada categoría aparece en {per} Escenas "
          f"({per}/{total} = {per / total * 100:.1f}% por robo).")
    pares = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    for e in range(4):
        comp = sum(1 for p in pares if e in p)
        assert comp == 3
    print("- Evidencias: cada expediente aparece en 3 de los 6 pares → 12 Evidencias compatibles "
          "(3 por tipo). Equilibrado ✔")
    p1 = 1 - (5 / 6) ** 4
    p2 = 1 - (5 / 6) ** 4 - 4 * (1 / 6) * (5 / 6) ** 3
    print(f"- Una Escena al azar coincide con ≥1 elemento del crimen: {p1 * 100:.1f}%; con ≥2: {p2 * 100:.1f}%.")
    print("  → Más de la mitad de las Escenas «parecen útiles»: el descarte casi siempre ofrece algo "
          "y la regla «una carta = un atributo» se pone a prueba constantemente.")
    for n in range(4, 9):
        p_sin = math.comb(4, n) / math.comb(8, n) if n <= 4 else 0
        print(f"- {n} jugadores: Acusaciones repartidas {n}/8; prob. de que no haya ninguna Formal "
              f"en mesa: {p_sin * 100:.1f}%; mazo tras el reparto: {total - 4 * n - 1} cartas para "
              f"{n * 10} robos.")
    print(f"- Cartas de Crimen: 32 prediseñadas, pero el dossier vende «1.296 combinaciones». "
          f"Son 32 casos jugables ({32 / 1296 * 100:.1f}% del espacio).")
    print("- Suministro máximo simultáneo: Cómplice 6 · Testigo 5 · Declaración 5 → como mucho "
          "5 jugadores pueden ser Detective o Testigo a la vez, y cada Declaración usada como "
          "ataque reduce ese techo.")


# ------------------------------------------------------------------
VARS = ['V1.0', 'V1.1']


def asientos(partidas):
    print("\n## 2. Ventaja por asiento (orden de turno, asiento 1 = jugador inicial)\n")
    for v in VARS:
        R = A.reglas(v)
        for n in (4, 6, 8):
            out = correr(R, n, partidas)
            surv = defaultdict(list)
            pts = defaultdict(list)
            for o in out:
                for f in o['filas']:
                    surv[f['asiento']].append(f['sobrevive'])
                    pts[f['asiento']].append(f['puntos'])
            fila = ' '.join(f"{statistics.mean(surv[a]) * 100:4.0f}%" for a in range(n))
            rango = (max(statistics.mean(surv[a]) for a in range(n))
                     - min(statistics.mean(surv[a]) for a in range(n)))
            print(f"- {v} {n}j supervivencia por asiento: {fila}   (diferencia máx {rango * 100:.0f} pts)")


# ------------------------------------------------------------------
ESTRATEGIAS = [
    ('control', 'juega normal (referencia)'),
    ('solo_asesino', 'solo persigue Asesino'),
    ('solo_complice', 'solo persigue Cómplice'),
    ('solo_testigo', 'solo persigue Testigo'),
    ('solo_detective', 'solo persigue Detective'),
    ('sin_especiales', 'nunca juega especiales (los guarda)'),
    ('especiales_siempre', 'juega cada especial en cuanto lo roba'),
    ('acaparador', 'nunca suelta cartas del crimen (negar al rival)'),
    ('revela_ya', 'se revela en cuanto puede'),
    ('nunca_revela', 'nunca se revela (espera a la Forzada)'),
    ('nunca_acusa', 'nunca acusa'),
    ('acusa_siempre', 'acusa siempre en Sospecha'),
]
ESTRATEGIAS_V12 = [
    ('nunca_reconvierte', 'nunca usa Reconversión'),
    ('reconvierte_ya', 'reconvierte en la ronda 9 si no tiene identidad'),
]


def estrategias(partidas):
    print("\n## 3. Estrategias dominantes / explotables\n")
    print("Jugador 0 = perfil calculador con estrategia fija; resto de la mesa mixta. "
          "Δ = diferencia frente a 'control'.\n")
    for v in VARS:
        R = A.reglas(v)
        lista = ESTRATEGIAS + (ESTRATEGIAS_V12 if R['v12'] else [])
        for n in (4, 6):
            print(f"### {v} — {n} jugadores\n")
            print("| Estrategia | Sobrevive | Δ | Puntos | Δ |")
            print("|---|---|---|---|---|")
            base = None
            for e, desc in lista:
                out = correr(R, n, partidas, estr=(e, 'calculador'))
                f0 = [next(f for f in o['filas'] if f['id'] == 0) for o in out]
                s = statistics.mean(f['sobrevive'] for f in f0)
                p = statistics.mean(f['puntos'] for f in f0)
                if base is None:
                    base = (s, p)
                print(f"| {desc} | {pct(s)} | {(s - base[0]) * 100:+.1f} | {p:.2f} | {p - base[1]:+.2f} |")
            print()


# ------------------------------------------------------------------
def puntuacion(partidas):
    print("\n## 4. Puntuación\n")
    for v in VARS:
        R = A.reglas(v)
        if R['v12']:
            print(f"### {v}: Modo Normal sin puntos (§18) — no aplica.\n")
            continue
        out = correr(R, 6, partidas)
        por = defaultdict(list)
        frec = Counter()
        for o in out:
            for f in o['filas']:
                por[f['ident']].append(f['puntos'])
                frec[f['ident']] += 1
        tot = sum(frec.values())
        print(f"### {v} — 6 jugadores\n")
        print("| Resultado | Frecuencia | Puntos medios (con bonus) | Puntos base |")
        print("|---|---|---|---|")
        for k in ('detective', 'asesino', 'testigo', 'complice', 'cazador', 'bloqueado', 'nadie'):
            if por[k]:
                print(f"| {k} | {pct(frec[k] / tot)} | {statistics.mean(por[k]):.2f} | {A.PUNTOS[k]} |")
        ev = Counter()
        for o in out:
            ev.update(o['ev'])
        for t, g, p in (('formal', 2, 1), ('complice', 1, 1)):
            n_ = ev[f'acusa_{t}']
            if n_:
                a = ev[f'acusa_{t}_exito'] / n_
                print(f"\n- Acusación {t}: acierto {a * 100:.0f}% → valor esperado en puntos "
                      f"{a * g - (1 - a) * p:+.2f} por acusación (sin contar Cazador ni el daño a la mano).")
        print()


# ------------------------------------------------------------------
AJUSTES = {
    'base': {},
    'más hábiles (+0.25)': dict(habilidad=+.25),
    'menos hábiles (−0.25)': dict(habilidad=-.25),
    'sin lectura de mesa': dict(lectura='x0'),
    'peor memoria (−0.3)': dict(memoria=-.3),
    'sin errores de regla': dict(error_regla='x0'),
}


def robustez(partidas):
    print("\n## 5. Robustez del simulador (¿cambian las conclusiones?)\n")
    print("| Supuesto humano | V1.0 4j | V1.1 4j | V1.0 8j | V1.1 8j | Det+Tes V1.0→V1.1 (6j) |")
    print("|---|---|---|---|---|---|")
    original = copy.deepcopy(A.PERFILES)
    for nombre, aj in AJUSTES.items():
        for p, d in A.PERFILES.items():
            d.clear()
            d.update(original[p])
            for k, delta in aj.items():
                d[k] = 0.0 if delta == 'x0' else min(1.0, max(0.0, d[k] + delta))
        celdas = []
        for n in (4, 8):
            for v in ('V1.0', 'V1.1'):
                out = correr(A.reglas(v), n, partidas)
                celdas.append(statistics.mean(sum(not f['sobrevive'] for f in o['filas']) for o in out))
        dt = []
        for v in ('V1.0', 'V1.1'):
            out = correr(A.reglas(v), 6, partidas)
            fl = [f for o in out for f in o['filas']]
            dt.append(sum(f['ident'] in ('detective', 'testigo') for f in fl) / len(fl))
        print(f"| {nombre} | {celdas[0]:.2f} | {celdas[1]:.2f} | {celdas[2]:.2f} | {celdas[3]:.2f} | "
              f"{dt[0] * 100:.1f}% → {dt[1] * 100:.1f}% |", flush=True)
    for p, d in A.PERFILES.items():
        d.clear()
        d.update(original[p])


def robustez_v12(partidas):
    print("\n## 5b. Robustez de V1.2.2 (Nadie y Cómplice con distintos supuestos humanos)\n")
    print("| Supuesto humano | Nadie 4j | Nadie 8j | Cómplice 6j | Acusaciones 6j |")
    print("|---|---|---|---|---|")
    original = copy.deepcopy(A.PERFILES)
    casos = list(AJUSTES.items()) + [('Cazador vale 0 (solo orgullo)', 'caz0'),
                                     ('Cazador vale mucho (1.0)', 'caz1')]
    for nombre, aj in casos:
        R = A.reglas('V1.2.2')
        for p, d in A.PERFILES.items():
            d.clear()
            d.update(original[p])
            if isinstance(aj, dict):
                for k, delta in aj.items():
                    d[k] = 0.0 if delta == 'x0' else min(1.0, max(0.0, d[k] + delta))
        if aj == 'caz0':
            R['valor_cazador'] = 0.0
        if aj == 'caz1':
            R['valor_cazador'] = 1.0
        nad = []
        for n in (4, 8):
            out = correr(R, n, partidas)
            nad.append(statistics.mean(sum(not f['sobrevive'] for f in o['filas']) for o in out))
        out = correr(R, 6, partidas)
        fl = [f for o in out for f in o['filas']]
        comp = sum(f['ident'] == 'complice' for f in fl) / len(fl)
        acus = sum(o['ev'].get('acusa_formal', 0) + o['ev'].get('acusa_complice', 0) for o in out) / len(out)
        print(f"| {nombre} | {nad[0]:.2f} | {nad[1]:.2f} | {comp * 100:.1f}% | {acus:.2f} |", flush=True)
    for p, d in A.PERFILES.items():
        d.clear()
        d.update(original[p])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--partidas', type=int, default=3000)
    ap.add_argument('--solo', choices=['estaticas', 'asientos', 'estrategias', 'puntuacion', 'robustez',
                                       'robustez_v12'])
    ap.add_argument('--variantes', default='V1.0,V1.1', help='lista separada por comas')
    a = ap.parse_args()
    VARS[:] = a.variantes.split(',')
    pasos = dict(estaticas=lambda: estaticas(), asientos=lambda: asientos(a.partidas),
                 estrategias=lambda: estrategias(a.partidas), puntuacion=lambda: puntuacion(a.partidas),
                 robustez=lambda: robustez(a.partidas // 2),
                 robustez_v12=lambda: robustez_v12(a.partidas // 2))
    for k, f in pasos.items():
        if a.solo == k or (a.solo is None and k != 'robustez_v12'):
            f()


if __name__ == '__main__':
    main()
