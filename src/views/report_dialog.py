"""
Dialog para geração de relatórios.
"""
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime, date
from typing import List, Optional
import os
import subprocess
import platform

from ..config import COLORS, FONTS, DIMENSIONS, APP_NAME
from ..components.button import StyledButton
from ..components.date_picker import DatePicker
from ..components.message_box import show_message
from ..models.document import Document
from ..database.document_repository import DocumentRepository
from ..services.report_service import ReportService


class ReportDialog(ctk.CTkToplevel):
    """Dialog para geração de relatórios."""

    def __init__(self, master):
        """Inicializa o dialog de relatórios."""
        super().__init__(master)

        self.title("Gerar Relatório")
        self.geometry("450x350")
        self.resizable(False, False)

        # Centraliza na tela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 350) // 2
        self.geometry(f"+{x}+{y}")

        # Modal
        self.transient(master)
        self.grab_set()

        # Configuração de fundo
        self.configure(fg_color=COLORS["surface"])

        self._repository = DocumentRepository()
        self._create_widgets()

        self.focus()

    def _create_widgets(self):
        """Cria os widgets do dialog."""
        # Container principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        title = ctk.CTkLabel(
            main_frame,
            text="Gerar Relatório de Documentos",
            font=FONTS["subtitle"],
            text_color=COLORS["text"],
        )
        title.pack(pady=(0, 20))

        # Instrução
        instruction = ctk.CTkLabel(
            main_frame,
            text="Selecione o período (opcional) e o formato do relatório.",
            font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        )
        instruction.pack(pady=(0, 20))

        # Frame de datas
        dates_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=(0, 20))

        # Data inicial
        start_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        start_frame.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self._date_start = DatePicker(start_frame, label="Data Inicial")
        self._date_start.pack()

        # Data final
        end_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        end_frame.pack(side="left", expand=True, fill="x", padx=(10, 0))

        self._date_end = DatePicker(end_frame, label="Data Final")
        self._date_end.pack()

        # Info
        info_label = ctk.CTkLabel(
            main_frame,
            text="Deixe as datas em branco para exportar todos os documentos.",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        info_label.pack(pady=(0, 20))

        # Botões de formato
        format_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, 20))

        format_label = ctk.CTkLabel(
            format_frame,
            text="Formato:",
            font=FONTS["body_bold"],
            text_color=COLORS["text"],
        )
        format_label.pack(side="left", padx=(0, 15))

        self._format_var = ctk.StringVar(value="pdf")

        pdf_radio = ctk.CTkRadioButton(
            format_frame,
            text="PDF",
            variable=self._format_var,
            value="pdf",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        )
        pdf_radio.pack(side="left", padx=(0, 20))

        xlsx_radio = ctk.CTkRadioButton(
            format_frame,
            text="Excel (XLSX)",
            variable=self._format_var,
            value="xlsx",
            font=FONTS["body"],
            text_color=COLORS["text"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
        )
        xlsx_radio.pack(side="left")

        # Botões de ação
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = StyledButton(
            button_frame,
            text="Cancelar",
            variant="secondary",
            command=self.destroy,
            width=100,
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        generate_btn = StyledButton(
            button_frame,
            text="Gerar Relatório",
            variant="primary",
            command=self._generate_report,
            width=140,
        )
        generate_btn.pack(side="right")

    def _generate_report(self):
        """Gera o relatório."""
        # Obtém datas
        date_start = self._date_start.get_datetime()
        date_end = self._date_end.get_datetime()

        # Obtém formato
        format_type = self._format_var.get()

        # Define extensão e tipo de arquivo
        if format_type == "pdf":
            default_ext = ".pdf"
            file_types = [("PDF Files", "*.pdf")]
        else:
            default_ext = ".xlsx"
            file_types = [("Excel Files", "*.xlsx")]

        # Nome padrão do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"relatorio_documentos_{timestamp}{default_ext}"

        # Diálogo para salvar
        file_path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=file_types,
            initialfile=default_name,
            title="Salvar Relatório",
        )

        if not file_path:
            return

        # Busca documentos
        documents = self._repository.get_all(
            date_start=date_start,
            date_end=date_end,
        )

        if not documents:
            show_message(
                self,
                "Nenhum documento encontrado no período selecionado.",
                variant="warning",
            )
            return

        # Gera relatório
        if format_type == "pdf":
            success, message = ReportService.generate_pdf(
                documents, file_path, date_start, date_end
            )
        else:
            success, message = ReportService.generate_xlsx(
                documents, file_path, date_start, date_end
            )

        if success:
            show_message(self, message, variant="success")
            # Abre o arquivo
            self._open_file(file_path)
            self.destroy()
        else:
            show_message(self, message, variant="error")

    def _open_file(self, file_path: str):
        """Abre o arquivo gerado."""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception:
            pass  # Ignora erro ao abrir arquivo
