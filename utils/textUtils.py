"""Conversões texto <-> ASCII <-> bits."""
import numpy as np


def fromTexttoASCIIConverter(texto):
    """Texto -> lista de códigos ASCII (inteiros 0..127). Levanta erro se houver caractere não-ASCII"""
    return list(texto.encode("ascii"))


def fromASCIItoBinaryConverter(codigos):
    """Lista de códigos ASCII -> vetor de bits (uint8), 8 bits por caractere, MSB primeiro"""
    return np.unpackbits(np.array(codigos, dtype=np.uint8))


def fromTexttoBinary(texto):
    """Atalho: texto -> vetor de bits."""
    return fromASCIItoBinaryConverter(fromTexttoASCIIConverter(texto))


def fromBinarytoASCIIConverter(bits):
    """Vetor de bits -> lista de códigos (0..255). Bits excedentes (não múltiplos de 8) são descartados"""
    bits = np.asarray(bits, dtype=np.uint8)
    n = (len(bits) // 8) * 8
    return [int(c) for c in np.packbits(bits[:n])]


def fromASCIItoTextConverter(codigos):
    """Códigos -> texto. Caracteres não imprimíveis (resultado de erros de bit) viram '?'"""
    return "".join(chr(c) if 32 <= c < 127 else "?" for c in codigos)


def fromBinarytoText(bits):
    return fromASCIItoTextConverter(fromBinarytoASCIIConverter(bits))


def formatarBinario(bits):
    """Vetor de bits -> string '01001000 01100101 ...' (um grupo por byte)"""
    s = "".join(str(int(b)) for b in bits)
    return " ".join(s[i:i + 8] for i in range(0, len(s), 8))
