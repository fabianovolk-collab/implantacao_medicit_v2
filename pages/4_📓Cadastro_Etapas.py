# ==============================
# cadastro_etapas.py (versão integrada com database.py)
# ==============================
import streamlit as st
import pandas as pd
from database import carregar_etapas, salvar_etapas  # <-- integração com database.py

st.set_page_config(page_title="Configuração Implantação", layout="wide")
st.title("⚙️ Configuração de Etapas e Checklists")

# -----------------------------
# CARREGAR CSV / DATABASE
# -----------------------------
df = carregar_etapas()
st.divider()

# -----------------------------
# NOVA ETAPA
# -----------------------------
st.subheader("➕ Nova Etapa")
col1, col2 = st.columns(2)

with col1:
    nova_etapa = st.text_input("Nome da Etapa")
with col2:
    ordem_etapa = st.number_input("Ordem da Etapa", min_value=1, step=1)

if st.button("➕ Adicionar Etapa"):
    if not nova_etapa:
        st.warning("Informe o nome da etapa")
    elif nova_etapa in df["etapa"].unique():
        st.warning("Etapa já existe")
    else:
        nova_linha = pd.DataFrame([{
            "etapa": nova_etapa,
            "item": "",
            "ordem_etapa": ordem_etapa,
            "ordem_item": 1,
            "ativo": True
        }])
        df = pd.concat([df, nova_linha], ignore_index=True)
        salvar_etapas(df)  # <-- salvando via database.py
        st.rerun()

# -----------------------------
# NOVO ITEM
# -----------------------------
st.subheader("🧩 Adicionar Item")
if not df.empty:
    etapas = sorted(df["etapa"].dropna().unique())
    col1, col2, col3 = st.columns(3)

    with col1:
        etapa_sel = st.selectbox("Etapa", etapas)
    with col2:
        novo_item = st.text_input("Descrição")
    with col3:
        ordem_item = st.number_input("Ordem do Item", min_value=1, step=1)

    if st.button("➕ Adicionar Item"):
        if not novo_item:
            st.warning("Informe o item")
        else:
            ordem_etapa_val = df[df["etapa"] == etapa_sel]["ordem_etapa"].iloc[0]
            nova_linha = pd.DataFrame([{
                "etapa": etapa_sel,
                "item": novo_item,
                "ordem_etapa": ordem_etapa_val,
                "ordem_item": ordem_item,
                "ativo": True
            }])
            df = pd.concat([df, nova_linha], ignore_index=True)
            salvar_etapas(df)  # <-- salvando via database.py
            st.rerun()

st.divider()

# -----------------------------
# TABELA EDITÁVEL
# -----------------------------
st.subheader("📋 Estrutura (Edição)")
df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# -----------------------------
# BOTÃO SALVAR
# -----------------------------
if st.button("💾 Salvar Alterações"):
    salvar_etapas(df_editado)  # <-- salvando via database.py
    st.rerun()

st.divider()

# -----------------------------
# VISUALIZAÇÃO
# -----------------------------
st.subheader("📊 Visualização por Etapa")
if not df_editado.empty:
    df_base = df_editado.copy()
    df_base["ativo"] = df_base["ativo"].astype(str).str.lower().isin(["true", "1", "sim"])
    df_view = df_base[df_base["ativo"]]

    etapas_ord = df_view[["etapa", "ordem_etapa"]].drop_duplicates().sort_values("ordem_etapa")
    n_cols = 2 if len(etapas_ord) <= 4 else 3
    cols = st.columns(n_cols)

    for i, (_, row) in enumerate(etapas_ord.iterrows()):
        col = cols[i % n_cols]
        with col:
            st.markdown(f"### 🔹 {int(row['ordem_etapa'])}. {row['etapa']}")
            itens = df_view[df_view["etapa"] == row["etapa"]].sort_values("ordem_item")["item"].tolist()
            for item in itens:
                if item:
                    st.write(f"✔ {item}")