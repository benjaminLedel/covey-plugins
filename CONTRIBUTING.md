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

Alongside errors it prints what your plugin is giving up:

```
redmine.json: ok — manifest plugin "redmine" (ticketing), 2 action(s): comment, get_issue
redmine.json: note — no poll: — nur-wenn: on this system cannot be answered and every heartbeat fires (fail-open)
```

### Declare what you can

A manifest can carry the same optional capabilities a plugin compiled into Covey has. None is mandatory, and each one you leave out costs the operator something concrete:

| Block | What it buys | Without it |
|---|---|---|
| `probe` | one read-only GET plus the field the identity is read from | no connection test — "saved" and "works" stay different things until an agent runs |
| `poll` | one GET per sub-scope plus a field carrying the work signature | `nur-wenn: <system>` in `HEARTBEAT.md` cannot be answered, so every heartbeat fires and wakes an agent for nothing |
| `scopes` | the vocabulary `ACCESS.md` may use | any word is accepted and none of them narrows anything |
| per-action `scope` + `doc` | narrows the prompt doc to what an agent may actually do | every agent carries every action's instructions in the context of every turn |

```json
"scopes": ["read", "comment"],
"probe": {"path": "/users/current.json", "identity_field": "user.login"},
"poll": {
  "": {"path": "/issues.json?assigned_to_id=me&status_id=open",
       "items_field": "issues", "signature_field": "updated_on"}
},
"actions": {
  "get_issue": {"method": "GET", "path": "/issues/{id}.json",
                "scope": "read", "doc": "read one issue including its notes"}
}
```

A note on `poll`: `signature_field` is what keeps an agent from being woken every few minutes for the same piece of news. It should be a per-item value that changes when the item does — an `updated_at`, the id of the newest comment. Leave it out and the condition fires on every tick for as long as the state persists.

A note on `doc`: scope narrowing works on structure, not on prose. If your `prompt_doc` is a block of free text and your actions have no `doc` lines, there is no way to tell which sentence belongs to which action, and the doc is handed over whole no matter what an agent's scopes say.

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
