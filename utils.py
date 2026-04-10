# =============================================================================
# UTILS.PY - FUNÇÕES UTILITÁRIAS E CONEXÕES (SEM UI STREAMLIT)
# =============================================================================

from datetime import datetime, timezone, timedelta
import gspread
import io
import pandas as pd
import requests
from geopy.geocoders import Nominatim
import streamlit as st
import traceback

# Google Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.discovery import build

# =============================================================================
# CONFIGURAÇÕES GLOBAIS
# =============================================================================

TIMEZONE_OFFSET = -3  # Horário de Brasília


# =============================================================================
# FUNÇÕES DE TEMPO
# =============================================================================

def get_agora_br():
    """Retorna horário atual em Brasília de forma consistente"""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=TIMEZONE_OFFSET)


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================

def validar_gps_basico(coords_str):
    """Verifica se as coordenadas parecem válidas (faixa do Brasil)"""
    if not coords_str or coords_str in ["Sem GPS", "Não informada", "Erro GPS", "Aguardando...",
                                        "GPS Inválido/Desativado"]:
        return False
    try:
        if "," in str(coords_str):
            lat, lon = map(float, str(coords_str).split(','))
            return -35 < lat < 5 and -75 < lon < -35
    except:
        pass
    return False


def sanitize_whatsapp(v):
    """
    Limpa e formata números de WhatsApp brasileiros.
    """
    if v is None or str(v).lower() in ["nan", "none", ""]:
        return ""

    s = str(v).strip().split('.')[0]
    nums = "".join(filter(str.isdigit, s))

    if nums.startswith("55") and len(nums) >= 12:
        core = nums[2:]
    else:
        core = nums

    if core.startswith("0"):
        core = core[1:]

    if len(core) == 10:
        core = core[:2] + "9" + core[2:]

    if len(core) == 11:
        return "55" + core

    return nums if len(nums) >= 10 else ""


# =============================================================================
# FUNÇÕES DE GOOGLE - CREDENCIAIS
# =============================================================================

def _get_drive_credentials(secrets, error_log=None):
    """Usa OAuthCredentials (Refresh Token) para os 15GB do Drive"""
    try:
        creds_info = secrets["google_drive"]
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
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_get_drive_credentials',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao carregar credenciais do Drive: {e}")
        return None


def _get_sheets_credentials(secrets, error_log=None):
    """Service Account - Para o Sheets (Logs/Usuarios)"""
    try:
        creds_dict = secrets.get("connections", {}).get("gsheets")
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_service_account_info(creds_dict, scopes=scope)
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_get_sheets_credentials',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro credenciais Sheets: {e}")
        return None


def _get_gspread_client(secrets, error_log=None):
    """Inicializa cliente do Google Sheets"""
    try:
        creds = _get_sheets_credentials(secrets, error_log)
        return gspread.authorize(creds) if creds else None
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': '_get_gspread_client',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao inicializar gspread: {e}")
        return None


# =============================================================================
# FUNÇÕES DE GOOGLE SHEETS - DADOS
# =============================================================================

def carregar_dados(nome_aba, planilha_id, error_log=None):
    """Carrega dados de uma aba da planilha como DataFrame"""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df = pd.read_csv(url)
        return df.astype(str).apply(lambda x: x.str.strip())
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'carregar_dados',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao carregar dados: {e}")
        return None


def registrar_acao(id_usuario, tipo_acao, localizacao, feedback, secrets, error_log=None):
    """Registra ação do usuário na planilha de Logs"""
    try:
        loc_safe = str(localizacao) if localizacao is not None else "Não informada"
        gps_valido = validar_gps_basico(loc_safe)
        if not gps_valido:
            loc_safe = "GPS Inválido/Desativado"

        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Logs")
        agora_br = get_agora_br()

        endereco = "Sem GPS"
        if gps_valido:
            endereco = obter_endereco_simples(loc_safe, error_log)

        aba.append_row([
            agora_br.strftime("%Y%m%d%H%M%S"),
            str(id_usuario),
            str(tipo_acao),
            agora_br.strftime("%d/%m/%Y %H:%M:%S"),
            loc_safe,
            str(endereco),
            str(feedback)
        ])
        return True

    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'registrar_acao',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao registrar ação: {e}")
        return False


def registrar_novo_contrato_admin(id_usuario, nome_arquivo, link_original, secrets, error_log=None):
    """Cria uma nova linha na aba Contratos"""
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Contratos")

        aba.append_row([
            str(id_usuario),
            str(nome_arquivo),
            str(link_original),
            "Aguardando Assinatura",
            ""
        ])
        return True
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'registrar_novo_contrato_admin',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao registrar contrato: {e}")
        return False


def atualizar_contrato_enviado(id_usuario, nome_arquivo, link_drive, secrets, error_log=None):
    """Atualiza o link e status do contrato na planilha"""
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Contratos")
        dados = aba.get_all_records()
        linha_para_atualizar = None

        for i, linha in enumerate(dados, start=2):
            if str(linha.get('ID_Usuario')) == str(id_usuario) and \
                    str(linha.get('Nome_Arquivo')) == str(nome_arquivo):
                linha_para_atualizar = i
                break

        if linha_para_atualizar:
            cabecalho = aba.row_values(1)

            if 'Link_Assinado' in cabecalho:
                col_link = cabecalho.index('Link_Assinado') + 1
                aba.update_cell(linha_para_atualizar, col_link, link_drive)

            if 'Status' in cabecalho:
                col_status = cabecalho.index('Status') + 1
                aba.update_cell(linha_para_atualizar, col_status, "Assinado / Em Análise")

            return True
        return False
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'atualizar_contrato_enviado',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Falha ao atualizar contrato: {e}")
        return False


# =============================================================================
# FUNÇÕES DE GOOGLE DRIVE - UPLOAD
# =============================================================================

def salvar_foto_drive(foto_arquivo, nome_arquivo, secrets, error_log=None):
    """Salva foto no Google Drive"""
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if not creds:
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_fotos = secrets["google_drive"]["id_pasta_fotos"]

        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_fotos]}
        foto_bytes = io.BytesIO(foto_arquivo.getvalue())
        media = MediaIoBaseUpload(foto_bytes, mimetype='image/jpeg', resumable=False)

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'salvar_foto_drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro no Drive (Foto): {e}")
        return None


def salvar_documento_drive(doc_arquivo, nome_arquivo, secrets, error_log=None):
    """Salva documento PDF no Google Drive"""
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if not creds:
            return None

        drive_service = build('drive', 'v3', credentials=creds)
        id_pasta_contratos = secrets["google_drive"]["id_pasta_contratos"]

        file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_contratos]}
        doc_bytes = io.BytesIO(doc_arquivo.getvalue())
        media = MediaIoBaseUpload(doc_bytes, mimetype='application/pdf', resumable=False)

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file.get('webViewLink')
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'salvar_documento_drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro no Drive (Docs): {e}")
        return None


# =============================================================================
# FUNÇÕES DE API EXTERNA
# =============================================================================

def obter_endereco_simples(coords_str, error_log=None):
    """Converte 'lat, lon' em um endereço curto (Rua ou Bairro)"""
    c_str = str(coords_str) if coords_str is not None else ""

    if not c_str or "GPS" in c_str or "informada" in c_str or "," not in c_str:
        return "Local não identificado"

    try:
        geolocator = Nominatim(user_agent="comando2026_geocoder")
        location = geolocator.reverse(c_str, timeout=10)
        address = location.raw.get('address', {})

        rua = address.get('road', '')
        bairro = address.get('suburb', '')
        cidade = address.get('city', address.get('town', ''))

        if rua:
            return f"{rua}, {bairro}".strip(", ")
        return f"{bairro}, {cidade}".strip(", ")
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'obter_endereco_simples',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        print(f"Erro ao obter endereço: {e}")
        return "Endereço indisponível"


# =============================================================================
# FUNÇÕES DE GESTÃO DE GRUPOS E MACRO_GRUPOS (COM CACHE)
# =============================================================================

@st.cache_data(ttl=120)  # Cache por 2 minutos
def carregar_macro_grupos_cached(planilha_id):
    """Carrega lista única de Macro_Grupos da planilha Grupos (COM CACHE)"""
    try:
        # Usa URL pública para evitar chamada de API
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?tqx=out:csv&sheet=Grupos"
        df = pd.read_csv(url)

        # Extrai Macro_Grupos únicos (excluindo vazios)
        if 'Macro_Grupo' in df.columns:
            macro_grupos = list(set([
                str(val).strip()
                for val in df['Macro_Grupo'].dropna().unique()
                if str(val).strip()
            ]))
            return sorted(macro_grupos)
        return []
    except Exception as e:
        print(f"Erro ao carregar Macro_Grupos: {e}")
        return []


@st.cache_data(ttl=120)  # Cache por 2 minutos
def carregar_grupos_completos_cached(planilha_id):
    """Carrega todos os grupos com suas informações (COM CACHE)"""
    try:
        # Usa URL pública para evitar chamada de API
        url = f"https://docs.google.com/spreadsheets/d/{planilha_id}/gviz/tq?tqx=out:csv&sheet=Grupos"
        df = pd.read_csv(url)

        # ✅ FILTRA: Exclui linhas que são apenas Macro_Grupos (ID começa com "_MACRO_")
        df_filtrado = df[~df['ID_Grupo'].astype(str).str.startswith('_MACRO_')]

        # Converte para lista de dicionários
        dados = df_filtrado.to_dict('records')
        return dados
    except Exception as e:
        print(f"Erro ao carregar Grupos: {e}")
        return []


def criar_novo_grupo(nome_grupo, macro_grupo, link_grupo, secrets, error_log=None):
    """Cria um novo grupo na planilha"""
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False, "Erro de conexão"

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Grupos")

        # Verifica se já existe
        dados = aba.get_all_records()
        for row in dados:
            if str(row.get('ID_Grupo', '')).upper() == str(nome_grupo).upper():
                return False, "Grupo já existe"

        # Adiciona novo grupo
        aba.append_row([
            str(nome_grupo).upper(),
            str(macro_grupo).strip(),
            str(link_grupo).strip()
        ])

        # Limpa cache após criação
        carregar_macro_grupos_cached.clear()
        carregar_grupos_completos_cached.clear()

        return True, "Grupo criado com sucesso"
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'criar_novo_grupo',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return False, f"Erro: {str(e)}"


def criar_novo_macro_grupo(nome_macro, secrets, error_log=None):
    """Cria um novo Macro_Grupo (adiciona entrada na planilha Grupos)"""
    try:
        client = _get_gspread_client(secrets, error_log)
        if client is None:
            return False, "Erro de conexão"

        planilha = client.open_by_key(secrets["planilha"]["id"])
        aba = planilha.worksheet("Grupos")

        # Verifica se já existe
        dados = aba.get_all_records()
        for row in dados:
            if str(row.get('Macro_Grupo', '')).strip().upper() == str(nome_macro).upper():
                return False, "Macro_Grupo já existe"

        # Adiciona entrada
        aba.append_row([
            f"_MACRO_{nome_macro.upper().replace(' ', '_')}",
            str(nome_macro).strip(),
            ""
        ])

        # Limpa cache após criação
        carregar_macro_grupos_cached.clear()
        carregar_grupos_completos_cached.clear()

        return True, "Macro_Grupo criado com sucesso"
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'criar_novo_macro_grupo',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return False, f"Erro: {str(e)}"



# =============================================================================
# FUNÇÕES DE DIAGNÓSTICO E SUPORTE TÉCNICO
# =============================================================================

def diagnosticar_conexoes(secrets, error_log=None):
    """Testa todas as conexões do sistema e retorna status"""
    resultados = {
        'sheets': {'status': '❌', 'msg': ''},
        'drive': {'status': '❌', 'msg': ''},
        'planilha': {'status': '❌', 'msg': ''},
        'cache': {'status': '❌', 'msg': ''}
    }

    # Teste Google Sheets
    try:
        client = _get_gspread_client(secrets, error_log)
        if client:
            resultados['sheets'] = {'status': '✅', 'msg': 'Conectado'}
            planilha = client.open_by_key(secrets["planilha"]["id"])
            resultados['planilha'] = {'status': '✅', 'msg': f'{planilha.title}'}
        else:
            resultados['sheets'] = {'status': '❌', 'msg': 'Falha na autenticação'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.sheets',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['sheets'] = {'status': '❌', 'msg': str(e)}

    # Teste Google Drive
    try:
        creds = _get_drive_credentials(secrets, error_log)
        if creds:
            resultados['drive'] = {'status': '✅', 'msg': 'Conectado'}
        else:
            resultados['drive'] = {'status': '❌', 'msg': 'Falha na autenticação'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.drive',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['drive'] = {'status': '❌', 'msg': str(e)}

    # Teste Cache
    try:
        carregar_macro_grupos_cached(secrets["planilha"]["id"])
        resultados['cache'] = {'status': '✅', 'msg': 'Funcionando'}
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'diagnosticar_conexoes.cache',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        resultados['cache'] = {'status': '❌', 'msg': str(e)}

    return resultados


def obter_logs_erros(error_log_session, limite=50):
    """Retorna lista de erros da sessão atual"""
    if not error_log_session:
        return []

    return error_log_session[-limite:]


def contar_chamadas_api():
    """Estimativa de chamadas à API (baseado no cache)"""
    # Isso é mais informativo, já que gviz não conta como API call
    return {
        'sheets_api': '0 (usando gviz)',
        'drive_api': 'Variável (uploads)',
        'cache_hits': 'Ativo (ttl=120s)'
    }


def simular_acao_usuario(id_usuario, tipo_acao, secrets, error_log=None):
    """Simula uma ação para teste (não grava na planilha)"""
    try:
        return {
            'id_usuario': id_usuario,
            'tipo_acao': tipo_acao,
            'timestamp': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'status': 'SIMULAÇÃO (não gravado)',
            'gps_teste': '-15.7801,-47.9292',
            'endereco_teste': obter_endereco_simples('-15.7801,-47.9292', error_log)
        }
    except Exception as e:
        if error_log is not None:
            error_log.append({
                'data': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
                'erro': str(e),
                'funcao': 'simular_acao_usuario',
                'traceback': traceback.format_exc(),
                'tipo': type(e).__name__
            })
        return {
            'id_usuario': id_usuario,
            'tipo_acao': tipo_acao,
            'timestamp': get_agora_br().strftime("%d/%m/%Y %H:%M:%S"),
            'status': 'SIMULAÇÃO FALHOU',
            'erro': str(e)
        }
