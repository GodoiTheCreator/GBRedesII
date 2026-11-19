"""Modelos de canal.

Definição de SNR usada em todo o trabalho: Eb/N0 em dB (energia por BIT / densidade
espectral de ruído). É a métrica que permite comparar modulações de ordens
diferentes de forma justa (mesma energia por bit de informação).
Relação com Es/N0: Es/N0 = Eb/N0 + 10*log10(bits_por_simbolo)
"""
import numpy as np


def simulaCanal(sinal, ebn0_db, energia_bit, rng, mascara=None, penalidade_db=0.0):
    """Adiciona ruído gaussiano branco ao sinal.

    sinal        : amostras/símbolos transmitidos
    ebn0_db      : Eb/N0 em dB
    energia_bit  : energia média por bit do sinal (Es/k para modulações; calculada p/ codificação de linha)
    mascara      : (opcional) vetor booleano; onde True o ruído é `penalidade_db` dB mais forte (rajada)
    Variância por dimensão real: sigma^2 = N0/2 = Eb / (2*Eb/N0)
    """
    sinal = np.asarray(sinal)
    sigma = np.sqrt(energia_bit / (2.0 * 10.0 ** (ebn0_db / 10.0)))
    if mascara is None:
        escala = sigma
    else:
        escala = np.where(mascara, sigma * 10.0 ** (penalidade_db / 20.0), sigma)
    if np.iscomplexobj(sinal):
        ruido = escala * (rng.standard_normal(sinal.shape) + 1j * rng.standard_normal(sinal.shape))
    else:
        ruido = escala * rng.standard_normal(sinal.shape)
    return sinal + ruido


def simulaAWGN(sinal, ebn0_db, energia_bit, rng):
    """Cenário 1: canal AWGN com controle de Eb/N0."""
    return simulaCanal(sinal, ebn0_db, energia_bit, rng)


def gerar_mascara_rajada(n, p_gb, p_bg, rng):
    """Cadeia de Markov de 2 estados (Gilbert-Elliott). True = estado RUIM.
    Tempo de permanência é geométrico: média 1/p_gb (bom) e 1/p_bg (ruim).
    O estado inicial segue a distribuição estacionária"""
    pi_ruim = p_gb / (p_gb + p_bg)
    inicia_ruim = bool(rng.random() < pi_ruim)
    n_ciclos = int(n / (1 / p_gb + 1 / p_bg) * 1.5) + 10
    duracoes, valores, total = [], [], 0
    while total < n:
        g = rng.geometric(p_gb, n_ciclos)
        r = rng.geometric(p_bg, n_ciclos)
        if inicia_ruim:
            seq, val = np.column_stack((r, g)).ravel(), np.tile([True, False], n_ciclos)
        else:
            seq, val = np.column_stack((g, r)).ravel(), np.tile([False, True], n_ciclos)
        duracoes.append(seq)
        valores.append(val)
        total += int(seq.sum())
    return np.repeat(np.concatenate(valores), np.concatenate(duracoes))[:n]


def fracao_ruim_estacionaria(p_gb, p_bg):
    return p_gb / (p_gb + p_bg)


def simulaRajadas(sinal, ebn0_db, energia_bit, rng, p_gb, p_bg, penalidade_db):
    """Cenário 2: ruído em rajadas. Retorna (sinal_ruidoso, mascara_estado_ruim)"""
    n = np.asarray(sinal).shape[0]
    mascara = gerar_mascara_rajada(n, p_gb, p_bg, rng)
    return simulaCanal(sinal, ebn0_db, energia_bit, rng, mascara, penalidade_db), mascara
