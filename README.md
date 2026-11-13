# TranZact Support Bot

[Open the support bot](https://tranzact-support-assistant.lenny870096.chatgpt.site/) · [Test answers and leave feedback](https://tranzact-support-assistant.lenny870096.chatgpt.site/test)

The opening screen offers **Facing an issue**, **Need help**, and **Request new development**, with a topic dropdown and free-text input. The tester uses a chat layout and lets a support reviewer mark each answer **Right** or **Wrong** and submit a correction.

## Knowledge and feedback

The initial import covers 13 November 2025 to 13 November 2026: 7,090 conversations and 597,627 messages, deduplicated by message ID. Search uses 32,197 evidence windows from conversations with customer questions and substantive agent replies. CSV exports, stored knowledge, requests, answer logs, feedback and credentials are excluded from this repository.

The server searches the imported history, passes relevant evidence to the OpenAI Responses API, and includes source dates in its answers. Questions without matching evidence receive a clarification or support-review fallback. Private notes and system events are excluded. Email addresses, phone numbers, links and common secret patterns are removed before indexing. This is basic redaction, not a guarantee that every identifying detail is removed; the live app remains owner-private.

Feedback and corrections are saved for review and do not automatically enter the answer knowledge. Requests are stored in the bot workspace; they do not send email or create Freshdesk tickets.

## Hosting

GitHub stores the source. GitHub Pages serves the `docs/` launch page, which opens the private application. The application and APIs run on Sites / Cloudflare Workers with an R2 binding called `BUCKET`. GitHub Pages cannot execute the private AI and Freshchat server code.

To enable the Pages launch page, open **Settings → Pages → Source → GitHub Actions**, then run the **Publish GitHub Pages** workflow. The expected launch URL is `https://tranzact-support.github.io/support-bot/`. Verify the deployment before sharing this URL.

Runtime secrets are configured on the server: `OPENAI_API_KEY`, `FRESHCHAT_API_TOKEN`, and `FRESHCHAT_BASE_URL`. Never put them in GitHub Pages or browser code. API billing must be enabled for AI-generated answers. The default model is `gpt-4.1-mini`; `OPENAI_MODEL` can override it.

Sites controls sign-in and owner-private access. Do not deploy this Worker to an unprotected public endpoint: the administrative import and refresh routes depend on the platform's owner-private boundary. Sharing the source repository does not grant access to the bot's stored knowledge.

## Build and verify

```sh
npm ci
npm run build
npm test
```

For a local UI preview, run `node scripts/dev-server.mjs` after preparing local seed data. It listens only on `127.0.0.1:8788`, uses a development-only user identity, and does not load production credentials.

`worker/page.html` contains the guided support interface; `worker/tester.html` contains the chat tester. `worker/index.js` owns APIs, retrieval, persistence, feedback and Freshchat refresh. `worker/knowledge.js` handles CSV parsing, redaction, evidence windows and ranking.

The hosted `/mcp` tools expose `knowledge_status` and `refresh_knowledge`. The updater starts a Freshchat raw export, then later calls advance the same report until it completes. Overlapping export windows capture late replies. Scheduled refresh configuration is managed by the linked Site automation; check the live Knowledge page for its current status.
