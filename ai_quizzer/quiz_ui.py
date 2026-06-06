from pathlib import Path


def build_irag_modal(active_citation, pdf_path, mo, mo_data, close_btn):
    """Build the i-RAG evidence modal overlay. Returns None if no citation is active.

    close_btn must be a mo.ui.button created in the calling cell body so that
    Marimo properly registers its on_click callback.
    """
    if active_citation is None:
        return None

    pdf_path = Path(pdf_path)
    ref = active_citation.get("reference", {})
    pages_list = ref.get("page_numbers", [])
    page_no = pages_list[0] if pages_list else 1
    section_str = ref.get("section", "General")
    snippet_str = ref.get("source_snippet", "")

    pdf_url = mo_data.pdf(pdf_path.read_bytes()).url + f"#page={page_no}&view=FitV"

    modal_body = mo.vstack(
        [
            mo.hstack(
                [
                    mo.md(f"### 📖 Source Reference: Page {pages_list} — *{section_str}*"),
                    close_btn,
                ],
                justify="space-between",
                align="center",
            ),
            mo.md("*Double-click or scroll inside the viewer to zoom and pan.*"),
            mo.pdf(src=pdf_url, width="100%", height="50vh"),
            mo.accordion(
                {"📄 View source text snippet": mo.md(f"```markdown\n{snippet_str}\n```")}
            ),
        ],
        gap=1,
    ).style(
        {
            "background": "#0d1117",
            "border": "1px solid rgba(240, 246, 252, 0.15)",
            "border-radius": "16px",
            "padding": "24px",
            "width": "100%",
            "max-width": "900px",
            "max-height": "85vh",
            "box-shadow": "0 20px 40px rgba(0,0,0,0.6)",
            "overflow-y": "auto",
            "color": "#e6edf3",
        }
    )

    return mo.vstack([modal_body], align="center", justify="center").style(
        {
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100vw",
            "height": "100vh",
            "background": "rgba(10, 12, 16, 0.75)",
            "backdrop-filter": "blur(8px)",
            "z-index": "9999",
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
        }
    )
