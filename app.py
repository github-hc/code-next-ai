import flet as ft
from pathlib import Path
from main import build_index, query_repo

def main(page: ft.Page):
    page.title = "Code Next AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.window_width = 1400
    page.window_height = 860

    # ─────────────────────────────────────────────
    # State
    # ─────────────────────────────────────────────
    current_open_file = {"path": None}

    # ─────────────────────────────────────────────
    # MIDDLE PANE: Code Editor
    # ─────────────────────────────────────────────
    editor_tab_label = ft.Text(
        "No file open",
        size=12,
        color=ft.Colors.ON_SURFACE_VARIANT,
        italic=True
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
                ft.Icon(ft.Icons.CODE, size=64, color=ft.Colors.OUTLINE),
                ft.Text(
                    "Select a file from the explorer to view it here",
                    color=ft.Colors.OUTLINE,
                    size=14,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.Alignment(0, 0),
    )

    editor_body = ft.Stack(
        [editor_placeholder, ft.Container(content=code_markdown, expand=True, visible=False, padding=20)],
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

    editor_pane = ft.Container(
        expand=True,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            [
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=ft.Padding(left=16, right=16, top=8, bottom=8),
                    content=ft.Row([
                        ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        editor_tab_label,
                    ], spacing=6),
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                ft.ListView(
                    controls=[editor_body],
                    expand=True,
                    auto_scroll=False,
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )

    # ─────────────────────────────────────────────
    # RIGHT PANE: Chat
    # ─────────────────────────────────────────────
    chat_list = ft.ListView(expand=True, spacing=12, auto_scroll=True, padding=16)

    def add_user_message(text: str):
        """Adds the user bubble immediately."""
        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, selectable=True),
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        padding=14,
                        border_radius=10,
                        width=380,
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def add_thinking_bubble():
        """Adds a temporary 'Thinking…' spinner bubble and returns it so we can remove it later."""
        bubble = ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.ProgressRing(width=14, height=14, stroke_width=2),
                            ft.Text("Thinking…", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=14,
                    border_radius=10,
                )
            ],
            alignment=ft.MainAxisAlignment.START,
        )
        chat_list.controls.append(bubble)
        page.update()
        return bubble

    def add_agent_answer(answer_text: str):
        """Adds the final LLM answer bubble."""
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
                        padding=14,
                        border_radius=10,
                        expand=True,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
        )
        page.update()

    def add_references(results, current_repo_path: str):
        """Adds collapsible reference panels using ExpansionTile."""
        if not results:
            return

        tiles = []
        for i, res in enumerate(results, 1):
            try:
                rel_path = Path(res["file_path"]).relative_to(Path(current_repo_path).resolve())
            except ValueError:
                rel_path = res["file_path"]

            code_block = ft.Markdown(
                f"```python\n{res['code']}\n```",
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark",
            )

            tile = ft.ExpansionTile(
                title=ft.Text(
                    f"{i}. {res['symbol_name']}",
                    size=12,
                    weight=ft.FontWeight.W_600,
                ),
                subtitle=ft.Text(
                    f"{rel_path}  ·  Lines {res['start_line']}–{res['end_line']}",
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                controls=[
                    ft.Container(content=code_block, padding=ft.Padding(left=8, right=8, top=4, bottom=8))
                ],
            )
            tiles.append(tile)

        refs_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text("References", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT),
                    *tiles,
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=10,
            padding=10,
        )

        chat_list.controls.append(
            ft.Row([refs_container], alignment=ft.MainAxisAlignment.START)
        )
        page.update()

    def add_simple_message(text: str):
        """Adds a plain text agent message."""
        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(text, selectable=True),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=14,
                        border_radius=10,
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

        query_input.disabled = True
        send_btn.disabled = True
        query_input.value = ""
        page.update()

        # 1. Show user bubble immediately
        add_user_message(query)

        # 2. Show "Thinking…" spinner immediately
        thinking_bubble = add_thinking_bubble()

        try:
            selected_model = model_dropdown.value
            answer, results = query_repo(current_repo_path, query, model_name=selected_model)

            # 3. Remove the thinking bubble
            chat_list.controls.remove(thinking_bubble)

            # 4. Show LLM answer
            add_agent_answer(answer)

            # 5. Show collapsible references
            add_references(results, current_repo_path)

        except Exception as ex:
            # Safely remove thinking bubble if still present
            if thinking_bubble in chat_list.controls:
                chat_list.controls.remove(thinking_bubble)
            add_simple_message(f"Error during search: {ex}")
        finally:
            query_input.disabled = False
            send_btn.disabled = False
            query_input.focus()
            page.update()

    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.PRIMARY,
        on_click=handle_query,
    )
    query_input = ft.TextField(
        hint_text="Ask a question about the codebase...",
        expand=True,
        on_submit=handle_query,
        border_radius=20,
        filled=True,
    )
    model_dropdown = ft.Dropdown(
        tooltip="Select LLM model",
        options=[
            ft.dropdown.Option("qwen2.5:7b"),
            ft.dropdown.Option("phi3:mini"),
            ft.dropdown.Option("gemma4:latest"),
        ],
        value="qwen2.5:7b",
        width=140,
        bgcolor=ft.Colors.SURFACE,
        text_size=12,
    )

    chat_pane = ft.Container(
        width=460,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            [
                # Chat header
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    padding=ft.Padding(left=16, right=16, top=8, bottom=8),
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text("AI Chat", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    ], spacing=6),
                ),
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                # Messages
                chat_list,
                ft.Divider(height=1, color=ft.Colors.OUTLINE),
                # Input bar with model dropdown
                ft.Container(
                    padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.SMART_TOY_OUTLINED, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                                    model_dropdown,
                                ],
                                spacing=4,
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
        hint_text="e.g. /Users/you/my-project",
        width=240,
        bgcolor=ft.Colors.SURFACE,
        text_size=12,
    )

    index_status_text = ft.Text("", size=11, color=ft.Colors.ON_SURFACE_VARIANT, italic=True)

    file_list_view = ft.ListView(expand=True, spacing=2, auto_scroll=False)

    file_explorer_container = ft.Container(
        content=file_list_view,
        expand=True,
        bgcolor=ft.Colors.SURFACE,
        border_radius=5,
        padding=8,
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
            index_status_text.value = "⏳ Parsing & embedding chunks…"
            page.update()

            chunks = build_index(current_repo_path)

            index_status_text.value = "⏳ Building file explorer…"
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
                            ft.Icon(ft.Icons.INSERT_DRIVE_FILE_OUTLINED, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text(str(rel_path), size=12, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                        spacing=6,
                    ),
                    on_click=create_click_handler(file_path_str),
                    ink=True,
                    padding=ft.Padding(left=8, right=8, top=5, bottom=5),
                    border_radius=4,
                )
                file_list_view.controls.append(file_item)

            file_explorer_container.visible = True
            index_status_text.value = f"✅ {chunks} chunks indexed"
            add_agent_answer(f"✅ Indexed **{chunks}** chunks from `{current_repo_path}`. Ready to answer questions!")
        except Exception as ex:
            index_status_text.value = f"❌ Indexing failed"
            add_simple_message(f"Error during indexing: {ex}")

        index_btn.disabled = False
        index_btn.text = "Index Repository"
        page.update()

    select_folder_btn = ft.ElevatedButton(
        "Browse Folder...",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=on_select_folder_click,
        width=240,
    )
    index_btn = ft.ElevatedButton("Index Repository", on_click=on_index_click, width=200)

    sidebar = ft.Container(
        width=270,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=ft.Padding(left=12, right=12, top=12, bottom=12),
        content=ft.Column(
            [
                ft.Text("Code Next AI", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                ft.Text("Workspace", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT),
                select_folder_btn,
                repo_path_input,
                index_btn,
                index_status_text,
                ft.Divider(height=12),
                ft.Text("Explorer", size=11, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE_VARIANT),
                file_explorer_container,
            ],
            spacing=8,
            expand=True,
        ),
    )

    # ─────────────────────────────────────────────
    # ROOT LAYOUT: 3 panes
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
