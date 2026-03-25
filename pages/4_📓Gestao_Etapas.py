import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Configuração Implantação", layout="wide")
st.title("⚙️ Configuração de Etapas e Checklists")

CAMINHO = "etapas_checklist.csv"

# -----------------------------
# CARREGAR CSV (robusto e seguro)
# -----------------------------
def carregar():
    if not os.path.exists(CAMINHO):
        return pd.DataFrame(columns=[
            "etapa", "item", "ordem_etapa", "ordem_item", "ativo"
        ])

    # Lê CSV
    df = pd.read_csv(CAMINHO)

    # Padroniza colunas
    df.columns = [c.strip().lower() for c in df.columns]

    # Mantém apenas as colunas essenciais
    colunas_essenciais = ["etapa", "item", "ordem_etapa", "ordem_item", "ativo"]
    df = df.loc[:, df.columns.isin(colunas_essenciais)]
    for col in colunas_essenciais:
        if col not in df.columns:
            df[col] = ""

    # Garantir que são Series
    for col in ["etapa", "item"]:
        df[col] = pd.Series(df[col]).astype(str).fillna("").str.strip()

    # Remove linhas sem etapa
    df = df[df["etapa"] != ""]

    # Corrige valores "nan" na coluna item
    df["item"] = df["item"].replace("nan", "")

    # Ordem da etapa
    if df["ordem_etapa"].isnull().all():
        etapas_unicas = df["etapa"].drop_duplicates().tolist()
        ordem_map = {etapa: i+1 for i, etapa in enumerate(etapas_unicas)}
        df["ordem_etapa"] = df["etapa"].map(ordem_map)
    else:
        df["ordem_etapa"] = pd.to_numeric(df["ordem_etapa"], errors="coerce").fillna(1).astype(int)

    # Ordem do item
    if df["ordem_item"].isnull().all():
        df["ordem_item"] = df.groupby("etapa").cumcount() + 1
    else:
        df["ordem_item"] = pd.to_numeric(df["ordem_item"], errors="coerce").fillna(1).astype(int)

    # Ativo
    df["ativo"] = df["ativo"].astype(str).str.lower().isin(["true", "1", "sim"])

    return df

# -----------------------------
# SALVAR CSV
# -----------------------------
def salvar(df):
    df_export = df.copy()
    df_export["ativo"] = df_export["ativo"].astype(bool)
    df_export.columns = [c.capitalize() for c in df_export.columns]
    df_export.to_csv(CAMINHO, index=False)

# -----------------------------
# LOAD
# -----------------------------
df = carregar()
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
        salvar(df)
        st.success("Etapa adicionada!")
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
            salvar(df)
            st.success("Item adicionado!")
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
    salvar(df_editado)
    st.success("Alterações salvas!")
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