import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import (
    carregar_clientes, carregar_etapas, carregar_implantacao,
    atualizar, inserir, registrar_historico,
    normalizar_doc, formatar_data_br, parse_data, CHECKLIST_SEP
)

st.set_page_config(layout="wide")
st.title("✅ Gestão de Implantação")

STATUS_PADRAO      = ["Não iniciado", "Em andamento", "Bloqueio/Pendente", "Concluído"]
DIAS_ALERTA_RISCO  = 7
DIAS_ALERTA_ATRASO = 15

# ==============================
# FUNÇÕES DE ALERTA
# ==============================

def dias_sem_atualizacao(ultima_str):
    dt = parse_data(ultima_str)
    return (date.today() - dt).days if dt else None

def prazo_ultrapassado(data_str, status):
    if status == "Concluído":
        return False
    dt = parse_data(data_str)
    return dt is not None and dt < date.today()

def nivel_alerta(row):
    status = str(row.get("status", ""))
    if status == "Concluído":
        return None
    if status == "Bloqueio/Pendente":
        return "bloqueio"
    if prazo_ultrapassado(row.get("data_conclusao", ""), status):
        return "atraso"
    dias = dias_sem_atualizacao(row.get("ultima_atualizacao", ""))
    if dias is not None and dias >= DIAS_ALERTA_ATRASO:
        return "atraso"
    if dias is not None and dias >= DIAS_ALERTA_RISCO:
        return "risco"
    return None

# ==============================
# LIMPAR TUDO RELACIONADO A UM CLIENTE
# Garante que ao trocar de cliente nenhum dado antigo persista
# ==============================

def limpar_dados_cliente(cnpj):
    """Remove do session_state todos os widgets vinculados a este cliente."""
    prefixos = [
        f"impl_check_{cnpj}_",
        f"impl_status_{cnpj}_",
        f"impl_di_{cnpj}_",
        f"impl_dc_{cnpj}_",
        f"impl_rmed_{cnpj}_",
        f"impl_rcli_{cnpj}_",
        f"impl_part_{cnpj}_",
        f"impl_motivo_{cnpj}_",
        f"impl_proxac_{cnpj}_",
        f"impl_etapa_{cnpj}",
    ]
    keys_remover = [
        k for k in list(st.session_state.keys())
        if any(k.startswith(p) for p in prefixos)
    ]
    for k in keys_remover:
        del st.session_state[k]

def limpar_formulario_etapa(cnpj, etapa):
    """Remove do session_state apenas os widgets de uma etapa específica."""
    prefixos = [
        f"impl_check_{cnpj}_{etapa}_",
        f"impl_status_{cnpj}_{etapa}",
        f"impl_di_{cnpj}_{etapa}",
        f"impl_dc_{cnpj}_{etapa}",
        f"impl_rmed_{cnpj}_{etapa}",
        f"impl_rcli_{cnpj}_{etapa}",
        f"impl_part_{cnpj}_{etapa}",
        f"impl_motivo_{cnpj}_{etapa}",
        f"impl_proxac_{cnpj}_{etapa}",
    ]
    keys_remover = [
        k for k in list(st.session_state.keys())
        if any(k.startswith(p) for p in prefixos)
    ]
    for k in keys_remover:
        del st.session_state[k]

# ==============================
# CARREGAR BASE
# ==============================

df_clientes = carregar_clientes().fillna("")
df_clientes["cnpj_cpf"] = df_clientes["cnpj_cpf"].apply(normalizar_doc)
df_etapas   = carregar_etapas()

if "importado_etapas" not in st.session_state:
    st.session_state["importado_etapas"] = {}

# ==============================
# BUSCA DE CLIENTE
# Inicia sem nenhum cliente selecionado
# ==============================

st.subheader("🔍 Selecionar Cliente")
search = st.text_input("Digite CNPJ/CPF ou Nome para filtrar", key="impl_search")

clientes_filtrados = df_clientes.copy()
if search:
    clientes_filtrados = df_clientes[
        df_clientes["cnpj_cpf"].str.contains(search.strip()) |
        df_clientes["Nome"].str.lower().str.contains(search.lower())
    ]

if clientes_filtrados.empty:
    st.warning("Nenhum cliente encontrado.")
    st.stop()

# Opção vazia no topo — página abre sem cliente selecionado
opcoes = ["-- Selecione um cliente --"] + [
    f"{row['Nome']} ({row['cnpj_cpf']})"
    for _, row in clientes_filtrados.iterrows()
]

selecionado = st.selectbox("Cliente", opcoes, key="impl_select")

if selecionado == "-- Selecione um cliente --":
    st.info("Selecione um cliente para continuar.")
    st.stop()

cnpj_cliente  = selecionado.split("(")[-1].replace(")", "")
cliente_sel   = selecionado.split(" (")[0]
chave_cliente = normalizar_doc(cnpj_cliente)

# ==============================
# DETECTAR TROCA DE CLIENTE
# Limpa todos os dados do cliente anterior do session_state
# ==============================

cliente_anterior = st.session_state.get("impl_cliente_ativo", None)

if cliente_anterior != chave_cliente:
    # Limpa dados do cliente anterior
    if cliente_anterior:
        limpar_dados_cliente(cliente_anterior)
    # Registra o novo cliente ativo
    st.session_state["impl_cliente_ativo"] = chave_cliente

# ==============================
# PAINEL DE ALERTAS DO CLIENTE
# ==============================

df_impl_view = carregar_implantacao().fillna("")
df_impl_view["cnpj_cpf"] = df_impl_view["cnpj_cpf"].apply(normalizar_doc)
df_impl_view["etapa"]    = df_impl_view["etapa"].astype(str).str.strip()

registros_cliente = df_impl_view[df_impl_view["cnpj_cpf"] == chave_cliente]

alertas_cliente = []
for _, row in registros_cliente.iterrows():
    n = nivel_alerta(row)
    if n:
        alertas_cliente.append({
            "nivel":  n,
            "etapa":  row.get("etapa", ""),
            "status": row.get("status", ""),
            "dias":   dias_sem_atualizacao(row.get("ultima_atualizacao", "")),
            "prazo":  row.get("data_conclusao", "")
        })

if alertas_cliente:
    st.markdown("#### 🔔 Alertas deste cliente")
    for a in sorted(alertas_cliente,
                    key=lambda x: {"bloqueio":0,"atraso":1,"risco":2}.get(x["nivel"],3)):
        icone = {"bloqueio":"🚨","atraso":"⏰","risco":"⚠️"}.get(a["nivel"],"")
        if a["nivel"] == "bloqueio":
            st.error(f"{icone} **{a['etapa']}** — {a['status']}")
        elif a["nivel"] == "atraso":
            msg = (f"prazo estourado ({a['prazo']})"
                   if prazo_ultrapassado(a["prazo"], a["status"])
                   else f"{a['dias']} dias sem atualização")
            st.warning(f"{icone} **{a['etapa']}** — {msg}")
        else:
            st.info(f"{icone} **{a['etapa']}** — {a['dias']} dias sem atualização")

# ==============================
# IMPORTAÇÃO DE ARQUIVO DE RETORNO
# ==============================

st.subheader("📥 Importar Planilha de Retorno")
uploaded_file = st.file_uploader(
    "Selecione o arquivo Excel", type=["xlsx"], key="impl_upload"
)

if uploaded_file is not None:
    try:
        df_ret = pd.read_excel(uploaded_file).fillna("")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        df_ret = pd.DataFrame()

    if not df_ret.empty:
        if "Chave" not in df_ret.columns or "cnpj_cpf" not in df_ret.columns:
            st.error("O arquivo deve conter as colunas 'Chave' e 'cnpj_cpf'.")
        else:
            cpfs = df_ret["cnpj_cpf"].apply(normalizar_doc).unique()
            if any(cpf != chave_cliente for cpf in cpfs):
                st.error("❌ O arquivo contém registros de outro cliente.")
            else:
                df_impl_fresh = carregar_implantacao().fillna("")
                df_impl_fresh["cnpj_cpf"] = df_impl_fresh["cnpj_cpf"].apply(normalizar_doc)
                etapas_cli = df_impl_fresh[df_impl_fresh["cnpj_cpf"] == chave_cliente]
                etapas_iniciadas = etapas_cli[
                    ~etapas_cli["status"].isin(["Não iniciado", ""])
                ]

                if not etapas_iniciadas.empty:
                    st.warning(
                        "⚠️ **Importação bloqueada.** Este cliente já possui etapas "
                        "em andamento ou concluídas. A importação só é permitida antes "
                        "de qualquer etapa ser iniciada."
                    )
                    st.markdown("**Etapas com progresso registrado:**")
                    for _, e in etapas_iniciadas.iterrows():
                        st.write(f"- **{e['etapa']}**: {e['status']}")

                elif st.session_state["importado_etapas"].get(chave_cliente):
                    st.info("ℹ️ Arquivo já importado para este cliente nesta sessão.")

                else:
                    with st.spinner("Importando registros..."):
                        chaves_existentes = df_impl_fresh["chave"].tolist()
                        total     = len(df_ret)
                        progresso = st.progress(0)

                        for i, row in enumerate(df_ret.itertuples(), 1):
                            chave     = str(getattr(row, "Chave", "")).strip()
                            cnpj_row  = normalizar_doc(str(getattr(row, "cnpj_cpf", "")))
                            data_ini  = formatar_data_br(str(getattr(row, "Data_Inicio", "")))
                            data_conc = formatar_data_br(str(getattr(row, "Data_Conclusao", "")))
                            resp_cli  = str(getattr(row, "Responsavel_Clinica", ""))
                            partic    = str(getattr(row, "Participantes", ""))

                            if chave in chaves_existentes:
                                existente = df_impl_fresh[
                                    df_impl_fresh["chave"] == chave
                                ].iloc[0].to_dict()
                                existente["checklist"]           = ""
                                existente["responsavel_cliente"] = resp_cli
                                existente["participantes"]       = partic
                                existente["data_inicio"]         = data_ini
                                existente["data_conclusao"]      = data_conc
                                existente["ultima_atualizacao"]  = datetime.now().strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                )
                                atualizar("implantacao", "chave", chave, existente)
                            else:
                                inserir("implantacao", {
                                    "chave":               chave,
                                    "cnpj_cpf":            cnpj_row,
                                    "cliente":             str(getattr(row, "Cliente", "")),
                                    "etapa":               str(getattr(row, "Etapa", "")),
                                    "status":              str(getattr(row, "Status", "Não iniciado")),
                                    "data_inicio":         data_ini,
                                    "checklist":           "",
                                    "responsavel_medicit": str(getattr(row, "Responsavel_Medicit", "")),
                                    "responsavel_cliente": resp_cli,
                                    "participantes":       partic,
                                    "motivo":              str(getattr(row, "Motivo", "")),
                                    "proxima_acao":        str(getattr(row, "Proxima_Acao", "")),
                                    "data_conclusao":      data_conc,
                                    "ultima_atualizacao":  datetime.now().strftime(
                                        "%d/%m/%Y %H:%M:%S"
                                    )
                                })

                            progresso.progress(int(i / total * 100))

                        # Limpa session_state deste cliente para forçar
                        # releitura do banco na próxima abertura de etapa
                        limpar_dados_cliente(chave_cliente)

                        registrar_historico(
                            cnpj_cpf=chave_cliente, cliente=cliente_sel,
                            pagina="Gestão Implantação", acao="Importação de planilha"
                        )
                        st.success("✅ Importação concluída!")
                        st.session_state["importado_etapas"][chave_cliente] = True

# ==============================
# SELEÇÃO DE ETAPA
# ==============================

st.subheader("📌 Selecionar Etapa")
etapa_selecionada = None

if not df_etapas.empty:
    etapas_disponiveis = (
        df_etapas[["etapa", "ordem_etapa"]]
        .drop_duplicates()
        .sort_values("ordem_etapa")
    )

    df_impl2 = carregar_implantacao().fillna("")
    df_impl2["cnpj_cpf"] = df_impl2["cnpj_cpf"].apply(normalizar_doc)
    etapas_importadas = (
        df_impl2[df_impl2["cnpj_cpf"] == chave_cliente]["etapa"].unique().tolist()
    )

    alerta_por_etapa = {a["etapa"]: a["nivel"] for a in alertas_cliente}
    icone_alerta     = {"bloqueio": " 🚨", "atraso": " ⏰", "risco": " ⚠️"}

    labels_etapa = []
    for etapa in etapas_disponiveis["etapa"].tolist():
        sufixo  = " ✅" if etapa in etapas_importadas else ""
        sufixo += icone_alerta.get(alerta_por_etapa.get(etapa, ""), "")
        labels_etapa.append(f"{etapa}{sufixo}")

    # Chave inclui o cliente → selectbox reseta automaticamente ao trocar
    idx_sel = st.selectbox(
        "Etapas disponíveis",
        range(len(etapas_disponiveis)),
        format_func=lambda i: labels_etapa[i],
        key=f"impl_etapa_{chave_cliente}"
    )
    etapa_selecionada = etapas_disponiveis["etapa"].tolist()[idx_sel]

# ==============================
# FORMULÁRIO DE REGISTRO
# ==============================

if not (cliente_sel and etapa_selecionada):
    st.stop()

# Chaves únicas por cliente + etapa
k_status = f"impl_status_{chave_cliente}_{etapa_selecionada}"
k_di     = f"impl_di_{chave_cliente}_{etapa_selecionada}"
k_dc     = f"impl_dc_{chave_cliente}_{etapa_selecionada}"
k_rmed   = f"impl_rmed_{chave_cliente}_{etapa_selecionada}"
k_rcli   = f"impl_rcli_{chave_cliente}_{etapa_selecionada}"
k_part   = f"impl_part_{chave_cliente}_{etapa_selecionada}"
k_motivo = f"impl_motivo_{chave_cliente}_{etapa_selecionada}"
k_proxac = f"impl_proxac_{chave_cliente}_{etapa_selecionada}"

df_itens = df_etapas[df_etapas["etapa"] == etapa_selecionada].sort_values("ordem_item")

# Lê dados do banco para este cliente + etapa
df_impl = carregar_implantacao().fillna("")
df_impl["cnpj_cpf"] = df_impl["cnpj_cpf"].apply(normalizar_doc)
df_impl["etapa"]    = df_impl["etapa"].astype(str).str.strip()

registro_existente = df_impl[
    (df_impl["cnpj_cpf"] == chave_cliente) &
    (df_impl["etapa"]    == etapa_selecionada)
]

# Alerta do registro atual
if not registro_existente.empty:
    n = nivel_alerta(registro_existente.iloc[0])
    if n == "bloqueio":
        st.error("🚨 Esta etapa está com bloqueio/pendência.")
    elif n == "atraso":
        st.warning("⏰ Esta etapa está atrasada.")
    elif n == "risco":
        st.info("⚠️ Esta etapa está sem atualização há mais de 7 dias.")

# Valores vindos do banco
v = {
    "status":        "Não iniciado",
    "data_inicio":   date.today(),
    "data_conclusao": None,
    "resp_medicit":  "",
    "resp_cliente":  "",
    "participantes": "",
    "motivo":        "",
    "proxima_acao":  "",
    "check_status":  {}
}

if not registro_existente.empty:
    reg = registro_existente.iloc[0]
    v["status"]        = reg.get("status", "Não iniciado")
    v["resp_medicit"]  = reg.get("responsavel_medicit", "")
    v["resp_cliente"]  = reg.get("responsavel_cliente", "")
    v["participantes"] = reg.get("participantes", "")
    v["motivo"]        = reg.get("motivo", "")
    v["proxima_acao"]  = reg.get("proxima_acao", "")
    v["data_inicio"]   = parse_data(reg.get("data_inicio", "")) or date.today()
    v["data_conclusao"] = parse_data(reg.get("data_conclusao", ""))
    v["check_status"]  = {
        item: True
        for item in reg.get("checklist", "").split(CHECKLIST_SEP) if item
    }

# ── Inicializa session_state do formulário sempre do banco ──
# (não usa "if k not in session_state" para garantir que trocar
#  de etapa ou importar sempre reflita os dados reais do banco)
st.session_state[k_status] = (
    v["status"] if v["status"] in STATUS_PADRAO else "Não iniciado"
)
st.session_state[k_di]     = v["data_inicio"]
st.session_state[k_dc]     = v["data_conclusao"]
st.session_state[k_rmed]   = v["resp_medicit"]
st.session_state[k_rcli]   = v["resp_cliente"]
st.session_state[k_part]   = v["participantes"]
st.session_state[k_motivo] = v["motivo"]
st.session_state[k_proxac] = v["proxima_acao"]

# ==============================
# CHECKLIST
# Sempre inicializado do banco — nunca herda de outro cliente
# ==============================

st.subheader(f"📝 Checklist — {etapa_selecionada}")
checklist_itens = []
itens_lista = (
    df_itens[df_itens["item"].astype(str).str.strip() != ""]["item"].tolist()
)

for idx, item in enumerate(itens_lista):
    k_check = f"impl_check_{chave_cliente}_{etapa_selecionada}_{idx}"
    # Sempre inicializa do banco — garante isolamento por cliente
    st.session_state[k_check] = v["check_status"].get(item, False)
    checked = st.checkbox(item, key=k_check)
    if checked:
        checklist_itens.append(item)

total_itens    = len(itens_lista)
pct            = int(len(checklist_itens) / total_itens * 100) if total_itens > 0 else 0
todos_marcados = total_itens > 0 and len(checklist_itens) == total_itens

st.progress(pct / 100)
st.caption(f"{len(checklist_itens)} de {total_itens} itens marcados ({pct}%)")

# Quando todos marcados → força Concluído e data de hoje
if todos_marcados:
    st.session_state[k_status] = "Concluído"
    if st.session_state.get(k_dc) is None:
        st.session_state[k_dc] = date.today()
    if v["status"] != "Concluído":
        st.success("✅ Todos os itens marcados — status atualizado para **Concluído**.")

# ==============================
# CAMPOS DO FORMULÁRIO
# ==============================

col1, col2, col3 = st.columns(3)
with col1:
    status = st.selectbox("Status", STATUS_PADRAO, key=k_status)
with col2:
    data_inicio = st.date_input("Data de Início", format="DD/MM/YYYY", key=k_di)
with col3:
    resp_medicit = st.text_input("Responsável Medicit", key=k_rmed)

col4, col5 = st.columns(2)
with col4:
    resp_cliente = st.text_input("Responsável Cliente", key=k_rcli)
with col5:
    participantes = st.text_input("Participantes", key=k_part)

motivo = st.text_input("Motivo / Observação", key=k_motivo)

col6, col7 = st.columns(2)
with col6:
    proxima_acao = st.text_input("Próxima Ação", key=k_proxac)
with col7:
    # Sugere hoje quando status Concluído e data ainda não definida
    if status == "Concluído" and st.session_state.get(k_dc) is None:
        st.session_state[k_dc] = date.today()
    data_conclusao = st.date_input("Data de Conclusão", format="DD/MM/YYYY", key=k_dc)

# ==============================
# SALVAR
# ==============================

if st.button("💾 Salvar Implantação", key="impl_salvar"):
    chave = f"{chave_cliente}||{etapa_selecionada}"

    novo_registro = {
        "chave":               chave,
        "cnpj_cpf":            chave_cliente,
        "cliente":             cliente_sel,
        "etapa":               etapa_selecionada,
        "status":              status,
        "data_inicio":         data_inicio.strftime("%d/%m/%Y") if data_inicio else "",
        "checklist":           CHECKLIST_SEP.join(checklist_itens),
        "responsavel_medicit": resp_medicit,
        "responsavel_cliente": resp_cliente,
        "participantes":       participantes,
        "motivo":              motivo,
        "proxima_acao":        proxima_acao,
        "ultima_atualizacao":  datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "data_conclusao":      data_conclusao.strftime("%d/%m/%Y") if data_conclusao else ""
    }

    existia = not registro_existente.empty
    if existia:
        ok   = atualizar("implantacao", "chave", chave, novo_registro)
        acao = "Atualização"
    else:
        inserir("implantacao", novo_registro)
        ok   = True
        acao = "Inserção"

    if ok or not existia:
        registrar_historico(
            cnpj_cpf=chave_cliente, cliente=cliente_sel,
            pagina="Gestão Implantação", acao=acao,
            etapa=etapa_selecionada, campo="status",
            valor_anterior=v["status"], valor_novo=status
        )
        st.success(f"✅ Implantação {'atualizada' if existia else 'cadastrada'} com sucesso!")
        # Limpa session_state desta etapa para forçar releitura do banco
        limpar_formulario_etapa(chave_cliente, etapa_selecionada)
        st.rerun()
    else:
        st.error("❌ Erro ao salvar. Tente novamente.")