# TranZact Support Bot — GitHub-only edition

[Open the bot](https://tranzact-support.github.io/support-bot/) · [Test answers and leave feedback](https://tranzact-support.github.io/support-bot/test.html)

GitHub Pages hosts the complete interface. Search runs in the browser against encrypted support knowledge. GitHub Actions fetches recent Freshchat transcripts daily and updates the encrypted knowledge. There are **no OpenAI calls, AI API keys or AI API charges**. GitHub and Freshchat account limits still apply.

## What the bot does

Choose **Facing an issue**, **Need help**, or **New development**, then select a topic and type a query. The bot searches relevant historical human support replies and shows their dates. It does not generate new explanations or claim that an old fix applies to the current issue. Where no clear answer exists, it asks for more information.

The initial import covers 13 November 2025–13 November 2026: **7,090 conversations, 597,627 messages, and 32,197 searchable evidence windows**. Private notes, system events and greetings alone are excluded. Basic redaction removes links, emails, phones and common secret patterns before indexing.

## Private knowledge on a public website

All published knowledge and search indexes are encrypted with AES-256-GCM after gzip compression. A random knowledge password is used with PBKDF2-SHA256 (210,000 iterations). The browser decrypts the knowledge after you enter the password. The password is kept in page memory, never in the source or published artifact. Anyone with the password can read the support knowledge, so share it only with authorized testers.

`docs/knowledge/manifest.json` publishes aggregate counts, dates, file names, and encryption parameters; it contains no transcript text. The `.enc.json` files contain ciphertext. Plaintext downloads and local environment files are ignored by Git.

## Feedback and requests

The tester offers **Right answer**, **Wrong answer**, and a correction box. Ratings and development requests are saved **only in the current browser**, with an **Export feedback CSV** button. They are not shared across devices or testers. Export before clearing browser storage. Feedback does not automatically become knowledge.

## Activate daily updates

Add two **repository secrets** in Settings → Secrets and variables → Actions:

- `FRESHCHAT_API_TOKEN`: the existing TranZact Freshchat API token.
- `KNOWLEDGE_PASSWORD`: exactly the password used to unlock the bot. Changing this secret without re-encrypting the existing knowledge will break updates.

The default Freshchat region is `https://api.in.freshchat.com`. Set repository variable `FRESHCHAT_BASE_URL` if the account uses another region.

Run the **Refresh Freshchat knowledge** workflow after adding secrets. It downloads chats since the last successful refresh, overlaps the last two days to capture late messages, excludes private notes, updates encrypted evidence, commits only encrypted knowledge, and publishes Pages. The schedule is **03:30 UTC / around 9:00 AM IST daily**. GitHub scheduled jobs may be delayed; the Knowledge tab and Actions logs show the actual last successful refresh. A failed export does not replace good knowledge or advance its timestamp.

No local computer needs to remain switched on. Missing secrets cause an explicit setup failure rather than a false successful update.

## Development and checks

```sh
npm ci
npm run build
node scripts/build-github.mjs
npm test
node --test scripts/github/test.mjs
```

`docs/client.js` handles browser search, password unlock, local feedback and CSV export. `worker/knowledge.js` holds shared parsing and retrieval functions. `scripts/github/fetch-daily.py` and `update.mjs` implement daily ingestion and encrypted publication. The `worker/` server version is retained as a legacy optional implementation; GitHub Pages does not call it.
