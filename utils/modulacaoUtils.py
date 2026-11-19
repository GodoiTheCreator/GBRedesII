"""Modulações digitais (banda base complexa) com mapeamento Gray e energia média
por símbolo normalizada Es = 1:  BPSK, QPSK e 16-QAM  (16-QAM = ordem superior).

Convenção de bits: bit 0 -> nível positivo, bit 1 -> nível negativo (BPSK/QPSK)
"""
import numpy as np

BITS_POR_SIMBOLO = {"BPSK": 1, "QPSK": 2, "16QAM": 4}

_ESC_QPSK = 1 / np.sqrt(2)
_ESC_16QAM = 1 / np.sqrt(10)


def _preencher(bits, k):
    """Completa com zeros até múltiplo de k (o receptor descarta o excesso)"""
    bits = np.asarray(bits, dtype=np.uint8)
    resto = len(bits) % k
    if resto:
        bits = np.concatenate([bits, np.zeros(k - resto, dtype=np.uint8)])
    return bits


# BPSK
def bpsk(bits):
    return (1.0 - 2.0 * np.asarray(bits, dtype=np.float64)).astype(np.complex128)


def bpsk_demod(simbolos):
    return (np.real(simbolos) < 0).astype(np.uint8)


# QPSK
def qpsk(bits):
    b = _preencher(bits, 2).reshape(-1, 2).astype(np.float64)
    return _ESC_QPSK * ((1 - 2 * b[:, 0]) + 1j * (1 - 2 * b[:, 1]))


def qpsk_demod(simbolos):
    s = np.asarray(simbolos)
    out = np.empty((len(s), 2), dtype=np.uint8)
    out[:, 0] = np.real(s) < 0
    out[:, 1] = np.imag(s) < 0
    return out.reshape(-1)


# 16-QAM
# Gray por eixo (4-PAM): 00->-3, 01->-1, 11->+1, 10->+3
def _pam4(b0, b1):
    idx = 2 * b0 + (b0 ^ b1)           # 00->0, 01->1, 11->2, 10->3
    return 2.0 * idx - 3.0


def sixteen_qam(bits):
    b = _preencher(bits, 4).reshape(-1, 4).astype(np.int64)
    return _ESC_16QAM * (_pam4(b[:, 0], b[:, 1]) + 1j * _pam4(b[:, 2], b[:, 3]))


def _pam4_demod(x):
    idx = np.digitize(x, [-2.0, 0.0, 2.0])   # limiares de decisão (mínima distância)
    b0 = (idx >= 2).astype(np.uint8)
    b1 = b0 ^ (idx & 1).astype(np.uint8)
    return b0, b1


def sixteen_qam_demod(simbolos):
    s = np.asarray(simbolos) / _ESC_16QAM
    out = np.empty((len(s), 4), dtype=np.uint8)
    out[:, 0], out[:, 1] = _pam4_demod(np.real(s))
    out[:, 2], out[:, 3] = _pam4_demod(np.imag(s))
    return out.reshape(-1)


# despachante
_MOD = {"BPSK": bpsk, "QPSK": qpsk, "16QAM": sixteen_qam}
_DEMOD = {"BPSK": bpsk_demod, "QPSK": qpsk_demod, "16QAM": sixteen_qam_demod}


def modular(nome, bits):
    return _MOD[nome](bits)


def demodular(nome, simbolos, n_bits=None):
    """Demodulação por decisão rígida (distância mínima). `n_bits` descarta o preenchimento"""
    bits = _DEMOD[nome](simbolos)
    return bits if n_bits is None else bits[:n_bits]


def constelacao_ideal(nome):
    """Pontos ideais da constelação (para plotagem)."""
    k = BITS_POR_SIMBOLO[nome]
    todos = ((np.arange(2 ** k)[:, None] >> np.arange(k - 1, -1, -1)) & 1).astype(np.uint8)
    return modular(nome, todos.reshape(-1)), todos
