---
name: setup-repeater
description: Establish the Bright project for the run and, for private or local targets, create or reuse a Repeater and connect it to the application under test.
---

## Setup Bright Project and Repeater

### Preconditions

`BRIGHT_TOKEN` authenticates every Bright operation. `BRIGHT_HOSTNAME` selects the Bright
cluster and is required to start the Repeater. Expect both values from the environment's secret
store (CI/cloud secrets) or the local shell environment.

Verify them before the first Bright call:

```bash
test -n "$BRIGHT_TOKEN" && echo "BRIGHT_TOKEN: set" || echo "BRIGHT_TOKEN: MISSING"
test -n "$BRIGHT_HOSTNAME" && echo "BRIGHT_HOSTNAME: $BRIGHT_HOSTNAME" || echo "BRIGHT_HOSTNAME: MISSING"
```

If `BRIGHT_TOKEN` reports `MISSING`, stop. Tell the user to export it in the shell they launch
the tool from and restart the session, because the MCP server reads it at startup:

```bash
export BRIGHT_TOKEN="your-bright-api-token"
export BRIGHT_HOSTNAME="app.brightsec.com"
```

Never ask the user to paste the token into the conversation, and never work around a missing one.

Do not assume the MCP server points at `BRIGHT_HOSTNAME`; if Bright calls fail on authentication
or reach the wrong cluster, report that the MCP server needs re-registering instead of retrying.

A Repeater is needed only for **private or local** targets. For a public one (e.g. a public
staging URL), resolve the project in Step 1, skip Steps 2–4, and pass no `repeaters` to the scan;
a missing `BRIGHT_HOSTNAME` then matters only for a `compose-har` upload, which needs it too. Ask
for the hostname before Step 3 if a Repeater turns out to be necessary, or before that upload.

### Step 1: Resolve the Bright project

1. If the user gave a project (id or name), use it and continue to Step 2.
2. Otherwise call `listProjects`.
3. If it returns exactly one project, use it and name it in your output.
4. If it returns several, ask the user which one.

Never pick between several on the user's behalf: not by repository-name similarity, and not by
taking the first result.

Record the resolved `projectId` and pass that same value to every later Bright call in this
run. Never resolve it a second time.

### Step 2: Create or reuse a Repeater (private/local targets)

1. Call `listRepeaters` for the project.
2. Look for a reusable Repeater: one that is already associated with the resolved project, or
   whose name matches the target or run (e.g. `bright-<repo-name>`, `<app>-discovery`). It must
   be one that nobody is using right now: `status` is `disconnected`, or `connected` only because
   of this run's own CLI process that you started earlier in this session.
3. **Never take over a Repeater that is `connected` and in use by someone else.** That breaks
   their scans or discoveries.
4. If several candidates qualify, pick the most specific name match (exact repo/app name over a
   generic one) and note which one was reused.
5. Create a new Repeater with `createRepeater` only when nothing reusable exists. Use a
   descriptive name such as `bright-<repo-name>`.
6. Record the `repeaterId` (reused or created) for Step 3 and the Output.

### Step 3: Start the Repeater

Use `$BRIGHT_HOSTNAME` exactly as below; do not substitute another host.

The Repeater runs on this machine, so the target must answer from here (localhost, LAN, VPN,
tunnel, or the user's port-forward). Confirm it does before starting; if not, stop and say so.

Start the Bright CLI Repeater:

```bash
npx @brightsec/cli repeater --id <REPEATER_ID> --hostname "$BRIGHT_HOSTNAME" --token "$BRIGHT_TOKEN"
```

Run it in the background and keep its PID for Cleanup. To find it later, use
`pgrep -f -- "--id <REPEATER_ID>"` without `-l` or `-a`. Never print a process command line
(`ps`, `pgrep -l`/`-a`, `/proc/*/cmdline`): it carries the token.

### Step 4: Verify connectivity

1. Poll `listRepeaters` until the Repeater is connected. This call goes through the MCP server,
   so it is also the check that both sides agree on the cluster: a Repeater whose process is
   running but never appears here was started against a different one.
2. Retry up to 3 times.
3. If it never connects, capture the process output and stop.

### Output

Return:
- `projectId`
- `projectName`
- `repeaterId` (or note that the target is public and no Repeater is needed)
- whether the Repeater was reused (with its ID and name) or created for this run
