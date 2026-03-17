import streamlit as st
import pandas as pd
from datetime import datetime
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_STREAMLIT_GSHEETS = True
except Exception:
    GSheetsConnection = None
    HAS_STREAMLIT_GSHEETS = False
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Comando 2026", layout="centered")
# --- ESTILIZAÇÃO CUSTOMIZADA ---
# --- ESTILIZAÇÃO CUSTOMIZADA (VISUAL MODERNO) ---
st.markdown("""
    <style>
        /* 1. Esconder Header, Menu (Hamburger) e Footer do Streamlit */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 2. Ajustar margens para compensar a falta do cabeçalho */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 500px; /* Estreita o layout para parecer um App Mobile no PC */
        }

        /* 3. Fundo da página e fontes */
        .stApp {
            background-color: #F8F9FA;
        }

        /* 4. Estilização de Botões (Padrão Max: Laranja) */
        div.stButton > button:first-child {
            background-color: #FF5E00; /* Laranja vibrante */
            color: white;
            border-radius: 12px;
            border: none;
            height: 50px;
            width: 100%;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(255, 94, 0, 0.2);
            margin-bottom: 10px;
        }
        
        div.stButton > button:hover {
            background-color: #E65500;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(255, 94, 0, 0.3);
            color: white;
        }

        /* 5. Estilização dos Inputs */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            padding: 12px;
        }

        /* 6. Cards e Containers */
        [data-testid="stExpander"], [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
            background-color: white;
            border-radius: 15px;
            padding: 15px;
            border: 1px solid #E9ECEF;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        }

        /* 7. Tabs (Abas) estilo Segmented Control */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #E9ECEF;
            padding: 5px;
            border-radius: 12px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            background-color: transparent;
            border-radius: 8px;
            color: #6C757D;
            border: none;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: white;
            color: #FF5E00;
            font-weight: bold;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 8. Estilo de Alertas/Infos */
        .stAlert {
            border-radius: 12px;
            border: none;
            background-color: #FFF3E0;
            color: #E65100;
        }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DO STATE ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None


def _get_gspread_client():
    """Cria e retorna um cliente gspread a partir de st.secrets.
    Retorna None e registra erro no Streamlit se secrets ausentes/invalidos.
    """
    try:
        creds_dict = st.secrets.get("connections", {}).get("gsheets")
        if not creds_dict:
            st.error("Credenciais do Google Sheets não encontradas em st.secrets.connections.gsheets")
            return None

        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao criar cliente gspread: {e}")
        return None


def sanitize_whatsapp(v: str) -> str:
    """Extrai apenas dígitos do número e retorna string vazia se inválido."""
    if v is None:
        return ""
    nums = ''.join(filter(str.isdigit, str(v)))
    return nums

def carregar_dados(nome_aba):
    try:
        sheet_id = st.secrets.get("planilha", {}).get("id")
        if not sheet_id:
            st.error("ID da planilha não configurado em st.secrets.planilha.id")
            return None

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df.astype(str).apply(lambda x: x.str.strip())
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def registrar_acao(id_usuario, tipo_acao):
    try:
        client = _get_gspread_client()
        if client is None:
            st.error("Não foi possível obter cliente do Google Sheets. Ação não registrada.")
            return

        planilha_id = st.secrets.get("planilha", {}).get("id")
        if not planilha_id:
            st.error("ID da planilha não configurado em st.secrets.planilha.id")
            return

        planilha = client.open_by_key(planilha_id)
        aba = planilha.worksheet("Logs")
        
        # 3. Prepara os dados
        nova_linha = [
            datetime.now().strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ]
        
        # 4. O comando 'append_row' é o mais poderoso: ele adiciona na última linha livre
        aba.append_row(nova_linha)
        st.toast(f"✅ Gravado: {tipo_acao}")
        
    except Exception as e:
        st.error(f"Erro fatal na gravação: {e}")
            
# --- ÁREA DE LOGIN CENTRALIZADA ---
if st.session_state["usuario_logado"] is None:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("<h1 style='text-align: center;'>🚀</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Comando 2026</h2>", unsafe_allow_html=True)
        
        with st.container(border=True):
            email_input = st.text_input("ID de Acesso (E-mail)")
            if st.button("Entrar no Painel", use_container_width=True, type="primary"):
                df_usuarios = carregar_dados("Usuarios")
                if df_usuarios is not None:
                    user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == email_input.lower().strip()]
                    if not user_match.empty:
                        st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("❌ ID não encontrado. Verifique se o e-mail está correto.")
    
    st.info("💡 Dica: Se for seu primeiro acesso, solicite seu ID ao seu supervisor.")

# --- CONTEÚDO DO APP (APÓS LOGIN) ---
else:
    u = st.session_state["usuario_logado"]
    cargo_limpo = str(u['Cargo']).strip().lower()

    # --- NOVA SIDEBAR (Coloque aqui!) ---
    with st.sidebar:
        st.header("👤 Perfil")
        st.write(f"Olá, **{u['Nome'].split()[0]}**")
        st.caption(f"Cargo: {u['Cargo']}")
        st.divider()
        
        # Botão Sair dentro da Sidebar
        if st.button("🚪 Sair / Trocar Conta", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.rerun()

# --- ÁREA PRINCIPAL ---
if st.session_state["usuario_logado"]:
    u = st.session_state["usuario_logado"]
    cargo_limpo = str(u['Cargo']).strip().lower()
    
    st.title(f"Painel: {u['Cargo']}")
    
# --- PERFIL: VOLUNTÁRIO ---
    if cargo_limpo in ["voluntario", "voluntário"]:
        st.header(f"Olá, {u['Nome'].split()[0]}! 🚩")
        df_msgs = carregar_dados("Mensagens")
        df_usuarios = carregar_dados("Usuarios")

        if df_msgs is None or df_usuarios is None:
            st.error("Falha ao carregar Mensagens ou Usuarios. Tente novamente.")
            st.stop()
        
        # 1. MENSAGEM DO DIA (Boas-vindas)
        if df_msgs is not None:
            msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str) == str(u['ID_Grupo'])]
            if not msg_grupo.empty:
                m = msg_grupo.iloc[-1]
                st.info(f"**MENSAGEM DO DIA:**\n\n{m['Mensagem_Inicial']}")
            else:
                st.warning(f"Sem instruções específicas para o grupo {u['ID_Grupo']}.")
        
        # 2. CHECK-IN (Agora como primeira ação principal)
        st.divider()
        if st.button("📍 Marcar Check-in de hoje", use_container_width=True, type="primary"):
            registrar_acao(u['ID_Usuario'], "Check-in")
            st.success("Check-in realizado com sucesso!")

        # 3. ÁREA DE MISSÕES (Logo após o Check-in)
        if df_msgs is not None and not msg_grupo.empty:
            st.subheader("🚀 Sugestões - Ao fazer algo clique nos botões abaixo")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                if st.button(f"📲 {m['Sugestao_1']}", use_container_width=True):
                    registrar_acao(u['ID_Usuario'], m['Sugestao_1'])
            with col_m2:
                if st.button(f"💬 {m['Sugestao_2']}", use_container_width=True):
                    registrar_acao(u['ID_Usuario'], m['Sugestao_2'])

            tarefa_txt = m['Tarefa_Direcionada'] if str(m['Tarefa_Direcionada']) != "nan" else "Nenhuma tarefa"
            if st.button(f"🚩 {tarefa_txt}", use_container_width=True):
                registrar_acao(u['ID_Usuario'], f"TAREFA: {tarefa_txt}")
                st.success(f"Tarefa registrada: {tarefa_txt}")

        # 4. REDES SOCIAIS (Apenas Instagram)
        st.divider()
        st.subheader("📱 Redes do Max")

        st.markdown("##### 📸 Instagram")
        
        insta_html = """
        <iframe src="https://www.instagram.com/maxmacieldf/embed" 
            width="100%" height="450" frameborder="0" scrolling="no" allowtransparency="true"
            style="border-radius: 10px; border: 1px solid #ddd;">
        </iframe>
        """
        st.components.v1.html(insta_html, height=460)

        # 5. CONTATO SUPERVISOR (Sidebar)
        st.sidebar.divider()
        id_sup = str(u['ID_Supervisor']).strip()
        supervisor_data = df_usuarios[df_usuarios['ID_Usuario'].astype(str).str.strip() == id_sup]
        if not supervisor_data.empty:
            sup_nome = supervisor_data.iloc[0]['Nome'].split()[0]
            whats_sup = sanitize_whatsapp(supervisor_data.iloc[0]['WhatsApp'])
            st.sidebar.write(f"Dúvidas? Fale com {sup_nome}:")
            st.sidebar.markdown(f"[💬 Chamar no WhatsApp](https://wa.me/{whats_sup})")
    
    
# --- PERFIL: SUPERVISOR ---


    elif cargo_limpo == "supervisor":
        st.title("📈 Gestão de Equipe")
        with st.spinner('Buscando atividades...'):
            df_usuarios = carregar_dados("Usuarios")
            df_logs = carregar_dados("Logs")
            
        if df_usuarios is None or df_logs is None:
            st.error("Não foi possível carregar dados necessários (Usuarios/Logs).")
        else:
            minha_equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str).str.strip() == str(u['ID_Usuario']).strip()]
            hoje = datetime.now().strftime("%d/%m/%Y")
            
            if not minha_equipe.empty:
                st.write(f"Acompanhamento: **{hoje}**")
                for _, vol in minha_equipe.iterrows():
                    logs_hoje = df_logs[(df_logs['ID_Usuario'].astype(str) == str(vol['ID_Usuario'])) & (df_logs['Data_Hora'].astype(str).str.contains(hoje))]
                    status_cor = "🟢" if not logs_hoje.empty else "⚪"
                    
                    with st.expander(f"{status_cor} {vol['Nome']}"):
                        if not logs_hoje.empty:
                            for _, log in logs_hoje.iterrows():
                                st.write(f"- {log['Tipo_Acao']}")
                        else:
                            st.warning("Nenhuma atividade hoje.")
                        
                        whats_vol = sanitize_whatsapp(vol['WhatsApp'])
                        st.markdown(f"[📲 Cobrar no WhatsApp](https://wa.me/{whats_vol})")

# --- PERFIL: ADMIN ---
# --- PERFIL: ADMIN (AQUI ENTRA O NOVO PAINEL) ---
    elif cargo_limpo == "admin":
        st.subheader("🛡️ Gestão Global do Sistema")
        
        tab_hierarquia, tab_mensagens, tab_logs, tab_cadastro = st.tabs([
            "👥 Equipes", "📝 Mensagens", "📊 Acompanhamento Geral", "➕ Novo Usuário"
        ])

# --- TABELA DE HIERARQUIA COM CARDS ---
        with tab_hierarquia:
            st.write("### 👥 Estrutura de Equipes")
            df_usuarios = carregar_dados("Usuarios")
            
            if df_usuarios is not None:
                # 1. Filtramos quem são os supervisores
                supervisores = df_usuarios[df_usuarios['Cargo'].str.lower().str.strip() == "supervisor"]
                
                if supervisores.empty:
                    st.warning("Nenhum supervisor encontrado na base de dados.")
                else:
                    for _, sup in supervisores.iterrows():
                        # Criamos um "Card" usando um container com borda
                        with st.container():
                            col_info, col_link = st.columns([3, 1])
                            
                            with col_info:
                                st.markdown(f"#### 👤 {sup['Nome']}")
                                st.caption(f"🆔 ID: {sup['ID_Usuario']} | 📍 Grupo: {sup['ID_Grupo']}")
                            
                            with col_link:
                                # Limpa o número de WhatsApp para o link
                                whats_limpo = ''.join(filter(str.isdigit, str(sup['WhatsApp'])))
                                if whats_limpo:
                                    st.link_button("💬 WhatsApp", f"https://wa.me/{whats_limpo}")
                            
                            # 2. Buscamos os voluntários que respondem a este supervisor
                            equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str).str.strip() == str(sup['ID_Usuario']).strip()]
                            
                            # Expander para mostrar os voluntários
                            with st.expander(f"📋 Ver Voluntários ({len(equipe)})"):
                                if not equipe.empty:
                                    for _, vol in equipe.iterrows():
                                        c1, c2, c3 = st.columns([2, 1, 1])
                                        c1.write(f"🚩 {vol['Nome']}")
                                        c2.write(f"ID: {vol['ID_Usuario']}")
                                        # Link rápido para o voluntário também, se precisar cobrar direto
                                        w_vol = sanitize_whatsapp(vol['WhatsApp'])
                                        c3.markdown(f"[Contato](https://wa.me/{w_vol})")
                                else:
                                    st.write("⚠️ Este supervisor ainda não tem voluntários vinculados.")
            else:
                st.error("Não foi possível carregar a lista de usuários.")

        # --- EDIÇÃO DE MENSAGENS (O código que fizemos com GSpread) ---
        with tab_mensagens:
            # Aqui chamamos a lógica de edição que desenvolvemos
            try:
                client = _get_gspread_client()
                if client is None:
                    raise RuntimeError("Cliente gspread indisponível")

                planilha_id = st.secrets.get("planilha", {}).get("id")
                if not planilha_id:
                    raise RuntimeError("ID da planilha não configurado em st.secrets.planilha.id")

                planilha = client.open_by_key(planilha_id)
                aba_msg = planilha.worksheet("Mensagens")

                df_msg = pd.DataFrame(aba_msg.get_all_records())

                lista_alvos = df_msg["ID_Alvo"].unique().tolist()
                alvo_selecionado = st.selectbox("Selecione o Alvo:", ["Novo..."] + lista_alvos)

                with st.form("form_admin_msg"):
                    if alvo_selecionado == "Novo...":
                        id_alvo, msg_i, sug1, sug2, tar, dat = "", "", "", "", "", ""
                    else:
                        d = df_msg[df_msg["ID_Alvo"] == alvo_selecionado].iloc[0]
                        id_alvo, msg_i, sug1, sug2, tar, dat = d["ID_Alvo"], d["Mensagem_Inicial"], d["Sugestao_1"], d["Sugestao_2"], d["Tarefa_Direcionada"], d["Data_Referencia"]

                    f_id = st.text_input("ID do Alvo:", value=id_alvo)
                    f_msg = st.text_area("Mensagem Inicial:", value=msg_i)
                    col_a, col_b = st.columns(2)
                    f_s1 = col_a.text_input("Sugestão 1:", value=sug1)
                    f_s2 = col_b.text_input("Sugestão 2:", value=sug2)
                    f_tar = st.text_area("Tarefa Direcionada:", value=tar)
                    f_dat = st.text_input("Data Ref:", value=dat)

                    if st.form_submit_button("Salvar Mensagens"):
                        # Lógica de atualização no Google Sheets
                        nova_linha = [f_id, f_msg, f_s1, f_s2, f_tar, f_dat]

                        # Se existe, deleta a linha antiga para não duplicar
                        if alvo_selecionado != "Novo...":
                            try:
                                cell = aba_msg.find(str(alvo_selecionado))
                                if cell:
                                    aba_msg.delete_rows(cell.row)
                            except Exception:
                                # se não encontrou, continuamos e apenas append
                                pass

                        aba_msg.append_row(nova_linha)
                        st.success("Planilha atualizada!")
                        st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro no painel: {e}")

# --- LOGS GERAIS E DIÁRIOS ---
        with tab_logs:
            st.write("### 📊 Monitoramento de Atividades")
            
            df_logs_admin = carregar_dados("Logs")
            df_usuarios = carregar_dados("Usuarios")
            
            if df_logs_admin is not None and df_usuarios is not None:
                # 1. Tratamento de Dados
                # Forçamos a conversão para datetime para os gráficos funcionarem
                df_logs_admin['Data_Hora_DT'] = pd.to_datetime(df_logs_admin['Data_Hora'], dayfirst=True, errors='coerce')
                
                df_completo = pd.merge(
                    df_logs_admin, 
                    df_usuarios[['ID_Usuario', 'Nome']], 
                    on='ID_Usuario', 
                    how='left'
                )
                df_completo['Nome'] = df_completo['Nome'].fillna(df_completo['ID_Usuario'])

                # 2. Filtro de Período
                hoje_str = datetime.now().strftime("%d/%m/%Y")
                filtro_tipo = st.radio("Selecione a visão:", ["Hoje", "Histórico Completo"], horizontal=True)
                
                if filtro_tipo == "Hoje":
                    df_filtrado = df_completo[df_completo['Data_Hora'].astype(str).str.contains(hoje_str)].copy()
                    texto_periodo = f"em {hoje_str}"
                else:
                    df_filtrado = df_completo.copy()
                    texto_periodo = "no Total"

                # 3. Métricas Dinâmicas
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric(f"Ações ({filtro_tipo})", len(df_filtrado))
                with m2:
                    st.metric(f"Pessoas Ativas", df_filtrado['ID_Usuario'].nunique())
                with m3:
                    checkins = len(df_filtrado[df_filtrado['Tipo_Acao'] == "Check-in"])
                    st.metric(f"Check-ins", checkins)

                st.divider()

# --- 4. PAINEL ANALÍTICO MODERNO ---
                if not df_filtrado.empty:
                    st.write(f"#### 📈 Insight de Performance ({filtro_tipo})")
                    col_analise1, col_analise2 = st.columns(2)

                    with col_analise1:
                        st.markdown("🚀 **Ranking de Atividades**")
                        contagem_tipo = df_filtrado['Tipo_Acao'].value_counts().reset_index()
                        contagem_tipo.columns = ['Atividade', 'Qtd']
                        
                        for _, row in contagem_tipo.iterrows():
                            st.markdown(f"""
                                <div style="
                                    background-color: #ffffff;
                                    padding: 15px;
                                    border-radius: 12px;
                                    border-left: 5px solid #1f77b4;
                                    box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
                                    margin-bottom: 12px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: space-between;
                                ">
                                    <div style="flex-grow: 1; margin-right: 10px;">
                                        <span style="color: #444; font-weight: 600; font-size: 0.95rem;">
                                            {row['Atividade']}
                                        </span>
                                    </div>
                                    <div style="
                                        background: #f0f2f6;
                                        color: #1f77b4;
                                        font-weight: bold;
                                        padding: 5px 12px;
                                        border-radius: 8px;
                                        min-width: 70px;
                                        text-align: center;
                                        font-size: 0.9rem;
                                        border: 1px solid #d1d5db;
                                    ">
                                        {row['Qtd']}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                    with col_analise2:
                        st.markdown("⏱️ **Picos de Produtividade**")
                        df_filtrado['Hora'] = df_filtrado['Data_Hora_DT'].dt.hour
                        top_horas = df_filtrado['Hora'].value_counts().head(4).reset_index()
                        top_horas.columns = ['Hora', 'Qtd']
                        top_horas = top_horas.sort_values(by='Qtd', ascending=False)

                        for _, row in top_horas.iterrows():
                            hora_ini = f"{int(row['Hora']):02d}:00"
                            hora_fim = f"{int(row['Hora'])+1:02d}:00"
                            # Card estilizado para horários
                            st.markdown(f"""
                                <div style="
                                    background-color: #f8f9fa;
                                    padding: 12px;
                                    border-radius: 10px;
                                    border: 1px solid #e9ecef;
                                    margin-bottom: 10px;
                                ">
                                    <div style="font-size: 0.8rem; color: #6c757d; text-transform: uppercase;">Janela de Pico</div>
                                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                        <span style="font-size: 1.1rem; font-weight: bold; color: #2c3e50;">{hora_ini} - {hora_fim}</span>
                                        <span style="color: #ff4b4b; font-weight: bold;">{row['Qtd']} registros</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                
                st.divider()

                # 5. Tabela Detalhada
                st.write(f"#### Detalhamento {texto_periodo}")
                st.dataframe(
                    df_filtrado.sort_values(by="Data_Hora_DT", ascending=False)[['Nome', 'Tipo_Acao', 'Data_Hora']],
                    column_config={
                        "Nome": "Voluntário",
                        "Tipo_Acao": "Ação",
                        "Data_Hora": "Data/Hora"
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # 6. Exportação
                csv = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Baixar Relatório ({filtro_tipo})",
                    data=csv,
                    file_name=f'logs_{filtro_tipo.lower()}.csv',
                    mime='text/csv',
                    use_container_width=True
                )
            else:
                st.info("Aguardando registros de logs...")


                # --- TABELA DE CADASTRO DE USUÁRIOS ---
        with tab_cadastro:
            st.write("### 👤 Cadastrar Novo Integrante")
            
            # 1. Carregar dados atuais para preencher os selects
            df_atual = carregar_dados("Usuarios")
            
            if df_atual is not None:
                # Criar listas únicas para os seletores
                # Pegamos apenas quem já é Supervisor para a lista de supervisores
                lista_supervisores = df_atual[df_atual['Cargo'].str.lower().str.strip() == "supervisor"]['ID_Usuario'].unique().tolist()
                lista_grupos = sorted(df_atual['ID_Grupo'].unique().tolist())
                
                with st.form("form_novo_usuario", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        novo_id = st.text_input("ID_Usuario (E-mail):", placeholder="exemplo@email.com").strip().lower()
                        novo_nome = st.text_input("Nome Completo:", placeholder="João Silva")
                        novo_whats = st.text_input("WhatsApp (com DDD):", placeholder="61988887777")
                    
                    with col2:
                        novo_cargo = st.selectbox("Cargo:", ["Voluntario", "Supervisor", "Admin"])
                        
                        # Lista de seleção para Grupo
                        novo_grupo = st.selectbox("Grupo (ID):", options=lista_grupos, help="Selecione um grupo existente")
                        
                        # Lista de seleção para Supervisor
                        novo_sup_selecionado = st.selectbox(
                            "ID_Supervisor (E-mail do Supervisor):", 
                            options=["Nenhum"] + lista_supervisores,
                            help="Obrigatório para Voluntários"
                        )

                    enviar_user = st.form_submit_button("Finalizar Cadastro")

                    if enviar_user:
                        if not novo_id or not novo_nome or not novo_whats:
                            st.error("Preencha os campos obrigatórios: ID, Nome e WhatsApp.")
                        elif novo_cargo == "Voluntario" and novo_sup_selecionado == "Nenhum":
                            st.error("⚠️ Voluntários precisam de um supervisor atribuído.")
                        else:
                            try:
                                client = _get_gspread_client()
                                if client is None:
                                    raise RuntimeError("Cliente gspread indisponível")

                                planilha_id = st.secrets.get("planilha", {}).get("id")
                                planilha = client.open_by_key(planilha_id)
                                aba_users = planilha.worksheet("Usuarios")

                                # Tratamento do valor do supervisor
                                valor_sup = novo_sup_selecionado if novo_sup_selecionado != "Nenhum" else ""

                                nova_linha_user = [
                                    novo_id,
                                    novo_nome,
                                    novo_whats,
                                    novo_cargo,
                                    novo_grupo,
                                    valor_sup
                                ]

                                aba_users.append_row(nova_linha_user)

                                st.toast("Usuário salvo com sucesso!", icon="✅")
                                st.cache_data.clear()
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erro ao salvar no Google Sheets: {e}")
            else:
                st.error("Erro ao carregar lista de usuários para o cadastro.")
