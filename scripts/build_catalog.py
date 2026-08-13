#!/usr/bin/env python3
"""Validate the entries under plugins/ and assemble catalog.json.

Without arguments this runs offline: schema validation, the cross-checks the
schema cannot express (name uniqueness, filename match, append-only versions),
and the catalogue is written out.

    python3 scripts/build_catalog.py

With --verify it additionally fetches every artefact, checks its digest and the
name inside it. That is what CI runs on a pull request; it needs network access.

    python3 scripts/build_catalog.py --verify

Deep validation of a plugin artefact itself (action methods, path form, webhook
fields) is deliberately NOT reimplemented here — `covey plugin lint` is the one
implementation of that check, and it is the same code an instance applies at
install time.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
SCHEMA = ROOT / "schema" / "entry.schema.json"
CATALOG_SCHEMA = ROOT / "schema" / "catalog.schema.json"
CATALOG = ROOT / "catalog.json"

SCHEMA_VERSION = 1
FETCH_TIMEOUT = 30
MAX_ARTEFACT_BYTES = 1 << 20  # 1 MiB — an artefact is a description, not a payload


class Problems(list):
    def add(self, where: str, msg: str) -> None:
        self.append(f"{where}: {msg}")


def load_entries(problems: Problems) -> list[dict]:
    entries = []
    for path in sorted(PLUGINS.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.add(path.name, f"not valid JSON ({e})")
            continue
        if not isinstance(entry, dict):
            problems.add(path.name, "top level must be an object")
            continue
        entry["_file"] = path
        entries.append(entry)
    return entries


def validate_schema(entries: list[dict], problems: Problems) -> None:
    try:
        import jsonschema
    except ImportError:
        print("note: jsonschema not installed — skipping schema validation "
              "(pip install jsonschema)", file=sys.stderr)
        return
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for entry in entries:
        payload = {k: v for k, v in entry.items() if k != "_file"}
        for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
            where = "/".join(str(p) for p in err.path) or "(root)"
            problems.add(entry["_file"].name, f"{where}: {err.message}")


def validate_catalog(catalog: dict, problems: Problems) -> None:
    """Check the assembled catalogue against the schema consumers are told to expect.

    The entries were validated one by one already — this checks the envelope,
    and it keeps catalog.schema.json honest. A schema that is published but
    never checked drifts away from what is actually served, and the people who
    find out are the ones writing readers against it.
    """
    try:
        import jsonschema
        from referencing import Registry, Resource
    except ImportError:
        print("note: jsonschema/referencing not installed — skipping catalogue "
              "schema validation (pip install jsonschema referencing)", file=sys.stderr)
        return
    entry = Resource.from_contents(json.loads(SCHEMA.read_text(encoding="utf-8")))
    registry = Registry().with_resource("entry.schema.json", entry)
    schema = json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    for err in validator.iter_errors(catalog):
        where = "/".join(str(p) for p in err.path) or "(root)"
        problems.add("catalog.json", f"{where}: {err.message}")


def validate_cross(entries: list[dict], problems: Problems) -> None:
    """The checks the schema cannot express."""
    seen: dict[str, str] = {}
    for entry in entries:
        file = entry["_file"]
        name = entry.get("name", "")
        if name and file.stem != name:
            problems.add(file.name, f'filename must match name "{name}" (expected {name}.json)')
        if name in seen:
            problems.add(file.name, f'name "{name}" already listed in {seen[name]}')
        seen[name] = file.name

        versions = entry.get("versions") or []
        numbers = [v.get("version") for v in versions]
        for dupe in {n for n in numbers if numbers.count(n) > 1}:
            problems.add(file.name, f'version "{dupe}" listed more than once')
        for v in versions:
            if branch := branch_ref(v.get("url", "")):
                problems.add(file.name,
                             f'version {v.get("version")}: url points at the branch "{branch}" — '
                             "use a tag or a commit, or the artefact will drift out of its digest")


MOVING_REFS = {"main", "master", "develop", "trunk", "HEAD", "latest"}


def branch_ref(url: str) -> str | None:
    """The moving ref a URL points at, if it is recognisably one.

    Only a heuristic — a tag may be named anything, and plenty of hosts are not
    covered. It catches the mistake that actually happens: linking the default
    branch, which passes CI once and then silently drifts out of its digest.
    """
    parts = urllib.parse.urlsplit(url)
    segments = [s for s in parts.path.split("/") if s]
    candidates = []
    if parts.netloc == "raw.githubusercontent.com" and len(segments) >= 3:
        candidates.append(segments[2])  # /<owner>/<repo>/<ref>/<path>
    # github.com/<o>/<r>/raw|blob/<ref>/…, gitlab /-/raw/<ref>/…, gitea /raw/branch/<ref>/…
    for marker in ("raw", "blob"):
        if marker in segments:
            rest = segments[segments.index(marker) + 1:]
            if rest and rest[0] == "branch":
                rest = rest[1:]
            if rest:
                candidates.append(rest[0])
    return next((c for c in candidates if c in MOVING_REFS), None)


def verify_artefacts(entries: list[dict], problems: Problems) -> None:
    for entry in entries:
        file = entry["_file"]
        for v in entry.get("versions") or []:
            url, want = v.get("url", ""), v.get("sha256", "")
            label = f'version {v.get("version")}'
            try:
                with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as resp:
                    body = resp.read(MAX_ARTEFACT_BYTES + 1)
            except (urllib.error.URLError, OSError, ValueError) as e:
                problems.add(file.name, f"{label}: cannot fetch {url} ({e})")
                continue
            if len(body) > MAX_ARTEFACT_BYTES:
                problems.add(file.name, f"{label}: artefact larger than {MAX_ARTEFACT_BYTES} bytes")
                continue
            got = hashlib.sha256(body).hexdigest()
            if got != want:
                problems.add(file.name, f"{label}: sha256 mismatch — entry says {want}, artefact is {got}")
                continue
            try:
                artefact = json.loads(body)
            except json.JSONDecodeError as e:
                problems.add(file.name, f"{label}: artefact is not valid JSON ({e})")
                continue
            inner = artefact.get("name") if isinstance(artefact, dict) else None
            if inner != entry.get("name"):
                problems.add(file.name,
                             f'{label}: artefact declares name "{inner}", entry says "{entry.get("name")}"')


def build(entries: list[dict]) -> dict:
    plugins = []
    for entry in sorted(entries, key=lambda e: e.get("name", "")):
        plugins.append({k: v for k, v in entry.items() if k != "_file"})
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": datetime.datetime.now(datetime.timezone.utc)
                                .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "plugins": plugins,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true",
                    help="fetch every artefact and check its digest (needs network)")
    ap.add_argument("--check", action="store_true",
                    help="do not write catalog.json; fail if it is out of date")
    ap.add_argument("--out", type=pathlib.Path, default=CATALOG)
    args = ap.parse_args()

    problems = Problems()
    entries = load_entries(problems)
    validate_schema(entries, problems)
    validate_cross(entries, problems)
    if args.verify:
        verify_artefacts(entries, problems)

    catalog = build(entries)
    validate_catalog(catalog, problems)

    if problems:
        print(f"{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    rendered = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not args.out.exists():
            print(f"{args.out.name} missing", file=sys.stderr)
            return 1
        # generated_at moves on every run — compare everything else.
        current = json.loads(args.out.read_text(encoding="utf-8"))
        if current.get("plugins") != catalog["plugins"] or current.get("schema") != catalog["schema"]:
            print(f"{args.out.name} is out of date — run scripts/build_catalog.py", file=sys.stderr)
            return 1
        print(f"{args.out.name} is up to date ({len(entries)} plugin(s))")
        return 0

    args.out.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.out.name}: {len(entries)} plugin(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
