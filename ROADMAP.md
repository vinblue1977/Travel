# Roadmap

When an item is finished, move it into Done.

## Done

Nothing yet.

## Next

- Repo, CI and a first CDK stack (DynamoDB, GitHub OIDC deploy role).
- Data model for trips and bookings (flight, hotel, car).
- Email parser: Claude Haiku 4.5 on Bedrock, strict schema validation, Sonnet 4.5 fallback.
- Trip grouping by destination city and date overlap; API to paste an email, list trips, edit and delete.
- Dark-only PWA (mockup approved first): sign-in, trip cards, trip detail, add booking.

## Then

- Poll a Gmail "Travel" label over IMAP so forwarding works.
- Web Push reminders: flight check-in, leave for the airport, hotel check-in, car pickup.

## Later

- Top sightseeing places per city (Bedrock, cached per city).
- Sri Lankan restaurants within 50 miles (OpenStreetMap first; real data, not LLM-invented places).

## Watch

- Haiku 5.5 / Sonnet 5.5 have a 0 tokens-per-minute Bedrock quota on this account; switch once raised.
