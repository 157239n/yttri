from adapters import *

app = web.Flask(__name__)

@app.route("/api/ep/<int:epId>/scan")
def api_ep_scan(epId):
    ep = db["episodes"][epId]
    if ep.site == "nhentai": asyncio.run(ep_scan_nhentai(ep)); return "ok"
    if ep.site == "hfox": asyncio.run(ep_scan_hfox(ep)); return "ok"
    if ep.site == "h2read": asyncio.run(ep_scan_h2read(ep)); return "ok"

@app.route("/api/tag/new", methods=["POST"])
def api_tag_new(js): return str(db["tags"].insert(name=js["name"]).id)
@app.route("/api/ep/new", methods=["POST"])
def api_ep_new(js):
    url = js["url"]; boilerplate = dict(url=url, complete=0, createdTime=int(time.time()), tagIds=[])
    if "nhentai.net" in url:
        code = str(int(url.split("nhentai.net/g/")[1].split("/")[0]))
        if db["episodes"].lookup(site="nhentai", code=code): web.toast_error("This episode has appeared before")
        db["episodes"].insert(site="nhentai", code=code, **boilerplate); return "ok"
    if "hentaifox.com" in url:
        code = str(int(url.split("hentaifox.com/g/")[1].split("/")[0]))
        if db["episodes"].lookup(site="hfox", code=code): web.toast_error("This episode has appeared before")
        db["episodes"].insert(site="hfox", code=code, **boilerplate); return "ok"
    if "hentai2read.com" in url:
        code = "/".join(url.split("hentai2read.com/")[1].strip("/").split("/")[:2])
        if db["episodes"].lookup(site="h2read", code=code): web.toast_error("This episode has appeared before")
        db["episodes"].insert(site="h2read", code=code, **boilerplate); return "ok"
    web.toast_error("Don't have any processor available for this site")
@app.route("/api/ep/<int:epId>/del")
def api_ep_delete(epId): db.query(f"delete from pages where episodeId = {epId}"); del db["episodes"][epId]; return "ok"
@app.route("/fragment/ep/<int:epId>")
def fragment_ep(epId): pre = init._jsDAuto(); ep = db["episodes"][epId]; return f"""
<h2>Episode {ep.url}</h2><button id="{pre}_scan" class="btn" style="margin-right: 8px">Scan</button>
<button id="{pre}_view" class="btn" style="margin-right: 8px">Vertical viewer</button><button id="{pre}_hview" class="btn">Horizontal viewer</button>
<script>{pre}_scan.onclick = async () => {{ await wrapToastReq(fetch(`/api/ep/{ep.id}/scan`)); }}
{pre}_view.onclick = async () => {{ window.open("/viewer/{epId}/1", "_blank") }}; {pre}_hview.onclick = async () => {{ window.open("/hviewer/{epId}/1", "_blank") }}</script>"""

def imgEngine(pre, epId, pageI, orient:str=""): ep = db["episodes"][epId]; imgUrls = [f"/{orient}page/{idx[0]}" for idx in db.query(f"select id from pages where episodeId = {ep.id} order by pageI")]; return f"""
async function preloadImages(urls) {{ const imgs = []; for (const url of urls) {{ const img = new Image(); img.src = url; await img.decode(); imgs.push(img); }} return imgs; }}
let imgUrls = {json.dumps(imgUrls)}; let imgI = {pageI}; preloadImages(imgUrls);
function updateCounter() {{ {pre}_counter.innerHTML = `${{imgI+1}} of {ep.nPages}`; history.pushState(null, "", `/{orient}viewer/{epId}/${{imgI+1}}`); }}
function prevPage() {{ imgI = Math.max(0, imgI-1); {pre}_img.src = imgUrls[imgI]; updateCounter(); }}
function nextPage() {{ imgI = Math.min(imgUrls.length-1, imgI+1); {pre}_img.src = imgUrls[imgI]; updateCounter(); }}; prevPage();
document.addEventListener("keydown", (e) => {{ if (e.key === "ArrowRight") nextPage(); if (e.key === "ArrowLeft") prevPage(); }});"""

@app.route("/hviewer/<int:epId>/<int:pageI>", daisyEnv=True)
def hviewer(epId, pageI): pre = init._jsDAuto(); return f"""
<style>button, .no-zoom {{ touch-action: manipulation; }} body {{ padding: 0px; }}</style>
<div style="display: flex; flex-direction: row;">
    <div style="flex: 1"></div><img id="{pre}_img" style="flex: 1; max-height: 100vh;" />
    <div style="flex: 1; display: flex; flex-direction: column"><div style="flex: 1"></div><div style="display: flex; flex-direction: row"><div style="flex: 1"></div><div id="{pre}_counter" style="writing-mode: sideways-lr;"></div><div style="flex: 1"></div></div><div style="flex: 1"></div></div>
</div><script>{imgEngine(pre, epId, pageI, "h")}</script>"""

@app.route("/viewer/<int:epId>/<int:pageI>", daisyEnv=True)
def viewer(epId, pageI):
    pre = init._jsDAuto(); ep = db["episodes"][epId]
    id2Tag = {x:y for x,y in db.query("select id, name from tags")}; tag2Id = {y:x for x,y in db.query("select id, name from tags")}
    tagBtns = "".join([f"<button onclick='toggleTag({x})' class='btn' style='margin-right: 8px; margin-bottom: 8px'>{y}</button>" for x,y in id2Tag.items()])
    return f"""
<style>
    #main {{ flex-direction: column-reverse; }}
    @media (min-width: 600px) {{ #main {{ flex-direction: row; }} }}
    button, .no-zoom {{ touch-action: manipulation; }}
    body {{ padding: 0px; }}
</style>
<div id="main" style="display: flex">
    <div id="sidebar" style="flex: 3; padding: 8px">
        <div style="display: flex; flex-direction: row; align-items: center; width: 100%">
            <h2>Episode {ep.id}</h2><div style="flex: 1"></div>
            <button id="{pre}_save" class="btn">Save</button>
        </div>
        <div>OG url: <a href="{ep.url}" target="_blank" style="color: blue">{ep.url}</a></div>
        <div>Created time: {ep.createdTime | toIso('Asia/Hanoi') | op().replace(*'T ')}</div>
        <div>Quality</div><input id="{pre}_quality" class="input input-bordered" type="number" style="width: 100%" value="{ep.quality or 0}" />
        <div>Description</div><textarea id="{pre}_descr" class="textarea textarea-bordered" style="width: 100%">{ep.descr or ''}</textarea>
        <div>Tags</div><textarea id="{pre}_tags" class="textarea textarea-bordered" style="width: 100%">{ep.tagIds}</textarea>
        <div style="display: flex; flex-direction: row; align-items: center; flex-wrap: wrap">{tagBtns}</div>
    </div>
    <div style="flex: 7; height: 99vh; display: flex; flex-direction: column; align-items: center; position: relative">
        <div id="{pre}_leftPane" style="position: absolute; left: 0px; top: 0px; bottom: 0px; width: 100px"></div>
        <div id="{pre}_rightPane" style="position: absolute; right: 0px; top: 0px; bottom: 0px; width: 100px"></div>
        <img id="{pre}_img" style="flex: 1; max-height: 90vh" />
        <div style="flex: 1"></div>
        <div style="display: flex; flex-direction: row; align-items: center">
            <button id="{pre}_prev" class="btn">Prev</button>
            <div id="{pre}_counter" style="margin: 0px 8px"></div>
            <button id="{pre}_next" class="btn">Next</button>
        </div><div style="flex: 1"></div>
    </div>
</div>
<script>{imgEngine(pre, epId, pageI)}
{pre}_prev.onclick = () => prevPage(); {pre}_next.onclick = () => nextPage(); {pre}_leftPane.onclick = () => prevPage(); {pre}_rightPane.onclick = () => nextPage();
let id2Tag = {id2Tag}; let tag2Id = {tag2Id}; let tagIds = {ep.tagIds};
function listTags() {{ {pre}_tags.value = `${{tagIds.map(x=>id2Tag[x])}}`; }}; listTags();
function toggleTag(tagId) {{ if (tagIds.includes(tagId)) {{ const index = tagIds.indexOf(tagId); if (index > -1) tagIds.splice(index, 1); }} else tagIds.push(tagId); listTags(); }}
{pre}_save.onclick = async () => {{ await wrapToastReq(fetchPost("/api/ep/{epId}/save", {{ quality: parseInt({pre}_quality.value ?? 0), descr: {pre}_descr.value, tagIds }})); }}
</script>"""

@app.route("/api/ep/<int:epId>/save", methods=["POST"])
def api_ep_save(epId, js): ep = db["episodes"][epId]; ep.quality = js["quality"]; ep.descr = js["descr"]; ep.tagIds = js["tagIds"]; return "ok"

@app.route("/page/<int:pageId>")
def page(pageId): page = db["pages"][pageId]; return page.content, 200, {"Content-Type": "image/jpg"}
@app.route("/hpage/<int:pageId>") # explicitly does not cache rotated images, because that would take up so much space (double it in fact!) for not that much gain
def hpage(pageId): return db["pages"][pageId].content | toImg() | op().transpose(PIL.Image.Transpose.ROTATE_90) | toBytes(), 200, {"Content-Type": "image/jpg"}

k1.logErr.flask(app)
sql.lite_flask(app)

@app.route("/fragment/browserAvailable")
def fragment_browserAvailable():
    res = asyncio.run(abrowserAvailable()); msg = f". Activate new window by installing the chrome extension and going to https://zircon.aigu.vn/join/yttri"
    return f"Browser available: {res}{'' if res else msg}"

@app.route("/", daisyEnv=True)
def index():
    pre = init._jsDAuto(); ui1 = db.query("select id, name from tags") | viz.Table(["id", "name"])
    id2Tag = {x:y for x,y in db.query("select id, name from tags")}
    ui2 = db.query("select id, site, code, nPages, complete, quality, createdTime, tagIds, descr from episodes order by id desc") | apply(lambda tagIds: [id2Tag[tagId] for tagId in json.loads(tagIds)] | join(", "), 7) | randomize(None) | (toJsFunc("term") | grep("${term}", lower=True) | viz.Table(["id", "site", "code", "nPages", "complete", "quality", "createdTime", "tagIds", "descr"], ondeleteFName=f"{pre}_epDel", onclickFName=f"{pre}_epSelect", selectable=True, sortF=True, height=500)) | op().interface() | toHtml()
    return f"""
<style>
    #main {{ flex-direction: column-reverse; }}
    @media (min-width: 600px) {{ #main {{ flex-direction: row; }} }}
</style>
<div id="main" style="display: flex">
    <div style="flex: 3">
        <div style="display: flex; flex-direction: row; align-items: center">
            <h2>Tags</h2>
            <input id="{pre}_tagName" class="input input-bordered" style="width: 100px; margin: 0px 8px" placeholder="Name" />
            <button id="{pre}_tagNew" class="btn">New</button>
        </div><div style="overflow-x: auto">{ui1}</div>
    </div><script>{pre}_tagNew.onclick = async () => {{ await wrapToastReq(fetchPost("/api/tag/new", {{ name: {pre}_tagName.value }})); }}</script>
    <div style="flex: 7; overflow-x: auto">
        <div style="display: flex; flex-direction: row; align-items: center">
            <h2>Episodes</h2>
            <input id="{pre}_epUrl" class="input input-bordered" style="width: 150px; margin: 0px 8px" placeholder="Name" />
            <button id="{pre}_epNew" class="btn">New</button>
        </div>
        <div id="{pre}_browserAvailable">Browser available: (fetching...)</div>
        <div style="overflow-x: auto">{ui2}</div><div id="{pre}_epDetails"></div>
        <div style="width: 100%; overflow-x: auto">{dups()}</div>
    </div>
</div>
<script>
    async function {pre}_epDel(row, i, e) {{ await wrapToastReq(fetch(`/api/ep/${{row[0]}}/del`)); }}
    function {pre}_epSelect(row, i, e) {{ dynamicLoad("#{pre}_epDetails", `/fragment/ep/${{row[0]}}`); }}
    {pre}_epNew.onclick = async () => {{ await wrapToastReq(fetchPost("/api/ep/new", {{ url: {pre}_epUrl.value }})); }}
    (async () => {{ {pre}_browserAvailable.innerHTML = await (await fetch("/fragment/browserAvailable")).text(); }})();
</script>"""

def u64_to_i64(u: int) -> int: u &= (1 << 64) - 1; return u - (1 << 64) if u >= (1 << 63) else u
# med: 42/s, diff: 42/s, percep: 40/s
@app.route("/genHash")
def genHash():
    hashes = ["med", "diff", "percep", "block"]
    for hi, h in enumerate(hashes):
        pages = db["pages"]; f = toImg() | toHash(h) | aS(u64_to_i64)
        for i in db.query(f"select id from pages where hash{hi+1} = 0 or hash{hi+1} is null") | cut(0) | tee(every=30).crt():
            try: page = pages[i]; setattr(page, f"hash{hi+1}", page.content | f)
            except Exception as e: print(f"{type(e)}, {e}")
    return "ok"

@app.route("/dups", daisyEnv=True)
def dups():
    pre = init._jsDAuto(); s = ""
    descs = {1: "median brightness threshold", 2: "difference between neighboring pixels", 3: "percep hash, low frequency DCT coefficients", 4: "block regional average brightness"}
    for i in range(1, 5):
        with k1.captureStdout() as out:
            db.query(f"SELECT hash{i}, count(*) as c FROM pages GROUP BY hash{i} HAVING COUNT(*) > 1 order by c desc") | filt("x", 0)\
            | ~apply(lambda h, freq: db.query(f"select episodeId from pages where hash{i} = {h}"))\
            | apply(lambda res: res | cut(0) | sort(None) | unique(None) | aS(list) | aS(tuple)) | filt("len(x)>1") | count() | ~sort(0) | insert(["freq", "episodeIds", "%"]) | display(None)
        s += f"<div style='min-width: 500px'><h3>hash{i}: {descs[i]}</h3><pre>" + (out() | join('\n')) + "</pre></div>"
    return f"""<h2>Image hashing</h2><div>These check for episode duplicates. So all pages/images have several image hashes (i64 value). All of them are checked against all others, to find pages that have identical hashes. Say pageA and pageB and pageC has similar hashes. Then it looks up the episodeId of all 3 pages: (epA, epB, epC). Then count the occurances of these tuples, sort by frequency and display in the tables below. This way you can quickly see what episodes have very similar images to what other episodes. If the frequency column is high, it means there's strong similarity correlation between 2 episodes and should be manually checked for duplication</div>
<button id="{pre}_genHash" class="btn">genHash</button><script>{pre}_genHash.onclick = async () => {{ await wrapToastReq(fetch("/genHash")); }}</script>""" + \
    f"<div style='display: flex; flex-direction: row; flex-wrap: wrap'>{s}</div>"

app.run(host="0.0.0.0", port=80) # same as normal flask code







