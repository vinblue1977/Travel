#!/usr/bin/env bash
# Public repo: fails on personal data in tracked files or commit history.
set -euo pipefail

status=0

# Runs a git command and prints its output; "no match" (git grep exit 1) is fine, a real git failure aborts the
# guard instead of letting it print "No personal data found" without having scanned anything.
git_scan() {
  local out rc=0
  out="$("$@")" || rc=$?
  [ "$rc" -le 1 ] || { echo "::error::git failed (exit $rc): $*" >&2; exit 2; }
  printf '%s' "$out"
}

# Emails (-o prints only the matched token, so an allowed address can't hide a real one on the same line),
# except no-reply and example addresses.
raw="$(git_scan git grep -nIoE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -- ':!*package-lock.json')"
emails="$(grep -vE ':(noreply@(github|anthropic)\.com|[^:]*@(users\.)?noreply\.(github|anthropic)\.com|[^:]*@example\.(com|org))$' <<<"$raw" || true)"
if [ -n "$emails" ]; then
  echo "$emails"
  echo "::error::Found email addresses above. Personal emails stay out of this public repo."
  status=1
fi

# AWS account IDs, except the docs example used in tests.
raw="$(git_scan git grep -nwoE '[0-9]{12}' -- ':!*package-lock.json')"
accounts="$(grep -vE ':123456789012$' <<<"$raw" || true)"
if [ -n "$accounts" ]; then
  echo "$accounts"
  echo "::error::Found 12-digit numbers above that look like AWS account IDs. The deploy reads the account from AWS."
  status=1
fi

# Names from the PII_DENYLIST secret (comma-separated, never printed).
if [ -n "${PII_DENYLIST:-}" ]; then
  IFS=',' read -r -a words <<<"$PII_DENYLIST"
  history="$(git log --format='%an %ae %cn %ce %B')"  # read once: grep -q on a pipe can SIGPIPE git under pipefail
  for word in "${words[@]}"; do
    word="${word#"${word%%[![:space:]]*}"}"  # trim without echo/xargs, which mangle "-n" and apostrophes
    word="${word%"${word##*[![:space:]]}"}"
    [ -z "$word" ] && continue
    if git grep -qiwF -- "$word" -- ':!*package-lock.json' || grep -qiwF -- "$word" <<<"$history"; then
      echo "::error::A word from PII_DENYLIST appears in tracked files or commit history (not printed, to keep it private)."
      status=1
    fi
  done
elif [ -n "${GITHUB_ACTIONS:-}" ]; then
  # Fork and Dependabot runs don't get the secret; say so instead of passing silently.
  echo "::warning::PII_DENYLIST is not available on this run, so the private-name check was skipped."
fi

# Real booking emails and exports: only made-up samples under tests/fixtures are allowed.
raw="$(git_scan git ls-files)"
datafiles="$(grep -v '^tests/fixtures/' <<<"$raw" | grep -iE '\.(eml|msg|mbox|xlsx|xls|csv|pdf)$' || true)"
if [ -n "$datafiles" ]; then
  echo "$datafiles"
  echo "::error::Email or data files are tracked above. Booking emails and exports must stay out of the repo."
  status=1
fi

[ "$status" -eq 0 ] && echo "No personal data found"
exit "$status"
