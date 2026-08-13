# Security

This repository is an **index**. It stores no plugin code — each entry points at an artefact hosted by its publisher and pins it by `sha256`. That shapes what can go wrong here and what can be done about it.

## Reporting

| What you found | Where it goes |
|---|---|
| A listed plugin behaves maliciously or misleadingly | Open an issue here, or write to the address below if disclosing it publicly would put installations at risk |
| A bug in a plugin | The plugin's own issue tracker — its `homepage` in the entry |
| A flaw in the index tooling (schema, build script, workflows) | Here |
| A vulnerability in Covey itself | The [Covey repository](https://github.com/benjaminLedel/covey) |

For anything that should not be public first: **youcloud.server@googlemail.com**. Please include the plugin name, the version, and what an installation would actually experience.

## What withdrawal does, and what it does not

An entry can be removed from the catalogue. That stops **further installations** — it does not reach into instances where the plugin is already installed. An organisation running a withdrawn plugin has to remove it themselves, and nobody here can do it for them.

This is a deliberate property, not a gap. A catalogue that could reach into a running instance would be a far larger risk than the one it was protecting against: the same channel that removes a bad plugin can install one. Covey instances therefore never act on the catalogue by themselves — installing and updating both require a person.

If you operate an instance and a plugin you installed is withdrawn, you will see it in the store. Removing it there is the fix.

## The trust model in one paragraph

Every version is pinned by digest, so the linked repository may be force-pushed, retagged or deleted without changing what installs — a changed artefact stops installing rather than silently becoming something else. Published versions are append-only; a fix is a new version. Every change that ever reaches an instance is a merge here, which makes the pull-request history the audit trail. Nothing in this index is signed beyond that today (see the open points in [Covey's spec](https://github.com/benjaminLedel/covey/blob/main/spec/22-plugin-marketplace.md)); the digest plus a reviewed merge is what carries it.

## What the index will not distribute

- **Executable code.** No binaries, no WASM. Manifests and MCP configurations only — data. This is a hard rule.
- **Credentials.** No tokens, keys or account details, in entries or in artefacts.

## What a listed plugin can actually reach

A **manifest** plugin cannot name a host. Its action paths are relative, and the base URL comes from the credential the installing organisation stored (`<name>_url`). A hostile entry therefore cannot redirect a brokered token to a server of its choosing — at worst it calls unintended endpoints of the system the organisation already pointed it at, where Covey's guard rails apply.

An **MCP** plugin does name its endpoint. That host is what review focuses on, it is displayed at install time, and it has to pass the installing organisation's egress allowlist. If you are reviewing an MCP entry, this is the field to look at.
