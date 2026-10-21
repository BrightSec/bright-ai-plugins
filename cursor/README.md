# Bright Security — Cursor plugin

Bright DAST (Dynamic Application Security Testing) agents and skills, packaged for Cursor.
The plugin wires three orchestration agents and seven skills to the **Bright MCP server**, so Cursor
can analyze an app, reach a target, register attack surface, run scans, and remediate findings —
in desktop Cursor or in Cursor Cloud Agents.

## What's inside
- **Agents** (`agents/`)
  - `bright-application-testing` — analyze the repo, reach the target, configure Bright, register
    attack surface, and run DAST scans (through a Repeater for private/local targets).
  - `bright-remediation-loop` — reproduce findings with DAST, apply minimal fixes, restart the
    app, and re-run validation scans until findings are gone.
  - `bright-discovery` — analyze the repo, reach the target, build the endpoint list from the
    code, register the endpoints in Bright with values that pass validation, and report what it
    couldn't register and why — no scanning, no code changes.
- **Skills** (`skills/`) — `analyze-codebase`, `setup-repeater`, `setup-auth`,
  `register-entrypoints`, `compose-har`, `run-scan`, `fix-and-validate`. The agents call these as
  building blocks.
- **MCP** (`mcp.json`) — the Bright MCP server over HTTP.

---

## Install

**1. Export your Bright credentials** in the shell/user environment (the MCP server and the Bright
Repeater both read them):

```bash
echo 'export BRIGHT_HOSTNAME="app.brightsec.com"' >> ~/.zshrc   # your Bright cluster hostname
echo 'export BRIGHT_TOKEN="your-bright-api-token"' >> ~/.zshrc  # your Bright API token
source ~/.zshrc
```

On Windows PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("BRIGHT_HOSTNAME", "app.brightsec.com", "User")
[Environment]::SetEnvironmentVariable("BRIGHT_TOKEN", "your-bright-api-token", "User")
```

**2. Add the marketplace and install the plugin.** Cursor installs plugins from the app, not from
the CLI. Add the marketplace source (once), then install from **Customize**:

```bash
# Add the marketplace source (CLI can add a marketplace, but not install a plugin)
cursor-agent plugin marketplace add https://github.com/BrightSec/bright-ai-plugins
```

Then in desktop Cursor open **Customize → Plugins**, find **Bright Security** under the `brightsec`
marketplace, and click **Install**. You can also browse and install from
[cursor.com/marketplace](https://cursor.com/marketplace).

**3. Enable the MCP server.** After install, confirm the **brightsec** MCP server is enabled in
Customize (or Cursor Settings → MCP), and that the three Bright agents appear.

> Prefer not to install? See [Use without installing](#use-without-installing) below.

---

## Use

Ask for an agent in chat — Cursor delegates to it based on the task:

```
Use the bright-application-testing agent to scan this app
Use the bright-remediation-loop agent to scan, fix, and re-verify
Use the bright-discovery agent to discover and register this app's endpoints
```

You can also pick the agent explicitly from Cursor's agent selector. Scan any target you own or are
authorized to test (local, staging, or another authorized environment). Reach private/local targets
through a Repeater — the agent sets one up for you.

---

## Advanced usage & options

### Use without installing

Load the plugin straight from a clone — handy for trying it out, pinning a commit, or CI.
`BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` still need to be in the environment.

```bash
git clone https://github.com/BrightSec/bright-ai-plugins
```

**Option A — CLI, single session.** The `--plugin-dir` flag loads a local plugin directory for one
run, with no marketplace and no install:

```bash
source ~/.zshrc
cd /path/to/your-project
cursor-agent --plugin-dir /path/to/bright-ai-plugins/cursor
```

**Option B — desktop Cursor, local plugin folder.** Symlink the plugin into Cursor's local plugin
directory, then reload:

```bash
ln -s /path/to/bright-ai-plugins/cursor ~/.cursor/plugins/local/bright-security
```

Restart Cursor (or run **Developer: Reload Window**) and the agents, skills, and MCP server load
without a marketplace install.

### MCP secrets in the CLI

The CLI keeps it simple: it reads `mcp.json` (from the plugin, or from `.cursor/mcp.json` /
`~/.cursor/mcp.json`) and resolves `${env:BRIGHT_HOSTNAME}` and `${env:BRIGHT_TOKEN}` straight from
the shell it runs in. No dashboard configuration is involved, and the Bright Repeater picks up the
same exported variables — one source of truth for both. (`envFile` is stdio-only, so it doesn't
apply to the Bright HTTP MCP server; use shell environment variables.)

Approve the MCP server so the CLI loads it without prompting:

```bash
# One-off: approve all MCP servers for this run
cursor-agent --plugin-dir /path/to/bright-ai-plugins/cursor --approve-mcps

# Or persist approval, then run normally
cursor-agent mcp enable brightsec
cursor-agent mcp list            # check status
cursor-agent mcp disable brightsec
```

### Run in Cursor Cloud Agents

Cloud Agents are first-class — use them when the target runs in the cloud.

1. Connect the repository to Cursor Cloud Agents.
2. Create a Bright API token in Bright.
3. Add `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` to Cursor Cloud Agent **secrets**.
4. Enable the Bright MCP server for Cloud Agents, mirroring `mcp.json`:
   - Name: `brightsec`
   - Transport: HTTP
   - URL: `https://${env:BRIGHT_HOSTNAME}/mcp`
   - Header: `Authorization: Api-Key ${env:BRIGHT_TOKEN}`
5. If the app requires login, add those credentials to Cloud Agent secrets too.
6. If your team restricts cloud egress, allowlist your `BRIGHT_HOSTNAME`.

### Update

Re-index the marketplace from its Git source, then let Cursor pick up the new version:

```bash
cursor-agent plugin marketplace update brightsec
```

In desktop Cursor, a team/marketplace plugin can also be refreshed from **Customize → Plugins**
(enable **Auto Refresh** on a team marketplace to update automatically on push). For the
clone-based setups above, update by pulling the repo (`git pull`) and, for Option B, reloading the
window.

### Uninstall / disable

- **Disable or uninstall the plugin:** open **Customize → Plugins**, find **Bright Security**, and
  toggle it off or remove it.
- **Remove the marketplace source (CLI):**
  ```bash
  cursor-agent plugin marketplace remove brightsec
  ```
- **Clone-based setups:** delete the symlink `~/.cursor/plugins/local/bright-security`, or just stop
  passing `--plugin-dir`.

### Verify and troubleshoot

- **Desktop:** check `echo $BRIGHT_HOSTNAME` and `echo $BRIGHT_TOKEN` before opening Cursor chat
  tools. If Bright tools are missing, reload Cursor and confirm the **brightsec** MCP server is
  enabled in Customize.
- **Cloud Agents:** confirm `BRIGHT_HOSTNAME` and `BRIGHT_TOKEN` exist in secrets and the Bright MCP
  server is enabled in the Cloud Agent MCP UI.
- **Auth fails:** replace the API token and restart Cursor.
- **Only the Repeater fails:** test the Bright CLI manually —
  ```bash
  npx @brightsec/cli repeater --id <REPEATER_ID> --hostname "$BRIGHT_HOSTNAME" --token "$BRIGHT_TOKEN"
  ```

---

## Safety

Only scan targets you own or are explicitly authorized to test — a local dev server, a staging/QA
environment, or any host you're authorized to assess. DAST sends real attack traffic, so
authorization is your responsibility. Reach private or local targets through a Bright Repeater (the
agent sets one up and tears it down); publicly reachable targets can be scanned directly. Provide
credentials the way that matches your execution mode — Cloud Agent secrets for cloud, shell/user
environment variables for desktop — and never commit a `.env` with real credentials.

## License
MIT © [Bright Security](https://brightsec.com)
