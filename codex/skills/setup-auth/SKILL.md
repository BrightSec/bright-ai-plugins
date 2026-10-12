---
name: setup-auth
description: Map the application's authentication mechanisms from its code and create a verified Bright auth object for each one the inventory needs.
---

## Setup Authentication

### Step 1: Build the auth map from the code

Read every router, middleware, guard, and handler-level check (e.g. bearer token, API key, session
cookie, signature, custom header). Assign every inventory route to a public group or a mechanism,
and record per mechanism, citing file and line:

- **guard** — what decides, including a handler or role check that differs from its middleware
- **credential** — what it expects, for which principal
- **obtained** — how the code issues it: login flow, key or token creation, exchange of another
  credential, a secret seeded by config or set through another route group. Capture **every**
  credential a login response issues, not only the one the primary mechanism uses: a response
  may return a token in its body and also set a cookie, header, or second token that a different
  route group reads. Take test credentials from seed data, fixtures, `.env.example`, or setup
  docs; never invent them
- **sent** — where it travels, plus every other value the guard checks with it
- **accepted / rejected** — what each path returns per the code: status, redirect target,
  headers, body. A rejection is not always a 4xx

### Step 2: Reuse an auth object that fits

Call `listAuths` in the project resolved in `setup-repeater`. An object covers a mechanism only if
its `test.request` (`getAuth`) is a route that mechanism guards, and `testAuth` with
`includeEvidence` passes with the map's rejection in its `validation` result and the map's
accepted response after authenticating. Never edit a listed object.

### Step 3: Verify each mechanism before saving

Iterate with `testAuth` on an unsaved payload (`authObject`) and call `addAuth` only once it
verifies.

Pick the `type` that reproduces how the credential is obtained and sent, and `reauthTriggers` that
match the map's rejection (`401` and `403` by default). Set `test.request` to a route this mechanism
guards. `testAuth` first sends it without the credential: a failed `validation` result means
the route or the triggers miss the map's rejection; fix those, not the credential.

Read the verdict explicitly: `verified=false`, or any entry in `tests[]` with `failed=true`, means
auth is not verified. Do not proceed on a partial pass.

Correct the payload from per-result evidence. Common causes: the login body shape, token extraction,
header name or format, a value the guard checks that the payload omits, the login path and content
type, and reachability (through the Repeater for private or local targets). Obtain a credential that
depends on another mechanism after that one; if that one is a gap, so is this one. If no auth object
type can attach a credential where the guard reads it, `curl` a guarded route with and without it
against the map, and hand it to `register-entrypoints`.

After 10 failed attempts at a mechanism, its route group is a gap: record the request you sent and
quote the response. A hypothesis is not evidence.

### Step 4: Save the verified auth objects

Call `addAuth` for each verified payload in that project, named after its mechanism. Set
`repeaterRequired: true` for private or local targets, and keep the `reauthTriggers` that verified.

### Output

Return the auth map: per mechanism, its route groups and guard, the credential's source and
transport, and its `authObjectId`, request-carried credential, or gap with the quoted response;
public groups; assumptions and blockers.
