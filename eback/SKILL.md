---
name: eback
description: >
  Track OKX trading fees and affiliate rebates from the affiliate API — see total
  fees paid by each invitee, verify they receive the correct rebate rate (e.g.
  20%), detect wash-trading red flags (high fee with near-zero volume), and export
  a Markdown report for transparency. Use when the user asks: "how much fees did my
  invitees pay", "are my invitees getting 20% rebate", "rebate report", "fee report",
  "who is washing", "affiliate commission check", "tổng phí khách trả", "khách có
  nhận đủ 20% hoàn phí không", "báo cáo hoàn phí". Works read-only with a Read
  permission API key — no trade/withdraw access needed.
license: MIT
metadata:
  author: hedra
  display_name: eBack
  version: "0.2.0"
  agent:
    requires:
      bins: ["okx"]
---

# eBack — Fee & Rebate Tracker (OKX Affiliate)

Track what invitees actually pay in trading fees and whether they receive the
rebate rate you configured (default 20%). Read-only. No order placement.

**Data source**: `GET /api/v5/affiliate/invitee/list` (paginated, lifetime stats:
`totalFee`, `totalVol`, `rebateRate`, `totalCommission`) — full field reference in
`references/okx-fee-affiliate-api.md`.

**Skill routing**
- Affiliate fee/rebate tracking → `eback` (this skill)
- Market data / indicators → `okx-cex-market`
- Account balance / positions → `okx-cex-portfolio`

## Prerequisites (once)

1. OKX API key with **Read** permission (affiliate endpoints require the key
   owned by the affiliate master account). Set in `~/.okx/config.toml` via
   `okx config init`, or via env vars: `OKX_KEY`, `OKX_SECRET`, `OKX_PASS`,
   `OKX_DOMAIN` (default `openapi.okx.com`; `us.okx.com` for US/AU, `eea.okx.com`
   for EU — see `references/okx-fee-affiliate-api.md` §Domain).
2. Run the preflight once per session:
   ```bash
   okx upgrade   # silently skips if checked <12h ago
   ```

## Usage

### 1. Full rebate report (default)

```bash
python3 scripts/rebate_tracker.py
```

Output (stdout, Markdown):
- Summary: invitee count, total fee (USDT), total commission, total volume
- Per-invitee rows: UID, join time, `rebateRate`, `totalFee`, `totalVol`,
  `totalCommission`, flags
- **REBATE_MISMATCH** flag: `rebateRate` ≠ expected (0.20 default) → the invitee
  is not receiving the configured 20% rebate — investigate
- **WASH** flag: `totalFee` > threshold (default 10 USDT) but `totalVol` ≈ 0 →
  possible wash/self-trading red flag (OKX handles rebate itself, but flag it)

### 2. JSON output (for bots / dashboards)

```bash
python3 scripts/rebate_tracker.py --json
```

### 3. Custom expected rebate rate

```bash
python3 scripts/rebate_tracker.py --expected-rate 0.25 --wash-fee-min 50
```

### 4. Specific invitee (exact UID match)

```bash
python3 scripts/rebate_tracker.py --uid 835449167911924693
```

## Checklist (run before sharing a report)

- [ ] `python3 scripts/rebate_tracker.py --help` runs (no auth needed)
- [ ] Full run returns `code: "0"` with invitee data
- [ ] Every flagged `REBATE_MISMATCH` invitee checked against
      `inviteeRebateRate` in `GET /api/v5/affiliate/invitee/detail` (self rebate
      rate the invitee sees — source of truth for what they receive)
- [ ] `--json` output validated (no PII beyond UID + country; do not publish
      `channelName` if it is sensitive)
- [ ] Report states OKX pays rebates automatically via the link
      (`inviteeRebateRate`) — this tool only monitors, never holds or pays fees

## Bẫy — đừng lặp (traps)

1. **`rebateRate` vs `inviteeRebateRate` là 2 thứ khác nhau** — `rebateRate` on
   `/invitee/list` = effective rate from the active rebate rule; `inviteeRebateRate`
   on `/invitee/detail` = self rebate rate the invitee sees. Verify a mismatch flag
   against `/invitee/detail` before acting. (docs §invitee/detail)
2. **Pagination** — `/invitee/list` is 1-indexed pages, `limit` clamped [1,100],
   response carries `totalPage` at the same level as `data`. Loop pages until the
   page counter exceeds `totalPage`; never assume a single page. (docs §invitee/list)
3. **Lifetime vs period fields** — `totalFee`/`totalVol`/`totalCommission` are
   LIFETIME cumulative. For a monthly report use `periodType=this_month` or
   `custom` begin/end (window ≤ 90 days, begin ≥ 180 days back). Don't subtract
   lifetime values across calls (double-count risk — delta logic from PLAN.md).
4. **Wash flag is a signal, not a verdict** — high fee + low volume can be
   legitimate (small spreads, maker rebates). Flag it, don't auto-exclude; OKX
   itself enforces rebate rules.
5. **Never print secrets** — the script reads keys from config/env only; a
   `--leak` scan must stay clean. Reports contain UID + country only.

## References

- `references/okx-fee-affiliate-api.md` — official OKX affiliate API fields
  (`invitee/list`, `invitee/detail`, `performance/summary`, `link/list`) +
  `GET /api/v5/account/trade-fee` + domain rules + error codes. Open when unsure
  about a field, pagination, or domain.
