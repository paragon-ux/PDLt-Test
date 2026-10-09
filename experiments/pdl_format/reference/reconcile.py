"""Reference reconcile.py: the stress test of grade_t1.py passes it on every criterion. Never shown to a model."""
import argparse
import csv
import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

REQUIRED = ("event_id", "account_id", "occurred_at", "event_type", "units")


def main():
    p = argparse.ArgumentParser()
    for name in ("--events", "--accounts", "--pricing", "--summary", "--rejects", "--excluded"):
        p.add_argument(name, required=True)
    a = p.parse_args()
    with open(a.accounts, encoding="utf-8", newline="") as f:
        accounts = {r["account_id"]: r for r in csv.DictReader(f)}
    with open(a.pricing, encoding="utf-8") as f:
        pricing = json.load(f)
    prices = {"standard": Decimal(pricing["standard_unit_price"]), "enterprise": Decimal(pricing["enterprise_unit_price"])}
    rejects, parsed = [], []
    with open(a.events, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                rejects.append({"line_number": n, "reason_code": "INVALID_JSON", "raw_line": raw})
                continue
            if not isinstance(rec, dict) or any(k not in rec for k in REQUIRED):
                rejects.append({"line_number": n, "reason_code": "MISSING_FIELD", "record": rec})
                continue
            parsed.append((n, rec))
    by_id = {}
    for n, rec in parsed:
        key = {k: rec[k] for k in REQUIRED}
        by_id.setdefault(rec["event_id"], []).append((n, rec, json.dumps(key, sort_keys=True)))
    totals, excluded = {}, []
    for eid in sorted(by_id):
        group = by_id[eid]
        if len({k for _, _, k in group}) > 1:
            for n, rec, _ in group:
                rejects.append({"line_number": n, "reason_code": "CONFLICTING_DUPLICATE_ID", "record": rec})
            continue
        n, rec, _ = group[0]
        if rec["event_type"] not in ("usage", "credit"):
            rejects.append({"line_number": n, "reason_code": "INVALID_EVENT_TYPE", "record": rec}); continue
        if not isinstance(rec["units"], int) or isinstance(rec["units"], bool):
            rejects.append({"line_number": n, "reason_code": "INVALID_UNITS", "record": rec}); continue
        try:
            ts = datetime.fromisoformat(rec["occurred_at"].replace("Z", "+00:00"))
        except ValueError:
            rejects.append({"line_number": n, "reason_code": "INVALID_TIMESTAMP", "record": rec}); continue
        if ts.tzinfo is None:
            rejects.append({"line_number": n, "reason_code": "TIMESTAMP_WITHOUT_OFFSET", "record": rec}); continue
        acct = accounts.get(rec["account_id"])
        if acct is None:
            rejects.append({"line_number": n, "reason_code": "UNKNOWN_ACCOUNT", "record": rec}); continue
        if acct["status"] != "active":
            excluded.append({"line_number": n, "event_id": eid, "account_id": rec["account_id"], "reason_code": "INACTIVE_ACCOUNT"}); continue
        if acct["plan"] == "trial":
            excluded.append({"line_number": n, "event_id": eid, "account_id": rec["account_id"], "reason_code": "TRIAL_ACCOUNT"}); continue
        day = ts.astimezone(timezone.utc).date().isoformat()
        totals[(rec["account_id"], day)] = totals.get((rec["account_id"], day), 0) + rec["units"]
    with open(a.summary, "w", encoding="utf-8", newline="") as f:
        f.write("account_id,usage_date_utc,net_units,unit_price_usd,amount_usd\n")
        for (acct, day) in sorted(totals):
            price = prices[accounts[acct]["plan"]]
            amount = (Decimal(totals[(acct, day)]) * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            f.write(f"{acct},{day},{totals[(acct, day)]},{pricing['standard_unit_price'] if accounts[acct]['plan'] == 'standard' else pricing['enterprise_unit_price']},{amount}\n")
    for path, rows in ((a.rejects, sorted(rejects, key=lambda r: r["line_number"])), (a.excluded, sorted(excluded, key=lambda r: r["line_number"]))):
        with open(path, "w", encoding="utf-8", newline="") as f:
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
