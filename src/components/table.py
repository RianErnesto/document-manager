"""
Componente de tabela de dados com ordenação e filtro.
"""
import customtkinter as ctk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Any

from ..config import COLORS, FONTS, DIMENSIONS, TABLE


class DataTable(ctk.CTkFrame):
    """Tabela de dados com ordenação e filtro."""

    def __init__(
        self,
        master,
        columns: List[Dict[str, Any]],
        on_select: Optional[Callable[[Dict], None]] = None,
        on_deselect: Optional[Callable[[], None]] = None,
        on_double_click: Optional[Callable[[Dict], None]] = None,
        **kwargs
    ):
        """
        Inicializa a tabela.

        Args:
            master: Widget pai
            columns: Lista de colunas [{"key": str, "label": str, "width": int}]
            on_select: Callback ao selecionar uma linha
            on_double_click: Callback ao dar duplo clique
        """
        super().__init__(master, fg_color=COLORS["surface"], **kwargs)

        self._columns = columns
        self._on_select = on_select
        self._on_deselect = on_deselect
        self._on_double_click = on_double_click
        self._data: List[Dict] = []
        self._filtered_data: List[Dict] = []
        self._sort_column = "id"
        self._sort_direction = "DESC"
        self._selected_item = None
        self._pending_click = None

        self._create_widgets()

    def _create_widgets(self):
        """Cria os widgets da tabela."""
        # Frame do cabeçalho com busca
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Título
        title_label = ctk.CTkLabel(
            header_frame,
            text="DOCUMENTOS CADASTRADOS",
            font=FONTS["heading"],
            text_color=COLORS["text"],
        )
        title_label.pack(side="left")

        # Frame para botões de ação (exposto para uso externo, oculto inicialmente)
        self.action_frame = ctk.CTkFrame(header_frame, fg_color="transparent")

        # Campo de busca geral
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(side="right")

        search_label = ctk.CTkLabel(
            search_frame,
            text="Buscar:",
            font=FONTS["body_bold"],
            text_color=COLORS["text"],
        )
        search_label.pack(side="left", padx=(0, 8))

        self._search_entry = ctk.CTkEntry(
            search_frame,
            width=280,
            height=36,
            font=FONTS["body"],
            fg_color=COLORS["surface"],
            border_color=COLORS["primary"],
            border_width=2,
            corner_radius=DIMENSIONS["border_radius"],
            placeholder_text="Código QR, estante, classificação...",
            placeholder_text_color=COLORS["text_secondary"],
        )
        self._search_entry.pack(side="left")
        self._search_entry.bind("<KeyRelease>", self._on_search)

        # Campo de busca específico por caixa
        box_search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        box_search_frame.pack(side="right", padx=(0, 12))

        box_label = ctk.CTkLabel(
            box_search_frame,
            text="Caixa:",
            font=FONTS["body_bold"],
            text_color=COLORS["text"],
        )
        box_label.pack(side="left", padx=(0, 8))

        self._box_search_entry = ctk.CTkEntry(
            box_search_frame,
            width=100,
            height=36,
            font=FONTS["body"],
            fg_color=COLORS["surface"],
            border_color=COLORS["primary"],
            border_width=2,
            corner_radius=DIMENSIONS["border_radius"],
            placeholder_text="Nº",
            placeholder_text_color=COLORS["text_secondary"],
        )
        self._box_search_entry.pack(side="left")
        self._box_search_entry.bind("<KeyRelease>", self._on_search)

        # Frame da tabela
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Estilo do Treeview
        style = ttk.Style()
        style.theme_use("clam")

        # Configuração do header
        style.configure(
            "Custom.Treeview.Heading",
            background=COLORS["primary"],
            foreground=COLORS["text_light"],
            font=FONTS["table_header"],
            relief="flat",
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", COLORS["primary_hover"])],
        )

        # Configuração das linhas
        style.configure(
            "Custom.Treeview",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["surface"],
            font=FONTS["table_body"],
            rowheight=TABLE["row_height"],
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", COLORS["primary"])],
            foreground=[("selected", COLORS["text_light"])],
        )

        # Treeview
        column_ids = [col["key"] for col in self._columns]
        self._tree = ttk.Treeview(
            table_frame,
            columns=column_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
        )

        # Configurar colunas
        for col in self._columns:
            self._tree.heading(
                col["key"],
                text=col["label"],
                command=lambda c=col["key"]: self._sort_by(c),
            )
            self._tree.column(
                col["key"],
                width=col.get("width", 100),
                minwidth=50,
                anchor="center",
            )

        # Scrollbars
        y_scroll = ctk.CTkScrollbar(table_frame, command=self._tree.yview)
        y_scroll.pack(side="right", fill="y")

        x_scroll = ctk.CTkScrollbar(table_frame, orientation="horizontal", command=self._tree.xview)
        x_scroll.pack(side="bottom", fill="x")

        self._tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self._tree.pack(fill="both", expand=True)

        # Binds
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self._tree.bind("<Button-1>", self._on_click)
        self._tree.bind("<Double-1>", self._on_row_double_click)

        # Rodapé com contagem
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=10, pady=(5, 10))

        self._selection_label = ctk.CTkLabel(
            footer_frame,
            text="",
            font=FONTS["body_bold"],
            text_color=COLORS["primary"],
        )
        self._selection_label.pack(side="left")

        self._count_label = ctk.CTkLabel(
            footer_frame,
            text="0 documento(s)",
            font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        self._count_label.pack(side="right")

    def _on_search(self, *args):
        """Filtra os dados pelos dois campos: busca geral + caixa."""
        search_text = self._search_entry.get().lower()
        box_text = self._box_search_entry.get().lower().strip()

        def matches(row):
            if search_text and not any(
                search_text in str(row.get(col["key"], "")).lower()
                for col in self._columns
            ):
                return False
            if box_text and box_text not in str(row.get("box", "")).lower():
                return False
            return True

        self._filtered_data = [row for row in self._data if matches(row)]
        self._refresh_display()

    def _sort_by(self, column: str):
        """Ordena os dados pela coluna."""
        if self._sort_column == column:
            self._sort_direction = "ASC" if self._sort_direction == "DESC" else "DESC"
        else:
            self._sort_column = column
            self._sort_direction = "ASC"

        self._apply_sort()
        self._refresh_display()
        self._update_headers()

    def _apply_sort(self):
        """Aplica a ordenação aos dados filtrados."""
        reverse = self._sort_direction == "DESC"

        def sort_key(row):
            value = row.get(self._sort_column, "")
            if isinstance(value, (int, float)):
                return value
            return str(value).lower()

        self._filtered_data.sort(key=sort_key, reverse=reverse)

    def _update_headers(self):
        """Atualiza os headers com indicador de ordenação."""
        for col in self._columns:
            text = col["label"]
            if col["key"] == self._sort_column:
                arrow = " ▼" if self._sort_direction == "DESC" else " ▲"
                text += arrow
            self._tree.heading(col["key"], text=text)

    def _refresh_display(self):
        """Atualiza a exibição da tabela."""
        # Limpa a tabela
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Adiciona os dados filtrados
        for row in self._filtered_data:
            values = [row.get(col["key"], "") for col in self._columns]
            self._tree.insert("", "end", values=values, tags=(str(row.get("id", "")),))

        # Atualiza contagem
        total = len(self._data)
        filtered = len(self._filtered_data)
        if total == filtered:
            text = f"{total} documento(s)"
        else:
            text = f"Mostrando {filtered} de {total} documento(s)"
        self._count_label.configure(text=text)

    def _on_click(self, event):
        """Detecta clique em linha já selecionada para deselecionar."""
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return

        current_selection = self._tree.selection()
        if current_selection and current_selection[0] == row_id:
            # Clique na linha já selecionada — agenda deselect com delay
            # para dar tempo de cancelar se for double-click
            if self._pending_click:
                self._tree.after_cancel(self._pending_click)
            self._pending_click = self._tree.after(300, self._deselect_row)

    def _deselect_row(self):
        """Executa o deselect agendado."""
        self._pending_click = None
        self.clear_selection()

    def _on_row_select(self, event):
        """Callback ao selecionar uma linha."""
        selected = self._tree.selection()
        if selected:
            item = self._tree.item(selected[0])
            values = item["values"]

            # Reconstrói o dicionário
            row_data = {}
            for i, col in enumerate(self._columns):
                row_data[col["key"]] = values[i] if i < len(values) else ""

            self._selected_item = row_data
            self._selection_label.configure(
                text=f"Documento selecionado:  ID {row_data.get('id', '')}"
            )

            if self._on_select:
                self._on_select(row_data)

    def _on_row_double_click(self, event):
        """Callback ao dar duplo clique."""
        # Cancela deselect pendente — o double-click tem prioridade
        if self._pending_click:
            self._tree.after_cancel(self._pending_click)
            self._pending_click = None

        if self._selected_item and self._on_double_click:
            self._on_double_click(self._selected_item)

    def set_data(self, data: List[Dict]):
        """Define os dados da tabela."""
        self._data = data
        self._filtered_data = data.copy()
        self._apply_sort()
        self._refresh_display()
        self._update_headers()

    def get_selected(self) -> Optional[Dict]:
        """Retorna o item selecionado."""
        return self._selected_item

    def clear_selection(self):
        """Limpa a seleção."""
        for item in self._tree.selection():
            self._tree.selection_remove(item)
        self._selected_item = None
        self._selection_label.configure(text="")
        if self._on_deselect:
            self._on_deselect()

    def refresh(self):
        """Atualiza a tabela."""
        self._refresh_display()

    def get_sort_info(self) -> tuple:
        """Retorna informações de ordenação atuais."""
        return self._sort_column, self._sort_direction
