# Travel

A personal, single-user travel planner. Forward flight, hotel and car reservation emails and get one card
per trip with every booking, plus push reminders for check-in, departure and pickup.

Status: planning. See [ROADMAP.md](ROADMAP.md).

## Design

- Dark mode only.
- AWS (us-east-2): Python Lambdas, DynamoDB, CDK in Python, a TypeScript/Preact PWA.
- Booking emails are read from a Gmail label and parsed with Claude on Amazon Bedrock.
- Built to stay inside the AWS free tiers; the only metered cost is Bedrock.

## Development

```sh
make install   # Python venv (uv if installed) + Node tools
make check     # everything CI runs: privacy, lint, tests, audit, synth
```

Merges to `main` deploy to AWS automatically (GitHub OIDC, no stored keys). Progress: [ROADMAP.md](ROADMAP.md).

### First-time AWS setup

CI deploys through a role that the stack itself creates, so the very first deploy is manual:

1. The account needs `cdk bootstrap` for `us-east-2` and the GitHub OIDC provider
   (`token.actions.githubusercontent.com`). Both already exist when other stacks share the account; the stack never creates them.
2. `make install`, sign in with the AWS CLI, then `. .venv/bin/activate && npx --no-install cdk deploy`.
3. In the repo settings create an environment named `production` (deployment branches: `main` only) and add the secret
   `AWS_DEPLOY_ROLE_ARN` with the `GitHubDeployRoleArn` output.
4. Merging to `main` now deploys. After a failed deploy, redeploy with `gh workflow run ci.yml --ref main`.
