import gspread
import io
from datetime import datetime
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from streamlit_js_eval import get_geolocation
import time
import urllib.parse
from datetime import datetime, timedelta

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

        /* 1. CENTRALIZAÇÃO E FUNDO GRADIENTE PREMIUM (OPÇÃO B) */
        [data-testid="stVerticalBlock"] > div {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }}

        .stApp {{
            /* Gradiente diagonal cinza azulado premium - Opção B */
            background: linear-gradient(135deg, #E9ECEF 0%, #ADB5BD 100%) !important;
            background-attachment: fixed !important;
            color: #1D1D1B !important;
            font-family: 'Roboto', sans-serif;
        }}

        /* Transparência total dos containers para o gradiente brilhar */
        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"], 
        [data-testid="stVerticalBlock"],
        [data-testid="stMainBlockContainer"] {{
            background-color: transparent !important;
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

        /* 5. ABAS (TABS) - ESTILO ADESIVO URBANO (ALINHAMENTO TRAVADO) */
        
        /* Container das abas */
        div[data-baseweb="tab-list"] {{
            gap: 0px !important; /* Zerado para controlarmos via margem da aba */
            background-color: transparent !important;
            padding: 10px 0 !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }}  

        /* Estilo base de cada aba (botão inativo) */
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
            margin: 0 6px 10px 6px !important; /* Mantém a distância fixa entre elas */
            transform: none !important; /* Trava a posição */
        }}

        /* Aba Selecionada (Ativa) - FIXA NO LUGAR, APENAS MUDA COR */
        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #E20613 !important; /* Vira Vermelho */
            color: #FFFFFF !important;
            box-shadow: 4px 4px 0px #1D1D1B !important; /* Mesma sombra da inativa */
            transform: none !important; /* Sem pular para o lado */
        }}

        /* Efeito de passar o mouse APENAS nas inativas */
        button[data-baseweb="tab"][aria-selected="false"]:hover {{
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
            margin: 0 !important;
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

agora = datetime.utcnow() - timedelta(hours=3)

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
            agora_real = datetime.utcnow() - timedelta(hours=3)
            gps_in = st.session_state.get('last_coords', "Sem GPS")
            with st.status("🚀 PROCESSANDO REGISTRO...", expanded=True) as status:
                nome_img = f"checkin_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link = salvar_foto_drive(foto_in, nome_img)
                
                if link:
                    registrar_acao(u['ID_Usuario'], f"Check-in | Foto: {link}", localizacao=gps_in)
                    try:
                        horario_formatado = agora_real.strftime("%Y-%m-%d %H:%M:%S")
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
            agora_real = datetime.utcnow() - timedelta(hours=3)
            gps_out = st.session_state.get('last_coords', "Sem GPS")
            with st.status("📡 PROCESSANDO SAÍDA...", expanded=True) as status:
                nome_img = f"checkout_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
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
        agora_br = datetime.utcnow() - timedelta(hours=3)
        
        aba.append_row([
            agora_br.strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            agora_br.strftime("%d/%m/%Y %H:%M:%S"),
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

# --- ESTADO DE LOGIN ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "logout_em_andamento" not in st.session_state:
    st.session_state["logout_em_andamento"] = False

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
                Max Maciel<br><span style='color: #E20613;'>🧢 2026</span>
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
            font-size: 2.2rem; /* Reduzi um pouco para nomes longos caberem */
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
    
    # 1. CARREGAMENTO PRÉVIO DA MENSAGEM (Para evitar o NameError 'm')
    df_msgs = carregar_dados("Mensagens")
    m = None  # Inicializamos m como vazio
    
    if df_msgs is not None:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str) == str(u['ID_Grupo'])]
        if not msg_grupo.empty:
            m = msg_grupo.iloc[-1]  # Agora m existe para todo o código do voluntário
            
            # Chama o Modal do dia APENAS se não tiver sido exibido ainda
            if not st.session_state["mensagem_exibida"]:
                modal_mensagem_dia(m['Mensagem_Inicial'])

    # 3. CAPTURA DE GPS COMPACTA
    location_data = get_geolocation()
    col_status, col_btn = st.columns([3, 1])
    with col_status:
        if location_data:
            try:
                lat = location_data['coords']['latitude']
                lon = location_data['coords']['longitude']
                st.session_state['last_coords'] = f"{lat},{lon}"
                st.markdown("🟢 **GPS ATIVO**")
            except:
                st.session_state['last_coords'] = "Erro GPS"
                st.markdown("🔴 **ERRO GPS**")
        else:
            st.session_state['last_coords'] = "Aguardando..."
            st.markdown("🟡 **BUSCANDO SINAL...**")
    with col_btn:
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    # 4. ABAS DE CONTEÚDO
    tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

    with tab_missoes:
        # --- REGISTRO DE PRESENÇA ---
        st.divider()
        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>REGISTRO DE PRESENÇA</h2>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", use_container_width=True, key="btn_modal_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", use_container_width=True, key="btn_modal_out"):
                modal_checkout(u, agora)

        # --- SEÇÃO DE MISSÕES (FIXAS) ---
        st.divider()
        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>🚀 MISSÕES DIÁRIAS</h2>
            </div>
        """, unsafe_allow_html=True)

        # TAREFA PRINCIPAL (Puxa da planilha se m existir, senão usa texto padrão)
        if m is not None and str(m['Tarefa_Direcionada']) != "nan":
            t_txt = str(m['Tarefa_Direcionada']).upper()
        else:
            t_txt = "MOBILIZAÇÃO GERAL E PANFLETAGEM"

        with st.container(border=True): 
            st.markdown(f"<h3 style='text-align: center; color: #1D1D1B; margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem;'>{t_txt}</p>", unsafe_allow_html=True)
            
            if st.button(f"CONCLUIR MISSÃO DE HOJE", use_container_width=True, key="btn_tarefa_fixa"):
                registrar_acao(u['ID_Usuario'], f"CONCLUIU: {t_txt}", localizacao=st.session_state.get('last_coords'))
            
                st.success("MISSÃO REGISTRADA COM SUCESSO!")

        st.markdown("<br>", unsafe_allow_html=True)

# --- AÇÕES DE REDE FIXAS ---
        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            # --- LÓGICA INSTAGRAM ---
            if st.button("📸 CURTA, COMENTE E COMPARTILHE NOSSO ÚLTIMO POST!", use_container_width=True, key="fixo_insta"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: INTERAÇÃO INSTAGRAM", localizacao=st.session_state.get('last_coords'))
                st.markdown(f"""
                    <a href="https://www.instagram.com/maxmacieldf/" target="_blank">
                        <div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; border: 2px solid #FFEB00; font-weight: bold; font-size: 0.8rem;'>
                            ABRIR PERFIL DO MAX ↗️
                        </div>
                    </a>
                """, unsafe_allow_html=True)

        with col_m2:
            # --- LÓGICA WHATSAPP ---
            if st.button("💬 TRAGA UM NOVO AMIGO PARA SER VOLUNTÁRIO!", use_container_width=True, key="fixo_whats"):
                # 1. Registra a ação no banco de dados
                registrar_acao(u['ID_Usuario'], "AÇÃO: TRAZER NOVO VOLUNTÁRIO!", localizacao=st.session_state.get('last_coords'))
                
                # 2. Prepara a mensagem padrão (URL Encoded)
                # Você pode alterar o texto abaixo como quiser!
                mensagem_pronta = "Salve! Dá uma olhada no que o Max Maciel está fazendo pelo DF. Estou junto nessa campanha e gostaria do seu apoio. Vamos juntos? 🚀 https://www.instagram.com/maxmacieldf/"
                
                import urllib.parse
                msg_url = urllib.parse.quote(mensagem_pronta)
                
                # 3. Mostra o botão de redirecionamento (estilo ID Visual)
                st.markdown(f"""
                    <a href="https://wa.me/?text={msg_url}" target="_blank">
                        <div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; border: 2px solid #FFEB00; font-weight: bold; font-size: 0.8rem;'>
                            ESCOLHER AMIGO ↗️
                        </div>
                    </a>
                """, unsafe_allow_html=True)

    # --- TAB DE CONTRATOS (Permanece igual) ---
    with tab_contratos:
        # Seu código de contratos aqui...
        pass

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

    df_usuarios = carregar_dados("Usuarios")
    df_logs = carregar_dados("Logs")

    if df_usuarios is not None and df_logs is not None:
        minha_equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str) == str(u['ID_Usuario'])]

        # 1. CRIAMOS UM ESPAÇO EM BRANCO NO TOPO PARA AS MÉTRICAS
        espaco_metricas = st.empty()

        # 2. SELETOR DE DATA (Agora aparece entre as Métricas e o Status)
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        c_data, c_vazio = st.columns([1.5, 1])
        with c_data:
            data_selecionada = st.date_input("📅 SELECIONE A DATA", datetime.now())
        
        data_str = data_selecionada.strftime("%d/%m/%Y")

        # --- CÁLCULOS BASEADOS NA DATA SELECIONADA ---
        logs_dia = df_logs[df_logs['Data_Hora'].str.contains(data_str)]
        ativos_dia = logs_dia[logs_dia['ID_Usuario'].isin(minha_equipe['ID_Usuario'])]
        
        total_vol = len(minha_equipe)
        num_ativos = ativos_dia[ativos_dia['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
        total_acoes = len(ativos_dia)

        # 3. PREENCHEMOS O ESPAÇO DO TOPO COM AS MÉTRICAS CALCULADAS
        espaco_metricas.markdown(f"""
            <div style="display: flex; justify-content: space-between; gap: 5px; width: 100%; margin-top: 15px; margin-bottom: 5px;">
                <div style="flex: 1; background-color: #FFFFFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px 2px;">
                    <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666; white-space: nowrap;">EQUIPE</p>
                    <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #1D1D1B; line-height: 1;">{total_vol}</p>
                </div>
                <div style="flex: 1; background-color: #FFFFFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px 2px;">
                    <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666; white-space: nowrap;">ATIVOS</p>
                    <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #E20613; line-height: 1;">{num_ativos}</p>
                </div>
                <div style="flex: 1; background-color: #FFFFFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px 2px;">
                    <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666; white-space: nowrap;">AÇÕES</p>
                    <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #1D1D1B; line-height: 1;">{total_acoes}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

# 4. TÍTULO DE STATUS (Com margin-top negativo para grudar no calendário)
        st.markdown(f"<h3 style='font-size: 1.2rem; text-align: left; margin-bottom: 10px; margin-top: -15px;'>📋 STATUS ({data_str[:5]})</h3>", unsafe_allow_html=True)
        
        # --- LOOP DE VOLUNTÁRIOS ---
        for _, vol in minha_equipe.iterrows():
            logs_vol_dia = df_logs[(df_logs['ID_Usuario'] == vol['ID_Usuario']) & (df_logs['Data_Hora'].str.contains(data_str))]
            ultimos_logs = logs_vol_dia.tail(5)
            
            tem_checkin = not logs_vol_dia[logs_vol_dia['Tipo_Acao'].str.contains("Check-in")].empty
            tem_missao = not logs_vol_dia[logs_vol_dia['Tipo_Acao'].str.contains("CONCLUIU:")].empty
            tem_redes = not logs_vol_dia[logs_vol_dia['Tipo_Acao'].str.contains("AÇÃO:")].empty
            
            if tem_checkin and tem_missao: status_label = "🔥 COMPLETO"
            elif tem_checkin: status_label = "🟢 EM CAMPO"
            elif tem_redes: status_label = "🟡 REDES"
            else: status_label = "⚪ OFF"

            with st.expander(f"{status_label} | {vol['Nome'].upper()}"):
                if not ultimos_logs.empty:
                    feed_html = ""
                    for _, row in ultimos_logs[::-1].iterrows():
                        acao_raw = str(row['Tipo_Acao'])
                        hora = row['Data_Hora'].split()[-1][:5]
                        texto_limpo = acao_raw.replace("AÇÃO: ", "").replace("CONCLUIU: ", "").split("|")[0].split("Foto:")[0].strip().upper()
                        loc = str(row['Localização'])
                        botao_mapa = ""
                        
                        if "," in loc:
                            botao_mapa = f"<a href='https://www.google.com/maps?q={loc}' target='_blank' style='background-color: #E20613; color: #FFFFFF; font-family: \"Archivo Black\", sans-serif; font-size: 0.55rem; padding: 4px 8px; text-decoration: none; border: 1px solid #1D1D1B; box-shadow: 2px 2px 0px #1D1D1B; text-transform: uppercase; white-space: nowrap;'>📍 MAPA</a>"

                        feed_html += f"<div style='background-color: #F4F4F4; border: 2px solid #1D1D1B; padding: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 3px 3px 0px #1D1D1B; margin-bottom: 10px;'>"
                        feed_html += f"<div style='display: flex; flex-direction: column;'>"
                        feed_html += f"<span style='font-family: \"Archivo Black\", sans-serif; font-size: 0.85rem; color: #1D1D1B;'>{texto_limpo}</span>"
                        feed_html += f"<span style='font-size: 0.75rem; color: #666; font-weight: bold; margin-top: 4px;'>🕒 {hora}</span>"
                        feed_html += "</div>"
                        feed_html += f"<div>{botao_mapa}</div>"
                        feed_html += "</div>"
                    
                    st.markdown(feed_html, unsafe_allow_html=True)
                else:
                    st.info(f"Nenhuma atividade registrada em {data_str[:5]}.")

                st.divider()
                w_limpo = sanitize_whatsapp(vol['WhatsApp'])
                p_nome = vol['Nome'].split()[0]
                c_wa1, c_wa2 = st.columns(2)
                
                with c_wa1:
                    # Correção: "btn_label, msg =" em todas as linhas
                    if tem_checkin and tem_missao: 
                        btn_label, msg = "🚀 PARABÉNS", f"Sensacional, {p_nome}! Vi seu relatório de {data_str[:5]}. Missão completa! 🔥"
                    elif tem_checkin: 
                        btn_label, msg = "💪 MOTIVAR", f"Bora, {p_nome}! Vi que no dia {data_str[:5]} você foi pra rua. Tamo junto! 🚀"
                    elif tem_redes: 
                        btn_label, msg = "⚡ REFORÇAR", f"Boa, {p_nome}! Vi sua mobilização digital no dia {data_str[:5]}. Nas próximas não esquece o check-in na rua! 💪"
                    else: 
                        btn_label, msg = "⚠️ COBRAR", f"Fala, {p_nome}! Tudo certo? Notei que não houve registro de atividades em {data_str[:5]}. Algum imprevisto?"

                    st.link_button(btn_label, f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg)}", use_container_width=True, type="primary")
                
                with c_wa2:
                    st.link_button("💬 ABRIR CHAT", f"https://wa.me/{w_limpo}", use_container_width=True)

        # 5. BOTÃO DE ENVIAR RELATÓRIO NO FINAL (Abaixo de todos os box de voluntários)
        st.markdown("<br>", unsafe_allow_html=True)
        relatorio_msg = (
            f"📊 *RELATÓRIO DA EQUIPE - COMANDO 2026*\n"
            f"📅 Data: {data_str}\n"
            f"👤 Supervisor: {nome_primeiro}\n\n"
            f"👥 Total da Equipe: {total_vol}\n"
            f"🔥 Ativos na Data: {num_ativos}\n"
            f"🎯 Ações Realizadas: {total_acoes}\n\n"
            f"Vamos pra cima! 🚀"
        )
        st.link_button("📲 ENVIAR RELATÓRIO P/ COORDENAÇÃO", f"https://api.whatsapp.com/send?text={urllib.parse.quote(relatorio_msg)}", use_container_width=True, type="primary")
        st.markdown("<br><br>", unsafe_allow_html=True)



# --- PERFIL: ADMIN (COORDENAÇÃO) ---
elif cargo_limpo == "admin":


    # Carrega as bases principais
    df_usuarios = carregar_dados("Usuarios")
    df_logs = carregar_dados("Logs")

    if df_usuarios is None or df_logs is None:
        st.error("Falha ao carregar o banco de dados principal.")
        st.stop()

    # 2. ABAS DE GESTÃO (Estilo Adesivo)
    tab_hierarquia, tab_mensagens, tab_logs, tab_cadastro = st.tabs([
        "👥 EQUIPES", "📝 MISSÕES", "📊 DASHBOARD", "➕ CADASTRO"
    ])

    # ==========================================
    # ABA 1: ESTRUTURA DE EQUIPES
    # ==========================================
    with tab_hierarquia:
        st.markdown("<h2 style='font-size: 1.5rem; text-align: left; margin-bottom: 15px;'>ESTRUTURA DE EQUIPES</h2>", unsafe_allow_html=True)
        
        supervisores = df_usuarios[df_usuarios['Cargo'].str.lower().str.strip() == "supervisor"]
        
        if supervisores.empty:
            st.warning("Nenhum supervisor encontrado na base de dados.")
        else:
            for _, sup in supervisores.iterrows():
                equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str).str.strip() == str(sup['ID_Usuario']).strip()]
                qtd_equipe = len(equipe)
                
                # Card do Supervisor
                st.markdown(f"""
                    <div style="background-color: #FFFFFF; border: 3px solid #1D1D1B; padding: 12px; margin-bottom: 5px; box-shadow: 4px 4px 0px #1D1D1B; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; font-size: 1.1rem; color: #E20613; text-align: left;">{sup['Nome'].upper()}</h3>
                            <span style="font-size: 0.75rem; color: #666; font-weight: bold;">GRUPO: {sup['ID_Grupo']} | VOLUNTÁRIOS: {qtd_equipe}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Expander nativo com os voluntários
                with st.expander(f"VER EQUIPE DE {sup['Nome'].split()[0].upper()}"):
                    # Botão de contato com o supervisor
                    w_sup = sanitize_whatsapp(sup['WhatsApp'])
                    st.link_button(f"💬 FALAR COM SUPERVISOR", f"https://wa.me/{w_sup}", use_container_width=True)
                    st.divider()
                    
                    if not equipe.empty:
                        for _, vol in equipe.iterrows():
                            # Lista simples e limpa
                            st.markdown(f"<div style='border-bottom: 1px solid #ddd; padding: 5px 0; font-size: 0.85rem;'><b>🚩 {vol['Nome'].upper()}</b><br><span style='color:#666;'>ID: {vol['ID_Usuario']}</span></div>", unsafe_allow_html=True)
                    else:
                        st.caption("Nenhum voluntário vinculado.")
                
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)


    # ==========================================
    # ABA 2: MENSAGENS E MISSÕES
    # ==========================================
    with tab_mensagens:
        st.markdown("<h2 style='font-size: 1.5rem; text-align: left; margin-bottom: 15px;'>DIRETRIZES DO DIA</h2>", unsafe_allow_html=True)
        
        try:
            client = _get_gspread_client()
            if client is None: raise RuntimeError("GSpread indisponível")
            
            planilha = client.open_by_key(st.secrets["planilha"]["id"])
            aba_msg = planilha.worksheet("Mensagens")
            df_msg = pd.DataFrame(aba_msg.get_all_records())

            lista_alvos = df_msg["ID_Alvo"].unique().tolist()
            alvo_selecionado = st.selectbox("SELECIONE O GRUPO ALVO:", ["Novo..."] + lista_alvos)

            with st.container(border=True): # Aplica a sombra/borda do CSS Global
                with st.form("form_admin_msg"):
                    st.markdown("<h3 style='font-size: 1.1rem; text-align: center; color: #E20613;'>EDITAR MISSÃO</h3>", unsafe_allow_html=True)
                    
                    if alvo_selecionado == "Novo...":
                        id_alvo, msg_i, tar, dat = "", "", "", ""
                    else:
                        d = df_msg[df_msg["ID_Alvo"] == alvo_selecionado].iloc[-1]
                        id_alvo = d.get("ID_Alvo", "")
                        msg_i = d.get("Mensagem_Inicial", "")
                        tar = d.get("Tarefa_Direcionada", "")
                        dat = d.get("Data_Referencia", "")

                    f_id = st.text_input("ID do Grupo Alvo (Ex: ZONA_NORTE):", value=id_alvo)
                    f_dat = st.text_input("Data de Referência (Ex: 24/03/2026):", value=dat)
                    f_msg = st.text_area("Mensagem do Dia (Aviso Geral):", value=msg_i, height=100)
                    f_tar = st.text_area("Missão Prioritária de Rua (Tarefa Principal):", value=tar, height=100)

                    # As colunas de Sugestão 1 e 2 foram deixadas em branco pois agora são fixas no código
                    st.info("💡 As ações de Instagram e WhatsApp agora são fixas no aplicativo dos voluntários para facilitar a usabilidade.")

                    if st.form_submit_button("🚀 SALVAR DIRETRIZES"):
                        nova_linha = [f_id, f_msg, "", "", f_tar, f_dat] # Deixamos as sugestões vazias

                        if alvo_selecionado != "Novo...":
                            try:
                                cell = aba_msg.find(str(alvo_selecionado))
                                if cell: aba_msg.delete_rows(cell.row)
                            except: pass

                        aba_msg.append_row(nova_linha)
                        st.success("✅ MISSÃO ATUALIZADA NO SISTEMA!")
                        st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao conectar com a planilha: {e}")


    # ==========================================
    # ABA 3: DASHBOARD GERAL
    # ==========================================
    with tab_logs:
        st.markdown("<h2 style='font-size: 1.5rem; text-align: left; margin-bottom: 5px;'>MONITORAMENTO GLOBAL</h2>", unsafe_allow_html=True)
        
        # Tratamento de Dados
        df_logs['Data_Hora_DT'] = pd.to_datetime(df_logs['Data_Hora'], dayfirst=True, errors='coerce')
        df_completo = pd.merge(df_logs, df_usuarios[['ID_Usuario', 'Nome']], on='ID_Usuario', how='left')
        df_completo['Nome'] = df_completo['Nome'].fillna(df_completo['ID_Usuario'])

        hoje_str = agora.strftime("%d/%m/%Y")
        
        # Botões de Filtro estáticos (Mais estáveis que radio no mobile)
        filtro_tipo = st.selectbox("PERÍODO DE ANÁLISE:", ["Hoje", "Histórico Completo"])
        
        if filtro_tipo == "Hoje":
            df_filtrado = df_completo[df_completo['Data_Hora'].astype(str).str.contains(hoje_str)].copy()
        else:
            df_filtrado = df_completo.copy()

        # Métricas Globais (Cards Neo-Brutalistas)
        total_acoes = len(df_filtrado)
        pessoas_ativas = df_filtrado['ID_Usuario'].nunique()
        checkins = len(df_filtrado[df_filtrado['Tipo_Acao'].str.contains("Check-in")])

        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; gap: 8px; width: 100%; margin-top: 15px; margin-bottom: 20px;">
                <div style="flex: 1; background-color: #FFFFFF; border: 3px solid #1D1D1B; box-shadow: 4px 4px 0px #1D1D1B; text-align: center; padding: 10px 2px;">
                    <p style="margin: 0; font-size: 0.65rem; font-family: 'Archivo Black'; color: #666;">AÇÕES</p>
                    <p style="margin: 0; font-size: 1.6rem; font-family: 'Archivo Black'; color: #1D1D1B; line-height: 1;">{total_acoes}</p>
                </div>
                <div style="flex: 1; background-color: #FFFFFF; border: 3px solid #1D1D1B; box-shadow: 4px 4px 0px #1D1D1B; text-align: center; padding: 10px 2px;">
                    <p style="margin: 0; font-size: 0.65rem; font-family: 'Archivo Black'; color: #666;">ATIVOS</p>
                    <p style="margin: 0; font-size: 1.6rem; font-family: 'Archivo Black'; color: #E20613; line-height: 1;">{pessoas_ativas}</p>
                </div>
                <div style="flex: 1; background-color: #FFFFFF; border: 3px solid #1D1D1B; box-shadow: 4px 4px 0px #1D1D1B; text-align: center; padding: 10px 2px;">
                    <p style="margin: 0; font-size: 0.65rem; font-family: 'Archivo Black'; color: #666;">PRESENÇA</p>
                    <p style="margin: 0; font-size: 1.6rem; font-family: 'Archivo Black'; color: #1D1D1B; line-height: 1;">{checkins}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if not df_filtrado.empty:
            st.markdown("<h3 style='font-size: 1.2rem; text-align: left; margin-top: 20px;'>🚀 RANKING DE ATIVIDADES</h3>", unsafe_allow_html=True)
            
            contagem_tipo = df_filtrado['Tipo_Acao'].value_counts().reset_index()
            contagem_tipo.columns = ['Atividade', 'Qtd']
            
            # Ranking com nossa ID Visual (Vermelho e Amarelo)
            html_ranking = "<div style='display: flex; flex-direction: column; gap: 8px;'>"
            for _, row in contagem_tipo.iterrows():
                nome_acao = str(row['Atividade']).split("|")[0].strip().upper()
                html_ranking += f"""
                    <div style="background-color: #FFFFFF; padding: 12px; border: 2px solid #1D1D1B; border-left: 8px solid #FFEB00; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Archivo Black', sans-serif; font-size: 0.85rem; color: #1D1D1B;">{nome_acao}</span>
                        <span style="background-color: #1D1D1B; color: #FFEB00; font-family: 'Archivo Black', sans-serif; padding: 4px 10px; font-size: 0.85rem;">{row['Qtd']}</span>
                    </div>
                """
            html_ranking += "</div>"
            st.markdown(html_ranking, unsafe_allow_html=True)

            st.divider()

            # Tabela NATIVA do Streamlit (Muito estável)
            st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>📄 ÚLTIMOS REGISTROS (DETALHADO)</h3>", unsafe_allow_html=True)
            
            df_display = df_filtrado.sort_values(by="Data_Hora_DT", ascending=False)[['Nome', 'Tipo_Acao', 'Data_Hora']]
            st.dataframe(
                df_display,
                column_config={"Nome": "Membro", "Tipo_Acao": "Ação", "Data_Hora": "Horário"},
                use_container_width=True, hide_index=True
            )
            
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 BAIXAR RELATÓRIO COMPLETO (CSV)", data=csv, file_name=f'relatorio_{filtro_tipo.lower()}.csv', mime='text/csv', use_container_width=True, type="primary")


    # ==========================================
    # ABA 4: CADASTRO DE USUÁRIOS
    # ==========================================
    with tab_cadastro:
        st.markdown("<h2 style='font-size: 1.5rem; text-align: left; margin-bottom: 15px;'>👤 NOVO INTEGRANTE</h2>", unsafe_allow_html=True)
        
        if df_usuarios is not None:
            lista_supervisores = df_usuarios[df_usuarios['Cargo'].str.lower().str.strip() == "supervisor"]['ID_Usuario'].unique().tolist()
            lista_grupos = sorted(df_usuarios['ID_Grupo'].unique().tolist())
            
            with st.container(border=True):
                with st.form("form_novo_usuario", clear_on_submit=True):
                    
                    novo_id = st.text_input("ID DE ACESSO (E-mail):", placeholder="exemplo@email.com").strip().lower()
                    novo_nome = st.text_input("NOME COMPLETO:")
                    novo_whats = st.text_input("WHATSAPP (Com DDD):", placeholder="61988887777")
                    
                    novo_cargo = st.selectbox("CARGO DO SISTEMA:",["Voluntario", "Supervisor", "Admin"])
                    novo_grupo = st.selectbox("GRUPO DE ATUAÇÃO (ID):", options=lista_grupos)
                    novo_sup_selecionado = st.selectbox("SUPERVISOR RESPONSÁVEL:", options=["Nenhum"] + lista_supervisores)

                    if st.form_submit_button("✅ SALVAR NOVO INTEGRANTE"):
                        if not novo_id or not novo_nome or not novo_whats:
                            st.error("Preencha ID, Nome e WhatsApp.")
                        elif novo_cargo == "Voluntario" and novo_sup_selecionado == "Nenhum":
                            st.error("⚠️ Voluntários precisam ter um Supervisor atribuído.")
                        else:
                            try:
                                client = _get_gspread_client()
                                planilha = client.open_by_key(st.secrets["planilha"]["id"])
                                aba_users = planilha.worksheet("Usuarios")
                                
                                valor_sup = novo_sup_selecionado if novo_sup_selecionado != "Nenhum" else ""
                                aba_users.append_row([novo_id, novo_nome, novo_whats, novo_cargo, novo_grupo, valor_sup])

                                st.success("🚀 NOVO INTEGRANTE SALVO COM SUCESSO!")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"Erro ao salvar: {e}")
