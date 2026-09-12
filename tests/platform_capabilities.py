from __future__ import annotations

import pathlib
import tempfile


def probe_symlink_capability() -> dict[str, str | bool]:
    with tempfile.TemporaryDirectory(prefix="joyflow-symlink-probe-") as td:
        root = pathlib.Path(td)
        target = root / "target.txt"
        link = root / "link.txt"
        target.write_bytes(b"probe")
        try:
            link.symlink_to(target.name)
            if not link.is_symlink() or link.read_bytes() != b"probe":
                return {"capability": "SYMLINK", "status": "NOT_APPLICABLE_PLATFORM_CAPABILITY", "supported": False, "reason": "probe did not produce a usable symlink"}
        except (OSError, NotImplementedError) as exc:
            return {"capability": "SYMLINK", "status": "NOT_APPLICABLE_PLATFORM_CAPABILITY", "supported": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {"capability": "SYMLINK", "status": "SUPPORTED", "supported": True, "reason": "direct probe succeeded"}
