import gspread
import io
from datetime import datetime
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx

# Diferenciando os tipos de credenciais
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build



# --- FUNÇÕES DE APOIO ---

def _get_drive_credentials():
    """Usa OAuthCredentials (Refresh Token) para os 15GB do Drive"""
    try:
        creds_info = st.secrets["google_drive"]
        creds = OAuthCredentials(
            token=None,
            refresh_token=creds_info["refresh_token"],
            token_uri=creds_info["token_uri"],
            client_id=creds_info["client_id"],
            client_secret=creds_info["client_secret"]
        )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        return creds
    except Exception as e:
        st.error(f"Erro ao carregar credenciais do Drive: {e}")
        return None

def _get_sheets_credentials():
    """Service Account - Para o Sheets (Logs/Usuarios)"""
    try:
        creds_dict = st.secrets.get("connections", {}).get("gsheets")
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        return ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scope)
    except Exception as e:
        st.error(f"Erro credenciais Sheets: {e}")
        return None

def salvar_foto_drive(foto_arquivo, nome_arquivo):
    """Upload via OAuth2 - Usa a cota da conta pessoal (15GB)"""
    try:
        from googleapiclient.discovery import build
        # MUDANÇA AQUI: Usa as credenciais do Drive (OAuth2) e não da Service Account
        creds = _get_drive_credentials() 
        
        if not creds:
            return "Erro de Autenticação"
            
        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_fotos = st.secrets["google_drive"]["id_pasta_fotos"]

        file_metadata = {
            'name': nome_arquivo,
            'parents': [id_pasta_fotos]
        }
        
        foto_bytes = io.BytesIO(foto_arquivo.getvalue())
        media = MediaIoBaseUpload(foto_bytes, mimetype='image/jpeg', resumable=False)

        # Upload
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Define permissão para qualquer um com o link ver
        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

def salvar_documento_drive(doc_arquivo, nome_arquivo):
    """Upload via OAuth2 para a pasta de Contratos - Usa a cota da conta pessoal"""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io

        # Usa as mesmas credenciais OAuth2 que já funcionam para fotos
        creds = _get_drive_credentials() 
        
        if not creds:
            st.error("Erro de Autenticação OAuth2")
            return None
            
        drive_service = build('drive', 'v3', credentials=creds)
        
        # MUDANÇA: Buscamos o ID da pasta de contratos no secrets
        # Certifique-se de adicionar 'id_pasta_contratos' no seu secrets.toml
        id_pasta_contratos = st.secrets["google_drive"]["id_pasta_contratos"]

        file_metadata = {
            'name': nome_arquivo,
            'parents': [id_pasta_contratos]
        }
        
        doc_bytes = io.BytesIO(doc_arquivo.getvalue())
        
        # MUDANÇA: Mimetype genérico para aceitar PDFs e outros docs
        media = MediaIoBaseUpload(doc_bytes, mimetype='application/pdf', resumable=False)

        # Upload
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Define permissão para qualquer um com o link ver (reader)
        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive (Documentos): {e}")
        return None


def _get_gspread_client():
    """Autoriza o gspread usando a Service Account"""
    creds = _get_sheets_credentials()
    return gspread.authorize(creds) if creds else None

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
            return

        planilha_id = st.secrets["planilha"]["id"]
        planilha = client.open_by_key(planilha_id)
        aba = planilha.worksheet("Logs")
        
        # O append_row é o método mais seguro para logs concorrentes
        aba.append_row([
            datetime.now().strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ])
        st.toast(f"✅ Log: {tipo_acao}")
    except Exception as e:
        st.error(f"Falha ao registrar log: {e}")

def atualizar_contrato_enviado(id_usuario, nome_arquivo, link_drive):
    """Atualiza o link do contrato assinado na aba Contratos seguindo o padrão gspread"""
    try:
        # 1. Usa o mesmo cliente gspread que já funciona nos logs
        client = _get_gspread_client()
        if client is None:
            return False

        # 2. Abre a planilha e acessa a aba correta
        planilha_id = st.secrets["planilha"]["id"]
        planilha = client.open_by_key(planilha_id)
        aba = planilha.worksheet("Contratos")
        
        # 3. Puxa todos os dados para localizar a linha certa
        # get_all_records transforma a planilha em uma lista de dicionários
        dados = aba.get_all_records()
        
        linha_para_atualizar = None
        # Começamos na linha 2 porque a 1 é o cabeçalho
        for i, linha in enumerate(dados, start=2):
            if str(linha.get('ID_Usuario')) == str(id_usuario) and \
               str(linha.get('Nome_Arquivo')) == str(nome_arquivo):
                linha_para_atualizar = i
                break
        
        if linha_para_atualizar:
            # 4. Localiza em qual coluna está o 'Link_Assinado'
            cabecalho = aba.row_values(1)
            if 'Link_Assinado' in cabecalho:
                coluna_index = cabecalho.index('Link_Assinado') + 1
                
                # 5. Faz o update da célula específica (mais rápido que reescrever tudo)
                aba.update_cell(linha_para_atualizar, coluna_index, link_drive)
                return True
            else:
                st.error("Coluna 'Link_Assinado' não encontrada na aba Contratos.")
        else:
            st.error(f"Não encontramos o contrato '{nome_arquivo}' para o usuário {id_usuario}.")
            
        return False
        
    except Exception as e:
        st.error(f"Falha ao atualizar contrato: {e}")
        return False


# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Comando 2026", layout="centered")

# Inicializa o gerenciador
cookie_manager = stx.CookieManager()

# IMPORTANTE: Definir uma variável vazia caso o componente ainda não tenha carregado
todos_os_cookies = cookie_manager.get_all()

# Se o componente ainda estiver carregando, 'todos_os_cookies' pode vir vazio ou None
if not todos_os_cookies:
    # Pequena pausa ou bypass para evitar o NameError enquanto o componente inicializa
    st.stop() # Ou apenas todos_os_cookies = {}


# Recupera o tempo de check-in do cookie para calcular a duração
checkin_str = todos_os_cookies.get("comando2026_checkin_time")
if checkin_str:
    try:
        checkin_dt = datetime.strptime(checkin_str, "%Y-%m-%d %H:%M:%S")
        duracao = agora - checkin_dt
        horas, rem = divmod(duracao.seconds, 3600)
        minutos, _ = divmod(rem, 60)
        tempo_missao = f"{duracao.days}d {horas}h {minutos}m"
    except:
        tempo_missao = "Erro no cálculo"

# --- INICIALIZAÇÃO DO STATE ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if todos_os_cookies:
    user_id_cookie = todos_os_cookies.get("comando2026_user_id")

    # Se existe cookie e o usuário NÃO está logado no state ainda
    if user_id_cookie and st.session_state["usuario_logado"] is None:
        df_usuarios = carregar_dados("Usuarios")
        if df_usuarios is not None:
            user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == user_id_cookie.lower().strip()]
            if not user_match.empty:
                st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                st.rerun() # Entra direto no painel


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
                        # AQUI: Salva no State
                        st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
            
                        # NOVIDADE: Salva o ID no Cookie (expira em 30 dias por padrão)
                        cookie_manager.set("comando2026_user_id", email_input.lower().strip(), key="set_user_cookie")
            
                        st.success("Bem-vindo!")
                        st.rerun()
                    else:
                        st.error("❌ ID não encontrado. Verifique se o e-mail está correto.")
    
    st.info("💡 Dica: Se for seu primeiro acesso, solicite seu ID ao seu supervisor.")

# --- CONTEÚDO DO APP (APÓS LOGIN) ---
else:
    u = st.session_state["usuario_logado"]
    cargo_limpo = str(u['Cargo']).strip().lower()

# --- NOVA SIDEBAR --
    with st.sidebar:
        st.header("👤 Perfil")
        st.write(f"Olá, **{u['Nome'].split()[0]}**")
        st.caption(f"Cargo: {u['Cargo']}")
        st.divider()

        if st.button("Atualizar Página", use_container_width=True):
                st.rerun()
                
        # Botão Sair dentro da Sidebar
        if st.button("Sair", use_container_width=True):
            # 1. Limpa o Cookie
            cookie_manager.delete("comando2026_user_id")
            # Limpa também o check-in se quiser que ele comece do zero
            cookie_manager.delete("comando2026_checkin_time") 
    
            # 2. Limpa o State
            st.session_state["usuario_logado"] = None
    
            # 3. Recarrega a página para voltar à tela de login
            st.rerun()

# --- ÁREA PRINCIPAL ---
if st.session_state["usuario_logado"]:
    u = st.session_state["usuario_logado"]
    cargo_limpo = str(u['Cargo']).strip().lower()
    
    st.title(f"Painel: {u['Cargo']}")
    
# --- PERFIL: VOLUNTÁRIO ---
    if cargo_limpo in ["voluntario", "voluntário"]:
        st.header(f"Olá, {u['Nome'].split()[0]}!")

        tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

        with tab_missoes:
            df_msgs = carregar_dados("Mensagens")
            df_usuarios = carregar_dados("Usuarios")

            if df_msgs is None or df_usuarios is None:
                st.error("Falha ao carregar dados. Tente novamente.")
                st.stop()
        

        # 1. MENSAGEM DO DIA
            if df_msgs is not None:
                msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str) == str(u['ID_Grupo'])]
                if not msg_grupo.empty:
                    m = msg_grupo.iloc[-1]
                    st.info(f"**MENSAGEM DO DIA:**\n\n{m['Mensagem_Inicial']}")

        # 2. ÁREA DE PRESENÇA (Check-in / Check-out com Popover)
            st.divider()
            st.subheader("Registro de Presença")
        
            col_c1, col_c2 = st.columns(2)
        
            with col_c1:
                with st.popover("🏁 Check-in", use_container_width=True):
                    st.write("### Registrar Entrada")
                    foto_in = st.camera_input("Tire uma foto para o Check-in", key="cam_in")
                
                    if st.button("Confirmar Check-in", use_container_width=True, type="primary"):
                        if foto_in:
                            with st.spinner("Enviando foto para o Drive..."):
                                try:
                                    nome_img = f"checkin_{u['Nome']}_{datetime.now().strftime('%d/%m/%Y_%H:%M:%S')}.jpg"
                                    # Tentativa de upload
                                    link_gerado = salvar_foto_drive(foto_in, nome_img)
                                
                                    if link_gerado and "http" in link_gerado:
                                        horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    
                                        # Registro na planilha: Enviamos o link concatenado para salvar no Sheets,
                                        # mas o Streamlit continuará tratando como uma ação de "Check-in"
                                        registrar_acao(u['ID_Usuario'], f"Check-in | Foto: {link_gerado}")
    
                                        cookie_manager.set("comando2026_checkin_time", horario_atual, key="set_checkin_clk")
                                        st.success("Check-in realizado!")
                                        st.rerun()
                                    else:
                                        st.error("Falha ao gerar link do Drive. Verifique as permissões da pasta.")
                                except Exception as e:
                                    st.error(f"Erro crítico no upload: {e}")
                        else:
                            st.warning("A foto é obrigatória para o registro.")

                with col_c2:
                    with st.popover("🏁 Check-out", use_container_width=True):
                        st.write("### Registrar Saída")
                        foto_out = st.camera_input("Tire uma foto para o Check-out", key="cam_out")
                
                        if st.button("Confirmar Check-out", use_container_width=True, type="primary"):
                            if foto_out:
                                with st.spinner("Enviando foto..."):
                                    nome_img = f"checkout_{u['Nome']}_{datetime.now().strftime('%d/%m/%Y_%H:%M:%S')}.jpg"
                                    link_checkout = salvar_foto_drive(foto_out, nome_img)
                            
                                # Montamos a mensagem que vai para a planilha
                                msg_planilha = f"Check-out | Foto: {link_checkout}"
                            
                                # Grava na planilha com o link
                                registrar_acao(u['ID_Usuario'], msg_planilha)
        
                                if "comando2026_checkin_time" in todos_os_cookies:
                                    cookie_manager.delete("comando2026_checkin_time")
                            
                                st.success("Check-out realizado!")
                                st.rerun()
                            else:
                                st.warning("A foto é obrigatória para o registro.")

        # 3. ÁREA DE MISSÕES
            if df_msgs is not None and not msg_grupo.empty:
                st.divider()
                st.subheader("Missões do Grupo")
            
                col_m1, col_m2 = st.columns(2)
           
            # --- Botão 1 ---
            with col_m1:
                    # Mantemos o st.button original para poder disparar o registrar_acao
                    if st.button(f"📲 {m['Sugestao_1']}", use_container_width=True):
                        # 1. Registra na planilha
                        registrar_acao(u['ID_Usuario'], f"Acesso Instagram: {m['Sugestao_1']}")
        
                        # 2. Feedback visual rápido
                        st.toast("Registrando e redirecionando...", icon="📸")
        
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0;URL=\'https://www.instagram.com/maxmacieldf/\'">',
                            unsafe_allow_html=True
                        )
        
                        # Caso o redirecionamento falhe no navegador do usuário, mostramos o botão fixo:
                        st.link_button("Clique aqui se não for redirecionado", "https://www.instagram.com/maxmacieldf/")
            #Botão 2
            with col_m2:
                if st.button(f"💬 {m['Sugestao_2']}", use_container_width=True):
                    registrar_acao(u['ID_Usuario'], m['Sugestao_2'])
                    st.toast("Ação registrada!", icon="✅")
            #Botão 3
            tarefa_txt = m['Tarefa_Direcionada'] if str(m['Tarefa_Direcionada']) != "nan" else "Tarefa Geral"
            if st.button(f"🚩 {tarefa_txt}", use_container_width=True):
                registrar_acao(u['ID_Usuario'], f"TAREFA: {tarefa_txt}")
                st.toast("Tarefa registrada!", icon="🚩")

        # 4. REDES SOCIAIS E CONTATO
            st.divider()
            with st.container():
                st.subheader("📱 Redes e Suporte")
            
                id_sup = str(u['ID_Supervisor']).strip()
                supervisor_data = df_usuarios[df_usuarios['ID_Usuario'].astype(str).str.strip() == id_sup]
                if not supervisor_data.empty:
                    sup_nome = supervisor_data.iloc[0]['Nome'].split()[0]
                    whats_sup = sanitize_whatsapp(supervisor_data.iloc[0]['WhatsApp'])
                    st.link_button(f"🆘 Dúvidas? Fale com {sup_nome}", f"https://wa.me/{whats_sup}", use_container_width=True)

            st.markdown("---")
            st.markdown("##### 📸 Instagram @maxmacieldf")
            insta_html = """
            <iframe src="https://www.instagram.com/maxmacieldf/embed" 
                width="100%" height="400" frameborder="0" scrolling="no" allowtransparency="true"
                style="border-radius: 15px; border: 1px solid #eee;">
            </iframe>
            """
            st.components.v1.html(insta_html, height=410)

        ###Contratos
        with tab_contratos:
            st.subheader("📄 Seus Documentos e Contratos")
            
            df_contratos = carregar_dados("Contratos") 

            if df_contratos is not None:
                meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
                
                if not meus_docs.empty:
                    for _, doc in meus_docs.iterrows():
                        link_enviado = str(doc.get('Link_Assinado', '')).strip()
                        esta_pendente = link_enviado == "" or link_enviado.lower() == "nan"

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Documento:** {doc['Nome_Arquivo']}")
                            if esta_pendente:
                                st.warning("⚠️ Aguardando sua assinatura")
                            else:
                                st.success("✅ Enviado e em análise")
                        
                        with col2:
                            st.link_button("📥 Baixar", doc['Link_Original'], use_container_width=True)
                        
                        if esta_pendente:
                            with st.expander("⬆️ Clique aqui para enviar o contrato assinado", expanded=True):
                                arquivo_assinado = st.file_uploader(
                                    "Faça upload do PDF", 
                                    type=['pdf'],
                                    key=f"up_{doc['Nome_Arquivo']}"
                                )
                                
                                if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}", type="primary"):
                                    if arquivo_assinado:
                                        with st.spinner("Enviando e atualizando..."):
                                            nome_final = f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}"
                                            link_drive = salvar_documento_drive(arquivo_assinado, nome_final)
                                            
                                            if link_drive:
                                                # Chama a função que acabamos de criar
                                                sucesso = atualizar_contrato_enviado(u['ID_Usuario'], doc['Nome_Arquivo'], link_drive)
                                                
                                                # Registra o Log (sua função original que já funciona)
                                                registrar_acao(u['ID_Usuario'], f"Envio de Contrato: {doc['Nome_Arquivo']}")
                                                
                                                if sucesso:
                                                    st.success("Sistema atualizado com sucesso!")
                                                    st.cache_data.clear() # Limpa o cache para atualizar a tela
                                                    st.rerun()
                                                else:
                                                    st.error("Documento salvo, mas não conseguimos atualizar a planilha.")
                                    else:
                                        st.warning("Selecione o PDF primeiro.")
                        st.divider()
                else:
                    st.info("Nenhum contrato encontrado.")
            
            # Opção de Suporte
            st.write("---")
            if st.button("Reportar erro em contrato", use_container_width=True):
                registrar_acao(u['ID_Usuario'], "SOLICITAÇÃO: Erro em contrato")
                st.warning("Sua solicitação foi enviada ao setor administrativo.")


    
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
