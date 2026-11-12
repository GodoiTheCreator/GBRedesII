from utils import codificacaoUtils, modulacaoUtils, modulacaoUtils, textUtils

""" 
Gerar uma mensagem em ASCII e convertê-la em dados binários.
"""

mensagem = "Hello, World!"
mensagem_ascii = textUtils.fromTexttoASCIIConverter(mensagem)
mensagem_binaria = textUtils.fromASCIItoBinaryConverter(mensagem)

print(f"Mensagem original: {mensagem}")
print(f"Mensagem em ASCII: {mensagem_ascii}")
print(f"Mensagem em binário: {mensagem_binaria}")

"""
Implementar pelo menos duas codificações de linha (por exemplo, AMI, Manchester ou bifase),
explicando a diferença entre codificação de linha e codificação de correção de erros.

Diferença entre codificação de linha e codificação de correção de erros:
- Codificação de linha: É um método de representar dados binários em sinais elétricos ou
    ópticos para transmissão em um meio físico. O objetivo principal da codificação de linha é garantir
    a integridade do sinal durante a transmissão, facilitando a sincronização e a detecção de erros.
- Codificação de correção de erros: É um método de adicionar informações extras aos dados transmitidos 
    para detectar e corrigir erros que podem ocorrer durante a transmissão.
"""
manchester_data = codificacaoUtils.manchester(mensagem_binaria)
ami_data = codificacaoUtils.ami(mensagem_binaria)

# print(f"Dados codificados em Manchester: {manchester_data}")
# print(f"Dados codificados em AMI: {ami_data}")

"""
Implementar e comparar pelo menos três modulações digitais, incluindo uma de ordem superior
(por exemplo, BPSK, QPSK e 16-QAM).
"""


bpsk_data = modulacaoUtils.bpsk(mensagem_binaria)
qpsk_data = modulacaoUtils.qpsk(mensagem_binaria)
sixteen_qam_data = modulacaoUtils.sixteen_qam(mensagem_binaria)

""" 
Simular canal AWGN com controle de SNR e um segundo cenário experimental, como ruído
em rajadas ou degradação adicional do canal.
"""




