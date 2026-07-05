from pathlib import Path
import pytest

ALLOWED_EXTENSIONS = {".tex", ".zip"}
MAX_FILE_SIZE = 50 * 1024 * 1024

def _validate_file(filename: str, content_length: int):
    if content_length > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: .tex, .zip")

class TestFileValidation:
    def test_tex_file_accepted(self):
        _validate_file("paper.tex", 1000)

    def test_zip_file_accepted(self):
        _validate_file("bundle.zip", 1000)

    def test_invalid_extension_rejected(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            _validate_file("paper.pdf", 1000)

    def test_oversized_file_rejected(self):
        with pytest.raises(ValueError, match="File too large"):
            _validate_file("paper.tex", MAX_FILE_SIZE + 1)

    def test_empty_tex_file_accepted(self):
        _validate_file("paper.tex", 0)

    def test_uppercase_extension_accepted(self):
        _validate_file("paper.TEX", 1000)
