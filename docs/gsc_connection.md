# GSC (Google Search Console) Connection (step-by-step)

Purpose
- Document how Google Search Console integration is configured, authenticated, and used to map queries to pages.

Files involved
- `dashboard/services/gsc_*` or any module handling GSC interactions
- `docs/GSC_SETUP_GUIDE.md` (existing)

Step-by-step implementation
1. API credentials
   - Create a Google Cloud project, enable Search Console API, and create OAuth credentials or service account depending on flow.
   - Follow `docs/GSC_SETUP_GUIDE.md` for setup details.
2. Storing credentials
   - Store client secrets securely (env vars or a protected JSON file outside VCS). Do not commit keys.
3. Authentication flow
   - For user-scoped OAuth: implement the consent flow and store refresh tokens encrypted.
   - For service account: grant access to desired GSC properties and use JWT signing to fetch data.
4. Data import
   - Implement periodic fetch tasks to map queries -> pages and update internal DB tables linking keywords to pages.
5. Error handling
   - Handle rate limits and expired tokens, plus retries and logging.
6. Tests
   - Mock GSC responses locally and assert mapping logic.

Security
- Keep credentials out of the repo and rotate keys regularly.
