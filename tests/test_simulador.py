import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import textUtils, codificacaoUtils as cod, modulacaoUtils as mod, canalUtils as canal, metricasUtils as met

RNG = np.random.default_rng(1)


def test_texto_ascii_bits_ida_e_volta():
    t = "Hello, World!"
    assert textUtils.fromTexttoASCIIConverter(t)[:2] == [72, 101]
    b = textUtils.fromTexttoBinary(t)
    assert len(b) == 8 * len(t)
    assert textUtils.formatarBinario(b[:8]) == "01001000"        # 'H'
    assert textUtils.fromBinarytoText(b) == t


def test_manchester_e_ami_ida_e_volta():
    b = RNG.integers(0, 2, 1000, dtype=np.uint8)
    assert np.array_equal(cod.manchester_decodificar(cod.manchester(b)), b)
    assert np.array_equal(cod.ami_decodificar(cod.ami(b)), b)
    assert np.array_equal(cod.manchester_bits_decodificar(cod.manchester_bits(b))[0], b)


def test_ami_alterna_polaridade():
    x = cod.ami(np.array([1, 0, 1, 1, 0, 1]))
    assert x.tolist() == [1, 0, -1, 1, 0, -1]
    assert cod.ami_violacoes(x) == 0
    assert cod.ami_violacoes(np.array([1, 0, 1.0])) == 1


def test_modulacao_ida_e_volta_sem_ruido():
    for m in mod.BITS_POR_SIMBOLO:
        b = RNG.integers(0, 2, 4000, dtype=np.uint8)
        assert np.array_equal(mod.demodular(m, mod.modular(m, b), len(b)), b), m


def test_energia_media_unitaria_e_gray():
    for m in mod.BITS_POR_SIMBOLO:
        pts, bits = mod.constelacao_ideal(m)
        assert abs(np.mean(np.abs(pts) ** 2) - 1) < 1e-12
        assert len(np.unique(np.round(pts, 9))) == 2 ** mod.BITS_POR_SIMBOLO[m]
    # Gray: vizinhos mais próximos do 16-QAM diferem em 1 bit
    pts, bits = mod.constelacao_ideal("16QAM")
    d = np.abs(pts[:, None] - pts[None, :]); np.fill_diagonal(d, 9)
    dmin = d.min()
    for i in range(16):
        for j in np.flatnonzero(np.isclose(d[i], dmin)):
            assert (bits[i] != bits[j]).sum() == 1


def test_preenchimento_quando_nao_multiplo():
    b = RNG.integers(0, 2, 7, dtype=np.uint8)
    assert np.array_equal(mod.demodular("16QAM", mod.modular("16QAM", b), 7), b)


def test_ber_simulada_proxima_da_teoria():
    n = 400_000
    for m in mod.BITS_POR_SIMBOLO:
        k = mod.BITS_POR_SIMBOLO[m]
        b = RNG.integers(0, 2, n, dtype=np.uint8)
        rx = canal.simulaAWGN(mod.modular(m, b), 6, 1.0 / k, RNG)
        ber = np.mean(mod.demodular(m, rx, n) != b)
        teo = float(met.ber_teorica(m, 6))
        assert abs(ber - teo) / teo < 0.15, (m, ber, teo)


def test_mascara_rajada_estatistica():
    p_gb, p_bg = 0.005, 0.1
    m = canal.gerar_mascara_rajada(2_000_000, p_gb, p_bg, RNG)
    assert abs(m.mean() - canal.fracao_ruim_estacionaria(p_gb, p_bg)) < 0.01
    # duração média da rajada ≈ 1/p_bg
    d = np.diff(np.flatnonzero(np.diff(np.concatenate([[0], m.astype(int), [0]]))))[::2]
    assert abs(d.mean() - 1 / p_bg) < 1.0


def test_eficiencia_espectral():
    assert [met.eficiencia_espectral_nominal(m) for m in ("BPSK", "QPSK", "16QAM")] == [1, 2, 4]
