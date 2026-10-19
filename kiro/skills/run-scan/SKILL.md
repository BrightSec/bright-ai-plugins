---
name: run-scan
description: Select Bright security tests, run scans against registered entrypoints, monitor execution, and retrieve findings.
---

## Run Security Scans

### Step 1: Select the test set

Call `listTests` and select from its response. It returns every test the connected Bright
cluster supports, each with a `tag`, a `description`, server-assigned `buckets` (such as `api`,
`server_side`, `client_side`, `business_logic`, `mcp_attacks`), and `enabled`, `deprecated`,
and `mutuallyExclusive` flags.

1. Drop tests that are `deprecated` or not `enabled`.
2. Narrow by `buckets` to what the target actually is. An HTTP API draws on `api` and
   `server_side`; a rendered web UI adds `client_side`; an MCP server adds `mcp_attacks`.
3. Within that shortlist, match each test's own `description` against what the endpoint group
   does — where it takes input, whether it renders templates, accepts uploads, executes
   commands, reaches other services, or is the authentication surface itself.
4. Give any test flagged `mutuallyExclusive` a scan of its own — it cannot share one with
   other tests.

Do not scan from a remembered list of tags. For an API surface, include the access-control and
object-authorization tests from the `api` and `business_logic` buckets.

Keep the set as small as it can be while still covering the endpoint group. Do not include
destructive or special-case tests unless the user explicitly asks for them.

### Step 2: Group scan work

Group entrypoints by equivalent test set and by auth object. Entrypoints in one project can carry different auth objects; public ones, or ones
whose credential travels in the request, carry none. Read each one's `authObjectId` from
`listEntrypoints` (`projectId`, `id`: the entrypoint IDs to scan, `limit: 100`, following
`next`) instead of assuming one for the whole set. A group never mixes auth objects, because
one that fails its check disrupts the whole scan.

Record per group; validation reruns reproduce it exactly:
- `entrypointIds`
- `tests`
- `authObjectId` — the one its entrypoints carry, or none (for `testAuth`, not for `runScan`)
- `repeaters`

### Step 3: Launch scans

Verify each group's `authObjectId` with `testAuth`. If it does not verify, do not launch that
group: restore what that auth object depends on (the app, its seeded user or credential, the
Repeater) and run `testAuth` on the same object again. If it still fails, report the group as
not scanned with the `testAuth` result; do not swap in another auth object, because the
group's entrypoints carry this one. Then call `runScan` once per group, in the project resolved
in `setup-repeater`, with the group's `entrypointIds`, `tests`, and `repeaters`. Never pass
`authObjectId` to `runScan` with `entrypointIds`: Bright rejects that scan, and each entrypoint
already carries its own.

### Step 4: Monitor to completion

1. Poll `getScanStatus` until every scan finishes.
2. If a scan fails, verify the local app and that group's auth object before retrying.
3. Fetch findings with `listScanVulnerabilities` (per scan); get full detail for a finding with
   `getScanVulnerability` (`includeEvidence: true` when you need the request and response).

### Output

Return:
- launched scan groups and IDs, each with its `authObjectId` or none, and any group not
  scanned with its `testAuth` result
- final status for each scan
- finding list with severity, method, URL, evidence, and remedy
- the exact scan configuration needed for validation reruns

MCP scans attack body, query, and fragment parameters only; path and header parameters are not
mutated. Report endpoints whose input is only in the path or headers as a coverage gap.
