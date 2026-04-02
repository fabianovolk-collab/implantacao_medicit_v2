import streamlit as st

st.set_page_config(page_title="Ajuda", layout="wide")

st.title("❓ Central de Ajuda")
st.caption("Guia completo do Sistema de Implantação — clique em cada seção para expandir.")

st.divider()

# ==============================
# VISÃO GERAL DO SISTEMA
# ==============================

with st.expander("🗺️ Visão Geral do Sistema", expanded=True):
    st.markdown("""
    O sistema organiza todo o processo de implantação de clientes em um único lugar,
    integrando cadastro, execução por etapas, acompanhamento e geração de documentos.

    **Fluxo recomendado de uso:**

    1. **Cadastro de Etapas** → Configure as etapas e checklists padrão da implantação *(feito uma vez)*
    2. **Cadastro de Clientes** → Cadastre o cliente e os dados do contrato
    3. **Etapa por Cliente** → Selecione quais etapas este cliente vai cumprir e gere a planilha
    4. **Gestão de Implantação** → Acompanhe e atualize cada etapa conforme o andamento
    5. **Consulta Geral** → Visão consolidada de todos os clientes
    6. **Protocolo** → Gere o PDF executivo para enviar ao cliente

    ---
    **Onde os dados ficam armazenados?**
    Todos os dados são salvos diretamente no Google Sheets, em tempo real.
    Qualquer usuário com acesso ao sistema vê as informações atualizadas.
    """)

st.divider()

# ==============================
# MENU / DASHBOARD
# ==============================

with st.expander("🚀 Tela Inicial (Menu / Dashboard)"):
    st.markdown("""
    A tela inicial é um painel de acompanhamento em tempo real. Ela não requer nenhuma ação do usuário.

    **Bloco de Notificações** *(aparece apenas quando há pendências)*
    | Ícone | Significado |
    |---|---|
    | 🚨 Bloqueada | Etapa marcada como Bloqueio/Pendente — requer atenção imediata |
    | ⏰ Atrasada | Sem atualização há mais de 15 dias ou com data de conclusão ultrapassada |
    | ⚠️ Em risco | Sem atualização entre 7 e 14 dias |

    **Métricas do topo**
    Mostram a quantidade de clientes em cada situação geral (calculado automaticamente a partir das etapas).

    **Barras de progresso**
    Cada barra representa um cliente. A cor indica a situação:
    - 🟢 Verde → 100% concluído
    - 🔵 Azul → 50% ou mais concluído
    - 🔴 Vermelho → menos de 50% concluído

    Para detalhes completos de cada cliente, acesse a tela **Consulta Geral**.
    """)

# ==============================
# CADASTRO DE CLIENTES
# ==============================

with st.expander("👤 Cadastro de Clientes"):
    st.markdown("""
    Tela principal de cadastro. Cada cliente é identificado pelo CPF ou CNPJ.

    **Como buscar um cliente existente**
    Digite o CPF/CNPJ no campo e clique em 🔍 **Buscar Cliente**.
    Se encontrado, os campos serão preenchidos automaticamente para edição.

    ---
    **Dados Cadastrais**

    | Campo | O que preencher |
    |---|---|
    | Tipo de Pessoa | Física (CPF) ou Jurídica (CNPJ) |
    | CPF / CNPJ | Somente números — o sistema valida automaticamente |
    | Nome / Razão Social | Nome completo do cliente ou razão social da empresa |
    | Telefone | Número com DDD — somente números |
    | Responsável Comercial | Quem vendeu / é responsável comercial pelo cliente |
    | Responsável Cliente | Pessoa de contato na clínica/empresa do cliente |
    | Responsável Medicit | Consultor interno responsável pela implantação |

    ---
    **Dados do Contrato**

    | Campo | O que preencher |
    |---|---|
    | Data de Assinatura do Contrato | Data em que o contrato foi assinado |
    | Pacote | Start, Gold ou Personalizado |
    | Adicional do Pacote | Módulos extras contratados (ex: Whats + Controle Financeiro) |
    | Qtde de Agendas | Número de agendas contratadas |
    | Prazo de Implantação (dias) | Dias combinados para concluir toda a implantação |
    | Prioridade | Alta, Média ou Baixa — usada para ordenar na Consulta Geral |
    | Data Prevista de Início | Data planejada para iniciar a implantação |
    | Observação | Qualquer anotação relevante sobre este cliente |

    ---
    **Excluir cliente**
    Só é possível excluir clientes que **não possuem implantação vinculada**.
    Se o cliente já tem etapas registradas, a exclusão será bloqueada para preservar o histórico.
    """)

# ==============================
# ETAPA POR CLIENTE
# ==============================

with st.expander("📋 Etapa por Cliente (Pré-Implantação)"):
    st.markdown("""
    Esta tela é o ponto de partida da implantação de cada cliente.
    Aqui você seleciona quais etapas o cliente vai cumprir e gera a planilha de trabalho.

    **Passo a passo:**

    1. Busque o cliente pelo nome ou CPF/CNPJ
    2. Confirme o **Responsável Medicit** (preenchido automaticamente do cadastro)
    3. Confirme ou ajuste o **Responsável Cliente** (preenchido do cadastro, destacado para revisão)
    4. Marque as etapas que se aplicam a este cliente
    5. Clique em **💾 Salvar Pré-Implantação**
    6. Clique em **📤 Gerar Planilha de Retorno** para baixar o Excel

    ---
    **Planilha de Retorno (Excel)**
    O arquivo gerado deve ser enviado para a clínica preencher com:
    - Responsável da clínica por etapa
    - Participantes de cada etapa
    - Data prevista de cada etapa

    Após o retorno preenchido pela clínica, importe o arquivo na tela de **Gestão de Implantação**.

    **Observação:** Etapas já cadastradas para o cliente aparecem marcadas com ✅ e ficam desabilitadas para evitar duplicidade.
    """)

# ==============================
# GESTÃO DE IMPLANTAÇÃO
# ==============================

with st.expander("✅ Gestão de Implantação"):
    st.markdown("""
    Tela principal de acompanhamento do dia a dia da implantação.
    Aqui você atualiza o status, marca o checklist e registra informações de cada etapa.

    ---
    **Importação de Planilha de Retorno**

    Após a clínica devolver o Excel preenchido:
    1. Selecione o cliente
    2. Clique em **📥 Importar Planilha de Retorno**
    3. Selecione o arquivo Excel retornado

    ⚠️ A importação só é permitida se **nenhuma etapa tiver sido iniciada** para este cliente.
    Isso evita sobrescrever informações já preenchidas manualmente.

    ---
    **Campos de cada etapa**

    | Campo | O que preencher |
    |---|---|
    | Status | Situação atual da etapa |
    | Data de Início | Data em que a etapa foi iniciada |
    | Responsável Medicit | Consultor interno responsável por esta etapa |
    | Responsável Cliente | Pessoa da clínica responsável por esta etapa |
    | Participantes | Nomes de todos os envolvidos nesta etapa |
    | Motivo / Observação | Contexto, anotações ou justificativa de bloqueio |
    | Próxima Ação | O que precisa ser feito na sequência |
    | Data de Conclusão | Data real de conclusão desta etapa |

    ---
    **Status disponíveis**

    | Status | Quando usar |
    |---|---|
    | Não iniciado | Etapa ainda não começou |
    | Em andamento | Etapa em execução |
    | Bloqueio/Pendente | Algum impedimento está travando o avanço — descreva no campo Motivo |
    | Concluído | Etapa 100% finalizada |

    ---
    **Comportamentos automáticos**
    - Quando **todos os itens do checklist** forem marcados → status muda automaticamente para **Concluído**
    - Quando o status **Concluído** for selecionado → data de conclusão é preenchida com a **data de hoje**
    - Etapas com problemas aparecem com alertas 🚨 ⏰ ⚠️ no topo da tela
    """)

# ==============================
# CONSULTA GERAL
# ==============================

with st.expander("📊 Consulta Geral"):
    st.markdown("""
    Visão consolidada de todos os clientes em um único lugar.
    Ideal para reuniões de acompanhamento e gestão da equipe.

    **Status geral de cada cliente** *(calculado automaticamente)*

    | Status | Significa |
    |---|---|
    | Não Iniciado | Nenhuma etapa foi iniciada ainda |
    | Em Andamento | Pelo menos uma etapa em andamento |
    | Bloqueio/Pendente | Pelo menos uma etapa travada |
    | Aguardando Dados | Pelo menos uma etapa aguardando dados do cliente |
    | Concluída | **Todas** as etapas concluídas |

    **Campos calculados automaticamente** *(não precisam ser preenchidos)*

    | Campo | Como é calculado |
    |---|---|
    | Progresso (%) | % de etapas concluídas sobre o total |
    | Dias Decorridos | Dias desde a data prevista de início até hoje |
    | Fora Prazo | Sim quando dias decorridos > prazo contratado |
    | Data Conclusão | Data da última etapa concluída (só aparece quando todas concluídas) |

    **Filtros disponíveis:** Nome/CPF, Status, Prioridade, Fora do Prazo

    **Exportar:** clique em 📥 **Exportar para Excel** para baixar a tabela filtrada.
    """)

# ==============================
# PROTOCOLO
# ==============================

with st.expander("📄 Protocolo de Implantação"):
    st.markdown("""
    Gera um PDF executivo com o resumo completo da implantação de um cliente.
    O documento é adequado para enviar ao cliente como comprovante de andamento.

    **O que o PDF contém:**
    - Dados do cliente (nome, CPF/CNPJ)
    - Data de início da implantação
    - Barra de progresso geral
    - Para cada etapa: status, responsáveis, datas, checklist com itens marcados e progresso individual
    - Rodapé com data e hora de geração

    **Como gerar:**
    1. Busque o cliente pelo nome ou CPF/CNPJ
    2. Verifique o progresso exibido na tela
    3. Clique em 📄 **Gerar Protocolo Executivo**
    4. O arquivo será baixado automaticamente

    **Logo no PDF:** o arquivo `logo.png` na raiz do servidor é inserido automaticamente no cabeçalho.
    """)

# ==============================
# HISTÓRICO
# ==============================

with st.expander("📜 Histórico de Alterações"):
    st.markdown("""
    Registro automático de todas as ações realizadas no sistema.
    Não é necessário preencher nada — o histórico é gerado automaticamente.

    **O que é registrado:**
    - Inserção, atualização e exclusão de clientes
    - Alterações de status em etapas
    - Importações de planilha
    - Inserção de novas etapas por cliente

    **Filtros disponíveis:** Cliente, Página de origem, Tipo de ação

    **Timeline:** ao filtrar por um cliente específico, as alterações aparecem em formato de linha do tempo,
    mostrando campo alterado, valor anterior e valor novo.

    > ⚠️ Para que o histórico funcione, o ID da planilha de histórico deve estar configurado em `database.py`.
    """)

# ==============================
# CADASTRO DE ETAPAS
# ==============================

with st.expander("⚙️ Cadastro de Etapas"):
    st.markdown("""
    Configuração das etapas e checklists padrão do processo de implantação.
    Esta tela é configurada uma vez e raramente precisa ser alterada.

    **Etapas**
    Cada etapa representa uma fase do processo (ex: Configuração Inicial, Treinamento, Go-Live).
    A **ordem da etapa** define a sequência em que aparecerão nas outras telas.

    **Itens do Checklist**
    Cada etapa pode ter vários itens de checklist.
    A **ordem do item** define a sequência dentro da etapa.

    **Como adicionar uma nova etapa:**
    1. Informe o nome e a ordem desejada
    2. Clique em ➕ **Adicionar Etapa**

    **Como adicionar um item ao checklist:**
    1. Selecione a etapa
    2. Informe a descrição do item
    3. Clique em ➕ **Adicionar Item**

    **Edição direta:** a tabela no final da tela permite editar qualquer campo diretamente.
    Após editar, clique em 💾 **Salvar Alterações**.

    > ⚠️ Alterações nas etapas afetam **novos** registros. Etapas já vinculadas a clientes não são alteradas retroativamente.
    """)

st.divider()

# ==============================
# DICAS GERAIS
# ==============================

st.markdown("### 💡 Dicas Gerais")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **🔄 Dados não atualizaram?**

    O sistema mantém um cache de 60 segundos para reduzir chamadas à API do Google.
    Se você salvou algo e não apareceu, aguarde 1 minuto e recarregue a página.
    """)

with col2:
    st.warning("""
    **⚠️ CPF/CNPJ com zeros**

    Sempre digite o CPF com 11 dígitos e o CNPJ com 14 dígitos, incluindo os zeros à esquerda.
    O sistema faz a validação automaticamente.
    """)

with col3:
    st.success("""
    **✅ Ordem de preenchimento**

    Para um novo cliente, siga sempre:
    Cadastro → Etapas → Gestão.
    Pular etapas pode causar registros incompletos.
    """)

st.divider()
st.caption("Sistema de Implantação · Desenvolvido com Streamlit e Google Sheets")