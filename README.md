# Amazon Informatica - Gerenciador de Documentos

Sistema desktop para gerenciamento de documentos com cadastro, visualizacao, filtros, ordenacao, sistema de travas, auditoria e geracao de relatorios em PDF/Excel.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Funcionalidades

### Cadastro de Documentos
- Cadastro com **Codigo QR**, **Estante**, **Prateleira**, **Caixa**, **Classificacao** e **N. do Processo**
- Validacao de campos obrigatorios ao clicar em Cadastrar/Atualizar
- Verificacao de codigo QR duplicado (unico no banco)
- **Mascara automatica** no campo de processo: o usuario digita apenas numeros e o sistema formata como `0000/00000...`
- **Setas de incremento/decremento** nos campos numericos (Estante, Prateleira, Caixa)
- **Sistema de Trava (Lock)**: Campos com cadeado podem ser travados para manter o valor apos cada cadastro
  - Campos travaveis: Estante, Prateleira, Caixa, Classificacao e N. do Processo
  - Util para cadastrar multiplos documentos na mesma localizacao
  - O campo Codigo QR nunca e travavel (sempre limpa apos cadastro)

### Tabela de Documentos
- Visualizacao de todos os documentos cadastrados
- **Ordenacao** por qualquer coluna (clique no cabecalho, alterna ASC/DESC)
- **Busca/Filtro** em tempo real por todas as colunas
- Selecao de linha com toggle (clique para selecionar, clique novamente para deselecionar)
- Duplo clique para edicao rapida
- Botoes **Editar** e **Excluir** aparecem somente quando ha uma linha selecionada
- Paginacao com indicador "Mostrando X-Y de Z"

### Relatorios
- Geracao de relatorios em **PDF** (paisagem A4) e **Excel (XLSX)**
- Filtro por periodo de data (opcional)
- Abertura automatica do arquivo apos geracao
- Relatorios incluem todos os campos: ID, Codigo QR, Estante, Prateleira, Caixa, Classificacao, N. Processo, Data de Cadastro

### Sistema de Auditoria (Logs)
- Logs automaticos de todas as operacoes em `C:\CPD\Logs\document_manager.log`
- Niveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Rotacao automatica por tamanho (5 MB, mantém 5 backups)
- Formato: `[2026-02-25 14:30:00] [INFO] Documento criado — ID: 42, QR: ABC123`
- Eventos registrados:
  - Inicio e encerramento do sistema
  - Criacao, atualizacao e exclusao de documentos
  - Geracao de relatorios
  - Migrations aplicadas
  - Erros no banco de dados e nos relatorios

### Sistema de Migrations
- Migrations automaticas executadas ao iniciar o sistema
- Controle de versao do schema via tabela `schema_migrations`
- Arquivos no formato `NNN_descricao.py` em `src/database/migrations/`
- Migrations aplicadas ate agora:
  - `001_initial_schema` — Tabela inicial com campos basicos
  - `002_classification_to_text` — Alteracao de classificacao de INTEGER para TEXT
  - `003_add_process` — Adicao da coluna processo

## Screenshots

```
+-------------------------------------------------------------+
|  AMAZON INFORMATICA - GERENCIADOR DE DOCUMENTOS  [Relatorios]|
+-------------------------------------------------------------+
|  +-------------------------------------------------------+  |
|  | CADASTRO DE DOCUMENTO                                  |  |
|  |                                                        |  |
|  | Codigo QR *: [________________]   N. Processo *: [____]|  |
|  |                                                        |  |
|  | Estante *:  [__]^v  Prateleira *: [__]^v               |  |
|  | Caixa *:    [__]^v  Classificacao *: [________]         |  |
|  |                                                        |  |
|  | Clique no cadeado para travar/destravar o campo.       |  |
|  |                                                        |  |
|  |                  [Limpar Campos]  [Cadastrar]          |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  | DOCUMENTOS CADASTRADOS  [Editar][Excluir]  Buscar:[__]|  |
|  +----+--------+-----+------+-----+------+------+-------+  |
|  | ID | QR     | Est.| Prat.| Cx  | Class| Proc | Data  |  |
|  +----+--------+-----+------+-----+------+------+-------+  |
|  | 1  | DOC001 | 1   | 2    | 3   | A1   |25/01 | ...   |  |
|  | 2  | DOC002 | 1   | 3    | 1   | B2   |25/02 | ...   |  |
|  +----+--------+-----+------+-----+------+------+-------+  |
|                                       Mostrando 1-15 de 50  |
+-------------------------------------------------------------+
```

## Requisitos

- Python 3.10 ou superior
- Windows 10/11 (recomendado)

## Instalacao

### 1. Clone ou baixe o repositorio

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

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```

## Configuracao com .env

A partir da v1.2.0, o app conecta a um banco SQLite hospedado num servidor de rede SMB. As credenciais e caminhos sao lidos de um arquivo `.env` na mesma pasta do executavel (ou na raiz do projeto, em modo desenvolvimento).

### 1. Criar o `.env`

Copie `.env.example` para `.env` e preencha com os valores reais:

```bash
copy .env.example .env
```

Edite `.env`:

```
DB_SERVER=192.168.3.180
DB_SHARE=BKP-Semas
DB_FILENAME=documents.db
DB_USER=admin
DB_PASSWORD=<senha real>

BACKUP_DIR=C:\CPD\Backups
BACKUP_INTERVAL_HOURS=24
BACKUP_RETENTION_DAYS=30
```

### 2. Pre-requisitos do servidor

A maquina `192.168.3.180` deve:

- Ter `D:\BKP-Semas` compartilhado com nome `BKP-Semas`
- Ter usuario `admin` com permissao de **leitura, escrita e criacao** em `D:\BKP-Semas`
- Ter SMBv2+ habilitado (default no Windows moderno)

### 3. O `.env` nunca e commitado

`.env` esta no `.gitignore`. Apenas `.env.example` (template sem segredos) faz parte do repositorio.

## Execucao

### Modo Desenvolvimento

```bash
# Com ambiente virtual ativo
python src/main.py
```

### Gerar Executavel

```bash
# Com ambiente virtual ativo
python build.py
```

O executavel sera gerado em `dist/DocumentManager.exe`

## Estrutura do Projeto

```
document-manager/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Ponto de entrada
│   ├── app.py                     # Classe principal (janela, icone, logger)
│   ├── config.py                  # Configuracoes (cores, fontes, dimensoes, colunas)
│   ├── components/                # Componentes reutilizaveis de UI
│   │   ├── __init__.py
│   │   ├── button.py              # Botao estilizado (variantes: primary, secondary, etc.)
│   │   ├── input.py               # Input com label e validacao
│   │   ├── lockable_input.py      # Input com trava, spinner numerico e mascara
│   │   ├── table.py               # Tabela com ordenacao, filtro e paginacao
│   │   ├── date_picker.py         # Seletor de data com calendario
│   │   └── message_box.py         # Caixas de mensagem e confirmacao
│   ├── views/                     # Telas da aplicacao
│   │   ├── __init__.py
│   │   ├── main_view.py           # Tela principal (formulario + tabela)
│   │   └── report_dialog.py       # Dialog de relatorios (PDF/Excel)
│   ├── database/                  # Camada de dados
│   │   ├── __init__.py
│   │   ├── connection.py          # Conexao SQLite (singleton, executa migrations)
│   │   ├── document_repository.py # CRUD de documentos
│   │   ├── migrator.py            # Sistema de migrations automaticas
│   │   └── migrations/            # Arquivos de migration
│   │       ├── __init__.py
│   │       ├── 001_initial_schema.py
│   │       ├── 002_classification_to_text.py
│   │       └── 003_add_process.py
│   ├── models/                    # Modelos de dados
│   │   ├── __init__.py
│   │   └── document.py            # Dataclass Document
│   ├── services/                  # Logica de negocio
│   │   ├── __init__.py
│   │   ├── audit_service.py       # Logger de auditoria (singleton, RotatingFileHandler)
│   │   └── report_service.py      # Geracao de relatorios PDF/XLSX
│   ├── utils/                     # Utilitarios
│   │   ├── __init__.py
│   │   └── validators.py
│   └── assets/                    # Recursos visuais
│       └── LogoAmazonSmall.ico    # Icone da aplicacao
├── requirements.txt               # Dependencias Python
├── build.py                       # Script de build (PyInstaller)
├── DocumentManager.spec           # Configuracao do PyInstaller
└── README.md
```

## Componentes Reutilizaveis

### StyledButton
Botao estilizado com variantes de cor.

```python
from src.components.button import StyledButton

btn = StyledButton(
    parent,
    text="Salvar",
    variant="primary",  # primary, secondary, success, danger, warning, outline
    command=callback,
    width=120
)
```

### StyledInput
Input com label e validacao integrada.

```python
from src.components.input import StyledInput

input_field = StyledInput(
    parent,
    label="Nome",
    placeholder="Digite o nome",
    required=True,
    validation_type="text"  # text, number
)
```

### LockableInput
Input com sistema de trava, setas de incremento/decremento para campos numericos e mascara para campo de processo.

```python
from src.components.lockable_input import LockableInput

# Campo numerico com spinner e trava
rack_input = LockableInput(
    parent,
    label="Estante",
    placeholder="N.",
    required=True,
    validation_type="number",  # number, text, process
    width=80,
    lockable=True
)

# Campo de processo com mascara automatica (0000/00000...)
process_input = LockableInput(
    parent,
    label="N. do Processo",
    placeholder="0000/00000",
    required=True,
    validation_type="process",
    width=140,
    lockable=True
)

# Verificar/alterar estado de trava
if rack_input.is_locked():
    pass  # Nao limpar apos cadastro

# Limpar respeitando trava
rack_input.clear(force=False)  # Nao limpa se travado

# Limpar forcando (ignora trava)
rack_input.clear(force=True)
```

**Tipos de validacao:**
| Tipo | Comportamento |
|------|---------------|
| `number` | Aceita apenas digitos. Exibe setas para incrementar/decrementar (minimo 1). |
| `text` | Aceita qualquer texto. |
| `process` | Aceita apenas digitos e aplica mascara automatica `0000/00000...`. Validacao minima: 5 digitos. |

### DataTable
Tabela com ordenacao, filtro, paginacao e selecao com callbacks.

```python
from src.components.table import DataTable

columns = [
    {"key": "id", "label": "ID", "width": 60},
    {"key": "name", "label": "Nome", "width": 200},
]

table = DataTable(
    parent,
    columns=columns,
    on_select=on_select_callback,       # Chamado ao selecionar linha
    on_deselect=on_deselect_callback,   # Chamado ao deselecionar
    on_double_click=on_double_click_callback
)

# Carregar dados
table.set_data([{"id": 1, "name": "Item 1"}, ...])

# Area para botoes de acao no cabecalho (ex: Editar, Excluir)
table.action_frame  # CTkFrame no cabecalho da tabela
```

### MessageBox
Caixas de dialogo para mensagens e confirmacoes.

```python
from src.components.message_box import show_message, show_confirm

# Mensagem simples (variantes: success, error, warning, info)
show_message(parent, "Operacao concluida!", variant="success")

# Confirmacao
if show_confirm(parent, "Deseja excluir?"):
    # Confirmado
```

### DatePicker
Seletor de data com calendario.

```python
from src.components.date_picker import DatePicker

picker = DatePicker(parent, label="Data Inicial")
date = picker.get()  # Retorna datetime.date
picker.clear()
```

## Banco de Dados

O sistema utiliza SQLite com migrations automaticas. O schema atual (apos todas as migrations):

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qr_code TEXT NOT NULL UNIQUE,
    shelf INTEGER NOT NULL,          -- Prateleira
    box INTEGER NOT NULL,            -- Caixa
    rack INTEGER NOT NULL,           -- Estante
    classification TEXT NOT NULL DEFAULT '',  -- Classificacao (texto livre)
    process TEXT NOT NULL DEFAULT '',         -- Numero do processo (ex: 2025/01023)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Controle de migrations
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

A partir da v1.2.0, o `documents.db` reside em `\\192.168.3.180\BKP-Semas\` (servidor de arquivos do CPD). Cada estacao cliente conecta via UNC path autenticando com as credenciais do `.env` no startup. Se o arquivo nao existir no servidor, o app cria automaticamente — desde que o usuario configurado tenha permissao de criacao. Migrations sao protegidas por lock exclusivo (`BEGIN IMMEDIATE`): clientes simultaneos esperam o lock e nao corrompem o schema. Operacoes normais de INSERT/UPDATE tambem serializam pelo `busy_timeout` configurado (30s), suficiente pro volume baixo de cadastros do CPD.

## Deploy em multiplas estacoes (v1.2.0+)

1. **Pre-requisito do servidor (`192.168.3.180`):** pasta `D:\BKP-Semas` compartilhada como `BKP-Semas`, usuario `admin` com permissao de leitura/escrita/criacao.

2. **Migracao inicial dos dados** (uma unica vez): para preservar os dados existentes, copie o `documents.db` da estacao com a base mais completa para `\\192.168.3.180\BKP-Semas\documents.db`. Para comecar do zero, pule este passo — o app cria um banco vazio na primeira execucao.

3. **Em cada estacao cliente:**
   - Substitua o `DocumentManager.exe` pelo build da v1.2.0.
   - Crie o `.env` ao lado do `.exe`, copiando de `.env.example` e preenchendo `DB_PASSWORD`.
   - Confira que o usuario logado consegue criar `C:\CPD\Backups\` (mesmo padrao de `C:\CPD\Logs\`).
   - Primeira abertura: o app vai conectar, rodar migrations pendentes e gerar o backup inicial em `C:\CPD\Backups\` (proximos backups respeitam `BACKUP_INTERVAL_HOURS`).

4. **Rollback:** se algo der muito errado nos primeiros dias, voltar para `DocumentManager.exe` v1.1.0 em cada estacao. Os dados acumulados na v1.2.0 ficam no servidor, mas cada estacao volta a usar seu `documents.db` local antigo (defasado desde antes do upgrade). **Antes** do rollback, exporte os dados do servidor (`\\192.168.3.180\BKP-Semas\documents.db`) e reimporte numa unica estacao escolhida como fonte canonica — senao cada estacao fica com versoes diferentes e divergentes da base. **Valide o checklist manual antes de fazer rollout amplo** pra evitar precisar deste caminho.

## Sincronizar dados de um .db local pro servidor

Quando um arquivo `documents.db` "remanescente" precisa ter seus dados consolidados no banco central do servidor (estacao desativada, backup antigo, base offline), use o script `scripts/sync_local_to_server.py`.

### Pre-requisitos

- Python e venv do projeto ativos (`pip install -r requirements.txt`)
- `.env` na raiz do projeto configurado com as variaveis do servidor (DB_SERVER, DB_USER, DB_PASSWORD etc.)
- Caminho do `.db` de origem em maos

### Comando

```cmd
venv\Scripts\python scripts\sync_local_to_server.py <caminho_do_db>
```

Flags:

- `-f` / `--force` — em conflito de `qr_code`, source sobrescreve servidor (default: servidor vence)
- `--log-dir DIR` — onde salvar o log da execucao (default: `C:\CPD\Logs`)

### Exemplos

```cmd
venv\Scripts\python scripts\sync_local_to_server.py D:\backups\estacao03.db

venv\Scripts\python scripts\sync_local_to_server.py D:\backups\estacao03.db -f

venv\Scripts\python scripts\sync_local_to_server.py "C:\Users\joao\Desktop\old.db" --log-dir D:\sync_logs
```

### O que o script faz

- Le todas as linhas de `documents` do `.db` local (read-only — nunca modifica o source)
- Pra cada linha, busca no servidor pelo `qr_code` (UNIQUE)
- Se nao existe -> insere os 6 campos (`qr_code, shelf, box, rack, classification, process`)
- Se existe e for **identica** -> pula
- Se existe mas algum campo difere:
  - Modo default -> pula e loga como "conflito" (servidor preservado)
  - Modo `-f` -> atualiza o servidor com os 6 campos do source e bate o `updated_at`

### Saida esperada

Cada execucao gera um log em `C:\CPD\Logs\sync_YYYY-MM-DD_HHMMSS.log` com o mesmo conteudo que aparece no terminal:

```
[2026-04-29 14:23:01] [INFO] === Sync iniciado ===
[2026-04-29 14:23:01] [INFO] Source:  D:\backups\estacao03.db
[2026-04-29 14:23:01] [INFO] Destino: \\AMZ-GD-02\Teste\documents.db
[2026-04-29 14:23:01] [INFO] Modo:    server-wins (default)
[2026-04-29 14:23:02] [INFO] Linhas no source: 247
[2026-04-29 14:23:03] [WARN] Conflito qr_code=DOC042
                              source:   shelf=5, ...
                              servidor: shelf=7, ...
                              acao: mantido servidor (rode com -f pra sobrescrever)
[2026-04-29 14:23:04] [INFO] === Resumo ===
[2026-04-29 14:23:04] [INFO] Total processado:  247
[2026-04-29 14:23:04] [INFO] Inseridos:         231
[2026-04-29 14:23:04] [INFO] Identicos (skip):  15
[2026-04-29 14:23:04] [INFO] Conflitos (skip):  1
[2026-04-29 14:23:04] [INFO] Sobrescritos:      0
```

### Reexecucao

O script e idempotente — pode rodar varias vezes seguidas. Linhas ja no servidor sao puladas. Util se a primeira execucao interromper por queda de rede.

## Tecnologias Utilizadas

| Tecnologia | Uso |
|------------|-----|
| **Python 3.10+** | Linguagem principal |
| **CustomTkinter** | Interface grafica moderna |
| **SQLite3** | Banco de dados (nativo do Python) |
| **ReportLab** | Geracao de relatorios em PDF |
| **OpenPyXL** | Geracao de planilhas Excel |
| **tkcalendar** | Seletor de data com calendario |
| **PyInstaller** | Geracao de executavel Windows |

## Dependencias

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

1. Preencha o **Codigo QR** (obrigatorio e unico)
2. Preencha **N. do Processo** (formato `0000/00000...`, mascara automatica)
3. Preencha **Estante**, **Prateleira** e **Caixa** (use as setas ou digite numeros)
4. Preencha **Classificacao** (texto livre, ex: A1, Fiscal, etc.)
5. Opcionalmente, clique no cadeado para travar campos que devem manter o valor
6. Clique em **Cadastrar**
7. Campos travados manterao seus valores para o proximo cadastro; o foco volta ao Codigo QR

### Editar Documento

1. Selecione um documento na tabela (clique na linha)
2. Os botoes **Editar** e **Excluir** aparecerão ao lado de "Documentos Cadastrados"
3. Clique em **Editar** ou de duplo clique na linha
4. Altere os campos desejados
5. Clique em **Atualizar**
6. Para cancelar, clique em **Cancelar Edicao**

### Excluir Documento

1. Selecione um documento na tabela
2. Clique em **Excluir**
3. Confirme a exclusao na caixa de dialogo

### Gerar Relatorio

1. Clique no botao **Relatorios** no canto superior direito
2. Opcionalmente, selecione um periodo de datas
3. Escolha o formato (**PDF** ou **Excel**)
4. Clique em **Gerar Relatorio**
5. Escolha onde salvar o arquivo
6. O arquivo sera aberto automaticamente apos a geracao

### Ordenar Tabela

- Clique no cabecalho de qualquer coluna para ordenar
- Clique novamente para inverter a ordem (ASC/DESC)
- Indicador visual (seta) mostra a coluna e direcao ativas

### Filtrar/Buscar

- Digite no campo **Buscar** acima da tabela para filtrar documentos
- A busca e feita em todas as colunas (QR, Estante, Prateleira, Caixa, Classificacao, Processo)

## Arquivos de Log

Os logs sao salvos em `C:\CPD\Logs\document_manager.log` com rotacao automatica.

Para visualizar os logs:
```bash
type C:\CPD\Logs\document_manager.log
```

Exemplo de saida:
```
[2026-02-25 14:30:00] [INFO] Sistema iniciado — versao 1.0.0
[2026-02-25 14:30:01] [INFO] Migration aplicada: 003_add_process
[2026-02-25 14:31:15] [INFO] Documento criado — ID: 42, QR: ABC123
[2026-02-25 14:32:00] [INFO] Documento atualizado — ID: 42, QR: ABC123
[2026-02-25 14:33:00] [INFO] Documento excluido — ID: 42, QR: ABC123
[2026-02-25 14:35:00] [ERROR] Erro ao cadastrar documento (QR: DUP001): UNIQUE constraint failed
[2026-02-25 14:40:00] [INFO] Sistema encerrado
```

## Licenca

Este projeto esta sob a licenca MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Autor

Desenvolvido para **Amazon Informatica** — Gerenciamento de documentos do CPD.

---

**Amazon Informatica - Gerenciador de Documentos** — Cadastro, organizacao e rastreamento de documentos.
