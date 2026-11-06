---
name: wrap
description: Close out the task. Build check, independent review, proof, commit, notes file and a 3-line handoff, then start fresh. "/grass:wrap quick" skips the review; "/grass:wrap full" forces it.
disable-model-invocation: true
argument-hint: "[quick | full]"
---

Mode: $ARGUMENTS

Close out the current task. Do these in order. Only step 2 can be skipped, and only as described there.

## 1. Check
If `.claude/check.sh` exists, run it. If it fails, fix the cause and run it again. Don't continue until it passes, unless the fix needs the user's decision (then stop and ask).

## 2. Independent review
Decide whether to run it:
- Mode `quick` → skip it.
- Mode `full` → run it.
- No mode → run it only if this session changed more than 2 files. Otherwise skip it.

When skipped, say so in the report as `⏭ Review skipped (small change)` or `⏭ Review skipped (quick)`.

To run it, use the `grass:reviewer` agent. Give it:
- what the task was meant to do (in the user's terms)
- the list of files changed this session
- how to run or see the result

It hasn't seen your work, which is the point. Fix any ❌ it reports, then re-run step 1. Pass its 👀 items to the user, not fixes you weren't asked for.

## 3. Proof
Capture what the user needs to see, the cheapest way that actually shows it:
- Mac app: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/proof-mac.sh" "<App name or path to .app>"`. It saves a window screenshot under `.claude/proof/`.
- Windows app: `powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/proof-win.ps1" -App "<path to .exe, optional>"`. It saves a screenshot under `.claude/proof/`.
- Web app: a browser preview screenshot, if you have a browser tool.
- No visual result: the passing check output, in one line.
- If a screenshot comes out blank or missing the app (some apps hide themselves from screen capture), say so with 👀 and use the check output instead.

## 4. Save state
- Commit everything with a clear message.
- Update the project's notes file (TASK.md unless the session start named another): goal, done, decisions made, open questions, next step. Keep its existing layout; in a newest-first log, add a new dated entry at the top.
- Replace the `## Handoff` section with exactly 3 lines. If the file has no Handoff section, add one near the top:
  1. Where things stand
  2. The very next step
  3. Anything the next session must not forget

## 5. Report
Touch Grass end-of-task list, including the reviewer's 👀 items and the 🧾 proof line. Last line: 🆕 Start a fresh session for the next task.
