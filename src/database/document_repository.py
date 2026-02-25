"""
Repositório para operações CRUD de documentos.
"""
from datetime import datetime
from typing import List, Optional, Tuple

from ..models.document import Document
from ..services.audit_service import AuditLogger
from .connection import DatabaseConnection


class DocumentRepository:
    """Classe para gerenciar operações de documentos no banco de dados."""

    def __init__(self):
        self._db = DatabaseConnection()
        self._conn = self._db.get_connection()
        self._logger = AuditLogger()

    def create(self, document: Document) -> Tuple[bool, str, Optional[int]]:
        """
        Cria um novo documento.
        Retorna (sucesso, mensagem, id_criado).
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (qr_code, shelf, box, rack, classification, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.qr_code,
                    document.shelf,
                    document.box,
                    document.rack,
                    document.classification,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self._conn.commit()
            return True, "Documento cadastrado com sucesso!", cursor.lastrowid
        except Exception as e:
            self._logger.error(f"Erro ao cadastrar documento (QR: {document.qr_code}): {e}")
            if "UNIQUE constraint failed" in str(e):
                return False, "Código QR já cadastrado!", None
            return False, f"Erro ao cadastrar: {str(e)}", None

    def get_all(
        self,
        search: str = "",
        order_by: str = "id",
        order_dir: str = "DESC",
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
    ) -> List[Document]:
        """Retorna todos os documentos com filtros opcionais."""
        cursor = self._conn.cursor()

        query = "SELECT * FROM documents WHERE 1=1"
        params = []

        if search:
            query += """ AND (
                qr_code LIKE ? OR
                CAST(shelf AS TEXT) LIKE ? OR
                CAST(box AS TEXT) LIKE ? OR
                CAST(rack AS TEXT) LIKE ? OR
                classification LIKE ?
            )"""
            search_param = f"%{search}%"
            params.extend([search_param] * 5)

        if date_start:
            query += " AND created_at >= ?"
            params.append(date_start.strftime("%Y-%m-%d 00:00:00"))

        if date_end:
            query += " AND created_at <= ?"
            params.append(date_end.strftime("%Y-%m-%d 23:59:59"))

        # Validar coluna de ordenação
        valid_columns = ["id", "qr_code", "shelf", "box", "rack", "classification", "created_at"]
        if order_by not in valid_columns:
            order_by = "id"

        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        query += f" ORDER BY {order_by} {order_dir}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [Document.from_row(row) for row in rows]

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        """Retorna um documento pelo ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        if row:
            return Document.from_row(row)
        return None

    def get_by_qr_code(self, qr_code: str) -> Optional[Document]:
        """Retorna um documento pelo código QR."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE qr_code = ?", (qr_code,))
        row = cursor.fetchone()

        if row:
            return Document.from_row(row)
        return None

    def update(self, document: Document) -> Tuple[bool, str]:
        """
        Atualiza um documento existente.
        Retorna (sucesso, mensagem).
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                UPDATE documents
                SET qr_code = ?, shelf = ?, box = ?, rack = ?, classification = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    document.qr_code,
                    document.shelf,
                    document.box,
                    document.rack,
                    document.classification,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    document.id,
                ),
            )
            self._conn.commit()

            if cursor.rowcount == 0:
                return False, "Documento não encontrado!"
            return True, "Documento atualizado com sucesso!"
        except Exception as e:
            self._logger.error(f"Erro ao atualizar documento (ID: {document.id}): {e}")
            if "UNIQUE constraint failed" in str(e):
                return False, "Código QR já existe em outro documento!"
            return False, f"Erro ao atualizar: {str(e)}"

    def delete(self, doc_id: int) -> Tuple[bool, str]:
        """
        Exclui um documento.
        Retorna (sucesso, mensagem).
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            self._conn.commit()

            if cursor.rowcount == 0:
                return False, "Documento não encontrado!"
            return True, "Documento excluído com sucesso!"
        except Exception as e:
            self._logger.error(f"Erro ao excluir documento (ID: {doc_id}): {e}")
            return False, f"Erro ao excluir: {str(e)}"

    def count(self) -> int:
        """Retorna o total de documentos."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        result = cursor.fetchone()
        return result["total"] if result else 0

    def exists_qr_code(self, qr_code: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica se um código QR já existe."""
        cursor = self._conn.cursor()

        if exclude_id:
            cursor.execute(
                "SELECT 1 FROM documents WHERE qr_code = ? AND id != ?",
                (qr_code, exclude_id),
            )
        else:
            cursor.execute("SELECT 1 FROM documents WHERE qr_code = ?", (qr_code,))

        return cursor.fetchone() is not None
