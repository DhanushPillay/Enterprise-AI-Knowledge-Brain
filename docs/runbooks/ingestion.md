# Adding New Data Sources

How to add support for a new document format or data source.

---

## What works now

| Format | Loader | Status |
|--------|--------|--------|
| PDF | `loaders.py` → `_load_pdf()` | Done |
| TXT | `loaders.py` → `_load_text()` | Done |
| Markdown | `loaders.py` → `_load_markdown()` | Done |
| Code (.py, .js, etc.) | `loaders.py` → `_load_code()` | Done |
| DOCX | — | Not yet |
| HTML | — | Not yet |
| CSV | — | Not yet |

---

## Adding a file format

### 1. Write the loader

Add this to `src/ingestion/loaders.py`:

```python
def _load_new_format(self, file_path: str) -> RawDocument:
    """Load [format] files."""
    with open(file_path, "rb") as f:
        raw = f.read()

    text = extract_text_from_format(raw)

    return RawDocument(
        text=text,
        metadata={
            "source": file_path,
            "format": "new_format",
            "size_bytes": len(raw),
        }
    )
```

### 2. Register it

Update the file type map in `loaders.py`:

```python
SUPPORTED_FORMATS = {
    ".pdf": "_load_pdf",
    ".txt": "_load_text",
    ".md": "_load_markdown",
    ".py": "_load_code",
    ".new_ext": "_load_new_format",  # Add here
}
```

### 3. Add any new dependencies

```bash
pip install new-library
echo "new-library==1.0.0" >> requirements.txt
```

### 4. Test it

```python
from src.ingestion.loaders import DocumentLoader

loader = DocumentLoader()
doc = loader.load("path/to/test.new_ext")
assert doc.text  # Not empty
assert doc.metadata["format"] == "new_format"
```

---

## Adding an API or database source

For non-file sources, write a new agent:

```python
# src/agents/api_source.py
class APISourceAgent:
    async def fetch(self, endpoint: str) -> list[RawDocument]:
        """Fetch data from API and convert to documents."""
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as resp:
                data = await resp.json()

        return [
            RawDocument(text=item["content"], metadata={"source": endpoint})
            for item in data
        ]
```

Then wire it into `src/agents/ingestion.py`.

---

## Test checklist

- [ ] Loader reads the file without crashing
- [ ] Text extraction actually gets content (not empty)
- [ ] Metadata is filled in correctly
- [ ] Chunks get created
- [ ] Embeddings get created
- [ ] Entities get extracted
- [ ] Graph gets updated
- [ ] A query can find the ingested data

---

## Common snags

| What goes wrong | What to try |
|----------------|-------------|
| Encoding errors | Use `utf-8`, fall back to `latin-1` if needed |
| Text comes back empty | Check if the file is binary instead of text |
| Memory blows up on big files | Stream the processing, chunk before loading |
| Weird characters in text | Run it through `preprocessor.py` |
