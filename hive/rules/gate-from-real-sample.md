# Gates from a real sample

AGENTS.md line: section 12 (merged into the test-command line, one in, one out). Merged lessons: issue 34 (same-owner, counted with issues 93 and 105).

Status: rule. Tally: 3 projects (3 measured). Measured: issue 34: dependency gate parsed 0 of 18 and 0 of 39 real lines; issue 105: replay of 7 real replies, 6 of 7 right after the fix. Independence: no author or bug report counted twice within this rule (checked 2026-11-18).

## Rule
Before writing a gate, hook, parser or integration, capture a real sample of its input from the actual producer and build the fixtures from it. Before it ships, replay it against real logged history, including the good outcomes it must let through. Every gate has a test where it must refuse and a production count of how often it refuses; a gate that never refuses is suspect. Each integration runs once end to end for real before it is called done.

## What happened
- [measured] issue 34: in the keeper's own pipeline several gates shipped dead because they were written against an imagined format. A dependency gate parsed 0 of 18 real prerequisite lines in one backlog and 0 of 39 in another, so it reported "all met" and builders were dispatched on items whose prerequisites did not exist. A hook read its input from an environment variable while the client sends JSON on stdin, used a token field that never appears in real logs and divided by the wrong quantity (one computed context figure was above one million percent). A parser guessed field names that the real type does not have. A script reading files in the system default codepage crashed on its first real run, which three earlier rounds had missed. A counter and its complement used different patterns so rows vanished from both.
- [measured] issue 93: a fail-open shell gate kept running after the host renamed its hook events and tool-name field; every event was parsed as "not for us". A capture showed 6 hook calls against 0 audit entries while the tests stayed green on old fixtures. Source: https://termaxa.com/blog/cursor-saga/ (also cited in monitor-health.md)
- [measured] issue 105: a CI gate on outbound replies used a keyword list written from imagined wording. Replayed against 7 logged real replies it would have blocked the only one that ever converted, because real people phrased the problem differently; the unit tests had all passed. After widening the vocabulary and adding the missed case as a regression test: 6 of 7 correct, zero false negatives, one false positive (author's figures). Source: https://dev.to/dutchaiagents/we-built-a-ci-gate-for-our-outbound-replayed-it-against-history-it-would-have-blocked-our-only-4525

## Mechanisms
- Fixture from capture: record one real payload from the current producer version and test against it; refresh it when the producer changes.
- One grammar: the producer's instructions and the consumer's parser come from the same document, or a test checks them against each other.
- Variant coverage: hand-built data for every variant a criterion names, not just the current state.
- Replay: run a new gate over logged history before shipping; any wrongly blocked good case becomes a regression test.
- Refusal metric: count refusals in production; zero over a long window is investigated.
- Explicit UTF-8 for all file reads and writes; counting categories are exact complements.
- Feed the gate the original input, not a paraphrase of it.

## Edge cases
- Issue 105 rests on 7 samples and self-reported figures; issue 93 comes from the gate's vendor. Read the numbers as illustrations.
- A replay only covers the history you logged; a gate on a new input type still needs a captured sample first.
- Overlaps monitor-health.md (activity cross-check, fixtures from a real capture); that file covers detecting a gate that went silent, this one covers building it right.
- Counter-search (2026-11-18; "backtesting alert rules against historical data overfitting limitations"): the known limit of replay is overfitting, from trading-strategy backtesting: a rule tuned on the same few samples it is judged on looks better than it is. Issue 105 widened its vocabulary on the 7 samples it then scored. Keep a held-out slice of history, or count production refusals after shipping (Mechanisms). No report found that building from a real sample made a gate worse.
