import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import carregar_clientes, carregar_implantacao, CHECKLIST_SEP

st.set_page_config(page_title="Sistema de Implantação", layout="wide")

# ==============================
# LOGO
# ==============================

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)
with col_titulo:
    st.title("🚀 Sistema de Implantação")
    st.caption("Gestão e acompanhamento de implantações de clientes")

st.divider()

# ==============================
# FUNÇÕES DE STATUS
# ==============================

STATUS_CONCLUIDO = {"concluído", "concluida", "concluída", "concluido"}
STATUS_BLOQUEIO  = {"bloqueio/pendente", "bloqueado/pendente", "bloqueado"}
STATUS_ANDAMENTO = {"em andamento"}

def norm_status(s):
    return str(s).strip().lower()

def calcular_status_geral(cnpj, df_impl):
    etapas = df_impl[df_impl["cnpj_cpf"] == cnpj]
    if etapas.empty:
        return "Não Iniciado"
    statuses = [norm_status(s) for s in etapas["status"]]
    if all(s in STATUS_CONCLUIDO for s in statuses):
        return "Concluída"
    if any(s in STATUS_BLOQUEIO for s in statuses):
        return "Bloqueio/Pendente"
    if any(s in STATUS_ANDAMENTO for s in statuses):
        return "Em Andamento"
    return "Não Iniciado"

def calcular_progresso_pct(cnpj, df_impl):
    etapas = df_impl[df_impl["cnpj_cpf"] == cnpj]
    if etapas.empty:
        return 0
    concluidas = sum(1 for s in etapas["status"] if norm_status(s) in STATUS_CONCLUIDO)
    return int(concluidas / len(etapas) * 100)

def dias_sem_atualizacao(ultima_str):
    if not ultima_str or str(ultima_str).strip() in ("", "nan"):
        return None
    for fmt in ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return (datetime.now() - datetime.strptime(str(ultima_str).strip(), fmt)).days
        except Exception:
            continue
    return None

def parse_data(valor):
    if not valor or str(valor).strip() in ("", "nan"):
        return None
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(str(valor).strip(), fmt).date()
        except Exception:
            continue
    return None

def fora_prazo(data_inicio, prazo_dias, status):
    if norm_status(status) in STATUS_CONCLUIDO:
        return False
    di = parse_data(data_inicio)
    if not di or not prazo_dias:
        return False
    try:
        return (date.today() - di).days > int(prazo_dias)
    except Exception:
        return False

# ==============================
# CARREGAR DADOS
# ==============================

df_clientes    = carregar_clientes().fillna("")
df_implantacao = carregar_implantacao().fillna("")
df_clientes["cnpj_cpf"]    = df_clientes["cnpj_cpf"].apply(
    lambda x: __import__("re").sub(r"\D", "", str(x)).zfill(11)
    if len(__import__("re").sub(r"\D", "", str(x))) <= 11
    else __import__("re").sub(r"\D", "", str(x)).zfill(14)
)
df_implantacao["cnpj_cpf"] = df_clientes["cnpj_cpf"].iloc[0:0].reindex(df_implantacao.index) \
    if df_implantacao.empty else df_implantacao["cnpj_cpf"].apply(
        lambda x: __import__("re").sub(r"\D", "", str(x)).zfill(11)
        if len(__import__("re").sub(r"\D", "", str(x))) <= 11
        else __import__("re").sub(r"\D", "", str(x)).zfill(14)
    )

# ==============================
# CALCULAR ALERTAS (sem duplicar lógica do Controle Geral)
# ==============================

alertas = []
if not df_implantacao.empty:
    for _, row in df_implantacao.iterrows():
        status = str(row.get("status", ""))
        if norm_status(status) in STATUS_CONCLUIDO:
            continue

        dias    = dias_sem_atualizacao(row.get("ultima_atualizacao", ""))
        prazo_d = parse_data(row.get("data_conclusao", ""))
        prazo_ok = prazo_d is not None and prazo_d < date.today()

        nivel = None
        if norm_status(status) in STATUS_BLOQUEIO:
            nivel = "bloqueio"
        elif prazo_ok:
            nivel = "atraso"
        elif dias is not None and dias >= 15:
            nivel = "atraso"
        elif dias is not None and dias >= 7:
            nivel = "risco"

        if nivel:
            alertas.append({
                "nivel":   nivel,
                "cliente": str(row.get("cliente", row.get("cnpj_cpf", ""))),
                "cnpj":    str(row.get("cnpj_cpf", "")),
                "etapa":   str(row.get("etapa", "")),
                "status":  status,
                "dias":    dias
            })

# ==============================
# BLOCO DE NOTIFICAÇÕES
# ==============================

if alertas:
    bloqueios_n = [a for a in alertas if a["nivel"] == "bloqueio"]
    atrasos_n   = [a for a in alertas if a["nivel"] == "atraso"]
    riscos_n    = [a for a in alertas if a["nivel"] == "risco"]

    st.markdown("### 🔔 Notificações")
    cb, ca, cr = st.columns(3)
    cb.error(  f"🚨 **{len(bloqueios_n)}** etapa(s) bloqueada(s)")
    ca.warning(f"⏰ **{len(atrasos_n)}** etapa(s) atrasada(s)")
    cr.info(   f"⚠️ **{len(riscos_n)}** etapa(s) em risco")

    with st.expander("Ver detalhes", expanded=len(bloqueios_n) > 0):
        for a in sorted(alertas, key=lambda x: {"bloqueio":0,"atraso":1,"risco":2}.get(x["nivel"],3)):
            icone = {"bloqueio":"🚨","atraso":"⏰","risco":"⚠️"}.get(a["nivel"],"")
            cor   = {"bloqueio":"red","atraso":"orange","risco":"blue"}.get(a["nivel"],"gray")
            dias_txt = f"{a['dias']} dias sem atualização" if a["dias"] is not None else ""
            st.markdown(
                f"{icone} **{a['cliente']}** — `{a['etapa']}` "
                f"· <span style='color:{cor}'>{a['status']}{' · ' + dias_txt if dias_txt else ''}</span>",
                unsafe_allow_html=True
            )
    st.divider()

# ==============================
# MÉTRICAS RESUMIDAS
# (intencionalmente simples — detalhes estão no Controle Geral)
# ==============================

total_clientes = len(df_clientes)

status_por_cliente = {}
for _, cli in df_clientes.iterrows():
    doc = cli["cnpj_cpf"]
    status_por_cliente[doc] = calcular_status_geral(doc, df_implantacao)

n_concluidos  = sum(1 for s in status_por_cliente.values() if s == "Concluída")
n_andamento   = sum(1 for s in status_por_cliente.values() if s == "Em Andamento")
n_bloqueio    = sum(1 for s in status_por_cliente.values() if s == "Bloqueio/Pendente")
n_nao_inic    = sum(1 for s in status_por_cliente.values() if s == "Não Iniciado")

st.markdown("### 📊 Resumo Geral")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("👥 Clientes",        total_clientes)
c2.metric("🆕 Não Iniciados",   n_nao_inic)
c3.metric("⏳ Em Andamento",    n_andamento)
c4.metric("🚨 Com Bloqueio",    n_bloqueio)
c5.metric("✅ Concluídos",      n_concluidos)

st.divider()

# ==============================
# PROGRESSO POR CLIENTE
# ==============================

st.markdown("### 📋 Progresso por Cliente")

if df_implantacao.empty:
    st.info("Nenhuma implantação registrada ainda.")
else:
    COR_PRIOR = {"Alta": "#dc3545", "Média": "#fd7e14", "Baixa": "#28a745"}

    resumo = []
    for _, cli in df_clientes.iterrows():
        doc        = cli["cnpj_cpf"]
        status_g   = calcular_status_geral(doc, df_implantacao)
        pct        = calcular_progresso_pct(doc, df_implantacao)
        etapas_cli = df_implantacao[df_implantacao["cnpj_cpf"] == doc]
        n_bloq     = sum(1 for s in etapas_cli["status"] if norm_status(s) in STATUS_BLOQUEIO)
        n_alert    = sum(1 for a in alertas if a["cnpj"] == doc)
        resumo.append({
            "doc": doc, "nome": cli.get("Nome",""),
            "pct": pct, "status": status_g,
            "prioridade": cli.get("prioridade",""),
            "n_bloq": n_bloq, "n_alert": n_alert,
            "total": len(etapas_cli),
            "concl": sum(1 for s in etapas_cli["status"] if norm_status(s) in STATUS_CONCLUIDO)
        })

    ordem_prior = {"Alta": 0, "Média": 1, "Baixa": 2, "": 3}
    resumo.sort(key=lambda x: (ordem_prior.get(x["prioridade"], 3), -x["pct"] if x["status"] != "Concluída" else 999))

    for r in resumo:
        pct    = r["pct"]
        cor    = "#28a745" if pct == 100 else "#007bff" if pct >= 50 else "#dc3545"
        prior  = r["prioridade"]
        cor_p  = COR_PRIOR.get(prior, "")

        col_nome, col_bar = st.columns([3, 7])
        with col_nome:
            prior_badge = (
                f"<span style='background:{cor_p};color:white;border-radius:4px;"
                f"padding:1px 6px;font-size:11px'>{prior}</span> "
                if prior and cor_p else ""
            )
            st.markdown(f"{prior_badge}**{r['nome']}**", unsafe_allow_html=True)
            st.caption(r["doc"])
        with col_bar:
            bloq_txt  = f" 🚨 {r['n_bloq']} bloq."  if r["n_bloq"]  > 0 else ""
            alert_txt = f" 🔔 {r['n_alert']} alert." if r["n_alert"] > 0 else ""
            st.markdown(
                f"<div style='background:#e9ecef;border-radius:8px;height:22px;margin-top:6px'>"
                f"<div style='width:{max(pct,2)}%;background:{cor};height:22px;border-radius:8px;"
                f"display:flex;align-items:center;padding-left:8px;min-width:2px'>"
                f"<span style='color:white;font-size:12px;font-weight:600'>"
                f"{pct}%{bloq_txt}{alert_txt}</span></div></div>",
                unsafe_allow_html=True
            )
        st.caption(
            f"✅ {r['concl']} concluídas · Total: {r['total']} etapas"
            f"  |  Status: {r['status']}"
        )
        st.markdown("---")

st.caption("Para detalhes completos acesse **📊 Controle Geral** no menu lateral.")