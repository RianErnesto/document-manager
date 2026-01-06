"""
Funções de validação para campos da aplicação.
"""
from typing import Tuple


class Validators:
    """Classe com métodos de validação."""

    @staticmethod
    def is_required(value: str) -> Tuple[bool, str]:
        """Valida se o campo foi preenchido."""
        if not value or not value.strip():
            return False, "Este campo é obrigatório"
        return True, ""

    @staticmethod
    def is_number(value: str) -> Tuple[bool, str]:
        """Valida se o valor é um número inteiro positivo."""
        if not value or not value.strip():
            return False, "Este campo é obrigatório"

        try:
            num = int(value)
            if num <= 0:
                return False, "O valor deve ser maior que zero"
            return True, ""
        except ValueError:
            return False, "Apenas números são permitidos"

    @staticmethod
    def is_positive_number(value: str) -> Tuple[bool, str]:
        """Valida se o valor é um número positivo."""
        if not value or not value.strip():
            return True, ""  # Campo opcional

        try:
            num = int(value)
            if num < 0:
                return False, "O valor não pode ser negativo"
            return True, ""
        except ValueError:
            return False, "Apenas números são permitidos"

    @staticmethod
    def validate_qr_code(value: str) -> Tuple[bool, str]:
        """Valida o código QR."""
        if not value or not value.strip():
            return False, "Código QR é obrigatório"

        if len(value.strip()) < 1:
            return False, "Código QR muito curto"

        return True, ""
