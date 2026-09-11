#!/usr/bin/env python3
"""
Retail Capstone v2 — Student-First Dataset Generator (Deterministic Totals + Shuffle + Indian Faker)
===================================================================================================

What’s new in this version
--------------------------
1) Clean + Bad rows are now **merged and then shuffled** before writing, so “bad”
   records are no longer grouped at the end of the files.
2) Names, emails, and cities are generated with **Faker localized to India** (`en_IN`),
   including gender-aware first names when applicable.

Guaranteed totals across all entities (CLEAN + BAD = MERGED):
  • CLEAN (pure):          1,200,000 rows
  • BAD (impurities):        200,000 rows
  • MERGED (distributed):  1,400,000 rows

Entity-level row counts (CLEAN + BAD = MERGED)
  customers:     215,000 clean + 29,000 bad  = 244,000
  products:       12,000 clean + 3,000 bad   = 15,000
  orders:        175,000 clean + 30,000 bad  = 205,000
  order_items:   680,000 clean + 118,000 bad = 798,000
  payments:      118,000 clean + 20,000 bad  = 138,000

Folder layout
-------------
retail_capstone_v2/
├─ data/
│  └─ merged/
│     ├─ customers_merged.csv
│     ├─ products_merged.csv
│     ├─ orders_merged.csv
│     ├─ order_items_merged.csv
│     └─ payments_merged.csv
└─ logs/
   ├─ profiling_summary.json
   └─ generation_config.json

Usage
-----
python generate_retail_capstone_dataset.py --out ./retail_capstone_v2 --seed 23 --no-progress

Dependencies
------------
pip install faker pandas numpy pyarrow
"""

from __future__ import annotations
import argparse
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List

import numpy as np
import pandas as pd
from faker import Faker


def mask_email(email: str) -> str:
    """Simple reversible mask: keep domain, blur local-part partially."""
    if not isinstance(email, str) or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * max(1, len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask all but last 4 digits."""
    if not isinstance(phone, str):
        return phone
    digits = ''.join([c for c in phone if c.isdigit()])
    if len(digits) < 4:
        return "*" * len(phone)
    return "*" * (len(phone) - 4) + phone[-4:]


def random_date(start: datetime, end: datetime, rng: np.random.Generator) -> datetime:
    delta = end - start
    sec = rng.integers(0, int(delta.total_seconds()) + 1)
    return start + timedelta(seconds=int(sec))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate Retail Capstone v2 merged datasets (with shuffle and Indian Faker).")
    p.add_argument("--out", type=str, required=True, help="Output root directory (e.g., ./retail_capstone_v2)")
    p.add_argument("--seed", type=int, default=23, help="Random seed (default: 23)")
    p.add_argument("--no-progress", action="store_true", help="Suppress progress prints")
    p.add_argument("--parquet", action="store_true", help="Also write Parquet files alongside CSV")
    return p


class Progress:
    def __init__(self, quiet: bool):
        self.quiet = quiet
    def log(self, msg: str):
        if not self.quiet:
            print(msg, flush=True)


def ensure_dirs(root: Path) -> Tuple[Path, Path]:
    data_dir = root / "data" / "merged"
    logs_dir = root / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return data_dir, logs_dir


def build_faker(seed: int) -> Faker:
    # Localized to India, as requested
    fake = Faker("en_IN")
    Faker.seed(seed)
    random.seed(seed)
    return fake


def gen_customers(clean_n: int, bad_n: int, rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    rows: List[dict] = []
    genders = ["male", "female"]
    # Clean rows
    for cid in range(1, clean_n + 1):
        gender = rng.choice(genders)
        if gender == "male":
            first = fake.first_name_male()
        else:
            first = fake.first_name_female()
        last = fake.last_name()
        full_name = f"{first} {last}"
        email = fake.email()
        city = fake.city()
        state = fake.state()
        phone = fake.phone_number()
        created_at = fake.date_time_between(start_date="-3y", end_date="-1y")
        updated_at = fake.date_time_between(start_date=created_at, end_date="-1d")
        rows.append({
            "customer_code": f"C{cid:07d}",
            "first_name": first,
            "last_name": last,
            "full_name": full_name,
            "email": email,
            "gender": gender,
            "city": city,
            "state": state,
            "phone": phone,
            "created_at": created_at.isoformat(sep=" "),
            "updated_at": updated_at.isoformat(sep=" "),
            "is_active": True
        })
    # Bad rows (inject various issues)
    for i in range(bad_n):
        base_id = clean_n + i + 1
        kind = rng.choice(["missing", "future_date", "dup_key", "type_mismatch"])
        gender = rng.choice(genders)
        first = fake.first_name_male() if gender == "male" else fake.first_name_female()
        last = fake.last_name()
        email = fake.email()
        city = fake.city()
        state = fake.state()
        phone = fake.phone_number()
        created_at = fake.date_time_between(start_date="-3y", end_date="-1y")
        updated_at = fake.date_time_between(start_date=created_at, end_date="-1d")
        record = {
            "customer_code": f"C{base_id:07d}",
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "email": email,
            "gender": gender,
            "city": city,
            "state": state,
            "phone": phone,
            "created_at": created_at.isoformat(sep=" "),
            "updated_at": updated_at.isoformat(sep=" "),
            "is_active": True
        }
        if kind == "missing":
            for col in rng.choice(["city", "email", "first_name"], size=2, replace=False):
                record[col] = None
        elif kind == "future_date":
            record["updated_at"] = (datetime.now() + timedelta(days=int(rng.integers(1, 365)))).isoformat(sep=" ")
        elif kind == "dup_key":
            # Duplicate a valid key from earlier range
            record["customer_code"] = f"C{int(rng.integers(1, clean_n+1)):07d}"
        elif kind == "type_mismatch":
            record["phone"] = "NOT_A_NUMBER"
        rows.append(record)

    df = pd.DataFrame(rows)
    return df


def gen_products(clean_n: int, bad_n: int, rng: np.random.Generator, fake: Faker) -> pd.DataFrame:
    rows: List[dict] = []
    categories = ["Electronics", "Home", "Fashion", "Sports", "Books", "Grocery", "Beauty", "Toys"]
    # Clean
    for pid in range(1, clean_n + 1):
        cat = rng.choice(categories)
        price = round(float(rng.uniform(50, 25000)), 2)
        rows.append({
            "product_code": f"P{pid:06d}",
            "product_name": f"{fake.color_name()} {fake.word().title()}",
            "category": cat,
            "unit_price": price,
            "is_active": True
        })
    # Bad
    for i in range(bad_n):
        base_id = clean_n + i + 1
        kind = rng.choice(["missing", "negative", "dup_key", "type_mismatch"])
        price = round(float(rng.uniform(50, 25000)), 2)
        rec = {
            "product_code": f"P{base_id:06d}",
            "product_name": f"{fake.bs().title()}",
            "category": rng.choice(categories + [None]),
            "unit_price": price,
            "is_active": True
        }
        if kind == "missing":
            rec["product_name"] = None
        elif kind == "negative":
            rec["unit_price"] = float(-rng.uniform(1, 999))
        elif kind == "dup_key":
            rec["product_code"] = f"P{int(rng.integers(1, clean_n+1)):06d}"
        elif kind == "type_mismatch":
            rec["unit_price"] = "FREE"
        rows.append(rec)
    return pd.DataFrame(rows)


def gen_orders(clean_n: int, bad_n: int, rng: np.random.Generator, fake: Faker, customer_clean_max: int, dup_id_max: int | None = None) -> pd.DataFrame:
    rows: List[dict] = []
    start = datetime.now() - timedelta(days=365*2)
    end = datetime.now() - timedelta(days=1)

    # Clean
    for oid in range(1, clean_n + 1):
        cust_id = int(rng.integers(1, customer_clean_max + 1))
        order_date = random_date(start, end, rng)
        status = rng.choice(["PLACED", "SHIPPED", "DELIVERED", "RETURNED"], p=[0.25, 0.45, 0.25, 0.05])
        rows.append({
            "order_id": f"O{oid:08d}",
            "customer_code": f"C{cust_id:07d}",
            "order_date": order_date.isoformat(sep=" "),
            "status": status,
            "order_city": fake.city(),
            "order_state": fake.state()
        })

    # Bad
    for i in range(bad_n):
        base_id = clean_n + i + 1
        kind = rng.choice(["orphan", "future_date", "dup_key", "missing"])
        cust_code = f"C{int(rng.integers(1, customer_clean_max + 1)):07d}"
        if kind == "orphan":
            cust_code = "__ORPHAN__"
        order_date = random_date(start, end, rng)
        rec = {
            "order_id": f"O{base_id:08d}",
            "customer_code": cust_code,
            "order_date": order_date.isoformat(sep=" "),
            "status": rng.choice(["PLACED", "SHIPPED", "DELIVERED", "RETURNED"]),
            "order_city": fake.city(),
            "order_state": fake.state()
        }
        if kind == "future_date":
            rec["order_date"] = (datetime.now() + timedelta(days=int(rng.integers(1, 120)))).isoformat(sep=" ")
        elif kind == "dup_key":
            # If generating bad rows separately, use provided dup_id_max (clean count) to avoid low>=high errors
            high = (dup_id_max if dup_id_max and dup_id_max > 0 else max(clean_n, 1))
            # If high == 1, duplicate the very first id deterministically
            dup_idx = 1 if high == 1 else int(rng.integers(1, high + 1))
            rec["order_id"] = f"O{dup_idx:08d}"
        elif kind == "missing":
            rec["order_state"] = None
        rows.append(rec)

    return pd.DataFrame(rows)


def gen_order_items(clean_n: int, bad_n: int, rng: np.random.Generator, product_clean_max: int, order_clean_max: int, dup_id_max: int | None = None) -> pd.DataFrame:
    rows: List[dict] = []
    # Clean
    for iid in range(1, clean_n + 1):
        pid = int(rng.integers(1, product_clean_max + 1))
        oid = int(rng.integers(1, order_clean_max + 1))
        qty = int(rng.integers(1, 6))
        unit_price = float(round(rng.uniform(50, 25000), 2))
        rows.append({
            "order_item_id": f"OI{iid:09d}",
            "order_id": f"O{oid:08d}",
            "product_code": f"P{pid:06d}",
            "quantity": qty,
            "unit_price": unit_price,
            "line_amount": round(qty * unit_price, 2)
        })
    # Bad
    for i in range(bad_n):
        base_id = clean_n + i + 1
        kind = rng.choice(["orphan_prod", "orphan_order", "negative", "type_mismatch", "dup_key"])
        pid = int(rng.integers(1, product_clean_max + 1))
        oid = int(rng.integers(1, order_clean_max + 1))
        qty = int(rng.integers(1, 6))
        unit_price = float(round(rng.uniform(50, 25000), 2))
        rec = {
            "order_item_id": f"OI{base_id:09d}",
            "order_id": f"O{oid:08d}",
            "product_code": f"P{pid:06d}",
            "quantity": qty,
            "unit_price": unit_price,
            "line_amount": round(qty * unit_price, 2)
        }
        if kind == "orphan_prod":
            rec["product_code"] = "__ORPHAN__"
        elif kind == "orphan_order":
            rec["order_id"] = "__ORPHAN__"
        elif kind == "negative":
            rec["quantity"] = -abs(int(rng.integers(1, 5)))
        elif kind == "type_mismatch":
            rec["unit_price"] = "TWENTY"
        elif kind == "dup_key":
            high = (dup_id_max if dup_id_max and dup_id_max > 0 else max(clean_n, 1))
            dup_idx = 1 if high == 1 else int(rng.integers(1, high + 1))
            rec["order_item_id"] = f"OI{dup_idx:09d}"
        rows.append(rec)
    return pd.DataFrame(rows)


def gen_payments(clean_n: int, bad_n: int, rng: np.random.Generator, order_clean_max: int, dup_id_max: int | None = None) -> pd.DataFrame:
    rows: List[dict] = []
    methods = ["CARD", "UPI", "NETBANKING", "COD", "WALLET"]
    # Clean
    for pid in range(1, clean_n + 1):
        oid = int(rng.integers(1, order_clean_max + 1))
        amount = float(round(rng.uniform(100, 50000), 2))
        rows.append({
            "payment_id": f"PM{pid:08d}",
            "order_id": f"O{oid:08d}",
            "payment_amount": amount,
            "payment_method": rng.choice(methods),
            "payment_date": (datetime.now() - timedelta(days=int(rng.integers(10, 700)))).isoformat(sep=" ")
        })
    # Bad
    for i in range(bad_n):
        base_id = clean_n + i + 1
        kind = rng.choice(["orphan_order", "negative", "type_mismatch", "dup_key", "missing"])
        oid = int(rng.integers(1, order_clean_max + 1))
        amount = float(round(rng.uniform(100, 50000), 2))
        rec = {
            "payment_id": f"PM{base_id:08d}",
            "order_id": f"O{oid:08d}",
            "payment_amount": amount,
            "payment_method": rng.choice(methods + [None]),
            "payment_date": (datetime.now() - timedelta(days=int(rng.integers(10, 700)))).isoformat(sep=" ")
        }
        if kind == "orphan_order":
            rec["order_id"] = "__ORPHAN__"
        elif kind == "negative":
            rec["payment_amount"] = -abs(float(rng.uniform(1, 999)))
        elif kind == "type_mismatch":
            rec["payment_amount"] = "MANY"
        elif kind == "dup_key":
            high = (dup_id_max if dup_id_max and dup_id_max > 0 else max(clean_n, 1))
            dup_idx = 1 if high == 1 else int(rng.integers(1, high + 1))
            rec["payment_id"] = f"PM{dup_idx:08d}"
        elif kind == "missing":
            rec["payment_method"] = None
        rows.append(rec)
    return pd.DataFrame(rows)


def shuffle_and_write(df_clean: pd.DataFrame, df_bad: pd.DataFrame, out_csv: Path, out_parquet: bool, seed: int):
    """Concatenate clean + bad, then **shuffle** rows deterministically before writing."""
    df = pd.concat([df_clean, df_bad], ignore_index=True)
    # Deterministic shuffle
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df.to_csv(out_csv, index=False)
    if out_parquet:
        df.to_parquet(out_csv.with_suffix(".parquet"), index=False)
    return df.shape[0]


def main():
    args = build_arg_parser().parse_args()
    root = Path(args.out).resolve()
    data_dir, logs_dir = ensure_dirs(root)
    progress = Progress(args.no_progress)
    seed = int(args.seed)

    # Seeds
    rng = np.random.default_rng(seed)
    fake = build_faker(seed)

    # Target counts
    COUNTS = {
        "customers": (215_000, 29_000),
        "products": (12_000, 3_000),
        "orders": (175_000, 30_000),
        "order_items": (680_000, 118_000),
        "payments": (118_000, 20_000),
    }

    progress.log("Generating customers ...")
    customers_clean_bad = gen_customers(*COUNTS["customers"], rng, fake)
    customers_clean = customers_clean_bad.iloc[:COUNTS["customers"][0]].copy()
    customers_bad = customers_clean_bad.iloc[COUNTS["customers"][0]:].copy()

    progress.log("Generating products ...")
    products_clean_bad = gen_products(*COUNTS["products"], rng, fake)
    products_clean = products_clean_bad.iloc[:COUNTS["products"][0]].copy()
    products_bad = products_clean_bad.iloc[COUNTS["products"][0]:].copy()

    progress.log("Generating orders ...")
    orders_clean = gen_orders(COUNTS["orders"][0], 0, rng, fake, customer_clean_max=COUNTS["customers"][0])
    orders_bad = gen_orders(0, COUNTS["orders"][1], rng, fake, customer_clean_max=COUNTS["customers"][0], dup_id_max=COUNTS["orders"][0])

    progress.log("Generating order_items ...")
    order_items_clean = gen_order_items(COUNTS["order_items"][0], 0, rng, product_clean_max=COUNTS["products"][0], order_clean_max=COUNTS["orders"][0])
    order_items_bad = gen_order_items(0, COUNTS["order_items"][1], rng, product_clean_max=COUNTS["products"][0], order_clean_max=COUNTS["orders"][0], dup_id_max=COUNTS["order_items"][0])

    progress.log("Generating payments ...")
    payments_clean = gen_payments(COUNTS["payments"][0], 0, rng, order_clean_max=COUNTS["orders"][0])
    payments_bad = gen_payments(0, COUNTS["payments"][1], rng, order_clean_max=COUNTS["orders"][0], dup_id_max=COUNTS["payments"][0])

    # Write merged (clean+bad) **shuffled** CSVs
    progress.log("Writing shuffled merged CSVs ...")
    totals = {}

    totals["customers"] = shuffle_and_write(
        customers_clean, customers_bad, data_dir / "customers_merged.csv", args.parquet, seed
    )
    totals["products"] = shuffle_and_write(
        products_clean, products_bad, data_dir / "products_merged.csv", args.parquet, seed
    )
    totals["orders"] = shuffle_and_write(
        orders_clean, orders_bad, data_dir / "orders_merged.csv", args.parquet, seed
    )
    totals["order_items"] = shuffle_and_write(
        order_items_clean, order_items_bad, data_dir / "order_items_merged.csv", args.parquet, seed
    )
    totals["payments"] = shuffle_and_write(
        payments_clean, payments_bad, data_dir / "payments_merged.csv", args.parquet, seed
    )

    # Quick profiling summary + config
    profiling = {
        "seed": seed,
        "entities": {
            "customers": {"clean": COUNTS["customers"][0], "bad": COUNTS["customers"][1], "total": totals["customers"]},
            "products": {"clean": COUNTS["products"][0], "bad": COUNTS["products"][1], "total": totals["products"]},
            "orders": {"clean": COUNTS["orders"][0], "bad": COUNTS["orders"][1], "total": totals["orders"]},
            "order_items": {"clean": COUNTS["order_items"][0], "bad": COUNTS["order_items"][1], "total": totals["order_items"]},
            "payments": {"clean": COUNTS["payments"][0], "bad": COUNTS["payments"][1], "total": totals["payments"]},
        },
        "grand_totals": {
            "clean_sum": sum([COUNTS[k][0] for k in COUNTS]),
            "bad_sum": sum([COUNTS[k][1] for k in COUNTS]),
            "merged_sum": sum(totals.values())
        },
        "orphan_placeholders": "__ORPHAN__",
        "notes": [
            "Clean + bad rows are concatenated and **shuffled** before write.",
            "Faker localized to India (en_IN) for names, emails & cities.",
            "Some bad rows include missing values, negative numbers, future dates, duplicate keys, orphan references and type mismatches."
        ]
    }
    (logs_dir / "profiling_summary.json").write_text(json.dumps(profiling, indent=2))

    config = {
        "version": "v2.1-shuffle-en_IN",
        "faker_locale": "en_IN",
        "shuffle": True,
        "write_parquet": bool(args.parquet),
        "targets": {k: {"clean": v[0], "bad": v[1]} for k, v in COUNTS.items()},
        "output_dir": str(root)
    }
    (logs_dir / "generation_config.json").write_text(json.dumps(config, indent=2))

    progress.log("Done. Files written to: " + str(root))


if __name__ == "__main__":
    main()
