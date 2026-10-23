# Travel

A personal, single-user travel planner. Forward flight, hotel and car reservation emails and get one card
per trip with every booking, plus push reminders for check-in, departure and pickup.

Status: planning. See [ROADMAP.md](ROADMAP.md).

## Design

- Dark mode only.
- AWS (us-east-2): Python Lambdas, DynamoDB, CDK in Python, a TypeScript/Preact PWA.
- Booking emails are read from a Gmail label and parsed with Claude on Amazon Bedrock.
- Built to stay inside the AWS free tiers; the only metered cost is Bedrock.
