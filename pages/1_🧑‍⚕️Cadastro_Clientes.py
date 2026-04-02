import streamlit as st
import pandas as pd
import datetime as dt
from database import (
    ler, inserir, atualizar, deletar,
    carregar_clientes, registrar_historico,
    normalizar_doc, formatar_data_br, parse_data,
    PACOTES_DISPONIVEIS, PRIORIDADES, SCHEMAS
)
from utils import validar_documento, validar_documento_tempo_real, formatar_telefone, somente_numeros

st.set_page_config(layout="wide")
st.title("👤 Cadastro de Cliente")

# ==============================
# BASE
# ==============================

def carregar_base():
    df = carregar_clientes()
    if df is None or df.empty:
        return pd.DataFrame(columns=SCHEMAS["clientes"])
    df.fillna("", inplace=True)
    return df

df = carregar_base()

df_implantacao = ler("implantacao")
if df_implantacao is None or df_implantacao.empty:
    df_implantacao = pd.DataFrame(columns=["cnpj_cpf"])
df_implantacao["cnpj_cpf"] = df_implantacao["cnpj_cpf"].apply(normalizar_doc)
df_implantacao.fillna("", inplace=True)

# ==============================
# FUNÇÕES
# ==============================

def buscar_cliente(doc):
    doc = normalizar_doc(doc)
    res = df[df["cnpj_cpf"] == doc]
    return res.iloc[0].to_dict() if not res.empty else None

def cliente_tem_vinculo(doc):
    return not df_implantacao[df_implantacao["cnpj_cpf"] == normalizar_doc(doc)].empty

# ==============================
# SESSION STATE
# ==============================

def init_state():
    defaults = {
        "tipo_pessoa":            "Pessoa Física",
        "documento":              "",
        "nome":                   "",
        "telefone":               "",
        "resp_comercial":         "",
        "resp_cliente":           "",
        "resp_medicit":           "",
        "data_ass_contrato":      None,
        "pacote":                 PACOTES_DISPONIVEIS[0],
        "adicional_pacote":       "",
        "qtde_agendas":           1,
        "prazo_implantacao_dias": 45,
        "prioridade":             "Alta",
        "data_prevista_inicio":   None,
        "observacao":             "",
        "modo":                   "novo",
        "limpar":                 False,
        "confirmar_exclusao":     False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

if st.session_state.limpar:
    for c in ["documento", "nome", "telefone", "resp_comercial",
              "resp_cliente", "resp_medicit", "adicional_pacote", "observacao"]:
        st.session_state[c] = ""
    st.session_state.data_ass_contrato      = None
    st.session_state.data_prevista_inicio   = None
    st.session_state.pacote                 = PACOTES_DISPONIVEIS[0]
    st.session_state.qtde_agendas           = 1
    st.session_state.prazo_implantacao_dias = 45
    st.session_state.prioridade             = "Alta"
    st.session_state.modo                   = "novo"
    st.session_state.limpar                 = False

# ==============================
# FORMULÁRIO — DADOS CADASTRAIS
# ==============================

st.subheader("➕ Cadastro / Edição de Cliente")

with st.form("form_cliente"):

    col1, col2 = st.columns(2)
    col1.selectbox("Tipo de Pessoa", ["Pessoa Física", "Pessoa Jurídica"], key="tipo_pessoa")
    col2.text_input("CPF / CNPJ", key="documento")

    status_doc, msg_doc = validar_documento_tempo_real(st.session_state.documento)
    if status_doc is True:
        st.success(msg_doc)
    elif status_doc is False:
        st.warning(msg_doc)

    consultar = st.form_submit_button("🔍 Buscar Cliente")

    if consultar:
        doc = normalizar_doc(st.session_state.documento)
        if not validar_documento(doc):
            st.error("Documento inválido.")
            st.stop()

        dados = buscar_cliente(doc)
        if dados is not None:
            st.session_state.modo             = "edicao"
            st.session_state.nome             = dados.get("Nome", "")
            st.session_state.telefone         = formatar_telefone(dados.get("Telefone", ""))
            st.session_state.resp_comercial   = dados.get("Responsavel_Comercial", "")
            st.session_state.resp_cliente     = dados.get("Responsavel_Cliente", "")
            st.session_state.resp_medicit     = dados.get("Responsavel_Medicit", "")
            st.session_state.adicional_pacote = dados.get("adicional_pacote", "")
            st.session_state.observacao       = dados.get("observacao", "")

            pac = dados.get("pacote", "")
            st.session_state.pacote = pac if pac in PACOTES_DISPONIVEIS else PACOTES_DISPONIVEIS[0]

            pri = dados.get("prioridade", "Alta")
            st.session_state.prioridade = pri if pri in PRIORIDADES else "Alta"

            st.session_state.data_ass_contrato    = parse_data(dados.get("data_ass_contrato", ""))
            st.session_state.data_prevista_inicio = parse_data(dados.get("data_prevista_inicio", ""))

            try:
                st.session_state.qtde_agendas = int(dados.get("qtde_agendas", 1))
            except Exception:
                st.session_state.qtde_agendas = 1

            try:
                st.session_state.prazo_implantacao_dias = int(dados.get("prazo_implantacao_dias", 45))
            except Exception:
                st.session_state.prazo_implantacao_dias = 45

            st.success("✅ Cliente encontrado.")
        else:
            st.session_state.modo = "novo"
            st.info("Cliente não encontrado — preencha os dados para cadastrar.")

    # --- Dados cadastrais ---
    col3, col4 = st.columns(2)
    col3.text_input("Nome / Razão Social", key="nome")
    col4.text_input("Telefone",            key="telefone")

    col5, col6 = st.columns(2)
    col5.text_input("Responsável Comercial", key="resp_comercial")
    col6.text_input("Responsável Cliente",   key="resp_cliente")
    st.text_input("Responsável Medicit",     key="resp_medicit")

    # --- Dados do Contrato ---
    st.markdown("---")
    st.markdown("#### 📄 Dados do Contrato")

    cc1, cc2 = st.columns(2)
    with cc1:
        st.date_input(
            "Data de Assinatura do Contrato",
            value=st.session_state.data_ass_contrato,
            format="DD/MM/YYYY",
            key="data_ass_contrato"
        )
        st.selectbox(
            "Pacote",
            PACOTES_DISPONIVEIS,
            index=PACOTES_DISPONIVEIS.index(st.session_state.pacote)
                  if st.session_state.pacote in PACOTES_DISPONIVEIS else 0,
            key="pacote"
        )
        st.text_input(
            "Adicional do Pacote",
            placeholder="Ex: Whats + Controle Financeiro",
            key="adicional_pacote"
        )

    with cc2:
        st.number_input(
            "Qtde de Agendas",
            min_value=1, step=1,
            value=st.session_state.qtde_agendas,
            key="qtde_agendas"
        )
        st.number_input(
            "Prazo de Implantação (dias)",
            min_value=1, step=1,
            value=st.session_state.prazo_implantacao_dias,
            key="prazo_implantacao_dias"
        )
        st.selectbox(
            "Prioridade",
            PRIORIDADES,
            index=PRIORIDADES.index(st.session_state.prioridade)
                  if st.session_state.prioridade in PRIORIDADES else 0,
            key="prioridade"
        )

    st.date_input(
        "📅 Data Prevista de Início da Implantação",
        value=st.session_state.data_prevista_inicio,
        format="DD/MM/YYYY",
        key="data_prevista_inicio"
    )
    st.text_area("Observação", key="observacao", height=80)

    # --- Botões ---
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    if st.session_state.modo == "edicao":
        salvar  = col_btn1.form_submit_button("✏️ Atualizar Cliente")
        excluir = col_btn2.form_submit_button("🗑️ Excluir Cliente")
    else:
        salvar  = col_btn1.form_submit_button("💾 Salvar Cliente")
        excluir = False

# ==============================
# EXCLUIR
# ==============================

if excluir:
    st.session_state.confirmar_exclusao = True

if st.session_state.confirmar_exclusao:
    st.warning("⚠️ Tem certeza que deseja excluir este cliente?")
    col1, col2 = st.columns(2)

    if col1.button("✅ Confirmar Exclusão"):
        doc = normalizar_doc(st.session_state.documento)
        if cliente_tem_vinculo(doc):
            st.error("❌ Este cliente possui implantação vinculada e não pode ser excluído.")
            st.stop()
        ok = deletar("clientes", "cnpj_cpf", doc)
        if ok:
            registrar_historico(
                cnpj_cpf=doc, cliente=st.session_state.nome,
                pagina="Cadastro Clientes", acao="Exclusão"
            )
            st.success("✅ Cliente excluído com sucesso.")
            st.session_state.limpar             = True
            st.session_state.confirmar_exclusao = False
            st.rerun()
        else:
            st.error("❌ Não foi possível localizar o cliente na planilha.")

    if col2.button("❌ Cancelar"):
        st.session_state.confirmar_exclusao = False

# ==============================
# SALVAR / ATUALIZAR
# ==============================

if salvar:
    doc = normalizar_doc(st.session_state.documento)

    status_doc, _ = validar_documento_tempo_real(doc)
    if status_doc is not True:
        st.error("Corrija o CPF/CNPJ antes de salvar.")
        st.stop()

    if not st.session_state.nome.strip():
        st.error("Nome é obrigatório.")
        st.stop()

    # Preserva data_conclusao_contrato já gravada
    dados_ant = buscar_cliente(doc)
    data_concl_atual = dados_ant.get("data_conclusao_contrato", "") if dados_ant else ""

    dados = {
        "Tipo_Pessoa":            st.session_state.tipo_pessoa,
        "cnpj_cpf":               doc,
        "Nome":                   st.session_state.nome.strip(),
        "Telefone":               somente_numeros(st.session_state.telefone),
        "Responsavel_Comercial":  st.session_state.resp_comercial.strip(),
        "Responsavel_Cliente":    st.session_state.resp_cliente.strip(),
        "Responsavel_Medicit":    st.session_state.resp_medicit.strip(),
        "data_ass_contrato":      st.session_state.data_ass_contrato.strftime("%d/%m/%Y")
                                  if st.session_state.data_ass_contrato else "",
        "pacote":                 st.session_state.pacote,
        "adicional_pacote":       st.session_state.adicional_pacote.strip(),
        "qtde_agendas":           str(st.session_state.qtde_agendas),
        "prazo_implantacao_dias": str(st.session_state.prazo_implantacao_dias),
        "prioridade":             st.session_state.prioridade,
        "data_prevista_inicio":   st.session_state.data_prevista_inicio.strftime("%d/%m/%Y")
                                  if st.session_state.data_prevista_inicio else "",
        "data_conclusao_contrato": data_concl_atual,
        "observacao":             st.session_state.observacao.strip()
    }

    if st.session_state.modo == "novo":
        if dados_ant is not None:
            st.error("❌ CPF/CNPJ já cadastrado.")
            st.stop()
        inserir("clientes", dados)
        registrar_historico(
            cnpj_cpf=doc, cliente=dados["Nome"],
            pagina="Cadastro Clientes", acao="Inserção"
        )
        st.success("✅ Cliente cadastrado com sucesso!")

    else:
        ok = atualizar("clientes", "cnpj_cpf", doc, dados)
        if ok:
            if dados_ant:
                for campo, novo_val in dados.items():
                    ant_val = str(dados_ant.get(campo, ""))
                    if str(novo_val) != ant_val:
                        registrar_historico(
                            cnpj_cpf=doc, cliente=dados["Nome"],
                            pagina="Cadastro Clientes", acao="Atualização",
                            campo=campo, valor_anterior=ant_val, valor_novo=str(novo_val)
                        )
            st.success("✅ Cliente atualizado com sucesso!")
        else:
            st.error("❌ Não foi possível localizar o cliente na planilha.")
            st.stop()

    st.session_state.limpar = True
    st.rerun()

# ==============================
# TABELA
# ==============================

st.subheader("📋 Clientes Cadastrados")
cols_exibir = ["Tipo_Pessoa", "cnpj_cpf", "Nome", "Telefone",
               "Responsavel_Comercial", "pacote", "prioridade"]
cols_exibir = [c for c in cols_exibir if c in df.columns]
st.dataframe(df[cols_exibir], use_container_width=True)