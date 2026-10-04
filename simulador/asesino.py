#!/usr/bin/env python3
"""
YO SOY UN ASESINO — Simulador de playtest con jugadores humanos realistas
==========================================================================

Implementa el Reglamento V1.0 (y variantes configurables) y lo juega con
agentes que imitan a personas reales, no a ordenadores perfectos:

  * Racionalidad limitada: valoran la mano con una estimación de
    probabilidades ("¿cuántas cartas me sirven todavía?") con ruido según
    su habilidad.
  * Memoria imperfecta: recuerdan solo parte del descarte y de lo que han
    visto con un Testigo ("unos segundos, sin notas"), y olvidan con el
    tiempo.
  * Errores de reglas: algunos novatos no interiorizan «una carta = un
    atributo», se creen con identidad y revelan una mano falsa.
  * Terquedad: cuesta cambiar de objetivo aunque otro sea algo mejor.
  * Lectura de mesa y cara de póker: los jugadores transparentes dan
    pistas; los buenos lectores las captan.
  * Farol: el farsante recoge del descarte cartas «de Asesino» para atraer
    acusaciones falsas.
  * Rencor del eliminado: un Bloqueado acapara cartas del crimen y ataca
    al líder.

Además de quién gana, mide si la partida *engancha*: cuántos Nadie pierden
por una sola carta, cambios de objetivo, tensión en Sospecha, interacción,
variedad de identidades, peso de la habilidad frente a la suerte, etc.

Uso rápido:
    python3 asesino.py                          # informe V1.0, 4/6/8 jugadores
    python3 asesino.py --variante V1.1          # informe de la propuesta
    python3 asesino.py --comparar               # tabla de todas las variantes
    python3 asesino.py --cronica --jugadores 5  # narra una partida turno a turno
"""

import argparse
import math
import random
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from multiprocessing import Pool


# ============================================================
# CODIFICACIÓN DE CARTAS (bits de "qué puede representar")
# ============================================================
CH, WE, VI, RO = 1, 2, 4, 8          # escena coincide con asesino/arma/víctima/lugar
CO, TE, DE = 16, 32, 64              # Cómplice / Testigo / Declaración
EV_TIPOS = ('huella', 'motivo', 'coartada', 'prueba')
EVB = {t: 128 << i for i, t in enumerate(EV_TIPOS)}
EV_ALL = 128 | 256 | 512 | 1024
ESCENA_BITS = (CH, WE, VI, RO)
ATRIBUTOS = ('asesino', 'arma', 'víctima', 'lugar')

HUECOS = {
    'asesino':  (CH, WE, VI, RO),
    'complice': (CH, WE, RO, CO),
    'testigo':  (CH, RO, TE, DE),
}
IDENTIDADES = ('asesino', 'detective', 'complice', 'testigo')
PRIORIDAD = ('detective', 'asesino', 'testigo', 'complice')
PUNTOS = {'detective': 6, 'asesino': 5, 'testigo': 4, 'complice': 3,
          'cazador': 2, 'nadie': 0, 'bloqueado': 0}
ESPECIALES = ('complice', 'testigo', 'declaracion')
EXPEDIENTES = '●▲■★'


def popcount(x):
    return bin(x).count('1')


# ============================================================
# REGLAS Y VARIANTES
# ============================================================
REGLAS_V10 = dict(
    nombre='V1.0',
    descripcion='Reglamento V1.0 tal cual',
    escenas=72, simbolos=6,
    complice=6, testigo=5, declaracion=5,
    mano=4, construccion=8, sospecha=2,
    acc_formal=4, acc_complice=2, acc_contra=2,
    mercado=1,          # cartas superiores del descarte que se pueden tomar
    robo_ciego=1,       # cartas que se roban del mazo (luego se descarta hasta 'mano')
    contra='literal',   # 'literal': igual que una acusación fallida normal
                        # 'bloquea': el acusador en falso queda Bloqueado
    fallo_formal=2,     # cartas al azar que pierde el acusador si falla
    revelar_temprano_bonus=0,   # puntos extra si sobrevives sin revelarte
    det_tipos=3,                # tipos distintos de Evidencia que exige Detective
    draft=0,                    # cartas extra en el reparto inicial (luego te quedas 'mano')
    v12=False,                  # identidades, acusaciones y final del Reglamento V1.2.2
    reconversion=False,         # V1.2.2 §11: una vez, rondas 9–10
    valor_cazador=0.35,         # cuánto valora un humano el reconocimiento Cazador (0–1)
    contra_si_culpable=0.6,     # prob. de jugar Contra-acusación aunque la acusación sea cierta
    complice_def='v12',         # 'v12' | 'con_asesino' | 'tres'
    testigo_def='v12',          # 'v12' | 'con_decl'
    cazador_salva=False,        # V1.2.2: Cazador NO da supervivencia
)

VARIANTES = {
    'V1.0': {},
    '96esc': dict(nombre='96 escenas', descripcion='Variable de playtest §18: 96 Escenas',
                  escenas=96),
    '10constr': dict(nombre='10 rondas constr.',
                     descripcion='Variable §18: 10 rondas de Construcción + 2 de Sospecha',
                     construccion=10),
    'mercado2': dict(nombre='Mercado de 2',
                     descripcion='Puedes tomar cualquiera de las 2 cartas superiores del descarte',
                     mercado=2),
    'robo2': dict(nombre='Roba 2 del mazo',
                  descripcion='Al robar del mazo coges 2 y descartas hasta 4',
                  robo_ciego=2),
    'contra': dict(nombre='Contra bloquea',
                   descripcion='Contra-acusación: el acusador en falso queda Bloqueado',
                   contra='bloquea'),
    'mano5': dict(nombre='Mano de 5',
                  descripcion='Terminas el turno con 5 cartas; la identidad usa 4 de ellas',
                  mano=5),
    'det2': dict(nombre='Detective 2 tipos',
                 descripcion='Detective: 3 Evidencias compatibles con al menos 2 tipos distintos',
                 det_tipos=2),
    'decl7': dict(nombre='7 Declaraciones',
                  descripcion='7 Declaraciones y 6 Testigos (menos cuello de botella)',
                  declaracion=7, testigo=6),
    'mercado2+contra': dict(nombre='Mercado 2 + Contra',
                            descripcion='Mercado de 2 + Contra-acusación que bloquea',
                            mercado=2, contra='bloquea'),
    'V1.2.2': dict(nombre='V1.2.2', descripcion='Reglamento consolidado V1.2.2 (Modo Normal)',
                   v12=True, reconversion=True),
    'V1.2.2-sinRec': dict(nombre='V1.2.2 sin Reconv.', descripcion='V1.2.2 sin Reconversión',
                          v12=True, reconversion=False),
    'V1.2.2+CómpAses': dict(nombre='V1.2.2 Cómplice c/Asesino',
                            descripcion='Cómplice: sus 2 Escenas deben incluir el Asesino',
                            v12=True, reconversion=True, complice_def='con_asesino'),
    'V1.2.2+Cómp3': dict(nombre='V1.2.2 Cómplice 3 atrib.',
                         descripcion='Cómplice: Cómplice + Asesino + Arma + Lugar (4 cartas)',
                         v12=True, reconversion=True, complice_def='tres'),
    'V1.2.2+TestDecl': dict(nombre='V1.2.2 Testigo c/Decl.',
                            descripcion='Testigo vuelve a pedir Declaración',
                            v12=True, reconversion=True, testigo_def='con_decl'),
    'V1.2.2+CazSalva': dict(nombre='V1.2.2 Cazador salva',
                            descripcion='Cazador vuelve a dar supervivencia si eres Nadie',
                            v12=True, reconversion=True, cazador_salva=True),
    'V1.3 candidata': dict(nombre='V1.3 candidata',
                           descripcion='V1.2.2 + Cómplice con Asesino + Cazador salva',
                           v12=True, reconversion=True, complice_def='con_asesino',
                           cazador_salva=True),
    'V1.1': dict(nombre='V1.1 propuesta',
                 descripcion='Mercado de 2 + Detective con 2 tipos + 6 Declaraciones + '
                             'Contra-acusación que bloquea + 2 puntos por sobrevivir sin revelarse',
                 mercado=2, det_tipos=2, declaracion=6, contra='bloquea',
                 revelar_temprano_bonus=2),
}


def reglas(nombre):
    R = dict(REGLAS_V10)
    R.update(VARIANTES[nombre])
    return R


# ============================================================
# PERFILES HUMANOS
# ============================================================
#  habilidad   : precisión al valorar la mano (0 = intuición pura, 1 = calcula)
#  memoria     : prob. de recordar una carta vista (descarte, Testigo)
#  error_regla : prob. de no entender «una carta = un atributo»
#  riesgo      : disposición a acusar con dudas
#  prudencia   : prob. de revelarse en cuanto tiene identidad en Sospecha
#  agresividad : ganas de usar especiales contra el líder
#  terquedad   : resistencia a cambiar de objetivo
#  farol       : tendencia a fingir que va a por Asesino
#  cara_poker  : cuánto disimula (1 = nada se le nota)
#  lectura     : cuánto capta de los demás
#  codicia     : preferencia por identidades de más puntos
PERFILES = {
    'novato':      dict(habilidad=.30, memoria=.35, error_regla=.30, riesgo=.35,
                        prudencia=.90, agresividad=.25, terquedad=.55, farol=.00,
                        cara_poker=.15, lectura=.15, codicia=.40),
    'casual':      dict(habilidad=.55, memoria=.50, error_regla=.08, riesgo=.40,
                        prudencia=.80, agresividad=.45, terquedad=.45, farol=.10,
                        cara_poker=.40, lectura=.35, codicia=.40),
    'calculador':  dict(habilidad=.92, memoria=.85, error_regla=.00, riesgo=.45,
                        prudencia=.60, agresividad=.50, terquedad=.15, farol=.15,
                        cara_poker=.70, lectura=.55, codicia=.50),
    'agresivo':    dict(habilidad=.60, memoria=.55, error_regla=.05, riesgo=.85,
                        prudencia=.40, agresividad=.95, terquedad=.35, farol=.25,
                        cara_poker=.45, lectura=.40, codicia=.70),
    'prudente':    dict(habilidad=.65, memoria=.60, error_regla=.03, riesgo=.10,
                        prudencia=1.0, agresividad=.15, terquedad=.50, farol=.00,
                        cara_poker=.55, lectura=.35, codicia=.20),
    'farsante':    dict(habilidad=.70, memoria=.65, error_regla=.02, riesgo=.55,
                        prudencia=.25, agresividad=.55, terquedad=.30, farol=.90,
                        cara_poker=.90, lectura=.50, codicia=.55),
    'codicioso':   dict(habilidad=.60, memoria=.55, error_regla=.05, riesgo=.55,
                        prudencia=.55, agresividad=.55, terquedad=.80, farol=.10,
                        cara_poker=.35, lectura=.30, codicia=1.0),
    'observador':  dict(habilidad=.70, memoria=.90, error_regla=.02, riesgo=.50,
                        prudencia=.70, agresividad=.35, terquedad=.30, farol=.10,
                        cara_poker=.60, lectura=.90, codicia=.40),
}

MESAS = {
    'mixta':   {p: 1 for p in PERFILES},
    'familia': dict(novato=4, casual=4, prudente=2, codicioso=1, agresivo=1),
    'jugones': dict(calculador=3, observador=2, farsante=2, agresivo=2, codicioso=1),
}


# ============================================================
# MEMO DE EMPAREJAMIENTO (regla §4: una carta = un atributo)
# ============================================================
_FILL = {}
DET_TIPOS = [3]   # se fija por partida según las reglas
V12 = [False]     # True = requisitos de identidad del Reglamento V1.2.2
MODOS = {'complice': 'v12', 'testigo': 'v12'}   # variantes de identidad sobre V1.2.2

# V1.2.2: Asesino 4 Escenas; Testigo = Asesino + Lugar + Testigo; Cómplice = Cómplice +
# 2 de {Asesino, Arma, Lugar}; Detective = 2 Evidencias de tipos distintos + Declaración.
DEFS_V10 = {'asesino': ((CH, WE, VI, RO),), 'complice': ((CH, WE, RO, CO),),
            'testigo': ((CH, RO, TE, DE),)}
DEFS_V12 = {'asesino': ((CH, WE, VI, RO),),
            'complice': ((CO, CH, WE), (CO, CH, RO), (CO, WE, RO)),
            'testigo': ((CH, RO, TE),)}


def defs():
    if not V12[0]:
        return DEFS_V10
    d = dict(DEFS_V12)
    if MODOS['complice'] == 'con_asesino':      # las 2 Escenas deben incluir el Asesino
        d['complice'] = ((CO, CH, WE), (CO, CH, RO))
    elif MODOS['complice'] == 'tres':           # Cómplice + Asesino + Arma + Lugar
        d['complice'] = ((CO, CH, WE, RO),)
    if MODOS['testigo'] == 'con_decl':          # Testigo + Declaración (como V1.0)
        d['testigo'] = ((CH, RO, TE, DE),)
    return d


def det_req():
    """(nº de Evidencias, tipos distintos mínimos) que pide Detective."""
    return (2, 2) if V12[0] else (3, DET_TIPOS[0])


def util_mask(ident):
    if ident == 'detective':
        return EV_ALL | DE
    m = 0
    for alt in defs()[ident]:
        for s in alt:
            m |= s
    return m


def tam_ident(ident):
    if ident == 'detective':
        return det_req()[0] + 1
    return len(defs()[ident][0])


def rellenar(masks, ident, relajado=False):
    """Devuelve (huecos_cubiertos, tupla_de_huecos_que_faltan) para la mejor
    asignación carta→hueco. Con relajado=True una carta puede cubrir varios
    huecos (el error típico de novato)."""
    key = (masks, ident, relajado, DET_TIPOS[0], V12[0], MODOS['complice'], MODOS['testigo'])
    r = _FILL.get(key)
    if r is not None:
        return r
    if ident == 'detective':
        # n_req Evidencias compatibles con al menos k tipos distintos + Declaración
        n_req, k = det_req()
        have, decl, n_ev = 0, False, 0
        for m in masks:
            if m & EV_ALL:
                n_ev += 1
            have |= m & EV_ALL
            decl = decl or bool(m & DE)
        tipos = popcount(have)
        cubiertas = min(n_req, n_ev, tipos + (n_req - k))
        nuevas = max(0, k - tipos)
        falta = [EV_ALL & ~have] * nuevas + [EV_ALL] * max(0, n_req - cubiertas - nuevas)
        if not decl:
            falta.append(DE)
        r = (n_req + 1 - len(falta), tuple(falta))
    else:
        mejor = None
        for slots in defs()[ident]:
            L = len(slots)
            if relajado:
                falta = tuple(x for x in slots if not any(m & x for m in masks))
            else:
                union = 0
                for x in slots:
                    union |= x
                cand = [m for m in masks if m & union]
                best = [None]

                def rec(j, usado, falta_):
                    if best[0] is not None and len(falta_) >= len(best[0]):
                        return
                    if j == L:
                        best[0] = tuple(falta_)
                        return
                    sl = slots[j]
                    for i, m in enumerate(cand):
                        if not (usado >> i) & 1 and m & sl:
                            rec(j + 1, usado | (1 << i), falta_)
                    rec(j + 1, usado, falta_ + [sl])

                rec(0, 0, [])
                falta = best[0]
            if mejor is None or len(falta) < len(mejor[1]):
                mejor = (L - len(falta), falta)
        r = mejor
    _FILL[key] = r
    return r


def identidad_real(masks):
    """Identidad según el reglamento (§5 y prioridad de puntos)."""
    for ident in PRIORIDAD:
        if not rellenar(masks, ident)[1]:
            return ident
    return 'nadie'


def mejor_identidad_de(masks_mano, tam):
    """Si la mano tiene más de `tam` cartas, la mejor sub-mano válida."""
    if len(masks_mano) <= tam:
        return identidad_real(tuple(sorted(masks_mano)))
    best = 'nadie'
    for sub in combinations(masks_mano, tam):
        i = identidad_real(tuple(sorted(sub)))
        if i != 'nadie' and (best == 'nadie' or PUNTOS[i] > PUNTOS[best]):
            best = i
    return best


def faltan_min(masks):
    return min(len(rellenar(masks, i)[1]) for i in IDENTIDADES)


# ============================================================
# JUGADOR
# ============================================================
class Jugador:
    def __init__(self, pid, perfil, rng):
        self.id = pid
        self.perfil = perfil
        self.p = PERFILES[perfil]
        self.rng = rng
        self.mano = []
        self.estado = 'activo'      # activo | revelado | bloqueado | nadie
        self.acusacion = None       # 'formal' | 'complice' | 'contra' | None
        self.visto = set()          # cartas que sabe que NO están en el mazo
        self.conoce = defaultdict(set)   # otro jugador -> cartas que cree que tiene
        self.obj = None
        self.cambios = 0
        self.malentiende = rng.random() < self.p['error_regla']
        self.cazador_ok = False
        self.bonus = 0
        self.identidad_final = None
        self.revelo_ronda = None
        self.tuvo_identidad = False
        self.perdio_identidad = False
        self.decision_tensa = False
        self.ruido = (1 - self.p['habilidad']) * 0.12
        self._outs = {}
        self.w = {i: 1 + self.p['codicia'] * (PUNTOS[i] - 4.5) / 12 for i in IDENTIDADES}
        if V12[0]:                  # Modo Normal: sin puntos, toda identidad vale lo mismo
            self.w = {i: 1.0 for i in IDENTIDADES}
        self.reconv = False
        self.estr = None            # estrategia fija (auditoría de estrategias dominantes)
        self.asiento = None

    # ---------- conocimiento ----------
    def ver(self, c):
        if c not in self.visto:
            self.visto.add(c)
            self._outs.clear()

    def olvidar(self, c):
        if c in self.visto:
            self.visto.discard(c)
            self._outs.clear()

    def outs(self, req, g):
        o = self._outs.get(req)
        if o is None:
            o = sum(1 for c in g.ids_con(req) if c not in self.visto)
            self._outs[req] = o
        return o

    # ---------- valoración ----------
    def p_completar(self, falta, D, g):
        if not falta:
            return 1.0
        if len(falta) > D:
            return 0.0
        N = max(1, g.total - len(self.visto))
        d_eff = D * (1 + 0.25 * (g.R['mercado'] - 1) + 0.6 * (g.R['robo_ciego'] - 1)) * 1.15
        p = 1.0
        vistos = set()
        for req in falta:
            o = self.outs(req, g)
            if req in vistos:            # segundo hueco igual (Detective): menos outs
                o *= 0.6
            vistos.add(req)
            if o <= 0:
                return 0.0
            p *= 1 - (1 - min(1.0, o / N)) ** d_eff
        return p

    def valor(self, mano, D, g, descartadas=()):
        masks = tuple(sorted(g.mask[c] for c in mano))
        if self.estado in ('bloqueado', 'nadie'):
            # Rencor: acaparar cartas del crimen que necesitan los demás
            return sum(popcount(m & 15) + (1 if m & (CO | TE | DE) else 0)
                       for m in masks) / 10, None
        best = second = 0.0
        best_id = None
        cerca = 0
        for ident in IDENTIDADES:
            f, falta = rellenar(masks, ident, self.malentiende and ident != 'detective')
            P = self.p_completar(falta, D, g)
            w = self.w[ident]
            if ident == self.obj:
                w += self.p['terquedad'] * 0.15
            v = w * P
            cerca = max(cerca, f)
            if v > best:
                second, best, best_id = best, v, ident
            elif v > second:
                second = v
        v = best + 0.25 * second + 0.01 * cerca
        if self.p['farol'] > 0 and best_id != 'asesino' and g.ronda >= 5:
            v += self.p['farol'] * 0.02 * sum(1 for m in masks if m & 15)
        regalo = 0.25 if self.estr == 'acaparador' else self.p['habilidad'] * 0.015
        for c in descartadas:            # no regalar cartas del crimen al siguiente
            v -= regalo * popcount(g.mask[c] & 15)
        return v, best_id

    def mejor_mano(self, cartas, D, g, ruido=True):
        k = g.R['mano']
        if len(cartas) <= k:
            v, ident = self.valor(cartas, D, g)
            return v, list(cartas), [], ident
        best = None
        for keep in combinations(range(len(cartas)), k):
            mano = [cartas[i] for i in keep]
            fuera = [cartas[i] for i in range(len(cartas)) if i not in keep]
            v, ident = self.valor(mano, D, g, fuera)
            vr = v + (self.rng.gauss(0, self.ruido) if ruido else 0)
            if best is None or vr > best[0]:
                best = (vr, mano, fuera, ident, v)
        return best[4], best[1], best[2], best[3]

    def cree_identidad(self, g):
        """Lo que el jugador CREE que tiene (puede equivocarse)."""
        masks = tuple(sorted(g.mask[c] for c in self.mano[:g.R['mano']]))
        for ident in PRIORIDAD:
            rel = self.malentiende and ident != 'detective'
            if not rellenar(masks, ident, rel)[1]:
                return ident
        return None

    # ---------- lectura de los demás ----------
    def prob_identidad(self, j, ident, g):
        """Estimación humana de que j PUEDA formar `ident` ahora mismo."""
        # Lo que cree saber (puede incluir cartas que ya no tiene: memoria falible)
        conocidas = [c for c in self.conoce[j.id] if c in j.mano or self.rng.random() < .3][-4:]
        util = util_mask(ident)
        basura = sum(1 for c in conocidas if not g.mask[c] & util)
        if tam_ident(ident) < g.R['mano']:
            basura = max(0, basura - (g.R['mano'] - tam_ident(ident)))   # 4.ª carta libre
        f, _ = rellenar(tuple(sorted(g.mask[c] for c in conocidas)), ident)
        # Intuición de mesa: ~1 de cada 4-5 jugadores que siguen ocultos en
        # Sospecha "va de algo"; cada pieza útil vista la hace más creíble.
        previa = 0.22 if ident == 'asesino' else (0.25 if V12[0] else 0.12)
        odds = previa / (1 - previa) * (2.6 ** f)
        if basura and len(j.mano) <= g.R['mano']:
            # Con 4 cartas no cabe basura: el que calcula lo descarta; el novato no lo ve.
            odds *= 0.05 ** (basura * self.p['habilidad'])
        P = odds / (1 + odds)
        verdad = 1.0 if not rellenar(tuple(sorted(g.mask[c] for c in j.mano)), ident)[1] else 0.0
        lect = (1 - j.p['cara_poker']) * self.p['lectura'] * 0.45
        P = P + (verdad - P) * lect
        P *= math.exp(self.rng.gauss(0, 0.5 * (1 - self.p['habilidad'])))
        return max(0.0, min(0.97, P))

    def amenaza(self, j, g):
        """¿Cuánto creo que va ganando j? (para elegir víctima de especiales)."""
        k = sum(popcount(g.mask[c] & 15) + (1 if g.mask[c] & (CO | TE | DE | EV_ALL) else 0)
                for c in self.conoce[j.id] if c in j.mano)
        real = 4 - faltan_min(tuple(sorted(g.mask[c] for c in j.mano)))
        lect = (1 - j.p['cara_poker']) * self.p['lectura']
        return k * 0.5 + real * lect + self.rng.random() * 0.8


# ============================================================
# PARTIDA
# ============================================================
class Partida:
    def __init__(self, R, n, rng, mesa='mixta', cronica=False):
        self.R = R
        DET_TIPOS[0] = R['det_tipos']
        V12[0] = R['v12']
        MODOS['complice'] = R['complice_def']
        MODOS['testigo'] = R['testigo_def']
        self.rng = rng
        self.cronica = cronica
        self.log = []
        self.crimen = tuple(rng.randrange(R['simbolos']) for _ in range(4)) + (rng.randrange(4),)
        self.cartas = self._mazo()
        self.total = len(self.cartas)
        self.mask = [self._mascara(c) for c in self.cartas]
        self._ids = {}
        self.mazo = list(range(self.total))
        rng.shuffle(self.mazo)
        self.descarte = []
        pesos = MESAS[mesa]
        perfiles = rng.choices(list(pesos), weights=list(pesos.values()), k=n)
        self.jug = [Jugador(i, perfiles[i], rng) for i in range(n)]
        self.ronda = 0
        self.ev = Counter()           # contadores de acciones
        self.tiempo = 0.0             # segundos estimados

    # ---------- construcción ----------
    def _mazo(self):
        R = self.R
        per = R['escenas'] // R['simbolos']
        cols = []
        for _ in range(4):
            col = [s for s in range(R['simbolos']) for _ in range(per)]
            self.rng.shuffle(col)
            cols.append(col)
        cartas = [('escena', tuple(cols[a][i] for a in range(4))) for i in range(per * R['simbolos'])]
        pares = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        cartas += [('evidencia', (t, p)) for t in EV_TIPOS for p in pares]
        cartas += [('complice', None)] * R['complice']
        cartas += [('testigo', None)] * R['testigo']
        cartas += [('declaracion', None)] * R['declaracion']
        return cartas

    def _mascara(self, carta):
        k, d = carta
        if k == 'escena':
            return sum(b for i, b in enumerate(ESCENA_BITS) if d[i] == self.crimen[i])
        if k == 'evidencia':
            return EVB[d[0]] if self.crimen[4] in d[1] else 0
        return {'complice': CO, 'testigo': TE, 'declaracion': DE}[k]

    def ids_con(self, req):
        l = self._ids.get(req)
        if l is None:
            l = [c for c in range(self.total) if self.mask[c] & req]
            self._ids[req] = l
        return l

    def kind(self, c):
        return self.cartas[c][0]

    def nombre(self, c):
        k, d = self.cartas[c]
        if k == 'escena':
            marca = ''.join('✓' if d[i] == self.crimen[i] else '·' for i in range(4))
            return f"Escena[{marca}]"
        if k == 'evidencia':
            return f"{d[0].capitalize()} {EXPEDIENTES[d[1][0]]}{EXPEDIENTES[d[1][1]]}"
        return {'complice': 'Cómplice', 'testigo': 'Testigo', 'declaracion': 'Declaración'}[k]

    def say(self, txt):
        if self.cronica:
            self.log.append(txt)

    # ---------- utilidades de mesa ----------
    def robar_mazo(self):
        if not self.mazo:
            if len(self.descarte) <= 1:
                return None
            top = self.descarte.pop()
            self.mazo = self.descarte
            if self.R['v12']:           # §16 V1.2.2: se baraja todo el descarte
                self.mazo.append(top)
            self.rng.shuffle(self.mazo)
            self.descarte = [] if self.R['v12'] else [top]
            for j in self.jug:          # vuelve al mazo: ya no se "sabe" dónde están
                for c in self.mazo:
                    if c not in j.mano:
                        j.olvidar(c)
            self.ev['rebarajes'] += 1
        return self.mazo.pop()

    def descartar(self, j, c):
        j.mano.remove(c)
        self.descarte.append(c)
        for o in self.jug:
            o.conoce[j.id].discard(c)
            if o is j or self.rng.random() < 0.5 + 0.5 * o.p['memoria']:
                o.ver(c)

    def activos(self, excepto=None):
        return [o for o in self.jug if o.estado == 'activo' and o is not excepto]

    def D(self):
        return self.R['construccion'] + self.R['sospecha'] - self.ronda

    # ---------- turno ----------
    def turno(self, j):
        if j.estado == 'revelado':
            return
        R = self.R
        D = self.D()
        self.tiempo += 22 + 10 * (1 - j.p['habilidad'])
        # 1 · ROBAR
        v_ciego, _ = j.valor(j.mano, D + 1, self)
        opciones = self.descarte[-R['mercado']:] if self.descarte else []
        mejor = None
        for c in opciones:
            v, _, _, _ = j.mejor_mano(j.mano + [c], D, self, ruido=False)
            if mejor is None or v > mejor[0]:
                mejor = (v, c)
        umbral = 0.015 + j.rng.gauss(0, j.ruido)
        if self.quiere_reconvertir(j, mejor, D):
            self.reconversion(j, D)
        elif mejor and mejor[0] > v_ciego + umbral:
            c = mejor[1]
            self.descarte.remove(c)
            j.mano.append(c)
            j.ver(c)
            self.ev['toma_descarte'] += 1
            for o in self.jug:
                if o is not j and self.rng.random() < 0.4 + 0.6 * o.p['memoria']:
                    o.conoce[j.id].add(c)
            self.say(f"  J{j.id} ({j.perfil}) toma del descarte {self.nombre(c)}")
        else:
            for _ in range(R['robo_ciego']):
                c = self.robar_mazo()
                if c is not None:
                    j.mano.append(c)
                    j.ver(c)
            self.say(f"  J{j.id} ({j.perfil}) roba del mazo")

        # 2 · ACTUAR
        if j.estado == 'activo' and self.ronda > R['construccion']:
            if self.fase_sospecha(j, D):
                return
        self.especial(j, D)

        # 3 · DESCARTAR
        self.fin_turno(j, D)

    # ---------- Reconversión (V1.2.2 §11) ----------
    def quiere_reconvertir(self, j, mejor, D):
        R = self.R
        if not R['reconversion'] or j.reconv or j.estado == 'revelado':
            return False
        if self.ronda <= R['construccion'] or j.estr == 'nunca_reconvierte':
            return False
        if j.cree_identidad(self):
            return False
        if mejor and mejor[0] >= 1.0:          # el descarte ya me completa
            return False
        if j.estado in ('bloqueado', 'nadie'):
            return j.rng.random() < 0.3
        if j.estr == 'reconvierte_ya':
            return True
        ultima = self.ronda == R['construccion'] + R['sospecha']
        p = 0.9 if ultima else 0.35 + 0.5 * j.p['habilidad']
        return j.rng.random() < p

    def reconversion(self, j, D):
        j.reconv = True
        self.ev['reconversion'] += 1
        self.tiempo += 12
        # 1) descarta 1 boca arriba (la que menos falta le hace)
        fuera = None
        if j.mano:      # con la mano vacía no hay nada que descartar (hueco de reglas)
            fuera = max(j.mano, key=lambda c: j.valor([x for x in j.mano if x != c], D + 2, self)[0])
            self.descartar(j, fuera)
        else:
            self.ev['reconversion_mano_vacia'] += 1
        # 2) roba 2
        for _ in range(2):
            c = self.robar_mazo()
            if c is not None:
                j.mano.append(c)
                j.ver(c)
        # 3) vuelve a 4
        if len(j.mano) > self.R['mano']:
            _, keep, sobran, _ = j.mejor_mano(j.mano, D, self)
            for c in sobran:
                self.descartar(j, c)
        j.reconv_identidad = identidad_real(tuple(sorted(self.mask[c] for c in j.mano))) != 'nadie'
        self.say(f"  J{j.id} ({j.perfil}) RECONVIERTE: descarta {self.nombre(fuera) if fuera is not None else 'nada'} y roba 2"
                 + (" → ¡completa identidad!" if j.reconv_identidad else ""))

    def fin_turno(self, j, D):
        if len(j.mano) > self.R['mano']:
            _, keep, fuera, ident = j.mejor_mano(j.mano, D, self)
            for c in fuera:
                self.descartar(j, c)
                self.say(f"    descarta {self.nombre(c)}")
        _, ident = j.valor(j.mano, D, self)
        if j.estado == 'activo' and ident and ident != j.obj:
            if j.obj is not None:
                j.cambios += 1
            j.obj = ident
        if j.estado == 'activo' and len(j.mano) >= 4:
            tiene = identidad_real(tuple(sorted(self.mask[c] for c in j.mano))) != 'nadie'
            if tiene:
                j.tuvo_identidad = True
            elif j.tuvo_identidad:
                j.perdio_identidad = True

    # ---------- especiales ----------
    def especial(self, j, D):
        esp = [c for c in j.mano if self.kind(c) in ESPECIALES]
        if not esp or j.estr == 'sin_especiales':
            return False
        objetivos = self.activos(excepto=j)
        if not objetivos:
            return False
        v_keep, _, _, _ = j.mejor_mano(j.mano, D, self, ruido=False)
        agr = j.p['agresividad']
        enfadado = j.estado in ('bloqueado', 'nadie')
        for c in esp:
            resto = [x for x in j.mano if x != c]
            v_use, _, _, _ = j.mejor_mano(resto, D, self, ruido=False)
            k = self.kind(c)
            if k == 'declaracion':
                efecto = 0.02 + 0.06 * agr
            elif k == 'testigo':
                efecto = 0.02 + (0.06 if j.acusacion in ('formal', 'complice') and self.ronda >= 6 else 0)
            else:
                efecto = 0.03 + 0.03 * agr
            if enfadado or j.estr == 'especiales_siempre' or v_use + efecto + j.rng.gauss(0, j.ruido) >= v_keep:
                return self.jugar_especial(j, c, objetivos, D)
        return False

    def jugar_especial(self, j, c, objetivos, D):
        k = self.kind(c)
        j.mano.remove(c)
        self.descarte.append(c)
        for o in self.jug:
            o.ver(c)
            o.conoce[j.id].discard(c)
        self.tiempo += 15
        self.ev['usa_' + k] += 1
        if k == 'complice':
            # roba al que tenga cartas que me sirven; si no, al líder
            def interes(o):
                return sum(1 for x in j.conoce[o.id] if x in o.mano and self.mask[x]) + j.amenaza(o, self) * .3
            t = max(objetivos, key=interes)
            if not t.mano:
                return True
            robada = self.rng.choice(t.mano)
            t.mano.remove(robada)
            j.mano.append(robada)
            j.ver(robada)
            _, keep, fuera, _ = j.mejor_mano(j.mano, D, self, ruido=True)
            dada = fuera[0] if fuera else self.rng.choice(j.mano)
            j.mano.remove(dada)
            t.mano.append(dada)
            t.ver(dada)
            j.conoce[t.id].discard(robada)
            j.conoce[t.id].add(dada)
            t.conoce[j.id].add(robada)
            self.say(f"  J{j.id} juega Cómplice sobre J{t.id}: le roba {self.nombre(robada)} "
                     f"y le da {self.nombre(dada)}")
            self.check_perdida(t)
        elif k == 'testigo':
            t = max(objetivos, key=lambda o: j.amenaza(o, self))
            rec = 0.45 + 0.45 * j.p['memoria']
            for x in t.mano:
                if self.rng.random() < rec:
                    j.conoce[t.id].add(x)
                    j.ver(x)
            self.say(f"  J{j.id} juega Testigo y mira la mano de J{t.id}")
        else:  # declaracion
            t = max(objetivos, key=lambda o: j.amenaza(o, self))
            conocidas = [x for x in j.conoce[t.id] if x in t.mano]
            peso = [sum(1 for x in conocidas if self.mask[x] & b) + self.rng.random() for b in ESCENA_BITS]
            ai = max(range(4), key=lambda i: peso[i])
            bit = ESCENA_BITS[ai]
            validas = [x for x in t.mano if self.kind(x) == 'escena' and self.mask[x] & bit]
            if validas:
                # el acusado entrega la que menos le duele
                Dt = self.D()
                peor = max(validas, key=lambda x: t.valor([y for y in t.mano if y != x], Dt, self)[0])
                self.descartar(t, peor)
                j.ver(peor)
                self.ev['declaracion_acierta'] += 1
                self.say(f"  J{j.id} juega Declaración ({ATRIBUTOS[ai]}) sobre J{t.id}: "
                         f"descarta {self.nombre(peor)}")
                self.check_perdida(t)
            else:
                self.say(f"  J{j.id} juega Declaración ({ATRIBUTOS[ai]}) sobre J{t.id}: no tiene")
        return True

    def check_perdida(self, t):
        if t.tuvo_identidad and identidad_real(tuple(sorted(self.mask[c] for c in t.mano))) == 'nadie':
            t.perdio_identidad = True
            self.ev['identidad_destruida'] += 1

    # ---------- sospecha: revelar / acusar ----------
    def fase_sospecha(self, j, D):
        R = self.R
        cree = None
        if len(j.mano) >= R['mano']:
            # elige las 4 que mostraría
            _, keep, _, _ = j.mejor_mano(j.mano, 0, self, ruido=False)
            masks = tuple(sorted(self.mask[c] for c in keep))
            for ident in PRIORIDAD:
                rel = j.malentiende and ident != 'detective'
                if not rellenar(masks, ident, rel)[1]:
                    cree = ident
                    break
        # --- REVELAR ---
        if cree:
            j.pudo_revelar = True
            ultima = self.ronda == R['construccion'] + R['sospecha']
            amenazado = cree in ('asesino', 'complice') or cree in ('testigo',)
            prud = j.p['prudencia']
            if R['revelar_temprano_bonus']:
                prud -= 0.25 + 0.1 * j.p['codicia']
            quiere_acusar = (j.acusacion in ('formal', 'complice') and not ultima
                             and j.p['riesgo'] > 0.5)
            p_rev = prud if amenazado else prud * 0.7
            if quiere_acusar:
                p_rev *= 0.5
            if ultima:
                p_rev *= 0.6   # en la última ronda ya casi da igual
            if j.estr == 'revela_ya':
                p_rev = 1.0
            elif j.estr == 'nunca_revela':
                p_rev = 0.0
            if j.rng.random() < p_rev:
                return self.revelar(j, D)
            j.decision_tensa = True
        # --- ACUSAR ---
        if j.acusacion in ('formal', 'complice') and j.estr != 'nunca_acusa':
            return self.quizas_acusar(j, D, tengo=cree is not None)
        return False

    def revelar(self, j, D):
        _, keep, fuera, _ = j.mejor_mano(j.mano, 0, self, ruido=False)
        for c in fuera:
            self.descartar(j, c)
        masks = tuple(sorted(self.mask[c] for c in j.mano))
        ident = identidad_real(masks)
        self.tiempo += 20
        for o in self.jug:
            for c in j.mano:
                o.ver(c)
        if ident == 'nadie':
            j.estado = 'bloqueado' if self.R['v12'] else 'nadie'
            j.identidad_final = j.estado
            self.ev['revelacion_falsa'] += 1
            self.say(f"  J{j.id} ({j.perfil}) dice «YO SOY…» ¡pero su mano no vale! → NADIE")
        else:
            j.estado = 'revelado'
            j.identidad_final = ident
            j.revelo_ronda = self.ronda
            self.ev['revela'] += 1
            self.say(f"  J{j.id} ({j.perfil}) dice «YO SOY {ident.upper()}» → a salvo")
        return True

    def quizas_acusar(self, j, D, tengo):
        candidatos = self.activos(excepto=j)
        if not candidatos:
            return False
        ident = 'asesino' if j.acusacion == 'formal' else 'complice'
        probs = [(j.prob_identidad(o, ident, self), o) for o in candidatos]
        P, t = max(probs, key=lambda x: x[0])
        mi_v, _, _, _ = j.mejor_mano(j.mano, D, self, ruido=False)
        mi_surv = 1.0 if tengo else min(1.0, mi_v)
        ultima = self.ronda == self.R['construccion'] + self.R['sospecha']
        if self.R['v12'] and not self.R['cazador_salva'] and j.acusacion == 'formal':
            # Cazador ya no da supervivencia: es solo reconocimiento (+ quitarle la
            # victoria a otro, que en Modo Normal no te beneficia directamente).
            ganancia = self.R['valor_cazador'] * (0.6 + 0.8 * j.p['codicia']) + 0.05 * j.p['agresividad']
            perdida = mi_surv * (0.8 if not ultima else 0.95) + 0.03
        elif j.acusacion == 'formal':
            ganancia = (1 - mi_surv) * 1.0 + 0.3 * j.p['codicia'] + 0.1
            perdida = mi_surv * (0.75 if not ultima else 0.95) + 0.1 * j.p['codicia']
        else:
            ganancia = 0.12 * j.p['codicia'] + 0.25 * j.p['agresividad']
            perdida = mi_surv * 0.3 + 0.05 * j.p['codicia']
        ev = P * ganancia - (1 - P) * perdida
        umbral = 0.05 + 0.25 * (1 - j.p['riesgo']) + j.rng.gauss(0, 0.05)
        if abs(ev - umbral) < 0.12:
            j.decision_tensa = True
        if ev < umbral and j.estr != 'acusa_siempre':
            return False
        self.acusar(j, t, j.acusacion, D)
        return True

    def acusar(self, j, t, tipo, D):
        R = self.R
        self.tiempo += 35
        tipo_txt = 'Formal' if tipo == 'formal' else 'de Cómplice'
        masks_t = tuple(sorted(self.mask[c] for c in t.mano))
        acierto = not rellenar(masks_t, 'asesino' if tipo == 'formal' else 'complice')[1]
        if R['v12']:
            return self.acusar_v12(j, t, tipo, acierto, D, tipo_txt)
        j.acusacion = None
        # comprobación privada: el acusador ve la mano
        for x in t.mano:
            j.conoce[t.id].add(x)
            j.ver(x)
        contra = (t.acusacion == 'contra')
        self.ev[f'acusa_{tipo}'] += 1
        if acierto:
            self.ev[f'acusa_{tipo}_exito'] += 1
            t.estado = 'bloqueado'
            t.identidad_final = 'bloqueado'
            if contra:
                t.acusacion = None
                self.ev['contra_inutil'] += 1
            if tipo == 'formal':
                if t.mano:
                    self.descartar(t, self.rng.choice(t.mano))
                c = self.robar_mazo()
                if c is not None:
                    j.mano.append(c)
                    j.ver(c)
                j.cazador_ok = True
                j.bonus += 2
            else:
                cs = [x for x in t.mano if self.kind(x) == 'complice']
                if cs:
                    self.descartar(t, cs[0])
                j.bonus += 1
            self.say(f"  J{j.id} ({j.perfil}) ACUSA {tipo_txt} a J{t.id}: ¡ACIERTA! J{t.id} queda BLOQUEADO")
        else:
            self.ev[f'acusa_{tipo}_fallo'] += 1
            j.bonus -= 1
            if tipo == 'formal':
                for _ in range(min(R['fallo_formal'], len(j.mano))):
                    self.descartar(j, self.rng.choice(j.mano))
                c = self.robar_mazo()
                if c is not None:
                    t.mano.append(c)
                    t.ver(c)
            else:
                _, keep, fuera, _ = j.mejor_mano(j.mano, D, self)
                victima = fuera[0] if fuera else self.rng.choice(j.mano)
                self.descartar(j, victima)
            if contra:
                t.acusacion = None
                self.ev['contra_usada'] += 1
                if R['contra'] == 'bloquea':
                    j.estado = 'bloqueado'
                    j.identidad_final = 'bloqueado'
                    j.cazador_ok = False
            self.say(f"  J{j.id} ({j.perfil}) ACUSA {tipo_txt} a J{t.id}: falla"
                     + (" y le responden con Contra-acusación" if contra else ""))
        return True

    def acusar_v12(self, j, t, tipo, acierto, D, tipo_txt):
        """Reglamento V1.2.2 §13."""
        R = self.R
        j.acusacion = None
        for x in t.mano:                       # verificación privada
            j.conoce[t.id].add(x)
            j.ver(x)
        # Contra-acusación: reacción antes de mostrar la mano. El acusado conoce su mano;
        # si la acusación es cierta ya va a quedar Bloqueado, así que el descarte extra
        # apenas le cuesta: la juega casi siempre.
        contra = False
        if t.acusacion == 'contra':
            if not acierto or t.estr == 'contra_siempre' or j.rng.random() < R['contra_si_culpable']:
                contra = True
                t.acusacion = None
                self.ev['contra_usada'] += 1
                self.ev['contra_usada_' + ('culpable' if acierto else 'inocente')] += 1
        mult = 2 if contra else 1
        self.ev[f'acusa_{tipo}'] += 1
        if acierto:
            self.ev[f'acusa_{tipo}_exito'] += 1
            t.estado = 'bloqueado'
            t.identidad_final = 'bloqueado'
            if tipo == 'formal':
                if t.mano:
                    self.descartar(t, self.rng.choice(t.mano))
                c = self.robar_mazo()
                if c is not None:
                    j.mano.append(c)
                    j.ver(c)
                j.cazador_ok = True
            else:
                cs = [x for x in t.mano if self.kind(x) == 'complice']
                if cs:
                    self.descartar(t, cs[0])
            if contra and t.mano:
                self.descartar(t, self.rng.choice(t.mano))
            self.say(f"  J{j.id} ({j.perfil}) ACUSA {tipo_txt} a J{t.id}: ¡ACIERTA! J{t.id} BLOQUEADO"
                     + (" (jugó Contra-acusación en vano)" if contra else ""))
        else:
            self.ev[f'acusa_{tipo}_fallo'] += 1
            if tipo == 'formal':
                for _ in range(min(R['fallo_formal'] * mult, len(j.mano))):
                    self.descartar(j, self.rng.choice(j.mano))
            else:
                for _ in range(min(mult, len(j.mano))):
                    _, keep, fuera, _ = j.mejor_mano(j.mano, D, self)
                    self.descartar(j, fuera[0] if fuera else min(
                        j.mano, key=lambda c: popcount(self.mask[c])))
            if tipo == 'formal' or contra:
                c = self.robar_mazo()
                if c is not None:
                    t.mano.append(c)
                    t.ver(c)
                if len(t.mano) > R['mano']:      # límite de mano inmediato
                    _, keep, fuera, _ = t.mejor_mano(t.mano, D, self)
                    for c in fuera:
                        self.descartar(t, c)
            self.say(f"  J{j.id} ({j.perfil}) ACUSA {tipo_txt} a J{t.id}: falla"
                     + (" ¡y recibe Contra-acusación (penalización doble)!" if contra else ""))
        return True

    # ---------- partida ----------
    def jugar(self):
        R = self.R
        for j in self.jug:
            for _ in range(R['mano'] + R['draft']):
                c = self.mazo.pop()
                j.mano.append(c)
                j.ver(c)
        if R['draft']:
            # Draft inicial: cada uno se queda con 'mano' cartas y devuelve el resto al mazo
            for j in self.jug:
                _, keep, fuera, _ = j.mejor_mano(j.mano, self.D(), self)
                for c in fuera:
                    j.mano.remove(c)
                    self.mazo.append(c)
            self.rng.shuffle(self.mazo)
        acc = (['formal'] * R['acc_formal'] + ['complice'] * R['acc_complice']
               + ['contra'] * R['acc_contra'])
        self.rng.shuffle(acc)
        for j in self.jug:
            j.acusacion = acc.pop() if acc else None
        c = self.mazo.pop()
        self.descarte.append(c)
        for j in self.jug:
            j.ver(c)
        self.inicio = {j.id: 4 - faltan_min(tuple(sorted(self.mask[x] for x in j.mano)))
                       for j in self.jug}
        for j in self.jug:
            _, j.obj = j.valor(j.mano, self.D(), self)
        orden = self.jug[:]
        k = self.rng.randrange(len(orden))
        orden = orden[k:] + orden[:k]
        for i, j in enumerate(orden):
            j.asiento = i
        crimen_txt = (f"asesino {self.crimen[0]}, arma {self.crimen[1]}, víctima {self.crimen[2]}, "
                      f"lugar {self.crimen[3]}, expediente {EXPEDIENTES[self.crimen[4]]}")
        self.say(f"CRIMEN: {crimen_txt}")
        self.say("Mesa: " + ", ".join(f"J{j.id}={j.perfil}"
                                      + ('(no entiende §4)' if j.malentiende else '')
                                      + f"[{j.acusacion}]" for j in self.jug))
        total = R['construccion'] + R['sospecha']
        for r in range(1, total + 1):
            self.ronda = r
            fase = 'CONSTRUCCIÓN' if r <= R['construccion'] else 'SOSPECHA'
            self.say(f"\n— Ronda {r} ({fase}) —")
            for j in orden:
                self.turno(j)
            # olvido con el tiempo
            for o in self.jug:
                f = (1 - o.p['memoria']) * 0.15
                for jid in list(o.conoce):
                    for c in list(o.conoce[jid]):
                        if self.rng.random() < f:
                            o.conoce[jid].discard(c)
        return self.final()

    def final(self):
        R = self.R
        tam = R['mano']
        res = {}
        for j in self.jug:
            if j.estado == 'activo':
                ident = mejor_identidad_de([self.mask[c] for c in j.mano], tam)
                if ident == 'nadie' and j.cazador_ok and (not R['v12'] or R['cazador_salva']):
                    ident = 'cazador'
                j.identidad_final = ident
                if ident not in ('nadie', 'cazador'):
                    j.bonus += R['revelar_temprano_bonus']
            res[j.id] = j.identidad_final
        self.say("\nREVELACIÓN FORZADA: " + ", ".join(
            f"J{j.id}({j.perfil})={res[j.id]}" for j in self.jug))
        return res


# ============================================================
# MÉTRICAS DE UNA PARTIDA
# ============================================================
def jugar_partida(args):
    R, n, seed, mesa = args[:4]
    estr = args[4] if len(args) > 4 else None     # (estrategia, perfil) para el jugador 0
    rng = random.Random(seed)
    g = Partida(R, n, rng, mesa)
    if estr:
        j0 = g.jug[0]
        j0.perfil, j0.p = estr[1], PERFILES[estr[1]]
        j0.ruido = (1 - j0.p['habilidad']) * 0.12
        j0.malentiende = False
        j0.estr = estr[0]
        j0.w = {i: 1 + j0.p['codicia'] * (PUNTOS[i] - 4.5) / 12 for i in IDENTIDADES}
        if R['v12']:
            j0.w = {i: 1.0 for i in IDENTIDADES}
        if estr[0].startswith('solo_'):
            j0.w = {i: (1.0 if i == estr[0][5:] else 0.0) for i in IDENTIDADES}
    res = g.jugar()
    tam = R['mano']
    filas = []
    for j in g.jug:
        ident = res[j.id]
        sobrevive = ident not in ('nadie', 'bloqueado')
        faltan = None
        if ident == 'nadie':
            masks = [g.mask[c] for c in j.mano]
            if len(masks) > tam:
                faltan = min(faltan_min(tuple(sorted(s))) for s in combinations(masks, tam))
            else:
                faltan = faltan_min(tuple(sorted(masks))) + (tam - len(masks))
        pts = 0 if ident == 'bloqueado' else PUNTOS[ident] + j.bonus
        caz = (ident == 'cazador') or j.cazador_ok if R['v12'] else (ident == 'cazador')
        filas.append(dict(pudo=getattr(j, 'pudo_revelar', False), cazador=caz, reconv=j.reconv,
                          reconv_ok=getattr(j, 'reconv_identidad', False), id=j.id, asiento=j.asiento, revelo=j.revelo_ronda, perfil=j.perfil, ident=ident, sobrevive=sobrevive, faltan=faltan,
                          cambios=j.cambios, tensa=j.decision_tensa, perdio=j.perdio_identidad,
                          inicio=g.inicio[j.id], puntos=pts, malentiende=j.malentiende))
    return dict(filas=filas, ev=dict(g.ev), tiempo=g.tiempo)


def simular(R, n, partidas, mesa='mixta', seed=1, procesos=4):
    tareas = [(R, n, seed * 100003 + i, mesa) for i in range(partidas)]
    if procesos > 1:
        with Pool(procesos) as pool:
            out = pool.map(jugar_partida, tareas, chunksize=max(1, partidas // (procesos * 8)))
    else:
        out = [jugar_partida(t) for t in tareas]
    return resumir(out, n, partidas)


def resumir(out, n, partidas):
    filas = [f for o in out for f in o['filas']]
    ident = Counter(f['ident'] for f in filas)
    total = len(filas)
    nadie_partida = [sum(1 for f in o['filas'] if not f['sobrevive']) for o in out]
    nadies = [f for f in filas if f['ident'] == 'nadie']
    cerca = sum(1 for f in nadies if f['faltan'] is not None and f['faltan'] <= 1)
    ev = Counter()
    for o in out:
        ev.update(o['ev'])
    surv = [f for f in filas if f['sobrevive'] and f['ident'] != 'cazador']
    reparto = Counter(f['ident'] for f in surv)
    ent = 0.0
    for k in ('asesino', 'detective', 'complice', 'testigo'):
        p = reparto[k] / max(1, len(surv))
        if p > 0:
            ent -= p * math.log(p, 4)
    por_perfil = {}
    for p in PERFILES:
        fp = [f for f in filas if f['perfil'] == p]
        if fp:
            por_perfil[p] = (sum(f['sobrevive'] for f in fp) / len(fp), len(fp))
    buen_inicio = [f for f in filas if f['inicio'] >= 2]
    mal_inicio = [f for f in filas if f['inicio'] <= 1]
    acc_f = ev['acusa_formal']
    acc_c = ev['acusa_complice']
    return dict(
        n=n, partidas=partidas,
        ident={k: ident[k] / total for k in
               ('asesino', 'detective', 'complice', 'testigo', 'cazador', 'bloqueado', 'nadie')},
        nadie_medio=statistics.mean(nadie_partida),
        nadie_dist=Counter(nadie_partida),
        todos_nadie=sum(1 for x in nadie_partida if x == n) / partidas,
        casi=cerca / max(1, len(nadies)),
        cambios=statistics.mean(f['cambios'] for f in filas),
        tensa=sum(f['tensa'] for f in filas) / total,
        perdio=sum(f['perdio'] for f in filas) / total,
        entropia=ent,
        por_perfil=por_perfil,
        suerte=(sum(f['sobrevive'] for f in buen_inicio) / max(1, len(buen_inicio))
                - sum(f['sobrevive'] for f in mal_inicio) / max(1, len(mal_inicio))),
        acusaciones=(acc_f + acc_c) / partidas,
        acierto_formal=ev['acusa_formal_exito'] / max(1, acc_f),
        acierto_complice=ev['acusa_complice_exito'] / max(1, acc_c),
        especiales=(ev['usa_complice'] + ev['usa_testigo'] + ev['usa_declaracion']) / partidas,
        tomas=ev['toma_descarte'] / partidas,
        revelaciones=ev['revela'] / partidas,
        falsas=ev['revelacion_falsa'] / partidas,
        cazador_partidas=sum(1 for o in out if any(f['cazador'] for f in o['filas'])) / partidas,
        reconversiones=ev['reconversion'] / partidas,
        reconv_salva=(sum(1 for f in filas if f['reconv'] and f['reconv_ok'])
                      / max(1, sum(1 for f in filas if f['reconv']))),
        contra_usada=ev['contra_usada'] / partidas,
        destruidas=ev['identidad_destruida'] / partidas,
        minutos=statistics.mean(o['tiempo'] for o in out) / 60,
        puntos=statistics.mean(f['puntos'] for f in filas),
        ev=ev,
    )


# ============================================================
# EVALUACIÓN "¿ENGANCHA?"
# ============================================================
def objetivo_nadie(n):
    # Reglamento §18: 4 jug → ~1 Nadie; 8 jug → 2–3. Interpolamos.
    lo = 0.6 + (n - 4) * (2 - 0.6) / 4
    hi = 1.4 + (n - 4) * (3 - 1.4) / 4
    return lo, hi


def semaforo(s):
    lo, hi = objetivo_nadie(s['n'])
    chequeos = [
        ('Nadie por partida', f"{s['nadie_medio']:.2f}", f"{lo:.1f}–{hi:.1f}",
         lo <= s['nadie_medio'] <= hi),
        ('Nadie a 1 carta («me faltó una»)', f"{s['casi']*100:.0f}%", '≥ 60%', s['casi'] >= .60),
        ('Cambios de objetivo / jugador', f"{s['cambios']:.2f}", '≥ 0.8', s['cambios'] >= .8),
        ('Jugadores con decisión tensa en 9–10', f"{s['tensa']*100:.0f}%", '≥ 30%', s['tensa'] >= .30),
        ('Variedad de identidades (entropía)', f"{s['entropia']:.2f}", '≥ 0.75', s['entropia'] >= .75),
        ('Acusaciones / partida', f"{s['acusaciones']:.2f}", '≥ 1.0', s['acusaciones'] >= 1.0),
        ('Acierto Acusación Formal', f"{s['acierto_formal']*100:.0f}%", '30–70%',
         .30 <= s['acierto_formal'] <= .70),
        ('Partidas con Cazador', f"{s['cazador_partidas']*100:.0f}%", '10–40%',
         .10 <= s['cazador_partidas'] <= .40),
        ('Peso de la mano inicial', f"{s['suerte']*100:+.0f} pts", '≤ +20', s['suerte'] <= .20),
        ('Duración estimada', f"{s['minutos']:.0f} min", '20–30', 18 <= s['minutos'] <= 32),
    ]
    return chequeos


def imprimir(s, R):
    print(f"\n{'=' * 72}\n{R['nombre']} — {s['n']} jugadores — {s['partidas']} partidas\n{'=' * 72}")
    print("  Identidad final:")
    for k, v in s['ident'].items():
        print(f"    {k:<11}{v * 100:6.1f}%")
    print(f"  Nadie por partida: {s['nadie_medio']:.2f}   (todos Nadie: {s['todos_nadie'] * 100:.1f}%)")
    dist = ', '.join(f"{k}:{v / s['partidas'] * 100:.0f}%" for k, v in sorted(s['nadie_dist'].items()))
    print(f"  Reparto de nº de perdedores: {dist}")
    print(f"  Revelaciones/partida {s['revelaciones']:.2f} · falsas {s['falsas']:.2f} · "
          f"tomas del descarte {s['tomas']:.1f} · especiales {s['especiales']:.1f} · "
          f"identidades destruidas {s['destruidas']:.2f}")
    print(f"  Acusaciones/partida {s['acusaciones']:.2f} · acierto Formal {s['acierto_formal'] * 100:.0f}% "
          f"· acierto Cómplice {s['acierto_complice'] * 100:.0f}% · Contra usada {s['contra_usada']:.2f}")
    print("  Supervivencia por perfil: " + ', '.join(
        f"{p} {v[0] * 100:.0f}%" for p, v in sorted(s['por_perfil'].items(), key=lambda x: -x[1][0])))
    print("\n  ¿ENGANCHA?")
    ok = 0
    for nombre, valor, obj, bien in semaforo(s):
        ok += bien
        print(f"    {'✅' if bien else '❌'} {nombre:<40}{valor:>10}   objetivo {obj}")
    print(f"    → {ok}/10 indicadores en objetivo")


# ============================================================
# MAIN
# ============================================================
def main():
    ap = argparse.ArgumentParser(description='Simulador de playtest de YO SOY UN ASESINO')
    ap.add_argument('--variante', default='V1.0', choices=list(VARIANTES))
    ap.add_argument('--jugadores', type=int, nargs='*', default=[4, 6, 8])
    ap.add_argument('--partidas', type=int, default=2000)
    ap.add_argument('--mesa', default='mixta', choices=list(MESAS))
    ap.add_argument('--semilla', type=int, default=1)
    ap.add_argument('--procesos', type=int, default=4)
    ap.add_argument('--comparar', action='store_true', help='tabla con todas las variantes')
    ap.add_argument('--cronica', action='store_true', help='narra una partida')
    a = ap.parse_args()

    if a.cronica:
        R = reglas(a.variante)
        g = Partida(R, a.jugadores[0], random.Random(a.semilla), a.mesa, cronica=True)
        g.jugar()
        print('\n'.join(g.log))
        return

    if a.comparar:
        cab = (f"{'variante':<20}{'n':>3}{'Nadie':>7}{'a1carta':>8}{'cambios':>8}{'tensa':>7}"
               f"{'entrop':>7}{'acus':>6}{'aciert':>7}{'cazad':>7}{'suerte':>7}{'min':>5}{'OK':>4}")
        print(cab)
        for v in VARIANTES:
            R = reglas(v)
            for n in a.jugadores:
                s = simular(R, n, a.partidas, a.mesa, a.semilla, a.procesos)
                ok = sum(c[3] for c in semaforo(s))
                print(f"{R['nombre']:<20}{n:>3}{s['nadie_medio']:>7.2f}{s['casi'] * 100:>7.0f}%"
                      f"{s['cambios']:>8.2f}{s['tensa'] * 100:>6.0f}%{s['entropia']:>7.2f}"
                      f"{s['acusaciones']:>6.2f}{s['acierto_formal'] * 100:>6.0f}%"
                      f"{s['cazador_partidas'] * 100:>6.0f}%{s['suerte'] * 100:>+6.0f}"
                      f"{s['minutos']:>5.0f}{ok:>4}", flush=True)
        return

    R = reglas(a.variante)
    for n in a.jugadores:
        s = simular(R, n, a.partidas, a.mesa, a.semilla, a.procesos)
        imprimir(s, R)


if __name__ == '__main__':
    main()
