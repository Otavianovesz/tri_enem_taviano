import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from typing import List, Tuple, Optional

# --- Constantes da Escala ENEM ---
# Estes são os valores padrão usados pelo INEP para normalizar as notas.
# Média da escala de proficiência (theta).
THETA_MEDIA = 0
# Desvio padrão da escala de proficiência (theta).
THETA_DESVIO_PADRAO = 1
# Média da nota final na escala ENEM.
NOTA_ENEM_MEDIA = 500
# Desvio padrão da nota final na escala ENEM.
NOTA_ENEM_DESVIO_PADRAO = 100

def probabilidade_acerto(theta: float, a: float, b: float, c: float) -> float:
    """
    Calcula a probabilidade de um indivíduo com proficiência (theta) acertar um item.
    Utiliza o Modelo Logístico de 3 Parâmetros (ML3).

    :param theta: A proficiência (habilidade) do indivíduo.
    :param a: Parâmetro 'a' do item (discriminação).
    :param b: Parâmetro 'b' do item (dificuldade).
    :param c: Parâmetro 'c' do item (probabilidade de acerto casual).
    :return: A probabilidade de acerto (um valor entre c e 1).
    """
    # O fator 1.7 é usado para aproximar a função logística da ogiva normal.
    fator_escala = 1.7
    expoente = -fator_escala * a * (theta - b)
    prob = c + (1 - c) * (1 / (1 + np.exp(expoente)))
    return prob

def log_verossimilhanca(theta: float, respostas: List[int], parametros_itens: List[Tuple[float, float, float]]) -> float:
    """
    Calcula o logaritmo negativo da função de verossimilhança.
    O objetivo da otimização é MINIMIZAR esta função, o que equivale a MAXIMIZAR a verossimilhança.

    :param theta: A proficiência (habilidade) do indivíduo.
    :param respostas: Uma lista de 0s (erro) e 1s (acerto) para cada item.
    :param parametros_itens: Uma lista de tuplas, onde cada tupla contém os parâmetros (a, b, c) de um item.
    :return: O valor do logaritmo negativo da verossimilhança.
    """
    log_likelihood = 0.0
    # Adiciona um pequeno valor para evitar o log de zero
    epsilon = 1e-9

    for i, resposta in enumerate(respostas):
        a, b, c = parametros_itens[i]
        p = probabilidade_acerto(theta, a, b, c)

        if resposta == 1: # Acerto
            log_likelihood += np.log(p + epsilon)
        else: # Erro
            log_likelihood += np.log(1 - p + epsilon)

    # Retornamos o negativo porque os otimizadores trabalham com minimização.
    return -log_likelihood

def estimar_proficiencia(respostas: List[int], parametros_itens: List[Tuple[float, float, float]]) -> Optional[float]:
    """
    Estima a proficiência (theta) de um indivíduo usando o método de Máxima Verossimilhança.

    :param respostas: Lista de 0s e 1s representando as respostas.
    :param parametros_itens: Lista de tuplas com os parâmetros (a, b, c) dos itens.
    :return: O valor estimado de theta, ou None se a otimização falhar.
    """
    # Verifica casos extremos que não permitem o cálculo (todos acertos ou todos erros)
    if all(r == 1 for r in respostas) or all(r == 0 for r in respostas):
        print("Padrão de resposta extremo (todos acertos ou todos erros). Não é possível estimar um theta único.")
        return None

    # Ponto de partida para a otimização. 0 é a média da proficiência.
    theta_inicial = 0.0
    
    # Realiza a otimização para encontrar o theta que minimiza o log-verossimilhança negativo.
    # 'L-BFGS-B' é um método de otimização eficiente que permite a definição de limites.
    resultado = minimize(
        fun=log_verossimilhanca,
        x0=theta_inicial,
        args=(respostas, parametros_itens),
        method='L-BFGS-B',
        bounds=[(-4, 4)]  # Limita a busca de theta a um intervalo razoável.
    )

    if resultado.success:
        return float(resultado.x[0])
    else:
        print(f"Otimização falhou em convergir: {resultado.message}")
        return None

def calcular_nota_tri(theta: Optional[float]) -> Optional[float]:
    """
    Converte a proficiência (theta) para a escala de notas do ENEM.

    :param theta: O valor da proficiência estimado.
    :return: A nota final na escala do ENEM (tipicamente entre 0 e 1000), ou None se theta for inválido.
    """
    if theta is None:
        return None
        
    # A transformação é uma normalização linear padrão.
    nota = NOTA_ENEM_MEDIA + (theta - THETA_MEDIA) * (NOTA_ENEM_DESVIO_PADRAO / THETA_DESVIO_PADRAO)
    return nota

