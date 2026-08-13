# Listing a plugin

A listing is a pull request that adds or extends one file under `plugins/`. Your plugin itself stays in your own repository.

## 1. Publish the artefact

Keep the manifest (or MCP configuration) in your repository and reference it at an **immutable** URL — a tag or a commit SHA, never a branch:

```
https://raw.githubusercontent.com/example-gmbh/covey-redmine/v1.2.0/covey/redmine.json   ✅
https://raw.githubusercontent.com/example-gmbh/covey-redmine/main/covey/redmine.json     ❌
```

A branch URL will pass CI once and then quietly drift out of its digest.

Compute the digest:

```sh
curl -sL <url> | shasum -a 256
```

## 2. Check the plugin locally

```sh
covey plugin lint covey/redmine.json
```

This is the same check CI runs, and the same one Covey applies at install time: schema, action methods, path form, webhook fields. Unknown fields are an error, not a warning — a typo in a field name would otherwise become a silently missing feature.

## 3. Write the entry

`plugins/<name>.json`, where `<name>` matches the `name` inside your artefact and the filename:

```json
{
  "name": "redmine",
  "label": "Redmine",
  "description": "Issue tracker: read issues, comment, change status.",
  "category": "ticketing",
  "kind": "custom",
  "publisher": "example-gmbh",
  "homepage": "https://github.com/example-gmbh/covey-redmine",
  "license": "MIT",
  "versions": [
    {
      "version": "1.2.0",
      "url": "https://raw.githubusercontent.com/example-gmbh/covey-redmine/v1.2.0/covey/redmine.json",
      "sha256": "9f2b…",
      "covey_min_version": "0.9.0"
    }
  ]
}
```

| Field | Notes |
|---|---|
| `name` | `^[a-z][a-z0-9_-]{1,31}$`, unique across the catalogue. It is also the credential prefix (`redmine_token`, `redmine_url`), the word used in an agent's `ACCESS.md`, and the guard-rail subject prefix — so pick the target system's plain name, not a product name of your own. |
| `label` | what a person sees in the store. |
| `description` | one sentence, what an agent can do with it. Not a pitch. |
| `category` | one of `ticketing`, `code`, `communication`, `files`, `web`, `dev`, `other`. |
| `kind` | `custom` (manifest) or `mcp` (MCP server). `builtin` is reserved for plugins compiled into Covey. |
| `publisher` | you — an organisation or a person, stable across your plugins. |
| `homepage` | where the source, the issues and the setup instructions live. Required: a plugin whose origin cannot be checked will not be merged. |
| `license` | an SPDX identifier. |
| `versions` | newest first, append-only. |
| `covey_min_version` | the oldest Covey release that can interpret the artefact. Leave it out if you are not sure and it uses nothing recent. |

Validate and build the catalogue the way CI does:

```sh
python3 scripts/build_catalog.py --verify
```

`--verify` fetches every artefact and checks its digest, so it needs network access. Without the flag the script validates the entries and writes `catalog.json` offline.

## 4. Open the pull request

CI checks the entry against the schema, the name against the rest of the catalogue, fetches the artefact, verifies the digest and the name inside it, and lints the plugin. On merge, `catalog.json` is regenerated automatically — **do not** edit it in your pull request.

## Releasing a new version

Add an entry to `versions`, do not touch the existing ones. A published version is immutable: instances have pinned it, and rewriting it would change what they believe they installed. Withdrawing a bad version is a separate pull request that removes it, and it prevents new installations only — it does not reach into instances that already have it.

## Review criteria

- The artefact matches its digest and lints cleanly.
- `homepage` leads to real source, with an issue tracker.
- The description matches what the actions actually do.
- MCP entries: the endpoint host is stated and plausible. Expect questions here — an MCP configuration names a host, and installing it means an organisation opens its egress to that host.
- No credentials, tokens or personal data anywhere in the entry or the artefact.

## Removing a plugin

Publishers may withdraw their own entries at any time. Anyone may report a plugin by opening an issue; entries that turn out to be misleading or hostile are removed and the reason recorded in the pull request that removes them.
