"""Simulador de transmissão digital – Trabalho II de Redes de Computadores (UNISINOS)."""

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

from config import CONFIG, config_rapida
from utils import textUtils, codificacaoUtils, modulacaoUtils, canalUtils, metricasUtils, experimentoUtils as exp, graphUtils

RES = "resultados"
FIG = os.path.join(RES, "figuras")


# DEMONSTRAÇÃO
def demo(cfg):
    """Gera mensagem ASCII -> bits -> linha -> modulação -> canal -> demodulação -> decodificação -> texto"""
    L = []
    p = L.append
    msg = cfg["mensagem_demo"]
    codigos = textUtils.fromTexttoASCIIConverter(msg)
    bits = textUtils.fromTexttoBinary(msg)
    snr = cfg["demo_ebn0_db"]

    p("=" * 78)
    p("1) MENSAGEM -> ASCII -> BITS")
    p("=" * 78)
    p(f"Mensagem original : {msg}")
    p(f"Códigos ASCII     : {codigos[:12]}{' ...' if len(codigos) > 12 else ''}  ({len(codigos)} caracteres)")
    p(f"Binário (1ºs 8 B) : {textUtils.formatarBinario(bits[:64])} ...  ({len(bits)} bits)")
    p("")
    p("Codificação de LINHA × codificação de CORREÇÃO de erros:")
    p("  - Linha: define COMO os bits viram níveis de sinal (sincronismo, sem DC, detecção de")
    p("    violações). Não corrige erros e não acrescenta proteção algébrica à informação.")
    p("  - Correção de erros (FEC: Hamming, Reed-Solomon, convolucional...): acrescenta bits")
    p("    redundantes calculados dos dados, permitindo detectar E corrigir erros. Aqui NÃO usada.")
    p("")
    p("=" * 78)
    p("2) CODIFICAÇÃO DE LINHA (primeiros 8 bits)")
    p("=" * 78)
    p(f"Bits      : {bits[:8].tolist()}")
    p(f"Manchester: {codificacaoUtils.manchester(bits[:8]).astype(int).tolist()}")
    p(f"AMI       : {codificacaoUtils.ami(bits[:8]).astype(int).tolist()}")
    p("")

    for nome_canal in ("AWGN", "RAJADA"):
        p("=" * 78)
        p(f"3) ENLACE COMPLETO – canal {nome_canal}, Eb/N0 = {snr:g} dB")
        p("=" * 78)
        for m in cfg["modulacoes"]:
            for linha in (None, "Manchester"):
                rng = np.random.default_rng([cfg["demo_seed"], ord(m[0]), len(m), 1 if linha else 0])
                r = exp.enlace_modulacao(msg, m, snr, nome_canal, rng, cfg["rajada"], linha)
                rot = f"{m}" + (" + Manchester" if linha else "")
                p(f"[{rot}]  bits errados: {r['erros']}/{len(bits)}  BER={r['ber']:.4f}"
                  + (f"  violações Manchester detectadas: {r['violacoes_detectadas']}" if linha else ""))
                if r["erros"]:
                    p(f"   posições (índice do bit): {r['posicoes_erro'][:20].tolist()}{' ...' if r['erros'] > 20 else ''}")
                p(f"   TX: {msg}")
                p(f"   RX: {r['texto_rx']}")
        p("Nota: na demo, Eb/N0 é a energia por bit TRANSMITIDO. Em '+ Manchester' cada bit de informação")
        p("usa 2 chips; se o Eb/N0 fosse contado por bit de INFORMAÇÃO, Manchester teria 3 dB a menos por chip.")
        p("As 'violações' (chips iguais '00'/'11') são erros DETECTADOS pela própria codificação de linha.")
        p("")

    p("=" * 78)
    p(f"4) CODIFICAÇÃO DE LINHA PURA EM BANDA BASE (Eb/N0 = {snr + 4:g} dB, AWGN)")
    p("=" * 78)
    for c in cfg["linhas"]:
        r = exp.enlace_banda_base(msg, c, snr + 4, "AWGN", np.random.default_rng(cfg["demo_seed"]), cfg["rajada"])
        p(f"[{c}] bits errados: {r['erros']}/{len(bits)}  BER={r['ber']:.4f}"
          + (f"  violações bipolares detectadas: {r['violacoes_detectadas']}" if c == "AMI" else ""))
        p(f"   RX: {r['texto_rx']}")
    texto = "\n".join(L)
    print(texto)
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "demo.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")


# CONSISTÊNCIA
def consistencia(cfg):
    """Em canal ideal e em SNR elevada a mensagem deve ser recuperada SEM nenhum erro"""
    L = []
    p = L.append
    msg = cfg["mensagem_teste"]
    bits = textUtils.fromTexttoBinary(msg)
    snr = cfg["consistencia_ebn0_db"]
    n = cfg["consistencia_repeticoes"]
    p(f"Mensagem de teste: \"{msg}\" ({len(bits)} bits)")
    p(f"Teste A: canal IDEAL (sem ruído).   Teste B: AWGN e rajadas com Eb/N0 = {snr:g} dB, {n} repetições.")
    p("")
    p(f"{'Esquema':<22}{'Canal':<10}{'Tentativas':>11}{'Recuperações exatas':>22}{'Bits errados':>14}  Resultado")
    ok_geral = True
    esquemas = [(m, l) for m in cfg["modulacoes"] for l in (None, "Manchester")]
    for m, l in esquemas:
        for canal_nome, reps in (("IDEAL", 1), ("AWGN", n), ("RAJADA", n)):
            exatas, err_tot = 0, 0
            for i in range(reps):
                rng = np.random.default_rng([cfg["seed"], 77, i])
                r = exp.enlace_modulacao(msg, m, snr, canal_nome, rng, cfg["rajada"], l)
                exatas += int(r["texto_rx"] == msg and r["erros"] == 0)
                err_tot += r["erros"]
            ok = exatas == reps
            ok_geral &= ok
            p(f"{m + (' + Manchester' if l else ''):<22}{canal_nome:<10}{reps:>11}{exatas:>22}{err_tot:>14}  {'OK' if ok else 'FALHOU'}")
    for c in cfg["linhas"]:
        for canal_nome, reps in (("IDEAL", 1), ("AWGN", n)):
            exatas, err_tot = 0, 0
            for i in range(reps):
                r = exp.enlace_banda_base(msg, c, snr, canal_nome, np.random.default_rng([cfg["seed"], 78, i]), cfg["rajada"])
                exatas += int(r["erros"] == 0)
                err_tot += r["erros"]
            ok = exatas == reps
            ok_geral &= ok
            p(f"{c + ' (banda base)':<22}{canal_nome:<10}{reps:>11}{exatas:>22}{err_tot:>14}  {'OK' if ok else 'FALHOU'}")
    p("")
    p("RESULTADO GERAL: " + ("APROVADO – mensagem recuperada integralmente em todos os casos." if ok_geral else "REPROVADO"))
    p("")
    p("Observações / possíveis divergências:")
    p("  - O 16-QAM exige múltiplo de 4 bits e o QPSK de 2: se a mensagem não for múltipla, o transmissor")
    p("    acrescenta bits de preenchimento (zeros) e o receptor os descarta; sem isso haveria erro de tamanho.")
    p("  - Em Eb/N0 alto a probabilidade de erro não é exatamente zero, apenas desprezível (ex.: BER 16-QAM")
    p(f"    teórica a {snr:g} dB ≈ {float(metricasUtils.ber_teorica('16QAM', snr)):.1e}); com {n} repetições de {len(bits)} bits")
    p("    não se espera observar nenhum erro.")
    p("  - No canal de rajadas, mesmo a 30 dB a rajada (-10 dB) deixa Eb/N0 efetivo em 20 dB: ainda sem erros.")
    texto = "\n".join(L)
    print(texto)
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "consistencia.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    return ok_geral


# EXPERIMENTOS
def experimentos(cfg):
    os.makedirs(FIG, exist_ok=True)
    with open(os.path.join(RES, "config_usada.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    t0 = time.time()
    print("Varredura de modulações...")
    bruto = exp.varredura(cfg, "modulacao")
    print("Varredura de codificações de linha...")
    bruto_l = exp.varredura(cfg, "linha")
    todo = pd.concat([bruto, bruto_l], ignore_index=True)
    todo.to_csv(os.path.join(RES, "resultados_brutos.csv"), index=False)
    exp.agregar(todo, cfg).to_csv(os.path.join(RES, "resultados_agregados.csv"), index=False)
    print("Experimento de recuperação de mensagem...")
    msg = exp.experimento_mensagem(cfg)
    msg.to_csv(os.path.join(RES, "mensagem_bruto.csv"), index=False)
    exp.agregar_mensagem(msg).to_csv(os.path.join(RES, "mensagem_agregado.csv"), index=False)
    print(f"Concluído em {time.time() - t0:.0f} s. CSVs em {RES}/")


# GRÁFICOS
def graficos(cfg):
    os.makedirs(FIG, exist_ok=True)
    agg = pd.read_csv(os.path.join(RES, "resultados_agregados.csv"))
    aggm = pd.read_csv(os.path.join(RES, "mensagem_agregado.csv"))
    graphUtils.fig_ber_modulacoes(agg, "AWGN", os.path.join(FIG, "fig1_ber_awgn.png"), cfg)
    graphUtils.fig_ber_modulacoes(agg, "RAJADA", os.path.join(FIG, "fig2_ber_rajadas.png"), cfg)
    graphUtils.fig_awgn_vs_rajada(agg, os.path.join(FIG, "fig3_awgn_vs_rajadas.png"), cfg)
    graphUtils.fig_linha(agg, os.path.join(FIG, "fig4_codificacao_linha.png"), cfg)
    graphUtils.fig_constelacoes(os.path.join(FIG, "fig5_constelacoes.png"), cfg)
    graphUtils.fig_mensagem(aggm, os.path.join(FIG, "fig6_recuperacao_mensagem.png"), cfg)
    tab = exp.tabela_compromisso(agg, cfg)
    graphUtils.fig_compromisso(agg, tab, os.path.join(FIG, "fig7_compromisso_ber_eficiencia.png"), cfg)
    graphUtils.fig_formas_de_onda(os.path.join(FIG, "fig8_formas_de_onda_linha.png"))
    tab.to_csv(os.path.join(RES, "tabela_compromisso.csv"), index=False)
    with open(os.path.join(RES, "tabela_compromisso.md"), "w", encoding="utf-8") as f:
        f.write(tabela_md(tab))
    print(tabela_md(tab))
    print(f"Figuras em {FIG}/")


def _fmt_num(v):
    if isinstance(v, (int, np.integer)):
        return str(v)
    if isinstance(v, float):
        if np.isnan(v):
            return "não atingido (> 12)"
        return f"{v:.2e}" if (v != 0 and abs(v) < 0.1) else (f"{v:.2f}" if v != 0 else "0 (sem erros)")
    return str(v)


def tabela_md(tab):
    cab = "| " + " | ".join(tab.columns) + " |\n|" + "---|" * len(tab.columns) + "\n"
    corpo = "".join("| " + " | ".join(_fmt_num(v) for v in row) + " |\n" for row in tab.itertuples(index=False))
    return cab + corpo


# CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("comando", choices=["demo", "consistencia", "experimentos", "graficos", "tudo"])
    ap.add_argument("--rapido", action="store_true", help="configuração reduzida (apenas para testar)")
    a = ap.parse_args()
    cfg = config_rapida() if a.rapido else CONFIG
    os.makedirs(FIG, exist_ok=True)
    if a.comando in ("demo", "tudo"):
        demo(cfg)
    if a.comando in ("consistencia", "tudo"):
        if not consistencia(cfg):
            sys.exit(1)
    if a.comando in ("experimentos", "tudo"):
        experimentos(cfg)
    if a.comando in ("graficos", "tudo"):
        graficos(cfg)
