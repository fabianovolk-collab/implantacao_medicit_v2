import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import (
    carregar_clientes, carregar_implantacao,
    normalizar_doc, PRIORIDADES
)

st.set_page_config(layout="wide")
st.title("📊 Controle Geral de Implantações")

# ==============================
# FUNÇÕES DE CÁLCULO
# ==============================

def parse_data(valor):
    if not valor or str(valor).strip() in ("", "nan", "None"):
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(str(valor).strip(), fmt).date()
        except Exception:
            continue
    return None

# Status considera variações de capitalização e acentuação
STATUS_CONCLUIDO = {"concluído", "concluida", "concluída", "concluido"}
STATUS_BLOQUEIO  = {"bloqueio/pendente", "bloqueado/pendente", "bloqueado"}
STATUS_ANDAMENTO = {"em andamento"}
STATUS_AGUARD    = {"aguardando dados"}

def normalizar_status(s):
    return str(s).strip().lower()

def calcular_status_geral(cnpj, df_impl):
    etapas = df_impl[df_impl["cnpj_cpf"] == cnpj]
    if etapas.empty:
        return "Não Iniciado"

    statuses = [normalizar_status(s) for s in etapas["status"].tolist()]

    if all(s in STATUS_CONCLUIDO for s in statuses):
        return "Concluída"
    if any(s in STATUS_BLOQUEIO for s in statuses):
        return "Bloqueio/Pendente"
    if any(s in STATUS_AGUARD for s in statuses):
        return "Aguardando Dados"
    if any(s in STATUS_ANDAMENTO for s in statuses):
        return "Em Andamento"
    if any(s in STATUS_CONCLUIDO for s in statuses):
        return "Em Andamento"   # algumas concluídas, outras não
    return "Não Iniciado"

def calcular_progresso_pct(cnpj, df_impl):
    etapas = df_impl[df_impl["cnpj_cpf"] == cnpj]
    if etapas.empty:
        return 0
    total     = len(etapas)
    concluidas = sum(1 for s in etapas["status"] if normalizar_status(s) in STATUS_CONCLUIDO)
    return int(concluidas / total * 100)

def calcular_data_conclusao_real(cnpj, df_impl):
    etapas = df_impl[df_impl["cnpj_cpf"] == cnpj]
    if etapas.empty:
        return None
    if not all(normalizar_status(s) in STATUS_CONCLUIDO for s in etapas["status"]):
        return None
    datas = etapas["data_conclusao"].apply(parse_data).dropna()
    return max(datas) if not datas.empty else None

def dias_decorridos(data_inicio):
    dt = parse_data(data_inicio)
    return (date.today() - dt).days if dt else None

def fora_prazo(data_inicio, prazo_dias, status):
    if normalizar_status(status) in STATUS_CONCLUIDO:
        return False
    di = parse_data(data_inicio)
    if not di or not prazo_dias:
        return False
    try:
        return (date.today() - di).days > int(prazo_dias)
    except Exception:
        return False

# ==============================
# CARREGAR E CRUZAR DADOS
# ==============================

df_clientes = carregar_clientes().fillna("")
df_impl     = carregar_implantacao().fillna("")

df_clientes["cnpj_cpf"] = df_clientes["cnpj_cpf"].apply(normalizar_doc)
df_impl["cnpj_cpf"]     = df_impl["cnpj_cpf"].apply(normalizar_doc)
df_impl["etapa"]        = df_impl["etapa"].astype(str).str.strip()

linhas = []
for _, cli in df_clientes.iterrows():
    doc = cli["cnpj_cpf"]

    status      = calcular_status_geral(doc, df_impl)
    pct         = calcular_progresso_pct(doc, df_impl)
    data_inicio = cli.get("data_prevista_inicio", "") or cli.get("data_inicio_implantacao", "")
    prazo_dias  = cli.get("prazo_implantacao_dias", "")
    dias_dec    = dias_decorridos(data_inicio)
    fora        = fora_prazo(data_inicio, prazo_dias, status)
    data_concl  = calcular_data_conclusao_real(doc, df_impl)

    # Etapas deste cliente para resumo
    etapas_cli  = df_impl[df_impl["cnpj_cpf"] == doc]
    n_etapas    = len(etapas_cli)
    n_concl     = sum(1 for s in etapas_cli["status"] if normalizar_status(s) in STATUS_CONCLUIDO)
    n_bloq      = sum(1 for s in etapas_cli["status"] if normalizar_status(s) in STATUS_BLOQUEIO)

    linhas.append({
        "cnpj_cpf":          doc,
        "Cliente":           cli.get("Nome", ""),
        "Telefone":          cli.get("Telefone", ""),
        "Resp. Comercial":   cli.get("Responsavel_Comercial", ""),
        "Resp. Medicit":     cli.get("Responsavel_Medicit", ""),
        "Data Contrato":     cli.get("data_ass_contrato", ""),
        "Pacote":            cli.get("pacote", ""),
        "Adicional":         cli.get("adicional_pacote", ""),
        "Agendas":           cli.get("qtde_agendas", ""),
        "Prazo (dias)":      prazo_dias,
        "Data Prev. Início": data_inicio,
        "Status":            status,
        "Prioridade":        cli.get("prioridade", ""),
        "Progresso (%)":     pct,
        "Total Etapas":      n_etapas,
        "Concluídas":        n_concl,
        "Bloqueadas":        n_bloq,
        "Dias Decorridos":   dias_dec if dias_dec is not None else "",
        "Fora Prazo":        "Sim" if fora else "Não",
        "Data Conclusão":    data_concl.strftime("%d/%m/%Y") if data_concl else "",
        "Observação":        cli.get("observacao", "")
    })

df_geral = pd.DataFrame(linhas)

if df_geral.empty:
    st.info("Nenhum cliente cadastrado ainda.")
    st.stop()

# ==============================
# MÉTRICAS RÁPIDAS
# ==============================

total      = len(df_geral)
concluidas = (df_geral["Status"] == "Concluída").sum()
andamento  = (df_geral["Status"] == "Em Andamento").sum()
bloqueios  = (df_geral["Status"] == "Bloqueio/Pendente").sum()
nao_inic   = (df_geral["Status"] == "Não Iniciado").sum()
fora_p     = (df_geral["Fora Prazo"] == "Sim").sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("👥 Total",           total)
c2.metric("🆕 Não Iniciado",    nao_inic)
c3.metric("⏳ Em Andamento",    andamento)
c4.metric("✅ Concluídas",      concluidas)
c5.metric("🚨 Com Bloqueio",    bloqueios)
c6.metric("⏰ Fora do Prazo",   fora_p)

st.divider()

# ==============================
# FILTROS
# ==============================

st.markdown("### 🔎 Filtros")
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    busca = st.text_input("Buscar (nome ou CPF/CNPJ)")
with fc2:
    status_opts   = ["Todos"] + sorted(df_geral["Status"].unique().tolist())
    filtro_status = st.selectbox("Status", status_opts)
with fc3:
    prior_opts   = ["Todas"] + PRIORIDADES
    filtro_prior = st.selectbox("Prioridade", prior_opts)
with fc4:
    filtro_fora = st.selectbox("Fora do Prazo", ["Todos", "Sim", "Não"])

df_view = df_geral.copy()
if busca:
    busca_doc = normalizar_doc(busca)
    df_view = df_view[
        df_view["Cliente"].str.lower().str.contains(busca.lower(), na=False) |
        df_view["cnpj_cpf"].str.contains(busca_doc, na=False)
    ]
if filtro_status != "Todos":
    df_view = df_view[df_view["Status"] == filtro_status]
if filtro_prior != "Todas":
    df_view = df_view[df_view["Prioridade"] == filtro_prior]
if filtro_fora != "Todos":
    df_view = df_view[df_view["Fora Prazo"] == filtro_fora]

# Ordena: prioridade → progresso crescente (menos avançados primeiro)
ordem_prior = {"Alta": 0, "Média": 1, "Baixa": 2, "": 3}
df_view = df_view.copy()
df_view["_ord"] = df_view["Prioridade"].map(lambda x: ordem_prior.get(x, 3))
df_view = df_view.sort_values(["_ord", "Progresso (%)"], ascending=[True, True])

st.caption(f"{len(df_view)} cliente(s) encontrado(s)")
st.divider()

# ==============================
# CARDS POR CLIENTE
# ==============================

COR_STATUS = {
    "Concluída":         "#28a745",
    "Em Andamento":      "#007bff",
    "Bloqueio/Pendente": "#dc3545",
    "Não Iniciado":      "#6c757d",
    "Aguardando Dados":  "#fd7e14"
}
COR_PRIOR = {"Alta": "#dc3545", "Média": "#fd7e14", "Baixa": "#28a745"}

for _, row in df_view.iterrows():
    cor_s = COR_STATUS.get(row["Status"], "#6c757d")
    cor_p = COR_PRIOR.get(row["Prioridade"], "#adb5bd")
    pct   = row["Progresso (%)"]

    with st.container():
        col_nome, col_info, col_status = st.columns([3, 5, 2])

        with col_nome:
            st.markdown(f"**{row['Cliente']}**")
            st.caption(row["cnpj_cpf"])
            if row["Telefone"]:
                st.caption(f"📞 {row['Telefone']}")

            # Barra de progresso de etapas
            cor_bar = "#28a745" if pct == 100 else "#007bff" if pct >= 50 else "#ffc107"
            st.markdown(
                f"<div style='background:#e9ecef;border-radius:6px;height:14px;margin-top:4px'>"
                f"<div style='width:{pct}%;background:{cor_bar};height:14px;border-radius:6px'></div>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.caption(
                f"Etapas: {row['Concluídas']}/{row['Total Etapas']} concluídas ({pct}%)"
                + (f" · 🚨 {row['Bloqueadas']} bloq." if row["Bloqueadas"] > 0 else "")
            )

        with col_info:
            pacote_str = row["Pacote"]
            if row["Adicional"]:
                pacote_str += f" + {row['Adicional']}"
            st.markdown(
                f"📦 **{pacote_str}** &nbsp;|&nbsp; "
                f"🗓️ Agendas: **{row['Agendas']}** &nbsp;|&nbsp; "
                f"⏱️ Prazo: **{row['Prazo (dias)']} dias**",
                unsafe_allow_html=True
            )
            resp_str = "  |  ".join(filter(None, [
                f"Comercial: {row['Resp. Comercial']}" if row["Resp. Comercial"] else "",
                f"Medicit: {row['Resp. Medicit']}"     if row["Resp. Medicit"]    else ""
            ]))
            if resp_str:
                st.caption(resp_str)

            datas = "  ".join(filter(None, [
                f"Contrato: {row['Data Contrato']}"         if row["Data Contrato"]     else "",
                f"Prev. Início: {row['Data Prev. Início']}" if row["Data Prev. Início"] else "",
                f"Conclusão: {row['Data Conclusão']}"       if row["Data Conclusão"]    else ""
            ]))
            if datas:
                st.caption(datas)

            if row["Observação"]:
                st.caption(f"💬 {row['Observação']}")

        with col_status:
            st.markdown(
                f"<div style='background:{cor_s};color:white;border-radius:6px;"
                f"padding:4px 10px;text-align:center;font-size:13px;font-weight:600'>"
                f"{row['Status']}</div>",
                unsafe_allow_html=True
            )
            if row["Prioridade"]:
                st.markdown(
                    f"<div style='background:{cor_p};color:white;border-radius:6px;"
                    f"padding:2px 10px;text-align:center;font-size:12px;margin-top:4px'>"
                    f"🎯 {row['Prioridade']}</div>",
                    unsafe_allow_html=True
                )
            if row["Dias Decorridos"] != "":
                sufixo = " ⏰" if row["Fora Prazo"] == "Sim" else ""
                st.caption(f"{row['Dias Decorridos']} dias decorridos{sufixo}")

    st.markdown("---")

# ==============================
# EXPORTAR EXCEL
# ==============================

if st.button("📥 Exportar para Excel"):
    from io import BytesIO
    cols = [c for c in df_view.columns if not c.startswith("_")]
    buf  = BytesIO()
    df_view[cols].to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel",
        data=buf,
        file_name=f"controle_implantacoes_{date.today().strftime('%d%m%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )