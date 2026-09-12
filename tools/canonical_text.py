#!/usr/bin/env python3
from __future__ import annotations

import pathlib

UTF8_BOM = b"\xef\xbb\xbf"


def canonical_text_bytes(text: str) -> bytes:
    if "\r" in text:
        raise ValueError("canonical Joyflow text must use LF newlines")
    data = text.encode("utf-8")
    if data.startswith(UTF8_BOM):
        raise ValueError("canonical Joyflow text must not contain a UTF-8 BOM")
    return data


def read_canonical_text(path: str | pathlib.Path) -> str:
    data = pathlib.Path(path).read_bytes()
    if data.startswith(UTF8_BOM):
        raise ValueError(f"canonical Joyflow text has UTF-8 BOM: {path}")
    if b"\r" in data:
        raise ValueError(f"canonical Joyflow text has non-LF newline bytes: {path}")
    return data.decode("utf-8")


def write_canonical_text(path: str | pathlib.Path, text: str) -> None:
    pathlib.Path(path).write_bytes(canonical_text_bytes(text))


def canonical_text_matches(path: str | pathlib.Path, text: str) -> bool:
    target = pathlib.Path(path)
    return target.is_file() and target.read_bytes() == canonical_text_bytes(text)
