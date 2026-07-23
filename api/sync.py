"""
Vercel serverless function: Sync Google Sheets → Supabase
GET /api/sync → chạy sync và trả JSON kết quả
"""
import json
import os
import urllib.request
import urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xaxohdyscyxbamvtdjzw.supabase.co")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbG...8SIo")
API_URL = "https://script.google.com/macros/s/AKfycbz73HKnzuubZYVQaharliKVIT9jUUu5IAnmBtv5FVLpjNyDFM3H4m370WHZns__ElAybw/exec"


def supabase_request(method, table, data=None, params=None):
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
    return str(val).strip() if val else ""


def clean_datetime(val):
    val = clean_text(val)
    return val if val else None


def parse_date_dmy(val):
    val = clean_text(val)
    if not val:
        return None
    parts = val.split("/")
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass
    return val


def _parse_bool(val):
    if val is None:
        return True
    s = str(val).strip().upper()
    if s in ("TRUE", "1", "YES", "CÓ", "CO"):
        return True
    if s in ("FALSE", "0", "NO", "KHÔNG", "KHONG"):
        return False
    return True


def fetch_api_data():
    import ssl
    ctx = ssl.create_default_context()
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clear_table(table):
    status, _ = supabase_request("DELETE", table, params={"id": "gt.0"})
    return status < 300


def import_ban_tin(rows):
    data_rows = []
    for i, row in enumerate(rows):
        # Skip header row
        if i == 0 and row.get("Tiêu_đề") == "Tiêu đề":
            continue
        tieu_de = clean_text(row.get("Tiêu_đề") or row.get("Tiêu đề"))
        noi_dung = clean_text(row.get("Nội_dung") or row.get("Nội dung"))
        if not tieu_de and not noi_dung:
            continue
        data_rows.append({
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
        })
    if not data_rows:
        return 0, "no data rows"
    ok = 0
    for i in range(0, len(data_rows), 50):
        batch = data_rows[i : i + 50]
        status, body = supabase_request("POST", "ban_tin", data=batch)
        if status < 300:
            ok += len(batch)
        else:
            return ok, f"HTTP {status}: {body[:200]}"
    return ok, "ok"


def import_lich_hoc(rows):
    data_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            if row.get("Tên bài giảng") == "Tên bài giảng":
                continue
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
    if not data_rows:
        return 0, "no data rows"
    ok = 0
    for i in range(0, len(data_rows), 50):
        batch = data_rows[i : i + 50]
        status, body = supabase_request("POST", "lich_hoc", data=batch)
        if status < 300:
            ok += len(batch)
        else:
            return ok, f"HTTP {status}: {body[:200]}"
    return ok, "ok"


def import_so_tay(rows):
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
            return len(data_rows), "ok"
        return 0, f"HTTP {status}: {body[:200]}"
    return 0, "no data rows"


def import_index(rows):
    data_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            continue
        loai_tb = clean_text(row.get("Loai_TB") or row.get("Loại TB") or row.get("1"))
        icon = clean_text(row.get("icon") or row.get("8"))
        if loai_tb:
            data_rows.append({"loai_tb": loai_tb, "icon": icon})
    if data_rows:
        status, body = supabase_request("POST", "_index", data=data_rows)
        if status < 300:
            return len(data_rows), "ok"
        return 0, f"HTTP {status}: {body[:200]}"
    return 0, "no data rows"


def run_sync():
    data = fetch_api_data()
    ok = all(clear_table(t) for t in ["ban_tin", "lich_hoc", "so_tay", "_index"])

    bt, bt_msg = import_ban_tin(data.get("Ban_tin", []))
    lh, lh_msg = import_lich_hoc(data.get("Lich_hoc", []))
    st, st_msg = import_so_tay(data.get("So_tay", []))
    ix, ix_msg = import_index(data.get("_index", []))

    return {
        "ok": ok,
        "ban_tin": bt,
        "lich_hoc": lh,
        "so_tay": st,
        "_index": ix,
        "messages": [bt_msg, lh_msg, st_msg, ix_msg],
    }


from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/api/sync":
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": "Not found"}).encode())
            return

        try:
            result = run_sync()
            self.send_response(200)
        except Exception as e:
            result = {"ok": False, "error": str(e), "type": type(e).__name__}
            self.send_response(500)

        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())