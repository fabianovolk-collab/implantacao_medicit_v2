import os
import streamlit as st
import pandas as pd
from database import carregar_clientes, carregar_implantacao, carregar_etapas, CHECKLIST_SEP
from utils import formatar_cnpj_cpf
from datetime import datetime
from fpdf import FPDF
import tempfile
import base64

st.set_page_config(layout="wide")
st.title("📄 Protocolo de Implantação")

# Logo na raiz do projeto (onde o Streamlit é executado)
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "..", "logo.png")

# ==============================
# CHECKLIST DINÂMICO (vem do banco, fonte única)
# ==============================

@st.cache_data(ttl=300)
def carregar_checklist():
    df = carregar_etapas()
    if df.empty:
        return {}
    checklist = {}
    for etapa, grupo in df.groupby("etapa"):
        itens = grupo.sort_values("ordem_item")["item"].tolist()
        checklist[etapa] = [i for i in itens if str(i).strip()]
    return checklist

CHECKLISTS = carregar_checklist()

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def status_icon(status):
    mapa = {
        "Concluído":         "✔",
        "Em andamento":      "⏳",
        "Bloqueio/Pendente": "🚨",
        "Não iniciado":      "-"
    }
    return mapa.get(status, "-")

def limpar_texto(texto):
    if not texto:
        return ""
    return str(texto).encode("latin-1", "ignore").decode("latin-1")

def formatar_data(data):
    if pd.isna(data) or data in ["", None]:
        return ""
    if isinstance(data, str):
        try:
            data = pd.to_datetime(data, dayfirst=True)
        except Exception:
            return str(data)
    return data.strftime("%d/%m/%Y")

def calcular_progresso(df_cliente):
    total = 0
    concluidos = 0
    for _, row in df_cliente.iterrows():
        base  = CHECKLISTS.get(row.get("Etapa", row.get("etapa", "")), [])
        salvo = [i for i in row.get("Checklist", row.get("checklist", "")).split(CHECKLIST_SEP) if i]
        total      += len(base)
        concluidos += len([i for i in base if i in salvo])
    return int(concluidos / total * 100) if total else 0

def garantir_colunas(df):
    mapa = {c.lower(): c for c in df.columns}
    renomear = {}
    colunas_esperadas = {
        "cliente": "Cliente", "etapa": "Etapa", "status": "Status",
        "motivo": "Motivo", "responsavel_medicit": "Responsavel_Etapa",
        "responsavel_cliente": "Responsavel_Cliente",
        "participantes": "Participantes",
        "data_inicio": "Data_Inicio", "data_conclusao": "Data_Conclusao",
        "checklist": "Checklist", "cnpj_cpf": "cnpj_cpf"
    }
    for lower, padrao in colunas_esperadas.items():
        if lower in mapa:
            renomear[mapa[lower]] = padrao
    df = df.rename(columns=renomear)
    for col in colunas_esperadas.values():
        if col not in df.columns:
            df[col] = ""
    return df

# ==============================
# CARREGAR DADOS
# ==============================

clientes_df = carregar_clientes().fillna("")
df_impl     = carregar_implantacao().fillna("")

# Padronizar colunas
df_impl = garantir_colunas(df_impl)

clientes_df = clientes_df.sort_values("Nome") if "Nome" in clientes_df.columns else clientes_df

# ==============================
# SELEÇÃO DE CLIENTE
# ==============================

st.subheader("📌 Selecionar Cliente")
col1, col2 = st.columns(2)

with col1:
    doc_busca = st.text_input("🔎 Buscar por CPF/CNPJ ou Nome")

if doc_busca:
    clientes_filtrados = clientes_df[
        clientes_df["cnpj_cpf"].astype(str).str.contains(doc_busca) |
        clientes_df["Nome"].str.lower().str.contains(doc_busca.lower())
    ]
else:
    clientes_filtrados = clientes_df.copy()

if clientes_filtrados.empty:
    st.warning("Nenhum cliente encontrado.")
    st.stop()

lista_clientes = ["-- Selecione --"] + clientes_filtrados["Nome"].tolist()
with col2:
    cliente_sel = st.selectbox("Selecione o cliente", lista_clientes)

if cliente_sel == "-- Selecione --":
    st.warning("Selecione um cliente para continuar.")
    st.stop()

# Busca o cnpj_cpf do cliente selecionado
linha_cliente = clientes_filtrados[clientes_filtrados["Nome"] == cliente_sel]
if linha_cliente.empty:
    st.error("Cliente não encontrado na base.")
    st.stop()

doc_sel = linha_cliente.iloc[0]["cnpj_cpf"]

# Filtra implantação pelo cnpj_cpf (fonte primária, mais confiável que nome)
df_cliente = df_impl[df_impl["cnpj_cpf"] == doc_sel].copy()

if df_cliente.empty:
    st.info("Nenhuma implantação encontrada para este cliente.")
    st.stop()

# ==============================
# PROGRESSO GERAL
# ==============================

progresso = calcular_progresso(df_cliente)
st.progress(progresso / 100)
st.write(f"**Progresso Geral: {progresso}%**")

# ==============================
# VISUALIZAÇÃO POR ETAPA
# ==============================

col1, col2 = st.columns(2)
for i, (_, row) in enumerate(df_cliente.iterrows()):
    container = col1 if i % 2 == 0 else col2
    etapa_nome = row.get("Etapa", "")
    status_val = row.get("Status", "")

    with container:
        st.markdown(f"""
        ### {status_icon(status_val)} {etapa_nome}
        **Status:** {status_val}
        **Responsável Medicit:** {row.get('Responsavel_Etapa', '')}
        **Responsável Cliente:** {row.get('Responsavel_Cliente', '')}
        **Participantes:** {row.get('Participantes', '')}
        **Início:** {formatar_data(row.get('Data_Inicio', ''))}
        **Conclusão:** {formatar_data(row.get('Data_Conclusao', ''))}
        """)

        if status_val == "Bloqueio/Pendente":
            st.error(f"🚨 Motivo: {row.get('Motivo', '')}")

        base  = CHECKLISTS.get(etapa_nome, [])
        salvo = [i for i in row.get("Checklist", "").split(CHECKLIST_SEP) if i]

        if base:
            st.markdown("**Checklist:**")
            for item in base:
                st.write(f"{'✔' if item in salvo else '⬜'} {item}")

# ==============================
# GERAÇÃO DE PDF
# ==============================

class PDF(FPDF):
    def __init__(self, logo_path=""):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        if self.logo_path and os.path.exists(self.logo_path):
            self.image(self.logo_path, 10, 8, 30)
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Protocolo de Implantacao", 0, 1, "C")
        self.ln(10)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, "C")

    def barra_progresso(self, percentual):
        self.set_fill_color(230, 230, 230)
        self.rect(10, self.get_y(), 190, 6, "F")
        if percentual > 0:
            largura = min((percentual / 100) * 190, 190)
            if percentual == 100:
                self.set_fill_color(0, 176, 80)
            elif percentual >= 50:
                self.set_fill_color(0, 102, 204)
            else:
                self.set_fill_color(255, 192, 0)
            self.rect(10, self.get_y(), largura, 6, "F")
        self.ln(8)

def progresso_etapa(row):
    etapa_nome = row.get("Etapa", "")
    base  = CHECKLISTS.get(etapa_nome, [])
    salvo = [i for i in row.get("Checklist", "").split(CHECKLIST_SEP) if i]
    return int(len([i for i in base if i in salvo]) / len(base) * 100) if base else 0

def gerar_pdf(df_cliente, cliente, progresso, doc_sel):
    pdf = PDF(logo_path=LOGO_PATH)
    pdf.add_page()
    pdf.set_font("Arial", "", 11)

    data_inicio_impl = (
        df_cliente["Data_Inicio"].replace("", None).dropna().min()
        if "Data_Inicio" in df_cliente.columns else ""
    )

    pdf.cell(0, 6, f"Cliente: {limpar_texto(cliente)}", 0, 1)
    pdf.cell(0, 6, f"CPF/CNPJ: {formatar_cnpj_cpf(doc_sel)}", 0, 1)
    pdf.cell(0, 6, f"Inicio da Implantacao: {formatar_data(data_inicio_impl)}", 0, 1)
    pdf.ln(3)
    pdf.cell(0, 5, f"Progresso Geral: {progresso}%", 0, 1)
    pdf.barra_progresso(progresso)
    pdf.ln(3)

    for _, row in df_cliente.iterrows():
        prog = progresso_etapa(row)
        etapa_nome = row.get("Etapa", "")

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Etapa: {limpar_texto(etapa_nome)}", 0, 1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Status: {limpar_texto(row.get('Status',''))}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Medicit: {limpar_texto(row.get('Responsavel_Etapa',''))}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Cliente: {limpar_texto(row.get('Responsavel_Cliente',''))}", 0, 1)
        pdf.cell(0, 5, f"Participantes: {limpar_texto(row.get('Participantes',''))}", 0, 1)
        pdf.cell(0, 5, f"Data Inicio: {formatar_data(row.get('Data_Inicio',''))}", 0, 1)
        pdf.cell(0, 5, f"Data Conclusao: {formatar_data(row.get('Data_Conclusao',''))}", 0, 1)

        if row.get("Status") == "Bloqueio/Pendente":
            pdf.set_text_color(200, 0, 0)
            pdf.multi_cell(0, 5, f"Motivo: {limpar_texto(row.get('Motivo',''))}")
            pdf.set_text_color(0, 0, 0)

        base  = CHECKLISTS.get(etapa_nome, [])
        salvo = [i for i in row.get("Checklist", "").split(CHECKLIST_SEP) if i]

        if base:
            pdf.cell(0, 5, "Checklist:", 0, 1)
            for item in base:
                pdf.cell(0, 5, f"[{'X' if item in salvo else ' '}] {limpar_texto(item)}", 0, 1)

        status_texto = (
            "Nao iniciado" if prog == 0 else
            "Em risco"     if prog <= 50 else
            "Em andamento" if prog < 100 else
            "Concluido"
        )
        pdf.ln(2)
        pdf.cell(0, 5, f"Progresso Etapa: {prog}% - {status_texto}", 0, 1)
        pdf.barra_progresso(prog)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# ==============================
# BOTÃO GERAR PDF
# ==============================

st.markdown("---")
if st.button("📄 Gerar Protocolo Executivo"):
    pdf_path = gerar_pdf(df_cliente, cliente_sel, progresso, doc_sel)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64  = base64.b64encode(pdf_bytes).decode()
    href = f'''<a id="dl" href="data:application/pdf;base64,{b64}"
        download="protocolo_{cliente_sel}.pdf"></a>
        <script>document.getElementById('dl').click();</script>'''
    st.components.v1.html(href, height=0)
    st.success("✅ Protocolo gerado com sucesso!")
