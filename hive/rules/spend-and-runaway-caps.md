# Spend and runaway caps

AGENTS.md line: section 0 (new theme). Merged lessons: issue 65 (counted with issues 100 and 113, three distinct Project-IDs). Backs issue 7 (time budget per step, still below quorum).

## Rule
An agent run that nobody watches has hard limits that live outside the model: a spend or token ceiling checked before every model call, a guard that stops the run when the same tool is called with identical arguments N times or the state stops changing for N steps, and dedupe on the triggers that start sessions. A tripped limit stops the run and alerts once; it never retries. Stopping a runaway also disables whatever restarts it.

## What happened
- issue 65: an overnight run summarising about 1,200 documents kept calling the same file-listing tool, got the same answer each time and never changed approach. About 14,000 calls and about 437 USD went by before a provider quota stopped it. Every call looked normal; the only signal was the billing dashboard the next morning. It had been tried on 5 files before the full run. The author estimates about 10 USD with guards in place, a counterfactual from someone whose fix section promotes their own library, so the "after" number is weak. Source: https://dev.to/magicrails/i-let-my-ai-agent-run-overnight-it-cost-437-dd7
- issue 100: flapping connectivity to a secondary agent made a message bridge re-send the same onboarding message every 60 to 90 seconds. Each message started a fresh session that reloaded its full startup context. It ran about 15 hours, roughly 400M input tokens over about 5,000 requests, with no alert. Killing the process did not stop it because the OS service manager restarted it; the service had to be unloaded. First-hand postmortem, cost figures vary by model. Source: https://dev.to/nerudek/400-million-tokens-burned-overnight-5bbg
- issue 113: an operator of 15+ production agents reports a retrieval loop where one agent kept calling the same tool, each call a little more expensive, with no error or alert. A hard spend ceiling in front of every inference call stopped it after 40 minutes; without it the run would have gone on until morning. Dashboards there serve only after-the-fact review. Self-reported single incident. Source: https://theproductionagent.substack.com/p/the-budget-gate-is-the-seatbelt-what

## Mechanisms
- Per-run (or per-agent) spend or token ceiling, checked by a wrapper before each model call, not summed afterwards. A trip is a hard stop plus one alert.
- Repeat guard: hash tool name plus arguments; N identical calls in a row, or N steps with no state change, stops the run and reports what it was doing.
- Trigger dedupe: identical incoming triggers within a cooldown window collapse into one session; the key is the trigger source or sender plus a hash of the message, so two senders with the same text still get their own sessions.
- Aggregate cap above the per-run cap: a ceiling per period across all sessions of one agent or trigger source. A trigger that keeps repeating after each cooldown would otherwise start fresh sessions, each under its own cap, forever; once the aggregate trips, new sessions need a human to resume.
- Rate alerting: alert on token or spend rate in real time, not on a daily total read the next morning.
- Kill path: stopping a runaway checks for a supervisor (service manager, cron, a restart loop) and disables it, then confirms the process stays down.
- Before a full unattended run, a staged rollout that is large enough to show looping, not only a handful of items.

## Edge cases
- Soft budget alerts and dashboards do not count as a cap: they report after the money is spent.
- A provider quota is a last resort, not the cap: it is shared, set high and stops other work too.
- Some tools are legitimately polled with the same arguments (a status check); count those against a time budget or back-off instead of the identical-call guard, and say so explicitly.
- All three reports are single first-hand write-ups; numbers are the authors' own and the "after" figures are estimates, not reruns.
- Related: the per-trigger recursion guard in worktree-and-discard.md (issue 33) and the time budget per step in idea issue 7.
