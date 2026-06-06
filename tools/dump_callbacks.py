"""Dump the Dash callback wiring map as greppable one-line entries.

Dash wires callbacks by string component ids, which symbol-based tools (LSP,
code graphs) cannot follow. Dash itself keeps the full registry at runtime,
so this script imports the app (with TESTING=1 mocks, no network) and prints
one line per callback:

    <file>:<line> <function> | out: id.prop, ... | in: id.prop, ... | state: id.prop, ...

Usage:
    poetry run python tools/dump_callbacks.py              # whole map
    poetry run python tools/dump_callbacks.py | rg pf-graf # wiring of one id
"""

import inspect
import os
import sys
from pathlib import Path
from typing import Any


def _ids(dependencies: list[dict[str, Any]]) -> str:
    """Render input/state dependency dicts as 'id.property' pairs."""
    return ", ".join(f"{d['id']}.{d['property']}" for d in dependencies)


def _outputs(output: Any) -> str:
    """Render a single Output or a list of Outputs as 'id.property' pairs."""
    outs = output if isinstance(output, list) else [output]
    return ", ".join(f"{o.component_id}.{o.component_property}" for o in outs)


def _location(entry: dict[str, Any], root: Path) -> tuple[Path | None, int]:
    """Resolve the real source file:line of the (dash-wrapped) callback.

    Returns (None, 0) for clientside callbacks — they register without a
    Python "callback" key (the function lives in JS).
    """
    fn = entry.get("callback")
    if fn is None:
        return None, 0
    fn = inspect.unwrap(fn)
    file = Path(fn.__code__.co_filename)
    try:
        file = file.relative_to(root)
    except ValueError:
        pass  # callback defined outside the repo — keep the absolute path
    return file, fn.__code__.co_firstlineno


def format_entry(entry: dict[str, Any], root: Path) -> str:
    """Format one callback_map entry as a single greppable line."""
    file, line = _location(entry, root)
    if file is None:
        head = "<clientside>"
    else:
        fn = inspect.unwrap(entry["callback"])
        head = f"{file}:{line} {fn.__name__}"
    parts = [
        head,
        f"out: {_outputs(entry['output'])}",
        f"in: {_ids(entry['inputs'])}",
    ]
    if entry["state"]:
        parts.append(f"state: {_ids(entry['state'])}")
    return " | ".join(parts)


def format_callback_map(callback_map: dict[str, dict[str, Any]], root: Path) -> str:
    """Format all entries sorted by source location (file, then line)."""

    def sort_key(entry: dict[str, Any]) -> tuple[str, int]:
        file, line = _location(entry, root)
        return ("", 0) if file is None else (str(file), line)  # clientside entries first

    return "\n".join(format_entry(entry, root) for entry in sorted(callback_map.values(), key=sort_key))


def main() -> None:
    """Import the app under TESTING mocks and print the full wiring map."""
    os.environ.setdefault("TESTING", "1")  # mocked okama — no network, no Redis data

    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))  # script runs by path, so tools/ — not the repo root — is on sys.path

    from app import app  # registers page callbacks into GLOBAL_CALLBACK_MAP on import
    from dash._callback import GLOBAL_CALLBACK_MAP

    merged = {**app.callback_map, **GLOBAL_CALLBACK_MAP}
    print(format_callback_map(merged, root))


if __name__ == "__main__":
    main()
