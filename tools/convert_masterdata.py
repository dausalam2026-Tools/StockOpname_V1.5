"""
Konversi file Master Tools Database (Excel .xlsx atau CSV) menjadi
app/src/main/assets/masterdata.json yang dipakai aplikasi Android.

CARA PAKAI (butuh Python 3 + pip install pandas openpyxl):
    python convert_masterdata.py path/ke/database_baru.xlsx

File Excel boleh terdiri dari BANYAK sheet (mis. satu sheet per store:
H4, PC, ML, HP, W1, W2, LG). Semua sheet otomatis digabung.

Kolom yang dicari (harus ada persis salah satu nama ini, tidak peduli
huruf besar/kecil): Status, Tool Number, Part Number, Key Number,
Serial Number, Tool Description, Manufacture, Model, Category, Store,
Location, Due Date. Kolom lain (Transit Destination, dst) diabaikan.

Pengelompokan store (harus sama dengan STORE_GROUPS di Models.kt):
  Tool Store Hangar 4             : H4, PC, ML, HP
  Tool Store Component Workshop   : W1, W2, LG

Kalau Anda tidak nyaman menjalankan script ini sendiri, cukup kirim
file database barunya (Excel/CSV/PDF) ke Claude — saya akan jalankan
konversinya dan kirim balik project yang sudah ter-update.
"""
import json
import sys
from pathlib import Path

import pandas as pd

COLUMN_MAP = {
    "status": "status",
    "tool number": "tn",
    "part number": "pn",
    "key number": "kn",
    "serial number": "sn",
    "tool description": "desc",
    "manufacture": "mfr",
    "model": "model",
    "store": "store",
    "location": "location",
    "due date": "due",
}

VALID_STATUS = {
    "available", "calibration", "borrowed", "quarantined",
    "maintenance", "broken", "missing",
}


STORE_GROUPS = {
    "Tool Store Hangar 4": ["H4", "PC", "ML", "HP"],
    "Tool Store Component Workshop": ["W1", "W2", "LG"],
}

NO_LOCATION = "(Lokasi belum diisi)"


def load_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        # sheet_name=None -> baca SEMUA sheet, lalu gabungkan jadi satu tabel
        sheets = pd.read_excel(path, sheet_name=None)
        for name, sdf in sheets.items():
            print(f"Sheet '{name}': {len(sdf)} baris")
        return pd.concat(sheets.values(), ignore_index=True)
    return pd.read_csv(path)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    lower_map = {c.strip().lower(): c for c in df.columns}
    rename = {}
    missing = []
    for wanted_lower, short in COLUMN_MAP.items():
        if wanted_lower in lower_map:
            rename[lower_map[wanted_lower]] = short
        else:
            missing.append(wanted_lower)
    if missing:
        print(f"PERINGATAN: kolom berikut tidak ditemukan dan akan dikosongkan: {missing}")
    df = df.rename(columns=rename)
    for short in COLUMN_MAP.values():
        if short not in df.columns:
            df[short] = ""
    return df


def norm(v) -> str:
    if pd.isna(v):
        return ""
    return " ".join(str(v).strip().split())


def norm_date(v) -> str:
    """Due Date -> 'YYYY-MM-DD', atau '' kalau kosong/tidak valid."""
    if pd.isna(v) or v == "":
        return ""
    ts = pd.to_datetime(v, errors="coerce", dayfirst=True)
    if pd.isna(ts):
        return ""
    return ts.strftime("%Y-%m-%d")


def main():
    if len(sys.argv) < 2:
        print("Pemakaian: python convert_masterdata.py path/ke/file.xlsx")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"File tidak ditemukan: {src}")
        sys.exit(1)

    df = load_table(src)
    df = normalize_columns(df)

    df["store"] = df["store"].apply(norm)
    df["location"] = df["location"].apply(norm)
    df["status"] = df["status"].apply(lambda v: norm(v).lower())

    before = len(df)
    df = df[df["store"] != ""].copy()

    # Tool tanpa lokasi tetap dimasukkan (jangan hilang dari opname).
    n_noloc = int((df["location"] == "").sum())
    if n_noloc:
        print(f"PERINGATAN: {n_noloc} tool tidak punya Location -> dimasukkan ke '{NO_LOCATION}'")
        df.loc[df["location"] == "", "location"] = NO_LOCATION

    # Lokasi yang sama tapi beda huruf besar/kecil (mis. 'i10-4' vs 'I10-4')
    # digabung per store, pakai ejaan yang paling sering muncul.
    key = df["store"] + "||" + df["location"].str.upper()
    canon = (
        df.assign(_k=key)
        .groupby("_k")["location"]
        .agg(lambda x: sorted(x.value_counts().items(), key=lambda kv: (-kv[1], not kv[0].isupper()))[0][0])
    )
    merged = int((df.groupby(key)["location"].nunique() > 1).sum())
    df["location"] = key.map(canon)
    if merged:
        print(f"Info: {merged} lokasi dengan ejaan huruf besar/kecil berbeda digabung.")

    blank_status = int((df["status"] == "").sum())
    if blank_status:
        print(f"PERINGATAN: {blank_status} tool Status-nya kosong -> dianggap 'available'. Sebaiknya dilengkapi di Excel.")
    unknown_status = sorted(set(df["status"]) - VALID_STATUS - {""})
    if unknown_status:
        print(f"PERINGATAN: status tidak dikenal ditemukan (tetap disimpan apa adanya): {unknown_status}")
    print(f"Baris valid: {len(df)} dari {before} baris mentah.")

    data = {}
    for store, g_store in df.groupby("store"):
        locs = {}
        for loc, g_loc in g_store.groupby("location"):
            tools = []
            for _, r in g_loc.iterrows():
                tools.append({
                    "tn": norm(r["tn"]),
                    "pn": norm(r["pn"]),
                    "kn": norm(r["kn"]),
                    "sn": norm(r["sn"]) or "N/A",
                    "desc": norm(r["desc"]),
                    "mfr": norm(r["mfr"]),
                    "model": norm(r["model"]) or "N/A",
                    "status": norm(r["status"]) or "available",
                    "due": norm_date(r["due"]),
                })
            locs[loc] = tools
        data[store] = locs

    stores_found = sorted(data.keys())
    print(f"Store ditemukan: {stores_found}")
    grouped = {st for sts in STORE_GROUPS.values() for st in sts}
    for gname, sts in STORE_GROUPS.items():
        total = sum(len(t) for st in sts for t in data.get(st, {}).values())
        print(f"  {gname}: {[st for st in sts if st in data]} -> {total} tool")
    orphan = [st for st in stores_found if st not in grouped]
    if orphan:
        print(f"PERINGATAN: store {orphan} belum masuk grup mana pun, sehingga TIDAK muncul di menu Stock Opname.")
        print("   Tambahkan ke STORE_GROUPS di Models.kt (dan di script ini).")

    out_path = Path(__file__).resolve().parent.parent / "app" / "src" / "main" / "assets" / "masterdata.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    total_tools = sum(len(t) for locs in data.values() for t in locs.values())
    print(f"\nSelesai. {total_tools} tool tersimpan ke:\n{out_path}")
    print("Lanjutkan seperti biasa: commit + push lewat GitHub Desktop, lalu build ulang di tab Actions.")


if __name__ == "__main__":
    main()
