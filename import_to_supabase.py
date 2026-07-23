"""
Import dữ liệu từ Google Sheets Apps Script API sang Supabase.
Chạy: cd C:\HOCMAI\AI-project\feed.hocmai && python import_to_supabase.py
"""
import json
import urllib.request
import urllib.error
import re
import sys

SUPABASE_URL = "https://xaxohdyscyxbamvtdjzw.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhheG9oZHlzY3l4YmFtdnRkanp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1NTkyMTAsImV4cCI6MjEwMDEzNTIxMH0.garOtg2u5-WzOC6XkQ_EzeTT_FNczcq7u0R28ee8SIo"
API_URL = "https://script.google.com/macros/s/AKfycbz73HKnzuubZYVQaharliKVIT9jUUu5IAnmBtv5FVLpjNyDFM3H4m370WHZns__ElAybw/exec"


def supabase_request(method, table, data=None, params=None):
    """Gọi Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url += f"?{qs}"

    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def clean_text(val):
    """Chuẩn hóa giá trị text"""
    if val is None:
        return ""
    return str(val).strip()


def clean_datetime(val):
    """Chuẩn hóa datetime, trả về None nếu không hợp lệ"""
    val = clean_text(val)
    if not val:
        return None
    return val  # Supabase chấp nhận ISO string

def _parse_bool(val):
    """Chuyển đổi giá trị TRUE/FALSE từ Google Sheet sang boolean"""
    if val is None:
        return True  # Mặc định là TRUE (hiển thị)
    s = str(val).strip().upper()
    if s in ('TRUE', '1', 'YES', 'CÓ', 'CO'):
        return True
    if s in ('FALSE', '0', 'NO', 'KHÔNG', 'KHONG'):
        return False
    return True  # Mặc định TRUE

def parse_date_dmy(val):
    """Chuyển đổi DD/MM/YYYY → ISO YYYY-MM-DD, trả về None nếu không hợp lệ"""
    val = clean_text(val)
    if not val:
        return None
    parts = val.split('/')
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass
    return val  # Trả về nguyên bản nếu không parse được


def fetch_api_data():
    """Lấy toàn bộ dữ liệu từ Apps Script API"""
    print("📡 Đang fetch dữ liệu từ Apps Script API...")
    import ssl
    ctx = ssl.create_default_context()
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    print(f"   ✅ Đã lấy: Ban_tin={len(data.get('Ban_tin',[]))} rows, "
          f"Lich_hoc={len(data.get('Lich_hoc',[]))} rows, "
          f"So_tay={len(data.get('So_tay',[]))} rows, "
          f"_index={len(data.get('_index',[]))} rows")
    return data


def clear_table(table):
    """Xóa toàn bộ dữ liệu cũ trong bảng"""
    print(f"🧹 Đang xóa dữ liệu cũ trong {table}...")
    status, body = supabase_request("DELETE", table, params={"id": "gt.0"})
    print(f"   {'✅' if status < 300 else '⚠️'} {table}: HTTP {status}")
    return status < 300


def import_ban_tin(rows):
    """Import dữ liệu Ban_tin"""
    print(f"📰 Import Ban_tin ({len(rows)} rows)...")
    data_rows = []
    for i, row in enumerate(rows):
        # Bỏ qua dòng tiêu đề (header) - kiểm tra dựa trên tieu_de
        tieu_de_raw = str(row.get("Tiêu_đề") or row.get("Tiêu đề") or "")
        noi_dung_raw = str(row.get("Nội_dung") or row.get("Nội dung") or "")
        if tieu_de_raw in ("Tiêu_đề", "Tiêu đề", "Tiêu_de") or noi_dung_raw in ("Nội_dung", "Nội dung", "Noi_dung"):
            continue

        tieu_de = clean_text(tieu_de_raw)
        noi_dung = clean_text(noi_dung_raw)

        # Bỏ qua dòng trống (không có tiêu đề VÀ không có nội dung)
        if not tieu_de and not noi_dung:
            continue

        item = {
            "ngay_dang": clean_datetime(row.get("Ngày_đăng") or row.get("Ngày đăng")),
            "tieu_de": tieu_de,
            "noi_dung": noi_dung,
            "section": clean_text(row.get("Section")) or "Tin mới",
            "loai_tb": clean_text(row.get("Loai_TB") or row.get("Loại TB")),
            "ky_thi": clean_text(row.get("Ky_thi") or row.get("Kỳ thi")) or "All",
            "giai_doan": clean_text(row.get("Giai_doan") or row.get("Giai đoạn")),
            "lo_trinh": clean_text(row.get("Lo_trinh") or row.get("Lộ trình")) or "All",
            "muc_do": clean_text(row.get("Muc_do") or row.get("Mức độ")),
            "start_time": clean_datetime(row.get("Start_time")) or None,
            "end_time": clean_datetime(row.get("End_Time")) or None,
            "hashtag": clean_text(row.get("hashtag") or row.get("Hashtag") or row.get("Hash_tag") or ""),
            "xuat_ban": _parse_bool(row.get("Xuất bản") or row.get("Xuất_bản") or row.get("Xuat_ban") or row.get("xuat_ban")),
        }

        data_rows.append(item)

    # Batch insert: 50 rows/lần
    success = 0
    batch_size = 50
    for i in range(0, len(data_rows), batch_size):
        batch = data_rows[i : i + batch_size]
        status, body = supabase_request("POST", "ban_tin", data=batch)
        if status < 300:
            success += len(batch)
        else:
            print(f"   ❌ Batch insert failed at row {i}: HTTP {status} {body[:200]}")
            return False

    print(f"   ✅ Imported {success}/{len(data_rows)} ban_tin rows")
    return True


def import_lich_hoc(rows):
    """Import lịch học"""
    print(f"📅 Import Lich_hoc ({len(rows)} rows)...")
    data_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            # Bỏ qua header rows
            if row.get("Tên bài giảng") == "Tên bài giảng":
                continue
            # Bỏ qua numeric mapping row (kiểu "Tên bài giảng = 3")
            if "= 3" in str(row.get("Tên bài giảng", "")):
                continue

        item = {
            "ten_bai_giang": clean_text(row.get("Tên bài giảng") or row.get("3")),
            "ten_gv": clean_text(row.get("Tên GV") or row.get("4") or ""),
            "ngay_live": parse_date_dmy(row.get("Ngày live") or row.get("5")),
            "khung_gio": clean_text(row.get("Khung giờ") or row.get("7") or ""),
            "ky_thi_lop": clean_text(row.get("Kỳ thi/Lớp") or row.get("32") or "All"),
        }
        if item["ten_bai_giang"]:
            data_rows.append(item)

    success = 0
    batch_size = 50
    for i in range(0, len(data_rows), batch_size):
        batch = data_rows[i : i + batch_size]
        status, body = supabase_request("POST", "lich_hoc", data=batch)
        if status < 300:
            success += len(batch)
        else:
            print(f"   ❌ Batch insert failed: HTTP {status} {body[:200]}")
            return False

    print(f"   ✅ Imported {success}/{len(data_rows)} lich_hoc rows")
    return True


def import_so_tay(rows):
    """Import sổ tay"""
    print(f"📘 Import So_tay ({len(rows)} rows)...")
    data_rows = []
    for i, row in enumerate(rows):
        if i == 0 and (row.get("TT") == "TT" or row.get("Tít") == "Tít"):
            continue

        tieu_de = clean_text(row.get("Tít") or row.get("Tiêu đề") or row.get("Tieu_de"))
        link = clean_text(row.get("Link") or row.get("") or row.get("3"))
        if tieu_de:
            data_rows.append({"tieu_de": tieu_de, "link": link})

    if data_rows:
        status, body = supabase_request("POST", "so_tay", data=data_rows)
        if status < 300:
            print(f"   ✅ Imported {len(data_rows)} so_tay rows")
            return True
        else:
            print(f"   ❌ Import failed: HTTP {status} {body[:200]}")
            return False
    else:
        print("   ⚠️ No so_tay data to import")
        return True


def import_index(rows):
    """Import _index (icon mapping)"""
    print(f"🖼️ Import _index ({len(rows)} rows)...")
    data_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            continue  # Bỏ header

        loai_tb = clean_text(row.get("Loai_TB") or row.get("Loại TB") or row.get("1"))
        icon = clean_text(row.get("icon") or row.get("8"))
        if loai_tb:
            data_rows.append({"loai_tb": loai_tb, "icon": icon})

    if data_rows:
        status, body = supabase_request("POST", "_index", data=data_rows)
        if status < 300:
            print(f"   ✅ Imported {len(data_rows)} _index rows")
            return True
        else:
            print(f"   ❌ Import failed: HTTP {status} {body[:200]}")
            return False
    else:
        print("   ⚠️ No _index data to import")
        return True


def main():
    print("=" * 60)
    print("📦 IMPORT GOOGLE SHEETS → SUPABASE")
    print(f"   URL: {SUPABASE_URL}")
    print("=" * 60)

    # Step 1: Fetch data
    data = fetch_api_data()

    # Step 2: Clear old data before re-import
    for table in ["ban_tin", "lich_hoc", "so_tay", "_index"]:
        clear_table(table)

    # Step 3: Import
    ok = True
    ok &= import_ban_tin(data.get("Ban_tin", []))
    ok &= import_lich_hoc(data.get("Lich_hoc", []))
    ok &= import_so_tay(data.get("So_tay", []))
    ok &= import_index(data.get("_index", []))

    if ok:
        print("\n🎉 IMPORT THÀNH CÔNG! Dữ liệu đã có trong Supabase.")
    else:
        print("\n❌ Import gặp lỗi. Kiểm tra log ở trên.")
        sys.exit(1)


if __name__ == "__main__":
    main()
