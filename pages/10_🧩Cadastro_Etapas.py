import streamlit as st
import pandas as pd
from database import carregar_etapas, salvar_etapas

st.set_page_config(page_title="Configuração de Etapas", layout="wide")
st.title("⚙️ Configuração de Etapas e Checklists")

# ==============================
# CARREGAR — sempre ordenado
# ==============================

df = carregar_etapas()   # já vem ordenado por ordem_etapa, ordem_item
st.divider()

# ==============================
# NOVA ETAPA
# ==============================

st.subheader("➕ Nova Etapa")

col1, col2 = st.columns(2)
with col1:
    nova_etapa = st.text_input("Nome da Etapa")
with col2:
    # Sugere próxima ordem automaticamente
    prox_ordem = int(df["ordem_etapa"].max()) + 1 if not df.empty else 1
    ordem_etapa = st.number_input("Ordem da Etapa", min_value=1, step=1, value=prox_ordem)

if st.button("➕ Adicionar Etapa"):
    if not nova_etapa.strip():
        st.warning("Informe o nome da etapa.")
    elif nova_etapa.strip().lower() in df["etapa"].astype(str).str.lower().values:
        st.warning("Etapa já existe.")
    else:
        nova_linha = pd.DataFrame([{
            "etapa":       nova_etapa.strip(),
            "item":        "",
            "ordem_etapa": int(ordem_etapa),
            "ordem_item":  1
        }])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df = df.sort_values(["ordem_etapa", "ordem_item"])
        salvar_etapas(df)
        st.success("✅ Etapa adicionada!")
        st.rerun()

# ==============================
# NOVO ITEM
# ==============================

st.subheader("🧩 Adicionar Item ao Checklist")

if not df.empty:
    # Etapas sempre em ordem
    etapas_ord = (
        df[["etapa", "ordem_etapa"]]
        .drop_duplicates()
        .sort_values("ordem_etapa")["etapa"]
        .tolist()
    )

    with st.form("form_novo_item"):
        col1, col2 = st.columns(2)
        with col1:
            etapa_sel = st.selectbox("Etapa", etapas_ord)
        with col2:
            novo_item = st.text_input("Descrição do Item")

        submitted = st.form_submit_button("➕ Adicionar Item")

        if submitted:
            if not novo_item.strip():
                st.warning("Informe a descrição do item.")
            elif novo_item.strip().lower() in df[df["etapa"] == etapa_sel]["item"].astype(str).str.lower().values:
                st.warning("Este item já existe nesta etapa.")
            else:
                ordem_etapa_val = df[df["etapa"] == etapa_sel]["ordem_etapa"].iloc[0]
                itens_etapa     = df[df["etapa"] == etapa_sel]
                ordem_item      = 1 if itens_etapa.empty else int(itens_etapa["ordem_item"].max()) + 1

                nova_linha = pd.DataFrame([{
                    "etapa":       etapa_sel,
                    "item":        novo_item.strip(),
                    "ordem_etapa": int(ordem_etapa_val),
                    "ordem_item":  ordem_item
                }])
                df = pd.concat([df, nova_linha], ignore_index=True)
                df = df.sort_values(["ordem_etapa", "ordem_item"])
                salvar_etapas(df)
                st.success("✅ Item adicionado!")
                st.rerun()

st.divider()

# ==============================
# EXCLUIR ETAPA
# ==============================

st.subheader("🗑️ Excluir Etapa")

if not df.empty:
    etapas_ord_lista = (
        df[["etapa", "ordem_etapa"]]
        .drop_duplicates()
        .sort_values("ordem_etapa")["etapa"]
        .tolist()
    )
    col1, col2 = st.columns([3, 1])
    with col1:
        etapa_excluir = st.selectbox("Selecione a etapa para excluir", etapas_ord_lista, key="etapa_excluir")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Excluir"):
            df = df[df["etapa"] != etapa_excluir]
            salvar_etapas(df)
            st.success(f"Etapa '{etapa_excluir}' excluída.")
            st.rerun()

st.divider()

# ==============================
# TABELA EDITÁVEL — sempre ordenada
# ==============================

st.subheader("📋 Edição Direta")

df_editado = st.data_editor(
    df.sort_values(["ordem_etapa", "ordem_item"]),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "ordem_etapa": st.column_config.NumberColumn("Ordem Etapa", min_value=1),
        "ordem_item":  st.column_config.NumberColumn("Ordem Item",  min_value=1),
    }
)

if st.button("💾 Salvar Alterações"):
    df_editado = df_editado.sort_values(["ordem_etapa", "ordem_item"])
    salvar_etapas(df_editado)
    st.success("✅ Alterações salvas!")
    st.rerun()

st.divider()

# ==============================
# VISUALIZAÇÃO — sempre ordenada
# ==============================

st.subheader("📊 Visualização por Etapa")

if not df_editado.empty:
    etapas_view = (
        df_editado[["etapa", "ordem_etapa"]]
        .drop_duplicates()
        .sort_values("ordem_etapa")
    )

    n_cols = 2 if len(etapas_view) <= 4 else 3
    cols   = st.columns(n_cols)

    for i, (_, row) in enumerate(etapas_view.iterrows()):
        with cols[i % n_cols]:
            st.markdown(f"### 🔹 {int(row['ordem_etapa'])}. {row['etapa']}")
            itens = (
                df_editado[df_editado["etapa"] == row["etapa"]]
                .sort_values("ordem_item")["item"]
                .tolist()
            )
            for item in itens:
                if str(item).strip():
                    st.write(f"✔ {item}")