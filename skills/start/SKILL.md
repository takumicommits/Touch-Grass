---
name: start
description: Kick off a task the Touch Grass way. Every question asked once, upfront (often none), approval only for big or risky work, then work alone until done or blocked.
disable-model-invocation: true
argument-hint: "[what you want done]"
---

Task from the user: $ARGUMENTS
(If you were pointed here by the session-start note instead of the command, the task is the user's message.)

Follow these steps in order.

## 1. Load context (silently)
- Read the project's notes file: the one named at session start, else TASK.md at the project root. If there is none, create TASK.md by copying `${CLAUDE_PLUGIN_ROOT}/templates/TASK.md` and filling in the Goal.
- Check whether `.claude/check.sh` exists. If it doesn't and this is a code project, note that for step 3.

## 2. Questions (all upfront, often none)
1. Walk through the whole task in your head first, start to finish.
2. Collect every decision you'll hit, now AND later: scope, look and feel, edge cases, what "done" looks like, what must not change.
3. Keep only questions where ALL are true:
   - a wrong guess means real rework, not a quick tweak
   - two or more options are genuinely reasonable
   - the code, the notes file and common sense don't settle it
4. Ask them all at once with the AskUserQuestion tool: at most 4, short button labels, recommended option first.
5. Everything else: decide, and list it as 👀 in the plan.

0–2 questions is typical. Zero is fine. Never ask in several rounds.

## 3. Plan
Show the plan in the Touch Grass style:
- Numbered steps, at most 7.
- A 👀 line for each assumption.
- How you'll prove it works (screenshot, recording, or a check that passes).
- If `.claude/check.sh` is missing in a code project, add a step to create it: the fastest command that proves the project still builds (e.g. `swift build`, `xcodebuild … build -quiet`, `npm run build`, `dotnet build`), and test it once.

Ask for a go-ahead only if the work is large, hard to undo, or changes something the user would notice right away. Otherwise show the plan in 3 lines and start immediately; the user can interrupt anytime.

## 4. Work alone
- Don't check in for progress or ask new questions. Stop only when done, or when blocked by something nobody could have foreseen that only the user can decide.
- Commit after each step that works, with a clear message.
- If a decision comes up that's cheap to reverse, make it, log it under Decisions made in the notes file, and mark it 👀 in your final reply.
- Keep the notes file current as you go.

## 5. Finish
End with the Touch Grass end-of-task list and a 🧾 proof line. Then one line: **"/grass:wrap"** when happy, or say what's off.
