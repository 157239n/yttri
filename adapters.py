from dbs import *

settings.zircon.http_server = "https://zircon.aigu.vn"
settings.zircon.ws_server = "wss://wszircon.aigu.vn"

def browserAvailable():
    try: b = zircon.newBrowser(); b.pickExtFromGroup("yttri"); return True
    except: return False

# ------------------------------------------- nhentai

@k1.cron(delay=10)
def scanLoop(): # auto scans new episodes
    for ep in db["eps"].select("where errUrls is null"):
        print(f"scanning {ep.id}")
        try:
            if ep.site == "nhentai": ep_scan_nhentai(ep)
            if ep.site == "hfox":    ep_scan_hfox(ep)
            if ep.site == "h2read":  ep_scan_h2read(ep)
        except Exception as e: ep.errUrls = f"{type(e)}\n{e}\n{traceback.format_exc()}"

def nhentai_pageStats(b): return b.querySelector(".page-number").textContent.split("\xa0of\xa0") | apply(int) | aS(list)
def nhentai_collectUrls(b):
    srcs = []
    for i in range(1000):
        print(f"page: {i}")
        srcs.append(b.querySelector("#image-container img").src)
        pageNum, totalPages = nhentai_pageStats(b); b.querySelector("a.next").click()
        if pageNum >= totalPages: break
    return srcs
def nhentai_gotoStart(b):
    for i in range(1000):
        b.querySelector("a.previous").click()
        if nhentai_pageStats(b)[0] == 1: break
def ep_scan_nhentai(ep): # grab the urls
    b = zircon.newBrowser(); url = ep.url; b.pickExtFromGroup("yttri")
    if len([x for x in ep.url.split("nhentai.net/g/")[1].split("/") if x]) == 1: url = url.strip("/") + "/1/"
    b.goto(url); nhentai_gotoStart(b); print("step 1")
    if not ep.nPages:
        pageNum, totalPages = nhentai_pageStats(b); assert pageNum == 1; ep.urls = nhentai_collectUrls(b); ep.errUrls = ""; print("step 2")
        for i, url in enumerate(ep.urls):
            if db["pages"].lookup(epId=ep.id, pageI=i): continue
            db["pages"].insert(epId=ep.id, pageI=i, url=url, imgB=b"")
        ep.nPages = totalPages; print("step 3")
    threading.Thread(target=ep_scan_2, args=(ep,)).start()
def u64_to_i64(u: int) -> int: u &= (1 << 64) - 1; return u - (1 << 64) if u >= (1 << 63) else u
def ep_scan_2(ep): # grab the actual images
    return # TODO: do full, across all episodes, instead of per-episode like this
    lock = k1.SharedLock("scanLock")
    def downloadPage(pageId):
        db = sql("dbs/main.db", mode="lite", manage=True)["default"]
        page = db["pages"][pageId]
        if len(page.content) > 0: page.errImg = ""; return # already downloaded
        try:
            res = requests.get(page.url)
            if not res.ok: return
            content = res.content | toImg() | toBytes()
            with lock: page.content = content; page.errImg = ""
        except Exception as e: page.errImg = f"{type(e)}\n{e}\n{traceback.format_exc()}"
        try:
            im = page.content | toImg()
            with lock: page.hash1 = im | toHash("med") | aS(u64_to_i64); page.hash2 = im | toHash("diff") | aS(u64_to_i64); page.hash3 = im | toHash("percep") | aS(u64_to_i64); page.hash4 = im | toHash("block") | aS(u64_to_i64)
        except Exception as e: page.errHash = f"{type(e)}\n{e}\n{traceback.format_exc()}"
    db["pages"].query(f"select id from pages where epId = {ep.id} and errImg is null") | cut(0) | applyMp(downloadPage, 10) | ignore()

# ------------------------------------------- hentaifox

def hfox_pageNum(b): return int(b.querySelector(".current").textContent)
def hfox_nPages(b): return int(b.querySelector(".total_pages").textContent)
def hfox_collectUrls(b):
    srcs = []; totalPages = hfox_nPages(b)
    imgE = b.querySelector("#gimg")
    nextE = b.querySelector(".nav_next")
    curE = b.querySelector(".current")
    for i in range(1000):
        print(f"hfox page {i}")
        srcs.append(imgE.src); pageNum = int(curE.textContent); nextE.click()
        if pageNum >= totalPages: break
    return srcs
def hfox_gotoStart(b):
    prevE = b.querySelector(".nav_prev"); curE = b.querySelector(".current")
    for i in range(1000):
        prevE.click()
        if int(curE.textContent) == 1: break
def ep_scan_hfox(ep): # grab the urls
    b = zircon.newBrowser(); url = ep.url; b.pickExtFromGroup("yttri")
    if len([x for x in ep.url.split("hentaifox.com/g/")[1].split("/") if x]) == 1: url = url.strip("/") + "/1/"
    b.goto(url); print("after goto"); hfox_gotoStart(b); print("after start"); totalPages = hfox_nPages(b); print("after nPages")
    if not ep.nPages:
        pageNum = hfox_pageNum(b); assert pageNum == 1; ep.urls = hfox_collectUrls(b); print("after correct urls"); ep.errUrls = ""
        for i, url in enumerate(ep.urls):
            if db["pages"].lookup(epId=ep.id, pageI=i): continue
            db["pages"].insert(epId=ep.id, pageI=i, url=url, imgB=b"")
        ep.nPages = totalPages
    ep_scan_2(ep)

# ------------------------------------------- hentai2read

def h2read_pageStats(b): return [int(x.strip()) for x in b.querySelector(".page-select_numbers").textContent.split("of")]
def h2read_collectUrls(b):
    srcs = []
    for i in range(1000):
        srcs.append(b.querySelector("#arf-reader").src)
        pageNum, totalPages = h2read_pageStats(b); b.querySelector(".js-page_next").click()
        if pageNum >= totalPages: break
    return srcs
def h2read_gotoStart(b):
    for i in range(1000):
        b.querySelector(".js-page_previous").click()
        if h2read_pageStats(b)[0] == 1: break
def ep_scan_h2read(ep): # grab the urls
    b = zircon.newBrowser(); b.pickExtFromGroup("yttri")
    url = "https://hentai2read.com/" + "/".join(ep.url.split("hentai2read.com/")[1].strip("/").split("/")[:2]) + "/"
    b.goto(url); h2read_gotoStart(b)
    if not ep.nPages:
        pageNum, totalPages = h2read_pageStats(b); assert pageNum == 1; ep.urls = h2read_collectUrls(b); ep.errUrls = ""
        for i, url in enumerate(ep.urls):
            if db["pages"].lookup(epId=ep.id, pageI=i): continue
            db["pages"].insert(epId=ep.id, pageI=i, url=url, imgB=b"")
        ep.nPages = totalPages
    ep_scan_2(ep)


