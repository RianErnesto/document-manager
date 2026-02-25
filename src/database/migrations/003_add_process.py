"""
Migration 003: Adiciona coluna 'process' (número do processo) à tabela documents.
"""


def up(cursor):
    cursor.execute("""
        ALTER TABLE documents ADD COLUMN process TEXT NOT NULL DEFAULT ''
    """)
