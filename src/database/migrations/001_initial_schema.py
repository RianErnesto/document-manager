"""
Migration 001: Schema inicial do banco de dados.

Cria a tabela documents e os índices necessários.
Usa IF NOT EXISTS para ser seguro em bancos já existentes.
"""


def up(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT NOT NULL UNIQUE,
            shelf INTEGER NOT NULL,
            box INTEGER NOT NULL,
            rack INTEGER NOT NULL,
            classification INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_qr_code ON documents(qr_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
    """)
