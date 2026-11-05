import hashlib
import json
from io import BytesIO

import pytest

from fee_schedule_diff.cli import download, main
from fee_schedule_diff.extract import parse_page


def test_cached_download_and_checksum_mismatch_leave_original(tmp_path, monkeypatch):
    good = b"%PDF- pinned edition"
    source = dict(
        label="edition",
        url="https://www2.gov.bc.ca/source.pdf",
        sha256=hashlib.sha256(good).hexdigest(),
    )
    path = tmp_path / "edition.pdf"
    path.write_bytes(good)
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: pytest.fail("network call"))
    assert download(source, tmp_path) == path
    path.write_bytes(b"original")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: BytesIO(b"%PDF- different"))
    with pytest.raises(ValueError, match="checksum"):
        download(source, tmp_path)
    assert path.read_bytes() == b"original"
    assert not list(tmp_path.glob("*.part"))


def test_html_response_and_non_government_host_rejected(tmp_path, monkeypatch):
    source = dict(label="edition", url="https://www2.gov.bc.ca/source.pdf", sha256="x")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **kw: BytesIO(b"<html>error</html>"))
    with pytest.raises(ValueError, match="PDF"):
        download(source, tmp_path)
    source["url"] = "https://gov.bc.ca.example.test/source.pdf"
    with pytest.raises(ValueError, match="gov.bc.ca"):
        download(source, tmp_path)


def test_cli_compare_and_validation(tmp_path, sampled_editions):
    paths = []
    for i, edition in enumerate(sampled_editions):
        path = tmp_path / f"{i}.json"
        path.write_text(json.dumps(edition))
        paths.append(str(path))
    result, report, short = [tmp_path / name for name in ("diff.json", "diff.md", "short.md")]
    assert (
        main(
            [
                "compare",
                *paths,
                "--out",
                str(result),
                "--markdown",
                str(report),
                "--short",
                str(short),
            ]
        )
        == 0
    )
    assert "#page=" in report.read_text()
    assert result.exists() and short.exists()
    assert main(["validate", *paths, "--out", str(tmp_path / "accuracy.json")]) == 0
    assert (
        main(
            [
                "extract",
                "missing.pdf",
                "--url",
                "javascript:bad",
                "--label",
                "x",
                "--out",
                str(result),
            ]
        )
        == 2
    )


def test_empty_page_is_explicit_review():
    items, review = parse_page([], 1, "https://www2.gov.bc.ca/a.pdf")
    assert not items
    assert "no extractable" in review[0]["reason"]
