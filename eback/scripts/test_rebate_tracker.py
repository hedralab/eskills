"""Unit test nhanh cho rebate_tracker (không cần API)."""
import importlib.util

spec = importlib.util.spec_from_file_location("rt", "scripts/rebate_tracker.py")
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

invitees = [
    {'uid': '111', 'country': 'VN', 'joinTime': '1712546713000', 'totalFee': '250.50',
     'totalVol': '5000.0', 'totalCommission': '25.0', 'rebateRate': '0.2000', 'isCompliant': True},
    {'uid': '222', 'country': 'CN', 'joinTime': '1712546713000', 'totalFee': '100.0',
     'totalVol': '2000.0', 'totalCommission': '10.0', 'rebateRate': '0.1600', 'isCompliant': True},
    {'uid': '333', 'country': 'US', 'joinTime': '', 'totalFee': '50.0',
     'totalVol': '0.0005', 'totalCommission': '0.0', 'rebateRate': '0.2000', 'isCompliant': True},
    {'uid': '444', 'country': 'XX', 'joinTime': '', 'totalFee': '0',
     'totalVol': '0', 'totalCommission': '0', 'rebateRate': '0.2000', 'isCompliant': False},
]

rows, summary = rt.analyze(invitees)
print('SUMMARY:', summary)
assert summary['inviteeCount'] == 4
assert summary['mismatchCount'] == 1, 'mismatch'
assert summary['washCount'] == 1, 'wash'
assert abs(summary['totalFee'] - 400.5) < 1e-6

flags = {r['uid']: r['flags'] for r in rows}
assert flags['222'] == ['REBATE_MISMATCH'], flags
assert flags['333'] == ['WASH'], flags
assert flags['444'] == ['NON_COMPLIANT'], flags
assert flags['111'] == [], flags
print('FLAGS OK:', flags)

md = rt.render_markdown(rows, summary)
assert '250.50' in md and 'REBATE_MISMATCH' in md
print('MARKDOWN OK —', len(md), 'chars')

# JSON round-trip
import json
js = json.dumps({"summary": summary, "invitees": rows})
assert json.loads(js)["summary"]["inviteeCount"] == 4
print('JSON OK')

# expected-rate=0 tắt mismatch
_, s2 = rt.analyze(invitees, expected_rate=None)
assert s2['mismatchCount'] == 0
print('DISABLE MISMATCH OK')
print('ALL TESTS PASS')
