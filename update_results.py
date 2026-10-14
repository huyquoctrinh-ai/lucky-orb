#!/usr/bin/env python3
"""Lấy kết quả Vietlott Power 6/55 & Mega 6/45 -> results.json (chỉ dùng thư viện chuẩn)."""
import json, re, sys, time, html, datetime, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "results.json"
KEEP = 120
GAMES = {
    "p55": {"n": 55, "urls": [
        "https://www.minhngoc.net.vn/ket-qua-xo-so/dien-toan-vietlott/power-6x55.html",
        "https://xsmn.mobi/xs-power.html",
        "https://xosodaiphat.com/xs-power-xo-so-power-655.html"]},
    "m45": {"n": 45, "urls": [
        "https://www.minhngoc.net.vn/ket-qua-xo-so/dien-toan-vietlott/mega-6x45.html",
        "https://xosodaiphat.com/xs-mega-xo-so-mega-645.html"]},
}
PA = re.compile(r"#\s*0*(\d{3,5})\s*\|?\s*Ngày quay thưởng\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*((?:\d{2}\s+){6,7})")
PB = re.compile(r"((?:\d{2}\s*-\s*){5,6}\d{2})\s*\|?\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})")


def fetch(url):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (VietlottResultBot/1.0)"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"  ! {url}: {e}", file=sys.stderr)
            time.sleep(3 * (i + 1))
    return ""


def to_text(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def rec(gk, d, nums, k=None):
    n = GAMES[gk]["n"]
    main = nums[:6]
    if len(main) < 6 or len(set(main)) != 6 or not all(1 <= x <= n for x in nums[:7]):
        return None
    r = {"d": d, "n": sorted(main)}
    if k: r["k"] = k
    if gk == "p55" and len(nums) >= 7: r["b"] = nums[6]
    return r


def parse(gk, t):
    found = {}
    for m in PA.finditer(t):
        d = f"{int(m[2]):02d}/{int(m[3]):02d}/{m[4]}"
        r = rec(gk, d, [int(x) for x in re.findall(r"\d{2}", m[5])], int(m[1]))
        if r: found.setdefault(d, r)
    for m in PB.finditer(t):
        d = f"{int(m[2]):02d}/{int(m[3]):02d}/{m[4]}"
        r = rec(gk, d, [int(x) for x in re.findall(r"\d{2}", m[1])])
        if r and d not in found: found[d] = r
        elif r and "b" not in found[d] and "b" in r: found[d]["b"] = r["b"]
    return found


def dkey(d):
    x, y, z = map(int, d.split("/")); return z * 10000 + y * 100 + x


def main():
    data = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {"games": {}}
    changed, parsed_any = False, False
    for gk, g in GAMES.items():
        cur = {r["d"]: r for r in data["games"].get(gk, [])}
        for url in g["urls"]:
            found = parse(gk, to_text(fetch(url)))
            print(f"{gk}: {len(found)} kỳ từ {url}")
            if found: parsed_any = True
            for d, r in found.items():
                if d not in cur:
                    cur[d] = r; changed = True; print(f"  + {gk} {d} {r['n']}")
                else:
                    old = cur[d]
                    for key in ("k", "b"):
                        if key in r and key not in old: old[key] = r[key]; changed = True
                    if old["n"] != r["n"]: print(f"  ? lệch số {gk} {d}: giữ {old['n']}, nguồn báo {r['n']}")
        data["games"][gk] = sorted(cur.values(), key=lambda r: -dkey(r["d"]))[:KEEP]
    if changed:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        data["updated"] = now.strftime("%H:%M %d/%m/%Y")
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), "utf-8")
        print("Đã cập nhật results.json")
    else:
        print("Không có kết quả mới")
    if not parsed_any:
        print("CẢNH BÁO: không đọc được nguồn nào — có thể trang đã đổi cấu trúc.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
