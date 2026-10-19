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
shell startup file or a synchronized dotfile; if you do put it in `~/.zshrc` / `~/.bashrc`, keep
that file off shared machines and out of version control. A **project-scoped** token limits the
blast radius if it leaks.

---

## Install

The repository is only the **source** of the power. You install it at the user/system level and
it is then available across your workspaces. There are two surfaces — the Kiro IDE and the Kiro
CLI — and they wire the power differently.

### A) Kiro IDE (Powers panel)

1. **Export `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN`** in the environment Kiro launches from.
2. **Install the power** from the **Powers** panel. Point it at this repository's `kiro/` folder —
   either a local clone's `kiro/` directory, or the GitHub repository
   (`https://github.com/NeuraLegion/bright-ai-plugins`, selecting the `kiro/` subdirectory where
   your Kiro build supports choosing a subdirectory power). The power installs at the user/system
   level, so it is available across workspaces.
3. On install, when a power carries an MCP server, **Kiro stores and manages that server for you**
   and namespaces its name to avoid conflicts with other powers. After install, confirm the Bright
   tools and the ten skills are available, and approve the server's use of your environment
   variables if Kiro prompts.

Discovery note: kiro.dev hosts a curated **Available Powers** registry with a one-click "Add to
Kiro" install. Bright Security is **not yet** published there, so install from this GitHub repo
URL or a local folder for now (the repo can be submitted to the registry later via
`kiro.dev/powers/submit`).

### B) Kiro CLI (user/global level, all workspaces)

The Kiro CLI does not auto-manage a power's bundled MCP server, so wire the two pieces — skills
and the MCP server — at the user level yourself. Kiro auto-discovers both from `~/.kiro`.

1. **Export `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN`.**
2. **Skills** — copy (or symlink) the ten skill directories into the user-level Kiro skills
   directory, which Kiro auto-discovers:

   ```bash
   git clone https://github.com/NeuraLegion/bright-ai-plugins
   mkdir -p ~/.kiro/skills
   cp -R bright-ai-plugins/kiro/skills/* ~/.kiro/skills/   # or symlink each dir for live updates
   ```

   `~/.kiro/skills/<name>/SKILL.md` is the global location; `.kiro/skills/<name>/SKILL.md` is the
   per-workspace equivalent, and the workspace copy wins on a name conflict.
3. **MCP server** — add the `brightsec` server to the user-level Kiro MCP config
   `~/.kiro/settings/mcp.json` (per-workspace equivalent `.kiro/settings/mcp.json`; workspace
   wins). Use Kiro's **native** MCP shape — Kiro expands `${BRIGHT_HOSTNAME}` / `${BRIGHT_TOKEN}`
   from the environment here, so the same exported variables drive both the MCP server and the
   Repeater. **Merge** into any existing `mcpServers` object rather than overwriting it:

   ```json
   {
     "mcpServers": {
       "brightsec": {
         "url": "https://${BRIGHT_HOSTNAME}/mcp",
         "headers": {
           "Authorization": "Api-Key ${BRIGHT_TOKEN}"
         }
       }
     }
   }
   ```

   `type` can be omitted for a remote server (as shown); `type: "http"` is also accepted. Use plain
   `${VAR}` references, not the `${env:VAR}` prefix.
4. **Verify** — run `/mcp` to see the `brightsec` server status and its tools, and `/context show`
   (or type `/`) to confirm the ten skills loaded. The CLI hot-reloads the MCP config on save.

Path note: these are the documented defaults. Kiro resolves agents, skills, settings, and sessions
against `~/.kiro`, and honors `KIRO_HOME` when it is set — verify the exact paths with `/mcp` and
`/context show` in your Kiro CLI version. Two upstream caveats worth knowing: `KIRO_HOME`
consistency mid-session is still being settled, and a custom `--agent` profile may not auto-discover
`~/.kiro/skills` the way the default agent does — this power ships skills, so the default agent sees
all ten.

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
works on Kiro by design: Kiro resolves the references through its own MCP management (IDE), or you
wire the native config that Kiro expands from the environment (CLI, step B.3). This is an
intentional, Kiro-specific tradeoff, called out here rather than hidden.

---

## Advanced / Update / Uninstall

- **IDE:** manage or remove the power from the Powers panel; Kiro also manages the bundled MCP
  server's lifecycle for you.
- **CLI update:** `git pull` the repo and re-copy the skill directories (or rely on symlinks for
  live updates). The MCP config is a one-time edit.
- **CLI uninstall:** remove the ten `~/.kiro/skills/*` directories you copied and delete the
  `brightsec` entry from `~/.kiro/settings/mcp.json`.
- **Troubleshooting:** confirm `echo $BRIGHT_HOSTNAME` and `echo $BRIGHT_TOKEN` are set before
  launching; `/mcp` shows the connection status; an auth failure shows up as a connection failure
  for that server (rotate the token and restart). If only the Repeater fails, test the Bright CLI
  directly:

  ```bash
  npx @brightsec/cli repeater --id <REPEATER_ID> --hostname "$BRIGHT_HOSTNAME" --token "$BRIGHT_TOKEN"
  ```

---

## Verification status

The install flow above is documented from Kiro's own docs and corroborating setup guides, not yet
confirmed on a running Kiro instance. These specific points still need a live acceptance pass before
they become guarantees rather than documented expectations:

- importing the power from the `kiro/` subdirectory of a GitHub repo in the Powers panel;
- the approved-environment-variables prompt and how it propagates to the managed MCP server;
- skill/workflow activation by keyword and from the `/` menu;
- the end-to-end MCP connection to Bright;
- the exact namespaced server name Kiro assigns to the managed `brightsec` server.

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
