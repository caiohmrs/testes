import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Comando 2026", layout="centered")

# --- INICIALIZAÇÃO DO STATE ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

def carregar_dados(nome_aba):
    try:
        sheet_id = st.secrets["planilha"]["id"]
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
        # 1. Configura as credenciais diretamente do st.secrets
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        
        # Criamos um dicionário de credenciais exatamente como o Google espera
        creds_dict = {
            "type": st.secrets["connections"]["gsheets"]["type"],
            "project_id": st.secrets["connections"]["gsheets"]["project_id"],
            "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
            "private_key": st.secrets["connections"]["gsheets"]["private_key"],
            "client_email": st.secrets["connections"]["gsheets"]["client_email"],
            "client_id": st.secrets["connections"]["gsheets"]["client_id"],
            "auth_uri": st.secrets["connections"]["gsheets"]["auth_uri"],
            "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["connections"]["gsheets"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["connections"]["gsheets"]["client_x509_cert_url"],
        }
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # 2. Abre a planilha pelo ID e a aba pelo nome
        # Mude o ID abaixo se necessário para garantir que é o atual
        planilha = client.open_by_key("1ANIjSHO8Wt8BstyDmZu1WbvGj8Xvi8702dsH3sDMGZA")
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
        
        st.toast(f"✅ Gravado via GSpread: {tipo_acao}")
        
    except Exception as e:
        st.error(f"Erro fatal na gravação: {e}")
            
# --- BARRA LATERAL (Login) ---
st.sidebar.title("🔐 Acesso")
email_input = st.sidebar.text_input("Digite seu ID (E-mail)")

if st.sidebar.button("Entrar"):
    df_usuarios = carregar_dados("Usuarios")
    if df_usuarios is not None:
        user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == email_input.lower().strip()]
        if not user_match.empty:
            st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
            st.rerun()
        else:
            st.sidebar.error("ID não encontrado.")

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
            st.balloons()
            st.success("Check-in realizado com sucesso!")

        # 3. ÁREA DE MISSÕES (Logo após o Check-in)
        if df_msgs is not None and not msg_grupo.empty:
            st.subheader("🚀 Sugestões - Ao fazer algo clique nos botões abaixo")
            
            if st.button(f"📲 {m['Sugestao_1']}", use_container_width=True):
                registrar_acao(u['ID_Usuario'], m['Sugestao_1'])
                st.success(f"Ação registrada: {m['Sugestao_1']}")

            if st.button(f"💬 {m['Sugestao_2']}", use_container_width=True):
                registrar_acao(u['ID_Usuario'], m['Sugestao_2'])
                st.success(f"Ação registrada: {m['Sugestao_2']}")

            tarefa_txt = m['Tarefa_Direcionada'] if str(m['Tarefa_Direcionada']) != "nan" else "Nenhuma tarefa"
            if st.button(f"🚩 {tarefa_txt}", use_container_width=True):
                registrar_acao(u['ID_Usuario'], f"TAREFA: {tarefa_txt}")
                st.success(f"Tarefa registrada: {tarefa_txt}")

        # 4. REDES SOCIAIS (Apenas Instagram)
        st.divider()
        st.subheader("📱 Redes do Max")

        st.markdown("##### 📸 Instagram")
        st.link_button("Abrir Instagram", "https://www.instagram.com/maxmacieldf", use_container_width=True)
        
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
            whats_sup = ''.join(filter(str.isdigit, str(supervisor_data.iloc[0]['WhatsApp'])))
            st.sidebar.write(f"Dúvidas? Fale com {sup_nome}:")
            st.sidebar.markdown(f"[💬 Chamar no WhatsApp](https://wa.me/{whats_sup})")
    # --- PERFIL: SUPERVISOR ---
    elif cargo_limpo == "supervisor":
        st.title("📈 Gestão de Equipe")
        with st.spinner('Buscando atividades...'):
            df_usuarios = carregar_dados("Usuarios")
            df_logs = carregar_dados("Logs")
            
        if df_usuarios is not None and df_logs is not None:
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
                        
                        whats_vol = ''.join(filter(str.isdigit, str(vol['WhatsApp'])))
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
                        with st.container(border=True):
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
                                        w_vol = ''.join(filter(str.isdigit, str(vol['WhatsApp'])))
                                        c3.markdown(f"[Contato](https://wa.me/{w_vol})")
                                else:
                                    st.write("⚠️ Este supervisor ainda não tem voluntários vinculados.")
            else:
                st.error("Não foi possível carregar a lista de usuários.")

        # --- EDIÇÃO DE MENSAGENS (O código que fizemos com GSpread) ---
        with tab_mensagens:
            # Aqui chamamos a lógica de edição que desenvolvemos
            try:
                # Conexão direta via gspread para evitar cache
                scope = ["https://www.googleapis.com/auth/spreadsheets"]
                creds_dict = st.secrets["connections"]["gsheets"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                client = gspread.authorize(creds)
                planilha = client.open_by_key(st.secrets["planilha"]["id"])
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
                            cell = aba_msg.find(str(alvo_selecionado))
                            aba_msg.delete_rows(cell.row)
                        
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
            
            with st.form("form_novo_usuario", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    novo_id = st.text_input("ID_Usuario (E-mail):", placeholder="exemplo@email.com").strip().lower()
                    novo_nome = st.text_input("Nome Completo:", placeholder="João Silva")
                    novo_whats = st.text_input("WhatsApp (com DDD):", placeholder="61988887777")
                
                with col2:
                    novo_cargo = st.selectbox("Cargo:", ["Voluntario", "Supervisor", "Admin"])
                    novo_grupo = st.text_input("Grupo (ID):", placeholder="ex: 1")
                    
                    # O campo supervisor só aparece ou faz sentido se for voluntário
                    novo_sup = st.text_input("ID_Supervisor (E-mail do Supervisor):", 
                                            placeholder="chefe@email.com",
                                            help="Obrigatório para Voluntários")

                enviar_user = st.form_submit_button("Finalizar Cadastro")

                if enviar_user:
                    if not novo_id or not novo_nome or not novo_whats:
                        st.error("Preencha os campos obrigatórios: ID, Nome e WhatsApp.")
                    else:
                        try:
                            # Conexão GSpread
                            scope = ["https://www.googleapis.com/auth/spreadsheets"]
                            creds_dict = st.secrets["connections"]["gsheets"]
                            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                            client = gspread.authorize(creds)
                            
                            planilha = client.open_by_key(st.secrets["planilha"]["id"])
                            aba_users = planilha.worksheet("Usuarios")
                            
                            # Prepara a linha para o Google Sheets (ajuste a ordem conforme sua planilha)
                            # Ordem sugerida: ID_Usuario, Nome, WhatsApp, Cargo, ID_Grupo, ID_Supervisor
                            nova_linha_user = [
                                novo_id, 
                                novo_nome, 
                                novo_whats, 
                                novo_cargo, 
                                novo_grupo, 
                                novo_sup if novo_cargo == "Voluntario" else ""
                            ]
                            
                            aba_users.append_row(nova_linha_user)
                        
                            st.toast("Usuário salvo com sucesso!", icon="✅")
                            # Limpa o cache para o novo usuário conseguir logar na hora
                            st.cache_data.clear()
                            
                        except Exception as e:
                            st.error(f"Erro ao salvar no Google Sheets: {e}")

                            
    # --- BOTÃO SAIR ---
    if st.sidebar.button("Sair"):
        st.session_state["usuario_logado"] = None
        st.rerun()
else:
    st.info("👋 Por favor, faça login na barra lateral.")