import pandas as pd
import os

ARQUIVO_CLIENTES = "clientes.csv"
ARQUIVO_IMPLANTACAO = "implantacao.csv"
ARQUIVO_ETAPAS = "etapas_checklist.csv"

# =============================
# CLIENTES
# =============================
def carregar_clientes():

    if os.path.exists(ARQUIVO_CLIENTES):
        df = pd.read_csv(ARQUIVO_CLIENTES, dtype=str)
    else:
        df = pd.DataFrame(columns=[
            "Tipo_Pessoa",
            "CNPJ_CPF",
            "Nome",
            "Telefone",
            "Responsavel_Comercial",
            "Responsavel_Cliente",
            "Responsavel_Medicit"
        ])

    for col in df.columns:
        df[col] = df[col].fillna("")

    return df


def salvar_clientes(df):
    df.to_csv(ARQUIVO_CLIENTES, index=False)


# =============================
# IMPLANTAÇÃO
# =============================
def carregar_implantacao():

    if os.path.exists(ARQUIVO_IMPLANTACAO):
        df = pd.read_csv(ARQUIVO_IMPLANTACAO, dtype=str)
    else:
        df = pd.DataFrame()

    colunas = [
        "CNPJ_CPF",
        "Cliente",
        "Etapa",
        "Status",
        "Data_Inicio",
        "Data_Conclusao",
        "Responsavel_Etapa",
        "Responsavel_Cliente",
        "Participantes",
        "Motivo",
        "Proxima_Acao",
        "Checklist",
        "Ultima_Atualizacao"
    ]

    for col in colunas:
        if col not in df.columns:
            df[col] = ""

    return df


def salvar_implantacao(df):
    df.to_csv(ARQUIVO_IMPLANTACAO, index=False)


# =============================
# ETAPAS DINÂMICAS
# =============================
def carregar_etapas():

    if os.path.exists(ARQUIVO_ETAPAS):
        df = pd.read_csv(ARQUIVO_ETAPAS)
    else:
        df = pd.DataFrame(columns=["Etapa", "Item"])

    df.fillna("", inplace=True)
    return df


def salvar_etapas(df):
    df.to_csv(ARQUIVO_ETAPAS, index=False)

def carregar_etapas_checklist():
    caminho = "data/etapas_checklist.csv"

    if not os.path.exists(caminho):
        return pd.DataFrame(columns=["Etapa", "Checklist"])

    return pd.read_csv(caminho).fillna("")    