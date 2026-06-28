1|# Security Policy
2|
3|Self Ershov Memory handles staged writes and writeback safety. Treat anything that touches live roots, artifact validation, or proposal generation as security-sensitive.
4|
5|## Supported versions
6|
7|Security fixes are handled on the current `main` branch and the latest tagged release.
8|
9|## Reporting a vulnerability
10|
11|Do **not** open a public issue for:
12|
13|- secrets or tokens in source, logs, or proposals
14|- path traversal or unsafe write behavior
15|- unexpected live mutation
16|- backup or discard failures
17|- any bug that could expose private data
18|
19|Instead, open a **private GitHub security advisory**:
20|
21|- https://github.com/ersh123/self-ershov-memory/security/advisories/new
22|
23|Include:
24|
25|- the affected version or commit
26|- exact steps to reproduce
27|- sanitized logs or screenshots
28|- the file or path involved, if relevant
29|- whether the problem touches live roots, artifact roots, or backups
30|
31|## What we care about
32|
33|- secret-like content rejection
34|- path safety
35|- approval gates for apply/discard
36|- backup integrity
37|- keeping staged artifacts reviewable instead of silently mutating live state
38|
39|## Response expectations
40|
41|If you report a valid issue privately, the maintainers will triage it promptly and keep the details out of public threads until the fix is ready.
42|