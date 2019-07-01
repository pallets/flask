import io


def test_changelog_utf8_compatible():
    with io.open("CHANGES.rst", encoding="UTF-8") as f:
        f.read()
