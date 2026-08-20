#!/usr/bin/env python3
"""rebate_tracker.py — OKX affiliate fee & rebate tracker (read-only).

Kéo GET /api/v5/affiliate/invitee/list (paginated), tổng hợp phí/hoàn phí
theo khách, đối soát rebateRate với mức kỳ vọng (mặc định 0.20 = 20%),
flag wash (fee cao + vol ~ 0), xuất báo cáo Markdown hoặc JSON.

Cần API key OKX có quyền Read của affiliate master account.
Env: OKX_KEY, OKX_SECRET, OKX_PASS, OKX_DOMAIN (mặc định openapi.okx.com).

Docs: references/okx-fee-affiliate-api.md (field + domain + lỗi).
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

try:
    from .okx_client import sign, request  # khi chạy như package
except ImportError:
    # Chạy độc lập trong scripts/ — dùng bản sao inline (không phụ thuộc package)
    import base64
    import hashlib
    import hmac

    def sign(secret, ts, method, path, body=""):
        prehash = ts + method.upper() + path + body
        return base64.b64encode(
            hmac.new(secret.encode(), prehash.encode(), hashlib.sha256).digest()
        ).decode()

    def request(env, method, path, body=None):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        payload = json.dumps(body) if body is not None else ""
        headers = {
            "OK-ACCESS-KEY": env["OKX_KEY"],
            "OK-ACCESS-SIGN": sign(env["OKX_SECRET"], ts, method, path, payload),
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": env["OKX_PASS"],
            "Content-Type": "application/json",
        }
        url = f"https://{env['OKX_DOMAIN']}{path}"
        req = urllib.request.Request(
            url, data=payload.encode() if payload else None,
            headers=headers, method=method,
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))


DEFAULT_DOMAIN = "openapi.okx.com"
DEFAULT_EXPECTED_RATE = 0.20
DEFAULT_WASH_FEE_MIN = 10.0
WASH_VOL_MAX = 0.001  # USDT — dưới mức này coi như không có volume


def load_env(paths=(".env", "config/.env")):
    """Load key=value từ .env vào os.environ (.env không ghi đè env hiện có)."""
    for p in paths:
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def fetch_invitees(env, uid=None, period_type=None):
    """Paginate /api/v5/affiliate/invitee/list → list[dict] invitee."""
    items, page, total_page = [], 1, 1
    while page <= total_page:
        params = [f"page={page}", "limit=100"]
        if uid:
            params.append(f"uid={uid}")
        if period_type:
            params.append(f"periodType={period_type}")
        resp = request(env, "GET", "/api/v5/affiliate/invitee/list?" + "&".join(params))
        code = resp.get("code")
        if code != "0":
            raise RuntimeError(f"API error {code}: {resp.get('msg')}")
        data = resp.get("data", [])
        items.extend(data)
        try:
            total_page = int(resp.get("totalPage", "1"))
        except (TypeError, ValueError):
            total_page = 1
        page += 1
        if len(data) == 0:
            break
        time.sleep(0.35)  # rate limit 3 req/s — nhẹ tay
    return items


def analyze(invitees, expected_rate=DEFAULT_EXPECTED_RATE, wash_fee_min=DEFAULT_WASH_FEE_MIN):
    """Tính summary + flag từng khách. Trả (rows, summary)."""
    rows = []
    t_fee = t_vol = t_comm = 0.0
    for inv in invitees:
        fee, vol, comm = _f(inv.get("totalFee")), _f(inv.get("totalVol")), _f(inv.get("totalCommission"))
        rate = _f(inv.get("rebateRate"))
        flags = []
        if expected_rate is not None and abs(rate - expected_rate) > 1e-9:
            flags.append("REBATE_MISMATCH")
        if fee >= wash_fee_min and vol <= WASH_VOL_MAX:
            flags.append("WASH")
        if inv.get("isCompliant") is False:
            flags.append("NON_COMPLIANT")
        t_fee += fee
        t_vol += vol
        t_comm += comm
        rows.append({
            "uid": inv.get("uid"),
            "country": inv.get("country", ""),
            "joinTime": inv.get("joinTime", ""),
            "firstTradeTime": inv.get("firstTradeTime", ""),
            "rebateRate": rate,
            "totalFee": fee,
            "totalVol": vol,
            "totalCommission": comm,
            "flags": flags,
        })
    summary = {
        "inviteeCount": len(rows),
        "totalFee": t_fee,
        "totalVol": t_vol,
        "totalCommission": t_comm,
        "expectedRate": expected_rate,
        "mismatchCount": sum(1 for r in rows if "REBATE_MISMATCH" in r["flags"]),
        "washCount": sum(1 for r in rows if "WASH" in r["flags"]),
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return rows, summary


def render_markdown(rows, summary):
    lines = ["# OKX Fee & Rebate Report", ""]
    lines.append(f"- Invitees: **{summary['inviteeCount']}**")
    lines.append(f"- Total fee paid: **{summary['totalFee']:.2f} USDT**")
    lines.append(f"- Total commission: **{summary['totalCommission']:.2f} USDT**")
    lines.append(f"- Total volume: **{summary['totalVol']:.2f} USDT**")
    lines.append(f"- Rebate mismatch (≠ {summary['expectedRate']:.0%}): **{summary['mismatchCount']}**")
    lines.append(f"- Wash flags: **{summary['washCount']}**")
    lines.append("")
    lines.append("| UID | Country | Join | rebateRate | totalFee | totalVol | totalCommission | Flags |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda x: -x["totalFee"]):
        flags = ", ".join(r["flags"]) if r["flags"] else ""
        jt = r["joinTime"]
        if jt and jt.isdigit():
            jt = datetime.fromtimestamp(int(jt) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        lines.append(
            f"| {r['uid']} | {r['country']} | {jt} | {r['rebateRate']:.4f} "
            f"| {r['totalFee']:.2f} | {r['totalVol']:.2f} | {r['totalCommission']:.2f} | {flags} |"
        )
    lines.append("")
    lines.append("> OKX pays rebates automatically via the affiliate link "
                 "(inviteeRebateRate). This report only monitors — it "
                 "never holds or pays fees.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(
        description="OKX affiliate fee & rebate tracker (read-only).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--expected-rate", type=float, default=DEFAULT_EXPECTED_RATE,
                    help="Rebate rate kỳ vọng (decimal, 0.20 = 20 pct) — lệch → REBATE_MISMATCH. Dùng 0 để tắt.")
    ap.add_argument("--wash-fee-min", type=float, default=DEFAULT_WASH_FEE_MIN,
                    help="Ngưỡng fee (USDT) để cờ WASH khi volume ~ 0.")
    ap.add_argument("--uid", type=str, default=None, help="Chỉ lấy đúng UID khách này.")
    ap.add_argument("--period", type=str, default=None,
                    help="periodType: this_month | last_month | last_30d | total (mặc định: lifetime).")
    ap.add_argument("--json", action="store_true", help="Xuất JSON thay vì Markdown.")
    ap.add_argument("--out", type=str, default=None, help="Ghi output vào file (mặc định stdout).")
    args = ap.parse_args()

    load_env()
    env = {
        "OKX_KEY": os.environ.get("OKX_KEY", ""),
        "OKX_SECRET": os.environ.get("OKX_SECRET", ""),
        "OKX_PASS": os.environ.get("OKX_PASS", ""),
        "OKX_DOMAIN": os.environ.get("OKX_DOMAIN", DEFAULT_DOMAIN),
    }
    if not all([env["OKX_KEY"], env["OKX_SECRET"], env["OKX_PASS"]]):
        print("Thiếu OKX_KEY/OKX_SECRET/OKX_PASS (env hoặc .env).", file=sys.stderr)
        sys.exit(2)

    expected = args.expected_rate if args.expected_rate > 0 else None
    invitees = fetch_invitees(env, uid=args.uid, period_type=args.period)
    rows, summary = analyze(invitees, expected_rate=expected, wash_fee_min=args.wash_fee_min)

    if args.json:
        out = json.dumps({"summary": summary, "invitees": rows}, indent=2, ensure_ascii=False)
    else:
        out = render_markdown(rows, summary)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Đã ghi {args.out} ({len(rows)} invitee).")
    else:
        print(out)


if __name__ == "__main__":
    main()
