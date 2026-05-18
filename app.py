import flet as ft
from pathlib import Path
from main import build_index, query_repo

def main(page: ft.Page):
    page.title = "Code Next AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.window_width = 1200
    page.window_height = 800

    repo_path_input = ft.TextField(
        label="Repository Path",
        hint_text="e.g. /Users/harshitchoudhary/Tech2go/Agentic",
        width=260,
        bgcolor=ft.Colors.SURFACE
    )
    current_repo_path = None
    
    chat_list = ft.ListView(expand=True, spacing=15, auto_scroll=True, padding=20)
    
    def add_message(role, content, is_markdown=False):
        if role == "user":
            bg_color = ft.Colors.SURFACE_CONTAINER_HIGHEST
            text_color = ft.Colors.ON_SURFACE_VARIANT
            align = ft.MainAxisAlignment.END
        else:
            bg_color = ft.Colors.SURFACE
            text_color = ft.Colors.ON_SURFACE
            align = ft.MainAxisAlignment.START

        if is_markdown:
            content_control = ft.Markdown(
                content,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                code_theme="atom-one-dark"
            )
        else:
            content_control = ft.Text(content, selectable=True)

        chat_list.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=content_control,
                        bgcolor=bg_color,
                        padding=15,
                        border_radius=10,
                        expand=True if is_markdown else False
                    )
                ],
                alignment=align
            )
        )
        page.update()

    def handle_query(e):
        current_repo_path = repo_path_input.value
        if not current_repo_path:
            add_message("agent", "Please enter a repository path and index it first.")
            return
            
        query = query_input.value
        if not query or query_input.disabled:
            return
            
        query_input.disabled = True
        send_btn.disabled = True
        loading_ring.visible = True
        add_message("user", query)
        query_input.value = ""
        page.update()
        
        # Call backend
        try:
            results = query_repo(current_repo_path, query)
            if not results:
                add_message("agent", "No relevant code chunks found.")
            else:
                md_output = ""
                for i, res in enumerate(results, 1):
                    # Make paths relative for cleaner view
                    try:
                        rel_path = Path(res['file_path']).relative_to(Path(current_repo_path).resolve())
                    except ValueError:
                        rel_path = res['file_path']
                        
                    md_output += f"### {i}. `{res['symbol_name']}`\n"
                    md_output += f"**File**: `{rel_path}` (Lines {res['start_line']}-{res['end_line']})\n\n"
                    md_output += f"```python\n{res['code']}\n```\n\n---\n"
                add_message("agent", md_output, is_markdown=True)
        except Exception as ex:
            add_message("agent", f"Error during search: {ex}")
        finally:
            query_input.disabled = False
            send_btn.disabled = False
            loading_ring.visible = False
            query_input.focus()
            page.update()

    loading_ring = ft.ProgressRing(visible=False, width=24, height=24)
    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.PRIMARY,
        on_click=handle_query
    )

    query_input = ft.TextField(
        hint_text="Ask a question about the codebase...",
        expand=True,
        on_submit=handle_query,
        border_radius=20,
        filled=True,
    )



    def on_select_folder_click(e):
        import subprocess
        try:
            # macOS native folder picker via AppleScript (runs in subprocess to avoid thread blocking)
            script = 'tell application "System Events" to activate\ntell application "System Events" to return POSIX path of (choose folder with prompt "Select Codebase Folder")'
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                repo_path_input.value = path
                page.update()
        except Exception as ex:
            add_message("agent", f"Could not open native folder picker. You can paste the path manually. Error: {ex}")

    select_folder_btn = ft.ElevatedButton(
        "Browse Folder...",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=on_select_folder_click,
        width=260
    )

    def on_index_click(e):
        current_repo_path = repo_path_input.value
        if not current_repo_path:
            add_message("agent", "Please enter a repository path first.")
            return
        
        index_btn.disabled = True
        index_btn.text = "Indexing..."
        page.update()
        
        try:
            chunks = build_index(current_repo_path)
            add_message("agent", f"Successfully indexed '{current_repo_path}'! {chunks} chunks stored.")
        except Exception as ex:
            add_message("agent", f"Error during indexing: {ex}")
            
        index_btn.disabled = False
        index_btn.text = "Index Repository"
        page.update()

    index_btn = ft.ElevatedButton("Index Repository", on_click=on_index_click, width=200)

    # UI Layout
    sidebar = ft.Container(
        width=300,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=20,
        content=ft.Column(
            [
                ft.Text("Code Next AI", size=24, weight="bold"),
                ft.Divider(height=30),
                ft.Text("Workspace", weight="bold"),
                select_folder_btn,
                repo_path_input,
                ft.Divider(height=30),
                index_btn
            ],
            spacing=10
        )
    )

    main_area = ft.Container(
        expand=True,
        padding=0,
        content=ft.Column(
            [
                chat_list,
                ft.Container(
                    padding=20,
                    content=ft.Row(
                        [
                            query_input,
                            loading_ring,
                            send_btn
                        ]
                    )
                )
            ]
        )
    )

    page.add(
        ft.Row(
            [sidebar, ft.VerticalDivider(width=1, color=ft.Colors.OUTLINE), main_area],
            expand=True,
            spacing=0
        )
    )

if __name__ == "__main__":
    ft.app(main)
