import re


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks of at most `size` characters.

    Cuts at a space or newline when one exists in the second half of the window,
    so words and steps aren't split. Newlines are kept because numbered steps need them.
    """
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need size > 0 and 0 <= overlap < size")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = max(text.rfind(" ", start + size // 2, end),
                      text.rfind("\n", start + size // 2, end))
            if cut != -1:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # always move forward
        # don't start in the middle of a word
        while start < end and not text[start - 1].isspace():
            start += 1
    return chunks