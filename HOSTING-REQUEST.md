# Hosting Request: PSE Orchestrator Support Assistant

**Requestor:** Dinesh Kumar (dinesh.kumar@uipath.com)
**What:** Host a small internal static web tool on an internal UiPath subdomain, behind company SSO.

---

## The ask

Please host a single self-contained static HTML page at an internal subdomain such as:

> **https://pseinsights.staging.uipath.com/**  (or a similar internal hostname you prefer)

…and gate it behind **UiPath SSO / internal-network access** so only UiPath employees can reach it.

## What the tool is

An interactive "PSE Support Assistant" — a decision-tree intake wizard that walks support engineers through UiPath Orchestrator **install / upgrade / migration / tenant onboarding / troubleshooting** checklists. It's used internally by the PSE team to standardize case handling.

## Why it's trivial to host

- **One file**, ~78 KB: `index.html`
- **100% static** — all HTML, CSS, and JavaScript are inline in that single file
- **No backend, no API calls, no database, no build step, no dependencies**
- Runs entirely client-side in the browser; nothing to deploy but the file itself
- No secrets or customer data in the content (procedural reference material only)

## Working demo (public, temporary)

A live preview is currently running on GitHub Pages so you can see exactly what it does:

> https://dinesh12nov.github.io/uipath-orchestrator-assistant/

*(This public URL is only a stopgap for review — the goal is to move it to an SSO-gated internal UiPath subdomain and retire the public one.)*

## What I can provide

- The `index.html` file (or a Git repo / zip)
- Any format your platform/hosting pipeline prefers (static bucket, internal web server, internal Pages, etc.)

## Requested outcome

1. An internal, SSO-gated subdomain — e.g. `pseinsights.staging.uipath.com` (or a similar official internal hostname you recommend)
2. Access restricted to UiPath employees (SSO or internal network)
3. Ability for me to push updates (or a simple hand-off process to update the single HTML file)

## Two things I need help confirming

- **Who owns / manages `uipath.host`?** I found that `uipath.host` is registered via Cloudflare and that `pseinsights.staging.uipath.host` already resolves. I don't have access to it and can't confirm it's an official UiPath-controlled domain. Please confirm whether it's legitimate and internal — and if so, who administers it — before anything is hosted there. (If it is *not* an official UiPath domain, please flag it to security.)
- **The right hosting path.** If `uipath.host` (or another internal domain) is on Cloudflare, the simplest option is Cloudflare Pages for the static file + Cloudflare Access restricted to `@uipath.com`. I'm happy to work with whatever your platform pipeline prefers.
