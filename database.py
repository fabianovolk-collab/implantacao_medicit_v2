import json
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# ----------------------------
# CONFIGURAÇÃO DA SERVICE ACCOUNT
# ----------------------------
try:
    # Lê o JSON como string do secrets
    service_account_str = st.secrets["GOOGLE_DRIVE"]["service_account_json"]
    
    # Converte para dicionário
    service_account_info = json.loads(service_account_str)
    
    # Corrige a private_key para quebras de linha reais
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
    
    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]
    )
    gc = gspread.authorize(credentials)

except Exception as e:
    st.error(f"Erro na configuração do Google Service Account: {e}")
    gc = None

# ----------------------------
# IDs dos arquivos no Google Drive
# ----------------------------
SHEET_CLIENTES = "14-mB92KNxpL3lPrbLFvEpyarKSVSfSBA"
SHEET_IMPLANTACAO = "1kda7U66av75JUJKPr71lN1kgXR5t0YbI"
SHEET_ETAPAS = "1Gkbpn6sapAb_Uk4_UvKEdg35d7TNZwx2"

# =============================
# FUNÇÃO AUXILIAR PARA PADRONIZAR DATAFRAME
# =============================
def padronizar_df(df, colunas_essenciais):
    for col in colunas_essenciais:
        if col not in df.columns:
            df[col] = ""
    df = df[colunas_essenciais]
    df.fillna("", inplace=True)
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
    try:
        sh = gc.open_by_key(SHEET_CLIENTES)
        ws = sh.sheet1
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        df = padronizar_df(df, colunas)
    except Exception as e:
        st.error(f"Erro ao carregar clientes: {e}")
        df = pd.DataFrame(columns=colunas)
    return df

def salvar_clientes(df):
    try:
        sh = gc.open_by_key(SHEET_CLIENTES)
        ws = sh.sheet1
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
    try:
        sh = gc.open_by_key(SHEET_IMPLANTACAO)
        ws = sh.sheet1
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        df = padronizar_df(df, colunas)
    except Exception as e:
        st.error(f"Erro ao carregar implantação: {e}")
        df = pd.DataFrame(columns=colunas)
    return df

def salvar_implantacao(df):
    try:
        sh = gc.open_by_key(SHEET_IMPLANTACAO)
        ws = sh.sheet1
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar implantação: {e}")

# =============================
# ETAPAS / CHECKLIST
# =============================
def carregar_etapas():
    colunas = ["etapa", "item", "ordem_etapa", "ordem_item", "ativo"]
    try:
        sh = gc.open_by_key(SHEET_ETAPAS)
        ws = sh.sheet1
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        df = padronizar_df(df, colunas)
        # Normaliza tipos
        df["ativo"] = df["ativo"].astype(str).str.lower().isin(["true","1","sim"])
        df["ordem_etapa"] = pd.to_numeric(df["ordem_etapa"], errors="coerce").fillna(1).astype(int)
        df["ordem_item"] = pd.to_numeric(df["ordem_item"], errors="coerce").fillna(1).astype(int)
    except Exception as e:
        st.error(f"Erro ao carregar checklist: {e}")
        df = pd.DataFrame(columns=colunas)
    return df

def salvar_etapas(df):
    try:
        sh = gc.open_by_key(SHEET_ETAPAS)
        ws = sh.sheet1
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar checklist: {e}")