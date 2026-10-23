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
raw+=$'\n'"$(git_scan git grep -nIoE '[0-9]{4}-[0-9]{4}-[0-9]{4}' -- ':!*package-lock.json')"  # 1234-5678-9012 style
accounts="$(grep -vE ':123456789012$|:1234-5678-9012$|^$' <<<"$raw" || true)"
if [ -n "$accounts" ]; then
  echo "$accounts"
  echo "::error::Found 12-digit numbers above that look like AWS account IDs. The deploy reads the account from AWS."
  status=1
fi

# Emails in author/committer fields and commit messages across the whole history (file contents are scanned in the
# current tree only). Anything that looks like an email must be a no-reply address.
raw="$(git_scan git log --format='%ae%n%ce%n%B')"
authors="$(grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' <<<"$raw" | grep -vE '^$|^(noreply@(github|anthropic)\.com|[^@ ]+@(users\.)?noreply\.(github|anthropic)\.com)$' | sort -u || true)"
if [ -n "$authors" ]; then
  echo "$authors"
  echo "::error::Commit author or committer emails above are not no-reply addresses. Use a noreply git email and keep addresses out of commit messages."
  status=1
fi

# Names from the PII_DENYLIST secret (comma- or newline-separated, never printed).
if [ -n "${PII_DENYLIST:-}" ]; then
  IFS=',' read -r -d '' -a words <<<"${PII_DENYLIST//$'\n'/,}" || true
  history="$(git_scan git log --format='%an %ae %cn %ce %B')"
  for word in "${words[@]}"; do
    word="${word#"${word%%[![:space:]]*}"}"  # trim without echo/xargs, which mangle "-n" and apostrophes
    word="${word%"${word##*[![:space:]]}"}"
    [ -z "$word" ] && continue
    tracked="$(git_scan git grep -liwF -- "$word" -- ':!*package-lock.json')"
    if [ -n "$tracked" ] || grep -qiwF -- "$word" <<<"$history"; then
      echo "::error::A word from PII_DENYLIST appears in tracked files or commit history (not printed, to keep it private)."
      status=1
    fi
  done
elif [ -n "${GITHUB_ACTIONS:-}" ]; then
  # Fork and Dependabot runs don't get the Actions secret (add it as a Dependabot secret too); say so, don't pass silently.
  echo "::warning::PII_DENYLIST is not available on this run, so the private-name check was skipped."
fi

# Real booking emails and exports: only made-up samples under tests/fixtures are allowed.
raw="$(git_scan git ls-files)"
datafiles="$(grep -v '^tests/fixtures/' <<<"$raw" | grep -iE '\.(eml|msg|mbox|ics|xlsx|xlsm|xls|csv|pdf|doc|docx|rtf|zip|har)$' || true)"
if [ -n "$datafiles" ]; then
  echo "$datafiles"
  echo "::error::Email or data files are tracked above. Booking emails and exports must stay out of the repo."
  status=1
fi

[ "$status" -eq 0 ] && echo "No personal data found"
exit "$status"
