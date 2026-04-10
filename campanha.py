# =============================================================================
# CAMPANHA.PY - ARQUIVO PRINCIPAL (UI STREAMLIT)
# =============================================================================

import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
from streamlit_js_eval import get_geolocation
import time
import urllib.parse
import xlsxwriter
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta, timezone
import io

from utils import (
    get_agora_br,
    validar_gps_basico,
    sanitize_whatsapp,
    obter_endereco_simples,
    _get_gspread_client,
    carregar_dados,
    salvar_foto_drive,
    salvar_documento_drive,
    registrar_acao,
    registrar_novo_contrato_admin,
    atualizar_contrato_enviado,
    # Funções de gestão de grupos (VERSÕES COM CACHE)
    carregar_macro_grupos_cached,
    carregar_grupos_completos_cached,
    criar_novo_grupo,
    criar_novo_macro_grupo,
    editar_grupo,
    excluir_grupo
)


# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

st.set_page_config(
    page_title="COMANDO 2026",
    page_icon="🧢",
)

# =============================================================================
# ESTILIZAÇÃO VISUAL UNIFICADA "COMANDO 2026"
# =============================================================================

st.markdown(f"""
    <style>
        /* 0. CONFIGURAÇÕES TÉCNICAS E FONTES */
        @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Roboto:wght@400;700&display=swap');

        :root {{
            color-scheme: light !important;
        }}

        [data-testid="stVerticalBlock"] > div {{
            width: 100%;
        }}

        .stApp {{
            background: linear-gradient(135deg, #E9ECEF 0%, #ADB5BD 100%) !important;
            background-attachment: fixed !important;
            color: #1D1D1B !important;
            font-family: 'Roboto', sans-serif;
        }}

        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"], 
        [data-testid="stVerticalBlock"],
        [data-testid="stMainBlockContainer"] {{
            background-color: transparent !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: #FFEB00 !important;
            border-right: 5px solid #1D1D1B !important;
        }}

        h1, h2, h3 {{
            font-family: 'Archivo Black', sans-serif !important;
            text-transform: uppercase;
            font-style: italic;
            color: #1D1D1B !important;
            text-align: center;
        }}

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

        div[data-baseweb="tab-list"] {{
            gap: 0px !important;
            background-color: transparent !important;
            padding: 10px 0 !important;
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }}

        button[data-baseweb="tab"] {{
            background-color: #FFEB00 !important;
            border: 3px solid #1D1D1B !important;
            border-radius: 0px !important;
            padding: 10px 20px !important;
            font-family: 'Archivo Black', sans-serif !important;
            text-transform: uppercase !important;
            font-style: italic !important;
            color: #1D1D1B !important;
            box-shadow: 4px 4px 0px #1D1D1B !important;
            transition: 0.2s !important;
            margin: 0 6px 10px 6px !important;
            transform: none !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #E20613 !important;
            color: #FFFFFF !important;
            box-shadow: 4px 4px 0px #1D1D1B !important;
            transform: none !important;
        }}

        button[data-baseweb="tab"][aria-selected="false"]:hover {{
            transform: translate(-2px, -2px) !important;
            box-shadow: 6px 6px 0px #1D1D1B !important;
        }}

        div[data-baseweb="tab-highlight"] {{
            display: none !important;
        }}

        button[data-baseweb="tab"] p {{
            font-size: 0.85rem !important;
            font-weight: bold !important;
            color: inherit !important;
            margin: 0 !important;
        }}

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

        footer {{
            display: none !important;
            visibility: hidden !important;
        }}

        div[data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stHeaderActionElements"], .stDeployButton {{
            display: none !important;
            visibility: hidden !important;
        }}

        header[data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0) !important;
            color: #1D1D1B !important;
        }}

        .block-container {{
            padding-top: 2rem !important;
        }}

        @media (max-width: 768px) {{
            button[data-baseweb="tab"] {{
                font-size: 0.7rem !important;
                padding: 8px 10px !important;
            }}
        }}

        button[aria-label="Close"] {{
            display: none !important;
        }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<meta name="color-scheme" content="light">', unsafe_allow_html=True)

# =============================================================================
# ESTADO E COOKIES
# =============================================================================

cookie_manager = stx.CookieManager()
todos_os_cookies = cookie_manager.get_all()

if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if "logout_em_andamento" not in st.session_state:
    st.session_state["logout_em_andamento"] = False

if "mensagem_exibida" not in st.session_state:
    st.session_state["mensagem_exibida"] = False

if "error_log" not in st.session_state:
    st.session_state["error_log"] = []


# =============================================================================
# MODAIS DE PRESENÇA (DIALOG)
# =============================================================================

@st.dialog("REGISTRO DE ENTRADA")
def modal_checkin(u, agora):
    st.markdown("""
        <div style='background-color: #FFEB00; padding: 15px; border: 3px solid #1D1D1B; text-align: center; margin-bottom: 20px;'>
            <h2 style='margin:0; font-size: 1.5rem; font-style: italic; color: #1D1D1B;'>INICIAR MISSÃO</h2>
        </div>
    """, unsafe_allow_html=True)

    foto_in = st.camera_input("FOTO OBRIGATÓRIA", key="cam_in_dialog")

    if st.button("CONFIRMAR CHECK-IN AGORA", width='stretch', type="primary"):
        if foto_in:
            agora_real = get_agora_br()
            gps_in = st.session_state.get('last_coords', "Sem GPS")
            with st.status("🚀 PROCESSANDO REGISTRO...", expanded=True) as status:
                nome_img = f"checkin_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link = salvar_foto_drive(foto_in, nome_img, st.secrets)

                if link:
                    registrar_acao(
                        u['ID_Usuario'],
                        f"Check-in | Foto: {link}",
                        localizacao=gps_in,
                        feedback="",
                        secrets=st.secrets,
                        error_log=st.session_state.get('error_log')
                    )
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
    st.divider()

    st.markdown("### 📊 RELATO DO DIA")
    clima = st.select_slider(
        "COMO FOI O TRABALHO HOJE?",
        options=["⚠️ DIFÍCIL", "😐 NORMAL", "🔥 EXCELENTE"],
        value="😐 NORMAL"
    )
    obs = st.text_area("OBSERVAÇÕES:", placeholder="Ex: chuva, falta de material...", height=80)

    if st.button("CONFIRMAR SAÍDA", width='stretch', type="primary"):
        if foto_out:
            agora_real = get_agora_br()
            gps_out = st.session_state.get('last_coords', "Sem GPS")

            with st.spinner("📡 ENVIANDO DADOS..."):
                nome_img = f"checkout_{u['Nome']}_{agora_real.strftime('%d-%m-%Y_%H-%M')}.jpg"
                link_drive = salvar_foto_drive(foto_out, nome_img, st.secrets)

                if link_drive:
                    acao_texto = f"Check-out | Foto: {link_drive}"
                    feedback_texto = f"{clima} | Obs: {obs if obs else 'Nenhuma'}"

                    registrar_acao(
                        u['ID_Usuario'],
                        acao_texto,
                        localizacao=gps_out,
                        feedback=feedback_texto,
                        secrets=st.secrets,
                        error_log=st.session_state.get('error_log')
                    )

                    try:
                        if "comando2026_checkin_time" in cookie_manager.get_all():
                            cookie_manager.delete("comando2026_checkin_time")
                    except:
                        pass

                    st.success("✅ TUDO SALVO! BOM DESCANSO.")
                    time.sleep(2)
                    st.rerun()
        else:
            st.error("⚠️ VOCÊ PRECISA TIRAR A FOTO PARA ENCERRAR!")


# =============================================================================
# AUTOLOGIN VIA COOKIE
# =============================================================================

if todos_os_cookies and not st.session_state["logout_em_andamento"]:
    user_id_cookie = todos_os_cookies.get("comando2026_user_id")

    if user_id_cookie and st.session_state["usuario_logado"] is None:
        df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"])
        if df_usuarios is not None:
            user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == user_id_cookie.lower().strip()]
            if not user_match.empty:
                st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                st.rerun()

# =============================================================================
# TELA DE LOGIN
# =============================================================================

if st.session_state["usuario_logado"] is None:
    st.session_state["logout_em_andamento"] = False
    st.markdown("<br><br>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])

    with col_l2:
        st.markdown("""
            <h1 style='text-align: center; font-size: 4rem; line-height: 0.9; margin-bottom: 20px; margin-top: -100px'>
                Max Maciel<br><span style='color: #E20613;'>🧢 2026</span>
            </h1>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
                <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 10px 10px 0px #1D1D1B; text-align: center;'>
                    <h2 style='margin-top: 0; font-size: 1.5rem; font-family: "Archivo Black", sans-serif; font-style: italic; text-transform: uppercase; color: #1D1D1B;'>
                        Faça seu login abaixo:
                    </h2>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

            email_input = st.text_input("ID DE USUÁRIO (E-MAIL)", placeholder="seu@email.com",
                                        label_visibility="collapsed")

            if st.button("ENTRAR NO PAINEL", width='stretch', type="primary"):
                with st.spinner("VALIDANDO..."):
                    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"])
                    if df_usuarios is not None:
                        user_match = df_usuarios[df_usuarios['ID_Usuario'].str.lower() == email_input.lower().strip()]
                        if not user_match.empty:
                            st.session_state["usuario_logado"] = user_match.iloc[0].to_dict()
                            cookie_manager.set("comando2026_user_id", email_input.lower().strip(),
                                               key="set_user_cookie")
                            st.rerun()
                        else:
                            st.error("❌ ID NÃO ENCONTRADO")

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Primeiro acesso? Solicite seu ID ao seu supervisor.")

    st.stop()

# =============================================================================
# VARIÁVEIS DO USUÁRIO (APÓS LOGIN)
# =============================================================================

u = st.session_state["usuario_logado"]
cargo_limpo = str(u['Cargo']).strip().lower()
agora = get_agora_br()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("👤 Perfil")
    st.write(f"Olá, **{u['Nome'].split()[0]}**")
    st.caption(f"Cargo: {u['Cargo']}")

    if st.button("🔄 ATUALIZAR PAINEL", width="stretch"):
        with st.spinner("Buscando dados..."):
            st.cache_data.clear()
            st.rerun()

    if st.button("Sair / Trocar Conta", width='stretch'):
        st.session_state["logout_em_andamento"] = True
        st.session_state["usuario_logado"] = None
        st.session_state["mensagem_exibida"] = False

        try:
            cookie_manager.delete("comando2026_user_id", key="del_user")
            cookie_manager.delete("comando2026_checkin_time", key="del_check")
        except:
            pass

        st.success("Saindo e limpando dados...")
        st.session_state.clear()
        st.cache_data.clear()
        time.sleep(2)
        st.rerun()

# =============================================================================
# CABEÇALHO BEM-VINDO
# =============================================================================

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
            font-size: 2.2rem; 
            font-family: "Archivo Black", sans-serif; 
            font-style: italic; 
            text-transform: uppercase; 
            color: #E20613;
            line-height: 1.1;
            white-space: nowrap;  
            overflow: hidden;     
            text-overflow: clip; 
            margin-top: -30px;
        '>
            {nome_primeiro}
        </h1>
    </div>
""", unsafe_allow_html=True)

# =============================================================================
# VISÃO: COLABORADOR
# =============================================================================

if cargo_limpo == "colaborador":

    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"])
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"])
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"])
    m = None

    hoje_str = agora.strftime("%d/%m/%Y")
    meus_logs_hoje = df_logs[(df_logs['ID_Usuario'] == u['ID_Usuario']) & (
        df_logs['Data_Hora'].str.contains(hoje_str))] if df_logs is not None else pd.DataFrame()
    qtd_acoes_hoje = len(meus_logs_hoje)

    st.markdown(f"""
        <div style='
            background-color: #FFEB00;
            border-top: 2px solid #1D1D1B;
            border-bottom: 2px solid #1D1D1B;
            padding: 6px 0;
            margin: 10px 0 25px 0;
            display: flex;
            justify-content: center;
            gap: 40px;
            font-family: "Archivo Black", sans-serif;
            text-transform: uppercase;
            font-style: italic;
        '>
            <span style='color: #1D1D1B; font-size: 0.9rem;'>
                <span style='color: #E20613;'>●</span> AÇÕES HOJE: {qtd_acoes_hoje}
            </span>
            <span style='color: #1D1D1B; font-size: 0.9rem;'>
                <span style='color: #E20613;'>●</span> STATUS: {'ATIVO' if qtd_acoes_hoje > 0 else 'OFF'}
            </span>
        </div>
    """, unsafe_allow_html=True)

    if df_msgs is not None and not df_msgs.empty:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str).str.strip() == str(u['ID_Grupo']).strip()]

        if not msg_grupo.empty:
            m = msg_grupo.iloc[-1]

            if not st.session_state["mensagem_exibida"]:
                st.markdown(f"""
                    <div style='background-color: #FFEB00; padding: 40px 20px; border: 5px solid #1D1D1B; 
                                box-shadow: 10px 10px 0px #1D1D1B; text-align: center; margin-top: 20px;'>
                        <h1 style='font-family: "Archivo Black", sans-serif; font-style: italic; color: #1D1D1B; font-size: 2.5rem;'>
                            COMANDO 2026<br><span style='color: #E20613;'>INFORME DO DIA</span>
                        </h1>
                        <hr style='border: 2px solid #1D1D1B; margin: 20px 0;'>
                        <p style='font-size: 1.4rem; font-weight: bold; color: #1D1D1B; line-height: 1.4;'>
                            {m['Mensagem_Inicial']}
                        </p>
                    </div>
                    <br>
                """, unsafe_allow_html=True)

                if st.button("✅ LI AS INSTRUÇÕES E QUERO ENTRAR", width='stretch', type="primary"):
                    st.session_state["mensagem_exibida"] = True
                    st.rerun()
                st.stop()

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

    tab_missoes, tab_contratos = st.tabs(["🚀 Missões e Presença", "📄 Meus Contratos"])

    with tab_missoes:
        st.divider()
        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>REGISTRO DE PRESENÇA</h2>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", width='stretch', key="btn_modal_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", width='stretch', key="btn_modal_out"):
                modal_checkout(u, agora)

        st.divider()
        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'>
                <h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>🚀 MISSÕES DIÁRIAS</h2>
            </div>
        """, unsafe_allow_html=True)

        t_txt = ""
        if m is not None:
            val_planilha = str(m.get('Tarefa_Direcionada', '')).strip()
            if val_planilha.lower() != 'nan' and val_planilha != "":
                t_txt = val_planilha.upper()

        if not t_txt:
            t_txt = "MOBILIZAÇÃO GERAL E PANFLETAGEM"

        with st.container(border=True):
            st.markdown(
                f"<h3 style='text-align: center; color: #1D1D1B; margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: #E20613;'>{t_txt}</p>",
                unsafe_allow_html=True)

            if st.button(f"CONCLUIR MISSÃO DE HOJE", width='stretch', key="btn_tarefa_fixa"):
                registrar_acao(u['ID_Usuario'], f"CONCLUIU: {t_txt}", localizacao=st.session_state.get('last_coords'),
                               feedback="", secrets=st.secrets, error_log=st.session_state.get('error_log'))
                st.success("MISSÃO REGISTRADA COM SUCESSO!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            if st.button("📸 CURTA, COMENTE E COMPARTILHE NOSSO ÚLTIMO POST!", width='stretch', key="fixo_insta"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: INTERAÇÃO INSTAGRAM",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                st.markdown(f"""
                    <a href="https://www.instagram.com/maxmacieldf/" target="_blank">
                        <div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; border: 2px solid #FFEB00; font-weight: bold; font-size: 0.8rem;'>
                            ABRIR PERFIL DO MAX ↗️
                        </div>
                    </a>
                """, unsafe_allow_html=True)

        with col_m2:
            if st.button("💬 TRAGA UM NOVO AMIGO PARA SER COLABORADOR!", width='stretch', key="fixo_whats"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: TRAZER NOVO COLABORADOR!",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                mensagem_pronta = "Salve! Já acompanha o trabalho do Max Maciel pelo DF?? Sou colaborador dele e estou muito feliz com o trabalho que estamos fazendo. Vamos juntos nessa campanha? 🚀 https://forms.gle/NzJy6NEynbaPyD6w6"
                msg_url = urllib.parse.quote(mensagem_pronta)
                st.markdown(f"""
                    <a href="https://wa.me/?text={msg_url}" target="_blank">
                        <div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; border: 2px solid #FFEB00; font-weight: bold; font-size: 0.8rem;'>
                            ESCOLHER AMIGO ↗️
                        </div>
                    </a>
                """, unsafe_allow_html=True)

    with tab_contratos:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 20px;'>
                <h2 style='margin:0; font-size: 1.3rem; font-family: "Archivo Black", sans-serif; font-style: italic; color: #1D1D1B;'>📝 NOVO CONTRATO</h2>
                <p style='margin:5px 0 0 0; font-size: 0.9rem; font-weight: bold;'>VOCÊ AINDA NÃO GEROU SEU CONTRATO?</p>
            </div>
        """, unsafe_allow_html=True)

        url_formulario = "https://forms.gle/9fqxvN8XfCmTRh9EA"
        st.link_button("📋 PREENCHER DADOS PARA GERAR CONTRATO", url_formulario, width='stretch', type="primary")

        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        st.divider()

        st.subheader("📄 Meus Documentos")
        df_contratos = carregar_dados("Contratos", st.secrets["planilha"]["id"])
        if df_contratos is not None:
            meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
            if not meus_docs.empty:
                for _, doc in meus_docs.iterrows():
                    with st.container(border=True):
                        st.write(f"**Doc:** {doc['Nome_Arquivo']}")
                        st.link_button("📥 Baixar Original", doc['Link_Original'], width='stretch')
                        arq = st.file_uploader("Upload Assinado (PDF)", type=['pdf'], key=f"up_{doc['Nome_Arquivo']}")
                        if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}", width='stretch',
                                     type="primary"):
                            if arq:
                                with st.spinner("Enviando..."):
                                    link = salvar_documento_drive(arq, f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}",
                                                                  st.secrets)
                                    if link and atualizar_contrato_enviado(u['ID_Usuario'], doc['Nome_Arquivo'], link,
                                                                           st.secrets):
                                        st.success("Enviado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
            else:
                st.info("Nenhum contrato pendente.")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🆘 PRECISA DE AJUDA?</h3>", unsafe_allow_html=True)

    col_sup1, col_sup2 = st.columns(2)
    id_supervisor_dele = str(u.get('ID_Supervisor', '')).strip().lower()
    dados_supervisor = df_usuarios[df_usuarios[
                                       'ID_Usuario'].str.lower().str.strip() == id_supervisor_dele] if df_usuarios is not None else pd.DataFrame()

    with col_sup1:
        if not dados_supervisor.empty:
            whats_sup = sanitize_whatsapp(dados_supervisor.iloc[0]['WhatsApp'])
            nome_sup = dados_supervisor.iloc[0]['Nome'].split()[0].upper()
            msg_sup = f"Olá {nome_sup}! Sou colaborador da sua equipe e preciso de ajuda."
            st.link_button(f"👤 FALAR COM {nome_sup}", f"https://wa.me/{whats_sup}?text={urllib.parse.quote(msg_sup)}",
                           width='stretch')
        else:
            st.button("👤 SUPERVISOR NÃO ENCONTRADO", disabled=True, width='stretch')

    with col_sup2:
        whats_tecnico = "5561998788292"
        msg_tecnica = "Olá! Estou tendo dificuldades técnicas com o aplicativo Comando 2026."
        st.link_button("🛠️ SUPORTE DO APP", f"https://wa.me/{whats_tecnico}?text={urllib.parse.quote(msg_tecnica)}",
                       width='stretch')

    st.markdown("<div style='margin-bottom: 50px;'></div>", unsafe_allow_html=True)

# =============================================================================
# VISÃO: SUPERVISOR
# =============================================================================

elif cargo_limpo == "supervisor":

    df_msgs = carregar_dados("Mensagens", st.secrets["planilha"]["id"])
    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"])
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"])
    m = None

    if df_msgs is not None and not df_msgs.empty:
        msg_grupo = df_msgs[df_msgs['ID_Alvo'].astype(str).str.strip() == str(u['ID_Grupo']).strip()]
        if not msg_grupo.empty:
            m = msg_grupo.iloc[-1]
            if not st.session_state["mensagem_exibida"]:
                st.markdown(f"""
                    <div style='background-color: #FFEB00; padding: 40px 20px; border: 5px solid #1D1D1B; 
                                box-shadow: 10px 10px 0px #1D1D1B; text-align: center; margin-top: 20px;'>
                        <h1 style='font-family: "Archivo Black", sans-serif; font-style: italic; color: #1D1D1B; font-size: 2.5rem;'>
                            COMANDO 2026<br><span style='color: #E20613;'>DIRETRIZES DE LIDERANÇA</span>
                        </h1>
                        <hr style='border: 2px solid #1D1D1B; margin: 20px 0;'>
                        <p style='font-size: 1.4rem; font-weight: bold; color: #1D1D1B; line-height: 1.4;'>{m['Mensagem_Inicial']}</p>
                    </div><br>
                """, unsafe_allow_html=True)
                if st.button("✅ CIENTE DAS DIRETRIZES", width='stretch', type="primary"):
                    st.session_state["mensagem_exibida"] = True
                    st.rerun()
                st.stop()

    location_data = get_geolocation()
    col_status, col_btn = st.columns([3, 1])
    with col_status:
        if location_data:
            try:
                lat, lon = location_data['coords']['latitude'], location_data['coords']['longitude']
                st.session_state['last_coords'] = f"{lat},{lon}"
                st.markdown("🟢 **GPS ATIVO**")
            except:
                st.markdown("🔴 **ERRO GPS**")
        else:
            st.markdown("🟡 **BUSCANDO SINAL...**")
    with col_btn:
        if st.button("🔄", help="Atualizar GPS"):
            st.rerun()

    tab_missoes, tab_contratos, tab_equipe = st.tabs([
        "🚀 MISSÕES E PRESENÇA", "📄 MEUS CONTRATOS", "📈 ACOMPANHAMENTO"
    ])

    with tab_missoes:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'><h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>MEU REGISTRO</h2></div>",
            unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏁 ENTRADA (CHECK-IN)", width='stretch', key="sup_in"):
                modal_checkin(u, agora)
        with c2:
            if st.button("🏁 SAÍDA (CHECK-OUT)", width='stretch', key="sup_out"):
                modal_checkout(u, agora)

        st.divider()
        st.markdown(
            "<div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 25px;'><h2 style='margin:0; font-size: 1.8rem; font-style: italic; color: #1D1D1B;'>🚀 MISSÕES DIÁRIAS</h2></div>",
            unsafe_allow_html=True)

        t_txt = str(m.get('Tarefa_Direcionada', 'MISSÃO GERAL')).upper() if m is not None else "MISSÃO GERAL"
        with st.container(border=True):
            st.markdown(
                f"<h3 style='text-align: center; color: #1D1D1B; margin-bottom: 10px;'>🚩 MISSÃO PRIORITÁRIA</h3>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align: center; font-weight: bold; font-size: 1.1rem; color: #E20613;'>{t_txt}</p>",
                unsafe_allow_html=True)
            if st.button("CONCLUIR MISSÃO DE HOJE", width='stretch', key="sup_task_done"):
                registrar_acao(u['ID_Usuario'], f"CONCLUIU: {t_txt}", localizacao=st.session_state.get('last_coords'),
                               feedback="", secrets=st.secrets, error_log=st.session_state.get('error_log'))
                st.success("MISSÃO REGISTRADA!")

        st.markdown("<h3 style='font-size: 1.2rem;'>📲 AÇÕES DE REDE</h3>", unsafe_allow_html=True)
        cm1, cm2 = st.columns(2)
        with cm1:
            if st.button("📸 INSTAGRAM", width='stretch', key="sup_insta"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: INTERAÇÃO INSTAGRAM",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                st.markdown(
                    f"<a href='https://www.instagram.com/maxmacieldf/' target='_blank'><div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; font-weight: bold; font-size: 0.8rem;'>ABRIR PERFIL ↗️</div></a>",
                    unsafe_allow_html=True)
        with cm2:
            if st.button("💬 WHATSAPP", width='stretch', key="sup_whats"):
                registrar_acao(u['ID_Usuario'], "AÇÃO: MOBILIZAÇÃO WHATSAPP",
                               localizacao=st.session_state.get('last_coords'), feedback="", secrets=st.secrets,
                               error_log=st.session_state.get('error_log'))
                msg_zap = urllib.parse.quote(
                    "Salve! Vamos juntos com Max Maciel 🚀 https://www.instagram.com/maxmacieldf/")
                st.markdown(
                    f"<a href='https://wa.me/?text={msg_zap}' target='_blank'><div style='background-color: #1D1D1B; color: #FFEB00; text-align: center; padding: 10px; font-weight: bold; font-size: 0.8rem;'>ENVIAR P/ AMIGO ↗️</div></a>",
                    unsafe_allow_html=True)

    with tab_contratos:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("""
            <div style='background-color: #FFEB00; padding: 15px; border: 4px solid #1D1D1B; box-shadow: 8px 8px 0px #1D1D1B; text-align: center; margin-bottom: 20px;'>
                <h2 style='margin:0; font-size: 1.3rem; font-family: "Archivo Black", sans-serif; font-style: italic; color: #1D1D1B;'>📝 NOVO CONTRATO</h2>
                <p style='margin:5px 0 0 0; font-size: 0.9rem; font-weight: bold;'>VOCÊ AINDA NÃO GEROU SEU CONTRATO?</p>
            </div>
        """, unsafe_allow_html=True)

        url_formulario = "https://forms.gle/9fqxvN8XfCmTRh9EA"
        st.link_button("📋 PREENCHER DADOS PARA GERAR CONTRATO", url_formulario, width='stretch', type="primary")

        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        st.divider()

        st.subheader("📄 Meus Documentos")
        df_contratos = carregar_dados("Contratos", st.secrets["planilha"]["id"])
        if df_contratos is not None:
            meus_docs = df_contratos[df_contratos['ID_Usuario'].astype(str) == str(u['ID_Usuario'])]
            if not meus_docs.empty:
                for _, doc in meus_docs.iterrows():
                    with st.container(border=True):
                        st.write(f"**Doc:** {doc['Nome_Arquivo']}")
                        st.link_button("📥 Baixar Original", doc['Link_Original'], width='stretch')
                        arq = st.file_uploader("Upload Assinado (PDF)", type=['pdf'], key=f"up_{doc['Nome_Arquivo']}")
                        if st.button("Confirmar Envio", key=f"btn_{doc['Nome_Arquivo']}", width='stretch',
                                     type="primary"):
                            if arq:
                                with st.spinner("Enviando..."):
                                    link = salvar_documento_drive(arq, f"ASSINADO_{u['Nome']}_{doc['Nome_Arquivo']}",
                                                                  st.secrets)
                                    if link and atualizar_contrato_enviado(u['ID_Usuario'], doc['Nome_Arquivo'], link,
                                                                           st.secrets):
                                        st.success("Enviado com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
            else:
                st.info("Nenhum contrato pendente.")

    with tab_equipe:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if df_usuarios is not None and df_logs is not None:
            minha_equipe = df_usuarios[df_usuarios['ID_Supervisor'].astype(str) == str(u['ID_Usuario'])]

            espaco_metricas = st.empty()

            c_data, _ = st.columns([1.5, 1])
            with c_data:
                data_sel = st.date_input("📅 DATA DE ANÁLISE", datetime.now(timezone.utc) - timedelta(hours=3))
            d_str = data_sel.strftime("%d/%m/%Y")

            logs_dia = df_logs[df_logs['Data_Hora'].str.contains(d_str)]
            ativos_dia = logs_dia[logs_dia['ID_Usuario'].isin(minha_equipe['ID_Usuario'])]
            total_vol = len(minha_equipe)
            num_ativos = ativos_dia[ativos_dia['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
            total_acoes = len(ativos_dia)

            espaco_metricas.markdown(f"""
                <div style="display: flex; justify-content: space-between; gap: 5px; width: 100%; margin-bottom: 15px;">
                    <div style="flex: 1; background: #FFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px;">
                        <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666;">EQUIPE</p>
                        <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #1D1D1B;">{total_vol}</p>
                    </div>
                    <div style="flex: 1; background: #FFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px;">
                        <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666;">ATIVOS</p>
                        <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #E20613;">{num_ativos}</p>
                    </div>
                    <div style="flex: 1; background: #FFF; border: 2px solid #1D1D1B; box-shadow: 3px 3px 0px #1D1D1B; text-align: center; padding: 5px;">
                        <p style="margin: 0; font-size: 0.6rem; font-family: 'Archivo Black'; color: #666;">AÇÕES</p>
                        <p style="margin: 0; font-size: 1.2rem; font-family: 'Archivo Black'; color: #1D1D1B;">{total_acoes}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(
                f"<h3 style='font-size: 1.1rem; text-align: left; margin-top: -15px;'>📋 STATUS DA EQUIPE ({d_str[:5]})</h3>",
                unsafe_allow_html=True)

            for _, vol in minha_equipe.iterrows():
                logs_vol = df_logs[
                    (df_logs['ID_Usuario'] == vol['ID_Usuario']) & (df_logs['Data_Hora'].str.contains(d_str))]

                tem_in = not logs_vol[logs_vol['Tipo_Acao'].str.contains("Check-in")].empty
                tem_net = not logs_vol[logs_vol['Tipo_Acao'].str.contains("AÇÃO:")].empty
                tem_ok = not logs_vol[logs_vol['Tipo_Acao'].str.contains("CONCLUIU:")].empty

                if tem_in and tem_ok:
                    label = "🔥 COMPLETO"
                elif tem_in:
                    label = "🟢 EM CAMPO"
                elif tem_net:
                    label = "🟡 REDES"
                else:
                    label = "⚪ OFF"

                with st.expander(f"{label} | {vol['Nome'].upper()}"):
                    if not logs_vol.empty:
                        feed_html = ""
                        for _, row in logs_vol.tail(5)[::-1].iterrows():
                            acao_txt = str(row['Tipo_Acao']).split("|")[0].split("Foto:")[0].strip().upper()
                            hora_txt = row['Data_Hora'].split()[-1][:5]
                            fb = str(row.get('Feedback', '')).strip()
                            badge = f"<span style='background-color:#FFEB00; border:1px solid #000; padding:1px 4px; font-size:0.5rem; margin-left:8px;'>{fb.split('|')[0]}</span>" if "Check-out" in \
                                                                                                                                                                                       row[
                                                                                                                                                                                           'Tipo_Acao'] and fb and fb != "nan" else ""

                            feed_html += f"<div style='background-color:#F4F4F4; border:2px solid #1D1D1B; padding:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; box-shadow:3px 3px 0px #1D1D1B;'><div style='text-align:left;'><span style='font-family:Archivo Black; font-size:0.8rem;'>{acao_txt}</span>{badge}<br><span style='font-size:0.7rem; color:#666; font-weight:bold;'>🕒 {hora_txt}</span></div>"
                            if "," in str(row['Localização']):
                                feed_html += f"<div><a href='https://www.google.com/maps?q={row['Localização']}' target='_blank' style='background-color:#E20613; color:#FFF; padding:3px 6px; border:1px solid #000; font-size:0.5rem; text-decoration:none; font-family:Archivo Black;'>📍 MAPA</a></div>"
                            feed_html += "</div>"
                        st.markdown(feed_html, unsafe_allow_html=True)

                    st.divider()
                    w_vol = sanitize_whatsapp(vol['WhatsApp'])
                    p_vol = vol['Nome'].split()[0]
                    c_w1, c_w2 = st.columns(2)
                    with c_w1:
                        if tem_in:
                            b_n, b_m = "💪 MOTIVAR", f"Bora {p_vol}! Pra cima! 🚀"
                        elif tem_net:
                            b_n, b_m = "⚡ REFORÇAR", f"Boa {p_vol}! Não esquece o check-in na rua! 💪"
                        else:
                            b_n, b_m = "⚠️ COBRAR", f"Fala {p_vol}! Algum problema? Não vi suas ações hoje."
                        st.link_button(b_n,
                                       f"https://api.whatsapp.com/send?text={urllib.parse.quote(b_m)}&phone={w_vol}",
                                       width='stretch', type="primary")
                    with c_w2:
                        st.link_button("💬 CHAT", f"https://wa.me/{w_vol}", width='stretch')

            st.markdown("<br>", unsafe_allow_html=True)
            rel_txt = f"📊 *RELATÓRIO {d_str}*\n👤 Sup: {nome_primeiro}\n👥 Equipe: {total_vol}\n🔥 Ativos: {num_ativos}\n🎯 Ações: {total_acoes}"
            st.link_button("📲 ENVIAR RELATÓRIO P/ COORDENAÇÃO",
                           f"https://api.whatsapp.com/send?text={urllib.parse.quote(rel_txt)}", width='stretch',
                           type="primary")

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<h3 style='font-size: 1.2rem; text-align: left;'>🛠️ SUPORTE DE LIDERANÇA</h3>", unsafe_allow_html=True)
    st.link_button("🛠️ REPORTAR ERRO NO APP", "https://wa.me/5561998788292?text=Erro no Painel de Supervisor",
                   width='stretch')

# =============================================================================
# VISÃO: ADMIN (COORDENAÇÃO)
# =============================================================================

elif cargo_limpo == "admin":

    st.markdown("""
        <style>
            .block-container {
                max-width: 1100px !important; 
                padding-top: 2rem !important;
            }
            button[data-baseweb="tab"] p {
                font-size: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    agora_br = get_agora_br()
    hoje_str = agora_br.strftime("%d/%m/%Y")

    df_usuarios = carregar_dados("Usuarios", st.secrets["planilha"]["id"])
    df_logs = carregar_dados("Logs", st.secrets["planilha"]["id"])

    if not df_logs.empty:
        ultimos_logs_raw = df_logs.tail(10)
        df_ticker = pd.merge(ultimos_logs_raw, df_usuarios[['ID_Usuario', 'Nome']], on='ID_Usuario', how='left')
        df_ticker['Nome'] = df_ticker['Nome'].fillna(df_ticker['ID_Usuario'])

        frase_ticker = "  ///  ".join([
            f"⚡ {str(row['Nome']).split()[0].upper()}: {str(row['Tipo_Acao']).split('|')[0].strip().upper()}"
            for _, row in df_ticker[::-1].iterrows()
        ])

        conteudo_duplicado = f"{frase_ticker} /// {frase_ticker}"

        st.markdown(f"""
            <style>
                @keyframes scroll {{
                    0% {{ transform: translateX(0); }}
                    100% {{ transform: translateX(-50%); }}
                }}
                .ticker-container {{
                    width: 100%;
                    overflow: hidden;
                    background: #FFEB00;
                    border-top: 3px solid #1D1D1B;
                    border-bottom: 3px solid #1D1D1B;
                    padding: 8px 0;
                    margin-bottom: 25px;
                    white-space: nowrap;
                    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
                }}
                .ticker-content {{
                    display: inline-block;
                    animation: scroll 45s linear infinite;
                    font-family: 'Archivo Black', sans-serif;
                    font-size: 0.9rem;
                    color: #1D1D1B;
                    font-style: italic;
                    text-transform: uppercase;
                }}
                .ticker-content:hover {{
                    animation-play-state: paused;
                }}
            </style>
            <div class="ticker-container">
                <div class="ticker-content">
                    {conteudo_duplicado}
                </div>
            </div>
        """, unsafe_allow_html=True)

    tab_hierarquia, tab_logs, tab_mapa, tab_mensagens, tab_cadastro, tab_contratos = st.tabs([
        "👥 EQUIPES", "📊 DASHBOARD", "🗺️ MAPA", "📝 MISSÕES", "➕ CADASTRO", "📄 CONTRATOS"
    ])

    # ==========================================
    # ABA 1: ESTRUTURA DE EQUIPES (MACRO_GRUPOS DINÂMICOS)
    # ==========================================
    with tab_hierarquia:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 25px; font-size: 2rem;'>ESTRUTURA DE EQUIPES</h2>",
            unsafe_allow_html=True)

        # Importa função com cache
        from utils import carregar_macro_grupos_cached

        planilha_id = st.secrets["planilha"]["id"]

        # Carrega Macro_Grupos com cache (1 chamada só)
        macro_grupos_disponiveis = carregar_macro_grupos_cached(planilha_id)

        # Filtro de Macro Região
        st.markdown(
            "<p style='font-family: \"Archivo Black\", sans-serif; font-size: 0.9rem; margin-bottom: 5px;'>📍 SELECIONE A MACRO REGIÃO:</p>",
            unsafe_allow_html=True)
        macro_selecionada = st.selectbox(
            "FILTRO_MACRO",
            ["TODAS AS REGIÕES"] + macro_grupos_disponiveis,
            label_visibility="collapsed",
            key="select_macro_hierarquia"
        )

        df_usuarios_raw = carregar_dados("Usuarios", planilha_id)
        df_grupos_info = carregar_dados("Grupos", planilha_id)

        if df_usuarios_raw is not None and df_grupos_info is not None:
            df_gerencial = pd.merge(df_usuarios_raw, df_grupos_info, on='ID_Grupo', how='left')
            df_gerencial['Macro_Grupo'] = df_gerencial['Macro_Grupo'].fillna("GERAL")

            if macro_selecionada == "TODAS AS REGIÕES":
                df_f_admin = df_gerencial.copy()
            else:
                df_f_admin = df_gerencial[df_gerencial['Macro_Grupo'] == macro_selecionada]

            supervisores = df_f_admin[df_f_admin['Cargo'].str.lower().str.strip() == "supervisor"]

            if supervisores.empty:
                st.warning("Nenhum supervisor nesta região.")
            else:
                col_sup1, col_sup2 = st.columns(2, gap="large")

                for i, (_, sup) in enumerate(supervisores.iterrows()):
                    col_alvo = col_sup1 if i % 2 == 0 else col_sup2

                    with col_alvo:
                        equipe = df_f_admin[
                            df_f_admin['ID_Supervisor'].astype(str).str.strip() == str(sup['ID_Usuario']).strip()]
                        qtd_equipe = len(equipe)

                        logs_eq = df_logs[(df_logs['ID_Usuario'].isin(equipe['ID_Usuario'])) & (
                            df_logs['Data_Hora'].str.contains(hoje_str))]
                        ativos_hoje = logs_eq[logs_eq['Tipo_Acao'].str.contains("Check-in")]['ID_Usuario'].nunique()
                        cor_ativos = "#E20613" if ativos_hoje > 0 else "#666666"

                        st.markdown(f"""
                            <div style='background-color: #FFFFFF; border: 4px solid #1D1D1B; box-shadow: 6px 6px 0px #1D1D1B; padding: 20px; margin-bottom: 12px;'>
                                <div style='border-bottom: 3px solid #1D1D1B; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <h3 style='margin: 0; font-family: "Archivo Black", sans-serif; font-size: 1.5rem; color: #E20613; text-transform: uppercase;'>{sup['Nome']}</h3>
                                        <span style='font-size: 0.8rem; color: #666; font-weight: bold;'>MACRO: {sup['Macro_Grupo']}</span>
                                    </div>
                                    <span style='background-color: #FFEB00; border: 2px solid #1D1D1B; padding: 4px 10px; font-family: "Archivo Black", sans-serif; font-size: 0.8rem;'>{sup['ID_Grupo']}</span>
                                </div>
                                <div style='display: flex; gap: 15px;'>
                                    <div style='flex: 1; background-color: #F4F4F4; border: 2px solid #1D1D1B; padding: 12px; text-align: center;'>
                                        <div style='font-family: "Archivo Black", sans-serif; font-size: 0.85rem; color: #666;'>EQUIPE</div>
                                        <div style='font-family: "Archivo Black", sans-serif; font-size: 2.2rem; color: #1D1D1B; line-height: 1; margin-top: 5px;'>{qtd_equipe}</div>
                                    </div>
                                    <div style='flex: 1; background-color: #F4F4F4; border: 2px solid #1D1D1B; padding: 12px; text-align: center;'>
                                        <div style='font-family: "Archivo Black", sans-serif; font-size: 0.85rem; color: #666;'>ATIVOS</div>
                                        <div style='font-family: "Archivo Black", sans-serif; font-size: 2.2rem; color: {cor_ativos}; line-height: 1; margin-top: 5px;'>{ativos_hoje}</div>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        raw_w_sup = str(sup.get('WhatsApp', '')).strip()
                        w_sup_limpo = sanitize_whatsapp(raw_w_sup)
                        link_grp = str(sup.get('Link_Grupo', '')).strip()

                        c_wa1, c_wa2 = st.columns(2)
                        with c_wa1:
                            if w_sup_limpo:
                                st.link_button(f"👤 CHAT: {sup['Nome'].split()[0].upper()}",
                                               f"https://wa.me/{w_sup_limpo}", width="stretch")
                            else:
                                st.button("👤 SEM WHATSAPP", disabled=True, width="stretch",
                                          key=f"no_wa_{sup['ID_Usuario']}")

                        with c_wa2:
                            if link_grp and "chat.whatsapp" in link_grp:
                                st.link_button("📢 GRUPO", f"{link_grp}#{sup['ID_Usuario']}", width="stretch")
                            else:
                                st.button("🚫 SEM LINK", disabled=True, width="stretch",
                                          key=f"no_link_{sup['ID_Usuario']}")

                        with st.expander(f"👥 LISTA DE INTEGRANTES ({qtd_equipe})"):
                            if not equipe.empty:
                                for _, vol in equipe.iterrows():
                                    w_vol = sanitize_whatsapp(vol.get('WhatsApp', ''))
                                    st.markdown(f"""
                                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; padding: 8px 0;">
                                            <span style="font-size: 0.9rem; font-weight: bold; color: #1D1D1B;">{vol['Nome'].upper()}</span>
                                            <a href="https://wa.me/{w_vol}" target="_blank" style="background-color: #25D366; color: #FFFFFF; font-size: 0.7rem; padding: 4px 10px; border: 2px solid #1D1D1B; text-decoration: none; font-weight: bold; white-space: nowrap;">CHAMAR</a>
                                        </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("Sem voluntários.")

                        st.markdown("<br><br>", unsafe_allow_html=True)

    with tab_mensagens:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 25px; font-size: 2rem;'>DIRETRIZES DO DIA</h2>",
            unsafe_allow_html=True)

        st.markdown("""
            <style>
                div[data-testid="stForm"] label p { font-size: 1.6rem !important; font-family: 'Archivo Black' !important; font-style: italic; }
                div[data-testid="stForm"] textarea, div[data-testid="stForm"] input { font-size: 1.4rem !important; font-weight: bold !important; border: 3px solid #1D1D1B !important; }
            </style>
        """, unsafe_allow_html=True)

        try:
            client = _get_gspread_client(st.secrets)
            aba_msg = client.open_by_key(st.secrets["planilha"]["id"]).worksheet("Mensagens")
            dados_msg = aba_msg.get_all_records()
            df_msg = pd.DataFrame(dados_msg)

            lista_alvos = df_msg["ID_Alvo"].unique().tolist() if not df_msg.empty else []
            alvo_selecionado = st.selectbox("1. SELECIONE O GRUPO:", ["Novo..."] + lista_alvos)

            with st.form("form_admin_msg"):
                if alvo_selecionado == "Novo...":
                    id_alvo, msg_i, tar = "", "", ""
                else:
                    d = df_msg[df_msg["ID_Alvo"] == alvo_selecionado].iloc[-1]
                    id_alvo = d.get("ID_Alvo", "")
                    msg_i = d.get("Mensagem_Inicial", "")
                    tar = d.get("Tarefa_Direcionada", "")

                f_id = st.text_input("ID DO GRUPO (IGUAL AO CADASTRADO):", value=id_alvo)
                f_msg = st.text_area("MENSAGEM NO POP-UP (BOAS-VINDAS):", value=msg_i, height=150)
                f_tar = st.text_area("MISSÃO DE RUA (TAREFA PRINCIPAL):", value=tar, height=100)

                if st.form_submit_button("🚀 ATUALIZAR DIRETRIZES", type="primary", width='stretch'):
                    if f_id:
                        data_auto = (get_agora_br()).strftime("%d/%m/%Y")
                        nova_linha = [f_id, f_msg, f_tar, data_auto]

                        if alvo_selecionado != "Novo...":
                            try:
                                cell = aba_msg.find(str(alvo_selecionado))
                                if cell:
                                    aba_msg.delete_rows(cell.row)
                            except:
                                pass

                        aba_msg.append_row(nova_linha)
                        st.success("✅ ATUALIZADO!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("O ID DO GRUPO É OBRIGATÓRIO")
        except Exception as e:
            st.error(f"Erro na conexão: {e}")

    with tab_logs:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 25px; font-size: 2rem;'>ESTATÍSTICAS DO COMANDO</h2>",
            unsafe_allow_html=True)

        if 'Localização' not in df_logs.columns:
            df_logs['Localização'] = "Sem GPS"
        if 'Endereço' not in df_logs.columns:
            df_logs['Endereço'] = "Não identificado"
        if 'Feedback' not in df_logs.columns:
            df_logs['Feedback'] = "Nenhum"

        df_logs['Data_Hora_DT'] = pd.to_datetime(df_logs['Data_Hora'], dayfirst=True, errors='coerce')
        df_logs['Data_Filtro'] = df_logs['Data_Hora'].str.split().str[0]

        datas_disponiveis = sorted(
            [d for d in df_logs['Data_Filtro'].unique().tolist() if isinstance(d, str) and "/" in d],
            key=lambda x: datetime.strptime(x, "%d/%m/%Y"),
            reverse=True
        )

        c_f1, c_f2 = st.columns([1, 1])
        with c_f1:
            periodo_selecionado = st.selectbox("📅 FILTRAR POR DATA:", ["Histórico Completo"] + datas_disponiveis)
        with c_f2:
            lista_sups = ["TODOS"] + df_usuarios[df_usuarios['Cargo'].str.lower() == "supervisor"][
                'Nome'].unique().tolist()
            sup_filtro = st.selectbox("👤 FILTRAR POR SUPERVISOR:", lista_sups)

        df_completo = pd.merge(df_logs, df_usuarios[['ID_Usuario', 'Nome', 'ID_Supervisor', 'ID_Grupo']],
                               on='ID_Usuario', how='left')
        df_completo = pd.merge(df_completo, df_usuarios[['ID_Usuario', 'Nome']].rename(
            columns={'Nome': 'Supervisor_Nome', 'ID_Usuario': 'ID_Supervisor'}), on='ID_Supervisor', how='left')
        df_completo['Nome'] = df_completo['Nome'].fillna(df_completo['ID_Usuario'])

        df_f = df_completo.copy()
        if periodo_selecionado != "Histórico Completo":
            df_f = df_f[df_f['Data_Filtro'] == periodo_selecionado]
        if sup_filtro != "TODOS":
            df_f = df_f[df_f['Supervisor_Nome'] == sup_filtro]

        total_acoes = len(df_f)
        ativos_unicos = df_f['ID_Usuario'].nunique()
        checkins_total = len(df_f[df_f['Tipo_Acao'].str.contains("Check-in", case=False)])

        st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 30px;">
        <div style="flex: 1; background: #FFF; border: 4px solid #1D1D1B; padding: 20px; text-align: center; box-shadow: 6px 6px 0px #1D1D1B;">
            <div style="font-family: 'Archivo Black'; font-size: 0.9rem; color: #666;">AÇÕES NO PERÍODO</div>
            <div style="font-family: 'Archivo Black'; font-size: 3rem; color: #1D1D1B; line-height: 1; margin-top: 10px;">{total_acoes}</div>
        </div>
        <div style="flex: 1; background: #FFF; border: 4px solid #1D1D1B; padding: 20px; text-align: center; box-shadow: 6px 6px 0px #1D1D1B;">
            <div style="font-family: 'Archivo Black'; font-size: 0.9rem; color: #666;">MEMBROS ATIVOS</div>
            <div style="font-family: 'Archivo Black'; font-size: 3rem; color: #E20613; line-height: 1; margin-top: 10px;">{ativos_unicos}</div>
        </div>
        <div style="flex: 1; background: #FFF; border: 4px solid #1D1D1B; padding: 20px; text-align: center; box-shadow: 6px 6px 0px #1D1D1B;">
            <div style="font-family: 'Archivo Black'; font-size: 0.9rem; color: #666;">PRESENÇA FÍSICA</div>
            <div style="font-family: 'Archivo Black'; font-size: 3rem; color: #1D1D1B; line-height: 1; margin-top: 10px;">{checkins_total}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

        if not df_f.empty:
            st.markdown(
                "<h3 style='font-family: \"Archivo Black\", sans-serif; font-size: 1.4rem; text-align: left;'>🏆 RANKING POR EQUIPE</h3>",
                unsafe_allow_html=True)
            df_rank = df_f.groupby('Supervisor_Nome').agg({
                'Tipo_Acao': 'count',
                'ID_Usuario': 'nunique'
            }).reset_index().rename(columns={'Supervisor_Nome': 'Supervisor', 'Tipo_Acao': 'Total de Ações',
                                             'ID_Usuario': 'Colaboradores na Rua'})

            st.dataframe(df_rank.sort_values(by='Total de Ações', ascending=False), use_container_width=True,
                         hide_index=True)

        st.divider()

        st.markdown(
            "<h3 style='font-family: \"Archivo Black\", sans-serif; font-size: 1.4rem; text-align: left;'>📄 DETALHAMENTO DAS MISSÕES</h3>",
            unsafe_allow_html=True)

        df_visual = df_f.sort_values(by="Data_Hora_DT", ascending=False)

        st.dataframe(
            df_visual[['Nome', 'Tipo_Acao', 'Data_Hora', 'Feedback', 'Endereço']],
            column_config={
                "Nome": "Colaborador",
                "Tipo_Acao": "Ação",
                "Data_Hora": "Horário",
                "Feedback": "📣 Relato/Clima",
                "Endereço": "📍 Local"
            },
            width='stretch',
            hide_index=True
        )

        # =====================================================================
        # EXPORTAÇÃO EXCEL - VERSÃO CORRIGIDA
        # =====================================================================
        if not df_f.empty:
            try:
                df_excel = df_visual[
                    ['Nome', 'Supervisor_Nome', 'ID_Grupo', 'Tipo_Acao', 'Data_Hora', 'Feedback', 'Endereço',
                     'Localização']].copy()

                # ✅ CORREÇÃO 1: Substituir todos os NaN por string vazia
                df_excel = df_excel.fillna('')

                # ✅ CORREÇÃO 2: Garantir que todas as colunas sejam string
                for col in df_excel.columns:
                    df_excel[col] = df_excel[col].astype(str)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name='Relatorio_Completo')
                    worksheet = writer.sheets['Relatorio_Completo']

                    # ✅ CORREÇÃO 3: Calcular largura de forma segura
                    for idx, col in enumerate(df_excel.columns):
                        # Usa apply com lambda para evitar erro com float
                        max_data_len = df_excel[col].apply(lambda x: len(str(x)) if x else 0).max()
                        header_len = len(str(col))
                        max_len = max(max_data_len, header_len) + 2
                        # Limita largura máxima para não ficar exagerado
                        max_len = min(max_len, 50)
                        worksheet.set_column(idx, idx, max_len)

                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label=f"📊 BAIXAR RELATÓRIO COMPLETO EM EXCEL ({periodo_selecionado})",
                    data=buffer.getvalue(),
                    file_name=f'comando2026_relatorio_{sup_filtro}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    width='stretch',
                    type="primary"
                )
            except Exception as e:
                st.error(f"Erro ao gerar Excel: {e}")

    # ==========================================
    # ABA 4: GESTÃO DE ACESSOS E GRUPOS
    # ==========================================
    with tab_cadastro:
        # Importa funções de gestão de grupos (versões com cache)
        from utils import (
            carregar_macro_grupos_cached,
            carregar_grupos_completos_cached,
            criar_novo_grupo,
            criar_novo_macro_grupo,
            editar_grupo,
            excluir_grupo
        )

        # =====================================================================
        # CARREGAR DADOS UMA VEZ SÓ (EVITA MÚLTIPLAS CHAMADAS À API)
        # =====================================================================
        planilha_id = st.secrets["planilha"]["id"]

        # Carrega dados com cache (1 chamada só, reutilizada em toda a aba)
        df_usuarios = carregar_dados("Usuarios", planilha_id)
        grupos_existentes = carregar_grupos_completos_cached(planilha_id)
        macro_grupos_lista = carregar_macro_grupos_cached(planilha_id)

        # Converte grupos para lista simples
        lista_grupos = sorted([g['ID_Grupo'] for g in grupos_existentes]) if grupos_existentes else []

        # =====================================================================
        # SEÇÃO 1: NOVO INTEGRANTE
        # =====================================================================
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 20px; font-size: 1.8rem;'>👤 NOVO INTEGRANTE</h2>",
            unsafe_allow_html=True)

        df_sup_only = df_usuarios[
            df_usuarios['Cargo'].str.lower().str.strip() == "supervisor"] if df_usuarios is not None else pd.DataFrame()

        mapeamento_sup = {
            f"{row['Nome'].upper()} ({row['ID_Usuario'].lower()})": row['ID_Usuario']
            for _, row in df_sup_only.iterrows()
        }
        lista_nomes_exibicao = sorted(mapeamento_sup.keys())

        # ✅ GARANTE: Apenas grupos reais (exclui Macro_Grupos)
        lista_grupos = sorted([
            g['ID_Grupo'] for g in grupos_existentes
            if not str(g.get('ID_Grupo', '')).startswith('_MACRO_')
        ]) if grupos_existentes else []

        with st.container(border=True):
            with st.form("form_novo_user_v2", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**DADOS PESSOAIS**")
                    n_id = st.text_input("ID / E-MAIL (LOGIN):").strip().lower()
                    n_nome = st.text_input("NOME COMPLETO:")
                    n_whats = st.text_input("WHATSAPP (DDD + NÚMERO):")
                with c2:
                    st.markdown("**VÍNCULO NO COMANDO**")
                    n_cargo = st.selectbox("CARGO:", ["Colaborador", "Supervisor", "Admin"])
                    n_grupo = st.selectbox(
                        "GRUPO / TERRITÓRIO:",
                        options=lista_grupos if lista_grupos else ["Nenhum grupo cadastrado"]
                    )

                    n_sup_selecionado_display = st.selectbox(
                        "SUPERVISOR RESPONSÁVEL:",
                        options=["NENHUM / PRÓPRIO SUPERVISOR"] + lista_nomes_exibicao
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("✅ CADASTRAR INTEGRANTE", type="primary", width='stretch'):
                    if n_id and n_nome and n_whats:
                        if n_grupo == "Nenhum grupo cadastrado":
                            st.error("⚠️ Cadastre pelo menos um grupo antes de criar usuários!")
                        else:
                            try:
                                client = _get_gspread_client(st.secrets)
                                aba_u = client.open_by_key(planilha_id).worksheet("Usuarios")

                                if n_sup_selecionado_display == "NENHUM / PRÓPRIO SUPERVISOR":
                                    id_supervisor_final = ""
                                else:
                                    id_supervisor_final = mapeamento_sup[n_sup_selecionado_display]

                                aba_u.append_row([
                                    n_id,
                                    n_nome.upper(),
                                    n_whats,
                                    n_cargo,
                                    n_grupo,
                                    id_supervisor_final
                                ])

                                st.success(f"🚀 {n_nome.upper()} CADASTRADO!")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
                    else:
                        st.error("⚠️ PREENCHA TODOS OS CAMPOS!")

        # =====================================================================
        # SEÇÃO 2: GESTÃO DE GRUPOS E MACRO_GRUPOS (SIMPLIFICADO)
        # =====================================================================
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 20px; font-size: 1.8rem;'>🚩 GESTÃO DE GRUPOS E MACRO_GRUPOS</h2>",
            unsafe_allow_html=True)

        # Duas colunas: Criar Grupo | Criar Macro_Grupo
        col_criar_grupo, col_criar_macro = st.columns(2)

        # =====================================================================
        # COLUNA 1: CRIAR NOVO GRUPO
        # =====================================================================
        with col_criar_grupo:
            with st.container(border=True):
                st.markdown("**📍 CRIAR NOVO GRUPO**")
                with st.form("form_novo_grupo_simples", clear_on_submit=True):
                    g_nome = st.text_input("NOME DO GRUPO (ID):", placeholder="Ex: GUARIROBA")
                    g_macro = st.selectbox(
                        "MACRO_GRUPO:",
                        options=macro_grupos_lista if macro_grupos_lista else ["Nenhum Macro_Grupo cadastrado"]
                    )
                    g_link = st.text_input("LINK DO GRUPO (WhatsApp):", placeholder="https://chat.whatsapp.com/...")

                    if st.form_submit_button("➕ REGISTRAR GRUPO", width='stretch', type="primary"):
                        if g_nome:
                            if g_macro == "Nenhum Macro_Grupo cadastrado":
                                st.error("⚠️ Crie pelo menos um Macro_Grupo primeiro!")
                            else:
                                sucesso, msg = criar_novo_grupo(g_nome, g_macro, g_link, st.secrets)
                                if sucesso:
                                    st.success(f"✅ {msg}")
                                    # Cria mensagem de boas-vindas automática
                                    try:
                                        client = _get_gspread_client(st.secrets)
                                        plan = client.open_by_key(planilha_id)
                                        data_atual_msg = (get_agora_br()).strftime("%d/%m/%Y")
                                        plan.worksheet("Mensagens").append_row([
                                            g_nome.upper(),
                                            "BEM-VINDO AO COMANDO!",
                                            "MISSÃO INICIAL DE RUA",
                                            data_atual_msg
                                        ])
                                    except:
                                        pass
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        else:
                            st.error("⚠️ Digite o nome do grupo!")

        # =====================================================================
        # COLUNA 2: CRIAR NOVO MACRO_GRUPO
        # =====================================================================
        with col_criar_macro:
            with st.container(border=True):
                st.markdown("**🗺️ CRIAR NOVO MACRO_GRUPO**")
                with st.form("form_novo_macro_grupo_simples", clear_on_submit=True):
                    m_nome = st.text_input("NOME DO MACRO_GRUPO:", placeholder="Ex: CEILÂNDIA/SOL NASCENTE")

                    if st.form_submit_button("➕ REGISTRAR MACRO_GRUPO", width='stretch', type="primary"):
                        if m_nome:
                            sucesso, msg = criar_novo_macro_grupo(m_nome, st.secrets)
                            if sucesso:
                                st.success(f"✅ {msg}")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                        else:
                            st.error("⚠️ Digite o nome do Macro_Grupo!")

        # =====================================================================
        # LISTAGEM DE GRUPOS E MACRO_GRUPOS (APENAS VISUALIZAÇÃO)
        # =====================================================================
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<h3 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 15px; font-size: 1.3rem;'>📋 GRUPOS CADASTRADOS</h3>",
            unsafe_allow_html=True)

        if grupos_existentes:
            # Cria tabela resumo
            df_resumo = pd.DataFrame(grupos_existentes)

            # Agrupa por Macro_Grupo para exibição
            for macro in macro_grupos_lista:
                grupos_do_macro = [g for g in grupos_existentes if g.get('Macro_Grupo', '') == macro]

                with st.expander(f"📍 {macro} ({len(grupos_do_macro)} grupos)", expanded=False):
                    if grupos_do_macro:
                        for g in grupos_do_macro:
                            col_g1, col_g2 = st.columns([3, 1])
                            with col_g1:
                                st.markdown(f"**{g.get('ID_Grupo', 'N/A')}**")
                                if g.get('Link_Grupo', ''):
                                    st.caption(f"🔗 [Link do Grupo]({g.get('Link_Grupo', '')})")
                            with col_g2:
                                st.caption(f"ID: {g.get('ID_Grupo', 'N/A')}")
                    else:
                        st.caption("Nenhum grupo neste Macro_Grupo.")
        else:
            st.info("Nenhum grupo cadastrado.")

        st.info("💡 **Dica:** Para editar ou excluir grupos, acesse diretamente a planilha 'Grupos' no Google Sheets.")

    with tab_mapa:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 25px; font-size: 2rem;'>🗺️ MAPA DE OPERAÇÕES</h2>",
            unsafe_allow_html=True)

        from folium.plugins import MarkerCluster

        df_logs['Data_Filtro'] = df_logs['Data_Hora'].str.split().str[0]
        datas_mapa = sorted(
            [d for d in df_logs['Data_Filtro'].unique().tolist() if isinstance(d, str) and "/" in d],
            key=lambda x: datetime.strptime(x, "%d/%m/%Y"),
            reverse=True
        )

        c_map_filtro, _ = st.columns([1.5, 2])
        with c_map_filtro:
            periodo_mapa = st.selectbox("📍 FILTRAR LOCALIZAÇÕES POR DATA:", ["Histórico Completo"] + datas_mapa,
                                        key="filtro_mapa_indep")

        if periodo_mapa == "Histórico Completo":
            df_m = df_completo.copy()
        else:
            df_m = df_completo[df_completo['Data_Filtro'] == periodo_mapa].copy()


        def extrair_lat_lon(pos):
            try:
                if pos and "," in str(pos):
                    lat, lon = str(pos).split(",")
                    return float(lat), float(lon)
            except:
                return None, None
            return None, None


        df_m['lat'], df_m['lon'] = zip(*df_m['Localização'].apply(extrair_lat_lon))
        df_geo = df_m.dropna(subset=['lat', 'lon'])

        if not df_geo.empty:
            m = folium.Map(location=[df_geo['lat'].mean(), df_geo['lon'].mean()], zoom_start=12, tiles="OpenStreetMap")
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in df_geo.iterrows():
                popup_content = f"""
                <div style="font-family: sans-serif; min-width: 180px; border: 2px solid #1D1D1B; padding: 10px; background-color: #FFF;">
                    <b style="color: #E20613; text-transform: uppercase; font-size: 14px;">{row['Nome']}</b><br>
                    <div style="margin: 5px 0; border-top: 1px solid #000;"></div>
                    <b>Ação:</b> {str(row['Tipo_Acao']).split('|')[0]}<br>
                    <b>Hora:</b> {row['Data_Hora'].split()[-1][:5]}<br>
                    <small style="color: #666;">{row['Endereço']}</small>
                </div>
                """

                folium.Marker(
                    location=[row['lat'], row['lon']],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(marker_cluster)

            st_folium(m, width=1200, height=600, returned_objects=[])
            st.markdown(
                f"💡 **Exibindo {len(df_geo)} registros geolocalizados.** Clique nos círculos para expandir as regiões.")
        else:
            with st.container(border=True):
                st.warning(f"⚠️ NENHUM DADO DE GPS ENCONTRADO PARA: {periodo_mapa}")
                st.info("Somente ações realizadas com GPS ativo no celular aparecem neste mapa.")

    with tab_contratos:
        st.markdown(
            "<h2 style='font-family: \"Archivo Black\", sans-serif; color: #1D1D1B; margin-bottom: 25px; font-size: 2rem;'>📄 GESTÃO DE CONTRATOS</h2>",
            unsafe_allow_html=True)

        col_envio, col_status = st.columns([1.2, 2], gap="large")

        with col_envio:
            st.markdown("### 📤 ENVIAR PARA INTEGRANTE")
            with st.container(border=True):
                with st.form("form_admin_envia_contrato", clear_on_submit=True):
                    df_destinatarios = df_usuarios[df_usuarios['Cargo'].str.lower() != "admin"]

                    mapeamento_dest = {
                        f"{row['Nome'].upper()} | {row['Cargo'].upper()} | {row['ID_Grupo']}": row['ID_Usuario']
                        for _, row in df_destinatarios.iterrows()
                    }
                    lista_nomes_contrato = sorted(mapeamento_dest.keys())

                    user_selecionado_display = st.selectbox("PARA QUEM É O CONTRATO?", options=lista_nomes_contrato)

                    n_doc = st.text_input("NOME DO DOCUMENTO:", placeholder="Ex: Contrato_NomeSobrenome_Data")
                    arq_pdf = st.file_uploader("ARQUIVO PDF:", type=['pdf'])

                    if st.form_submit_button("🚀 ENVIAR AGORA", width='stretch', type="primary"):
                        if arq_pdf and n_doc and user_selecionado_display:
                            u_destino = mapeamento_dest[user_selecionado_display]

                            with st.spinner("Subindo para o Drive..."):
                                link_gerado = salvar_documento_drive(arq_pdf, f"ORIGINAL_{n_doc}_{u_destino}",
                                                                     st.secrets)

                                if link_gerado:
                                    if registrar_novo_contrato_admin(u_destino, n_doc, link_gerado, st.secrets):
                                        st.success(f"✅ DOCUMENTO ENVIADO COM SUCESSO!")
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
                        else:
                            st.error("Preencha o nome do doc e selecione o PDF.")

        with col_status:
            st.markdown("### 📋 MONITORAMENTO")
            df_cont = carregar_dados("Contratos", st.secrets["planilha"]["id"])

            if df_cont is not None and not df_cont.empty:
                df_view = pd.merge(df_cont, df_usuarios[['ID_Usuario', 'Nome']], on='ID_Usuario', how='left')
                df_view['Nome'] = df_view['Nome'].fillna(df_view['ID_Usuario'])

                st.dataframe(
                    df_view[['Nome', 'Nome_Arquivo', 'Status']],
                    column_config={
                        "Nome": "Integrante",
                        "Nome_Arquivo": "Documento",
                        "Status": "Situação"
                    },
                    width="stretch",
                    hide_index=True
                )

                with st.expander("🔍 VER LINKS E ARQUIVOS", expanded=True):
                    for _, row in df_view.iterrows():
                        c_info, c_links = st.columns([2, 1.5])

                        with c_info:
                            st.markdown(f"**{row['Nome'].upper()}**")
                            st.caption(f"Arquivo: {row['Nome_Arquivo']}")

                        with c_links:
                            sub_c1, sub_c2 = st.columns(2)
                            sub_c1.link_button("📄 ORIG", row['Link_Original'], width='stretch',
                                               help="Baixar original enviado")

                            link_assin = str(row.get('Link_Assinado', ''))
                            if link_assin.startswith("http"):
                                sub_c2.link_button("✍️ ASSIN", link_assin, width='stretch', type="primary",
                                                   help="Ver assinado pelo integrante")
                            else:
                                sub_c2.button("⏳ PEND", disabled=True, width='stretch')
                        st.divider()
