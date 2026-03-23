import gspread
import io
from datetime import datetime
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from streamlit_js_eval import get_geolocation
import time

# Diferenciando os tipos de credenciais
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build

# --- CONFIGURAÇÃO INICIAL ---

# --- ESTILIZAÇÃO VISUAL UNIFICADA "COMANDO 2026" - VERSÃO FINAL CORRIGIDA ---
st.markdown(f"""
    <style>
        /* 0. CONFIGURAÇÕES TÉCNICAS E FONTES */
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto:wght@400;700&display=swap');

        :root {{
            color-scheme: light !important;
        }}

        /* 1. CENTRALIZAÇÃO E FUNDO GLOBAL */
        [data-testid="stVerticalBlock"] > div {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }}

        .stApp {{
            background-color: #FFFFFF !important;
            color: #1D1D1B !important;
            font-family: 'Roboto', sans-serif;
        }}

        /* 2. SIDEBAR AMARELA */
        section[data-testid="stSidebar"] {{
            background-color: #FFEB00 !important;
            border-right: 5px solid #1D1D1B !important;
        }}

        /* 3. TÍTULOS ESTILO CARTAZ */
        h1, h2, h3 {{
            font-family: 'Archivo Black', sans-serif !important;
            text-transform: uppercase;
            font-style: italic;
            color: #1D1D1B !important;
            text-align: center;
        }}

        /* 4. PADRONIZAÇÃO TOTAL DE BOTÕES (MISSÕES + POPOVER) */
        .stButton > button, 
        div[data-testid="stPopover"] > button {{
            background-color: #E20613 !important;
            color: #FFFFFF !important;
            font-family: 'Archivo Black', sans-serif !important;
            border: 3px solid #1D1D1B !important;
            border-radius: 0px !important;
            text-transform: uppercase !important;
            box-shadow: 4px 4px 0px #1D1D1B !important;
            width: 100% !important;
            min-height: 3.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        /* 5. ABAS (TABS) - ESTILO ADESIVO URBANO (REFORÇADO) */
        
        /* Container das abas */
        div[data-baseweb="tab-list"] {{
            gap: 10px !important;
            background-color: transparent !important;
            padding: 10px 0 !important;
        }}

        /* Estilo base de cada aba (botão) */
        button[data-baseweb="tab"] {{
            background-color: #FFEB00 !important; /* Amarelo */
            border: 3px solid #1D1D1B !important;
            border-radius: 0px !important;
            padding: 10px 20px !important;
            font-family: 'Archivo Black', sans-serif !important;
            text-transform: uppercase !important;
            font-style: italic !important;
            color: #1D1D1B !important;
            box-shadow: 4px 4px 0px #1D1D1B !important;
            transition: 0.2s !important;
            margin-bottom: 10px !important;
        }}

        /* Aba Selecionada (Ativa) */
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #E20613 !important; /* Vira Vermelho */
            color: #FFFFFF !important;
            transform: translate(-2px, -2px) !important;
            box-shadow: 6px 6px 0px #1D1D1B !important;
        }}

        /* Remover a linha vermelha/azul padrão embaixo das abas */
        div[data-baseweb="tab-highlight"] {{
            display: none !important;
        }}
        
        /* Ajuste de texto dentro da aba */
        button[data-baseweb="tab"] p {{
            font-size: 0.85rem !important;
            font-weight: bold !important;
            color: inherit !important;
        }}

        /* 6. OUTROS COMPONENTES */
        
        div[data-testid="stExpander"], div[data-testid="stVerticalBlock"] > div[style*="border"] {{
            border: 3px solid #1D1D1B !important;
            background-color: #F4F4F4 !important;
            box-shadow: 6px 6px 0px #FFEB00 !important;
        }}

        .stTextInput input {{
            border: 2px solid #1D1D1B !important;
            text-align: center !important;
            background-color: #FFFFFF !important;
        }}

        /* LIMPEZA DE INTERFACE */
        .stDeployButton, #MainMenu, div[data-testid="stDecoration"], footer {{
            display: none !important;
        }}

        header[data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0) !important;
        }}

        .block-container {{
            padding-top: 2rem !important;
        }}

        /* Ajuste Mobile */
        @media (max-width: 768px) {{
            button[data-baseweb="tab"] {{
                font-size: 0.7rem !important;
                padding: 8px 10px !important;
            }}
        }}
    </style>
""", unsafe_allow_html=True)

# Meta tag adicional para forçar Light Mode no Mobile
st.markdown('<meta name="color-scheme" content="light">', unsafe_allow_html=True)
#agora

agora = datetime.now()

# --- FUNÇÕES DE APOIO ---


# --- MODAIS DE PRESENÇA (DIALOG) ---

@st.dialog("REGISTRO DE ENTRADA")
def modal_checkin(u, agora):
    st.markdown("""
        <div style='background-color: #FFEB00; padding: 15px; border: 3px solid #1D1D1B; text-align: center; margin-bottom: 20px;'>
            <h2 style='margin:0; font-size: 1.5rem; font-style: italic; color: #1D1D1B;'>INICIAR MISSÃO</h2>
        </div>
    """, unsafe_allow_html=True)
    
    foto_in = st.camera_input("FOTO OBRIGATÓRIA", key="cam_in_dialog")
    
    if st.button("CONFIRMAR CHECK-IN AGORA", use_container_width=True, type="primary"):
        if foto_in:
            gps_in = st.session_state.get('last_coords', "Sem GPS")
            with st.status("🚀 PROCESSANDO REGISTRO...", expanded=True) as status:
                nome_img = f"checkin_{u['Nome']}_{agora.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link = salvar_foto_drive(foto_in, nome_img)
                
                if link:
                    registrar_acao(u['ID_Usuario'], f"Check-in | Foto: {link}", localizacao=gps_in)
                    try:
                        horario_formatado = agora.strftime("%Y-%m-%d %H:%M:%S")
                        cookie_manager.set("comando2026_checkin_time", horario_formatado)
                    except Exception:
                        pass
                    
                    status.update(label="✅ ENTRADA REGISTRADA!", state="complete")
                    time.sleep(2)
                    st.rerun()
        else:
            st.error("⚠️ VOCÊ PRECISA TIRAR A FOTO!")

@st.dialog("REGISTRO DE SAÍDA")
def modal_checkout(u, agora):
    st.markdown("""
        <div style='background-color: #FFEB00; padding: 15px; border: 3px solid #1D1D1B; text-align: center; margin-bottom: 20px;'>
            <h2 style='margin:0; font-size: 1.5rem; font-style: italic; color: #1D1D1B;'>FINALIZAR MISSÃO</h2>
        </div>
    """, unsafe_allow_html=True)
    
    foto_out = st.camera_input("FOTO OBRIGATÓRIA", key="cam_out_dialog")
    
    if st.button("CONFIRMAR SAÍDA AGORA", use_container_width=True, type="primary"):
        if foto_out:
            gps_out = st.session_state.get('last_coords', "Sem GPS")
            with st.status("📡 PROCESSANDO SAÍDA...", expanded=True) as status:
                nome_img = f"checkout_{u['Nome']}_{agora.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link = salvar_foto_drive(foto_out, nome_img)
                
                if link:
                    registrar_acao(u['ID_Usuario'], f"Check-out | Foto: {link}", localizacao=gps_out)
                    try:
                        if "comando2026_checkin_time" in cookie_manager.get_all():
                            cookie_manager.delete("comando2026_checkin_time")
                    except Exception:
                        pass
                    
                    status.update(label="✅ SAÍDA REGISTRADA!", state="complete")
                    time.sleep(2)
                    st.rerun()
        else:
            st.error("⚠️ VOCÊ PRECISA TIRAR A FOTO!")

@st.dialog("COMANDO 2026: INFORME")
def modal_mensagem_dia(mensagem):
    st.markdown(f"""
        <div style='background-color: #FFEB00; padding: 20px; border: 3px solid #1D1D1B; text-align: center;'>
            <h2 style='margin:0; font-family: "Archivo Black", sans-serif; font-style: italic; color: #1D1D1B;'>MENSAGEM DO DIA</h2>
            <hr style='border: 1px solid #1D1D1B;'>
            <p style='font-size: 1.2rem; font-weight: bold; color: #1D1D1B;'>{mensagem}</p>
        </div>
        <br>
    """, unsafe_allow_html=True)
    
    # O BOTÃO É O ÚNICO QUE MUDA O ESTADO
    if st.button("ENTENDIDO / IR PARA MISSÕES", use_container_width=True, type="primary"):
        st.session_state["mensagem_exibida"] = True  # <--- MUDANÇA AQUI
        st.rerun()



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
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scope)
    except Exception as e:
        st.error(f"Erro credenciais Sheets: {e}")
        return None

def _get_gspread_client():
    creds = _get_sheets_credentials()
    return gspread.authorize(creds) if creds else None

@st.cache_data(ttl=60)
def carregar_dados(nome_aba):
    try:
        sheet_id = st.secrets["planilha"]["id"]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df = pd.read_csv(url)
        return df.astype(str).apply(lambda x: x.str.strip())
    except Exception as e:
        return None

def salvar_foto_drive(foto_arquivo, nome_arquivo):
    try:
        creds = _get_drive_credentials() 
        if not creds: return None
        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_fotos = st.secrets["google_drive"]["id_pasta_fotos"]
        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_fotos]}
        foto_bytes = io.BytesIO(foto_arquivo.getvalue())
        media = MediaIoBaseUpload(foto_bytes, mimetype='image/jpeg', resumable=False)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive: {e}")
        return None

def registrar_acao(id_usuario, tipo_acao, localizacao="Não informada"):
    try:
        client = _get_gspread_client()
        if client is None: return
        planilha_id = st.secrets["planilha"]["id"]
        planilha = client.open_by_key(planilha_id)
        aba = planilha.worksheet("Logs")
        aba.append_row([
            datetime.now().strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            str(localizacao)
        ])
        st.toast(f"✅ Log: {tipo_acao}")
    except Exception as e:
        st.error(f"Falha ao registrar log: {e}")

# ... (Funções salvar_documento_drive e atualizar_contrato_enviado permanecem iguais) ...

def salvar_documento_drive(doc_arquivo, nome_arquivo):
    try:
        creds = _get_drive_credentials() 
        if not creds: return None
        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_contratos = st.secrets["google_drive"]["id_pasta_contratos"]
        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_contratos]}
        doc_bytes = io.BytesIO(doc_arquivo.getvalue())
        media = MediaIoBaseUpload(doc_bytes, mimetype='application/pdf', resumable=False)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        drive_service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Erro no Drive (Docs): {e}")
        return None

def atualizar_contrato_enviado(id_usuario, nome_arquivo, link_drive):
    try:
        client = _get_gspread_client()
        if client is None: return False
        planilha_id = st.secrets["planilha"]["id"]
        planilha = client.open_by_key(planilha_id)
        aba = planilha.worksheet("Contratos")
        dados = aba.get_all_records()
        linha_idx = None
        for i, linha in enumerate(dados, start=2):
            if str(linha.get('ID_Usuario')) == str(id_usuario) and str(linha.get('Nome_Arquivo')) == str(nome_arquivo):
                linha_idx = i
                break
        if linha_idx:
            cabecalho = aba.row_values(1)
            if 'Link_Assinado' in cabecalho:
                col_idx = cabecalho.index('Link_Assinado') + 1
                aba.update_cell(linha_idx, col_idx, link_drive)
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar contrato: {e}")
        return False

def sanitize_whatsapp(v: str) -> str:
    if v is None: return ""
    return ''.join(filter(str.isdigit, str(v)))

# --- LOGICA DE COOKIES ---
cookie_manager = stx.CookieManager()
todos_os_cookies = cookie_manager.get_all()

if not todos_os_cookies:
    st.stop()

# --- ESTADO DE LOGIN ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "logout_em_andamento" not in st.session_state:
    st.session_state["logout_em_andamento"] = False

# ADICIONE ESTA LINHA AQUI:
if "mensagem_exibida" not in st.session_state:
    st.session_state["mensagem_exibida"] = False

# Autologin via Cookie (Só tenta se não estiver saindo)
if todos_os_cookies and not st.session_state["logout_em_andamento"]:
    user_id_cookie = todos_os_cookies.get("comando2026_user_id")
    
    if user_id_cookie and st.session_state["usuario_logado"] is None:
        df_usuarios = carregar_dados("Usuarios")
        if df_usuarios is not None:
            user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == user_id_cookie.lower().strip()]
            if not user_match.empty:
                st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                st.rerun()

# --- TELA DE LOGIN ---
if st.session_state["usuario_logado"] is None:
    # Reseta o sinal de logout para permitir novo login
    st.session_state["logout_em_andamento"] = False
    
    # Criamos um espaço no topo para centralizar verticalmente
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    
    with col_l2:
        # TÍTULO ESTILIZADO (Igual às artes)
        st.markdown("""
            <h1 style='text-align: center; font-size: 4rem; line-height: 0.9; margin-bottom: 20px;'>
                Max Maciel<br><span style='color: #E20613;'>🧢 2026</span;>
            </h1>
        """, unsafe_allow_html=True)
        
# CONTAINER DE LOGIN (Estilo Card Amarelo Centralizado)
        with st.container():
            st.markdown("""
                <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 10px 10px 0px #1D1D1B; text-align: center;'>
                    <h2 style='margin-top: 0; font-size: 1.5rem; font-family: "Archivo Black", sans-serif; font-style: italic; text-transform: uppercase; color: #1D1D1B;'>
                        Faça seu login abaixo:
                    </h2>
                </div>
            """, unsafe_allow_html=True)
            st.divider()
            # Espaço entre o título e o input
            st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
            
            # O input e o botão herdarão o estilo centralizado se estiverem dentro de colunas ou se o CSS global permitir
            # Mas para garantir o visual dentro da caixa, costumamos usar este truque de CSS:
            email_input = st.text_input("ID DE USUÁRIO (E-MAIL)", placeholder="seu@email.com", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ENTRAR NO PAINEL", use_container_width=True, type="primary"):
                with st.spinner("VALIDANDO..."):
                    df_usuarios = carregar_dados("Usuarios")
                    if df_usuarios is not None:
                        user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == email_input.lower().strip()]
                        if not user_match.empty:
                            st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                            cookie_manager.set("comando2026_user_id", email_input.lower().strip(), key="set_user_cookie")
                            st.rerun()
                        else:
                            st.error("❌ ID NÃO ENCONTRADO")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Primeiro acesso? Solicite seu ID ao seu supervisor.")

    st.stop()

# --- VARIÁVEIS DO USUÁRIO (SÓ APÓS LOGIN) ---
u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Perfil")
    st.write(f"Olá, **{u['Nome'].split()[0]}**")
    st.caption(f"Cargo: {u['Cargo']}")
    
    if st.button("Sair / Trocar Conta", use_container_width=True):
        # 1. Sinaliza que o logout começou (bloqueia auto-login)
        st.session_state["logout_em_andamento"] = True
        st.session_state["usuario_logado"] = None
        st.session_state["mensagem_exibida"] = False 
        
        # 2. Tenta deletar os cookies com chaves únicas
        try:
            cookie_manager.delete("comando2026_user_id", key="del_user")
        except:
            pass
            
        try:
            cookie_manager.delete("comando2026_checkin_time", key="del_check")
        except:
            pass

        st.success("Saindo e limpando dados...")
        
        # 3. Limpa as memórias da sessão e os caches de dados
        st.session_state.clear()
        st.cache_data.clear()
        
        # 4. Pausa crucial para o navegador apagar os cookies de fato
        import time
        time.sleep(2)
        
        # 5. Recarrega a página, voltando para o login
        st.rerun()

        
# --- CABEÇALHO BEM-VINDO (VERSÃO SEM QUEBRA DE LINHA) ---
nome_primeiro = u['Nome'].split()[0].upper()

st.markdown(f"""
    <div style='
        background-color: #FFEB00; 
        padding: 15px; 
        border: 4px solid #1D1D1B; 
        box-shadow: 8px 8px 0px #1D1D1B; 
        text-align: center;
        width: 90%;
        margin: 10px auto 25px auto;
    '>
        <h3 style='
            margin: 0; 
            font-size: 1.5rem; 
            font-family: "Archivo Black", sans-serif; 
            font-style: italic; 
            color: #1D1D1B;
            line-height: 1;
        '>
            BEM-VINDO,
        </h3>
        <h1 style='
            margin: 0; 
            font-size: 2.6rem; /* Reduzi um pouco para nomes longos caberem */
            font-family: "Archivo Black", sans-serif; 
            font-style: italic; 
            text-transform: uppercase; 
            color: #E20613;
            line-height: 1.1;
            white-space: nowrap;  /* <--- FORÇA O NOME EM UMA LINHA SÓ */
            overflow: hidden;     /* <--- EVITA QUE O NOME SAIA DO QUADRO */
            text-overflow: clip; 
        '>
            {nome_primeiro}
        </h1>
    </div>
""", unsafe_allow_html=True)


# --- VISÃO: VOLUNTÁRIO ---
if cargo_limpo in ["voluntario", "voluntário"]:
    
    # 1. Carregar dados das mensagens
    df_msgs = carregar_dados("Mensagens")
    if df_msgs is not None:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str) == str(u['ID_Grupo'])]
        
        # SÓ CHAMA O MODAL. NÃO MUDA A VARIÁVEL AQUI!
        if not msg_grupo.empty and not st.session_state["mensagem_exibida"]:
            m = msg_grupo.iloc[-1]
            modal_mensagem_dia(m['Mensagem_Inicial']) 
    
    # 1. CAPTURA DE GPS COMPACTA
    location_data = get_geolocation()
    
    # Criamos uma linha fina para o GPS
    col_status, col_btn = st.columns([3, 1])
    
    with col_status:
        if location_data:
            try:
                lat = location_data['coords']['latitude']
                lon = location_data['coords']['longitude']
                st.session_state['last_coords'] = f"{lat},{lon}"
                st.markdown("🟢 **GPS ATIVO**") # Texto simples em vez de st.success
            except:
                st.session_state['last_coords'] = "Erro GPS"
                st.markdown("🔴 **ERRO GPS - Verifique se o GPS está ativado e conceda permissão**")
        else:
            st.session_state['last_coords'] = "Aguardando..."
            st.markdown("🟡 **BUSCANDO SINAL...**")
            
    with col_btn:
        # Botão pequeno apenas com o ícone para economizar espaço
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

    with tab_missoes:
        df_msgs = carregar_dados("Mensagens")
        df_usuarios = carregar_dados("Usuarios")
        
        # Presença  
        st.divider()
        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>Registro de Presença</h2>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        
        with c1:
            # O botão já herda o estilo vermelho/sombra do seu CSS global
            if st.button("🏁 ENTRADA (CHECK-IN)", use_container_width=True, key="btn_modal_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", use_container_width=True, key="btn_modal_out"):
                modal_checkout(u, agora)



# --- SEÇÃO DE MISSÕES (ESTILO BRIEFING) ---
        if df_msgs is not None and not msg_grupo.empty:
            st.divider()
            m = msg_grupo.iloc[-1]
            
            # 1. CABEÇALHO DA SEÇÃO
            st.markdown("""
                <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                    <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>🚀 MISSÕES DO DIA</h2>
                </div>
            """, unsafe_allow_html=True)

            # 2. TAREFA DIRECIONADA (A MISSÃO PRINCIPAL - DESTAQUE TOTAL)
            t_txt = str(m['Tarefa_Direcionada']).upper() if str(m['Tarefa_Direcionada']) != "nan" else "TAREFA GERAL"
            
            with st.container(border=True): # O CSS global vai aplicar a sombra amarela aqui
                st.markdown(f"<h3 style='text-align: center; color: #1D1D1B; margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem;'>{t_txt}</p>", unsafe_allow_html=True)
                
                if st.button(f"CONCLUIR: {t_txt[:20]}...", use_container_width=True, key="btn_tarefa_principal"):
                    registrar_acao(u['ID_Usuario'], f"TAREFA CONCLUÍDA: {t_txt}", localizacao=st.session_state.get('last_coords'))
                    st.success("MISSÃO REGISTRADA!")

            st.markdown("<br>", unsafe_allow_html=True)

            # 3. SUGESTÕES DE AÇÃO (BOTÕES LADO A LADO)
            st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES RÁPIDAS</h3>", unsafe_allow_html=True)
            col_m1, col_m2 = st.columns(2)

            with col_m1:
                # Sugestão 1 (Geralmente Instagram)
                label_s1 = str(m['Sugestao_1']).upper()
                if st.button(f"🔗 {label_s1}", use_container_width=True, key="btn_s1"):
                    registrar_acao(u['ID_Usuario'], f"AÇÃO: {label_s1}", localizacao=st.session_state.get('last_coords'))
                    # Mostra o link de redirecionamento logo abaixo ao clicar
                    st.markdown(f"""
                        <a href="https://www.instagram.com/maxmacieldf/" target="_blank">
                            <div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; border: 2px solid #FFEB00; font-weight: bold;'>
                                CLIQUE AQUI P/ ABRIR INSTA
                            </div>
                        </a>
                    """, unsafe_allow_html=True)

            with col_m2:
                # Sugestão 2 (Geralmente WhatsApp/Interação)
                label_s2 = str(m['Sugestao_2']).upper()
                if st.button(f"💬 {label_s2}", use_container_width=True, key="btn_s2"):
                    registrar_acao(u['ID_Usuario'], f"AÇÃO: {label_s2}", localizacao=st.session_state.get('last_coords'))
                    st.toast("Ação registrada!", icon="💬")

            st.markdown("<br>", unsafe_allow_html=True)

    with tab_contratos:
        # (Seu código de contratos permanece o mesmo, chamando carregar_dados e as funções de upload)
        st.subheader("📄 Meus Documentos")
        df_contratos = carregar_dados("Contratos")
        if df_contratos is not None:
            meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
            for _, doc in meus_docs.iterrows():
                with st.container(border=True):
                    st.write(f"**Doc:** {doc['Nome_Arquivo']}")
                    st.link_button("📥 Baixar Original", doc['Link_Original'])
                    arq = st.file_uploader("Upload Assinado (PDF)", type=['pdf'], key=doc['Nome_Arquivo'])
                    if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}"):
                        if arq:
                            link = salvar_documento_drive(arq, f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}")
                            if link and atualizar_contrato_enviado(u['ID_Usuario'], doc['Nome_Arquivo'], link):
                                st.success("Enviado!")
                                st.rerun()

# --- VISÃO: SUPERVISOR --- 
elif cargo_limpo == "supervisor":
    st.subheader("📈 Gestão de Equipe")
    df_usuarios = carregar_dados("Usuarios")
    df_logs = carregar_dados("Logs")
    if df_usuarios is not None and df_logs is not None:
        equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str) == str(u['ID_Usuario'])]
        for _, vol in equipe.iterrows():
            with st.expander(f"👤 {vol['Nome']}"):
                v_logs = df_logs[df_logs['ID_Usuario'] == vol['ID_Usuario']].tail(5)
                st.dataframe(v_logs[['Tipo_Acao', 'Data_Hora', 'Localização']], use_container_width=True)
                w_limpo = sanitize_whatsapp(vol['WhatsApp'])
                st.link_button("Cobrar no WhatsApp", f"https://wa.me/{w_limpo}")


# --- PERFIL: ADMIN ---
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
