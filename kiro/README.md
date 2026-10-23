# Bright Security — Kiro power

Bright DAST (Dynamic Application Security Testing), packaged for Kiro as a **power** (Agent
Plugins 1.0.0). The power wires three orchestration workflows and seven skills to the **Bright MCP
server**, so Kiro can analyze an app, reach a target, register attack surface, run scans, and
remediate findings — in the Kiro IDE or the Kiro CLI.

Agent Plugins 1.0.0 defines only two portable component types — **skills** and **MCP servers** —
so the three orchestration workflows ship as **keyword-activated skills**, not as a separate agent
type. The power is **10 skills** (7 building-block skills + 3 orchestration skills) plus the Bright
MCP server.

## What's inside

- **Orchestration skills** (`skills/`) — ask for one and Kiro activates it:
  - `bright-application-testing` — analyze the repo, reach the target, configure Bright, register
    attack surface, and run DAST scans (through a Repeater for private/local targets).
  - `bright-remediation-loop` — run DAST, apply minimal fixes, restart, and re-run validation
    scans until findings are gone.
  - `bright-discovery` — analyze the repo, reach the target, build the endpoint list from the
    code, register the endpoints in Bright with values that pass validation, and report what it
    couldn't register and why — no scanning, no code changes.
- **Building-block skills** (`skills/`) — `analyze-codebase`, `setup-repeater`, `setup-auth`,
  `register-entrypoints`, `compose-har`, `run-scan`, `fix-and-validate`. The orchestration skills
  call these as building blocks.
- **MCP** (`mcp.json`) — the Bright MCP server (`brightsec`) over the portable `streamable-http`
  transport.

All ten skill bodies are the same instructions the other packages ship; `claude-code` is the
canonical copy they all mirror.

---

## Required environment

- `BRIGHT_HOSTNAME` — Bright cluster hostname, host only, no `https://` (e.g. `app.brightsec.com`)
- `BRIGHT_TOKEN` — Bright API token (used by the MCP server and the Bright CLI Repeater)
- **A Bright project** — everything a run creates (Repeater, auth object, entrypoints, scans) is
  scoped to one project. With a **project-scoped** `BRIGHT_TOKEN` there is only one project to
  reach, so the skills use it and tell you which; you never name it. With an **org-wide** token,
  name the project when you start — the skills ask rather than guess, because guessing wrong writes
  your scan results into someone else's project.

```bash
export BRIGHT_HOSTNAME="app.brightsec.com"   # your Bright cluster hostname
export BRIGHT_TOKEN="your-bright-api-token"  # your Bright API token
```

Export these in the environment Kiro launches from — the MCP server reads them when it connects,
so set them before launching, not mid-session. For a long-lived org-wide token, prefer a secret
manager (OS keychain, 1Password, `pass`, or a cloud secrets manager) over a plaintext value in a
shell startup file or a synchronized dotfile. A **project-scoped** token limits the blast radius if
it leaks.

---

## Install

The repository is only the **source** of the power. Installing it copies the power into Kiro's own
storage, so it is available regardless of where this repo lives — you don't run it "from" the repo.
There are two surfaces, the Kiro IDE and the Kiro CLI, and each installs the power its own way.

Before installing on either surface, export `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` in the environment
Kiro launches from — Kiro expands these references when the bundled MCP server connects.

### A) Kiro CLI (`kiro-cli powers install`)

The CLI installs a power with one command. Its argument is a **catalog name** or a **local
filesystem path** — a GitHub URL is **not** accepted, so install from a clone of this repo and
point at the `kiro/` subdirectory:

```bash
git clone https://github.com/NeuraLegion/bright-ai-plugins
kiro-cli powers install ./bright-ai-plugins/kiro
# → Installed power "bright-security"
```

That's the whole install. The CLI copies the power into `~/.kiro/powers/installed/bright-security/`
(all ten skills plus `mcp.json`) and records it in `~/.kiro/powers/installed.json`. The bundled
`brightsec` MCP server travels with the power and connects automatically — you do **not** hand-edit
any MCP config file, and you do **not** copy skills into `~/.kiro/skills/`.

Verify it loaded: start a chat and confirm the power is wired up.

```bash
kiro-cli chat
# then, inside the session:
/mcp              # shows the brightsec server status and its tools
/                 # lists the ten skills as slash commands
```

The `brightsec` tools are available to the agent once the power is installed and the two
environment variables are set. You can also just ask for a workflow in plain language (see
**Use**). To remove the power later, see **Uninstall**.

> Catalog name: once Bright Security is accepted into Kiro's curated **Available Powers** registry,
> `kiro-cli powers install bright-security` (by name, no clone) will also work. It is **not yet**
> in the registry — install from a local clone for now.

### B) Kiro IDE (Powers panel)

1. Open the **Powers** panel.
2. Add the power from either source:
   - **Local Path** — select this repository's `kiro/` folder from a clone. (Verified to work.)
   - **GitHub** — import from the repository
     (`https://github.com/NeuraLegion/bright-ai-plugins`), selecting the `kiro/` subdirectory on a
     Kiro build that supports choosing a subdirectory power.
3. When a power carries an MCP server, **Kiro stores and manages that server for you** and
   namespaces its name to avoid conflicts with other powers. After install, confirm the Bright
   tools and the ten skills are available, and approve the server's use of your environment
   variables if Kiro prompts.

Discovery note: kiro.dev hosts a curated **Available Powers** registry with a one-click "Add to
Kiro" install. Bright Security is **not yet** published there, so install from a local folder or
the GitHub repo for now (the repo can be submitted to the registry via `kiro.dev/powers/submit`).

---

## Use

Ask for a workflow in plain language and Kiro activates the matching skill — there is no `--agent`
to pass, these are skills:

```
Use bright-application-testing to scan this app
Use bright-remediation-loop to scan, fix, and re-verify
Use bright-discovery to discover and register this app's endpoints
```

You can also invoke any of the ten skills explicitly from the `/` slash-command menu. Scan any
target you own or are authorized to test (local, staging, or another authorized environment). Reach
private/local targets through a Repeater — the `bright-application-testing` and
`bright-remediation-loop` workflows set one up for you.

---

## Why the three workflows ship as skills

Agent Plugins 1.0.0 has no portable "agent" component — only skills and MCP servers — so the three
orchestration workflows are packaged as keyword-activated skills. The instructions are the same
ones the other tools' agents carry; Kiro activates them on a matching request or from the `/` menu.

---

## Portability caveat (MCP auth)

The bundled `kiro/mcp.json` keeps `${BRIGHT_HOSTNAME}` / `${BRIGHT_TOKEN}` as references, matching
every other package in this repo. The Agent Plugins spec (§7.2.1) says a strictly conformant client
MUST NOT expand placeholders or environment variables in a server `url` or in header names/values —
so a strict non-Kiro client would send the literal `${BRIGHT_TOKEN}` and be rejected. This power
works on Kiro by design: Kiro expands the references from the environment when the managed MCP
server connects. This is an intentional, Kiro-specific tradeoff, called out here rather than hidden.

---

## Update / Uninstall

- **CLI update:** `git pull` in the clone, then reinstall over the current copy from the clone
  root — `kiro-cli powers install ./kiro`.
- **CLI uninstall:** `kiro-cli powers uninstall bright-security`. This removes the power from
  `~/.kiro/powers/installed/` and `installed.json`; the bundled MCP server goes with it, so there
  is no separate MCP config to clean up.
- **IDE:** manage, update, or remove the power from the Powers panel; Kiro also manages the bundled
  MCP server's lifecycle for you.
- **Troubleshooting:** confirm both variables are set before launching Kiro — check that the token
  is present **without printing it** (the same way `setup-repeater` does):

  ```bash
  test -n "$BRIGHT_TOKEN" && echo "BRIGHT_TOKEN: set" || echo "BRIGHT_TOKEN: MISSING"
  test -n "$BRIGHT_HOSTNAME" && echo "BRIGHT_HOSTNAME: $BRIGHT_HOSTNAME" || echo "BRIGHT_HOSTNAME: MISSING"
  ```

  In a CLI chat, `/mcp` shows the `brightsec` connection status and its tools; an auth failure
  shows up as a connection failure for that server (rotate the token and restart). If only the
  Repeater fails, test the Bright CLI directly:

  ```bash
  npx @brightsec/cli repeater --id <REPEATER_ID> --hostname "$BRIGHT_HOSTNAME" --token "$BRIGHT_TOKEN"
  ```

---

## Verification status

Verified live on **Kiro CLI 2.32.0** (macOS, arm64):

- `kiro-cli powers install ./kiro` installs the power (`Installed power "bright-security"`), landing
  all ten skills + `mcp.json` under `~/.kiro/powers/installed/bright-security/` and recording it in
  `installed.json`;
- the agent sees all ten skills by name;
- the bundled `brightsec` MCP server connects and responds — a `listProjects` call returned live
  Bright projects using `BRIGHT_HOSTNAME` / `BRIGHT_TOKEN` from the environment, with no manual MCP
  config step;
- `kiro-cli powers install` rejects a GitHub URL / `owner/repo` reference — only a catalog name or
  local path is accepted (hence the clone-then-path flow above);
- `kiro-cli powers uninstall bright-security` removes it cleanly.

Not yet confirmed on a running instance (documented from Kiro's docs, pending a live pass):

- the IDE Powers-panel import from the `kiro/` subdirectory and its approved-environment-variables
  prompt;
- the exact namespaced server name Kiro assigns to the managed `brightsec` server;
- installation by catalog name (requires registry acceptance first).

The portable schema conformance (both manifests), the `streamable-http` transport value, the name
`bright-security`, the version `0.2.0`, and the byte-for-byte identity of the ten skill bodies with
the canonical `claude-code` copies are all verified by the repository's package-sync check.

---

## Safety

Only scan targets you own or are explicitly authorized to test — a local dev server, a staging/QA
environment, or any host you're authorized to assess. DAST sends real attack traffic, so
authorization is your responsibility. Reach private or local targets through a Bright Repeater (the
workflow sets one up and tears it down); publicly reachable targets can be scanned directly. Provide
`BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` through your environment, and never commit a file with a real
token.

## License
MIT © [Bright Security](https://brightsec.com)
