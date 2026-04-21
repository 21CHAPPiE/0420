from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import get_config


def extract_pdf_text(force: bool = False) -> Path:
    config = get_config()
    output_path = config.parsed_text_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        return output_path

    cmd = [
        config.pdftotext_path,
        "-layout",
        "-enc",
        "UTF-8",
        str(config.pdf_path),
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    return output_path

