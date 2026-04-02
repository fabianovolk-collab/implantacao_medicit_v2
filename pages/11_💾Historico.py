import streamlit as st
import pandas as pd
from database import carregar_historico, carregar_clientes, SHEET_IDS

st.set_page_config(layout="wide")
st.title("📜 Histórico de Alterações")

# ==============================
# VERIFICAR CONFIGURAÇÃO
# ==============================

if not SHEET_IDS.get("historico"):
    st.warning("""
    ⚠️ **Histórico não configurado**

    Para ativar esta funcionalidade:
    1. Crie uma nova planilha no Google Sheets
    2. Compartilhe-a com a service account configurada em `secrets.toml`
    3. Cole o ID da planilha em `database.py` no campo `"historico"`

    O ID fica na URL da planilha:
    `https://docs.google.com/spreadsheets/d/**ID_AQUI**/edit`
    """)
    st.stop()

# ==============================
# CARREGAR DADOS
# ==============================

df_hist = carregar_historico()
df_clientes = carregar_clientes()

if df_hist.empty:
    st.info("Nenhum registro de histórico encontrado ainda.")
    st.stop()

df_hist.fillna("", inplace=True)
df_hist["cnpj_cpf"] = df_hist["cnpj_cpf"].astype(str).str.zfill(11)

# ==============================
# FILTROS
# ==============================

col1, col2, col3 = st.columns(3)

with col1:
    # Filtro por cliente
    clientes_opcoes = ["Todos"] + sorted(df_hist["cliente"].unique().tolist())
    cliente_filtro  = st.selectbox("Filtrar por Cliente", clientes_opcoes)

with col2:
    # Filtro por página
    paginas_opcoes = ["Todas"] + sorted(df_hist["pagina"].unique().tolist())
    pagina_filtro  = st.selectbox("Filtrar por Página", paginas_opcoes)

with col3:
    # Filtro por ação
    acoes_opcoes = ["Todas"] + sorted(df_hist["acao"].unique().tolist())
    acao_filtro  = st.selectbox("Filtrar por Ação", acoes_opcoes)

# Aplicar filtros
df_filtrado = df_hist.copy()
if cliente_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["cliente"] == cliente_filtro]
if pagina_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado["pagina"] == pagina_filtro]
if acao_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado["acao"] == acao_filtro]

# Ordenar do mais recente para o mais antigo
try:
    df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)
except Exception:
    pass

st.divider()

# ==============================
# RESUMO
# ==============================

st.markdown(f"**{len(df_filtrado)} registro(s) encontrado(s)**")

col1, col2, col3 = st.columns(3)
col1.metric("Total de eventos", len(df_filtrado))
col2.metric("Clientes envolvidos", df_filtrado["cnpj_cpf"].nunique())
col3.metric("Páginas ativas",      df_filtrado["pagina"].nunique())

st.divider()

# ==============================
# TIMELINE POR CLIENTE
# ==============================

if cliente_filtro != "Todos":
    st.subheader(f"🕐 Timeline — {cliente_filtro}")

    for _, row in df_filtrado.iterrows():
        icone = {
            "Inserção":           "🟢",
            "Atualização":        "🔵",
            "Exclusão":           "🔴",
            "Importação de planilha": "📥",
            "Inserção de etapas": "📋",
        }.get(row["acao"], "⚪")

        with st.container():
            col_icone, col_info = st.columns([1, 11])
            with col_icone:
                st.markdown(f"### {icone}")
            with col_info:
                st.markdown(f"**{row['acao']}** — {row['pagina']}")
                st.caption(row["data_hora"])
                if row.get("etapa"):
                    st.write(f"Etapa: {row['etapa']}")
                if row.get("campo"):
                    st.write(
                        f"Campo **{row['campo']}**: "
                        f"`{row['valor_anterior'] or '(vazio)'}` → `{row['valor_novo'] or '(vazio)'}`"
                    )
        st.markdown("---")
else:
    # ==============================
    # TABELA GERAL
    # ==============================

    colunas_exibir = ["data_hora", "cliente", "pagina", "acao", "etapa", "campo", "valor_anterior", "valor_novo"]
    colunas_exibir = [c for c in colunas_exibir if c in df_filtrado.columns]

    st.dataframe(
        df_filtrado[colunas_exibir].rename(columns={
            "data_hora":       "Data/Hora",
            "cliente":         "Cliente",
            "pagina":          "Página",
            "acao":            "Ação",
            "etapa":           "Etapa",
            "campo":           "Campo",
            "valor_anterior":  "Valor Anterior",
            "valor_novo":      "Valor Novo"
        }),
        use_container_width=True
    )
