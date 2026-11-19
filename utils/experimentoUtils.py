"""Pipeline ponta a ponta e varreduras experimentais.

Pipeline com modulação:
  texto -> ASCII -> bits -> [Manchester opcional] -> modulação -> CANAL -> demodulação
        -> [decodificação de linha] -> bits -> texto
Pipeline de banda base (codificação de linha pura):
  bits -> AMI | Manchester (níveis) -> CANAL -> decisão -> bits
"""
import numpy as np
import pandas as pd
from scipy import stats

from utils import textUtils, codificacaoUtils as cod, modulacaoUtils as mod, canalUtils as canal, metricasUtils as met

ID_CANAL = {"AWGN": 0, "RAJADA": 1}


# geração de bits
def bits_aleatorios(n_bits, seed, rep):
    """Mesma sequência de bits para todos os esquemas/SNR de uma mesma repetição (comparação pareada)"""
    return np.random.default_rng([seed, 999, rep]).integers(0, 2, n_bits, dtype=np.uint8)


# canal (símbolos)
def _passar_canal(sinal, ebn0_db, energia_bit, nome_canal, rng, cfg_rajada):
    """Retorna (sinal_rx, mascara_rajada|None). nome_canal in {IDEAL, AWGN, RAJADA}."""
    if nome_canal == "IDEAL" or ebn0_db is None or np.isinf(ebn0_db):
        return np.array(sinal, copy=True), None
    if nome_canal == "AWGN":
        return canal.simulaAWGN(sinal, ebn0_db, energia_bit, rng), None
    if nome_canal == "RAJADA":
        return canal.simulaRajadas(sinal, ebn0_db, energia_bit, rng, **cfg_rajada)
    raise ValueError(nome_canal)


# 1 execução: modulação
def simular_modulacao(modulacao, bits, ebn0_db, nome_canal, rng, cfg_rajada):
    k = mod.BITS_POR_SIMBOLO[modulacao]
    simbolos = mod.modular(modulacao, bits)
    rx, _ = _passar_canal(simbolos, ebn0_db, 1.0 / k, nome_canal, rng, cfg_rajada)   # Es=1 -> Eb=1/k
    return mod.demodular(modulacao, rx, len(bits))


# 1 execução: codificação de linha
def simular_linha(codigo, bits, ebn0_db, nome_canal, rng, cfg_rajada):
    x = cod.manchester(bits) if codigo == "Manchester" else cod.ami(bits)
    eb = float(np.sum(x ** 2)) / len(bits)                                   # energia média por bit
    y, _ = _passar_canal(x, ebn0_db, eb, nome_canal, rng, cfg_rajada)
    return cod.manchester_decodificar(y) if codigo == "Manchester" else cod.ami_decodificar(y)


# varreduras (DataFrames)
def varredura(cfg, tipo, progresso=True):
    """tipo = 'modulacao' ou 'linha'. Retorna DataFrame com 1 linha por (canal, esquema, SNR, repetição)"""
    esquemas = cfg["modulacoes"] if tipo == "modulacao" else cfg["linhas"]
    func = simular_modulacao if tipo == "modulacao" else simular_linha
    linhas = []
    for nome_canal in ("AWGN", "RAJADA"):
        for ie, esq in enumerate(esquemas):
            for isnr, snr in enumerate(cfg["ebn0_db"]):
                for rep in range(cfg["n_repeticoes"]):
                    bits = bits_aleatorios(cfg["n_bits"], cfg["seed"], rep)
                    sem = [cfg["seed"], ID_CANAL[nome_canal], ie, isnr, rep]
                    rng = np.random.default_rng(sem)
                    rx = func(esq, bits, snr, nome_canal, rng, cfg["rajada"])
                    erros, ber, _ = met.contar_erros(bits, rx)
                    linhas.append(dict(experimento=tipo, canal=nome_canal, esquema=esq, ebn0_db=snr,
                                       repeticao=rep, seed="-".join(map(str, sem)),
                                       n_bits=len(bits), erros=erros, ber=ber))
        if progresso:
            print(f"  [{tipo}] canal {nome_canal} concluído")
    return pd.DataFrame(linhas)


def agregar(bruto, cfg):
    """Média, desvio-padrão, IC95% (t de Student), mín/máx e BER teórica por (canal, esquema, SNR)"""
    r = cfg["rajada"]
    saida = []
    for (exp, can, esq, snr), g in bruto.groupby(["experimento", "canal", "esquema", "ebn0_db"]):
        b = g["ber"].to_numpy()
        n = len(b)
        dp = b.std(ddof=1) if n > 1 else 0.0
        ic = stats.t.ppf(0.975, n - 1) * dp / np.sqrt(n) if n > 1 else 0.0
        linha = exp == "linha"
        if can == "AWGN":
            teo = float((met.ber_teorica_linha if linha else met.ber_teorica)(esq, snr))
        else:
            teo = float(met.ber_teorica_rajada(esq, snr, r["p_gb"], r["p_bg"], r["penalidade_db"], linha))
        saida.append(dict(experimento=exp, canal=can, esquema=esq, ebn0_db=snr, n_repeticoes=n,
                          bits_total=int(g["n_bits"].sum()), erros_total=int(g["erros"].sum()),
                          ber_media=b.mean(), ber_desvio=dp, ber_ic95=ic,
                          ber_min=b.min(), ber_max=b.max(), ber_teorica=teo))
    return pd.DataFrame(saida)


# ponta a ponta (com texto)
def enlace_modulacao(texto, modulacao, ebn0_db, nome_canal, rng, cfg_rajada, linha=None):
    """Executa o enlace completo para um texto. `linha` in {None, 'Manchester'}."""
    bits_tx = textUtils.fromTexttoBinary(texto)
    a_enviar = cod.manchester_bits(bits_tx) if linha == "Manchester" else bits_tx
    k = mod.BITS_POR_SIMBOLO[modulacao]
    simbolos = mod.modular(modulacao, a_enviar)
    rx, mascara = _passar_canal(simbolos, ebn0_db, 1.0 / k, nome_canal, rng, cfg_rajada)
    demod = mod.demodular(modulacao, rx, len(a_enviar))
    violacoes = 0
    if linha == "Manchester":
        bits_rx, violacoes = cod.manchester_bits_decodificar(demod)
    else:
        bits_rx = demod
    erros, ber, idx = met.contar_erros(bits_tx, bits_rx)
    return dict(bits_tx=bits_tx, bits_rx=bits_rx, texto_rx=textUtils.fromBinarytoText(bits_rx),
                erros=erros, ber=ber, posicoes_erro=idx, violacoes_detectadas=violacoes,
                simbolos_tx=simbolos, simbolos_rx=rx, mascara_rajada=mascara)


def enlace_banda_base(texto, codigo, ebn0_db, nome_canal, rng, cfg_rajada):
    """AMI/Manchester diretamente em banda base (sem modulação)."""
    bits_tx = textUtils.fromTexttoBinary(texto)
    x = cod.manchester(bits_tx) if codigo == "Manchester" else cod.ami(bits_tx)
    eb = float(np.sum(x ** 2)) / len(bits_tx)
    y, _ = _passar_canal(x, ebn0_db, eb, nome_canal, rng, cfg_rajada)
    bits_rx = cod.manchester_decodificar(y) if codigo == "Manchester" else cod.ami_decodificar(y)
    erros, ber, idx = met.contar_erros(bits_tx, bits_rx)
    viol = cod.ami_violacoes(y) if codigo == "AMI" else 0
    return dict(bits_tx=bits_tx, bits_rx=bits_rx, texto_rx=textUtils.fromBinarytoText(bits_rx),
                erros=erros, ber=ber, posicoes_erro=idx, violacoes_detectadas=viol)


# recuperação da mensagem
def experimento_mensagem(cfg):
    """Transmite a mensagem de teste n_tentativas vezes por (canal, modulação, SNR, repetição) e mede:
    prob. de recuperação EXATA, BER e taxa de erro de caracteres (CER)"""
    bits_msg = textUtils.fromTexttoBinary(cfg["mensagem_teste"])
    L, nchar = len(bits_msg), len(bits_msg) // 8
    nt = cfg["mensagem_exp"]["n_tentativas"]
    linhas = []
    for nome_canal in ("AWGN", "RAJADA"):
        for ie, m in enumerate(cfg["modulacoes"]):
            for isnr, snr in enumerate(cfg["ebn0_db"]):
                for rep in range(cfg["mensagem_exp"]["n_repeticoes"]):
                    rng = np.random.default_rng([cfg["seed"], 5000 + ID_CANAL[nome_canal], ie, isnr, rep])
                    tx = np.tile(bits_msg, nt)
                    rx = simular_modulacao(m, tx, snr, nome_canal, rng, cfg["rajada"])
                    err = (tx != rx).reshape(nt, L)
                    linhas.append(dict(canal=nome_canal, esquema=m, ebn0_db=snr, repeticao=rep,
                                       n_tentativas=nt, prob_recuperacao=float(np.mean(~err.any(axis=1))),
                                       ber=float(err.mean()),
                                       cer=float(np.mean(err.reshape(nt, nchar, 8).any(axis=2)))))
    return pd.DataFrame(linhas)


def agregar_mensagem(df):
    g = df.groupby(["canal", "esquema", "ebn0_db"])
    out = g.agg(prob_media=("prob_recuperacao", "mean"), prob_desvio=("prob_recuperacao", "std"),
                cer_media=("cer", "mean"), cer_desvio=("cer", "std"), ber_media=("ber", "mean")).reset_index()
    return out


# tabela de compromisso
def ebn0_para_ber(df_esq, alvo):
    """Eb/N0 (dB) em que a curva MEDIDA cruza `alvo` (interpolação em log10(BER)). NaN se não cruzar"""
    d = df_esq.sort_values("ebn0_db")
    x, y = d["ebn0_db"].to_numpy(), d["ber_media"].to_numpy()
    for i in range(len(x) - 1):
        if y[i] >= alvo > y[i + 1] or (y[i] >= alvo and y[i + 1] == 0):
            ly0 = np.log10(y[i])
            ly1 = np.log10(max(y[i + 1], 1e-9))
            return float(x[i] + (np.log10(alvo) - ly0) * (x[i + 1] - x[i]) / (ly1 - ly0))
    return float("nan")


def tabela_compromisso(agg, cfg):
    mods = cfg["modulacoes"]
    am = agg[agg.experimento == "modulacao"]
    linhas = []
    for m in mods:
        a = am[(am.canal == "AWGN") & (am.esquema == m)]
        r = am[(am.canal == "RAJADA") & (am.esquema == m)]
        def b(df, s):
            v = df[df.ebn0_db == s]["ber_media"]
            return float(v.iloc[0]) if len(v) else float("nan")
        linhas.append({
            "Modulação": m,
            "Bits/símbolo": mod.BITS_POR_SIMBOLO[m],
            "Efic. espectral nominal (bits/s/Hz)": met.eficiencia_espectral_nominal(m),
            "BER AWGN @4 dB": b(a, 4), "BER AWGN @8 dB": b(a, 8), "BER AWGN @10 dB": b(a, 10),
            "Eb/N0 p/ BER=1e-3, AWGN (dB)": ebn0_para_ber(a, 1e-3),
            "Eb/N0 p/ BER=1e-2, AWGN (dB)": ebn0_para_ber(a, 1e-2),
            "Eb/N0 p/ BER=1e-2, rajada (dB)": ebn0_para_ber(r, 1e-2),
            "Eb/N0 p/ BER=1e-5, AWGN teórico (dB)": met.ebn0_necessario_teorico(m, 1e-5),
            "BER rajada @8 dB": b(r, 8), "BER rajada @12 dB": b(r, 12),
        })
    return pd.DataFrame(linhas)
