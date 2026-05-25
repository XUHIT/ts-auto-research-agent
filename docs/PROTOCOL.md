# Research Protocol

## One Experiment Round

1. Propose or select a `vibe_idea`.
2. Run pre-taste review.
3. Queue an experiment plan only if the taste gate approves it.
4. Execute one backend run.
5. Parse metrics and update the leaderboard.
6. Run post-taste review.
7. Emit a strict reviewer decision.
8. Queue a follow-up only when the reviewer says `continue`.

## Pre-Taste Gate

Scores are 1-5:

- `interestingness`
- `non_obviousness`
- `importance`
- `story_potential`
- `experimentability`
- `defensibility`
- `trend_alignment`
- `personal_fit`

Default blocking rules:

- `interestingness < 3`: do not run.
- `non_obviousness < 3`: do not run.
- `experimentability < 3`: defer.
- `defensibility < 3`: strengthen the defense before running.

## Post-Taste Review

Post-taste asks:

- Did the result change belief?
- Was there surprise?
- Can this support a claim?
- Should the next step deepen, broaden, kill, pivot, or ask a human?

The final reviewer output is always one of:

- `continue`
- `kill`
- `pivot`
- `needs_human_confirmation`
