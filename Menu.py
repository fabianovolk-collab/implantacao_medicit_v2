import streamlit as st

# -----------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Medicit - Implantação",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# TÍTULO PRINCIPAL
# -----------------------------
st.title("📊 Sistema de Implantação - Medicit")

st.markdown("---")

# -----------------------------
# APRESENTAÇÃO
# -----------------------------
st.markdown("""
### 👋 Bem-vindo ao sistema de controle de implantação

Este sistema foi desenvolvido para:

✔ Controlar o processo de implantação dos clientes  
✔ Acompanhar cada etapa da implantação  
✔ Identificar bloqueios e pendências  
✔ Garantir padronização e eficiência no processo  

---

### 📌 Como utilizar o sistema

Use o **menu lateral esquerdo** para navegar entre as funcionalidades:

""")

# -----------------------------
# MENU EXPLICATIVO
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
### 👤 Cadastro de Cliente
- Cadastro completo do cliente
- Informações comerciais e responsáveis
""")

    st.markdown("""
### ⚙️ Fases de Implantação
- Controle das etapas
- Atualização de status
- Gestão de bloqueios
""")

with col2:
    st.markdown("""
### 📊 Consulta Geral
- Visualização de todos os dados
- Acompanhamento completo
""")

    st.markdown("""
### ❓ Ajuda
- Descrição dos campos
- Orientações de uso
""")

# -----------------------------
# ALERTA / ORIENTAÇÃO
# -----------------------------
st.markdown("---")

st.info("""
💡 Dica: Sempre mantenha as etapas atualizadas para garantir visibilidade e evitar atrasos na implantação.
""")

# -----------------------------
# RODAPÉ
# -----------------------------
st.markdown("---")

st.caption("Sistema interno de controle de implantação - Medicit")