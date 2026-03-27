import json
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------
# CARREGAR SERVICE ACCOUNT
# ----------------------------
def conectar_google():
    try:
        # ===== PRIORIDADE: STREAMLIT CLOUD =====
        if "GOOGLE_DRIVE" in st.secrets:
            service_account_info = dict(st.secrets["GOOGLE_DRIVE"])

        # ===== FALLBACK: ARQUIVO LOCAL =====
        else:
            with open("medicit-1712064582328-fa3976fdd1e4.json") as f:
                service_account_info = json.load(f)

        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/spreadsheets"
            ]
        )

        return gspread.authorize(credentials)

    except Exception as e:
        st.error(f"Erro ao conectar com Google: {e}")
        return None


gc = conectar_google()

# ----------------------------
# IDs DAS PLANILHAS
# ----------------------------
SHEET_CLIENTES = "1gglsDbdPYv-3fgsNHspNZd1MlPf3x2mcGDYsR7VEPWA"
SHEET_IMPLANTACAO = "1kda7U66av75JUJKPr71lN1kgXR5t0YbI"
SHEET_ETAPAS = "1Gkbpn6sapAb_Uk4_UvKEdg35d7TNZwx2"


# =============================
# PADRONIZAR DATAFRAME
# =============================
def padronizar_df(df, colunas):
    for col in colunas:
        if col not in df.columns:
            df[col] = ""

    df = df[colunas]
    df = df.fillna("")
    return df


# =============================
# CLIENTES
# =============================
def carregar_clientes():
    colunas = [
        "Tipo_Pessoa",
        "CNPJ_CPF",
        "Nome",
        "Telefone",
        "Responsavel_Comercial",
        "Responsavel_Cliente",
        "Responsavel_Medicit"
    ]

    if not gc:
        return pd.DataFrame(columns=colunas)

    try:
        ws = gc.open_by_key(SHEET_CLIENTES).sheet1
        df = pd.DataFrame(ws.get_all_records())
        return padronizar_df(df, colunas)

    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")
        return pd.DataFrame(columns=colunas)


def salvar_clientes(df):
    if not gc:
        return

    try:
        ws = gc.open_by_key(SHEET_CLIENTES).sheet1
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())

    except Exception as e:
        st.error(f"Erro ao salvar clientes: {e}")


# =============================
# IMPLANTAÇÃO
# =============================
def carregar_implantacao():
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

    if not gc:
        return pd.DataFrame(columns=colunas)

    try:
        ws = gc.open_by_key(SHEET_IMPLANTACAO).sheet1
        df = pd.DataFrame(ws.get_all_records())
        return padronizar_df(df, colunas)

    except Exception as e:
        st.error(f"Erro ao carregar implantação: {e}")
        return pd.DataFrame(columns=colunas)


def salvar_implantacao(df):
    if not gc:
        return

    try:
        ws = gc.open_by_key(SHEET_IMPLANTACAO).sheet1
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())

    except Exception as e:
        st.error(f"Erro ao salvar implantação: {e}")


# =============================
# ETAPAS / CHECKLIST
# =============================
def carregar_etapas():
    colunas = ["etapa", "item", "ordem_etapa", "ordem_item", "ativo"]

    if not gc:
        return pd.DataFrame(columns=colunas)

    try:
        ws = gc.open_by_key(SHEET_ETAPAS).sheet1
        df = pd.DataFrame(ws.get_all_records())
        df = padronizar_df(df, colunas)

        # Tipos
        df["ativo"] = df["ativo"].astype(str).str.lower().isin(["true", "1", "sim"])
        df["ordem_etapa"] = pd.to_numeric(df["ordem_etapa"], errors="coerce").fillna(1).astype(int)
        df["ordem_item"] = pd.to_numeric(df["ordem_item"], errors="coerce").fillna(1).astype(int)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar etapas: {e}")
        return pd.DataFrame(columns=colunas)


def salvar_etapas(df):
    if not gc:
        return

    try:
        ws = gc.open_by_key(SHEET_ETAPAS).sheet1
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())

    except Exception as e:
        st.error(f"Erro ao salvar etapas: {e}")