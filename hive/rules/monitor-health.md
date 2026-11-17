# Monitor health

AGENTS.md line: section 12. Merged lessons: issue 14 (same-owner, counted with issues 93 and 96).

## Rule
Every feature, release or scheduled job answers one question before it ships: how would we know, automatically, if it broke? The answer is a monitor, and the monitor is itself checked once built: it has real data, covers every platform, and something reads it.
A monitor watches for unexpected absence, not only for errors. A job that did not run in its window, or a source with no update within its expected cadence (about 48 hours as a default), is FAIL, never OK. Zero rows is FAIL unless the source can legitimately be empty; such a source gets a separate signal that it is alive (a heartbeat row, a last-checked timestamp). Each monitor has its own health check, and the alert path sits outside the code it watches.

## What happened
- issue 14: users who hit a failure usually leave without reporting it, so silent failures are found only by monitors. A monitor can be silent too: a data source with zero rows, one that stopped updating, or a platform that was never wired in all read as healthy until someone looks. No measurement; reported as recurring pain in the keeper's own projects.
- issue 93: a fail-open gate for agent shell commands kept running after the host editor renamed its hook events and tool-name field. For about four minor host versions every event was parsed as "not for us" and ignored. A debug capture showed 6 hook calls against 0 audit-log entries, while the test suite stayed green the whole time because its fixtures still used the old payload shape. The tool looked installed and healthy while doing nothing. First-hand report by the gate's vendor. Source: https://termaxa.com/blog/cursor-saga/
- issue 96: 7 cron-scheduled agent jobs, each a shell script around a headless agent call. A helper module in another repo was renamed and 2 jobs broke on day 1: the import failed, strict error mode ended the script before its alert line, stderr went to the null device and cron had no mail target. The dashboard showed 5 runs a day instead of 7 for 18 days before anyone noticed; tracing only saw jobs that started. After adding a wrapper with exit-code logging and a heartbeat, both dead jobs were flagged within about 10 minutes and a later failure within about 20 (author's figures). Source: https://dev.to/kenimo49/i-cron-scheduled-7-ai-agents-2-silently-failed-for-18-days-tracing-wouldnt-have-caught-it-24fa

## Mechanisms
- Freshness and volume checks per data source: last-update age against the source's cadence and row count, with an unexpected zero or an age past the window reported as FAIL.
- Heartbeat per scheduled job: a wrapper logs the exit code, sends the success ping only after a zero exit, and reports a nonzero exit to the alert path itself; a missing ping in the expected window pages a human. The alert does not depend on the job reaching its own last line, and a failed run never sends the success ping.
- A deliberate skip uses its own exit code, so a skip is not read as a crash and a crash is not read as a skip.
- Coverage check: every platform or source the feature ships on appears in the monitor; a missing one is a FAIL, not an empty row.
- Activity cross-check for gates and integrations: if the host reports activity (calls, events) and the gate recorded none, or an event cannot be parsed, fail loudly, even when the gate is fail-open towards the agent.
- Fixtures for a third-party payload are refreshed from a real capture of the current host version; a suite built only on old fixtures does not show the integration still works.

## Edge cases
- issue 14 has no measurement; issues 93 and 96 have counts from single first-hand write-ups (issue 93 by a vendor of the tool, so read its framing with care).
- Fail-open towards the agent and fail-loud towards the operator are compatible: the gate may let a command through but must still raise its own health alarm.
- A dashboard of runs that happened cannot show a run that never started; count expected runs, not only observed ones.
- The 48-hour window is an example default; set it from the source's real update cadence (a monthly job is not stale after two days).
- Some sources are healthy when empty (for example a table of security alerts); there an empty result is OK and liveness comes from a separate signal.
