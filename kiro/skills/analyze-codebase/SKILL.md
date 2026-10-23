---
name: analyze-codebase
description: Detect the technology stack and inventory the HTTP endpoints that can be scanned through Bright DAST, excluding those whose effects cannot be undone.
---

## Analyze Codebase

### Step 1: Detect the technology stack

Read top-level files such as `package.json`, `go.mod`, `requirements.txt`, `Gemfile`,
`pom.xml`, `Cargo.toml`, `Dockerfile`, and `docker-compose.yml`.

Identify languages, frameworks, databases, startup commands, and likely ports.

### Step 2: Find route definitions or API definitions

Look for:
- OpenAPI or Swagger files
- GraphQL schemas
- controller files
- route files
- framework decorators and middleware that define endpoints

### Step 3: Extract endpoints

For each endpoint, capture:
- method
- path
- body schema with realistic sample values
- query parameters with realistic sample values
- content type

### Step 4: Exclude endpoints that cannot be safely fuzzed

A scan sends many malformed and hostile requests to every registered endpoint. Exclude an
endpoint when repeated hostile calls would cause an effect the user cannot undo in this
environment.

Decide from what the handler does, not from the method name or the field names:

- **Irreversible state change** — hard deletes, purges, or mutations with no restore path in
  this environment.
- **Out-of-band side effects** — sending mail or SMS, charging cards, calling metered
  third-party APIs, triggering deploys or webhooks that reach systems outside the target.
- **Loss of access to the target** — rotating or invalidating the credentials, tokens, or
  accounts that the scan itself authenticates with.

Applying the criterion:

- `DELETE` is strong evidence of the first case, not a verdict. A `DELETE` over seeded,
  disposable data is an ordinary scan target; a `DELETE` that removes a real tenant is not.
- A field named `password`, `token`, or `secret` is not by itself a reason to exclude. The
  login endpoint accepts a password and is one of the most valuable endpoints to scan — it is
  the target of the `brute_force_login` and `jwt` tests. Exclude a credential-mutating route
  only when it would lock the scan out of the target (third case).
- When the target runs on seeded data the user can reset, the first case mostly disappears.
  Confirm with the user before excluding endpoints on that basis alone.

When you are unsure about an endpoint, exclude it and say why, rather than registering it
silently.

### Output

Return:
- stack summary
- startup options
- total endpoints discovered
- endpoints retained for scanning
- excluded endpoints, each with the specific effect that made it unsafe
