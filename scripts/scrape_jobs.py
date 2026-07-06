#!/usr/bin/env python3
"""Scrape a mokahr campus-recruitment job list into a markdown file.

The mokahr SPA serves its job data through AES-128-CBC encrypted JSON
(``{"data": <b64 ciphertext>, "necromancer": <16-byte key>}``). The IV lives
on ``window.TurboApply.data.aesIv`` and is read at runtime, so nothing is
hardcoded — the script stays valid even if mokahr rotates the IV.

Pipeline:
  1. Headless Chrome loads the jobs list page; capture + decrypt
     ``website/jobs/v2`` → all job ids + list-level metadata.
  2. For each job, load its detail page; capture + decrypt ``website/job``
     → department, commitment, HTML description, locations, …
  3. Render a markdown file (one section per job).

Usage:
  python3 scripts/scrape_jobs.py                       # deeproute 2027 defaults
  python3 scripts/scrape_jobs.py --org deeproute --recruit-id 145894 \
      --output "configs/deeproute-2027秋招-岗位清单.md"

Requirements: selenium, pycryptodome (see requirements.txt).
"""

import argparse
import base64
import html
import json
import re
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt_response(resp: dict, iv: bytes) -> dict:
    """Decrypt a ``{"data", "necromancer"}`` mokahr response to JSON."""
    ct = base64.b64decode(resp["data"])
    key = resp["necromancer"].encode()
    pt = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
    return json.loads(pt)


def html_to_text(h: str) -> str:
    """Convert jobDescription HTML to plain text matching the list format."""
    if not h:
        return ""
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = h.replace("</p>", "\n\n").replace("</li>", "\n")
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    h = re.sub(r"\n{3,}", "\n\n", h)
    return h.strip()


def location_string(locs: list) -> str:
    """e.g. [{'provinceName':'广东','cityName':'福田区'},...] → '广东福田区、北京市海淀区'."""
    return "、".join(f"{l.get('provinceName', '')}{l.get('cityName', '')}" for l in locs)


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    )
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(60)
    return d


def capture_api(driver, url, api_suffix, iv, wait=6, retries=2):
    """Load `url`, return the decrypted JSON of the first response whose URL
    ends with `api_suffix` (e.g. '/website/jobs/v2', '/website/job')."""
    last = None
    for attempt in range(retries):
        if attempt:
            time.sleep(2)
        try:
            driver.get(url)
            time.sleep(wait)
        except Exception as e:
            print(f"  [warn] page load failed: {e}", file=sys.stderr)
            continue
        for entry in driver.get_log("performance"):
            try:
                m = json.loads(entry["message"])["message"]
            except Exception:
                continue
            if m.get("method") != "Network.responseReceived":
                continue
            u = m["params"]["response"]["url"]
            if not (u.endswith(api_suffix) or (api_suffix + "?") in u):
                continue
            rid = m["params"]["requestId"]
            try:
                body = driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": rid}
                )
                resp = json.loads(body["body"])
                if "necromancer" in resp and "data" in resp:
                    return decrypt_response(resp, iv), u
                last = resp
            except Exception:
                continue
    return None, last


def fetch_job_list(driver, base_url, iv):
    """Load #/jobs/, return list of job dicts (id, title, locations, ...)."""
    data, _ = capture_api(driver, base_url + "#/jobs/", "/website/jobs/v2", iv)
    if not data:
        raise RuntimeError("failed to capture website/jobs/v2 (is the page reachable?)")
    jobs = data["data"]["jobs"]
    total = data["data"].get("jobStats", {}).get("total")
    print(f"[info] list API reports {total} jobs, received {len(jobs)}", file=sys.stderr)
    return jobs


def fetch_job_detail(driver, base_url, iv, job_id):
    """Load #/job/<id>, return the decrypted detail `data` dict (or {})."""
    data, _ = capture_api(driver, base_url + f"#/job/{job_id}", "/website/job", iv)
    return (data or {}).get("data") or {}


# Functional taxonomy for grouping jobs (ordered). Titles must match the
# mokahr job title verbatim (including the 【2027秋招】 prefix). Unmapped
# titles fall into "其他" so new jobs never break the script.
CATEGORIES = [
    ("一、自动驾驶算法与评测", [
        "【2027秋招】感知算法工程师",
        "【2027秋招】规划算法工程师",
        "【2027秋招】端到端算法工程师",
        "【2027秋招】SLAM算法工程师",
        "【2027秋招】导航地图算法工程师",
        "【2027秋招】强化学习算法工程师",
        "【2027秋招】系统评测工程师",
    ]),
    ("二、AI 与大模型", [
        "【2027秋招】大模型算法工程师",
        "【2027秋招】AI Agent 算法工程师",
        "【2027秋招】训练优化工程师",
        "【2027秋招】数据生成算法工程师",
    ]),
    ("三、数据工程", [
        "【2027秋招】数据挖掘工程师",
        "【2027秋招】数据湖仓工程师",
    ]),
    ("四、工程开发", [
        "【2027秋招】软件工程师",
        "【2027秋招】后端开发工程师",
        "【2027秋招】前端开发工程师",
        "【2027秋招】AI Infra工程师",
    ]),
    ("五、产品 / 项目 / 商业", [
        "【2027秋招】产品经理",
        "【2027秋招】项目经理",
        "【2027秋招】商业分析师",
    ]),
    ("六、运营与品牌", [
        "【2027秋招】品牌及艺术创意专员",
        "【2027秋招】用户增长运营专员",
    ]),
]


def build_markdown(jobs, page_url, fetched_at):
    by_title = {j["title"]: j for j in jobs}
    mapped = {t for _, ts in CATEGORIES for t in ts}
    others = [j for j in jobs if j["title"] not in mapped]
    cats = list(CATEGORIES)
    if others:
        cats.append(("其他", [j["title"] for j in others]))

    summary = "、".join(f"{name}（{len(ts)}）" for name, ts in cats)
    lines = [
        "# 元戎启行 2027 秋招岗位清单\n",
        f"> 来源：{page_url}\n",
        f"> 岗位数：{len(jobs)}（均为【2027秋招】开头）\n",
        f"> 分类：{summary}\n",
        f"> 抓取时间：{fetched_at}\n",
        "\n---\n",
    ]
    n = 0
    for cat_name, titles in cats:
        if not titles:
            continue
        lines.append(f"\n## {cat_name}（{len(titles)} 个岗位）\n")
        for title in titles:
            n += 1
            r = by_title[title]
            link = f"{page_url}#/job/{r['id']}"
            lines.append(f"\n### {n}. {r['title']}\n")
            lines.append(f"- **部门**：{r['department']}")
            lines.append(f"- **工作性质**：{r['commitment']}")
            lines.append(f"- **工作地点**：{location_string(r['locations'])}")
            lines.append(f"- **发布时间**：{r['publishedAt']}")
            lines.append(f"- **状态**：{r['status']}")
            lines.append(f"- **岗位链接**：{link}")
            lines.append(f"\n#### 岗位描述\n")
            lines.append(r["description"])
            lines.append("\n\n---\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Scrape a mokahr campus recruitment job list.")
    ap.add_argument("--org", default="deeproute", help="mokahr org id (default: deeproute)")
    ap.add_argument("--recruit-id", default="145894", help="recruitment id (default: 145894)")
    ap.add_argument("--locale", default="zh-CN", help="locale (default: zh-CN)")
    ap.add_argument("--output", default="configs/deeproute-2027秋招-岗位清单.md",
                    help="output markdown path")
    ap.add_argument("--fetched-at", default="2026-07-06", help="fetch timestamp label")
    args = ap.parse_args()

    page_url = (
        f"https://app.mokahr.com/campus-recruitment/{args.org}/{args.recruit_id}"
    )  # clean URL for display; SPA routes appended as #/jobs/ , #/job/<id>
    nav_url = f"{page_url}?locale={args.locale}"  # used for actual navigation

    driver = make_driver()
    try:
        # Read IV from the page (rotates occasionally), then capture the list.
        driver.get(nav_url + "#/jobs/")
        time.sleep(6)
        iv_raw = driver.execute_script(
            "return (window.TurboApply && window.TurboApply.data || {}).aesIv || ''"
        )
        if not iv_raw:
            raise RuntimeError("aesIv not found on window.TurboApply.data")
        iv = iv_raw.encode()
        print(f"[info] aesIv = {iv_raw}", file=sys.stderr)

        list_jobs = fetch_job_list(driver, nav_url, iv)

        records = []
        for i, lj in enumerate(list_jobs, 1):
            uid = lj["id"]
            print(f"[{i}/{len(list_jobs)}] {uid[:8]} {lj['title']}", file=sys.stderr)
            det = fetch_job_detail(driver, nav_url, iv, uid)
            if not det:
                print(f"  [warn] no detail API for {uid}; using list fields", file=sys.stderr)
            records.append({
                "id": uid,
                "title": (det.get("title") or lj.get("title", "")).strip(),
                "department": (det.get("department") or {}).get("name", ""),
                "commitment": det.get("commitment") or "全职",
                "locations": det.get("locations") or lj.get("locations") or [],
                "publishedAt": det.get("publishedAt") or lj.get("publishedAt", ""),
                "status": det.get("status") or lj.get("status", ""),
                "description": html_to_text(det.get("jobDescription") or ""),
            })
    finally:
        driver.quit()

    md = build_markdown(records, page_url, args.fetched_at)
    with open(args.output, "w") as f:
        f.write(md)
    print(f"[done] wrote {len(records)} jobs to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
