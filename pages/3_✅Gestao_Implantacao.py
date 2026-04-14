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
# CHAVE DE CONTEXTO ATIVO
# Identifica qual combinação cliente+etapa está carregada no form
# ==============================

def chave_contexto(cnpj, etapa):
    return f"{cnpj}||{etapa}"

def inicializar_formulario(cnpj, etapa, v):
    """
    Inicializa os widgets do formulário a partir dos dados do banco.
    Só executa quando o contexto (cliente+etapa) muda.
    Retorna True se houve inicialização (contexto novo), False se já estava carregado.
    O chamador deve fazer st.rerun() quando retornar True para que os widgets
    sejam renderizados com os valores corretos do session_state.
    """
    ctx = chave_contexto(cnpj, etapa)
    if st.session_state.get("impl_contexto_ativo") == ctx:
        return False  # mesmo contexto → não reinicializa → usuário edita livremente

    # Contexto novo → carrega dados do banco
    st.session_state["impl_contexto_ativo"] = ctx

    k = lambda campo: f"impl_{campo}_{cnpj}_{etapa}"

    st.session_state[k("status")] = (
        v["status"] if v["status"] in STATUS_PADRAO else "Não iniciado"
    )
    st.session_state[k("di")]     = v["data_inicio"]
    st.session_state[k("dc")]     = v["data_conclusao"]
    st.session_state[k("rmed")]   = v["resp_medicit"]
    st.session_state[k("rcli")]   = v["resp_cliente"]
    st.session_state[k("part")]   = v["participantes"]
    st.session_state[k("motivo")] = v["motivo"]
    st.session_state[k("proxac")] = v["proxima_acao"]

    # Checkboxes inicializados do banco
    itens = v.get("itens_lista", [])
    for idx, item in enumerate(itens):
        st.session_state[f"impl_check_{cnpj}_{etapa}_{idx}"] = (
            v["check_status"].get(item, False)
        )

    return True  # contexto novo → chamador deve fazer st.rerun()

def limpar_contexto():
    """Chamado após salvar ou ao trocar de cliente, força releitura do banco."""
    if "impl_contexto_ativo" in st.session_state:
        del st.session_state["impl_contexto_ativo"]

# ==============================
# CARREGAR BASE
# ==============================

df_clientes = carregar_clientes().fillna("")
df_clientes["cnpj_cpf"] = df_clientes["cnpj_cpf"].apply(normalizar_doc)
df_etapas   = carregar_etapas()

if "importado_etapas" not in st.session_state:
    st.session_state["importado_etapas"] = {}

# ==============================
# BUSCA DE CLIENTE — abre sem seleção
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

# Detecta troca de cliente → limpa contexto para forçar releitura do banco
if st.session_state.get("impl_cliente_ativo") != chave_cliente:
    st.session_state["impl_cliente_ativo"] = chave_cliente
    limpar_contexto()

# ==============================
# ALERTAS DO CLIENTE
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
# RESPONSÁVEIS DO CADASTRO
# ==============================

dados_cadastro_cli = df_clientes[df_clientes["cnpj_cpf"] == chave_cliente]
resp_med_cadastro  = dados_cadastro_cli.iloc[0].get("Responsavel_Medicit", "") \
                     if not dados_cadastro_cli.empty else ""
resp_cli_cadastro  = dados_cadastro_cli.iloc[0].get("Responsavel_Cliente", "") \
                     if not dados_cadastro_cli.empty else ""

# ==============================
# IMPORTAÇÃO — ativada por toggle
# ==============================

habilitar_importacao = st.checkbox(
    "📥 Importar Planilha de Retorno",
    value=False,
    key=f"impl_habilitar_importacao_{chave_cliente}"
)

if habilitar_importacao:
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx)",
        type=["xlsx"],
        key="impl_upload"
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
                    etapas_cli       = df_impl_fresh[df_impl_fresh["cnpj_cpf"] == chave_cliente]
                    etapas_iniciadas = etapas_cli[~etapas_cli["status"].isin(["Não iniciado", ""])]

                    if not etapas_iniciadas.empty:
                        st.warning(
                            "⚠️ **Importação bloqueada.** Este cliente já possui etapas "
                            "em andamento ou concluídas."
                        )
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
                                    existente.update({
                                        "checklist":           "",
                                        "responsavel_cliente": resp_cli,
                                        "participantes":       partic,
                                        "data_inicio":         data_ini,
                                        "data_conclusao":      data_conc,
                                        "ultima_atualizacao":  datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                    })
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
                                        "ultima_atualizacao":  datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                    })
                                progresso.progress(int(i / total * 100))

                            limpar_contexto()
                            registrar_historico(
                                cnpj_cpf=chave_cliente, cliente=cliente_sel,
                                pagina="Gestão Implantação", acao="Importação de planilha"
                            )
                            st.success("✅ Importação concluída!")
                            st.session_state["importado_etapas"][chave_cliente] = True

# ==============================
# SELEÇÃO DE ETAPA
# Auto-seleciona a próxima etapa não concluída
# ==============================

st.subheader("📌 Selecionar Etapa")
etapa_selecionada = None

if df_etapas.empty:
    st.warning("Nenhuma etapa cadastrada.")
    st.stop()

etapas_disponiveis = (
    df_etapas[["etapa", "ordem_etapa"]]
    .drop_duplicates()
    .sort_values("ordem_etapa")
)
lista_etapas = etapas_disponiveis["etapa"].tolist()

df_impl2 = carregar_implantacao().fillna("")
df_impl2["cnpj_cpf"] = df_impl2["cnpj_cpf"].apply(normalizar_doc)
df_impl2["etapa"]    = df_impl2["etapa"].astype(str).str.strip()
etapas_cliente_df   = df_impl2[df_impl2["cnpj_cpf"] == chave_cliente]
etapas_importadas   = etapas_cliente_df["etapa"].unique().tolist()

# Status por etapa para o badge e para auto-seleção
status_por_etapa = {
    row["etapa"]: row["status"]
    for _, row in etapas_cliente_df.iterrows()
}

# Determina o índice padrão: primeira etapa não concluída
idx_padrao = 0
for i, etapa in enumerate(lista_etapas):
    s = str(status_por_etapa.get(etapa, "")).strip().lower()
    if s not in {"concluído", "concluida", "concluída", "concluido"}:
        idx_padrao = i
        break

alerta_por_etapa = {a["etapa"]: a["nivel"] for a in alertas_cliente}
icone_alerta     = {"bloqueio": " 🚨", "atraso": " ⏰", "risco": " ⚠️"}

labels_etapa = []
for etapa in lista_etapas:
    s      = str(status_por_etapa.get(etapa, "")).strip().lower()
    concl  = s in {"concluído", "concluida", "concluída", "concluido"}
    badge  = " ✅" if concl else (" ✔" if etapa in etapas_importadas else "")
    badge += icone_alerta.get(alerta_por_etapa.get(etapa, ""), "")
    labels_etapa.append(f"{etapa}{badge}")

# Chave inclui cliente → selectbox reseta ao trocar cliente
k_etapa_sel = f"impl_etapa_sel_{chave_cliente}"
if k_etapa_sel not in st.session_state:
    st.session_state[k_etapa_sel] = idx_padrao

idx_sel = st.selectbox(
    "Etapas disponíveis",
    range(len(lista_etapas)),
    format_func=lambda i: labels_etapa[i],
    key=k_etapa_sel
)
etapa_selecionada = lista_etapas[idx_sel]

# Detecta troca de etapa → limpa contexto para forçar releitura do banco
ctx_atual = chave_contexto(chave_cliente, etapa_selecionada)
if st.session_state.get("impl_contexto_ativo") != ctx_atual:
    limpar_contexto()

# ==============================
# CARREGAR DADOS DA ETAPA SELECIONADA
# ==============================

df_itens = df_etapas[df_etapas["etapa"] == etapa_selecionada].sort_values("ordem_item")
itens_lista = df_itens[df_itens["item"].astype(str).str.strip() != ""]["item"].tolist()

df_impl = carregar_implantacao().fillna("")
df_impl["cnpj_cpf"] = df_impl["cnpj_cpf"].apply(normalizar_doc)
df_impl["etapa"]    = df_impl["etapa"].astype(str).str.strip()

registro_existente = df_impl[
    (df_impl["cnpj_cpf"] == chave_cliente) &
    (df_impl["etapa"]    == etapa_selecionada)
]

# Alerta visual
if not registro_existente.empty:
    n = nivel_alerta(registro_existente.iloc[0])
    if n == "bloqueio":
        st.error("🚨 Esta etapa está com bloqueio/pendência.")
    elif n == "atraso":
        st.warning("⏰ Esta etapa está atrasada.")
    elif n == "risco":
        st.info("⚠️ Esta etapa está sem atualização há mais de 7 dias.")

# Valores do banco
# Responsáveis padrão vêm do cadastro do cliente quando etapa ainda não tem registro
v = {
    "status":        "Não iniciado",
    "data_inicio":   date.today(),
    "data_conclusao": None,
    "resp_medicit":  resp_med_cadastro,   # pré-preenchido do cadastro
    "resp_cliente":  resp_cli_cadastro,   # pré-preenchido do cadastro
    "participantes": "",
    "motivo":        "",
    "proxima_acao":  "",
    "check_status":  {},
    "itens_lista":   itens_lista
}

if not registro_existente.empty:
    reg = registro_existente.iloc[0]
    # Se já tem registro salvo, usa os valores do banco (podem ter sido ajustados)
    v.update({
        "status":        reg.get("status", "Não iniciado"),
        "resp_medicit":  reg.get("responsavel_medicit", "") or resp_med_cadastro,
        "resp_cliente":  reg.get("responsavel_cliente", "") or resp_cli_cadastro,
        "participantes": reg.get("participantes", ""),
        "motivo":        reg.get("motivo", ""),
        "proxima_acao":  reg.get("proxima_acao", ""),
        "data_inicio":   parse_data(reg.get("data_inicio", "")) or date.today(),
        "data_conclusao": parse_data(reg.get("data_conclusao", "")),
        "check_status":  {
            item: True
            for item in reg.get("checklist", "").split(CHECKLIST_SEP) if item
        }
    })

# Inicializa form apenas quando muda de contexto (cliente ou etapa).
# Se houve inicialização (contexto novo), faz rerun para que os widgets
# sejam renderizados com os valores corretos — sem isso os campos aparecem
# vazios na primeira abertura e o usuário precisa trocar de etapa para carregar.
if inicializar_formulario(chave_cliente, etapa_selecionada, v):
    st.rerun()

# ==============================
# CHECKLIST
# Os checkboxes agora LEEM do session_state (já inicializado do banco)
# e ESCREVEM no session_state normalmente — sem sobrescrever a cada render
# ==============================

st.subheader(f"📝 Checklist — {etapa_selecionada}")
checklist_itens = []

for idx, item in enumerate(itens_lista):
    k_check = f"impl_check_{chave_cliente}_{etapa_selecionada}_{idx}"
    checked = st.checkbox(item, key=k_check)
    if checked:
        checklist_itens.append(item)

total_itens    = len(itens_lista)
pct            = int(len(checklist_itens) / total_itens * 100) if total_itens > 0 else 0
todos_marcados = total_itens > 0 and len(checklist_itens) == total_itens

st.progress(pct / 100)
st.caption(f"{len(checklist_itens)} de {total_itens} itens marcados ({pct}%)")

k = lambda campo: f"impl_{campo}_{chave_cliente}_{etapa_selecionada}"

nenhum_marcado = total_itens > 0 and len(checklist_itens) == 0

# ── Ajuste automático de status conforme checklist ──
# Só altera se o usuário não mudou o status manualmente nesta sessão
# (o status_atual é o que está no session_state neste momento)
status_atual = st.session_state.get(k("status"), "Não iniciado")

if todos_marcados:
    # Todos marcados → Concluído
    if status_atual != "Concluído":
        st.session_state[k("status")] = "Concluído"
        st.success("✅ Todos os itens marcados — status atualizado para **Concluído**.")
    if st.session_state.get(k("dc")) is None:
        st.session_state[k("dc")] = date.today()

elif nenhum_marcado:
    # Nenhum marcado → Não iniciado (reverte conclusão indevida)
    if status_atual == "Concluído":
        st.session_state[k("status")] = "Não iniciado"
        st.session_state[k("dc")]     = None
        st.info("ℹ️ Todos os itens foram desmarcados — status revertido para **Não iniciado**.")

elif 0 < len(checklist_itens) < total_itens:
    # Parcialmente marcado → Em andamento (só se estava Concluído ou Não iniciado)
    if status_atual in ("Concluído", "Não iniciado"):
        st.session_state[k("status")] = "Em andamento"
        if status_atual == "Concluído":
            st.session_state[k("dc")] = None
            st.warning("⚠️ Checklist incompleto — status revertido para **Em andamento**.")

# ==============================
# CAMPOS DO FORMULÁRIO
# ==============================

col1, col2, col3 = st.columns(3)
with col1:
    status = st.selectbox("Status", STATUS_PADRAO, key=k("status"))
with col2:
    data_inicio = st.date_input("Data de Início", format="DD/MM/YYYY", key=k("di"))
with col3:
    resp_medicit = st.text_input("Responsável Medicit", key=k("rmed"))

col4, col5 = st.columns(2)
with col4:
    resp_cliente = st.text_input("Responsável Cliente", key=k("rcli"))
with col5:
    participantes = st.text_input("Participantes", key=k("part"))

motivo = st.text_area("Motivo / Observação", key=k("motivo"), height=120)

col6, col7 = st.columns(2)
with col6:
    proxima_acao = st.text_input("Próxima Ação", key=k("proxac"))
with col7:
    if status == "Concluído" and st.session_state.get(k("dc")) is None:
        st.session_state[k("dc")] = date.today()
    data_conclusao = st.date_input("Data de Conclusão", format="DD/MM/YYYY", key=k("dc"))

# ==============================
# SALVAR
# ==============================

if st.button("💾 Salvar Implantação", key="impl_salvar"):
    chave_impl = f"{chave_cliente}||{etapa_selecionada}"

    novo_registro = {
        "chave":               chave_impl,
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
        ok   = atualizar("implantacao", "chave", chave_impl, novo_registro)
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

        # ── Garante que todas as etapas existam para o cliente ──
        # Evita que a consulta geral mostre 100% quando só algumas etapas foram salvas
        df_impl_check = carregar_implantacao().fillna("")
        df_impl_check["cnpj_cpf"] = df_impl_check["cnpj_cpf"].apply(normalizar_doc)
        etapas_existentes_cli = df_impl_check[
            df_impl_check["cnpj_cpf"] == chave_cliente
        ]["etapa"].str.strip().tolist()

        todas_etapas = df_etapas[["etapa", "ordem_etapa"]].drop_duplicates()
        for _, et in todas_etapas.iterrows():
            et_nome = str(et["etapa"]).strip()
            if et_nome not in etapas_existentes_cli:
                chave_et = f"{chave_cliente}||{et_nome}"
                inserir("implantacao", {
                    "chave":               chave_et,
                    "cnpj_cpf":            chave_cliente,
                    "cliente":             cliente_sel,
                    "etapa":               et_nome,
                    "status":              "Não iniciado",
                    "data_inicio":         "",
                    "checklist":           "",
                    "responsavel_medicit": resp_med_cadastro,
                    "responsavel_cliente": resp_cli_cadastro,
                    "participantes":       "",
                    "motivo":              "",
                    "proxima_acao":        "",
                    "ultima_atualizacao":  datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "data_conclusao":      ""
                })

        # Limpa contexto para forçar releitura do banco na próxima abertura
        limpar_contexto()
        st.success(f"✅ Implantação {'atualizada' if existia else 'cadastrada'} com sucesso!")
        st.rerun()
    else:
        st.error("❌ Erro ao salvar. Tente novamente.")