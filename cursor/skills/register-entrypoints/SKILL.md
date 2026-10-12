---
name: register-entrypoints
description: Register the application's operations in Bright as entrypoints from its source code, with code-grounded parameter values, health checks, and named gaps; crawl only as a fallback.
---

## Register Entrypoints

Reuse the `projectId` and Repeater from `setup-repeater` and the auth map from `setup-auth`;
Step 5 says when each is attached. Every `addEntrypoint` and `editEntrypoint` runs its auth
object's full login and sends the real request to the target, so registration has side effects.
Without a user-set time, cost, or count budget, never narrow the inventory to save effort; if an
external limit stops the run, name every unprocessed operation and why.

### Step 1: Complete the inventory from the code

Start from the `analyze-codebase` inventory and its exclusions; do not redo them. Complete and
verify it from the code, recording per operation:

- the full path, including prefixes, versioning, and sub-routers mounted in middleware, and its
  auth-map group (an unmapped route goes back to `setup-auth`)
- for gRPC-gateway, the `google.api.http` mapping; request-message fields not bound to the path or
  `body` become query parameters
- every query parameter and request header this handler reads — framework accessors (e.g.
  `QueryParam(...)`, `request.args`, `req.query`, header getters) and bind/DTO tags — not a set
  copied from a neighbouring route
- the handler identity (file plus function, or RPC name) for Step 3
- the operation's own tests, when the repository has them — they exercise the exact request the
  handler expects (required headers and their values, protocol or version strings, body shape),
  including requirements the handler delegates to a framework or library and so does not spell
  out in its own code. Read them to pin values the handler alone does not reveal
- if the app serves a built frontend: the JavaScript the served `index.html` references (`curl`
  the `baseUrl`), its service worker, and the chunks they load, or the build output directory
  (e.g. `dist/`). Frontend source with no bundle in the served `index.html` is a JavaScript
  coverage gap: the frontend was not built or served

A single URL that fronts a protocol transport is a surface, not one operation: enumerate the
operations it exposes and register each. An MCP endpoint (e.g. `POST /mcp`) is the clearest case
— register the handshake (`initialize`), the catalogue call (`tools/list`), and one tool
invocation (`tools/call`) per tool the server exposes, with that tool's arguments taken from its
input schema. The same applies to any transport that multiplexes many operations behind one path
(a JSON-RPC or batch endpoint). The server's own code or tests list the operations; the single
handshake request the transport rejects is not the surface.

A shipped API definition (OpenAPI/Swagger) is input for this inventory and for `compose-har`
entries: paths, parameters, schemas. Values still come from Step 2; its `example` values are not
evidence. Never upload the definition itself to Bright.

Also list the surface the code cannot reveal — routes built at runtime, plugin route tables,
server-rendered pages not statically visible, parts with no source in the repository.
That list is the only input to Step 6.

### Step 2: Craft functional parameter values

Every path, query, body, and header value must pass validation and seed mutation well. Build
each request from a concrete URL on `baseUrl`, deriving every value from the code.

Bind the body to **this operation's own request message or DTO**, read from its handler. Do not
reuse the body of a sibling route that shares a resource noun: two operations on related URLs
(e.g. a create on a collection and a different RPC on the same resource) are usually distinct
messages with distinct required fields. When a 400 names a field or a `oneof` the body is
missing, that field is the one to supply — not a signal to drop the operation.

- **Enums and constants** — the exact member and casing (`OAUTH2`, not `oauth2`); a real key from
  an enumerated set, not `"test"`.
- **Encoded fields** — encode what the handler decodes: a JSON-decoded `value` is `"\"en\""`, not
  `"en"`.
- **Framework conventions** — e.g. gRPC-gateway Update RPCs need an `update_mask` listing the
  fields being set.
- **Types and validation** — the declared type, format hints (email, UUID, date-time, URI),
  patterns, length bounds, every required DTO field, nested object and array shapes. Encode each
  field as the type the message declares: a field that is itself a nested message or object is
  sent as an object with that message's fields, even when its only field is a name or id — not as
  the bare string of that value. A field that is declared as a plain string stays a string.
- **Seeds** — IDs, slugs, and foreign keys from the seeded data.
- **Dependent objects** — read real IDs from the running app. Create a missing object first
  through the application's API (`curl` against `baseUrl` with the run's credentials), and a
  separate sacrificial object for every destructive operation. If you cannot, record the route
  as a gap instead of registering a guaranteed 404.

Then:

- Build one representative value set per operation; no combinatorial variants of optional
  parameters.
- Include every required parameter plus the optional ones that widen the attack surface —
  filters, search, sort, pagination, IDs, free text, file and URL fields. A GET registered without
  the query parameters its handler reads is a defect.
- Never register `{}`, `""`, `string`, `0`, or `null` placeholders where the handler expects
  richer input, and send a non-empty body wherever the endpoint expects one.
- Bright templates such as `{{entrypoint.params.query_limit}}` in a URL are fine.

### Step 3: Deduplicate by operation

Deduplication is your judgement about operations, not a method-plus-path rule. Before each
`addEntrypoint`, call `listEntrypoints` with the `projectId` and
`host: ["<host[:port] of baseUrl>"]`, narrowed by `q` (a path fragment) and `method`, and decide
whether one already covers the operation:

- One handler, RPC, or operation is one entrypoint, whatever its parameter combinations, carrying
  the union of the parameters worth mutating.
- Two transports of one handler — a gRPC-gateway RPC path and its REST mapping — are one
  operation. Keep the one exposing more mutable input (usually REST); add the other only if it
  reaches input the first cannot. A `q` + `method` lookup misses these pairs: match by handler
  identity and search the resource fragment without `method`.
- Different handlers, different method semantics on one path, or different resources stay
  distinct: `GET` and `POST` on a collection are two entrypoints, five filter variants of the
  `GET` are one.
- Operations multiplexed behind one protocol-transport URL (Step 1) are distinct from each other
  and from any REST route that reaches the same handler — the transport is its own attack surface
  with its own parsing and dispatch. Do not merge them by shared outer body field names (a
  JSON-RPC envelope makes every call look alike at the top level): the operation is the inner
  method or tool name, so each transport method and each tool call is its own entrypoint, kept
  even when a REST entrypoint already wraps the same underlying handler.
- If one covers the operation, `editEntrypoint` it with the missing parameters or better values
  instead of adding another.

### Step 4: Decide what to register

**Static noise.** Do not register CSS, images (png, jpg, gif, svg, webp, ico), fonts (woff, woff2,
ttf, otf, eot), source maps, `manifest.json` or `*.webmanifest`, `robots.txt`, `sitemap.xml`, or
other non-executable static files. Keep JavaScript — application bundles, chunks, locale bundles,
service workers — as it can carry vulnerabilities.

**Exclusions.** If the calling agent states that its own exclusion rule replaces this default,
apply it. Otherwise keep every exclusion `analyze-codebase` made, do not re-judge the operations it
retained, and judge each operation you add with its Step 4 criterion. Under any rule, even for an
operation `analyze-codebase` retained, exclude one that revokes the current session or
bearer token server-side (not one that only clears a cookie), deletes the auth user, exists to
change their password or other credentials, or shuts the application down. Cite the handler for
every exclusion.

The test is loss of access, not whether a credential value changes. An operation that **issues or
rotates a credential while leaving the caller authenticated** — a token refresh that mints a new
access token from a still-valid refresh credential, a re-issue that returns the new value — keeps
the session alive and is a valuable target, so register it; exclude only the operation that leaves
the caller unable to authenticate (revoke, sign-out that invalidates server-side, delete the
account). When such an operation is reached without the bearer because a public credential drives
it (a cookie or refresh token from an earlier response, per `setup-auth`), register it on the
public surface and send that credential.

**Scan-risk.** An operation the active rule retains may still be turned against the run by a
fuzzed request — global settings that could disable login or signup, or an update of the auth
user's own profile that could change the username, password, or role. Register it and list it under **Scan-risk entrypoints** in the Output with a one-line reason
citing the handler.

### Step 5: Register and verify

Register reads and creates first, then updates, and destructive operations (delete, deactivate,
reset, purge, revoke…) last, each against a sacrificial object from Step 2. Never target
the user, session, or credential an auth object depends on, or objects other entrypoints
reference.

**Register through a file.** Per auth object, request-carried credential, or public routes: when
the auth object obtains its credential through requests (not static headers alone) and more than
10 of its operations remain, when more than 50 remain, or once a registration meets a login rate
limit or lockout, register the rest with the `compose-har` skill, loaded in full, and verify
them once each discovery completes.

Register each operation with `addEntrypoint`: `projectId`; `request` with `method`, `url`,
`headers` as an object of name→string array (including the content type), and `body`;
`repeaterId` for private or local targets; and the `authObjectId` of the mechanism guarding the
route's group, none for public routes, so a scan also tests them and JavaScript anonymously.
Put a request-carried credential from `setup-auth` in the request. Do not register routes of a
gap mechanism; the Step 7 diff lists them with `setup-auth`'s quoted response. `addEntrypoint`
returns only `entrypointId`, not health.

**Health.** Call `getEntrypoint` (`projectId`, `entrypointId`) and read `response.status`,
`response.headers["content-type"]`, and `response.body`. Healthy is the handler's success path as
the code defines it, whichever apply: status, content type, redirect target, effect (a
change you can read back). A redirect, empty list, or bare 2xx alone is not proof: create what
it should show (Step 2) and check again, or count it unhealthy. Unhealthy is no `response`
object (Bright got no answer — check `testAuth`, the target, and the Repeater first), any 4xx or
5xx, or a `text/html` SPA `index.html` shell on a route that should return JSON or a file. The
top-level `status` (`new`/`changed`/`tested`/`vulnerable`) is the security status, not health.

**Evidence.** Every gap, health verdict, and runtime-based exclusion cites a request actually
sent and quotes its response. Never register an unevidenced value (an invented ID, another
mechanism's credentials) as real: obtain it or record a gap. Never edit the app's database or
fixtures to make a registration pass.

Check health at these points; Step 7 reconciles the rest:

- after the first registration of each kind — public, per mechanism, mutating: check one before
  registering the rest of that kind, and fix a systemic cause (auth object, Repeater, base URL,
  the content type the framework expects) first
- after each destructive registration: call `testAuth` with each saved `authObjectId`. A `curl`
  with your own token, or re-reading an entrypoint, does not test an auth object
- after every `editEntrypoint`

**Fixing.** The auth map's rejection or no response on an authenticated route goes back to
`setup-auth`; if its mechanism ends as a gap, delete those entrypoints.
Otherwise read the error in `response.body`, fix the values or path with `editEntrypoint` (or
re-register it), and check again — at most 3 attempts, each response quoted. Keep an entrypoint
whose handler answered as unhealthy only after 3 failed attempts, with its status and message;
delete one whose request never reached the handler (404, SPA shell, no response) with
`deleteEntrypoint` and record a gap.

**Unreachable target.** If `addEntrypoint` or `editEntrypoint` fails with "Cannot access the
target" or similar, stop registering and list the failed requests. Recover in at most 3
attempts, each one restart of the Repeater (`setup-repeater` Step 3) or the app, then one `curl`
of `baseUrl` and one `listRepeaters` check for `status` `connected`. Once both succeed, retry
exactly the failed registrations; after 3 failed attempts, record them as gaps.

### Step 6: Crawl only as a fallback

Use `runDiscovery` with `crawlerUrls` only for the gaps Step 1 listed — a large surface is not a
reason. Pass `projectId`, a descriptive `name`, `crawlerUrls` seeded at the gap (not just the
`baseUrl`), `repeaters` as a single-element array for private or local targets, and the
`authObjectId` of the mechanism guarding the seeded area (none if public), one crawl per auth
object. A user-supplied HAR (uploaded as `compose-har` Step 4 says), then `runDiscovery` with
its `fileId`, can fill a gap the same way. Register gap routes you can describe yourself through
`compose-har`, or with `addEntrypoint` when few remain (Step 5 criterion).

For every discovery, poll `getDiscoveryStatus` until it completes, then read the
results with `listDiscoveryEntrypoints` (`limit: 100`, following `next`) and
`getDiscoveryEntrypoint`. Results are discovery-scoped: `editEntrypoint` and `deleteEntrypoint`
need the project entrypoint ID, from its `targetEntrypointId`. Put every result through Steps 3–4 (delete duplicates and noise), then
give the survivors Step 2 values, their route group's `authObjectId`, and Step 5 health checks.

If a discovery came back thin, check `getDiscoveryWarnings` (unreachable or unauthenticated
routes) and `getDiscoveryLogs` (the request trace) before concluding the surface is small —
usually a missing or expired auth object, shallow seeds, or an unreachable Repeater.

### Step 7: Final review

Read this target's entrypoints with `listEntrypoints` (`projectId`,
`host: ["<host[:port] of baseUrl>"]`, `limit: 100`), following every `next`. Then:

1. Diff the Step 1 inventory — operations and JavaScript — against that list, one by one: each
   item is covered by an entrypoint ID, excluded with its evidence, or missing. Register what is
   missing or record it as a gap with its evidence, and write the diff out: it is the Output's
   only source of gaps.
2. Reconcile health: `getEntrypoint` every listed entrypoint not read since its last edit
   (`listEntrypoints` has no parameters or health), and build the final table from the reads:
   ID, method, URL, `authObjectId`, the parameters in `request`, `response.status` and content
   type. Only a response on the handler's success path (Step 5) is healthy; no response, a 4xx
   or 5xx, or an empty list or body where seeded data should match is unhealthy, not success.
3. Confirm no two entrypoints cover one operation and no static noise remains (JavaScript kept).
   Run Step 5 Fixing on every unhealthy entrypoint from item 2: each ends fixed, deleted as a
   gap, or kept as unhealthy after 3 `editEntrypoint` or re-registration attempts, each response
   quoted.

If items 1–3 changed anything, repeat the paginated `listEntrypoints` and item 2 before the
Output; an entrypoint not read since its last edit is never healthy.

### Output

Build the Output only from the last Step 7 reconciliation — never from memory, tallies, or
estimates — and claim nothing Bright's responses do not support (parameters not in `request`,
"excluded X" while X is registered). Never call the set validated, healthy, or complete while any
entrypoint is unhealthy, unread, or has no response.

Return:

- a counts line `inventory N / registered M (healthy H, unhealthy U) / excluded E / gaps G` in
  exact numbers, never `~`: M from the last paginated `listEntrypoints`, H + U = M from the
  reconciliation, E and G from the Step 7 diff. Other reported numbers must match it
- the final active set a scan reuses — every entrypoint left after Step 7, healthy or not:
  project entrypoint ID, method, URL, `authObjectId`, the values stored in `request`, and
  Bright's recorded `response.status`. Over 50 entrypoints, write this table to a file in the
  run's scratch directory and give its path; always list the unhealthy ones separately inline
  with their quoted response
- **scan-risk entrypoints**, each with its one-line reason
- excluded operations with handler evidence, and coverage gaps with evidence for each missed or
  pruned route
- duplicates merged and noise excluded, with counts
- the discovery path — whitebox, plus any crawl or `compose-har` file with its
  `discoveryId` and justification
