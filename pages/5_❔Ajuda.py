import streamlit as st

st.set_page_config(layout="wide")
st.title("❓ Ajuda e Guia de Utilização")

# -----------------------------
# INTRODUÇÃO
# -----------------------------
st.markdown("""
### 📊 Sistema de Implantação - Medicit

Este sistema foi criado para organizar, padronizar e dar visibilidade ao processo de implantação dos clientes.

Agora o sistema conta com:
- ✅ Checklist por etapa
- ✅ Progresso automático
- ✅ Tela de Protocolo
- ✅ Geração de Protocolo Executivo (PDF automático)

Use esta página como referência sempre que tiver dúvidas.
""")

# -----------------------------
# COMO USAR
# -----------------------------
with st.expander("🚀 Como usar o sistema"):
    st.markdown("""
### Passo a passo:

1. **Cadastrar o cliente**
2. **Preencher as Fases de Implantação**
3. **Atualizar checklist e status**
4. **Acompanhar na tela de Protocolo**
5. **Gerar o Protocolo Executivo (PDF)**

---

### Regra principal:
👉 Nunca duplicar etapas — apenas atualizar
""")

# -----------------------------
# CADASTRO CLIENTE
# -----------------------------
with st.expander("👤 Cadastro de Cliente"):
    st.markdown("""
### Campos:

- **CNPJ/CPF**  
Documento único do cliente (não pode duplicar)

- **Nome / Razão Social**  
Nome da clínica ou empresa

- **Telefone**  
Contato principal

- **Responsável Comercial**  
Quem realizou a venda

- **Responsável Cliente**  
Pessoa do cliente responsável pela implantação

- **Responsável Medicit**  
Responsável interno pelo processo
""")

# -----------------------------
# FASES ATUALIZADAS
# -----------------------------
with st.expander("⚙️ Fases de Implantação (Novo Modelo)"):
    st.markdown("""
### Etapas padrão:

1. **Inicial**
   - Cadastro do cliente
   - Liberação de acesso
   - Boas-vindas
   - Agendamento inicial

2. **Cadastro**
   - Clínica
   - Profissionais
   - Serviços
   - Agenda
   - Financeiro

3. **Importação de Base**
   - Recebimento da base
   - Validação
   - Importação
   - Conferência com cliente

4. **Treinamento**
   - Agenda
   - Pacientes
   - Financeiro
   - Dúvidas

5. **Go-Live**
   - Virada do sistema
   - Início oficial
   - Equipe alinhada

6. **Acompanhamento**
   - Uso no dia a dia
   - Ajustes
   - Validação final
   - Autonomia do cliente
""")

# -----------------------------
# STATUS
# -----------------------------
with st.expander("📌 Status das Etapas"):
    st.markdown("""
- **Não iniciado** → Ainda não começou  
- **Em andamento** → Está sendo executado  
- **Bloqueado/Pendente** → Existe impedimento  
- **Concluído** → Finalizado  

---

### 🚨 Importante:
Se estiver bloqueado → SEMPRE preencher o motivo
""")

# -----------------------------
# CHECKLIST
# -----------------------------
with st.expander("✅ Checklist"):
    st.markdown("""
Cada etapa possui um checklist obrigatório.

👉 O progresso é calculado automaticamente com base no checklist.

✔ Evita retrabalho  
✔ Garante padrão  
✔ Mostra evolução real da implantação  
""")

# -----------------------------
# PROTOCOLO
# -----------------------------
with st.expander("📄 Protocolo"):
    st.markdown("""
Nesta tela você pode:

- Buscar cliente por **CPF/CNPJ**
- Selecionar cliente por **nome (ordem alfabética)**
- Visualizar todas as etapas da implantação
- Acompanhar o progresso geral
- Ver checklist detalhado por etapa
- Identificar bloqueios e responsáveis

---

### 📈 Barra de Progresso (Semáforo)

- **0%** → Não iniciado (cinza)
- **1% a 50%** → Em risco (amarelo)
- **51% a 99%** → Em andamento (azul)
- **100%** → Concluído (verde)

---

### 📄 Protocolo Executivo

Ao clicar em **Gerar Protocolo Executivo**:

✔ O PDF é gerado automaticamente  
✔ O download é iniciado automaticamente  
✔ Documento pronto para envio ao cliente  

---

👉 Essa tela substitui a antiga "Consulta" e centraliza toda a visão da implantação
""")

# -----------------------------
# BOAS PRÁTICAS
# -----------------------------
with st.expander("🔥 Boas Práticas"):
    st.markdown("""
### Faça sempre:

✔ Atualize diariamente  
✔ Preencha checklist completo  
✔ Defina responsáveis claros  
✔ Registre bloqueios corretamente  

---

### Evite:

❌ Deixar etapas sem status  
❌ Não preencher bloqueios  
❌ Duplicar dados  
❌ Ignorar checklist  

---

👉 Implantação bem controlada = menos churn + mais satisfação
""")

# -----------------------------
# CONCLUSÃO
# -----------------------------
st.markdown("---")

st.success("""
🎯 Objetivo do sistema:

Garantir controle total da implantação, padronizar processos e aumentar a satisfação do cliente.

🚀 Resultado esperado:
Mais organização, mais controle e uma implantação previsível e escalável.
""")