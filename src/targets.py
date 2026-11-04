"""The target slicers from upstream.lock.toml: the one source of every version the build writes."""

import tomllib
from pathlib import Path
from typing import TypedDict, cast

LOCK = Path(__file__).resolve().parent.parent / "upstream.lock.toml"
NAMES = ("orca", "bambu", "qidi", "snapmaker")


class Target(TypedDict):
    """One target slicer release and the stock profile tree it ships."""

    app: str
    version: str
    preset_version: str
    repository: str
    tag: str
    commit: str


def load(path: Path = LOCK) -> dict[str, Target]:
    """Read and check the lock: every target present, every field a non-empty string."""
    data = cast("dict[str, object]", tomllib.loads(path.read_text(encoding="utf-8")))
    raw = data.get("targets")
    if data.get("schema_version") != 1 or not isinstance(raw, dict):
        msg = f"{path.name}: expected schema_version 1 and a [targets] table"
        raise ValueError(msg)
    tables = cast("dict[str, object]", raw)
    out: dict[str, Target] = {}
    for name in NAMES:
        table = tables.get(name)
        fields = cast("dict[str, object]", table) if isinstance(table, dict) else {}
        missing = [k for k in Target.__annotations__ if not isinstance(fields.get(k), str) or not fields.get(k)]
        if missing or set(fields) - set(Target.__annotations__):
            msg = f"{path.name}: [targets.{name}] needs exactly {', '.join(Target.__annotations__)}"
            raise ValueError(msg)
        f = {k: str(v) for k, v in fields.items()}
        out[name] = Target(
            app=f["app"],
            version=f["version"],
            preset_version=f["preset_version"],
            repository=f["repository"],
            tag=f["tag"],
            commit=f["commit"],
        )
    return out


def preset_version(name: str) -> str:
    """Return the "version" written into the generated presets of one target."""
    return load()[name]["preset_version"]


def readme_table(targets: dict[str, Target]) -> str:
    """Return the README table of tested slicer versions."""
    rows = ["| Slicer | Version | Stock profiles |", "|---|---|---|"]
    for t in targets.values():
        url = f"https://github.com/{t['repository']}/tree/{t['tag']}/resources/profiles"
        rows.append(f"| {t['app']} | {t['version']} | [`{t['repository']}` {t['tag']}]({url}) |")
    return "\n".join(rows) + "\n"
