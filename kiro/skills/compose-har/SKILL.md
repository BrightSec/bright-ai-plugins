---
name: compose-har
description: Register many routes of one credential through one archive discovery, not one login per entrypoint — compose a HAR 1.2 file, discover it, and reconcile each entry with its entrypoint.
---

## Compose HAR

`register-entrypoints` Step 5 sends a group here: the remaining routes of one auth object,
one request-carried credential, or the public routes. `register-entrypoints` Steps 1–7
(R1–R7 below) still govern everything except how requests reach Bright. A discovery replays
each file entry once, in file order, through one session: one login per file. Each later
`addEntrypoint` or `editEntrypoint` logs in again: get the values right first.

### Step 1: Choose the entries

- **Only new operations.** Leave out every operation an entrypoint on the `baseUrl` host
  already covers (paginated `listEntrypoints`; R3 improves it). A discovery would overwrite
  its stored request and health, not its auth object.
- **Only the group's routes.** The discovery's auth object goes to every entrypoint it
  creates, public ones included.
- **One entry per operation**, with the union of its parameters. Bright fingerprints an entry by
  method, path, and the names of its query and body parameters, and silently drops a later entry
  with the same fingerprint, whatever its values or content type.
- **Values from R2**, with IDs and objects read from the running app, never by sending the
  entry first. An entry whose replay answers `404` is dropped without a trace: a missing route
  or object is a gap, not an entry. A destructive entry targets a sacrificial object created
  and read back before the discovery, never an ID an earlier entry would create.
- **No invented IDs.** Never use the ID of an object that does not exist in the app, and never
  edit the app's database or fixtures to make an entry pass.
- **Order** as R5 orders registrations; file order is replay order.
- **At most 90 entries per file**, under Bright's discovery entrypoint limit; split
  larger groups.

### Step 2: Pilot first

Before a group's main files, run a pilot file through Steps 3–5: its first-of-kind entries
(R5) — one read, one create or update — and one per body encoding it uses. Check their health
and fix a systemic cause first; the main files leave the pilot's operations out. After a login
rate limit or lockout, start the pilot only once `testAuth` passes again: at most 3 calls,
minutes apart (each logs in), then R5 Fixing.

### Step 3: Write the file

Generate compact, valid JSON by script in the run's scratch directory:
`{"log":{"version":"1.2","creator":{"name":"…","version":"…"},"entries":[…]}}`, entries like
this:

```json
{"startedDateTime":"2026-01-01T00:00:01.000Z","time":0,
 "request":{"method":"POST","url":"http://localhost:8080/api/items?view=full",
  "httpVersion":"HTTP/1.1","cookies":[],"headersSize":-1,"bodySize":17,
  "headers":[{"name":"Host","value":"localhost:8080"},{"name":"Accept","value":"application/json"},
   {"name":"Content-Type","value":"application/json"}],
  "queryString":[{"name":"view","value":"full"}],
  "postData":{"mimeType":"application/json","text":"{\"name\":\"item-1\"}"}},
 "response":{"status":200,"statusText":"OK","httpVersion":"HTTP/1.1","cookies":[],
  "headers":[{"name":"Content-Type","value":"application/json"}],
  "content":{"size":0,"mimeType":"application/json","text":""},
  "redirectURL":"","headersSize":-1,"bodySize":0},
 "cache":{},"timings":{"send":0,"wait":0,"receive":0},"comment":"inventory item"}
```

- `startedDateTime` rises in file order. `url` is absolute on `baseUrl` with the query string,
  and `queryString` repeats its pairs.
- **Headers:** `Host`, `Accept`, every header the handler reads, and `Content-Type` for a body.
  Bright adds `Content-Length`; leave it and hop-by-hop headers out.
- **No credentials** with an auth object: leave out every header and cookie it sets
  (`Authorization`, session cookie, API key, companion values). Without one, headers are
  stored as sent: only the request-carried credential from `setup-auth` goes there. A
  non-auth cookie the handler reads goes in `Cookie`.
- **Bodies:** `postData.mimeType` equals `Content-Type`. JSON serialized; forms URL-encoded;
  multipart in full with CRLF line ends, the header's boundary, and small text files as file
  parts. Raw binary bodies are untested: use `addEntrypoint`.
- **Response:** the placeholder above; Bright ignores it.

### Step 4: Upload and discover

1. Upload the file with the Bright CLI. Start every filename with a prefix unique to this run
   (e.g. the Repeater or run name: `<run>-api-reads-1.har`); an upload under a name already in
   the project replaces that file:

   ```bash
   FILE_ID=$(npx @brightsec/cli archive:upload --type har --discard false --project <projectId> \
     --token "$BRIGHT_TOKEN" --hostname "$BRIGHT_HOSTNAME" <file.har> | tail -n1 | tr -d '[:space:]')
   ```

   `FILE_ID` is the `fileId`; empty means the upload failed. The CLI validates the HAR before
   sending it: on an error, stderr names the violation; fix the file and upload again. Never
   pass HAR content in tool arguments, and never echo the token.
2. `runDiscovery` with `projectId`, a `name` for the group and part, the `fileId`, `repeaters`
   for private or local targets, and the group's `authObjectId` (none for public or
   request-carried files). Never `crawlerUrls`: Bright would ignore the file.
3. Poll `getDiscoveryStatus` until complete; in `getDiscoveryWarnings`,
   `ENTRYPOINTS_LIMIT_REACHED` means the run stopped early. A failed discovery or a Repeater
   or target error gets R5's unreachable-target recovery.
4. Before the next file, check health: `curl` `baseUrl`, and `testAuth` the file's auth object
   (a request-carried credential: one request on a route it guards). A failure gets R5's
   unreachable-target recovery or R5 Fixing first.

A file with destructive entries runs after every other file, one at a time, with no other
discovery running.

A file runs once: a re-run re-creates its objects, misses its deletes, and overwrites the first
run's results. Entries still missing go into a new file or through `addEntrypoint`, by the
`register-entrypoints` Step 5 criterion applied to what remains.

### Step 5: Read back and reconcile

1. Read the results as R6 says and `getEntrypoint` each one.
2. Diff the file against them by the Step 1 fingerprint, and compare matched query and body
   values: a mismatch is a corrupted upload, fixed under R5. An entry with no match was:
   - **merged** — same fingerprint as an earlier entry. Never `addEntrypoint` it: Bright would
     log in and send it before its `409`. Count it with the duplicates merged, or, if
     R3 calls it a distinct operation, as a gap naming the entry it collided with.
   - **dropped** — `404`, another host, the limit, no answer (R5 unreachable-target recovery), or
     a response body without `Content-Type` (try `addEntrypoint`). Fix the cause and register it
     again (a fresh sacrificial object if destructive), or record a gap with R5 evidence.
3. Apply R5 health, evidence, and fixing to every entrypoint read. After a file with
   destructive entries, `testAuth` each saved auth object; if one fails, the cause is the
   destructive entry just before the first that stores that mechanism's rejection, or the last
   one if none does.
4. Continue with R7.

### Output

Per file: the group (`authObjectId`, request-carried, or public), `fileId`, `discoveryId`, and
`entries N / mapped M / merged D / dropped X` with each drop's outcome.
