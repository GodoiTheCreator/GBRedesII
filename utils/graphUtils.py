"""Geração de todos os gráficos"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import modulacaoUtils as mod, canalUtils as canal, metricasUtils as met, codificacaoUtils as cod, textUtils

COR = {"BPSK": "tab:blue", "QPSK": "tab:orange", "16QAM": "tab:green", "Manchester": "tab:purple", "AMI": "tab:red"}
MARC = {"BPSK": "o", "QPSK": "s", "16QAM": "^", "Manchester": "D", "AMI": "v"}
PISO = 1e-9


def _curva(ax, d, esq, estilo="-", rotulo=None, teoria=True, estilo_teoria=":"):
    d = d.sort_values("ebn0_db")
    x = d["ebn0_db"].to_numpy()
    m = d["ber_media"].to_numpy()
    ic = d["ber_ic95"].to_numpy()
    n_tot = d["bits_total"].to_numpy()
    pos = m > 0
    y = np.where(pos, m, 1.0 / n_tot)          # BER = 0 é desenhada em 1/N (limite superior)
    lo = np.maximum(m - ic, np.where(pos, m * 0.02, PISO))
    err = np.vstack([np.where(pos, y - lo, 0), np.where(pos, ic, 0)])
    vazio = esq == "BPSK"   # BPSK e QPSK têm BER idêntica: marcador vazado e maior para ambos ficarem visíveis
    ax.errorbar(x[pos], y[pos], yerr=err[:, pos], color=COR[esq], marker=MARC[esq], ls=estilo,
                ms=9 if vazio else 5, mfc="none" if vazio else None, lw=1.4, capsize=3, label=rotulo or esq)
    if (~pos).any():
        ax.plot(x[~pos], y[~pos], color=COR[esq], marker="v", ls="none", mfc="none", ms=6)
    if teoria:
        ax.semilogy(x, d["ber_teorica"], color=COR[esq], ls=estilo_teoria, lw=1.0, alpha=0.8)


def _fmt(ax, titulo, ymin=1e-7):
    ax.set_yscale("log")
    ax.set_ylim(ymin, 1)
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("BER")
    ax.set_title(titulo)
    ax.grid(True, which="both", alpha=0.3)


def fig_ber_modulacoes(agg, canal_nome, caminho, cfg):
    fig, ax = plt.subplots(figsize=(7, 5))
    d = agg[(agg.experimento == "modulacao") & (agg.canal == canal_nome)]
    for m in cfg["modulacoes"]:
        _curva(ax, d[d.esquema == m], m)
    ax.plot([], [], "k:", lw=1, label="teoria")
    ax.plot([], [], "kv", mfc="none", ls="none", label="BER = 0 (plotada em 1/N)")
    nome = "AWGN" if canal_nome == "AWGN" else "ruído em rajadas"
    nb = f"{cfg['n_bits']:,}".replace(",", ".")
    _fmt(ax, f"BER × Eb/N0 – canal {nome}\n(média e IC95% de {cfg['n_repeticoes']} repetições × {nb} bits)")
    ax.legend()
    fig.tight_layout(); fig.savefig(caminho, dpi=160); plt.close(fig)


def fig_awgn_vs_rajada(agg, caminho, cfg):
    mods = cfg["modulacoes"]
    fig, axs = plt.subplots(1, len(mods), figsize=(5 * len(mods), 4.6), sharey=True)
    d = agg[agg.experimento == "modulacao"]
    for ax, m in zip(axs, mods):
        _curva(ax, d[(d.esquema == m) & (d.canal == "AWGN")], m, "-", "AWGN")
        _curva(ax, d[(d.esquema == m) & (d.canal == "RAJADA")], m, "--", "Rajadas", teoria=False)
        dr = d[(d.esquema == m) & (d.canal == "RAJADA")].sort_values("ebn0_db")
        ax.semilogy(dr.ebn0_db, dr.ber_teorica, color="k", ls=":", lw=1, label="teoria (AWGN / mistura de rajadas)")
        _fmt(ax, m)
        ax.legend(fontsize=8)
    fig.suptitle("Impacto da degradação (rajadas) sobre a BER", y=1.0)
    fig.tight_layout(); fig.savefig(caminho, dpi=160); plt.close(fig)


def fig_linha(agg, caminho, cfg):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    d = agg[agg.experimento == "linha"]
    for ax, c, nome in zip(axs, ("AWGN", "RAJADA"), ("AWGN", "ruído em rajadas")):
        for l in cfg["linhas"]:
            _curva(ax, d[(d.canal == c) & (d.esquema == l)], l)
        _fmt(ax, f"Codificação de linha – {nome}")
        ax.legend()
    fig.tight_layout(); fig.savefig(caminho, dpi=160); plt.close(fig)


def fig_mensagem(aggm, caminho, cfg):
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, c, nome in zip(axs, ("AWGN", "RAJADA"), ("AWGN", "ruído em rajadas")):
        for m in cfg["modulacoes"]:
            d = aggm[(aggm.canal == c) & (aggm.esquema == m)].sort_values("ebn0_db")
            ax.errorbar(d.ebn0_db, d.prob_media, yerr=d.prob_desvio.fillna(0), color=COR[m], marker=MARC[m],
                        capsize=3, label=m)
        ax.set_title(f"Recuperação exata de \"{cfg['mensagem_teste']}\" – {nome}")
        ax.set_xlabel("Eb/N0 (dB)"); ax.grid(alpha=0.3); ax.legend()
    axs[0].set_ylabel("P(mensagem recebida sem nenhum erro)")
    fig.tight_layout(); fig.savefig(caminho, dpi=160); plt.close(fig)


def fig_constelacoes(caminho, cfg):
    snr = cfg["constelacao_ebn0_db"]
    n = cfg["constelacao_n_simbolos"]
    r = cfg["rajada"]
    mods = cfg["modulacoes"]
    fig, axs = plt.subplots(len(mods), 3, figsize=(12, 3.8 * len(mods)))
    for i, m in enumerate(mods):
        k = mod.BITS_POR_SIMBOLO[m]
        bits = np.random.default_rng(cfg["seed"]).integers(0, 2, n * k, dtype=np.uint8)
        tx = mod.modular(m, bits)
        rx_a = canal.simulaAWGN(tx, snr, 1.0 / k, np.random.default_rng(1))
        rx_r, mask = canal.simulaRajadas(tx, snr, 1.0 / k, np.random.default_rng(2), **r)
        ideal, _ = mod.constelacao_ideal(m)
        paineis = [("Antes do canal (TX)", tx, None), (f"Depois – AWGN ({snr:g} dB)", rx_a, None),
                   (f"Depois – rajadas ({snr:g} dB)", rx_r, mask)]
        for ax, (t, s, mk) in zip(axs[i], paineis):
            if mk is None:
                ax.scatter(s.real, s.imag, s=6, alpha=0.4, color=COR[m])
            else:
                ax.scatter(s.real[~mk], s.imag[~mk], s=6, alpha=0.4, color=COR[m], label="estado bom")
                ax.scatter(s.real[mk], s.imag[mk], s=8, alpha=0.7, color="crimson", label="estado ruim (rajada)")
                ax.legend(fontsize=7, loc="upper right")
            ax.scatter(ideal.real, ideal.imag, marker="x", color="k", s=40)
            lim = 1.8 if m != "BPSK" else 2.0
            ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_aspect("equal"); ax.grid(alpha=0.3)
            ax.set_title(f"{m} – {t}", fontsize=10); ax.set_xlabel("I"); ax.set_ylabel("Q")
    fig.tight_layout(); fig.savefig(caminho, dpi=140); plt.close(fig)


def fig_compromisso(agg, tab, caminho, cfg):
    fig, ax = plt.subplots(figsize=(7, 5))
    eta = np.linspace(0.4, 5, 200)
    ax.plot(eta, met.ebn0_minimo_shannon_db(eta), "k--", label="Limite de Shannon")
    for m in cfg["modulacoes"]:
        e = met.eficiencia_espectral_nominal(m)
        y = met.ebn0_necessario_teorico(m, 1e-5)
        ax.scatter(e, y, s=90, color=COR[m], marker=MARC[m], zorder=3, label=f"{m}")
        ax.annotate(m, (e, y), textcoords="offset points", xytext=(8, -4))
    ax.set_xlabel("Eficiência espectral nominal (bits/s/Hz)")
    ax.set_ylabel("Eb/N0 necessário para BER = 10⁻⁵ (dB, AWGN teórico)")
    ax.set_title("Compromisso BER × eficiência espectral")
    ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(caminho, dpi=160); plt.close(fig)


def fig_formas_de_onda(caminho, texto="Hi"):
    bits = textUtils.fromTexttoBinary(texto)
    n = len(bits)
    t = np.arange(n)
    fig, axs = plt.subplots(4, 1, figsize=(10, 6.5), sharex=True)
    sinais = [("Bits (" + texto + ")", bits.astype(float), None), ("NRZ-L (referência)", cod.nrz(bits), None),
              ("AMI", cod.ami(bits), None), ("Manchester", cod.manchester(bits), "manch")]
    for ax, (nome, x, tipo) in zip(axs, sinais):
        if tipo == "manch":
            ax.step(np.arange(2 * n) / 2.0, x, where="post", color="tab:purple")
        else:
            ax.step(t, x, where="post", color="tab:blue")
        ax.set_ylabel(nome, fontsize=8); ax.grid(alpha=0.3)
    for ax in axs:
        for i in range(n + 1):
            ax.axvline(i, color="gray", lw=0.3)
    for i, b in enumerate(bits):
        axs[0].text(i + 0.5, 0.5, str(b), ha="center", va="center")
    axs[-1].set_xlabel("tempo (períodos de bit)")
    fig.tight_layout(); fig.savefig(caminho, dpi=150); plt.close(fig)
