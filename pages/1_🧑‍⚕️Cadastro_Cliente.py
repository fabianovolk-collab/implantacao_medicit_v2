import streamlit as st
import pandas as pd
from database import carregar_clientes, salvar_clientes, carregar_implantacao

st.set_page_config(layout="wide")
st.title("👤 Cadastro de Cliente")

# ==============================
# CARREGAR BASE
# ==============================
df = carregar_clientes()
df.fillna("", inplace=True)

df_implantacao = carregar_implantacao()
df_implantacao.fillna("", inplace=True)

# ==============================
# FUNÇÕES
# ==============================

def somente_numeros(valor):
    return "".join(filter(str.isdigit, str(valor)))

def formatar_documento(valor):
    valor = somente_numeros(valor)

    if len(valor) <= 11:
        if len(valor) > 9:
            return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"
        elif len(valor) > 6:
            return f"{valor[:3]}.{valor[3:6]}.{valor[6:]}"
        elif len(valor) > 3:
            return f"{valor[:3]}.{valor[3:]}"
        return valor
    else:
        if len(valor) > 12:
            return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}"
        elif len(valor) > 8:
            return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:]}"
        elif len(valor) > 5:
            return f"{valor[:2]}.{valor[2:5]}.{valor[5:]}"
        elif len(valor) > 2:
            return f"{valor[:2]}.{valor[2:]}"
        return valor

def formatar_telefone(valor):
    valor = somente_numeros(valor)

    if len(valor) > 10:
        return f"({valor[:2]}) {valor[2]} {valor[3:7]}-{valor[7:11]}"
    elif len(valor) > 6:
        return f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
    elif len(valor) > 2:
        return f"({valor[:2]}) {valor[2:]}"
    return valor

# ==============================
# VALIDAÇÃO
# ==============================

def validar_cpf(cpf):
    cpf = somente_numeros(cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10

    return cpf[-2:] == f"{dig1}{dig2}"

def validar_cnpj(cnpj):
    cnpj = somente_numeros(cnpj)

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_digito(cnpj, pesos):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1

    dig1 = calc_digito(cnpj[:12], pesos1)
    dig2 = calc_digito(cnpj[:13], pesos2)

    return cnpj[-2:] == dig1 + dig2

def validar_documento(doc):
    doc = somente_numeros(doc)
    return validar_cpf(doc) if len(doc) <= 11 else validar_cnpj(doc)

# ==============================
# BUSCA
# ==============================

def buscar_cliente(df, doc):
    df["CNPJ_CPF"] = df["CNPJ_CPF"].astype(str)
    res = df[df["CNPJ_CPF"] == doc]
    return res.iloc[0] if not res.empty else None

def cliente_tem_vinculo(doc):
    doc = somente_numeros(doc)
    if "CNPJ_CPF" in df_implantacao.columns:
        return not df_implantacao[df_implantacao["CNPJ_CPF"].astype(str) == doc].empty
    return False

# ==============================
# SESSION STATE
# ==============================

def init_state():
    defaults = {
        "tipo_pessoa": "Pessoa Física",
        "documento": "",
        "nome": "",
        "telefone": "",
        "resp_comercial": "",
        "resp_cliente": "",
        "resp_medicit": "",
        "modo": "novo",
        "load_data": False,
        "data_loaded": None,
        "limpar": False,
        "confirmar_exclusao": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ==============================
# RESET
# ==============================

if st.session_state.limpar:
    for campo in ["documento","nome","telefone","resp_comercial","resp_cliente","resp_medicit"]:
        st.session_state[campo] = ""
    st.session_state.modo = "novo"
    st.session_state.limpar = False

# ==============================
# LOAD CONTROLADO
# ==============================

if st.session_state.load_data and st.session_state.data_loaded is not None:
    dados = st.session_state.data_loaded

    st.session_state.tipo_pessoa = dados.get("Tipo_Pessoa", "Pessoa Física")
    st.session_state.documento = formatar_documento(dados.get("CNPJ_CPF", ""))
    st.session_state.nome = dados.get("Nome", "")
    st.session_state.telefone = formatar_telefone(dados.get("Telefone", ""))
    st.session_state.resp_comercial = dados.get("Responsavel_Comercial", "")
    st.session_state.resp_cliente = dados.get("Responsavel_Cliente", "")
    st.session_state.resp_medicit = dados.get("Responsavel_Medicit", "")

    st.session_state.load_data = False
    st.session_state.data_loaded = None

# ==============================
# FORMULÁRIO
# ==============================

st.subheader("➕ Cadastro / Edição de Cliente")

with st.form("form_cliente"):

    col1, col2 = st.columns(2)

    col1.selectbox("Tipo de Pessoa", ["Pessoa Física", "Pessoa Jurídica"], key="tipo_pessoa")
    col2.text_input("CPF / CNPJ", key="documento")

    consultar = st.form_submit_button("🔍 Buscar Cliente")

    if consultar:
        doc = somente_numeros(st.session_state.documento)

        if not doc:
            st.error("Informe CPF ou CNPJ")
            st.stop()

        if not validar_documento(doc):
            st.error("CPF ou CNPJ inválido")
            st.stop()

        dados = buscar_cliente(df, doc)

        if dados is not None:
            st.session_state.modo = "edicao"
            st.session_state.load_data = True
            st.session_state.data_loaded = dados.to_dict()
            st.success("Cliente encontrado — carregando dados...")
            st.rerun()
        else:
            # 🔥 CORREÇÃO AQUI
            st.session_state.modo = "novo"
            st.session_state.nome = ""
            st.session_state.telefone = ""
            st.session_state.resp_comercial = ""
            st.session_state.resp_cliente = ""
            st.session_state.resp_medicit = ""

            st.info("Cliente não encontrado — preencha para cadastrar")

    col3, col4 = st.columns(2)
    col3.text_input("Nome / Razão Social", key="nome")
    col4.text_input("Telefone", key="telefone")

    col5, col6 = st.columns(2)
    col5.text_input("Responsável Comercial", key="resp_comercial")
    col6.text_input("Responsável Cliente", key="resp_cliente")

    st.text_input("Responsável Medicit", key="resp_medicit")

    col_btn1, col_btn2 = st.columns(2)

    if st.session_state.modo == "edicao":
        salvar = col_btn1.form_submit_button("✏️ Atualizar Cliente")
        excluir = col_btn2.form_submit_button("🗑️ Excluir Cliente")
    else:
        salvar = col_btn1.form_submit_button("💾 Salvar Cliente")
        excluir = False

# ==============================
# EXCLUIR COM CONFIRMAÇÃO
# ==============================

if excluir:
    st.session_state.confirmar_exclusao = True

if st.session_state.confirmar_exclusao:
    st.warning("⚠️ Tem certeza que deseja excluir este cliente?")

    col1, col2 = st.columns(2)

    if col1.button("✅ Confirmar Exclusão"):
        doc = somente_numeros(st.session_state.documento)

        if cliente_tem_vinculo(doc):
            st.error("❌ Cliente possui implantação vinculada")
            st.session_state.confirmar_exclusao = False
            st.stop()

        df = df[df["CNPJ_CPF"].astype(str) != doc]
        salvar_clientes(df)

        st.success("Cliente excluído com sucesso")

        st.session_state.confirmar_exclusao = False
        st.session_state.limpar = True
        st.rerun()

    if col2.button("❌ Cancelar"):
        st.session_state.confirmar_exclusao = False

# ==============================
# SALVAR
# ==============================

if salvar:
    doc = somente_numeros(st.session_state.documento)

    if not doc or not st.session_state.nome:
        st.error("Preencha CPF/CNPJ e Nome")
        st.stop()

    if not validar_documento(doc):
        st.error("CPF ou CNPJ inválido")
        st.stop()

    dados_existente = buscar_cliente(df, doc)

    if st.session_state.modo == "novo":

        if dados_existente is not None:
            st.error("CPF/CNPJ já cadastrado")
            st.stop()

        novo = pd.DataFrame([{
            "Tipo_Pessoa": st.session_state.tipo_pessoa,
            "CNPJ_CPF": doc,
            "Nome": st.session_state.nome,
            "Telefone": somente_numeros(st.session_state.telefone),
            "Responsavel_Comercial": st.session_state.resp_comercial,
            "Responsavel_Cliente": st.session_state.resp_cliente,
            "Responsavel_Medicit": st.session_state.resp_medicit
        }])

        df = pd.concat([df, novo], ignore_index=True)
        salvar_clientes(df)

        st.success("Cliente cadastrado com sucesso")

    else:
        idx = df[df["CNPJ_CPF"] == doc].index[0]

        df.at[idx, "Tipo_Pessoa"] = st.session_state.tipo_pessoa
        df.at[idx, "Nome"] = st.session_state.nome
        df.at[idx, "Telefone"] = somente_numeros(st.session_state.telefone)
        df.at[idx, "Responsavel_Comercial"] = st.session_state.resp_comercial
        df.at[idx, "Responsavel_Cliente"] = st.session_state.resp_cliente
        df.at[idx, "Responsavel_Medicit"] = st.session_state.resp_medicit

        salvar_clientes(df)

        st.success("Cliente atualizado com sucesso")

    st.session_state.limpar = True
    st.rerun()

# ==============================
# TABELA
# ==============================
st.subheader("📋 Clientes")
st.dataframe(df, use_container_width=True)