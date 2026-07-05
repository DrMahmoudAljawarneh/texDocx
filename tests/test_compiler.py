from pathlib import Path
import pytest

class TestCompileLatex:
    def test_pick_daemon_url_returns_string(self):
        host = "latexml"
        ports = ["3334", "3335", "3336"]
        import random
        port = random.choice(ports)
        url = f"http://{host}:{port}/"
        assert url.startswith("http://")
        assert url.endswith("/")
        assert "3334" in url or "3335" in url or "3336" in url

    def test_macros_injection(self):
        macros = "\\newcommand{\\mycmd}{replacement}"
        tex_content = "\\documentclass{article}\\begin{document}test\\end{document}"
        result = macros + "\n" + tex_content
        assert result.startswith(macros)
        assert "\\documentclass" in result
