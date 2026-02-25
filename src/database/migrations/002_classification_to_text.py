"""
Migration 002: Altera classification de INTEGER para TEXT.

SQLite não suporta ALTER COLUMN, então recriamos a tabela
copiando os dados existentes com CAST para TEXT.
"""


def up(cursor):
    cursor.execute("""
        CREATE TABLE documents_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT NOT NULL UNIQUE,
            shelf INTEGER NOT NULL,
            box INTEGER NOT NULL,
            rack INTEGER NOT NULL,
            classification TEXT NOT NULL DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO documents_new (id, qr_code, shelf, box, rack, classification, created_at, updated_at)
        SELECT id, qr_code, shelf, box, rack, CAST(classification AS TEXT), created_at, updated_at
        FROM documents
    """)

    cursor.execute("DROP TABLE documents")

    cursor.execute("ALTER TABLE documents_new RENAME TO documents")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_qr_code ON documents(qr_code)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at)
    """)
