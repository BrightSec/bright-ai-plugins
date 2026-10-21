# Bright Security — GitHub Copilot plugin

Bright DAST (Dynamic Application Security Testing) agents and skills, packaged for GitHub Copilot.
It works on two surfaces:

- **Copilot CLI** — native plugin install, plus the Bright MCP server added once.
- **Copilot coding agent** (github.com) — copy the agents and skills into the target repo.

## What's inside
- **`plugin.json`** — Copilot CLI plugin manifest (points at `agents/` and `skills/`).
- **CLI agents** (`agents/*.agent.md`): `bright-application-testing`, `bright-remediation-loop`,
  `bright-discovery`.
- **Skills** (`skills/*/SKILL.md`): `analyze-codebase`, `setup-repeater`, `setup-auth`,
  `register-entrypoints`, `compose-har`, `run-scan`, `fix-and-validate`.
- **Coding-agent agents** (`.github/agents/*.md`): the same three agents, with `mcp-servers`
  frontmatter using `${{ vars.BRIGHT_HOSTNAME }}` / `${{ secrets.BRIGHT_TOKEN }}`.

---

## Install (Copilot CLI)

**1. Export your Bright credentials** in the shell Copilot runs in (the MCP server and the Bright
Repeater both read them):

```bash
export BRIGHT_HOSTNAME="app.brightsec.com"   # your Bright cluster hostname
export BRIGHT_TOKEN="your-bright-api-token"  # your Bright API token
```

**2. Install the plugin** (this adds the agents and skills):

```bash
copilot plugin marketplace add BrightSec/bright-ai-plugins
copilot plugin install bright-security@brightsec
```

**3. Add the Bright MCP server** so the agents have tools to call. Copilot CLI does **not** expand
`${VAR}` inside MCP config, so use the native command and let your shell expand the values:

```bash
copilot mcp add --transport http --header "Authorization: Api-Key $BRIGHT_TOKEN" \
  brightsec "https://$BRIGHT_HOSTNAME/mcp"
```

Verify: `copilot plugin list`, `copilot skill list`, `copilot mcp get brightsec` (should show
`brightsec` enabled, http, with the Authorization header). Bright accepts the `Api-Key` scheme.

> Why a separate step? The CLI plugin ships the agents and skills; it doesn't bundle an MCP
> config. Registering `brightsec` with `copilot mcp add` is what makes the Bright tools available,
> and it also handles self-hosted / non-default clusters via your `BRIGHT_HOSTNAME`.

---

## Use

Run an agent and describe the task:

```bash
copilot --agent bright-application-testing -i "Scan this app"
copilot --agent bright-remediation-loop -i "Scan, fix, and re-verify"
copilot --agent bright-discovery -i "Discover and register this app's endpoints"
```

`-i` starts an interactive session with that first prompt. For non-interactive/scripted runs use
`-p` and pre-allow tools:

```bash
copilot --agent bright-application-testing --allow-all-tools -p "Scan this app through a Repeater"
```

Scan any target you own or are authorized to test (local, staging, or another authorized
environment). Reach private/local targets through a Repeater — the agent sets one up for you.

---

## Advanced usage & options

### Use without installing

Load the plugin straight from a clone for a single session — handy for trying it out, pinning a
commit, or CI. `BRIGHT_HOSTNAME` / `BRIGHT_TOKEN` still need to be exported, and you still add the
MCP server (step 3 above) once.

```bash
git clone https://github.com/BrightSec/bright-ai-plugins
copilot --plugin-dir /path/to/bright-ai-plugins/github-copilot --agent bright-security:bright-application-testing -i "Scan this app"
```

`--plugin-dir` loads the agents and skills from the directory without a marketplace install (repeat
it to load more than one). Under `--plugin-dir`, agents are namespaced as `bright-security:<agent>`,
and the global option goes before a subcommand (`copilot --plugin-dir <dir> plugin list`).

### Copilot coding agent (github.com)

To run on the Copilot coding agent instead of the CLI, copy the coding-agent pieces into the target
repository:

```bash
cp -R github-copilot/.github  your-repo/                                   # custom agents
mkdir -p your-repo/.github/skills && cp -R github-copilot/skills/*  your-repo/.github/skills/
```

Custom agents are discovered from `.github/agents/`, skills from `.github/skills/`. The agent
frontmatter builds the MCP URL from `${{ vars.BRIGHT_HOSTNAME }}` and authenticates with
`${{ secrets.BRIGHT_TOKEN }}`, so self-hosted and private clusters work by setting that variable —
no need to edit the agent files.

Then wire credentials into the Copilot environment (repo/org secrets are **not** visible to Copilot
agents):

- Add `BRIGHT_TOKEN` as a **secret** in the repository's `copilot` GitHub Actions environment.
- Add `BRIGHT_HOSTNAME` as a repository/organization **variable** (e.g. `app.brightsec.com`).
- Allowlist your Bright hostname under **Copilot → Cloud agent → Internet access → Custom
  allowlist**.

### Update

```bash
copilot plugin marketplace update brightsec        # refresh the marketplace catalog
copilot plugin update bright-security@brightsec     # update the plugin (or --all for every plugin)
```

### Uninstall

```bash
copilot mcp remove brightsec                        # remove the MCP server
copilot plugin uninstall bright-security            # remove the plugin
copilot plugin marketplace remove brightsec         # remove the marketplace source
```

For the coding agent, delete the copied `.github/agents/bright-*` and `.github/skills/*` from the
target repo.

---

## Safety

Only scan targets you own or are explicitly authorized to test (local, staging, or another
authorized environment). DAST sends real attack traffic, so authorization is your responsibility.
Reach private/local targets through a Bright Repeater; public targets can be scanned directly.

## License
MIT © [Bright Security](https://brightsec.com)
