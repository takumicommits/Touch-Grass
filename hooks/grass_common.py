"""Shared helpers for the Touch Grass hooks: settings, notes file, exempt folders, git snapshots.

Settings live in ~/.claude/touch-grass/config.json (change them with /grass:setup):
  notes_files      names to look for, in order; the first one found is the project's notes file,
                   and the first name is used when a project has none yet   (default TASK.md, STATUS.md)
  exempt_dirs      folders where the hooks do nothing, e.g. ones unattended jobs run in
  notes_max_lines  how much of a long notes file to load at session start   (default 150)

Test overrides (used by tests/selftest.sh): GRASS_CONFIG, GRASS_STATE, GRASS_TEST_HOME, GRASS_SETTINGS.
"""
import json, os, re, subprocess, sys

# Windows consoles default to a legacy code page; icons in our messages need UTF-8.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DIR = os.path.join(os.path.expanduser("~"), ".claude", "touch-grass")
STYLE_NAME = "touch-grass"
DEFAULTS = {"notes_files": ["TASK.md", "STATUS.md"], "exempt_dirs": [], "notes_max_lines": 150}
CODE_MARKERS = {"Package.swift", "package.json", "pyproject.toml", "setup.py", "requirements.txt",
                "Cargo.toml", "go.mod", "Gemfile", "pom.xml", "build.gradle", "build.gradle.kts",
                "Makefile", "CMakeLists.txt", "deno.json", "composer.json", "pubspec.yaml"}
CODE_SUFFIXES = (".xcodeproj", ".xcworkspace", ".csproj", ".sln", ".fsproj", ".vcxproj")


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def config():
    cfg = dict(DEFAULTS)
    path = os.environ.get("GRASS_CONFIG") or os.path.join(USER_DIR, "config.json")
    try:
        cfg.update(json.loads(read_text(path)))
    except Exception:
        pass
    if not cfg.get("notes_files"):
        cfg["notes_files"] = DEFAULTS["notes_files"]
    return cfg


def state_dir():
    return (os.environ.get("GRASS_STATE")
            or (os.path.join(os.environ["CLAUDE_PLUGIN_DATA"], "state") if os.environ.get("CLAUDE_PLUGIN_DATA") else None)
            or os.path.join(USER_DIR, "state"))


def welcome_marker():
    """Lives in ~/.claude/touch-grass so /grass:setup (which can't see the plugin data folder) can set it too."""
    return os.path.join(os.environ.get("GRASS_STATE") or USER_DIR, "welcomed")


def real(path):
    return os.path.realpath(os.path.expanduser(path))


def home():
    return real(os.environ.get("GRASS_TEST_HOME") or "~")


def style_active(cwd):
    """True when a settings file picks the Touch Grass output style (then the style itself carries the rules)."""
    paths = [os.environ.get("GRASS_SETTINGS") or os.path.join(os.path.expanduser("~"), ".claude", "settings.json")]
    if not os.environ.get("GRASS_SETTINGS"):
        paths += [os.path.join(cwd, ".claude", "settings.json"), os.path.join(cwd, ".claude", "settings.local.json")]
    for p in paths:
        try:
            if STYLE_NAME in str(json.loads(read_text(p)).get("outputStyle", "")):
                return True
        except Exception:
            pass
    return False


def style_rules():
    """The output style's body, without its frontmatter."""
    text = read_text(os.path.join(PLUGIN_ROOT, "output-styles", "touch-grass.md"))
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()

def is_exempt(path, cfg):
    rp = real(path)
    for d in cfg.get("exempt_dirs", []):
        d = real(d)
        if rp == d or rp.startswith(d + os.sep):
            return True
    return False


def is_unattended():
    """Scheduled, headless or SDK runs: nobody is there to read a nudge."""
    if os.environ.get("GRASS_UNATTENDED") == "1":
        return True
    return os.environ.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk")


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return 1, ""  # git isn't installed
    return r.returncode, r.stdout


def repo_root(cwd):
    rc, out = git(cwd, "rev-parse", "--show-toplevel")
    return out.strip() if rc == 0 else None


def head(root):
    rc, out = git(root, "rev-parse", "HEAD")
    return out.strip() if rc == 0 else ""


def notes_path(folder, cfg):
    """(path, exists): the first configured notes file found, else where a new one would go."""
    for name in cfg["notes_files"]:
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            return p, True
    return os.path.join(folder, cfg["notes_files"][0]), False


def is_code_project(root):
    try:
        names = os.listdir(root)
    except OSError:
        return False
    return any(n in CODE_MARKERS or n.endswith(CODE_SUFFIXES) for n in names)


def mtime(path):
    try:
        return os.stat(path).st_mtime_ns
    except OSError:
        return None


def dirty_files(root):
    """{relative path: mtime or None} for every changed, staged or untracked file (gitignore respected)."""
    rc, out = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    files = {}
    if rc != 0:
        return files
    parts = out.split("\0")
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if len(rec) < 4:
            continue
        x, path = rec[0], rec[3:]
        if x in "RC":
            i += 1  # the next record is the original path of a rename/copy
        files[path] = mtime(os.path.join(root, path))
    return files


KEY_HEADING = re.compile(
    r"^(#{1,6})\s*(goal|next( steps?)?|handoff|open questions?|blockers?|current( focus| state)?|now|"
    r"decisions?( made)?)\b", re.I)
HEADING = re.compile(r"^(#{1,6})\s")


def notes_excerpt(path, max_lines):
    """Whole file when short. When long: the top (newest entries in newest-first logs)
    plus the first copy of each key section (goal, next step, open questions, handoff…)."""
    lines = read_text(path).splitlines()
    name = os.path.basename(path)
    if len(lines) <= max_lines:
        return f"Notes file for this project: {name} (read before starting):\n" + "\n".join(lines)

    top_n = min(40, max_lines // 3)
    keep = set(range(top_n))
    seen = set()
    for i, line in enumerate(lines):
        m = KEY_HEADING.match(line)
        if not m:
            continue
        key = m.group(2).lower().split()[0]
        if key in seen:
            continue
        seen.add(key)
        level = len(m.group(1))
        j = i + 1
        while j < len(lines) and j - i < 30:
            h = HEADING.match(lines[j])
            if h and len(h.group(1)) <= level:
                break
            j += 1
        keep.update(range(i, j))

    out, last = [], -1
    for i in sorted(keep):
        if len(out) >= max_lines:
            break
        if last != -1 and i != last + 1:
            out.append("…")
        out.append(lines[i])
        last = i
    header = (f"Notes file for this project: {name} ({len(lines)} lines). Showing the top and its key sections "
              f"(goal, next step, open questions, handoff). Read more of it only if the task needs older detail:")
    return header + "\n" + "\n".join(out)
