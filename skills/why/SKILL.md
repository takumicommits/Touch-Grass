---
name: why
description: Expand one numbered item from your last reply into its reasoning. Usage "/grass:why 2". With no number, explains every 👀 item.
disable-model-invocation: true
argument-hint: "[item number]"
---

Item requested: $ARGUMENTS

Look at your most recent reply before this command.

- If a number was given, find that numbered item.
- If no number was given, take every 👀 item in that reply.
- If the number doesn't exist, list the numbered items in one line each and stop.

For each item, answer in 3–5 bullets, in everyday words, from what you already know. Don't start new work, edit files, or run tools unless a fact is truly missing:

- **Why**: the reason you did it or concluded it
- **Instead of**: the main alternative you passed on, and why
- **Assumed**: what you took for granted (👀 anything unverified)
- **Risk**: what would break or look wrong if that's mistaken
- **Check**: the fastest way the user can confirm it, ideally by looking at something

No preamble. Then stop and wait.
