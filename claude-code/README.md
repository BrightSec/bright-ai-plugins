# Bright Security — Claude Code plugin

Bright DAST (Dynamic Application Security Testing) agents and skills, packaged for Claude Code.
The plugin wires three orchestration agents and seven skills to the **Bright MCP server**, so Claude
Code can analyze an app, reach a target, register attack surface, run scans, and remediate
findings — all from your terminal.

## What's inside
- **Agents** (`agents/`)
  - `bright-application-testing` — analyze the repo, reach the target, configure Bright, register
    attack surface, and run DAST scans (through a Repeater for private/local targets).
  - `bright-remediation-loop` — run DAST, apply minimal fixes, restart, and re-run validation
    scans until findings are gone.
  - `bright-discovery` — analyze the repo, reach the target, build the endpoint list from the
    code, register the endpoints in Bright with values that pass validation, and report what it
    couldn't register and why — no scanning, no code changes.
- **Skills** (`skills/`) — `analyze-codebase`, `setup-repeater`, `setup-auth`,
  `register-entrypoints`, `compose-har`, `run-scan`, `fix-and-validate`. The agents call these as
  building blocks.
- **MCP** (`.mcp.json`) — the Bright MCP server over HTTP.

---

## Install

**1. Export your Bright credentials** in the shell you launch `claude` from (the MCP server and the
Bright Repeater both read them, and the MCP server reads them at startup — so set them before
launching, not mid-session):

```bash
export BRIGHT_HOSTNAME="app.brightsec.com"   # your Bright cluster hostname
export BRIGHT_TOKEN="your-bright-api-token"  # your Bright API token
```

Add them to `~/.zshrc` / `~/.bashrc` so every session has them. The agents check both up front and
stop with a clear message if one is missing; the token is never requested in the conversation.

**2. Install the plugin** from the marketplace:

```bash
claude plugin marketplace add BrightSec/bright-ai-plugins
claude plugin install bright-security@brightsec
```

That's it — the plugin is enabled on install. Verify with `claude plugin list` (should show
`bright-security@brightsec → enabled`), or inside a session run `/agents` to see the three Bright
agents.

---

## Use

Ask for an agent in plain language — Claude delegates to it:

```
> Use the bright-application-testing agent to scan this app
> Use the bright-remediation-loop agent to scan, fix, and re-verify
> Use the bright-discovery agent to discover and register this app's endpoints
```

Or **@-mention** it to guarantee that exact agent runs:

```
> @"bright-application-testing (agent)" scan this app
```

Or **run the whole session as the agent**, so its system prompt, tools, and model drive everything:

```bash
claude --agent bright-application-testing
```

Scan any target you own or are authorized to test (local, staging, or another authorized
environment). Reach private/local targets through a Repeater — the agent sets one up for you.

---

## Advanced usage & options

### Run a scan without permission prompts

A full scan runs many shell commands and MCP calls. To avoid approving each one, pre-allow the
Bright MCP tools plus the tools the agent needs in `.claude/settings.json`:

```json
{
  "agent": "bright-application-testing",
  "permissions": {
    "allow": [
      "mcp__plugin_bright-security_brightsec__*",
      "Bash",
      "Read",
      "Write",
      "Edit"
    ]
  }
}
```

Setting `"agent"` also makes this agent the default for the project, so a bare `claude` starts as
it. `mcp__plugin_bright-security_brightsec__*` covers every Bright MCP tool (`runScan`,
`runDiscovery`, `createRepeater`, `listProjects`, …). To skip prompts entirely for a one-off run,
launch with `--permission-mode bypassPermissions` instead — use it only against targets you own,
since the agent then acts fully autonomously.

### Use without installing

You can load the agents, skills, and MCP server directly from a clone — handy for trying it out,
pinning a specific commit, or air-gapped setups. `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` still need to
be exported.

```bash
git clone https://github.com/BrightSec/bright-ai-plugins
```

**Option A — drop into a project (native `--agent` support).** Copy the components into your
project's `.claude/` directory and the MCP config into the project root:

```bash
cd /path/to/your-project
mkdir -p .claude/agents .claude/skills
cp -r /path/to/bright-ai-plugins/claude-code/agents/*  .claude/agents/
cp -r /path/to/bright-ai-plugins/claude-code/skills/*  .claude/skills/
cp    /path/to/bright-ai-plugins/claude-code/.mcp.json .mcp.json

claude --agent bright-application-testing
```

Claude Code auto-discovers `.claude/agents/`, `.claude/skills/`, and the project `.mcp.json`, so
everything is available with no marketplace install.

**Option B — attach the MCP server for a single session.** If you only need the MCP tools:

```bash
claude --mcp-config /path/to/bright-ai-plugins/claude-code/.mcp.json
```

### Update

Plugins are **not** updated automatically. Refresh the marketplace catalog, then update the plugin,
then restart Claude Code so the new version loads:

```bash
claude plugin marketplace update brightsec       # fetch the latest catalog from GitHub
claude plugin update bright-security@brightsec    # update the plugin (restart required to apply)
```

Confirm with `claude plugin details bright-security@brightsec`.

If you installed **without** the marketplace (the clone approach), update by pulling the repo and
re-copying the files:

```bash
cd /path/to/bright-ai-plugins && git pull
# then re-run the cp commands from "Use without installing"
```

### Uninstall / disable

```bash
claude plugin disable bright-security@brightsec    # keep it installed but turn it off
claude plugin uninstall bright-security@brightsec  # remove the plugin
claude plugin marketplace remove brightsec         # also remove the marketplace source
```

For a clone-based setup, delete the files you copied (`.claude/agents/bright-*`,
`.claude/skills/*`, and the project `.mcp.json`).

---

## Safety

Only scan targets you own or are explicitly authorized to test — a local dev server, a staging/QA
environment, or any host you're authorized to assess. DAST sends real attack traffic, so
authorization is your responsibility. Reach private or local targets through a Bright Repeater
(the agent sets one up and tears it down); publicly reachable targets can be scanned directly.

## License
MIT © [Bright Security](https://brightsec.com)
