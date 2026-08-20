# eBack

Track OKX trading fees and affiliate rebates — read-only, from the OKX affiliate API.

- See total fees paid by each invitee (`totalFee`, lifetime or per-period)
- Verify invitees receive the configured rebate rate (default 20%)
- Flag wash-trading red flags (high fee with near-zero volume)
- Export a Markdown report for transparency, or JSON for bots / dashboards

## Why

Traders are blind to fees (0.05% × 500 trades = 25% of capital/month). Affiliates
are blind to whether their invitees actually get the rebate rate promised.
This skill closes both gaps with one read-only API call.

## Requirements

- Python 3.10+ (stdlib only — no pip install)
- OKX API key with **Read** permission, owned by the affiliate master account
- Config via env vars or `.env`: `OKX_KEY`, `OKX_SECRET`, `OKX_PASS`,
  `OKX_DOMAIN` (default `openapi.okx.com`)

## Usage

```bash
# Full rebate report (Markdown → stdout)
python3 scripts/rebate_tracker.py

# JSON for bots
python3 scripts/rebate_tracker.py --json

# Custom expected rate / wash threshold
python3 scripts/rebate_tracker.py --expected-rate 0.25 --wash-fee-min 50

# One invitee (exact UID)
python3 scripts/rebate_tracker.py --uid 835449167911924693

# Monthly report
python3 scripts/rebate_tracker.py --period this_month

# Write to file
python3 scripts/rebate_tracker.py --out report.md
```

## Report flags

- **REBATE_MISMATCH** — `rebateRate` ≠ expected (default 0.20). Verify against
  `inviteeRebateRate` in `/invitee/detail` before acting (they are different fields).
- **WASH** — `totalFee` above threshold (default 10 USDT) with `totalVol` ≈ 0.
  A signal, not a verdict — OKX enforces rebate rules itself.
- **NON_COMPLIANT** — invitee restricted by regional compliance (`isCompliant: false`).

## Notes

- OKX pays rebates automatically via the affiliate link (`inviteeRebateRate`).
  This tool only monitors — it never holds or pays fees.
- Lifetime vs period: `totalFee`/`totalVol`/`totalCommission` are lifetime
  cumulative. Use `--period this_month` or `custom` for period reports.
- Full API field reference: `references/okx-fee-affiliate-api.md`.

## License

MIT — see [LICENSE](LICENSE).
