# Bright Security — Antigravity CLI plugin

Bright DAST (Dynamic Application Security Testing) workflows, packaged as a native plugin for
Google's **Antigravity CLI** (`agy`, the successor to the Gemini CLI). The plugin bundles the
Bright skills; the Bright MCP server gives `agy` the tools to configure Bright, run scans, and
retrieve findings.

Antigravity has no separate "agent" type, so the three orchestration workflows ship as **skills**
alongside the seven step skills:

- **Orchestration skills:** `bright-application-testing`, `bright-remediation-loop`,
  `bright-discovery`
- **Step skills:** `analyze-codebase`, `setup-repeater`, `setup-auth`, `register-entrypoints`,
  `compose-har`, `run-scan`, `fix-and-validate`

The always-on safety constraints (authorization, Repeater-for-private, an explicit Bright
project, no endpoints with effects you cannot undo) are embedded in the orchestration skills.

---

## Install

**1. Export your Bright credentials:**

```bash
export BRIGHT_HOSTNAME="app.brightsec.com"   # your Bright cluster hostname
export BRIGHT_TOKEN="your-bright-api-token"  # your Bright API token
```

**2. Install the plugin** (this adds the skills). `agy plugin install` accepts a GitHub URL with a
subpath, or a local directory:

```bash
agy plugin install https://github.com/BrightSec/bright-ai-plugins/tree/main/antigravity
# or, from a clone:
# git clone https://github.com/BrightSec/bright-ai-plugins.git
# agy plugin install ./bright-ai-plugins/antigravity
```

The plugin lands in `~/.gemini/config/plugins/bright-security/`. Verify with `agy plugin list`
(shows `skills` and `mcpServers` components) or `agy plugin validate ./antigravity`.

**3. Add the Bright MCP server** so the skills have tools to call. Installing the plugin registers
the skills, but the CLI reads MCP servers from `~/.gemini/config/mcp_config.json` — add the server
there. Antigravity uses `serverUrl` (not `url`) for HTTP MCP servers:

```json
{
  "mcpServers": {
    "brightsec": {
      "serverUrl": "https://app.brightsec.com/mcp",
      "headers": {
        "Authorization": "Api-Key <your-bright-api-token>"
      }
    }
  }
}
```

Use literal values for the hostname and token (or expand them when you write the file, e.g. via a
heredoc). The bundled `mcp_config.json` ships `${BRIGHT_HOSTNAME}` / `${BRIGHT_TOKEN}` placeholders
as a template — replace them with real values, since env-var expansion in the MCP config isn't
guaranteed across Antigravity versions. For a self-hosted or non-default cluster, point `serverUrl`
at your host.

---

## Use

Start `agy` and describe the task:

```
agy
AGY> Run a Bright DAST scan on this app and summarize findings
AGY> Scan, fix the findings, and re-verify
AGY> Use the bright-discovery skill to discover and register this app's endpoints
```

Non-interactive/scripted runs use `-p`; add `--dangerously-skip-permissions` to auto-approve tool
calls:

```bash
agy --dangerously-skip-permissions -p "Run a Bright DAST scan on this app and summarize findings"
```

Scan any target you own or are authorized to test (local, staging, or another authorized
environment). Reach private/local targets through a Repeater — the workflow sets one up for you.

---

## Advanced usage & options

### Bundled MCP config

The plugin ships `mcp_config.json` with the Bright server over HTTP:

```json
{
  "mcpServers": {
    "brightsec": {
      "serverUrl": "https://${BRIGHT_HOSTNAME}/mcp",
      "headers": { "Authorization": "Api-Key ${BRIGHT_TOKEN}" }
    }
  }
}
```

This is the template the plugin bundles. The CLI does not auto-activate it — copy the server into
`~/.gemini/config/mcp_config.json` with real values as shown in step 3. (`~/.gemini/antigravity/mcp_config.json`
is the Antigravity IDE's config, separate from the `agy` CLI.)

### Validate before installing

If you've modified the plugin, validate it first:

```bash
agy plugin validate ./antigravity
```

### Update

Antigravity has no dedicated plugin-update command — reinstall to pick up a new version:

```bash
git -C bright-ai-plugins pull        # if you installed from a clone
agy plugin install ./bright-ai-plugins/antigravity
```

### Enable / disable / uninstall

```bash
agy plugin disable bright-security     # keep installed but turn off
agy plugin enable bright-security      # turn back on
agy plugin uninstall bright-security   # remove the plugin
```

Remove the `brightsec` entry from `~/.gemini/config/mcp_config.json` when you no longer need the MCP
server.

---

## Safety

Only scan targets you own or are explicitly authorized to test (local, staging, or another
authorized environment). DAST sends real attack traffic, so authorization is your responsibility.
Reach private/local targets through a Bright Repeater; public targets can be scanned directly.

## License
MIT © [Bright Security](https://brightsec.com)
