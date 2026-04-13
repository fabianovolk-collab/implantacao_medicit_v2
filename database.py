import re
import time
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SHEET_IDS = {
    "clientes":    "1gglsDbdPYv-3fgsNHspNZd1MlPf3x2mcGDYsR7VEPWA",
    "implantacao": "1Uaxabzo-vxGG7oPP_IuZWQOEjbztCprV6xfIWlFMwEU",
    "etapas":      "1sJ68oM4sPN_5LagHk1KJ3tOtr4Sg-nlITUubKo6O9wI",
    "historico":   "1FjRawI6K-11N9RNfBhyM1unHRZ-lTLXPC6YeG5Nkf7Y"
}

ABA_PADRAO    = "Página1"
CHECKLIST_SEP = "|"

PACOTES_DISPONIVEIS = ["Start", "Gold", "Personalizado"]
PRIORIDADES         = ["Alta", "Média", "Baixa"]

SCHEMAS = {
    "clientes": [
        "Tipo_Pessoa",
        "cnpj_cpf",
        "Nome",
        "Telefone",
        "Responsavel_Comercial",
        "Responsavel_Cliente",
        "Responsavel_Medicit",
        # campos de contrato
        "data_ass_contrato",
        "pacote",
        "adicional_pacote",
        "qtde_agendas",
        "prazo_implantacao_dias",
        "prioridade",
        "data_prevista_inicio",      # era data_inicio_implantacao / responsavel_implantacao removido
        "data_conclusao_contrato",
        "observacao"
    ],
    "implantacao": [
        "chave", "cnpj_cpf", "cliente", "etapa", "status",
        "data_inicio", "checklist", "responsavel_medicit", "responsavel_cliente",
        "participantes", "motivo", "proxima_acao", "ultima_atualizacao", "data_conclusao"
    ],
    "etapas": [
        "etapa", "item", "ordem_etapa", "ordem_item"
    ],
    "historico": [
        "data_hora", "cnpj_cpf", "cliente", "pagina",
        "acao", "etapa", "campo", "valor_anterior", "valor_novo"
    ]
}

# =============================
# NORMALIZAÇÃO CPF/CNPJ
# =============================

def normalizar_doc(valor):
    digits = re.sub(r"\D", "", str(valor))
    if not digits:
        return ""
    return digits.zfill(11) if len(digits) <= 11 else digits.zfill(14)

def normalizar_chave(valor):
    partes   = str(valor).split("||", 1)
    doc_norm = normalizar_doc(partes[0])
    etapa    = partes[1] if len(partes) > 1 else ""
    return f"{doc_norm}||{etapa}"

def normalizar_coluna(col, serie):
    if col == "cnpj_cpf":
        return serie.apply(normalizar_doc)
    if col == "chave":
        return serie.apply(normalizar_chave)
    return serie.astype(str).str.strip()

def normalizar_valor(col, valor):
    if col == "cnpj_cpf":
        return normalizar_doc(valor)
    if col == "chave":
        return normalizar_chave(valor)
    return str(valor).strip()

# =============================
# DATAS — formato brasileiro
# =============================

def formatar_data_br(valor):
    """Converte qualquer formato de data para dd/mm/yyyy string."""
    if not valor or str(valor).strip() in ("", "nan", "None"):
        return ""
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y"]:
        try:
            return datetime.strptime(str(valor).strip(), fmt).strftime("%d/%m/%Y")
        except Exception:
            continue
    return str(valor).strip()

def parse_data(valor):
    """Converte string de data para objeto date. Retorna None se inválido."""
    if not valor or str(valor).strip() in ("", "nan", "None"):
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%y"]:
        try:
            return datetime.strptime(str(valor).strip(), fmt).date()
        except Exception:
            continue
    return None

# =============================
# CONEXÃO
# =============================

@st.cache_resource
def conectar():
    creds_dict = dict(st.secrets["GOOGLE_DRIVE"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def coluna_letra(n):
    resultado = ""
    while n >= 0:
        resultado = chr(n % 26 + ord('A')) + resultado
        n = n // 26 - 1
    return resultado

def abrir_planilha(nome):
    client = conectar()
    return client.open_by_key(SHEET_IDS[nome]).worksheet(ABA_PADRAO)

def normalizar_colunas_df(df):
    df.columns = df.columns.str.strip().str.lower()
    return df

def ajustar_para_schema(df, schema):
    mapa = {col.lower(): col for col in schema}
    df   = normalizar_colunas_df(df)
    df   = df.rename(columns=mapa)
    for col in schema:
        if col not in df.columns:
            df[col] = ""
    return df[schema]

def garantir_cabecalho(nome):
    ws      = abrir_planilha(nome)
    headers = ws.row_values(1)
    if not headers:
        headers = SCHEMAS.get(nome, [])
        if headers:
            ws.insert_row(headers, 1)
    return ws, headers

# =============================
# LEITURA
# =============================

@st.cache_data(ttl=60)
def ler(nome):
    ws, headers = garantir_cabecalho(nome)
    dados = ws.get_all_records()
    if not dados:
        return pd.DataFrame(columns=headers)
    df = pd.DataFrame(dados)
    df = ajustar_para_schema(df, headers)
    return df.astype(str)

# =============================
# INSERIR
# =============================

def _executar_com_retry(func, max_tentativas=5):
    """
    Executa func() com retry e backoff exponencial.
    Trata erros 429 (quota) e 503 (indisponível) do Google Sheets API.
    """
    for tentativa in range(max_tentativas):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            codigo = getattr(e, "response", None)
            codigo = codigo.status_code if codigo else 0
            if codigo in (429, 503) and tentativa < max_tentativas - 1:
                espera = (2 ** tentativa) + 1   # 2, 3, 5, 9 segundos
                time.sleep(espera)
                continue
            raise
        except Exception:
            raise


def inserir(nome, dados: dict):
    ws, headers = garantir_cabecalho(nome)
    linha = [str(dados.get(col, "")) for col in headers]
    _executar_com_retry(lambda: ws.append_row(linha, value_input_option="RAW"))
    limpar_cache()

# =============================
# ATUALIZAR
# =============================

def atualizar(nome, chave_col, chave_valor, dados: dict) -> bool:
    ws, headers = garantir_cabecalho(nome)
    registros   = ws.get_all_records()
    df          = pd.DataFrame(registros).astype(str)

    if df.empty or chave_col not in df.columns:
        return False

    col_norm = normalizar_coluna(chave_col, df[chave_col])
    val_norm = normalizar_valor(chave_col, chave_valor)

    mask = col_norm == val_norm
    if not mask.any():
        return False

    linha      = int(df.index[mask][0]) + 2
    valores    = [str(dados.get(col, "")) for col in headers]
    ultima_col = coluna_letra(len(headers) - 1)
    _executar_com_retry(
        lambda: ws.update(f"A{linha}:{ultima_col}{linha}", [valores], value_input_option="RAW")
    )
    limpar_cache()
    return True

# =============================
# DELETAR
# =============================

def deletar(nome, chave_col, chave_valor) -> bool:
    ws, _     = garantir_cabecalho(nome)
    registros = ws.get_all_records()
    df        = pd.DataFrame(registros).astype(str)

    if df.empty or chave_col not in df.columns:
        return False

    col_norm = normalizar_coluna(chave_col, df[chave_col])
    val_norm = normalizar_valor(chave_col, chave_valor)

    mask = col_norm == val_norm
    if not mask.any():
        return False

    linha = int(df.index[mask][0]) + 2
    _executar_com_retry(lambda: ws.delete_rows(linha))
    limpar_cache()
    return True

# =============================
# ETAPAS
# =============================

def carregar_etapas():
    df = ler("etapas")
    if df.empty:
        return pd.DataFrame(columns=SCHEMAS["etapas"])
    df["ordem_etapa"] = pd.to_numeric(df["ordem_etapa"], errors="coerce").fillna(0).astype(int)
    df["ordem_item"]  = pd.to_numeric(df["ordem_item"],  errors="coerce").fillna(0).astype(int)
    return df.sort_values(["ordem_etapa", "ordem_item"])

def salvar_etapas(df):
    ws, headers = garantir_cabecalho("etapas")
    df = ajustar_para_schema(df, headers).astype(str)
    _executar_com_retry(lambda: ws.clear())
    _executar_com_retry(lambda: ws.append_row(headers))
    if not df.empty:
        linhas = df.values.tolist()
        _executar_com_retry(lambda: ws.append_rows(linhas, value_input_option="RAW"))
    limpar_cache()

# =============================
# CLIENTES
# =============================

def carregar_clientes():
    df = ler("clientes")
    if df.empty:
        return pd.DataFrame(columns=SCHEMAS["clientes"])
    df["cnpj_cpf"] = df["cnpj_cpf"].apply(normalizar_doc)
    df.fillna("", inplace=True)
    return df

# =============================
# IMPLANTAÇÃO
# =============================

def carregar_implantacao():
    df = ler("implantacao")
    df.fillna("", inplace=True)
    df["cnpj_cpf"] = df["cnpj_cpf"].apply(normalizar_doc)
    if "chave" not in df.columns:
        df["chave"] = df["cnpj_cpf"] + "||" + df["etapa"]
    else:
        df["chave"] = df["chave"].apply(normalizar_chave)
    return df

def salvar_implantacao(df):
    ws, headers = garantir_cabecalho("implantacao")
    df = ajustar_para_schema(df, SCHEMAS["implantacao"])
    df["cnpj_cpf"] = df["cnpj_cpf"].apply(normalizar_doc)
    df = df.astype(str)
    ws.clear()
    ws.append_row(SCHEMAS["implantacao"])
    if not df.empty:
        ws.append_rows(
            [[row[col] for col in SCHEMAS["implantacao"]] for _, row in df.iterrows()],
            value_input_option="RAW"
        )
    limpar_cache()

# =============================
# HISTÓRICO
# =============================

def registrar_historico(cnpj_cpf="", cliente="", pagina="", acao="",
                         etapa="", campo="", valor_anterior="", valor_novo=""):
    try:
        inserir("historico", {
            "data_hora":      datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "cnpj_cpf":       str(cnpj_cpf),
            "cliente":        str(cliente),
            "pagina":         str(pagina),
            "acao":           str(acao),
            "etapa":          str(etapa),
            "campo":          str(campo),
            "valor_anterior": str(valor_anterior),
            "valor_novo":     str(valor_novo)
        })
    except Exception:
        pass

def carregar_historico():
    return ler("historico")

# =============================
# CACHE
# =============================

def limpar_cache():
    ler.clear()