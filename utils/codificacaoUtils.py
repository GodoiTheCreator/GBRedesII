"""Codificação de LINHA (como os bits viram níveis de sinal no meio). Não adiciona
capacidade de correção de erros; apenas dá ao sinal propriedades úteis
(sincronismo, ausência de componente DC, detecção de violações).

Implementadas: Manchester e AMI
"""
import numpy as np


#  Manchester
def manchester(bits):
    """Manchester (convenção deste trabalho): 1 -> (+1,-1)  e  0 -> (-1,+1).
    Taxa de sinalização = 2 amostras/bit. Retorna vetor de níveis (float)"""
    b = np.asarray(bits, dtype=np.int8)
    nivel = 2.0 * b - 1.0
    saida = np.empty(2 * len(b))
    saida[0::2] = nivel
    saida[1::2] = -nivel
    return saida


def manchester_decodificar(amostras):
    """Decisão ótima (correlação): bit = 1 se (a1 - a2) > 0"""
    a = np.asarray(amostras)
    return ((a[0::2] - a[1::2]) > 0).astype(np.uint8)


def manchester_bits(bits):
    """Versão em 'chips' binários (1 -> [1,0], 0 -> [0,1]) para alimentar um modulador digital"""
    b = np.asarray(bits, dtype=np.uint8)
    saida = np.empty(2 * len(b), dtype=np.uint8)
    saida[0::2] = b
    saida[1::2] = 1 - b
    return saida


def manchester_bits_decodificar(chips):
    """Decodifica chips binários (após decisão rígida). Retorna (bits, n_violacoes).
    Violação = par de chips iguais ('00' ou '11'), impossível em Manchester válido -> erro DETECTADO"""
    c = np.asarray(chips, dtype=np.uint8)
    violacoes = int(np.sum(c[0::2] == c[1::2]))
    return c[0::2].copy(), violacoes


# AMI
def ami(bits):
    """AMI (bipolar): 0 -> 0 ; cada 1 alterna a polaridade (+1, -1, +1, ...). 1 amostra/bit"""
    b = np.asarray(bits, dtype=np.int8)
    polaridade = np.where(np.cumsum(b) % 2 == 1, 1.0, -1.0)  # 1º '1' -> +1, 2º -> -1 ...
    return b * polaridade


def ami_decodificar(amostras, limiar=0.5):
    """Decisão por limiar de magnitude: |x| > 0.5 -> bit 1."""
    return (np.abs(np.asarray(amostras)) > limiar).astype(np.uint8)


def ami_violacoes(amostras, limiar=0.5):
    """Conta violações bipolares (dois pulsos consecutivos com a mesma polaridade) -> erros detectáveis"""
    x = np.asarray(amostras)
    pulsos = np.sign(x[np.abs(x) > limiar])
    return int(np.sum(pulsos[1:] == pulsos[:-1]))


# referência (sem codificação)
def nrz(bits):
    """NRZ-L polar (1 -> +1, 0 -> -1). Usado apenas como referência nos gráficos de formas de onda"""
    return 2.0 * np.asarray(bits, dtype=np.int8) - 1.0
