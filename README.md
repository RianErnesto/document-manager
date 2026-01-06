# Document Manager

Sistema desktop para gerenciamento de documentos com cadastro, visualização, filtros, ordenação e geração de relatórios.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Funcionalidades

### Cadastro de Documentos
- Cadastro de documentos com **Código QR**, **Estante**, **Prateleira** e **Caixa**
- Validação de campos obrigatórios em tempo real
- Verificação de código QR duplicado
- **Sistema de Trava (Lock)**: Permite travar campos numéricos para agilizar cadastro em massa
  - Campos travados mantêm o valor após cada cadastro
  - Útil para cadastrar múltiplos documentos na mesma localização

### Tabela de Documentos
- Visualização de todos os documentos cadastrados
- **Ordenação** por qualquer coluna (clique no cabeçalho)
- **Busca/Filtro** em tempo real
- Seleção de linha para edição ou exclusão
- Duplo clique para edição rápida

### Relatórios
- Geração de relatórios em **PDF** e **Excel (XLSX)**
- Filtro por período de data (opcional)
- Abertura automática do arquivo após geração

## Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│  DOCUMENT MANAGER                              [Relatórios] │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │ CADASTRO DE DOCUMENTO                               │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Código QR: [________________]                       │    │
│  │                                                     │    │
│  │ Estante:   [____] 🔓  Prateleira: [____] 🔓        │    │
│  │ Caixa:     [____] 🔓                                │    │
│  │                                                     │    │
│  │              [Limpar]  [Cadastrar]                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ DOCUMENTOS CADASTRADOS              Buscar: [_____] │    │
│  ├───────┬──────────┬──────────┬────────┬─────────────┤    │
│  │ ID ▼  │ QR Code  │ Estante  │ Prat.  │ Caixa │ Data│    │
│  ├───────┼──────────┼──────────┼────────┼─────────────┤    │
│  │ 1     │ DOC001   │ 1        │ 2      │ 3     │ ... │    │
│  │ 2     │ DOC002   │ 1        │ 3      │ 1     │ ... │    │
│  └───────┴──────────┴──────────┴────────┴─────────────┘    │
│                                                             │
│  [Editar] [Excluir]                    Mostrando 1-10 de 50 │
└─────────────────────────────────────────────────────────────┘
```

## Requisitos

- Python 3.10 ou superior
- Windows 10/11 (recomendado)

## Instalação

### 1. Clone ou baixe o repositório

```bash
git clone https://github.com/seu-usuario/document-manager.git
cd document-manager
```

### 2. Crie e ative o ambiente virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## Execução

### Modo Desenvolvimento

```bash
# Com ambiente virtual ativo
python src/main.py
```

### Gerar Executável

```bash
# Com ambiente virtual ativo
python build.py
```

O executável será gerado em `dist/DocumentManager.exe`

## Estrutura do Projeto

```
document-manager/
├── venv/                      # Ambiente virtual (não versionado)
├── src/
│   ├── __init__.py
│   ├── main.py                # Ponto de entrada
│   ├── app.py                 # Classe principal da aplicação
│   ├── config.py              # Configurações (cores, fontes, etc.)
│   ├── components/            # Componentes reutilizáveis
│   │   ├── __init__.py
│   │   ├── button.py          # Botão estilizado
│   │   ├── input.py           # Input com validação
│   │   ├── lockable_input.py  # Input com trava
│   │   ├── table.py           # Tabela com filtro e ordenação
│   │   ├── date_picker.py     # Seletor de data
│   │   └── message_box.py     # Caixas de mensagem
│   ├── views/                 # Telas da aplicação
│   │   ├── __init__.py
│   │   ├── main_view.py       # Tela principal
│   │   └── report_dialog.py   # Dialog de relatórios
│   ├── database/              # Camada de dados
│   │   ├── __init__.py
│   │   ├── connection.py      # Conexão SQLite
│   │   └── document_repository.py
│   ├── models/                # Modelos de dados
│   │   ├── __init__.py
│   │   └── document.py
│   ├── services/              # Lógica de negócio
│   │   ├── __init__.py
│   │   └── report_service.py  # Geração de relatórios
│   └── utils/                 # Utilitários
│       ├── __init__.py
│       └── validators.py
├── assets/                    # Recursos (ícones)
│   └── icon.ico
├── requirements.txt           # Dependências
├── build.py                   # Script de build
└── README.md
```

## Componentes Reutilizáveis

A aplicação foi desenvolvida com forte componentização para facilitar manutenção e reutilização:

### StyledButton
Botão estilizado com variantes de cor.

```python
from src.components import StyledButton

btn = StyledButton(
    parent,
    text="Salvar",
    variant="primary",  # primary, secondary, success, danger, warning, outline
    command=callback,
    width=120
)
```

### StyledInput
Input com label e validação integrada.

```python
from src.components import StyledInput

input = StyledInput(
    parent,
    label="Nome",
    placeholder="Digite o nome",
    required=True,
    validation_type="text"  # text, number
)
```

### LockableInput
Input numérico com sistema de trava.

```python
from src.components import LockableInput

input = LockableInput(
    parent,
    label="Estante",
    required=True,
    lockable=True
)

# Verificar se está travado
if input.is_locked():
    # Não limpar após cadastro

# Limpar forçando (ignora trava)
input.clear(force=True)
```

### DataTable
Tabela com ordenação e filtro.

```python
from src.components import DataTable

columns = [
    {"key": "id", "label": "ID", "width": 60},
    {"key": "name", "label": "Nome", "width": 200},
]

table = DataTable(
    parent,
    columns=columns,
    on_select=on_select_callback,
    on_double_click=on_double_click_callback
)

table.set_data([{"id": 1, "name": "Item 1"}, ...])
```

### MessageBox
Caixas de diálogo para mensagens e confirmações.

```python
from src.components.message_box import show_message, show_confirm

# Mensagem simples
show_message(parent, "Operação concluída!", variant="success")

# Confirmação
if show_confirm(parent, "Deseja excluir?"):
    # Confirmado
```

### DatePicker
Seletor de data com calendário.

```python
from src.components import DatePicker

picker = DatePicker(parent, label="Data Inicial")
date = picker.get()  # Retorna datetime.date
picker.clear()
```

## Banco de Dados

O sistema utiliza SQLite com o seguinte schema:

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_code TEXT NOT NULL UNIQUE,
    shelf INTEGER NOT NULL,        -- Prateleira
    box INTEGER NOT NULL,          -- Caixa
    rack INTEGER NOT NULL,         -- Estante
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

O arquivo `documents.db` é criado automaticamente na pasta do executável.

## Tecnologias Utilizadas

| Tecnologia | Uso |
|------------|-----|
| **Python 3.10+** | Linguagem principal |
| **CustomTkinter** | Interface gráfica moderna |
| **SQLite3** | Banco de dados (nativo) |
| **ReportLab** | Geração de PDFs |
| **OpenPyXL** | Geração de planilhas Excel |
| **tkcalendar** | Seletor de data |
| **PyInstaller** | Geração de executável |

## Dependências

```
customtkinter>=5.2.0
pillow>=10.0.0
reportlab>=4.0.0
openpyxl>=3.1.0
tkcalendar>=1.6.1
pyinstaller>=6.0.0
```

## Como Usar

### Cadastrar Documento

1. Preencha o **Código QR** (obrigatório e único)
2. Preencha **Estante**, **Prateleira** e **Caixa** (apenas números)
3. Opcionalmente, clique no cadeado 🔓 para travar campos
4. Clique em **Cadastrar**
5. Se campos estiverem travados, eles mantêm o valor para o próximo cadastro

### Editar Documento

1. Selecione um documento na tabela
2. Clique em **Editar** ou dê duplo clique na linha
3. Altere os campos desejados
4. Clique em **Atualizar**

### Excluir Documento

1. Selecione um documento na tabela
2. Clique em **Excluir**
3. Confirme a exclusão

### Gerar Relatório

1. Clique no botão **Relatórios** no canto superior direito
2. Opcionalmente, selecione um período de datas
3. Escolha o formato (PDF ou Excel)
4. Clique em **Gerar Relatório**
5. Escolha onde salvar o arquivo

### Ordenar Tabela

- Clique no cabeçalho de qualquer coluna para ordenar
- Clique novamente para inverter a ordem (ASC/DESC)

### Filtrar/Buscar

- Digite no campo **Buscar** para filtrar documentos
- A busca é feita em todas as colunas

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Autor

Desenvolvido como MVP para gerenciamento de documentos.

---

**Document Manager** - Gerenciamento simples e eficiente de documentos.
