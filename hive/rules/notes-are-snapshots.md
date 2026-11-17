# Notes are snapshots

AGENTS.md line: section 1 (merged into the work-tracking line, one in, one out). Merged lessons: issue 1 (same-owner, counted with issues 91 and 104).

## Rule
A handoff note, checkpoint, or saved memory entry records one moment. It is not the current truth. Before reporting or acting on anything it calls pending, waiting, unsent, expired or approved, query the live source (issue, PR, CI run, deploy config). Prefer storing a pointer to where the state lives over storing the state itself, and record outward actions as "done #N" or "not done", never as "waiting".

## What happened
- issue 1: an agent resumed from its own handoff note and reported items as still to do that another run had already finished. The human was asked the same question twice and a duplicate outward action nearly went out. The note had been correct when written. No measurement; keeper's own pipeline.
- issue 91: a developer's coding agent nearly acted on a memory note about how scheduled publishing worked; the setup had changed two months earlier. An audit of all 35 notes found 7 still true, 3 provably false (an item listed as pending that was already published, two items listed as unsent that had been sent weeks earlier, a credential listed as expired that had been renewed) and 25 that could not be checked mechanically. Every false note had been true on the day it was written. Source: https://dev.to/javieraguilarai/the-memory-that-was-true-bg5
- issue 104: within a week of getting persistent memory, an agent stated three false facts with confidence: a deploy region recorded before an infrastructure move (it kept aiming deploys at an empty region), a vague remark stored as approval of a plan the user had rejected two days earlier, and a one-off tool choice that a summarising pass turned into a standing preference. Self-editing memory sometimes added a contradicting entry instead of replacing the old one. Source: https://dev.to/kenimo49/i-gave-my-agent-persistent-memory-it-remembered-the-wrong-3-things-for-a-week-50c9

## Mechanisms
- Store a pointer (issue number, PR, file, query) rather than a status word; resolve it at read time.
- Timestamp every entry; treat volatile facts (regions, versions, deadlines, approvals, credential state) as suspect after a short window and re-check before use.
- Keep what the user said apart from what the agent inferred; an inferred entry needs more evidence before it drives an action, and an approval is never inferred from a vague remark.
- A correction overwrites the old entry and records where it came from; it does not append a contradicting one.
- Update or close out notes when a session ends; mark in-progress items as transitional.
- A periodic audit script checks the notes it can verify mechanically and flags the rest.

## Edge cases
- Issue 1 has no numbers; issue 91 has one audit on one day; issue 104 reports counts but no logs and says the problem is not fully solved.
- Many notes cannot be checked mechanically (25 of 35 in issue 91); for those, the safe default is to ask or re-derive, not to act.
- A summarising or consolidation pass is itself a source of drift; its output needs the same timestamps and provenance.
