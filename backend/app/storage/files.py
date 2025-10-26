"""File-system helpers for local persistence."""

from collections.abc import Iterable
from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def list_files(path: Path | str, suffixes: Iterable[str] | None = None) -> list[Path]:
    base = Path(path)
    if not base.exists():
        return []
    if suffixes is None:
        return sorted(p for p in base.glob("*") if p.is_file())
    suffix_set = {s.lower() for s in suffixes}
    return sorted(p for p in base.glob("*") if p.is_file() and p.suffix.lower() in suffix_set)


def read_bytes(path: Path | str) -> bytes:
    return Path(path).read_bytes()


def write_bytes(path: Path | str, data: bytes) -> None:
    target = Path(path)
    ensure_dir(target.parent)
    target.write_bytes(data)
