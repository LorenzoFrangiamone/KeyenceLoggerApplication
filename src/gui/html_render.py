import markdown

_CSS = """
    body {
        font-family: Segoe UI, Arial, sans-serif;
        font-size: 11pt;
        color: #1f2937;
        background: #ffffff;
        padding: 14px;
        line-height: 1.55;
        margin: 0;
    }

    h1 {
        font-size: 18pt;
        margin: 0 0 10px 0;
        color: #111827;
    }

    h2 {
        font-size: 14pt;
        margin: 18px 0 8px 0;
        color: #111827;
    }

    h3 {
        font-size: 12pt;
        margin: 14px 0 6px 0;
        color: #111827;
    }

    p {
        margin: 8px 0;
    }

    ul, ol {
        margin: 8px 0 8px 20px;
        padding-left: 18px;
    }

    li {
        margin: 4px 0;
    }

    strong {
        color: #111827;
        font-weight: 600;
    }

    em {
        color: #374151;
        font-style: italic;
    }

    code {
        font-family: Consolas, "Courier New", monospace;
        background: #f3f4f6;
        border-radius: 6px;
        padding: 2px 5px;
        font-size: 10pt;
    }

    pre {
        font-family: Consolas, "Courier New", monospace;
        background: #f3f4f6;
        border-radius: 8px;
        padding: 12px;
        white-space: pre-wrap;
    }

    blockquote {
        border-left: 4px solid #cbd5e1;
        padding-left: 12px;
        margin: 10px 0;
        color: #475569;
        background: #f8fafc;
    }

    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 16px 0;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    th, td {
        border: 1px solid #e5e7eb;
        padding: 8px;
        text-align: left;
    }

    th {
        background: #f9fafb;
    }
"""


def wrap_html_body(html_body: str) -> str:
    return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>{_CSS}</style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """


def render_markdown(md_text: str) -> str:
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "sane_lists", "nl2br"]
    )
    return wrap_html_body(html_body)
