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
def api_ep_delete(epId): del db["episodes"][epId]; return "ok"
@app.route("/fragment/ep/<int:epId>")
def fragment_ep(epId): pre = init._jsDAuto(); ep = db["episodes"][epId]; return f"""
<h2>Episode {ep.url}</h2>
<button id="{pre}_scan" class="btn">Scan</button>
<button id="{pre}_view" class="btn">View</button>
<script>{pre}_scan.onclick = async () => {{ await wrapToastReq(fetch(`/api/ep/{ep.id}/scan`)); }}
{pre}_view.onclick = async () => {{ window.open("/viewer/{epId}", "_blank") }}</script>"""

@app.route("/viewer/<int:epId>", daisyEnv=True)
def viewer(epId):
    pre = init._jsDAuto(); ep = db["episodes"][epId]
    imgUrls = [f"/page/{idx[0]}" for idx in db.query(f"select id from pages where episodeId = {ep.id} order by pageI")]
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
<script>
async function preloadImages(urls) {{ const imgs = []; for (const url of urls) {{ const img = new Image(); img.src = url; await img.decode(); imgs.push(img); }} return imgs; }}
let imgUrls = {json.dumps(imgUrls)}; let imgI = 0; preloadImages(imgUrls);
function updateCounter() {{ {pre}_counter.innerHTML = `${{imgI+1}} of {ep.nPages}`; }}
{pre}_prev.onclick = () => {{ imgI = Math.max(0, imgI-1); {pre}_img.src = imgUrls[imgI]; updateCounter(); }}; {pre}_prev.click();
{pre}_next.onclick = () => {{ imgI = Math.min(imgUrls.length-1, imgI+1); {pre}_img.src = imgUrls[imgI]; updateCounter(); }}
{pre}_leftPane.onclick = () => {pre}_prev.click(); {pre}_rightPane.onclick = () => {pre}_next.click();
document.addEventListener("keydown", (e) => {{ if (e.key === "ArrowRight") {pre}_next.click(); if (e.key === "ArrowLeft") {pre}_prev.click(); }});
let id2Tag = {id2Tag}; let tag2Id = {tag2Id}; let tagIds = {ep.tagIds};
function listTags() {{ {pre}_tags.value = `${{tagIds.map(x=>id2Tag[x])}}`; }}; listTags();
function toggleTag(tagId) {{ if (tagIds.includes(tagId)) {{ const index = tagIds.indexOf(tagId); if (index > -1) tagIds.splice(index, 1); }} else tagIds.push(tagId); listTags(); }}
{pre}_save.onclick = async () => {{ await wrapToastReq(fetchPost("/api/ep/{epId}/save", {{ quality: parseInt({pre}_quality.value ?? 0), descr: {pre}_descr.value, tagIds }})); }}
</script>"""

@app.route("/api/ep/<int:epId>/save", methods=["POST"])
def api_ep_save(epId, js): ep = db["episodes"][epId]; ep.quality = js["quality"]; ep.descr = js["descr"]; ep.tagIds = js["tagIds"]; return "ok"

@app.route("/page/<int:pageId>")
def page(pageId): page = db["pages"][pageId]; return page.content, 200, {"Content-Type": "image/jpg"}

k1.logErr.flask(app)
sql.lite_flask(app)

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
        </div><div style="overflow-x: auto">{ui2}</div>
        <div id="{pre}_epDetails"></div>
    </div>
</div>
<script>
    async function {pre}_epDel(row, i, e) {{ await wrapToastReq(fetch(`/api/ep/${{row[0]}}/del`)); }}
    function {pre}_epSelect(row, i, e) {{
        dynamicLoad("#{pre}_epDetails", `/fragment/ep/${{row[0]}}`);
    }}
    {pre}_epNew.onclick = async () => {{ await wrapToastReq(fetchPost("/api/ep/new", {{ url: {pre}_epUrl.value }})); }}
</script>"""

app.run(host="0.0.0.0", port=6005) # same as normal flask code







