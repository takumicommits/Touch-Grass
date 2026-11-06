---
name: setup
description: Set up or change Touch Grass. Checks the machine, turns on the reply style, optionally pre-approves routine commands, runs the self-test, and shows the welcome. "/grass:setup undo" reverses it; "/grass:setup exempt <folder>" and "/grass:setup notes <file>" change settings.
argument-hint: "[undo | exempt <folder> | notes <file>]"
---

Arguments: $ARGUMENTS

Talk in the Touch Grass style: short numbered Markdown lists with icons, no essays. You run every command; the user only clicks.

The helper is `${CLAUDE_PLUGIN_ROOT}/scripts/setup.py`. Always run it through the Python launcher:
`bash "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh" "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" <flags>`

## Shortcuts
- `undo` → run with `--undo`, report its line, stop.
- `exempt <folder>` → run with `--exempt <folder>`, report, stop.
- `notes <file>` → run with `--notes <file>`, report, stop.
- No arguments → the full setup below.

## Full setup

**1. Check the machine.** Run the launcher with `GRASS_REQUIRE_PYTHON=1` in front and `--check`.
- Exit code 3 means no Python 3. Ask with buttons whether to install it:
  - Windows: `winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements`, then tell the user to quit and reopen the Claude app and run **"/grass:setup"** again.
  - macOS: `xcode-select --install`, then tell the user to click **Install** in the popup, wait, and run **"/grass:setup"** again.
  - Linux: suggest their package manager's `python3` package.
- `bash` not found at all (Windows without Git for Windows): tell the user to install Git for Windows from git-scm.com, reopen the app, and run **"/grass:setup"** again. Stop.

**2. Ask once, with buttons** (AskUserQuestion, one batch):
- "Use the Touch Grass reply style?" → **Turn it on** (recommended) / **Not now**. Without it the rules still load into each session, just less firmly.
- "Pre-approve routine commands (git status, diff, add, commit, builds) so you see fewer permission prompts?" → **Yes** (recommended) / **No**. Push, delete and restore always still ask.
- Only if the check reported an earlier Focus install: "Remove the earlier Focus install so hooks don't run twice?" → **Remove** (recommended) / **Keep**.

**3. Apply.** Run the launcher with `--mark-welcomed`, plus `--style on` if chosen, plus `--allow` if chosen. If they chose **Remove**: `python3 ~/.claude/focus/install.py --uninstall` (use `python` or `py` if `python3` is missing).

**4. Self-test.** `bash "${CLAUDE_PLUGIN_ROOT}/tests/selftest.sh"`. Every line should say PASS. If one fails, don't edit the plugin's files: report it with ❌ and suggest opening an issue at github.com/takumicommits/touch-grass/issues with the output.

**5. Celebrate.** Show the welcome card from `${CLAUDE_PLUGIN_ROOT}/skills/welcome/SKILL.md` exactly as written. Then:

1. ✅ Touch Grass is set up
2. 👉 Start a new session so the reply style loads
3. ℹ️ Undo anytime: **"/grass:setup undo"**
