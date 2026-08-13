<!--
Adding or updating a plugin? Everything below applies. Changing the tooling,
the schema or the docs instead? Delete the checklist and describe the change.
-->

## What this changes

<!-- New listing / new version / withdrawal — and for a new version, what changed in the plugin. -->

## Checklist

- [ ] `plugins/<name>.json` — one file, filename matches the `name` inside it
- [ ] The artefact URL points at a **tag or commit**, never a branch
- [ ] `sha256` matches the artefact (`curl -sL <url> | shasum -a 256`)
- [ ] `covey plugin lint <artefact>` passes, and I have read its notes
- [ ] `python3 scripts/build_catalog.py --verify` passes locally
- [ ] `homepage` leads to the source and an issue tracker
- [ ] For a new version: existing `versions` entries are untouched
- [ ] `catalog.json` is **not** in this pull request — CI generates it

## For MCP entries only

- [ ] The endpoint host is: <!-- host here -->
- [ ] I understand that installing this opens an organisation's egress to that host

## Anything a reviewer should know

<!-- Rate limits, auth quirks, which Covey version this needs, why a capability is missing. -->
