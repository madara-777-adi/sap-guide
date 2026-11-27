import re

from app.chunking import chunk_text

T_CODE_RE = re.compile(r"T-code:?\s+([A-Z][A-Z0-9]{3,9})\b")
BODY_SIZE = 700  # leaves room for the heading lines added to every chunk


def find_t_code(*texts: str) -> str | None:
    for text in texts:
        match = T_CODE_RE.search(text)
        if match:
            return match.group(1)
    return None


def split_markdown(text: str) -> list[tuple[int, int, str, str | None]]:
    """Return (section_no, chunk_index, content, t_code) rows.

    Every chunk starts with the document title and the section heading.
    Sections with no body are skipped. Section numbers start at 1.
    """
    title = ""
    sections: list[tuple[str, list[str]]] = []
    heading, lines = "Overview", []
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            sections.append((heading, lines))
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)
    sections.append((heading, lines))

    rows = []
    number = 0
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        number += 1
        t_code = find_t_code(heading, body)
        header = f"{title}\n{heading}".strip()
        for index, part in enumerate(chunk_text(body, size=BODY_SIZE, overlap=100)):
            rows.append((number, index, f"{header}\n\n{part}", t_code))
    return rows