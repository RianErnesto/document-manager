"""
Tela principal da aplicação.
"""
import customtkinter as ctk
from typing import Optional

from ..config import COLORS, FONTS, DIMENSIONS, TABLE_COLUMNS, APP_NAME
from ..components.button import StyledButton
from ..components.input import StyledInput
from ..components.lockable_input import LockableInput
from ..components.table import DataTable
from ..components.message_box import show_message, show_confirm
from ..services.audit_service import AuditLogger
from ..database.document_repository import DocumentRepository
from ..models.document import Document
from .report_dialog import ReportDialog


class MainView(ctk.CTkFrame):
    """Tela principal com formulário e tabela de documentos."""

    def __init__(self, master, **kwargs):
        """Inicializa a tela principal."""
        super().__init__(master, fg_color=COLORS["background"], **kwargs)

        self._repository = DocumentRepository()
        self._logger = AuditLogger()
        self._editing_id: Optional[int] = None

        self._create_widgets()
        self._load_data()

    def _create_widgets(self):
        """Cria os widgets da tela."""
        # Container principal com scroll
        self._main_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
        )
        self._main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Cabeçalho
        self._create_header()

        # Card de cadastro
        self._create_form_card()

        # Card da tabela
        self._create_table_card()

    def _create_header(self):
        """Cria o cabeçalho."""
        header_frame = ctk.CTkFrame(self._main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # Título
        title = ctk.CTkLabel(
            header_frame,
            text=APP_NAME.upper(),
            font=FONTS["title"],
            text_color=COLORS["primary"],
        )
        title.pack(side="left")

        # Botão de relatórios
        report_btn = StyledButton(
            header_frame,
            text="Relatórios",
            variant="outline",
            command=self._open_reports,
            width=120,
        )
        report_btn.pack(side="right")

    def _create_form_card(self):
        """Cria o card do formulário de cadastro."""
        # Card
        form_card = ctk.CTkFrame(
            self._main_container,
            fg_color=COLORS["surface"],
            corner_radius=DIMENSIONS["border_radius"],
        )
        form_card.pack(fill="x", pady=(0, 20))

        # Padding interno
        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=DIMENSIONS["card_padding"], pady=DIMENSIONS["card_padding"])

        # Título do card
        form_title = ctk.CTkLabel(
            form_inner,
            text="CADASTRO DE DOCUMENTO",
            font=FONTS["heading"],
            text_color=COLORS["text"],
        )
        form_title.pack(anchor="w", pady=(0, 15))

        # Linha 1: Código QR
        row1 = ctk.CTkFrame(form_inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))

        self._qr_input = StyledInput(
            row1,
            label="Código QR",
            placeholder="Digite o código QR",
            required=True,
            width=400,
        )
        self._qr_input.pack(side="left", padx=(0, 20))

        self._process_input = LockableInput(
            row1,
            label="Nº do Processo",
            placeholder="0000/00000",
            required=True,
            validation_type="process",
            width=140,
        )
        self._process_input.pack(side="left")

        # Linha 2: Estante, Prateleira, Caixa (com travas)
        row2 = ctk.CTkFrame(form_inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 15))

        self._rack_input = LockableInput(
            row2,
            label="Estante",
            placeholder="Nº",
            required=True,
            validation_type="number",
            width=80,
        )
        self._rack_input.pack(side="left", padx=(0, 20))

        self._shelf_input = LockableInput(
            row2,
            label="Prateleira",
            placeholder="Nº",
            required=True,
            validation_type="number",
            width=80,
        )
        self._shelf_input.pack(side="left", padx=(0, 20))

        self._box_input = LockableInput(
            row2,
            label="Caixa",
            placeholder="Nº",
            required=True,
            validation_type="number",
            width=80,
        )
        self._box_input.pack(side="left", padx=(0, 20))

        self._classification_input = LockableInput(
            row2,
            label="Classificação",
            placeholder="Ex: A1, Fiscal...",
            required=True,
            validation_type="text",
            width=120,
        )
        self._classification_input.pack(side="left")

        # Dica sobre trava
        lock_hint = ctk.CTkLabel(
            form_inner,
            text="Clique no cadeado para travar/destravar o campo. Campos travados mantêm o valor após o cadastro.",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        lock_hint.pack(anchor="w", pady=(0, 15))

        # Botões
        button_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        button_row.pack(fill="x")

        self._save_btn = StyledButton(
            button_row,
            text="Cadastrar",
            variant="primary",
            command=self._save_document,
            width=120,
        )
        self._save_btn.pack(side="right", padx=(10, 0))

        self._clear_btn = StyledButton(
            button_row,
            text="Limpar Campos",
            variant="secondary",
            command=self._clear_form,
            width=120,
        )
        self._clear_btn.pack(side="right")

        self._cancel_edit_btn = StyledButton(
            button_row,
            text="Cancelar Edição",
            variant="danger",
            command=self._cancel_edit,
            width=140,
        )
        self._cancel_edit_btn.pack(side="right", padx=(0, 10))
        self._cancel_edit_btn.pack_forget()  # Oculto inicialmente

    def _create_table_card(self):
        """Cria o card da tabela."""
        # Card
        table_card = ctk.CTkFrame(
            self._main_container,
            fg_color=COLORS["surface"],
            corner_radius=DIMENSIONS["border_radius"],
        )
        table_card.pack(fill="both", expand=True)

        # Tabela
        self._table = DataTable(
            table_card,
            columns=TABLE_COLUMNS,
            on_select=self._on_row_select,
            on_deselect=self._on_row_deselect,
            on_double_click=self._on_row_double_click,
        )
        self._table.pack(fill="both", expand=True)

        # Botões de ação no cabeçalho da tabela
        self._edit_btn = StyledButton(
            self._table.action_frame,
            text="Editar",
            variant="primary",
            command=self._edit_selected,
            width=80,
        )
        # Inicialmente ocultos
        self._edit_btn.pack_forget()

        self._delete_btn = StyledButton(
            self._table.action_frame,
            text="Excluir",
            variant="danger",
            command=self._delete_selected,
            width=80,
        )
        self._delete_btn.pack_forget()

    def _load_data(self):
        """Carrega os dados na tabela."""
        sort_col, sort_dir = self._table.get_sort_info()
        documents = self._repository.get_all(order_by=sort_col, order_dir=sort_dir)
        data = [doc.to_dict() for doc in documents]
        self._table.set_data(data)

    def _save_document(self):
        """Salva o documento (criar ou atualizar)."""
        # Valida campos
        valid = True

        if not self._qr_input.validate():
            valid = False
        if not self._rack_input.validate():
            valid = False
        if not self._shelf_input.validate():
            valid = False
        if not self._box_input.validate():
            valid = False
        if not self._classification_input.validate():
            valid = False
        if not self._process_input.validate():
            valid = False

        if not valid:
            return

        # Obtém valores
        qr_code = self._qr_input.get().strip()
        rack = int(self._rack_input.get())
        shelf = int(self._shelf_input.get())
        box = int(self._box_input.get())
        classification = self._classification_input.get().strip()
        process = self._process_input.get().strip()

        # Verifica QR duplicado
        if self._repository.exists_qr_code(qr_code, exclude_id=self._editing_id):
            self._qr_input.set_error("Código QR já cadastrado!")
            return

        # Cria ou atualiza
        if self._editing_id:
            # Atualização
            document = Document(
                id=self._editing_id,
                qr_code=qr_code,
                rack=rack,
                shelf=shelf,
                box=box,
                classification=classification,
                process=process,
            )
            success, message = self._repository.update(document)

            if success:
                self._logger.info(f"Documento atualizado — ID: {self._editing_id}, QR: {qr_code}")
                show_message(self.winfo_toplevel(), message, variant="success")
                self._cancel_edit()
                self._load_data()
            else:
                show_message(self.winfo_toplevel(), message, variant="error")
        else:
            # Criação
            document = Document(
                qr_code=qr_code,
                rack=rack,
                shelf=shelf,
                box=box,
                classification=classification,
                process=process,
            )
            success, message, new_id = self._repository.create(document)

            if success:
                self._logger.info(f"Documento criado — ID: {new_id}, QR: {qr_code}")
                show_message(self.winfo_toplevel(), message, variant="success")
                self._clear_form(respect_locks=True)
                self._load_data()
                # Coloca foco no QR Code para próximo cadastro
                self._qr_input.focus()
            else:
                show_message(self.winfo_toplevel(), message, variant="error")

    def _clear_form(self, respect_locks: bool = False):
        """
        Limpa o formulário.

        Args:
            respect_locks: Se True, não limpa campos travados
        """
        self._qr_input.clear()

        if respect_locks:
            self._rack_input.clear(force=False)
            self._shelf_input.clear(force=False)
            self._box_input.clear(force=False)
            self._classification_input.clear(force=False)
            self._process_input.clear(force=False)
        else:
            self._rack_input.clear(force=True)
            self._shelf_input.clear(force=True)
            self._box_input.clear(force=True)
            self._classification_input.clear(force=True)
            self._process_input.clear(force=True)

        self._qr_input.focus()

    def _cancel_edit(self):
        """Cancela a edição."""
        self._editing_id = None
        self._save_btn.configure(text="Cadastrar")
        self._cancel_edit_btn.pack_forget()
        self._clear_form()
        self._table.clear_selection()

    def _on_row_select(self, row_data: dict):
        """Callback ao selecionar uma linha."""
        self._table.action_frame.pack(side="left", padx=(15, 0))
        self._edit_btn.pack(side="left", padx=(0, 8))
        self._delete_btn.pack(side="left")

    def _on_row_deselect(self):
        """Callback ao deselecionar."""
        self._edit_btn.pack_forget()
        self._delete_btn.pack_forget()
        self._table.action_frame.pack_forget()

    def _on_row_double_click(self, row_data: dict):
        """Callback ao dar duplo clique."""
        self._start_edit(row_data)

    def _edit_selected(self):
        """Edita o documento selecionado."""
        selected = self._table.get_selected()
        if not selected:
            show_message(
                self.winfo_toplevel(),
                "Selecione um documento para editar.",
                variant="warning",
            )
            return
        self._start_edit(selected)

    def _start_edit(self, row_data: dict):
        """Inicia a edição de um documento."""
        self._editing_id = int(row_data["id"])

        self._qr_input.set(str(row_data["qr_code"]))
        self._rack_input.set(str(row_data["rack"]))
        self._shelf_input.set(str(row_data["shelf"]))
        self._box_input.set(str(row_data["box"]))
        self._classification_input.set(str(row_data.get("classification", "")))
        self._process_input.set(str(row_data.get("process", "")))

        self._save_btn.configure(text="Atualizar")
        self._cancel_edit_btn.pack(side="right", padx=(0, 10))

        self._qr_input.focus()

    def _delete_selected(self):
        """Exclui o documento selecionado."""
        selected = self._table.get_selected()
        if not selected:
            show_message(
                self.winfo_toplevel(),
                "Selecione um documento para excluir.",
                variant="warning",
            )
            return

        # Confirmação
        confirmed = show_confirm(
            self.winfo_toplevel(),
            f"Deseja realmente excluir o documento '{selected['qr_code']}'?",
            title="Confirmar Exclusão",
        )

        if confirmed:
            success, message = self._repository.delete(int(selected["id"]))

            if success:
                self._logger.info(f"Documento excluído — ID: {selected['id']}, QR: {selected['qr_code']}")
                show_message(self.winfo_toplevel(), message, variant="success")
                self._load_data()

                # Se estava editando este documento, cancela edição
                if self._editing_id == int(selected["id"]):
                    self._cancel_edit()
            else:
                show_message(self.winfo_toplevel(), message, variant="error")

    def _open_reports(self):
        """Abre o dialog de relatórios."""
        ReportDialog(self.winfo_toplevel())
