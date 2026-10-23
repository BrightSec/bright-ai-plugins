# Bright AI Plugins

Bright Security DAST agents and skills, installable the **native way** into every major AI
coding tool from this single repository: Cursor, Claude Code, Codex, GitHub Copilot,
Antigravity CLI, and Kiro.

Every package wires the **same three agents** and **seven skills** to the Bright MCP server:

**Agents**
- `bright-application-testing` — analyze the repo, reach the target (local, staging, or any
  authorized environment), configure Bright, register attack surface, and run DAST scans
  (through a Repeater for private/local targets).
- `bright-remediation-loop` — run DAST, apply minimal fixes, restart, and re-run the same
  validation scans until findings are gone.
- `bright-discovery` — analyze the repo, reach the target, build the endpoint list from the code,
  register the endpoints in Bright with values that pass validation, and report what it couldn't
  register and why — no scanning, no code changes.

**Skills**
- `analyze-codebase`, `setup-repeater`, `setup-auth`, `register-entrypoints`, `compose-har`, `run-scan`, `fix-and-validate`

## Packages

Each tool has its own package with native install, usage, update, and uninstall steps in its
README:

- **Cursor** — [`cursor/`](./cursor/)
- **Claude Code** — [`claude-code/`](./claude-code/)
- **Codex** — [`codex/`](./codex/)
- **GitHub Copilot** — [`github-copilot/`](./github-copilot/)
- **Antigravity CLI** — [`antigravity/`](./antigravity/)
- **Kiro** — [`kiro/`](./kiro/)

The `claude-code/` package is the canonical source the others mirror. Codex, Antigravity, and Kiro
have no separate agent type, so their three orchestration workflows ship as skills (for Kiro,
because the Agent Plugins format it uses has no portable agent component — only skills and MCP
servers).

Marketplace manifests live at the repo root — `.cursor-plugin/marketplace.json`,
`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
`.github/plugin/marketplace.json` — all indexing the marketplace `brightsec` and the plugin
`bright-security`.

## Required environment (all packages)
- `BRIGHT_HOSTNAME` — Bright cluster hostname, host only, no `https://` (e.g. `app.brightsec.com`)
- `BRIGHT_TOKEN` — Bright API token (used by the MCP server and the Bright CLI Repeater)
- **A Bright project** — everything a run creates (Repeater, auth object, entrypoints, scans)
  is scoped to one project. With a **project-scoped** `BRIGHT_TOKEN` there is only one project
  to reach, so the agents use it and tell you which; you never need to name it. With an
  org-wide token, name the project when you start — the agents ask rather than guess, because
  guessing wrong writes your scan results into someone else's project.

```bash
export BRIGHT_HOSTNAME="app.brightsec.com"
export BRIGHT_TOKEN="your-bright-api-token"
```

Each package's `README.md` has the tool-specific install steps and MCP notes (some tools
expand env vars in MCP config; Codex and Copilot need the token wired differently — the
package READMEs cover it).

## What you can do with it

A scanner pointed at a URL can tell you *that* an endpoint is injectable. These agents run
where the code is, so a finding comes back attached to the handler that caused it — and the
second agent closes the loop by proving the fix, instead of leaving you a report.

### Which agent

| | `bright-application-testing` | `bright-remediation-loop` | `bright-discovery` |
| --- | --- | --- | --- |
| Does | Scans and reports | Scans, edits code, re-scans until the finding is gone | Discovers attack surface and registers entrypoints |
| Touches your code | No | **Yes** | No |
| Also needs | — | A way to get fixes into the running target | — |
| Reach for it when | You want to know what's exposed | You want it fixed and the fix proved | Your targets are hard to crawl, you lack Swagger/HAR files, or you want the endpoints from your code registered and checked before scanning |

The remediation loop's value is the *proof*: a finding counts as fixed only when the same scan,
over the same entrypoints and tests, stops reporting it. That requires your edited code to be
running in the target, so if it can't redeploy, it says so before scanning rather than handing
you unverified patches.

### 1. See what a branch exposes before it merges

You added endpoints and want to know what they opened up.

```
> Use the bright-application-testing agent to scan this app, Bright project "acme-api"
```

It reads your routes and controllers, works out realistic request bodies, excludes endpoints
whose effects can't be undone, registers the rest, picks tests from the Bright catalogue for
what each endpoint actually does, and scans. You get findings grouped by severity with the
method, URL, evidence, and the endpoint each one belongs to.

The examples below name a project because an org-wide token can reach many. On a project-scoped
token, drop that part — there is only one project and the agent uses it.

### 2. Scan an environment that's already deployed

Your app runs on staging and you don't want anything started locally.

```
> Scan https://staging.acme.example with bright-application-testing, project "acme-api".
> It's already running — don't start anything.
```

Given a URL, the agent health-checks it and skips startup entirely. A publicly reachable target
is scanned directly; anything private goes through a Repeater that runs **on your machine**, so
the target has to answer from there — over the local network, a VPN, or a tunnel you already
have up.

### 3. Get past the login page

Most of an API's surface sits behind auth, and an unauthenticated scan never sees it.

```
> Scan this API with bright-application-testing, project "acme-api".
> Test credentials are in fixtures/users.json.
```

The agent finds your login flow, builds an auth object, and verifies it works *before* saving
it, retrying against the real endpoint until the login succeeds. It sets re-auth on `401`/`403`
so sessions expiring mid-scan don't quietly turn the rest of the run into noise.

### 4. Fix the findings and prove they're gone

```
> Use bright-remediation-loop on this repo, project "acme-api".
> Redeploy with `make deploy-dev`.
```

It scans, traces each finding from the request to the vulnerable sink, applies the smallest fix
that removes it, redeploys, then re-runs the *same* scan and compares. Findings that disappear
are reported as fixed; ones that survive stay open for the next round. You get the list of files
changed alongside the evidence that each change worked.

Tell it how to redeploy — without that it can scan and write fixes but can't verify them, and it
will stop and ask before spending a scan rather than reporting unverified edits as remediated.

### 5. Map the attack surface without scanning

Your targets crawl poorly, you have no Swagger spec, and you don't want to hand-build HAR
files. The discovery agent reads the code, builds the endpoint list from it, works out parameter
values that pass validation, and registers them in Bright — ready for a scan later.

```
> Use the bright-discovery agent to discover and register this app's endpoints, Bright project "acme-api"
```

It reads routes, handlers, and DTOs, reaches the target, and registers each endpoint directly
with realistic parameter values. It collapses duplicates of the same operation, skips static
assets (keeping JavaScript), crawls only to fill gaps the code cannot show, and prunes anything
that doesn't connect. You get a checked entrypoint list — IDs, methods, URLs, populated
parameters, health — with unhealthy entrypoints and gaps named. No scan is run.

### If your app doesn't start with `docker compose`

Say how it runs and the agents follow that instead of guessing from the repository. A
`Dockerfile` that exists for CI is not how your app is deployed, and starting a local copy of an
app you asked about on staging scans the wrong thing.

```
> Bring it up with `helm install acme ./chart --values dev.yaml`, then scan it.
```

## Keeping the packages in sync
Every package ships the same seven step skills and three orchestration agents. Only the
frontmatter differs per tool — Copilot's agents carry an `mcp-servers` block, Codex and
Antigravity carry the agents as skills without an `argument-hint`. The instructions below the
frontmatter must be identical everywhere, so a change to one package has to reach all of them.

`claude-code` is the canonical copy. Edit it, then propagate:

```bash
python3 scripts/check_package_sync.py --fix   # propagate, then review the result
python3 scripts/check_package_sync.py         # verify; this is what CI runs
```

The check also fails on a component it doesn't know about, so a new package or skill can't
be added while silently sitting outside the check. It also fails when the plugin and
marketplace manifests disagree on the plugin or marketplace name, or on the version — bump all
of them together.

## Safety
Only scan targets you own or are explicitly authorized to test — a local dev server, a
staging/QA environment, or any host you're authorized to assess. The agents ask for
confirmation before scanning a target that isn't obviously yours. Reach private or local
targets through a Bright Repeater; publicly reachable targets can be scanned directly. DAST
sends real attack traffic, so authorization is the operator's responsibility.

## License
MIT © [Bright Security](https://brightsec.com)
