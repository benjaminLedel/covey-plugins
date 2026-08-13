---
name: Request a target system
about: A system you would like to see in the catalogue but do not want to write yourself
title: "request: <system name>"
labels: ["request"]
---

**System:** <!-- Redmine, Jira, OpenProject, … -->
**Its API docs:** <!-- link -->

**What an agent should be able to do with it**

<!--
Actions, in the order they matter. "Read an issue, comment on it, change its
status" is enough to start from — this becomes the plugin's action list.
-->

**How work would arrive**

- [ ] The system can call a webhook
- [ ] It can only be polled (an agent checks on a heartbeat)
- [ ] I do not know

**How it authenticates**

- [ ] An API token in a header
- [ ] OAuth2, or something else — <!-- describe -->

<!--
Worth knowing before anybody starts: a plugin distributed through this catalogue
is a JSON manifest interpreted by Covey's REST engine, or an MCP server
configuration. A system that speaks plain REST/JSON with a token in a header
fits. OAuth flows, non-JSON protocols (IMAP, WebDAV) or real logic (parsing,
merging sources) need a plugin compiled into Covey instead — that request
belongs in the Covey repository.
-->
