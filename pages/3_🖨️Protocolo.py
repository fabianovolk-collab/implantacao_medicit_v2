import streamlit as st
import pandas as pd
from database import carregar_clientes, carregar_implantacao
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
import base64

st.set_page_config(layout="wide")
st.title("📄 Protocolo de Implantação")

# -----------------------------
# FUNÇÃO PARA CARREGAR CHECKLIST DINÂMICO
# -----------------------------
@st.cache_data
def carregar_checklist():
    # Arquivo na raiz do projeto
    df = pd.read_csv("etapas_checklist.csv")
    
    # Garantir colunas corretas
    for col in ["Etapa", "Item"]:
        if col not in df.columns:
            df[col] = ""
    
    # Remover itens em branco
    df = df[df["Item"].notna() & (df["Item"].str.strip() != "")]
    
    # Criar dicionário {Etapa: [Itens]}
    checklist_dict = {}
    for etapa, grupo in df.groupby("Etapa"):
        checklist_dict[etapa] = grupo.sort_values("Ordem_item")["Item"].tolist()
    return checklist_dict

# -----------------------------
# FUNÇÕES AUXILIARES
# -----------------------------
def status_icon(status):
    if status == "Concluido":
        return "OK"
    elif status == "Em andamento":
        return "EM ANDAMENTO"
    elif status == "Bloqueado/Pendente":
        return "BLOQUEADO"
    else:
        return "-"

def limpar_texto(texto):
    if not texto:
        return ""
    return str(texto).encode("latin-1", "ignore").decode("latin-1")

# -----------------------------
# FUNÇÃO PARA FORMATAR CPF/CNPJ
# -----------------------------
def formatar_cpf_cnpj(numero):
    numero = ''.join(filter(str.isdigit, str(numero)))  # remove tudo que não é número
    if len(numero) == 11:  # CPF
        return f"{numero[:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:]}"
    elif len(numero) == 14:  # CNPJ
        return f"{numero[:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:]}"
    else:
        return str(numero)  # caso não seja nem CPF nem CNPJ

def calcular_progresso(df_cliente, checklist_dict):
    total_itens = 0
    itens_concluidos = 0

    for _, row in df_cliente.iterrows():
        base = checklist_dict.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []
        total_itens += len(base)
        itens_concluidos += len([item for item in base if item in salvo])

    if total_itens == 0:
        return 0
    return int((itens_concluidos / total_itens) * 100)

def garantir_colunas(df):
    colunas = [
        "Cliente", "Etapa", "Status", "Motivo",
        "Responsavel_Etapa", "Responsavel_Cliente",
        "Participantes",
        "Data_Inicio", "Data_Conclusao", "Checklist"
    ]
    for col in colunas:
        if col not in df.columns:
            df[col] = ""
    return df

# -----------------------------
# CARREGAR DADOS
# -----------------------------
clientes_df = carregar_clientes().fillna("")
df = carregar_implantacao().fillna("")
df = garantir_colunas(df)
clientes_df = clientes_df.sort_values("Nome")

# Ajuste de etapas duplicadas
df["Etapa"] = df["Etapa"].replace({
    "Acompanhamento Inicial": "Acompanhamento",
    "Acompanhamento Final": "Acompanhamento"
})

# -----------------------------
# BUSCA E SELEÇÃO DE CLIENTE
# -----------------------------
st.subheader("📌 Cliente / Clínica")
col1, col2 = st.columns(2)

with col1:
    doc_busca = st.text_input("🔎 Buscar por CPF/CNPJ")
    if doc_busca:
        clientes_filtrados = clientes_df[
            clientes_df["CNPJ_CPF"].astype(str).str.contains(doc_busca)
        ]
    else:
        clientes_filtrados = clientes_df

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
df_cliente = df[df["Cliente"] == cliente_sel].copy()

# -----------------------------
# CARREGAR CHECKLIST
# -----------------------------
CHECKLISTS = carregar_checklist()

# -----------------------------
# PROGRESSO
# -----------------------------
progresso = calcular_progresso(df_cliente, CHECKLISTS)
st.progress(progresso)
st.write(f"Progresso Geral: **{progresso}%**")

# -----------------------------
# VISUALIZAÇÃO
# -----------------------------
col1, col2 = st.columns(2)
for i, (_, row) in enumerate(df_cliente.iterrows()):
    container = col1 if i % 2 == 0 else col2
    with container:
        st.markdown(f"""
        ### {status_icon(row['Status'])} {row['Etapa']}

        **Status:** {row['Status']}  
        **Responsável Medicit:** {row['Responsavel_Etapa']}  
        **Responsável Cliente:** {row['Responsavel_Cliente']}  
        **Participantes:** {row['Participantes']}  
        **Início:** {row['Data_Inicio']}  
        **Conclusão:** {row['Data_Conclusao']}  
        """)
        if row["Status"] == "Bloqueado/Pendente":
            st.error(f"🚨 Motivo: {row['Motivo']}")

        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []
        if base:
            st.markdown("**Checklist:**")
            for item in base:
                if item in salvo:
                    st.write(f"✔ {item}")
                else:
                    st.write(f"⬜ {item}")

# -----------------------------
# PDF
# -----------------------------
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Protocolo Implantacao", 0, 1, "C")
        self.ln(10)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, "C")

    def barra(self, percentual):
        self.set_fill_color(255, 255, 255)
        self.cell(0, 6, "", 1, 1)
        if percentual <= 0:
            self.ln(2)
            return
        largura = (percentual / 100) * 190
        if percentual == 100:
            cor = (0, 176, 80)
        elif percentual > 50:
            cor = (0, 102, 204)
        else:
            cor = (255, 192, 0)
        self.set_fill_color(*cor)
        self.set_xy(10, self.get_y() - 6)
        self.cell(largura, 6, "", 0, 1, "L", True)
        self.ln(2)

def progresso_etapa(row):
    base = CHECKLISTS.get(row["Etapa"], [])
    salvo = row["Checklist"].split("|") if row["Checklist"] else []
    if len(base) == 0:
        return 0
    feitos = len([item for item in base if item in salvo])
    return int((feitos / len(base)) * 100)

def gerar_pdf(df_cliente, cliente, progresso, doc_sel):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 11)
    data_inicio_implantacao = df_cliente["Data_Inicio"].replace("", None).dropna().min()
    pdf.cell(0, 6, f"Cliente: {limpar_texto(cliente)}", 0, 1)
    pdf.cell(0, 6, f"CPF/CNPJ: {formatar_cpf_cnpj(doc_sel)}", 0, 1)
    pdf.cell(0, 6, f"Data Inicio Implantacao: {limpar_texto(data_inicio_implantacao)}", 0, 1)
    pdf.ln(3)
    pdf.cell(0, 5, f"Progresso Geral: {progresso}%", 0, 1)
    pdf.barra(progresso)
    pdf.ln(3)

    for _, row in df_cliente.iterrows():
        prog = progresso_etapa(row)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Etapa: {limpar_texto(row['Etapa'])}", 0, 1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, f"Status: {limpar_texto(row['Status'])}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Medicit: {limpar_texto(row['Responsavel_Etapa'])}", 0, 1)
        pdf.cell(0, 5, f"Responsavel Cliente: {limpar_texto(row['Responsavel_Cliente'])}", 0, 1)
        pdf.cell(0, 5, f"Participantes: {limpar_texto(row['Participantes'])}", 0, 1)
        pdf.cell(0, 5, f"Data Inicio Etapa: {limpar_texto(row['Data_Inicio'])}", 0, 1)

        if row["Status"] == "Bloqueado/Pendente":
            pdf.set_text_color(200, 0, 0)
            pdf.multi_cell(0, 5, f"Motivo Bloqueio/Pendencia: {limpar_texto(row['Motivo'])}")
            pdf.set_text_color(0, 0, 0)

        base = CHECKLISTS.get(row["Etapa"], [])
        salvo = row["Checklist"].split("|") if row["Checklist"] else []

        pdf.cell(0, 5, "Checklist:", 0, 1)
        for item in base:
            if item in salvo:
                pdf.cell(0, 5, f"[X] {limpar_texto(item)}", 0, 1)
            else:
                pdf.cell(0, 5, f"[ ] {limpar_texto(item)}", 0, 1)
        pdf.ln(2)

        status_texto = (
            "Não iniciado" if prog == 0 else
            "Em risco" if prog <= 50 else
            "Em andamento" if prog < 100 else
            "Concluído"
        )
        pdf.cell(0, 5, f"Progresso Etapa: {prog}% - {status_texto}", 0, 1)
        pdf.barra(prog)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# -----------------------------
# BOTÃO GERAR PDF
# -----------------------------
st.markdown("---")
if st.button("📄 Gerar Protocolo Executivo"):
    pdf_path = gerar_pdf(df_cliente, cliente_sel, progresso, doc_sel)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'''
    <html>
        <body>
            <a id="download_link" href="data:application/pdf;base64,{b64}" download="protocolo_{cliente_sel}.pdf"></a>
            <script>
                document.getElementById('download_link').click();
            </script>
        </body>
    </html>
    '''
    st.components.v1.html(href, height=0)
    st.success("📄 Protocolo gerado com sucesso!")