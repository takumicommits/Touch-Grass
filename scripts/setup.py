#!/usr/bin/env python3
"""Touch Grass setup helper, run by /grass:setup. Every change to your settings is backed up first
and can be undone with --undo.

  setup.py --check              report Python, git, OS, current style, and anything that might clash
  setup.py --style on|off       pick (or drop) the Touch Grass reply style in ~/.claude/settings.json
  setup.py --allow              pre-approve routine commands (git status/diff/log/add/commit, builds)
  setup.py --notes TASK.md      the notes file each project keeps
  setup.py --exempt ~/folder    a folder where the hooks do nothing (repeatable)
  setup.py --mark-welcomed      don't show the first-run welcome again
  setup.py --undo               restore your old style and remove the pre-approvals this added

Test override: GRASS_CLAUDE_DIR (instead of ~/.claude).
"""
import json, os, platform, shutil, subprocess, sys, time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

CLAUDE = os.environ.get("GRASS_CLAUDE_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
USER_DIR = os.path.join(CLAUDE, "touch-grass")
SETTINGS = os.path.join(CLAUDE, "settings.json")
RECORD = os.path.join(USER_DIR, "setup.json")
CONFIG = os.path.join(USER_DIR, "config.json")
STYLE = "grass:touch-grass"
ALLOW = [
    "Bash(git status)", "Bash(git status *)", "Bash(git diff)", "Bash(git diff *)", "Bash(git log *)",
    "Bash(git show *)", "Bash(git add *)", "Bash(git commit *)",
    "Bash(swift build)", "Bash(swift build *)", "Bash(swift test *)", "Bash(xcodebuild *)",
    "Bash(npm run *)", "Bash(npm test)", "Bash(dotnet build *)", "Bash(dotnet test *)",
    "Bash(bash .claude/check.sh)",
]
ARGS = sys.argv[1:]


def values(flag):
    return [ARGS[i + 1] for i, a in enumerate(ARGS) if a == flag and i + 1 < len(ARGS)]


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read().strip()
        return json.loads(text) if text else default
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        sys.exit(f"❌ {path} isn't valid JSON ({e}). Fix it first; nothing was changed.")


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2) + "\n")


def backup(path):
    if os.path.isfile(path):
        d = os.path.join(USER_DIR, "backups", time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(d, exist_ok=True)
        shutil.copy2(path, os.path.join(d, os.path.basename(path)))
        return d
    return None


def check():
    lines = [f"✅ Python {platform.python_version()}", f"ℹ️ OS: {platform.system()} {platform.release()}"]
    git = shutil.which("git")
    lines.append("✅ git found" if git else "❌ git not found: the build check and change tracking need it")
    if platform.system() == "Windows" and not shutil.which("bash"):
        lines.append("👀 Git Bash not on PATH; hooks need Git for Windows (git-scm.com)")
    s = read_json(SETTINGS, {})
    style = s.get("outputStyle")
    lines.append(f"ℹ️ current reply style: {style or 'default'}" + (" (Touch Grass)" if style == STYLE else ""))
    if os.path.isfile(os.path.join(CLAUDE, "focus", "installed.json")):
        lines.append("👀 an earlier Focus install is present; its hooks would run twice alongside Touch Grass. "
                     "Remove it with: python3 ~/.claude/focus/install.py --uninstall")
    for name in ("start", "why", "wrap"):
        if os.path.isfile(os.path.join(CLAUDE, "skills", name, "SKILL.md")):
            lines.append(f"ℹ️ you have your own /{name} skill; Touch Grass's is /grass:{name}, so both keep working")
    cfg = read_json(CONFIG, {})
    lines.append(f"ℹ️ notes file: {(cfg.get('notes_files') or ['TASK.md'])[0]}; exempt folders: "
                 f"{', '.join(cfg.get('exempt_dirs', [])) or 'none'}")
    print("\n".join(lines))


def main():
    if not ARGS or "--help" in ARGS:
        print(__doc__)
        return
    if "--check" in ARGS:
        check()
        return
    rec = read_json(RECORD, {})
    msgs = []

    if "--undo" in ARGS:
        s = read_json(SETTINGS, {})
        b = backup(SETTINGS)
        if s.get("outputStyle") == STYLE:
            if rec.get("previous_style"):
                s["outputStyle"] = rec["previous_style"]
            else:
                s.pop("outputStyle", None)
        perms = s.get("permissions", {})
        if "allow" in perms:
            perms["allow"] = [r for r in perms["allow"] if r not in rec.get("allow_added", [])]
            if not perms["allow"]:
                del perms["allow"]
        if "permissions" in s and not s["permissions"]:
            del s["permissions"]
        write_json(SETTINGS, s)
        write_json(RECORD, {})
        print(f"✅ restored your reply style and removed Touch Grass pre-approvals (backup: {b})")
        return

    if values("--style") or "--allow" in ARGS:
        s = read_json(SETTINGS, {})
        b = backup(SETTINGS)
        for v in values("--style"):
            if v == "on" and s.get("outputStyle") != STYLE:
                if "previous_style" not in rec:
                    rec["previous_style"] = s.get("outputStyle")
                s["outputStyle"] = STYLE
                msgs.append("✅ reply style: Touch Grass (applies to new sessions)")
            elif v == "off" and s.get("outputStyle") == STYLE:
                prev = rec.pop("previous_style", None)
                if prev:
                    s["outputStyle"] = prev
                else:
                    s.pop("outputStyle", None)
                msgs.append("✅ reply style restored")
        if "--allow" in ARGS:
            allow = s.setdefault("permissions", {}).setdefault("allow", [])
            added = [r for r in ALLOW if r not in allow]
            allow.extend(added)
            rec["allow_added"] = sorted(set(rec.get("allow_added", [])) | set(added))
            msgs.append(f"✅ pre-approved {len(added)} routine commands (push, delete and restore still ask)")
        write_json(SETTINGS, s)
        if b:
            msgs.append(f"ℹ️ backup: {b}")

    if values("--notes") or values("--exempt"):
        cfg = read_json(CONFIG, {})
        for n in values("--notes"):
            cfg["notes_files"] = [n] + [x for x in cfg.get("notes_files", ["TASK.md", "STATUS.md"]) if x != n]
            msgs.append(f"✅ notes file: {n}")
        for d in values("--exempt"):
            cfg.setdefault("exempt_dirs", [])
            if d not in cfg["exempt_dirs"]:
                cfg["exempt_dirs"].append(d)
            msgs.append(f"✅ hooks skip: {d}")
        write_json(CONFIG, cfg)

    if "--mark-welcomed" in ARGS:
        os.makedirs(USER_DIR, exist_ok=True)
        open(os.path.join(USER_DIR, "welcomed"), "w").close()

    write_json(RECORD, rec)
    print("\n".join(msgs) if msgs else "ℹ️ nothing to change")


if __name__ == "__main__":
    main()
