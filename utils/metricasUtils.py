"""Métricas: BER, eficiência espectral nominal e curvas teóricas"""
import numpy as np
from scipy.special import erfc
from scipy.optimize import brentq
from utils.modulacaoUtils import BITS_POR_SIMBOLO


def contar_erros(bits_tx, bits_rx):
    """Retorna (n_erros, BER, posições dos bits errados)"""
    tx = np.asarray(bits_tx, dtype=np.uint8)
    rx = np.asarray(bits_rx, dtype=np.uint8)
    errados = np.flatnonzero(tx != rx)
    return int(len(errados)), len(errados) / len(tx), errados


def eficiencia_espectral_nominal(modulacao, rolloff=0.0):
    """Eficiência espectral nominal (bits/s/Hz) = log2(M)/(1+rolloff).
    Com filtro de Nyquist ideal (rolloff = 0): BPSK=1, QPSK=2, 16-QAM=4. Sem codificação de canal"""
    return BITS_POR_SIMBOLO[modulacao] / (1.0 + rolloff)


# Largura de banda até o 1º nulo do espectro, pulso retangular de duração = 1 slot de sinalização
_EFIC_LINHA = {"AMI": 1.0, "Manchester": 0.5, "NRZ": 1.0}


def eficiencia_linha(codigo):
    """bits/s/Hz nominal (Rb / largura até o 1º nulo). Manchester dobra a banda; AMI mantém"""
    return _EFIC_LINHA[codigo]


# teoria AWGN
def qfunc(x):
    return 0.5 * erfc(np.asarray(x, dtype=float) / np.sqrt(2.0))


def ber_teorica(modulacao, ebn0_db):
    """BER teórica em AWGN (Gray, decisão rígida). 16-QAM usa a aproximação padrão de 1ª ordem"""
    g = 10.0 ** (np.asarray(ebn0_db, dtype=float) / 10.0)
    if modulacao in ("BPSK", "QPSK"):
        return qfunc(np.sqrt(2.0 * g))
    if modulacao == "16QAM":
        return 0.75 * qfunc(np.sqrt(0.8 * g))
    raise ValueError(modulacao)


def ber_teorica_linha(codigo, ebn0_db):
    """Manchester (receptor por correlação) = antipodal: Q(sqrt(2g)).
    AMI com limiar |x|>0.5 e Eb médio = 0.5:  1.5*Q(sqrt(g)) - 0.5*Q(3*sqrt(g))"""
    g = 10.0 ** (np.asarray(ebn0_db, dtype=float) / 10.0)
    if codigo == "Manchester":
        return qfunc(np.sqrt(2.0 * g))
    if codigo == "AMI":
        return 1.5 * qfunc(np.sqrt(g)) - 0.5 * qfunc(3.0 * np.sqrt(g))
    raise ValueError(codigo)


def ber_teorica_rajada(esquema, ebn0_db, p_gb, p_bg, penalidade_db, linha=False):
    """BER esperada no canal de rajadas: mistura (1-pi)*BER(g) + pi*BER(g - penalidade)"""
    pi = p_gb / (p_gb + p_bg)
    f = ber_teorica_linha if linha else ber_teorica
    e = np.asarray(ebn0_db, dtype=float)
    return (1 - pi) * f(esquema, e) + pi * f(esquema, e - penalidade_db)


def ebn0_necessario_teorico(modulacao, ber_alvo):
    """Eb/N0 (dB) teórico em AWGN para atingir `ber_alvo`"""
    return brentq(lambda x: np.log10(ber_teorica(modulacao, x)) - np.log10(ber_alvo), -5, 25)


def ebn0_minimo_shannon_db(eficiencia):
    """Limite de Shannon: Eb/N0 mínimo (dB) para uma eficiência espectral (bits/s/Hz)"""
    eficiencia = np.asarray(eficiencia, dtype=float)
    return 10 * np.log10((2.0 ** eficiencia - 1) / eficiencia)
