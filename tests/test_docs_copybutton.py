from pathlib import Path


def test_docs_dependency_includes_copybutton() -> None:
    """Docs dependency group must install sphinx-copybutton."""

    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "sphinx-copybutton" in text


def test_docs_conf_enables_copybutton() -> None:
    """Sphinx config must enable the extension and prompt stripping."""

    conf = Path("docs/conf.py").read_text(encoding="utf-8")
    assert '"sphinx_copybutton"' in conf
    assert "copybutton_prompt_text" in conf

