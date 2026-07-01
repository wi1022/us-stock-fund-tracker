"""
缇庤偂鍩洪噾娑ㄨ穼鍔╂墜 - 鏁版嵁鏇存柊鑴氭湰
姣忓ぉ缇庤偂鏀剁洏鍚庤繍琛岋紝鏇存柊 data.json 涓殑鎸囨暟娑ㄨ穼鍜屽熀閲戜及鍊?"""
import json
import urllib.request
import re
import os
import sys
from datetime import datetime

# ==================== 閰嶇疆 ====================

# QDII鍩洪噾鍒楄〃
FUNDS = [
    {"name": "鍗庡鍏ㄧ悆绉戞妧鍏堥攱", "code": "005698", "indexTag": "nasdaq"},
    {"name": "鏄撴柟杈惧叏鐞冩垚闀跨簿閫?, "code": "012920", "indexTag": "nasdaq"},
    {"name": "鍥藉瘜鍏ㄧ悆绉戞妧浜掕仈", "code": "006373", "indexTag": "sp500"},
    {"name": "鍢夊疄鍏ㄧ悆浜т笟鍗囩骇", "code": "017730", "indexTag": "sp500"},
    {"name": "閾舵捣娴峰鏁板瓧缁忔祹", "code": "015203", "indexTag": "nasdaq"},
    {"name": "娴﹂摱瀹夌洓鍏ㄧ悆鏅鸿兘绉戞妧", "code": "006555", "indexTag": "sp500"},
    {"name": "鍗庡绉诲姩浜掕仈", "code": "002891", "indexTag": "nasdaq"},
    {"name": "澶╁紭鍏ㄧ悆楂樼鍒堕€?, "code": "016664", "indexTag": "dji"},
    {"name": "鍗庡疂绾虫柉杈惧厠绮鹃€?, "code": "017436", "indexTag": "nasdaq"},
    {"name": "姹囨坊瀵屽叏鐞冪Щ鍔ㄤ簰鑱?, "code": "001668", "indexTag": "nasdaq"},
    {"name": "鏅『闀垮煄绾虫柉杈惧厠绉戞妧", "code": "017091", "indexTag": "nasdaq"},
    {"name": "鍢夊疄缇庡浗鎴愰暱", "code": "000043", "indexTag": "sp500"},
    {"name": "鍗庡疂鑷磋繙娣峰悎", "code": "008253", "indexTag": "sp500"},
    {"name": "闀垮煄鍏ㄧ悆鏂拌兘婧愯溅", "code": "501226", "indexTag": "dji"},
    {"name": "骞垮彂鍏ㄧ悆绮鹃€夎偂绁?, "code": "270023", "indexTag": "sp500"},
    {"name": "澶ф垚绾虫柉杈惧厠100", "code": "000834", "indexTag": "nasdaq"},
]

# 缇庤偂鎸囨暟绗﹀彿
INDICES = {
    "nasdaq": "%5EIXIC",   # 绾虫柉杈惧厠缁煎悎鎸囨暟
    "sp500": "%5EGSPC",    # 鏍囨櫘500
    "dji": "%5EDJI",       # 閬撶惣鏂伐涓氬钩鍧?}

# 鏁版嵁鏂囦欢璺緞
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== 鏁版嵁鑾峰彇 ====================

def get_fund_valuation(code):
    """浠庡ぉ澶╁熀閲戣幏鍙栧熀閲戝疄鏃朵及鍊兼定璺屽箙"""
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
        match = re.search(r"jsonpgz\((.*)\)", content)
        if match:
            data = json.loads(match.group(1))
            gszzl = float(data.get("gszzl", 0))
            gztime = data.get("gztime", "")
            print(f"  {code} {data.get('name', '')}: {gszzl:+.2f}% ({gztime})")
            return gszzl
    except Exception as e:
        print(f"  {code} 鑾峰彇澶辫触: {e}")
    return None


def get_us_index(symbol_key):
    """鑾峰彇缇庤偂鎸囨暟娑ㄨ穼骞?""
    symbol = INDICES[symbol_key]
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")

        if price and prev_close and prev_close != 0:
            change_pct = (price - prev_close) / prev_close * 100
            return round(change_pct, 2)

        # 闄嶇骇锛氱敤鏈€杩戜袱鏃ユ敹鐩樹环璁＄畻
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            change_pct = (closes[-1] - closes[-2]) / closes[-2] * 100
            return round(change_pct, 2)

    except Exception as e:
        print(f"  鎸囨暟 {symbol_key} 鑾峰彇澶辫触: {e}")

    return None


def get_fx_rate():
    """鑾峰彇缇庡厓鍏戜汉姘戝竵姹囩巼鍙婂彉鍔?""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        rate = data["rates"]["CNY"]
        # 姹囩巼鍙樺姩寰堝皬锛屼娇鐢ㄥ浐瀹氬熀鍑嗚绠楀彉鍖?        # 7.25 涓鸿繎浼煎熀鍑嗘眹鐜?        prev_rate = 7.25
        change = (rate - prev_rate) / prev_rate * 100
        print(f"  缇庡厓/浜烘皯甯? {rate:.4f} ({change:+.2f}%)")
        return round(change, 2)
    except Exception as e:
        print(f"  姹囩巼鑾峰彇澶辫触: {e}")
    return None


# ==================== 涓绘祦绋?====================

def main():
    print(f"\n{'='*50}")
    print(f"缇庤偂鍩洪噾鏁版嵁鏇存柊 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # 1. 鑾峰彇缇庤偂鎸囨暟娑ㄨ穼
    print("\n[1/3] 鑾峰彇缇庤偂鎸囨暟娑ㄨ穼...")
    indices = {}
    for key in INDICES:
        val = get_us_index(key)
        if val is not None:
            indices[key] = val
            print(f"  {key}: {val:+.2f}%")
        else:
            print(f"  {key}: 鑾峰彇澶辫触锛屼娇鐢ㄦ棫鏁版嵁")

    # 2. 鑾峰彇姹囩巼
    print("\n[2/3] 鑾峰彇姹囩巼...")
    fx = get_fx_rate()
    if fx is not None:
        indices["fx"] = fx

    # 3. 鑾峰彇鍩洪噾浼板€?    print("\n[3/3] 鑾峰彇鍩洪噾瀹炴椂浼板€?..")
    funds = []
    for fund in FUNDS:
        change = get_fund_valuation(fund["code"])
        if change is not None:
            funds.append({
                "name": fund["name"],
                "code": fund["code"],
                "change": round(change, 2),
                "tag": "澶滅洏",
                "indexTag": fund["indexTag"]
            })
        else:
            # 淇濈暀鏃ф暟鎹?            funds.append({
                "name": fund["name"],
                "code": fund["code"],
                "change": 0,
                "tag": "澶滅洏",
                "indexTag": fund["indexTag"]
            })

    # 4. 鏋勫缓杈撳嚭
    output = {
        "indices": indices,
        "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "funds": funds
    }

    # 5. 鍐欏叆 data.json
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n鉁?鏁版嵁鏇存柊瀹屾垚锛屽凡鍐欏叆 {DATA_FILE}")
    print(f"   鎸囨暟: {len(indices)} 椤?| 鍩洪噾: {len(funds)} 鍙?)
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
