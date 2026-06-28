1|# Operator digest and action loop format
2|
3|## Purpose
4|
5|This note defines the local digest format for Self Ershov Memory artifacts and the action loop that follows it.
6|It is intentionally Telegram-friendly, but it does not send anything anywhere. It is just the render contract.
7|
8|The digest must be generated entirely from local artifact data and run history:
9|
10|- `manifest.json`
11|- `REPORT.md`
12|- `sources.jsonl`
13|- `proposals.jsonl`
14|- `audit.jsonl`
15|- `runs.jsonl`
16|- `ERSHOV.md`
17|- `state.json`
18|
19|No remote state, no hidden cache, no second source of truth.
20|
21|## Design goals
22|
23|1. Make the current artifact obvious in one scan.
24|2. Put the highest-value decisions at the top.
25|3. Show what changed since the last memory run, not a wall of repeated history.
26|4. Make approve/reject commands copy-paste safe.
27|5. Keep weekly rollups useful, not ceremonial.
28|6. Stay readable on a phone.
29|
30|## Digest shape
31|
32|The digest is a single plain-text message with a fixed section order.
33|If it would exceed the transport limit, split at section boundaries, never mid-command.
34|
35|### Section order
36|
37|1. Header
38|2. Status snapshot
39|3. Priority-ranked proposals
40|4. What changed since last memory run
41|5. Action loop
42|6. Weekly rollup, only when requested or when the current artifact closes a week
43|
44|### Header
45|
46|Keep it short.
47|
48|Example:
49|
50|- `Self Ershov Memory digest`
51|- `Artifact: 20260527T221500Z-abc12345`
52|- `Status: staged | valid | 4 proposals | 2 approved | 1 rejected | 0 applied`
53|- `Priority: 87/100`
54|
55|The header should expose only the facts an operator needs to decide whether to keep reading.
56|
57|### Status snapshot
58|
59|This section is the local equivalent of a report card summary.
60|Use the existing artifact model fields directly:
61|
62|- artifact id
63|- created at
64|- provider
65|- status
66|- source count
67|- proposal count
68|- validation state
69|- apply state
70|- discard state
71|- target kind breakdown
72|- theme labels
73|- applied proposal ids
74|- backup file copies
75|- rollback evidence records
76|- created-file tombstones
77|
78|Keep it to a few bullets, not a dump.
79|
80|## Priority scoring
81|
82|The digest needs a stable way to rank artifacts and proposals.
83|The score is not truth, it is a triage tool.
84|It should reward usefulness, urgency, and recurrence, while penalizing sludge.
85|
86|### Artifact priority score
87|
88|Score range: `0-100`
89|
90|Recommended formula:
91|
92|`artifact_priority = clamp(blocker + value + recurrence + freshness + readiness - noise, 0, 100)`
93|
94|#### Components
95|
96|`blocker` 0-40
97|
98|- +40, validation errors or unsafe/conflicting proposals
99|- +25, unresolved approval state with at least one actionable proposal
100|- +20, artifact is ready to apply but not yet applied
101|- +0, already discarded or fully settled
102|
103|`value` 0-30
104|
105|- +30, at least one `user` proposal
106|- +22, at least one `skill` proposal
107|- +16, at least one `memory` proposal
108|- +10, at least one `fact` proposal
109|- +2, for each additional distinct target kind beyond the first, up to +6 total
110|
111|`recurrence` 0-15
112|
113|- +8, same theme appeared in the last memory run
114|- +7, same theme appears in 2+ source sessions or source snapshots
115|
116|`freshness` 0-10
117|
118|- +10, new proposal set or new evidence since the last memory run
119|- +5, mostly unchanged but with new audit state
120|- +0, pure repeat with no new signal
121|
122|`readiness` 0-10
123|
124|- +10, average confidence >= 0.90
125|- +7, average confidence >= 0.80
126|- +3, average confidence >= 0.70
127|- +0, below that
128|
129|`noise` 0-20
130|
131|- +10, missing provenance on a proposal
132|- +10, duplicate/conflicting proposal inside the artifact
133|- +5, rejected proposal with no reason
134|- +5, obvious slop theme with no operational value
135|
136|### Proposal priority score
137|
138|Inside an artifact, proposals are sorted by this score:
139|
140|`proposal_score = target_kind_weight + confidence_weight + evidence_weight + recurrence_bonus - conflict_penalty`
141|
142|#### Proposal weights
143|
144|`target_kind_weight`
145|
146|- `user`: 40
147|- `skill`: 30
148|- `memory`: 20
149|- `fact`: 10
150|
151|`confidence_weight`
152|
153|- `>= 0.90`: +20
154|- `0.80-0.89`: +15
155|- `0.70-0.79`: +8
156|- `< 0.70`: +0
157|
158|`evidence_weight`
159|
160|- +10, direct source quote or explicit marker
161|- +8, corroborated by 2+ source sessions or snapshots
162|- +5, supported by audit history or prior accepted memory run
163|- +0, weak or indirect evidence only
164|
165|`recurrence_bonus`
166|
167|- +10, recurring theme across multiple memory runs
168|- +5, recurring theme across multiple source sessions
169|- +0, one-off
170|
171|`conflict_penalty`
172|
173|- -25, duplicate target in the same artifact
174|- -20, contradicts a higher-confidence proposal
175|- -10, proposal is too broad or vague
176|- -5, low signal but still potentially useful
177|
178|### Ranking rule
179|
180|Order artifacts by `artifact_priority` descending.
181|Inside an artifact, order proposals by `proposal_score` descending.
182|If scores tie, prefer:
183|
184|1. `user`
185|2. `skill`
186|3. `memory`
187|4. `fact`
188|5. higher confidence
189|6. newer evidence
190|
191|## What changed since last memory run
192|
193|This is the part that keeps the digest from becoming a rerun.
194|The section should compare the current artifact to the previous memory run, not to some abstract idea of progress.
195|
196|### Definition of "last memory run"
197|
198|Use the most recent successful run from `runs.jsonl`.
199|If the current artifact belongs to a chain of related runs, prefer the previous artifact with the same source bundle or source roots.
200|If no prior successful run exists, say so plainly and skip the delta block.
201|
202|### Delta categories
203|
204|Report only the deltas that matter:
205|
206|- `new` — proposal or theme did not exist in the prior memory run
207|- `changed` — same proposal id, but summary, confidence, target, or proposed text changed
208|- `resolved` — proposal moved to approved, rejected, or applied
209|- `repeated` — same theme showed up again with new evidence
210|- `removed` — proposal existed before but is absent now
211|- `stalled` — nothing changed except audit churn
212|
213|### Recommended format
214|
215|Use a short bullet list like this:
216|
217|- New: 2 user-facing proposals, 1 skill update
218|- Changed: proposal `p-04` confidence rose 0.78 -> 0.91
219|- Resolved: `p-02` rejected, reason recorded
220|- Repeated: review UX and live-root quoting showed up again
221|- Removed: none
222|
223|### What not to do
224|
225|Do not restate the whole artifact.
226|Do not repeat full proposal text in the delta section.
227|Do not hide the actual difference behind vague language like “some updates happened”.
228|
229|## Action loop
230|
231|This is the operational part.
232|The digest should end by telling the operator what to do next, with exact commands.
233|
234|### Happy-path loop
235|
236|1. Read the digest.
237|2. Approve or reject the proposals.
238|3. Re-run summarize to confirm the state counts changed.
239|4. Run diff.
240|5. Run validate.
241|6. Apply only after the artifact is approved and valid.
242|7. Finish with status.
243|
244|### Command rules
245|
246|Commands must be shell-safe and copy-pasteable.
247|Always quote artifact paths.
248|Always quote rejection reasons.
249|
250|Examples:
251|
252|- `ershov summarize '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345'`
253|- `ershov approve '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345' all`
254|- `ershov reject '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345' p-04 --reason "too broad"`
255|- `ershov diff '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345' --live-root '/tmp/live root'`
256|- `ershov validate '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345' --live-root '/tmp/live root'`
257|- `ershov apply '/tmp/self-ershov-memory/artifacts/20260527T221500Z-abc12345' --live-root '/tmp/live root' --backup-root '/tmp/backups'`
258|
259|### Approval gate wording
260|
261|When there are unreviewed proposals, the digest should say:
262|
263|- `Next step: approve or reject proposals`
264|
265|When everything is reviewed but not applied, it should say:
266|
267|- `Next step: apply approved proposals`
268|
269|When the artifact is already applied or discarded, it should say:
270|
271|- `Next step: run status or compact`
272|
273|## Weekly rollup
274|
275|The weekly rollup is a separate summary, not part of every digest.
276|It should cover the last 7 days, or the current calendar week if the operator prefers that view.
277|Pick one definition and keep it consistent.
278|
279|### Weekly rollup sections
280|
281|1. Accepted themes
282|2. Rejected themes
283|3. Recurring themes
284|4. Decision patterns
285|5. Next-week watchlist
286|
287|### Weekly rollup format
288|
289|Example:
290|
291|- Accepted themes:
292|  - review UX clarity, 4 wins, 1 apply-ready follow-up
293|  - live-root quoting safety, 2 wins
294|- Rejected themes:
295|  - broad refactors with weak provenance, 3 rejections
296|  - duplicate noise proposals, 2 rejections
297|- Recurring themes:
298|  - review ergonomics, 5 appearances
299|  - command safety, 4 appearances
300|- Decision patterns:
301|  - `user` and `skill` proposals are more likely to be approved than `fact` proposals
302|  - low-confidence duplicates get rejected fast
303|- Next-week watchlist:
304|  - proposal provenance
305|  - command quoting
306|  - state transition audit quality
307|
308|### How to compute the rollup
309|
310|Use run history and artifact audits:
311|
312|- `runs.jsonl` for run outcomes and timestamps
313|- `ERSHOV.md` for the human-readable diary trail
314|- `audit.jsonl` for per-proposal state transitions
315|- `manifest.json` for proposal metadata
316|
317|Count accepted/rejected/applied transitions by theme label.
318|Count recurring themes by repeated appearance across artifacts or source sessions.
319|Use examples, not a data dump.
320|
321|## Suggested local implementation contract
322|
323|A local renderer can build this digest without any network access.
324|It only needs to:
325|
326|1. load the current artifact
327|2. load the previous successful run or artifact
328|3. score the artifact and proposals
329|4. compute deltas
330|5. render a flat text digest
331|6. optionally render a weekly rollup from the run ledger
332|
333|That is the whole job.
334|If it needs more than that, the format is too clever.
335|
336|## Non-goals
337|
338|- No real Telegram API send in this task
339|- No external database
340|- No LLM-only scoring
341|- No hidden state outside the artifact/run ledger
342|- No giant wall of text that nobody will read
343|
344|## Bottom line
345|
346|The digest should act like a sharp operator brief, not a scrapbook.
347|It should tell Niko what matters, what changed, what to approve, what to reject, and what to do next.
348|If it doesn't help him decide in under a minute, it failed.
349|