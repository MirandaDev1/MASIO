import json
import os
import re


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_CONFIG = os.path.join(BASE_DIR, "config", "comandos.json")


class ComandoNaoEncontradoError(ValueError):
    pass


def carregar_configuracao(caminho=CAMINHO_CONFIG):
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho}")

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ValueError(f"JSON inválido em {caminho}: {erro}") from erro
    except OSError as erro:
        raise OSError(f"Falha ao ler o arquivo de configuração: {erro}") from erro

    if not isinstance(dados, dict):
        raise ValueError("O conteúdo de comandos.json deve ser um objeto JSON.")

    if "acoes" not in dados or "apps" not in dados:
        raise ValueError("O JSON deve conter as chaves 'acoes' e 'apps'.")

    return dados


def normalizar_texto(texto):
    texto = str(texto).lower().strip()
    texto = re.sub(r"[^\w\sáàâãéèêíïóòôõöúçñ-]", " ", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def localizar_acao(texto_normalizado, acoes):
    melhor_acao = None
    maior_tamanho = -1

    for nome_acao, dados_acao in acoes.items():
        sinonimos = dados_acao.get("sinonimos", [])
        if not isinstance(sinonimos, list):
            continue

        for sinonimo in sinonimos:
            sinonimo_norm = normalizar_texto(sinonimo)
            if not sinonimo_norm:
                continue

            padrao = r"(?<!\w)" + re.escape(sinonimo_norm) + r"(?!\w)"
            if re.search(padrao, texto_normalizado):
                tamanho = len(sinonimo_norm)
                if tamanho > maior_tamanho:
                    melhor_acao = nome_acao
                    maior_tamanho = tamanho

    return melhor_acao


def localizar_alvo(texto_normalizado, acao, config):
    apps = config.get("apps", {})
    if not isinstance(apps, dict):
        return ""

    for nome_app, executavel in apps.items():
        nome_app_norm = normalizar_texto(nome_app)
        executavel_norm = normalizar_texto(executavel)

        if re.search(r"(?<!\w)" + re.escape(nome_app_norm) + r"(?!\w)", texto_normalizado):
            return nome_app

        if re.search(r"(?<!\w)" + re.escape(executavel_norm) + r"(?!\w)", texto_normalizado):
            return nome_app

    if acao:
        sinonimos = config.get("acoes", {}).get(acao, {}).get("sinonimos", [])
        for sinonimo in sinonimos:
            sinonimo_norm = normalizar_texto(sinonimo)
            if not sinonimo_norm:
                continue
            texto_normalizado = re.sub(
                r"(?<!\w)" + re.escape(sinonimo_norm) + r"(?!\w)",
                " ",
                texto_normalizado
            )

    texto_restante = re.sub(r"\s+", " ", texto_normalizado).strip()
    return texto_restante


def analisar(entrada):
    """
    Recebe uma string do usuário e retorna:
    {'acao': '...', 'alvo': '...'}
    """
    if not isinstance(entrada, str) or not entrada.strip():
        raise ValueError("A entrada deve ser uma string não vazia.")

    config = carregar_configuracao()
    texto = normalizar_texto(entrada)

    acao = localizar_acao(texto, config["acoes"])
    if not acao:
        raise ComandoNaoEncontradoError(f"Comando não reconhecido: {entrada}")

    alvo = localizar_alvo(texto, acao, config)

    return {
        "acao": acao,
        "alvo": alvo
    }


if __name__ == "__main__":
    try:
        entrada = input("Comando: ")
        resultado = analisar(entrada)
        print(resultado)
    except Exception as erro:
        print(f"Erro: {erro}")
