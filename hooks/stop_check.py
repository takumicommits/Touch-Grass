#!/usr/bin/env python3
"""Stop hook: don't let Claude call it done when
  - the project's .claude/check.sh fails, or
  - this session changed files but the notes file (TASK.md by default) is older than those changes.
Only what changed during this session counts: files that were already modified or untracked when the
session started are ignored unless they change again. Turns that changed nothing pass straight through.
Unattended runs (scheduled, headless, SDK) skip the notes check but still get the build check.
Gives Claude one chance to fix; after that it lets it stop and tells you instead."""
import hashlib, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grass_common as fc

CHECK_TIMEOUT = 600  # seconds
IGNORE_PREFIXES = (".claude/proof/",)


def emit(obj):
    print(json.dumps(obj))
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    cwd = data.get("cwd") or os.getcwd()
    sid = data.get("session_id") or "unknown"
    retrying = bool(data.get("stop_hook_active"))
    cfg = fc.config()
    if fc.is_exempt(cwd, cfg):
        sys.exit(0)
    root = fc.repo_root(cwd)
    if not root:
        sys.exit(0)

    state_file = os.path.join(fc.state_dir(), f"{sid}.json")
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception:
        # No snapshot from session start (e.g. installed mid-session): take one now and let this turn pass.
        os.makedirs(fc.state_dir(), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump({"root": root, "baseline": fc.head(root), "dirty": fc.dirty_files(root)}, f)
        sys.exit(0)

    start_dirty = state.get("dirty", {})
    changed = set()
    # Commits made during this session
    baseline, now_head = state.get("baseline", ""), fc.head(root)
    if baseline and now_head and baseline != now_head:
        _, out = fc.git(root, "diff", "--name-only", baseline, now_head)
        changed |= {l for l in out.splitlines() if l}
    # Uncommitted changes, minus anything untouched since the session started
    now_dirty = fc.dirty_files(root)
    for p, m in now_dirty.items():
        if p not in start_dirty or start_dirty[p] != m:
            changed.add(p)
    for p in start_dirty:
        if p not in now_dirty and p not in changed and fc.mtime(os.path.join(root, p)) != start_dirty[p]:
            changed.add(p)  # was dirty at start, since committed or reverted
    changed = {p for p in changed if not p.startswith(IGNORE_PREFIXES)}
    if not changed:
        sys.exit(0)  # this session changed nothing

    problems = []

    # 1. Notes freshness (projects that keep a notes file; skipped when unattended)
    notes, has_notes = fc.notes_path(root, cfg)
    notes_rel = os.path.relpath(notes, root)
    if has_notes and not fc.is_unattended():
        times = [fc.mtime(os.path.join(root, p)) for p in changed if p != notes_rel]
        newest = max((t for t in times if t is not None), default=0)
        if newest > (fc.mtime(notes) or 0):
            problems.append(f"{notes_rel} is older than your latest changes. Update it "
                            "(goal, done, decisions, open questions, next step).")

    # 2. Project build check, skipped if nothing changed since it last passed
    check = os.path.join(root, ".claude", "check.sh")
    if os.path.isfile(check):
        h = hashlib.sha256(now_head.encode())
        for p in sorted(changed):
            h.update(f"{p}:{fc.mtime(os.path.join(root, p))}".encode())
        fingerprint = h.hexdigest()
        if state.get("check_passed") != fingerprint:
            try:
                shell = shutil.which("bash") or shutil.which("sh") or "bash"
                r = subprocess.run([shell, check], cwd=root, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=CHECK_TIMEOUT)
                ok, output = r.returncode == 0, r.stdout + r.stderr
            except subprocess.TimeoutExpired:
                ok, output = False, f"check.sh timed out after {CHECK_TIMEOUT}s"
            except OSError as e:
                ok, output = False, f"couldn't run check.sh ({e})"
            if ok:
                state["check_passed"] = fingerprint
            else:
                tail = "\n".join(output.strip().splitlines()[-30:])
                problems.append(f".claude/check.sh failed. Fix it before finishing.\n{tail}")

    with open(state_file, "w") as f:
        json.dump(state, f)

    if not problems:
        sys.exit(0)
    if retrying:
        emit({"systemMessage": "❌ Finished with open problems:\n- " + "\n- ".join(p.splitlines()[0] for p in problems)})
    emit({"decision": "block", "reason": "Not done yet:\n- " + "\n- ".join(problems)})


if __name__ == "__main__":
    main()
