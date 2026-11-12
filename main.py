from utils import codificacaoUtils, textUtils

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

print(f"Dados codificados em Manchester: {manchester_data}")
print(f"Dados codificados em AMI: {ami_data}")
