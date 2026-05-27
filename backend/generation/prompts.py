from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────
#  System persona — sets the LLM's role and behaviour
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert software engineering assistant embedded inside a developer's IDE.
Your job is to answer questions about the codebase that has been indexed, using ONLY \
the retrieved code chunks provided below as ground truth.

Rules you MUST follow:
1. Answer precisely and concisely — avoid padding or filler text.
2. Ground every claim in the provided code chunks. Do NOT hallucinate APIs, \
functions, or file names that are not present in the context.
3. If the answer cannot be found in the context, reply exactly:
   "I don't have enough context to answer this from the indexed codebase."
4. When referencing code, use inline markdown code fences with the correct language.
5. When referencing a file or symbol, mention its file path and line range \
as shown in the context headers.
6. If the question asks you to count things (files, tools, functions, etc.), \
count only what is visible in the context chunks — do not guess.
7. Structure longer answers with clear headings or bullet points.
"""


def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs the full prompt string that will be sent to the LLM.

    Args:
        query:          The natural language question from the developer.
        context_chunks: List of flat result dicts returned by WeaviateVectorStore.hybrid_search.
                        Each dict contains: file_path, symbol_name, start_line, end_line, score, code.

    Returns:
        A single prompt string ready to be passed to /api/generate.
    """
    if not context_chunks:
        context_section = "No relevant code chunks were retrieved for this query."
    else:
        chunk_blocks = []
        for i, chunk in enumerate(context_chunks, 1):
            file_path   = chunk.get("file_path", "unknown")
            symbol_name = chunk.get("symbol_name", "unknown")
            start_line  = chunk.get("start_line", "?")
            end_line    = chunk.get("end_line", "?")
            score       = chunk.get("score", 0.0)
            code        = chunk.get("code", "").strip()

            # Derive language hint from file extension for the code fence
            ext = file_path.rsplit(".", 1)[-1] if "." in file_path else ""
            lang_map = {
                "py": "python", "ts": "typescript", "tsx": "tsx",
                "js": "javascript", "jsx": "jsx", "json": "json",
                "md": "markdown", "html": "html", "css": "css",
                "sh": "bash", "yaml": "yaml", "yml": "yaml",
            }
            lang = lang_map.get(ext, "")

            block = (
                f"### Chunk {i}  |  `{file_path}`  lines {start_line}–{end_line}"
                f"  |  symbol: `{symbol_name}`  |  score: {score:.3f}\n"
                f"```{lang}\n{code}\n```"
            )
            chunk_blocks.append(block)

        context_section = "\n\n".join(chunk_blocks)

    return (
        f"{SYSTEM_PROMPT}\n"
        f"{'─' * 60}\n"
        f"## Retrieved Code Context\n\n"
        f"{context_section}\n\n"
        f"{'─' * 60}\n"
        f"## Developer Question\n\n"
        f"{query}\n\n"
        f"{'─' * 60}\n"
        f"## Answer\n"
    )


