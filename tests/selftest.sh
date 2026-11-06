#!/bin/bash
# Touch Grass self-test. Uses throwaway folders and its own settings; touches nothing of yours.
# Prints PASS/FAIL per check, exits non-zero if anything failed. Run: bash tests/selftest.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
H="$ROOT/hooks"
RUN="$H/run.sh"
T="$(mktemp -d)"; fails=0
trap 'rm -rf "$T"' EXIT
export GRASS_STATE="$T/state" GRASS_CONFIG="$T/config.json" GRASS_TEST_HOME="$T/home" GRASS_SETTINGS="$T/settings.json"
unset GRASS_UNATTENDED CLAUDE_CODE_ENTRYPOINT CLAUDE_PLUGIN_DATA
echo '{"outputStyle":"grass:touch-grass"}' > "$GRASS_SETTINGS"
mkdir -p "$T/state"; touch "$T/state/welcomed"
printf '{"notes_files":["TASK.md","STATUS.md"],"exempt_dirs":["%s"],"notes_max_lines":150}\n' "$T/exempt" > "$GRASS_CONFIG"
mkdir -p "$T/home" "$T/exempt"
pass(){ echo "PASS  $1"; }
fail(){ echo "FAIL  $1"; fails=$((fails+1)); }
SID=1
j(){ printf '{"session_id":"t%s","cwd":"%s","stop_hook_active":%s}' "$SID" "$1" "${2:-false}"; }
start(){ j "$1" | bash "$RUN" "$H/session_start.py"; }
stop(){ j "$1" "$2" | bash "$RUN" "$H/stop_check.py"; }
newrepo(){ mkdir -p "$1/.claude" && git -C "$1" init -q && git -C "$1" config user.email t@t && git -C "$1" config user.name t; }
commit(){ git -C "$1" add -A && git -C "$1" commit -qm "$2"; }
tick(){ sleep 1.1; }

# Machine
GRASS_REQUIRE_PYTHON=1 bash "$RUN" -c "pass" 2>/dev/null && pass "Python 3 found" || fail "Python 3.8+ missing"
command -v git >/dev/null && pass "git found" || fail "git missing"

# Welcome once, and rules as context only when the style isn't picked
SID=0; rm -f "$T/state/welcomed"; mkdir -p "$T/w"
grep -q "welcome card" <<<"$(start "$T/w")" && pass "first session shows the welcome" || fail "welcome missing"
! grep -q "welcome card" <<<"$(start "$T/w")" && pass "welcome shows only once" || fail "welcome repeated"
! grep -q "Touch Grass plugin on" <<<"$(start "$T/w")" && pass "style picked: rules not duplicated" || fail "rules duplicated"
echo '{}' > "$GRASS_SETTINGS"
grep -q "Touch Grass plugin on" <<<"$(start "$T/w")" && pass "style not picked: rules load as context" || fail "rules missing"
echo '{"outputStyle":"grass:touch-grass"}' > "$GRASS_SETTINGS"

# Setup helper: style on, pre-approvals, undo restores
C="$T/claude"; mkdir -p "$C"; echo '{"outputStyle":"Explanatory","permissions":{"allow":["Bash(ls *)"]}}' > "$C/settings.json"
GRASS_CLAUDE_DIR="$C" bash "$RUN" "$ROOT/scripts/setup.py" --style on --allow >/dev/null
grep -q '"grass:touch-grass"' "$C/settings.json" && grep -q 'git commit' "$C/settings.json" \
  && pass "setup: style on + pre-approvals" || fail "setup apply"
GRASS_CLAUDE_DIR="$C" bash "$RUN" "$ROOT/scripts/setup.py" --undo >/dev/null
bash "$RUN" -c "import json,sys;s=json.load(open(sys.argv[1]));sys.exit(0 if s=={'outputStyle':'Explanatory','permissions':{'allow':['Bash(ls *)']}} else 1)" "$C/settings.json" \
  && pass "setup: undo restores settings exactly" || fail "setup undo"

# New git code project, no notes file, no build check
P="$T/proj"; newrepo "$P"; echo '{}' > "$P/package.json"; echo v1 > "$P/app.txt"; commit "$P" init
out="$(start "$P")"
grep -q "no TASK.md yet" <<<"$out" && pass "kickoff: points to /start steps when no notes file" || fail "kickoff"
grep -q "no build check yet" <<<"$out" && pass "asks for a build check in code projects" || fail "build check prompt"

# Notes file present
SID=2; printf '# Task\n## Next step\nship it\n' > "$P/TASK.md"; commit "$P" notes
grep -q "ship it" <<<"$(start "$P")" && pass "loads the notes file" || fail "notes load"

# C: long newest-first notes keep the key section that sits far down
SID=3; L="$T/long"; newrepo "$L"
{ echo "# Log"; for i in $(seq 1 600); do echo "- entry $i"; done; echo "## Next step"; echo "deep-next-step-marker"; \
  for i in $(seq 1 500); do echo "- old $i"; done; } > "$L/TASK.md"; commit "$L" long
out="$(start "$L")"; n=$(wc -l <<<"$out")
grep -q "deep-next-step-marker" <<<"$out" && [[ $n -le 160 ]] && pass "long notes → top + key sections ($n lines)" || fail "long notes ($n lines)"

# A: work that existed before the session doesn't count
SID=4; echo old > "$P/untracked-before.txt"; echo v1-dirty > "$P/app.txt"
start "$P" >/dev/null
[[ -z "$(stop "$P")" ]] && pass "chat-only turn in a dirty repo passes" || fail "dirty repo blocked a chat-only turn"
tick; echo v2 > "$P/app.txt"
grep -q '"block"' <<<"$(stop "$P")" && pass "editing a pre-existing dirty file counts" || fail "pre-existing dirty edit missed"
tick; echo "- done" >> "$P/TASK.md"
[[ -z "$(stop "$P")" ]] && pass "allowed once notes are updated" || fail "allow after notes update"

# Build check
printf 'grep -q BROKEN app.txt && { echo "build error"; exit 1; }; exit 0\n' > "$P/.claude/check.sh"
tick; echo BROKEN >> "$P/app.txt"; echo "- more" >> "$P/TASK.md"
grep -q 'check.sh failed' <<<"$(stop "$P")" && pass "failing build check blocked" || fail "failing check"
grep -q systemMessage <<<"$(stop "$P" true)" && pass "no endless loop (warns instead)" || fail "loop guard"

# D: unattended runs skip the notes check
SID=5; Q="$T/q"; newrepo "$Q"; echo '# Task' > "$Q/TASK.md"; echo a > "$Q/a.txt"; commit "$Q" init
start "$Q" >/dev/null; tick; echo b > "$Q/a.txt"
[[ -z "$(GRASS_UNATTENDED=1 stop "$Q")" ]] && pass "unattended run skips the notes check" || fail "unattended"
grep -q '"block"' <<<"$(stop "$Q")" && pass "attended run still checks notes" || fail "attended"

# Exempt folder
SID=6; newrepo "$T/exempt"; echo x > "$T/exempt/x.txt"; commit "$T/exempt" init
[[ -z "$(start "$T/exempt")" ]] && pass "exempt folder: session start silent" || fail "exempt start"
echo y > "$T/exempt/x.txt"
[[ -z "$(stop "$T/exempt")" ]] && pass "exempt folder: never blocked" || fail "exempt stop"

# F: notes in a non-git home folder don't load; other non-git folders do
SID=7; echo "home-notes-marker" > "$T/home/TASK.md"
[[ -z "$(start "$T/home")" ]] && pass "home-folder notes not loaded" || fail "home notes"
mkdir -p "$T/plain"; echo "plain-notes-marker" > "$T/plain/TASK.md"
grep -q plain-notes-marker <<<"$(start "$T/plain")" && pass "non-git project folder notes load" || fail "plain folder"

echo; [[ $fails -eq 0 ]] && echo "ALL PASSED" || echo "$fails FAILED"
exit $fails
