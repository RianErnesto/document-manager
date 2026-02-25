"""
Configurações centralizadas da aplicação Document Manager.
"""

# Informações da Aplicação
APP_NAME = "Amazon Informática - Gerenciador de Documentos"
COMPANY_NAME = "Amazon Informática"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 750
MIN_WIDTH = 900
MIN_HEIGHT = 600

# Paleta de Cores - Azul Profissional
COLORS = {
    "primary": "#1a73e8",
    "primary_hover": "#1557b0",
    "primary_light": "#e8f0fe",
    "secondary": "#5f6368",
    "secondary_hover": "#4a4d51",
    "success": "#34a853",
    "success_hover": "#2d9249",
    "danger": "#ea4335",
    "danger_hover": "#d33828",
    "warning": "#fbbc04",
    "warning_hover": "#e5ab00",
    "background": "#f8f9fa",
    "surface": "#ffffff",
    "text": "#202124",
    "text_secondary": "#5f6368",
    "text_light": "#ffffff",
    "border": "#dadce0",
    "border_focus": "#1a73e8",
    "locked": "#fef7e0",
    "locked_border": "#f9ab00",
}

# Fontes
FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "subtitle": ("Segoe UI", 16, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 12, "bold"),
    "small": ("Segoe UI", 10),
    "button": ("Segoe UI", 12, "bold"),
    "input": ("Segoe UI", 12),
    "table_header": ("Segoe UI", 11, "bold"),
    "table_body": ("Segoe UI", 11),
}

# Dimensões dos Componentes
DIMENSIONS = {
    "button_height": 36,
    "button_padding": 16,
    "input_height": 36,
    "input_padding": 12,
    "border_radius": 6,
    "card_padding": 20,
    "spacing_xs": 4,
    "spacing_sm": 8,
    "spacing_md": 16,
    "spacing_lg": 24,
    "spacing_xl": 32,
}

# Configurações do Banco de Dados
DATABASE = {
    "name": "documents.db",
    "table_name": "documents",
}

# Configurações da Tabela
TABLE = {
    "row_height": 35,
    "header_height": 40,
    "rows_per_page": 15,
}

# Formato de Data
DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DATE_FORMAT_DB = "%Y-%m-%d %H:%M:%S"

# Mensagens
MESSAGES = {
    "success_save": "Documento cadastrado com sucesso!",
    "success_update": "Documento atualizado com sucesso!",
    "success_delete": "Documento excluído com sucesso!",
    "error_required": "Este campo é obrigatório",
    "error_number": "Este campo aceita apenas números",
    "error_duplicate": "Código QR já cadastrado",
    "error_not_found": "Documento não encontrado",
    "confirm_delete": "Deseja realmente excluir este documento?",
    "report_success": "Relatório gerado com sucesso!",
    "report_error": "Erro ao gerar relatório",
    "no_data": "Nenhum documento encontrado no período selecionado",
}

# Colunas da Tabela
TABLE_COLUMNS = [
    {"key": "id", "label": "ID", "width": 60},
    {"key": "qr_code", "label": "Código QR", "width": 180},
    {"key": "rack", "label": "Estante", "width": 70},
    {"key": "shelf", "label": "Prateleira", "width": 80},
    {"key": "box", "label": "Caixa", "width": 70},
    {"key": "classification", "label": "Classificação", "width": 120},
    {"key": "created_at", "label": "Data de Cadastro", "width": 140},
]
