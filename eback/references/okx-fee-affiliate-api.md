# OKX Affiliate & Fee API — field reference (verified 2026-08-19)

> Nguồn: https://www.okx.com/docs-v5/en/ · Lấy 2026-08-19. Chỉ giữ field dùng cho fee/rebate tracking.

## Domain (bắt buộc theo nơi đăng ký)

- `openapi.okx.com` — quốc tế
- `us.okx.com` — US & AU (đăng ký tại app.okx.com)
- `eea.okx.com` — EU (đăng ký tại my.okx.com)

Dùng sai domain → lỗi. Đặt `OKX_DOMAIN` trong env/.env.

## Auth (mọi private endpoint)

Headers: `OK-ACCESS-KEY` · `OK-ACCESS-SIGN` (Base64(HMAC-SHA256(ts + method + path + body))) · `OK-ACCESS-TIMESTAMP` (ISO8601 UTC ms, lệch >30s → 50102) · `OK-ACCESS-PASSPHRASE`.

- Key cần quyền **Read** — affiliate endpoints yêu cầu key thuộc affiliate master account.
- Key không bind IP có quyền trade/withdraw sẽ hết hạn sau 14 ngày không dùng.

## GET /api/v5/affiliate/invitee/list — DANH SÁCH KHÁCH (dùng chính)

Rate limit: 3 req/s (User ID). Pagination: `page` (1-indexed, default 1) · `limit` (clamp [1,100], default 100) · response có `totalPage` **cùng cấp với `data`**.

Params hữu ích: `periodType` (last_7d/last_30d/this_month/last_month/total/today/this_week/custom) · `begin`+`end` (custom, ≤90 ngày, begin ≥180 ngày trước; thiếu 1 trong 2 → 50014) · `keyword` (UID/channel) · `commissionCategory` (SPOT/DERIVATIVE/BSC) · `orderBy` (cTime/depAmt/vol/fee/rebate) · `orderDir` (asc/desc) · `kycStatus` (unverified/verified) · `uid` (tối đa 100, comma-separated) · `joinTimeBegin`+`joinTimeEnd` (phải đi cùng, ≤90 ngày).

Response `data[]` — field quan trọng:

| Field | Type | Ý nghĩa |
|---|---|---|
| `uid` | String | External user UID |
| `country` | String | ISO 3166-1 alpha-2 (VD: CN, KR) — rỗng nếu chưa set |
| `joinTime` | String | Timestamp ms thiết lập quan hệ rebate |
| `firstTradeTime` | String | Timestamp ms lệnh đầu sau quan hệ — `""` nếu chưa trade |
| `channelName` | String | Tên channel đăng ký |
| `rebateRate` | String | **Effective rebate rate của invitee** từ rule đang áp dụng (decimal, 0.1600 = 16%) |
| `feeTierRank` | String | Bậc phí (0 = thấp nhất, 13 = cao nhất) |
| `kycStatus` / `kycTime` | String | KYC2 (verified/unverified + timestamp) |
| `depAmt` | String | Tổng nạp (USDT) |
| `totalVol` | String | **Tổng volume lifetime (USDT)** |
| `totalFee` | String | **Tổng phí giao dịch lifetime (USDT)** |
| `totalCommission` | String | **Tổng hoa hồng kiếm từ invitee này (USDT)** |
| `isCompliant` | Boolean | Tuân thủ khu vực (false = bị giới hạn KYC/jurisdiction) |

⚠️ `totalFee`/`totalVol`/`totalCommission` là **lifetime cumulative** — báo cáo theo tháng phải dùng `periodType`/`custom`, không trừ 2 lần gọi lifetime (tránh cộng trùng).

## GET /api/v5/affiliate/invitee/detail — CHI TIẾT 1 KHÁCH (đối soát rebate)

Request: `?uid=<uid>&periodType=<window>` (periodType bắt buộc nếu muốn volPeriod; custom không hỗ trợ → 51000).

Response `data[]` — field quan trọng:

| Field | Type | Ý nghĩa |
|---|---|---|
| `inviteeRebateRate` | String | **Self rebate rate invitee nhận được (decimal, 0.39 = 39%)** — thứ khách THẤY, nguồn sự thật đối soát |
| `totalCommission` | String | Tổng hoa hồng kiếm từ khách (USDT) |
| `accFee` | String | Tổng phí giao dịch tích lũy (USDT) |
| `volMonth` | String | Volume tháng hiện tại (USDT) |
| `totalVol` | String | Volume lifetime (USDT) |
| `volPeriod` | String | Volume trong window (chỉ khi có periodType) |
| `region` | String | Quốc gia (VD: "Vietnam") |
| `level` | String | Bậc phí (Lv1...) |
| `firstTradeTime` | String | Lệnh đầu — `""` nếu chưa trade |

⚠️ **`rebateRate` (list) ≠ `inviteeRebateRate` (detail)** — list = rate theo rule đang áp dụng; detail = rate invitee nhận. Flag mismatch từ list phải xác nhận lại ở detail trước khi xử lý.

## GET /api/v5/affiliate/performance/summary — TỔNG QUAN

Request: `?periodType=total` (hoặc custom begin/end — thiếu 1 trong 2 → 50014; periodType khác thì bỏ qua begin/end).

Response `data[]`: `uTime` (snapshot) · `inviteeCnt` · `depAmt` (USDT) · `details[]` per `commissionCategory` (SPOT/DERIVATIVE/BSC): `firstTraderCnt` · `traderCnt` · `vol` (period-scoped) · `commission` (period-scoped).

## GET /api/v5/affiliate/link/list — LINK & TỶ LỆ

Response `data[]`: `channelId` · `channelName` · `joinLink` (VD https://okx.com/join/78295211) · `linkType` (standard/co_inviter) · `inviterCommissionRate` (decimal) · `inviteeDiscountRate` (**rebate template trên link, decimal**) · `inviteeCnt` · `traderCnt` · `totalCommission` · `commission24h` · `isDefault` · `linkStatus`.

## GET /api/v5/account/trade-fee — PHÍ GIAO DỊCH (per-instrument tier)

Endpoints khác: `GET /api/v5/account/trade-fee` (fee rates theo instId/instType/uly; trả maker/taker rate + tier). Dùng khi cần đối chiếu phí khách đang trả với bậc phí. (Nguồn: OKX docs v5 — "Get fee rates".)

## Lỗi thường gặp

- `50014` — thiếu param bắt buộc (VD: custom thiếu begin/end; joinTimeBegin thiếu joinTimeEnd)
- `50102` — timestamp lệch server >30s (luôn UTC ms)
- `50011` — rate limit (throttle, ngủ 0.35s giữa các page)
- `50030` — key không có quyền endpoint này (cần Read + affiliate master)
- `50103` — thiếu OK-ACCESS-KEY header
- `51000` — periodType không hỗ trợ (custom trên invitee/detail)
- `70003` — (skill marketplace) version chưa được duyệt — không liên quan API này

## Ghi chú pháp lý

- OKX **tự trả rebate** cho invitee qua link (`inviteeRebateRate`) — công cụ này chỉ theo dõi, KHÔNG giữ/trả tiền.
- OKX API Agreement 9.3 Non-Commercial Use — trước khi commercial hóa skill, xác nhận với OKX (xem `research-crypto-forex/okx-marketplace/3-plan.md`).
