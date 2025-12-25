from dbs import *

settings.zircon.http_server = "https://zircon.aigu.vn"
settings.zircon.ws_server = "wss://wszircon.aigu.vn"

async def nhentai_pageStats(b): return (await (await b.querySelector(".page-number")).value(".textContent")).split("\xa0of\xa0") | apply(int) | aS(list)
async def nhentai_collectUrls(b):
    srcs = []
    for i in range(1000):
        srcs.append(await (await (await b.querySelector("#image-container")).querySelector("img")).value(".src"))
        pageNum, totalPages = await nhentai_pageStats(b); await (await b.querySelector("a.next")).func(".click")
        if pageNum >= totalPages: break
    return srcs
async def nhentai_gotoStart(b):
    for i in range(1000):
        await (await b.querySelector("a.previous")).func(".click")
        if (await nhentai_pageStats(b))[0] == 1: break
async def ep_scan_nhentai(ep): # grab the urls
    if ep.complete: return
    b = zircon.newBrowser(); url = ep.url; await b.pickExtFromGroup("yttri")
    if len([x for x in ep.url.split("nhentai.net/g/")[1].split("/") if x]) == 1: url = url.strip("/") + "/1/"
    await b.goto(url); await nhentai_gotoStart(b)
    if not ep.nPages:
        pageNum, totalPages = await nhentai_pageStats(b); assert pageNum == 1; urls = await nhentai_collectUrls(b)
        for i, url in enumerate(urls):
            if db["pages"].lookup(episodeId=ep.id, pageI=i): continue
            db["pages"].insert(episodeId=ep.id, pageI=i, url=url, complete=0, content=b"", hash1=0)
        ep.nPages = totalPages
    await ep_scan_2(ep)
async def ep_scan_2(ep): # grab the actual images
    for page in db["pages"].select(f"where episodeId = {ep.id} and complete = 0"):
        print(page.id)
        if len(page.content) > 0: page.complete = 1; continue
        try: page.content = requests.get(page.url).content | toImg() | toBytes(); page.complete = 1
        except Exception as e: print(e); page.complete = 0
    if len(db["pages"].select(f"where episodeId = {ep.id} and complete = 0")) == 0: ep.complete = 1





async def hfox_pageNum(b): return int(await (await b.querySelector(".current")).value(".textContent"))
async def hfox_nPages(b): return int(await (await b.querySelector(".total_pages")).value(".textContent"))
async def hfox_collectUrls(b):
    srcs = []; totalPages = await hfox_nPages(b)
    for i in range(1000):
        srcs.append(await (await b.querySelector("#gimg")).value(".src"))
        pageNum = await hfox_pageNum(b); await (await b.querySelector(".nav_next")).func(".click")
        if pageNum >= totalPages: break
    return srcs
async def hfox_gotoStart(b):
    for i in range(1000):
        await (await b.querySelector(".nav_prev")).func(".click")
        if (await hfox_pageNum(b)) == 1: break
async def ep_scan_hfox(ep): # grab the urls
    if ep.complete: return
    b = zircon.newBrowser(); url = ep.url; await b.pickExtFromGroup("yttri")
    if len([x for x in ep.url.split("hentaifox.com/g/")[1].split("/") if x]) == 1: url = url.strip("/") + "/1/"
    await b.goto(url); await hfox_gotoStart(b); totalPages = await hfox_nPages(b)
    if not ep.nPages:
        pageNum = await hfox_pageNum(b); assert pageNum == 1; urls = await hfox_collectUrls(b)
        for i, url in enumerate(urls):
            if db["pages"].lookup(episodeId=ep.id, pageI=i): continue
            db["pages"].insert(episodeId=ep.id, pageI=i, url=url, complete=0, content=b"", hash1=0)
        ep.nPages = totalPages
    await ep_scan_2(ep)



async def h2read_pageStats(b): return [int(x.strip()) for x in (await (await b.querySelector(".page-select_numbers")).value(".textContent")).split("of")]
async def h2read_collectUrls(b):
    srcs = []
    for i in range(1000):
        srcs.append(await (await b.querySelector("#arf-reader")).value(".src"))
        pageNum, totalPages = await h2read_pageStats(b); await (await b.querySelector(".js-page_next")).func(".click")
        if pageNum >= totalPages: break
    return srcs
async def h2read_gotoStart(b):
    for i in range(1000):
        await (await b.querySelector(".js-page_previous")).func(".click")
        if (await h2read_pageStats(b))[0] == 1: break
async def ep_scan_h2read(ep): # grab the urls
    if ep.complete: return
    b = zircon.newBrowser(); await b.pickExtFromGroup("yttri")
    url = "https://hentai2read.com/" + "/".join(ep.url.split("hentai2read.com/")[1].strip("/").split("/")[:2]) + "/"
    await b.goto(url); await h2read_gotoStart(b)
    if not ep.nPages:
        pageNum, totalPages = await h2read_pageStats(b); assert pageNum == 1; urls = await h2read_collectUrls(b)
        for i, url in enumerate(urls):
            if db["pages"].lookup(episodeId=ep.id, pageI=i): continue
            db["pages"].insert(episodeId=ep.id, pageI=i, url=url, complete=0, content=b"", hash1=0)
        ep.nPages = totalPages
    await ep_scan_2(ep)


