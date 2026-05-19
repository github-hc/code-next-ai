import flet as ft
import threading
from pathlib import Path
from main import build_index, query_repo

# ═══════════════════════════════════════════════════════════
#  DESIGN TOKENS  — change here, applies everywhere
# ═══════════════════════════════════════════════════════════

# Typography
FS_APP_TITLE   = 16   # App name in sidebar
FS_SECTION     = 11   # Section header labels ("Explorer", "Workspace")
FS_BODY        = 13   # Regular text, chat messages
FS_CAPTION     = 11   # Subtitles, meta info
FS_CODE        = 12   # File names, badges

# Spacing / Padding
PAD_PANE       = ft.Padding(left=16, right=16, top=10, bottom=10)
PAD_SIDEBAR    = ft.Padding(left=14, right=14, top=14, bottom=14)
PAD_BUBBLE     = ft.Padding(left=14, right=14, top=10, bottom=10)
PAD_ROW        = ft.Padding(left=10, right=10, top=6, bottom=6)
PAD_BADGE      = ft.Padding(left=6, right=6, top=2, bottom=2)
PAD_FILE_ITEM  = ft.Padding(left=8, right=8, top=5, bottom=5)
PAD_EDITOR     = 20

# Border radii
BR_BUBBLE      = 10
BR_BADGE       = 4
BR_CONTAINER   = 6

# Icon sizes
ICON_SM        = 14
ICON_MD        = 16

# Control dimensions
SIDEBAR_WIDTH  = 260
CHAT_WIDTH     = 460
LIST_SPACING   = 10

# ═══════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "Code Next AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.window_width = 1400
    page.window_height = 860

    current_open_file = {"path": None}

    # ─────────────────────────────────────────────
    # MIDDLE PANE: Code Editor
    # ─────────────────────────────────────────────
    editor_tab_label = ft.Text(
        "No file open",
        size=FS_CODE,
        color=ft.Colors.ON_SURFACE_VARIANT,
        italic=True,
    )

    code_markdown = ft.Markdown(
        "",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
        code_theme="atom-one-dark",
        expand=True,
    )

    editor_placeholder = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CODE, size=48, color=ft.Colors.OUTLINE),
                ft.Text(
                    "Select a file from the explorer",
                    color=ft.Colors.OUTLINE,
                    size=FS_BODY,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        expand=True,
        alignment=ft.Alignment(0, 0),
    )

    editor_body = ft.Stack(
        [
            editor_placeholder,
            ft.Container(content=code_markdown, expand=True, visible=False, padding=PAD_EDITOR),
        ],
        expand=True,
    )

    def open_file_in_editor(file_path_str: str):
        try:
            path = Path(file_path_str)
            content = path.read_text(encoding="utf-8")
            ext_map = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".tsx": "tsx", ".jsx": "jsx", ".json": "json",
                ".md": "markdown", ".html": "html", ".css": "css",
                ".sh": "bash", ".yaml": "yaml", ".yml": "yaml",
            }
            lang = ext_map.get(path.suffix.lower(), "")
            code_markdown.value = f"```{lang}\n{content}\n```"
            editor_tab_label.value = path.name
            editor_tab_label.italic = False
            editor_tab_label.color = ft.Colors.ON_SURFACE
            editor_body.controls[0].visible = False
            editor_body.controls[1].visible = True
            current_open_file["path"] = file_path_str
            page.update()
        except Exception as ex:
            editor_tab_label.value = f"Error: {ex}"
            page.update()

    def _pane_header(icon, label: str):
        """Reusable tab-bar style header row."""
        return ft.Container(
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=PAD_PANE,
            content=ft.Row(
                [
                    ft.Icon(icon, size=ICON_SM, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(label, size=FS_CAPTION, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            ),
        )

    editor_pane = ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            [
                _pane_header(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, "Editor"),
                ft.Container(content=ft.Row([editor_tab_label], spacing=6), padding=ft.Padding(left=16, right=16, top=6, bottom=6)),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                ft.ListView(controls=[editor_body], expand=True, auto_scroll=False),
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ─────────────────────────────────────────────
    # RIGHT PANE: Chat
    # ─────────────────────────────────────────────
    chat_list = ft.ListView(expand=True, spacing=LIST_SPACING, auto_scroll=True, padding=16)

    def add_user_message(text: str):
        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, selectable=True, size=FS_BODY),
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        padding=PAD_BUBBLE,
                        border_radius=BR_BUBBLE,
                        width=360,
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def add_thinking_bubble():
        bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ProgressRing(width=ICON_SM, height=ICON_MD, stroke_width=2),
                            ft.Text("Thinking…", size=FS_BODY, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=PAD_BUBBLE,
                    border_radius=BR_BUBBLE,
                )
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        chat_list.controls.append(bubble)
        page.update()
        return bubble

    def add_agent_answer(answer_text: str):
        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Markdown(
                            answer_text,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            code_theme="atom-one-dark",
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=PAD_BUBBLE,
                        border_radius=BR_BUBBLE,
                        expand=True,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def add_references(results, current_repo_path: str):
        if not results:
            return

        tiles = []
        for i, res in enumerate(results, 1):
            try:
                rel_path = Path(res["file_path"]).relative_to(Path(current_repo_path).resolve())
            except ValueError:
                rel_path = res["file_path"]

            score = res.get("score", 0)
            score_color = (
                ft.Colors.GREEN_400 if score > 0.7
                else ft.Colors.ORANGE_400 if score > 0.4
                else ft.Colors.RED_400
            )

            meta_row = ft.Row(
                [
                    ft.Container(
                        content=ft.Text(f"{score:.3f}", size=FS_CAPTION, color=ft.Colors.ON_SURFACE),
                        bgcolor=score_color,
                        border_radius=BR_BADGE,
                        padding=PAD_BADGE,
                    ),
                    ft.Text(
                        f"{rel_path}",
                        size=FS_CAPTION,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        expand=True,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(f"L{res['start_line']}–{res['end_line']}", size=FS_CAPTION, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=6,
            )

            tile = ft.ExpansionTile(
                title=ft.Text(f"[{i}]  {res['symbol_name']}", size=FS_CODE, weight=ft.FontWeight.W_600),
                subtitle=meta_row,
                controls=[
                    ft.Container(
                        content=ft.Markdown(
                            f"```python\n{res['code']}\n```",
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            code_theme="atom-one-dark",
                        ),
                        padding=ft.Padding(left=8, right=8, top=4, bottom=8),
                    )
                ],
            )
            tiles.append(tile)

        context_panel = ft.ExpansionTile(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.SEARCH, size=ICON_SM, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(
                        f"Context passed to LLM  ({len(results)} chunks)",
                        size=FS_CODE,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=6,
            ),
            controls=[
                ft.Container(
                    content=ft.Column(tiles, spacing=4),
                    padding=ft.Padding(left=4, right=4, top=4, bottom=4),
                )
            ],
        )

        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=context_panel,
                        expand=True,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        border_radius=BR_CONTAINER,
                        padding=4,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def add_simple_message(text: str):
        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, selectable=True, size=FS_BODY),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=PAD_BUBBLE,
                        border_radius=BR_BUBBLE,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def handle_query(e):
        current_repo_path = repo_path_input.value
        if not current_repo_path:
            add_simple_message("Please enter a repository path and index it first.")
            return

        query = query_input.value.strip()
        if not query or query_input.disabled:
            return

        # ── Immediately update UI (on the event thread) ──
        query_input.disabled = True
        send_btn.disabled = True
        query_input.value = ""
        page.update()                    # flush: clears the input box

        add_user_message(query)          # shows user bubble right away
        thinking_bubble = add_thinking_bubble()  # shows spinner right away

        selected_model = model_dropdown.value

        # ── Heavy work runs off the UI thread ──
        def run_query():
            try:
                token_stream, results = query_repo(current_repo_path, query, model_name=selected_model)
                
                # Remove the thinking bubble as soon as retrieval is complete / generation starts
                chat_list.controls.remove(thinking_bubble)
                
                # Create a placeholder bubble for the agent response
                md_control = ft.Markdown(
                    "",
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    code_theme="atom-one-dark",
                )
                agent_bubble = ft.Row(
                    [
                        ft.Container(
                            content=md_control,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                            padding=PAD_BUBBLE,
                            border_radius=BR_BUBBLE,
                            expand=True,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
                chat_list.controls.append(agent_bubble)
                page.update()

                # Stream tokens to the UI
                full_text = ""
                for token in token_stream:
                    full_text += token
                    md_control.value = full_text
                    page.update()

                # Display references underneath
                add_references(results, current_repo_path)
            except Exception as ex:
                if thinking_bubble in chat_list.controls:
                    chat_list.controls.remove(thinking_bubble)
                add_simple_message(f"Error during search: {ex}")
            finally:
                query_input.disabled = False
                send_btn.disabled = False
                page.update()

        threading.Thread(target=run_query, daemon=True).start()

    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.PRIMARY,
        on_click=handle_query,
        icon_size=ICON_MD,
    )
    query_input = ft.TextField(
        hint_text="Ask a question about the codebase...",
        hint_style=ft.TextStyle(size=FS_BODY),
        text_style=ft.TextStyle(size=FS_BODY),
        expand=True,
        on_submit=handle_query,
        border_radius=BR_BUBBLE,
        filled=True,
        content_padding=ft.Padding(left=14, right=14, top=10, bottom=10),
    )
    model_dropdown = ft.Dropdown(
        tooltip="Select LLM model",
        options=[
            ft.dropdown.Option("qwen2.5:7b"),
            ft.dropdown.Option("phi3:mini"),
            ft.dropdown.Option("gemma4:latest"),
        ],
        value="qwen2.5:7b",
        width=148,
        bgcolor=ft.Colors.SURFACE,
        text_size=FS_CODE,
    )

    chat_pane = ft.Container(
        width=CHAT_WIDTH,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            [
                _pane_header(ft.Icons.CHAT_BUBBLE_OUTLINE, "AI Chat"),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                chat_list,
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                ft.Container(
                    padding=PAD_ROW,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.SMART_TOY_OUTLINED, size=ICON_SM, color=ft.Colors.ON_SURFACE_VARIANT),
                                    ft.Text("Model:", size=FS_CAPTION, color=ft.Colors.ON_SURFACE_VARIANT),
                                    model_dropdown,
                                ],
                                spacing=6,
                            ),
                            ft.Row([query_input, send_btn], spacing=4),
                        ],
                        spacing=6,
                    ),
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ─────────────────────────────────────────────
    # LEFT PANE: Sidebar
    # ─────────────────────────────────────────────
    repo_path_input = ft.TextField(
        label="Repository Path",
        hint_text="/path/to/project",
        hint_style=ft.TextStyle(size=FS_CAPTION),
        text_style=ft.TextStyle(size=FS_BODY),
        label_style=ft.TextStyle(size=FS_SECTION),
        width=232,
        bgcolor=ft.Colors.SURFACE,
        content_padding=ft.Padding(left=10, right=10, top=8, bottom=8),
    )

    index_status_text = ft.Text("", size=FS_CAPTION, color=ft.Colors.ON_SURFACE_VARIANT, italic=True)

    file_list_view = ft.ListView(expand=True, spacing=2, auto_scroll=False)

    file_explorer_container = ft.Container(
        content=file_list_view,
        expand=True,
        bgcolor=ft.Colors.SURFACE,
        border_radius=BR_CONTAINER,
        padding=6,
        visible=False,
    )

    def on_select_folder_click(e):
        import subprocess
        try:
            script = 'tell application "System Events" to activate\ntell application "System Events" to return POSIX path of (choose folder with prompt "Select Codebase Folder")'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode == 0:
                repo_path_input.value = result.stdout.strip()
                index_status_text.value = ""
                file_explorer_container.visible = False
                page.update()
        except Exception as ex:
            add_simple_message(f"Could not open folder picker: {ex}")

    def on_index_click(e):
        current_repo_path = repo_path_input.value
        if not current_repo_path:
            add_simple_message("Please enter a repository path first.")
            return

        index_btn.disabled = True
        index_btn.text = "Indexing..."
        index_status_text.value = "⏳ Scanning files…"
        file_explorer_container.visible = False
        page.update()

        try:
            index_status_text.value = "⏳ Parsing & embedding…"
            page.update()
            chunks = build_index(current_repo_path)

            index_status_text.value = "⏳ Building explorer…"
            page.update()

            from backend.retrieval.scanner import FileScanner
            scanner = FileScanner(Path(current_repo_path))
            files = scanner.scan()

            file_list_view.controls.clear()

            def create_click_handler(p):
                return lambda e: open_file_in_editor(p)

            for f in files:
                rel_path = f.relative_to(Path(current_repo_path))
                file_path_str = str(f.resolve())

                file_item = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=ICON_SM, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(str(rel_path), size=FS_CAPTION, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=6,
                    ),
                    on_click=create_click_handler(file_path_str),
                    ink=True,
                    padding=PAD_FILE_ITEM,
                    border_radius=BR_BADGE,
                )
                file_list_view.controls.append(file_item)

            file_explorer_container.visible = True
            index_status_text.value = f"✅ {chunks} chunks indexed"
            add_agent_answer(f"✅ Indexed **{chunks}** chunks from `{current_repo_path}`. Ready to answer questions!")
        except Exception as ex:
            index_status_text.value = "❌ Indexing failed"
            add_simple_message(f"Error during indexing: {ex}")

        index_btn.disabled = False
        index_btn.text = "Index Repository"
        page.update()

    def _section_label(text: str):
        return ft.Text(text, size=FS_SECTION, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT)

    select_folder_btn = ft.ElevatedButton(
        "Browse Folder...",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=on_select_folder_click,
        width=232,
    )
    index_btn = ft.ElevatedButton(
        "Index Repository",
        on_click=on_index_click,
        width=200,
    )

    sidebar = ft.Container(
        width=SIDEBAR_WIDTH,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=PAD_SIDEBAR,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.MEMORY_OUTLINED, size=ICON_MD, color=ft.Colors.PRIMARY),
                        ft.Text("Code Next AI", size=FS_APP_TITLE, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=16),
                _section_label("Workspace"),
                select_folder_btn,
                repo_path_input,
                index_btn,
                index_status_text,
                ft.Divider(height=10),
                _section_label("Explorer"),
                file_explorer_container,
            ],
            spacing=8,
            expand=True,
        ),
    )

    # ─────────────────────────────────────────────
    # ROOT LAYOUT
    # ─────────────────────────────────────────────
    page.add(
        ft.Row(
            [
                sidebar,
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE),
                editor_pane,
                ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE),
                chat_pane,
            ],
            expand=True,
            spacing=0,
        )
    )

if __name__ == "__main__":
    ft.app(main)
