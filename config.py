"""Configuração central do simulador.
Todos os parâmetros dos experimentos ficam aqui (e são gravados em
resultados/config_usada.json a cada execução, para reprodutibilidade).
"""
import copy

CONFIG = {
    # mensagens
    "mensagem_demo": "Redes de Computadores - UNISINOS - Trabalho II: codificacao de linha e modulacao digital.",
    "mensagem_teste": "Hello, World!",

    # reprodutibilidade
    "seed": 20261119,

    # --- plano experimental ---
    "ebn0_db": list(range(0, 13)),          # 13 valores (requisito: >= 8)
    "n_bits": 1_000_000,                    # bits por (esquema, SNR, repetição) (requisito: >= 100.000)
    "n_repeticoes": 10,                     # repetições independentes (requisito: >= 5)
    "modulacoes": ["BPSK", "QPSK", "16QAM"],
    "linhas": ["Manchester", "AMI"],

    # 2º cenário de canal: ruído em rajadas (modelo de Gilbert-Elliott)
    # Estado BOM: AWGN com a Eb/N0 nominal. Estado RUIM: ruído `penalidade_db` dB mais forte
    "rajada": {
        "p_gb": 0.005,          # P(bom -> ruim) por símbolo
        "p_bg": 0.10,           # P(ruim -> bom) por símbolo  (rajada média = 1/p_bg = 10 símbolos)
        "penalidade_db": 10.0,  # degradação de SNR dentro da rajada
    },

    # experimento de recuperação da mensagem
    "mensagem_exp": {"n_tentativas": 2000, "n_repeticoes": 5},

    # demonstração ponta a ponta
    "demo_ebn0_db": 4.0,
    "demo_seed": 7,

    # teste de consistência
    "consistencia_ebn0_db": 30.0,
    "consistencia_repeticoes": 1000,

    # constelações
    "constelacao_ebn0_db": 12.0,
    "constelacao_n_simbolos": 3000,
}


def config_rapida():
    """Versão reduzida só para testar o pipeline rapidamente (NÃO usar nos resultados finais)"""
    c = copy.deepcopy(CONFIG)
    c["n_bits"] = 100_000
    c["n_repeticoes"] = 5
    c["mensagem_exp"] = {"n_tentativas": 300, "n_repeticoes": 5}
    return c
