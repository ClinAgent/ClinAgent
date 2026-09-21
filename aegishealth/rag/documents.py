"""Load the specified Executive Summary and retain source/page/character provenance."""

import hashlib
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

GUIDELINE_URL = "https://www.ahajournals.org/doi/10.1161/CIR.0000000000000677"
GUIDELINE_TITLE = (
    "2019 ACC/AHA Guideline on the Primary Prevention of Cardiovascular Disease: Executive Summary"
)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_guideline(path: Path) -> tuple[list[Document], dict]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Guideline not found: {path}. Provide the Executive Summary TXT or PDF."
        )
    if path.suffix.lower() not in {".txt", ".pdf"}:
        raise ValueError("Guideline must be a .txt or .pdf file, not the UCI tabular dataset")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    metadata = {
        "source": path.name,
        "source_sha256": digest,
        "source_url": GUIDELINE_URL,
        "title": GUIDELINE_TITLE,
    }
    skipped = []
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF: provide an unlocked, text-readable guideline")
        documents = []
        for number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                skipped.append(number)
                continue
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        **metadata,
                        "page": number,
                        "page_label": reader.page_labels[number - 1],
                    },
                )
            )
        if len(skipped) > len(reader.pages) / 2:
            raise ValueError(
                "PDF has too many pages without text. Run OCR or supply a text export."
            )
    else:
        text = raw.decode("utf-8-sig").replace("\r\n", "\n")
        if re.search(r"<(?:!doctype|html|body)\b", text[:2000], re.IGNORECASE):
            raise ValueError("HTML/login page detected. Supply the actual guideline text or PDF.")
        documents = [Document(page_content=text, metadata=metadata)]
    combined = "\n".join(d.page_content for d in documents)
    if len(combined.strip()) < 2000:
        raise ValueError(
            "Document is too short: supply the complete Executive Summary, not its abstract"
        )
    heading = re.sub(r"\s+", " ", combined[:20000]).lower()
    required = ["2019", "primary prevention", "cardiovascular disease", "executive summary"]
    if not all(phrase in heading for phrase in required):
        raise ValueError(
            "Expected the 2019 ACC/AHA primary-prevention Executive Summary. Check the file."
        )
    return documents, {
        **metadata,
        "document_units": len(documents),
        "characters": len(combined),
        "blank_pdf_pages_skipped": skipped,
    }


def split_guideline(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        strip_whitespace=False,
        length_function=len,
    )
    chunks = [d for d in splitter.split_documents(documents) if d.page_content.strip()]
    if len(chunks) < 2:
        raise ValueError("At least two nonempty guideline chunks are required")
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        identity = f"{chunk.metadata['source_sha256']}:{chunk.metadata.get('page', 0)}:{chunk.metadata['start_index']}:{chunk.page_content}"
        chunk.metadata["chunk_id"] = hashlib.sha256(identity.encode()).hexdigest()
    return chunks
