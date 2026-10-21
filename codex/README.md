# Bright Security — Codex plugin

Bright DAST (Dynamic Application Security Testing) workflows, packaged for Codex. The plugin
bundles the Bright skills; the Bright MCP server gives Codex the tools to configure Bright, run
scans, and retrieve findings.

Codex has no separate "agent" type, so the three orchestration workflows ship as **skills** alongside
the seven step skills:

- **Orchestration skills:** `bright-application-testing`, `bright-remediation-loop`,
  `bright-discovery`
- **Step skills:** `analyze-codebase`, `setup-repeater`, `setup-auth`, `register-entrypoints`,
  `compose-har`, `run-scan`, `fix-and-validate`

---

## Install

**1. Export your Bright credentials** in the environment Codex runs in:

```bash
echo 'export BRIGHT_HOSTNAME="app.brightsec.com"' >> ~/.zshrc   # your Bright cluster hostname
echo 'export BRIGHT_TOKEN="your-bright-api-token"' >> ~/.zshrc  # your Bright API token
source ~/.zshrc
```

**2. Install the plugin** (this adds the skills):

```bash
codex plugin marketplace add BrightSec/bright-ai-plugins
codex plugin add bright-security@brightsec
```

Verify with `codex plugin list` — `bright-security@brightsec` should show `installed, enabled`.

**3. Register the Bright MCP server** so the skills have tools to call:

```bash
codex mcp add brightsec --url "https://$BRIGHT_HOSTNAME/mcp" --bearer-token-env-var BRIGHT_TOKEN
```

Verify with `codex mcp list` — `brightsec` should appear as `enabled` with `BRIGHT_TOKEN` as its
bearer-token env var. Bright accepts the `Bearer` scheme, so this authenticates cleanly.

> Why a separate step? Installing the plugin registers its skills, but Codex loads MCP tools from
> your Codex MCP configuration. Registering `brightsec` with `codex mcp add` is what makes the
> Bright tools available to the agent. See [Bundled MCP config](#bundled-mcp-config) for the
> `.mcp.json` the plugin ships and why the token can't be an interpolated string.

---

## Use

The orchestration workflows are skills — invoke one with `$skill-name`, or just describe the task:

```
$bright-application-testing scan this app
$bright-remediation-loop scan, fix, and re-verify
$bright-discovery discover and register this app's endpoints
```

Scan any target you own or are authorized to test (local, staging, or another authorized
environment). Reach private/local targets through a Repeater — the workflow sets one up for you.

---

## Advanced usage & options

### Bundled MCP config

The plugin ships `.mcp.json` with the Bright MCP server over streamable HTTP:

```json
{
  "mcp_servers": {
    "brightsec": {
      "url": "https://app.brightsec.com/mcp",
      "bearer_token_env_var": "BRIGHT_TOKEN"
    }
  }
}
```

Codex does **not** interpolate `${VAR}` inside config values, so the token is wired through Codex's
env mechanism (`bearer_token_env_var`) and the URL is a literal pointing at the default cloud
cluster. The `codex mcp add` command in step 3 registers the same server from your
`BRIGHT_HOSTNAME`, which also handles self-hosted or non-default clusters without editing any file.

### Install from a local clone (no marketplace)

To run from a checkout instead of GitHub — for trying it out, pinning a commit, or air-gapped
setups — add the repo as a local marketplace, then install as usual:

```bash
git clone https://github.com/BrightSec/bright-ai-plugins
codex plugin marketplace add ./bright-ai-plugins   # local path
codex plugin add bright-security@brightsec
```

Then register the MCP server as in step 3. `BRIGHT_HOSTNAME` / `BRIGHT_TOKEN` still need to be
exported.

### Update

```bash
codex plugin marketplace upgrade brightsec   # refresh the marketplace snapshot from Git
codex plugin add bright-security@brightsec   # reinstall to pick up the new version
```

For a local-clone install, `git pull` in the clone and re-run `codex plugin marketplace upgrade`.

### Uninstall

```bash
codex mcp remove brightsec                    # remove the MCP server
codex plugin remove bright-security@brightsec # remove the plugin
codex plugin marketplace remove brightsec     # remove the marketplace source
```

---

## Safety

Only scan targets you own or are explicitly authorized to test (local, staging, or another
authorized environment). DAST sends real attack traffic, so authorization is your responsibility.
Reach private/local targets through a Bright Repeater; public targets can be scanned directly.

## License
MIT © [Bright Security](https://brightsec.com)
