#!/usr/bin/env python3
"""SessionStart hook (costs no model tokens to run; what it prints is added to Claude's context).
  - first session after install: asks Claude to show the welcome card once
  - Touch Grass style not selected: adds its rules as context, so the plugin works with zero setup
  - remembers which files were already changed when the session began, so the Stop hook
    only judges what this session changed
  - loads the project's notes file (all of it when short, the key parts when long)
  - git project with no notes file: points Claude at /grass:start's steps for tasks that change files
  - code project with no build check: asks Claude to create .claude/check.sh
Exempt folders get nothing. A notes file in your home folder isn't loaded unless home is a git project."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grass_common as gc


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    cwd = data.get("cwd") or os.getcwd()
    sid = data.get("session_id") or "unknown"
    cfg = gc.config()
    if gc.is_exempt(cwd, cfg):
        return
    out = []
    os.makedirs(gc.state_dir(), exist_ok=True)

    welcomed = gc.welcome_marker()
    if not os.path.isfile(welcomed) and not gc.is_unattended():
        welcome = os.path.join(gc.PLUGIN_ROOT, "skills", "welcome", "SKILL.md")
        out.append("Touch Grass was just installed and this person hasn't seen its welcome yet. At the top of "
                   f"your first reply, show the welcome card from {welcome} exactly as written there, then "
                   "handle their message as usual.")
        os.makedirs(os.path.dirname(welcomed), exist_ok=True)
        with open(welcomed, "w") as f:
            f.write("1\n")

    if not gc.style_active(cwd):
        out.append("The user has the Touch Grass plugin on. Follow these rules for every reply and task:\n\n"
                   + gc.style_rules())

    root = gc.repo_root(cwd)
    if root:
        state_file = os.path.join(gc.state_dir(), f"{sid}.json")
        if not os.path.isfile(state_file):  # keep the first snapshot across resume/compact
            with open(state_file, "w") as f:
                json.dump({"root": root, "baseline": gc.head(root), "dirty": gc.dirty_files(root)}, f)

    folder = root or cwd
    at_home = not root and gc.real(cwd) == gc.home()
    if not at_home:
        path, exists = gc.notes_path(folder, cfg)
        if exists:
            out.append(gc.notes_excerpt(path, int(cfg.get("notes_max_lines", 150))))
        elif root:
            start = os.path.join(gc.PLUGIN_ROOT, "skills", "start", "SKILL.md")
            out.append(f"This git project has no {os.path.basename(path)} yet. If the user's task changes files, "
                       f"first read {start} and follow it, using their message as the task. "
                       "For questions or chat, ignore this.")

    if root and gc.is_code_project(root) and not os.path.isfile(os.path.join(root, ".claude", "check.sh")):
        out.append("This code project has no build check yet (.claude/check.sh). If the user's task changes code, "
                   "create it before finishing: the fastest command that proves the project still builds "
                   "(e.g. `swift build`, `xcodebuild … build -quiet`, `npm run build`, `dotnet build`). Run it once, "
                   "and mention it in your reply with 👀. If the project truly can't be checked, make the file "
                   "contain `# no build check` and `exit 0`. For questions or chat, ignore this.")
    if out:
        print("\n\n".join(out))


if __name__ == "__main__":
    main()
