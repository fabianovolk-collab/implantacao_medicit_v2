import streamlit as st
import pandas as pd
import os
from database import carregar_clientes, carregar_implantacao, salvar_implantacao
from datetime import datetime

st.set_page_config(layout="wide")
st.title("⚙️ Fases de Implantação")

# -----------------------------
# CONFIG CSV DINÂMICO
# -----------------------------
CAMINHO_CONFIG = "etapas_checklist.csv"

@st.cache_data
def carregar_config():
    if not os.path.exists(CAMINHO_CONFIG):
        st.warning("Arquivo etapas_checklist.csv não encontrado")
        return pd.DataFrame(columns=["etapa", "ordem", "item", "ativo"])
    df = pd.read_csv(CAMINHO_CONFIG)
    df.columns = df.columns.astype(str)
    df.columns = df.columns.str.strip().str.lower()
    df = df.loc[:, ~df.columns.duplicated()]
    for col in ["etapa", "ordem", "item", "ativo"]:
        if col not in df.columns:
            df[col] = None
    df["etapa"] = df["etapa"].apply(lambda x: str(x).strip() if pd.notnull(x) else "")
    df["item"] = df["item"].apply(lambda x: str(x).strip() if pd.notnull(x) else "")
    df["ativo"] = df["ativo"].apply(lambda x: str(x).lower() in ["true", "1", "sim", "yes"])
    df["ordem"] = pd.to_numeric(df["ordem"], errors="coerce").fillna(999).astype(int)
    df = df[df["ativo"] == True]
    df = df[df["etapa"] != ""]
    return df

df_config = carregar_config()

# -----------------------------
# ETAPAS
# -----------------------------
etapas_ordenadas = df_config[["etapa", "ordem"]].drop_duplicates().sort_values("ordem")
ETAPAS = etapas_ordenadas["etapa"].tolist()
if not ETAPAS:
    st.error("Nenhuma etapa ativa encontrada no CSV")
    st.stop()
CHECKLISTS = df_config.groupby("etapa")["item"].apply(lambda x: [i for i in x if i != ""]).to_dict()
STATUS_VALIDOS = ["Não iniciado", "Em andamento", "Bloqueado/Pendente", "Concluido"]

# -----------------------------
# FUNÇÕES
# -----------------------------
def parse_data(valor):
    if not valor:
        return None
    try:
        return pd.to_datetime(valor, dayfirst=True).date()
    except:
        return None

def formatar_data(data):
    if data:
        return data.strftime("%d/%m/%Y")
    return ""

def calcular_progresso(base, marcado):
    if not base:
        return 0
    return int((len(marcado) / len(base)) * 100)

def sanitizar_base(df):
    df["Etapa"] = df["Etapa"].apply(lambda x: x if x in ETAPAS else None)
    df = df.dropna(subset=["Etapa"])
    for col in ["Status", "Motivo", "Responsavel_Cliente", "Participantes", "Responsavel_Etapa"]:
        if col not in df.columns:
            df[col] = "" if col != "Status" else "Não iniciado"
    df["Status"] = df["Status"].replace({"Bloqueado": "Bloqueado/Pendente"})
    df["Status"] = df["Status"].apply(lambda x: x if x in STATUS_VALIDOS else "Não iniciado")
    return df

# -----------------------------
# CARREGAR DADOS
# -----------------------------
clientes_df = carregar_clientes().fillna("")
df = carregar_implantacao().fillna("")
df = sanitizar_base(df)
clientes_df = clientes_df.sort_values("Nome")

# -----------------------------
# BUSCA E SELEÇÃO DE CLIENTE
# -----------------------------
st.subheader("📌 Cliente / Clínica")
col1, col2 = st.columns(2)

with col1:
    doc_busca = st.text_input("🔎 Buscar por CPF/CNPJ")
    clientes_filtrados = clientes_df if not doc_busca else clientes_df[
        clientes_df["CNPJ_CPF"].astype(str).str.contains(doc_busca)
    ]

cliente_sel = None
if doc_busca and len(clientes_filtrados) == 1:
    cliente_sel = clientes_filtrados.iloc[0]["Nome"]
    st.success(f"Cliente encontrado: {cliente_sel}")
else:
    lista_clientes = ["-- Selecione --"] + clientes_filtrados["Nome"].tolist()
    with col2:
        cliente_sel = st.selectbox("Selecione o cliente", lista_clientes)
    if cliente_sel == "-- Selecione --":
        st.warning("Selecione um cliente para continuar")
        st.stop()

doc_sel = clientes_df[clientes_df["Nome"] == cliente_sel]["CNPJ_CPF"].values[0]

# Inicializar estado para controlar importação
if "importado_cliente" not in st.session_state:
    st.session_state["importado_cliente"] = None

# =============================
# IMPORTAÇÃO DO EXCEL
# =============================
st.markdown("### 📥 Importar planilha do cliente")
disable_upload = st.session_state["importado_cliente"] == doc_sel
if disable_upload:
    st.info("✅ Planilha já importada para este cliente. Para outro cliente ou reiniciar a sessão, a importação será habilitada novamente.")

arquivo_importado = st.file_uploader(
    "Selecione o Excel preenchido pelo cliente",
    type=["xlsx"],
    disabled=disable_upload
)

if arquivo_importado and not disable_upload:
    try:
        df_excel = pd.read_excel(arquivo_importado, dtype=str)
        df_excel.fillna("", inplace=True)
        colunas_esperadas = [
            "CNPJ_CPF","Cliente","Etapa","Checklist",
            "Responsavel_Medicit", "Responsavel_Clinica",
            "Participantes","Data_Prevista"
        ]
        if not all(col in df_excel.columns for col in colunas_esperadas):
            st.error("❌ Estrutura inválida.")
            st.stop()
        if str(df_excel["CNPJ_CPF"].iloc[0]) != str(doc_sel):
            st.error("❌ Cliente do arquivo diferente do selecionado.")
            st.stop()

        atualizados = 0
        for _, row in df_excel.iterrows():
            mask = (df["CNPJ_CPF"] == row["CNPJ_CPF"]) & (df["Etapa"] == row["Etapa"])
            if mask.any():
                df.loc[mask, "Responsavel_Etapa"] = row["Responsavel_Medicit"]
                df.loc[mask, "Responsavel_Cliente"] = row["Responsavel_Clinica"]
                df.loc[mask, "Participantes"] = row["Participantes"]
                df.loc[mask, "Ultima_Atualizacao"] = datetime.now()
                atualizados += 1
        salvar_implantacao(df)
        st.session_state["importado_cliente"] = doc_sel
        st.success(f"Importação concluída! {atualizados} etapas atualizadas.")
        st.info("⚠️ Agora você pode alterar os dados manualmente abaixo.")
    except Exception as e:
        st.error(f"Erro ao importar: {e}")

# -----------------------------
# GARANTIR ETAPAS
# -----------------------------
def garantir_etapas(df, cliente, doc):
    df_cliente = df[df["Cliente"] == cliente]
    existentes = df_cliente["Etapa"].tolist()
    novas = []
    for etapa in ETAPAS:
        if etapa not in existentes:
            novas.append({
                "CNPJ_CPF": doc,
                "Cliente": cliente,
                "Etapa": etapa,
                "Status": "Não iniciado",
                "Data_Inicio": "",
                "Data_Conclusao": "",
                "Responsavel_Etapa": "",
                "Responsavel_Cliente": "",
                "Participantes": "",
                "Motivo": "",
                "Proxima_Acao": "",
                "Checklist": "",
                "Ultima_Atualizacao": datetime.now()
            })
    if novas:
        df = pd.concat([df, pd.DataFrame(novas)], ignore_index=True)
        salvar_implantacao(df)
    return df

df = garantir_etapas(df, cliente_sel, doc_sel)

# -----------------------------
# SELEÇÃO DE ETAPA
# -----------------------------
etapa_sel = st.selectbox("Selecione a Etapa", ETAPAS)
dados = df[(df["Cliente"] == cliente_sel) & (df["Etapa"] == etapa_sel)].iloc[0]

# -----------------------------
# PROGRESSO
# -----------------------------
base = CHECKLISTS.get(etapa_sel, [])
salvo = dados["Checklist"].split("|") if dados["Checklist"] else []
progresso = calcular_progresso(base, salvo)
st.progress(progresso)
st.write(f"Progresso: **{progresso}%**")

# -----------------------------
# FORMULÁRIO DE EDIÇÃO
# -----------------------------
col1, col2 = st.columns(2)
status_atual = dados["Status"] if dados["Status"] in STATUS_VALIDOS else "Não iniciado"
status = col1.selectbox("Status", STATUS_VALIDOS, index=STATUS_VALIDOS.index(status_atual))
responsavel = col2.text_input("Responsável Interno (Medicit)", value=dados["Responsavel_Etapa"])

col3, col4 = st.columns(2)
responsavel_cliente = col3.text_input("Responsável Cliente", value=dados["Responsavel_Cliente"])
participantes = col4.text_input("Participantes (Separar com ;) ", value=dados["Participantes"])

col5, col6 = st.columns(2)
data_inicio = col5.date_input("Data Inicio", value=parse_data(dados["Data_Inicio"]), format="DD/MM/YYYY")
data_conclusao = col6.date_input("Data Conclusão", value=parse_data(dados["Data_Conclusao"]), format="DD/MM/YYYY")

motivo = st.text_input("Motivo (Bloqueio/Pendência)", value=dados.get("Motivo", ""))
proxima_acao = st.text_input("Próxima Ação", value=dados["Proxima_Acao"])

# -----------------------------
# CHECKLIST
# -----------------------------
st.markdown("### ✅ Checklist")
marcados = []
for i, item in enumerate(base):
    key = f"{cliente_sel}_{etapa_sel}_{i}"
    if st.checkbox(item, value=item in salvo, key=key):
        marcados.append(item)

# -----------------------------
# SALVAR ALTERAÇÕES
# -----------------------------
if st.button("💾 Salvar"):
    idx = df[(df["Cliente"] == cliente_sel) & (df["Etapa"] == etapa_sel)].index[0]

    if status == "Bloqueado/Pendente" and motivo.strip() == "":
        st.warning("Informe o motivo do bloqueio/pendência")
        st.stop()

    if status != "Bloqueado/Pendente":
        motivo = ""

    if len(marcados) == len(base) and base:
        status = "Concluido"
        data_conclusao = datetime.now().date()

    df.at[idx, "Status"] = status
    df.at[idx, "Motivo"] = motivo
    df.at[idx, "Proxima_Acao"] = proxima_acao
    df.at[idx, "Responsavel_Etapa"] = responsavel
    df.at[idx, "Responsavel_Cliente"] = responsavel_cliente
    df.at[idx, "Participantes"] = participantes
    df.at[idx, "Checklist"] = "|".join(marcados)
    df.at[idx, "Ultima_Atualizacao"] = datetime.now()
    df.at[idx, "Data_Inicio"] = formatar_data(data_inicio)
    df.at[idx, "Data_Conclusao"] = formatar_data(data_conclusao)
    salvar_implantacao(df)
    st.success("Atualizado com sucesso")

# -----------------------------
# TABELA FINAL
# -----------------------------
st.subheader("📋 Etapas do Cliente")
df_cliente = df[df["Cliente"] == cliente_sel].copy()
st.dataframe(df_cliente, use_container_width=True)