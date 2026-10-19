# Reward opportunity discovery from configured resources (#1270 D1)

This provider-free module and read-only GET /api/reward-opportunities endpoint consume the same sanitized Model Control /api/resources read model (hybrid mode), and optional allowlisted Windows running-app names. They do not open session stores, credentials, API keys or provider pages, and do not execute sign-in, provider inference, reward redemption or quota refresh.

**Provider candidates, not verified account eligibility:** every discovered record has account_verified=false, can_auto_claim=false, claim_performed=false and reward_received=null. This is deliberate even if a Connection or Magpie account is present. Arbitrary friendly Connection names do not count as provider identity; only exact known upstream_provider_id or Magpie provider keys are mapped. No configured account produces NOT_CONFIGURED_OR_UNVERIFIED, not a false 'no check-in required'.

- TRAE Work: A first-party community wiki https://forum.trae.cn/t/topic/182999 describes daily sign-in and the official community confirms its profile-menu entry. Historical TRAE SOLO CN desktop process label MAY belong to TraeWork following 2026-06-09 rename per https://docs.trae.cn/work_changelog. Must inspect account-specific UI before declaring a claimable reward. Third-party scripts use reverse-engineered private endpoints and token extraction; this implementation does NOT use them.
- WorkBuddy: Current Tencent policy https://intl.cloud.tencent.com/zh/document/product/1316/84378 describes automatic daily active rewards after genuine desktop activity, NOT a click-to-check-in. Scripted fake activity is explicitly prohibited by provider rules. An installed process does not imply logged-in eligibility or a credited reward.
- Codex/Claude subscription limit windows are passive quota phenomena, not daily check-ins. Claude banked reset redemption is a separate official/manual flow, not generic daily sign-in.

This slice deliberately implements resource inventory and local API only. Future D2 still requires an official approved claiming method, a specific opted-in account, a verified receipt, and durable per-account-per-period fencing. The resource UI opt-in controls and daily scheduler are NOT implemented here. Do not treat this PR as completed live automatic sign-in.

Tests: python -m pytest tests/platform_v1/test_reward_opportunities.py tests/platform_v1/test_reward_discovery.py tests/test_reward_claims.py -q.
