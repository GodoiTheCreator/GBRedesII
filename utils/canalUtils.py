def simulaAWGN(signal, snr):
    """
    Simula um canal AWGN (Additive White Gaussian Noise) para um sinal informado.

    Parâmetros:
    signal : array_like
        O sinal de entrada ao qual será adicionado ruído.
    snr : float
        A relação sinal-ruído desejada em decibéis (dB).

    Retorna:
    noisy_signal : array_like
        O sinal de saída com ruído adicionado.
    """
    import numpy as np

    # Calcula a potência do sinal
    signal_power = np.mean(np.abs(signal) ** 2)

    # Calcula a potência do ruído a partir da SNR
    snr_linear = 10 ** (snr / 10)
    noise_power = signal_power / snr_linear

    # Gera ruído gaussiano branco
    noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)

    # Adiciona o ruído ao sinal original
    noisy_signal = signal + noise

    return noisy_signal