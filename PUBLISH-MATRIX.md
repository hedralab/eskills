# PUBLISH-MATRIX — Nơi list eBack (đẩy lên hết chỗ list được)

> Ngày: 2026-08-20 · Version: **eBack v0.2.0** (skill `eskills/eback/` + engine `eback/`)
> Chiến lược: skill free = funnel → monetize ngoài (bundle + membership)

## Danh sách nơi list — trạng thái

| # | Nơi | Loại | Trạng thái | Cách đăng |
|---|---|---|---|---|
| 1 | **OKX Skills Marketplace** | Skill AI trading (free) | ⏳ CHƯA — rebate=0 skill (gap thật) | Web: okx.com/agent-tradekit/skills → tab "Hồ sơ" → upload (cần KYC + duyệt) |
| 2 | **GitHub** | Repo public/private | ✅ DONE (private) | https://github.com/hedralab/eback — đã push |
| 3 | **skills.sh** (Vercel) | Skill discovery + cài 1 lệnh | ⏳ CHƯA | API cần Vercel OIDC token — cần đăng ký tác giả |
| 4 | **PromptBase** | Bán skill.md | ⏳ CHƯA (bán) | promptbase.com — đăng skill + giá bundle |
| 5 | **Gumroad** | Bán bundle | ⏳ CHƯA (bán) | gumroad.com — bundle $29-69 |
| 6 | **npm** (@okx_ai ecosystem) | CLI | ⏳ CHƯA | cần package riêng — sau khi có demand |

## OKX Marketplace — LUỒNG ĐĂNG (đã research publish-flow.md)

1. Đăng nhập OKX → **KYC hoàn tất** (bắt buộc)
2. Mở https://www.okx.com/vi/agent-tradekit/skills → tab **"Hồ sơ"** (nút upload hiện khi `canUpload=true`)
3. Upload package eBack (zip — xem phần đóng gói dưới)
4. Hệ thống tự kiểm tra format + quét bảo mật → safety score
5. Chờ duyệt (approval per version) → OKX ký Ed25519 → phát hành
6. Verify: `okx skill search rebate` → thấy eBack

## 🔑 KEY POLICY (chốt 2026-08-20 — user quyết định)

| Key | Dùng cho | KHÔNG dùng cho |
|---|---|---|
| **Key AFFILIATE** (OKX_KEY trong eback/.env — quyền Read, affiliate master) | ✅ **PUBLISH skill lên marketplace** (`okx skill search/add` — auth skill API) · ✅ kéo invitee/fee/rebate (engine eBack) | Không đặt lệnh |
| **Key TRADE** (etrade — demo/simulation) | ✅ **TEST bot + nghiên cứu** (chạy thử, simulation mode) | Không publish sản phẩm |

**Quy tắc vàng**: *publish sản phẩm = dùng key AFF · test bot/nghiên cứu = dùng key TRADE (demo)* — không lẫn.

⚠️ Lưu ý pháp lý: OKX API Agreement 9.3 Non-Commercial — skill trên OKX FREE (không bán qua API), monetize ngoài (PromptBase/Gumroad) — đúng chiến lược đã chốt.

## Đóng gói eBack skill (zip sẵn sàng upload OKX)

```bash
cd /Users/admin/eback/eskills
zip -r eback-v0.2.0.zip eback/ -x "*.git*" -x "*.DS_Store" -x "__pycache__*"
# verify:
unzip -l eback-v0.2.0.zip
```

Cấu trúc package (đúng format OKX — SKILL.md + frontmatter name/description/license/metadata):
```
eback/
├── SKILL.md              # v0.2.0 — format OKX chuẩn
├── README.md
├── LICENSE               # MIT
├── references/okx-fee-affiliate-api.md
└── scripts/
    ├── rebate_tracker.py
    └── test_rebate_tracker.py
```

## Verify trước khi đăng (gate)

- [x] `validate-skill.py` PASS
- [x] `--leak --brand` sạch (không lộ hedraback/elog/ebot/HEDRA20)
- [x] Unit test 8 case PASS
- [ ] Zip đúng cấu trúc (`unzip -l`)
- [ ] KYC OKX hoàn tất (điều kiện upload)
- [ ] Đăng → chờ duyệt → `okx skill search rebate` thấy eBack

## Sau khi lên OKX

- skills.sh: đăng ký tác giả → submit repo GitHub
- PromptBase/Gumroad: bundle eBack + eVerify/eSize (khi build) — $29-69
- Membership journal (elog) — nguồn thu chính dài hạn
