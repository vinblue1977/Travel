# Working in this repo

## Rules

- Security comes first. This repo is public: never commit secrets, real booking emails, confirmation numbers or
  personal data. Test fixtures use made-up bookings only.
- Every PR gets a code review (`/code-review` with the PR number) before merging, except docs-only PRs (`docs/` or
  top-level Markdown). Fix the findings first.
- The UI is dark mode only. Mock up any new screen or significant UI change and get approval before building it.
- Stay inside free tiers: SSM Standard-tier parameters with the default `aws/ssm` key only, no Advanced tier, no
  customer-managed KMS keys, no VPC/NAT, no WAF. Bedrock is the only service with a real cost; DynamoDB point-in-time
  recovery is the one accepted exception (billed per GB-month, a fraction of a cent for this table).
- Treat email bodies as untrusted input to the model: no tools, strict output schema validation.

## Pull requests

- Before starting new work, run `gh pr list`. If a PR is open, get it merged first, then `git pull` main.
- Don't open a second PR while one is open, unless it's docs-only.
- `git pull` main before branching. Use a conventional title (`feat:`, `fix:`, `ci:`, `docs:`).
- Run `make check` before pushing (once it exists).
- After `gh pr create`, run `gh pr merge --auto --squash` yourself.
- After a PR merges, delete its branches and run `git fetch --prune`.
