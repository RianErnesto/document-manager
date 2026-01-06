"""
Modelo de dados para Documento.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Document:
    """Classe que representa um documento."""

    id: Optional[int] = None
    qr_code: str = ""
    shelf: int = 0  # Prateleira
    box: int = 0  # Caixa
    rack: int = 0  # Estante
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Converte o documento para dicionário."""
        return {
            "id": self.id,
            "qr_code": self.qr_code,
            "shelf": self.shelf,
            "box": self.box,
            "rack": self.rack,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M") if self.created_at else "",
            "updated_at": self.updated_at.strftime("%d/%m/%Y %H:%M") if self.updated_at else "",
        }

    @classmethod
    def from_row(cls, row) -> "Document":
        """Cria um Document a partir de uma linha do banco."""
        created_at = None
        updated_at = None

        if row["created_at"]:
            try:
                created_at = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                created_at = datetime.strptime(row["created_at"][:19], "%Y-%m-%d %H:%M:%S")

        if row["updated_at"]:
            try:
                updated_at = datetime.strptime(row["updated_at"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                updated_at = datetime.strptime(row["updated_at"][:19], "%Y-%m-%d %H:%M:%S")

        return cls(
            id=row["id"],
            qr_code=row["qr_code"],
            shelf=row["shelf"],
            box=row["box"],
            rack=row["rack"],
            created_at=created_at,
            updated_at=updated_at,
        )
