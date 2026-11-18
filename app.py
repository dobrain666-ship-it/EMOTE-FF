import os, sys, threading, json, time, struct, base64, socket, requests, urllib3
from flask import Flask, request, jsonify, render_template_string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
api_lock = threading.Lock()

REDIS_URL = os.getenv("REDIS_URL", "https://honest-cod-92290.upstash.io")
REDIS_TOKEN = os.getenv("REDIS_TOKEN", "gQAAAAAAAWiCAAIgcDE3NjI3NDFmM2MyYzU0MzVlOWY3Yjc5YzRlYWVlNzRlZQ")
REDIS_KEY = "ff_cache"

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>MADE BY MAVIA</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&family=JetBrains+Mono:wght@500&display=swap');
:root{--bg:#08090d;--panel:rgba(20,23,34,0.7);--border:rgba(255,255,255,0.08);--blue:#2563eb;--blue-glow:rgba(37,99,235,0.6);--text:#e2e8f0;--text-dim:#94a3b8;--input-bg:rgba(0,0,0,0.4);}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg);background-image:radial-gradient(circle at 50% 0%,rgba(37,99,235,0.15) 0%,transparent 50%);color:var(--text);min-height:100vh;padding:20px 15px 60px;-webkit-tap-highlight-color:transparent;}
.header{text-align:center;margin-bottom:25px;margin-top:10px;}
.header h1{color:#fff;font-size:26px;font-weight:800;letter-spacing:2px;text-shadow:0 0 15px var(--blue-glow),0 0 30px var(--blue-glow);background:linear-gradient(to right,#60a5fa,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.panel{background:var(--panel);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--border);border-radius:14px;padding:16px;margin-bottom:16px;box-shadow:0 8px 32px rgba(0,0,0,0.3);}
.panel-title{font-size:11px;font-weight:800;color:var(--text-dim);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;display:flex;align-items:center;gap:6px;}
.row{display:flex;gap:10px;margin-bottom:10px;flex-wrap:wrap;}
input{background:var(--input-bg);border:1px solid var(--border);color:#fff;padding:12px 14px;border-radius:8px;font-size:13px;font-family:'Plus Jakarta Sans',sans-serif;outline:none;width:100%;transition:all 0.2s;}
input:focus{border-color:var(--blue);box-shadow:0 0 10px rgba(37,99,235,0.3);}
input::placeholder{color:#475569;font-size:12px;font-weight:600;}
#log{background:rgba(0,0,0,0.5);border:1px solid var(--border);padding:12px;border-radius:8px;height:50px;overflow-y:auto;font-family:'JetBrains Mono',monospace;font-size:11px;white-space:pre-wrap;color:var(--text-dim);display:flex;align-items:center;}
.ok{color:#10b981;text-shadow:0 0 8px rgba(16,185,129,0.4);font-weight:bold;}
.err{color:#ef4444;text-shadow:0 0 8px rgba(239,68,68,0.4);font-weight:bold;}
.search-container{position:sticky;top:10px;z-index:100;margin-bottom:15px;}
.search-box{background:rgba(20,23,34,0.9);backdrop-filter:blur(10px);border:1px solid var(--border);color:#fff;padding:14px 16px;border-radius:12px;font-size:13px;width:100%;outline:none;box-shadow:0 4px 20px rgba(0,0,0,0.5);}
.search-box:focus{border-color:var(--blue);}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:12px;}
.card{background:rgba(20,23,34,0.6);border:1px solid var(--border);border-radius:12px;padding:10px;cursor:pointer;text-align:center;transition:all 0.2s cubic-bezier(0.4,0,0.2,1);position:relative;overflow:hidden;}
.card:hover,.card:active{border-color:var(--blue);transform:translateY(-3px) scale(1.02);box-shadow:0 8px 25px rgba(37,99,235,0.25);background:rgba(37,99,235,0.1);}
.card img{width:100%;height:85px;object-fit:contain;background:#000;border-radius:8px;margin-bottom:8px;border:1px solid rgba(255,255,255,0.05);}
.card .nm{font-size:11px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:6px;color:#fff;}
.card .id{font-size:9px;font-family:'JetBrains Mono',monospace;color:#64748b;background:rgba(0,0,0,0.4);display:inline-block;padding:3px 8px;border-radius:6px;}
.top-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.count-badge{background:rgba(37,99,235,0.2);color:#60a5fa;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:0.5px;border:1px solid rgba(37,99,235,0.3);}
</style>
</head>
<body>

<div class="header">
  <h1>MADE BY MAVIA</h1>
</div>

<div class="panel">
  <div class="panel-title">⚙️ Setup</div>
  <div class="row"><input id="tc" placeholder="Team Code" inputmode="numeric" autocomplete="off"></div>
  <div class="row"><input id="uid" placeholder="Target UID" inputmode="numeric" autocomplete="off"></div>
</div>

<div class="panel" style="padding:12px;">
  <div class="panel-title" style="margin-bottom:8px;">📡 Response</div>
  <div id="log">Ready. Fill details & click an emote.</div>
</div>

<div class="top-bar">
  <span style="color:#60a5fa;font-weight:800;font-size:13px;letter-spacing:1px;">EMOTES</span>
  <span class="count-badge" id="countBadge">0 TOTAL</span>
</div>

<div class="search-container">
  <input id="search" class="search-box" placeholder="Search emote..." oninput="render()" autocomplete="off">
</div>

<div class="grid" id="grid"></div>

<script src="/emotes.js"></script>
<script>
let busy = false;

function iconFB(el){
  if(el.dataset.ff && el.dataset.step !== '1'){ el.dataset.step = '1'; el.src = el.dataset.ff; }
  else { el.style.opacity = '0.2'; }
}

function render(){
  const q = document.getElementById('search').value.toLowerCase().trim();
  const g = document.getElementById('grid'); g.innerHTML = '';
  
  let list = EMOTES.filter(e => {
      if (e.id == "67") return false;
      return !q || e.name.toLowerCase().includes(q) || e.id.toString().includes(q);
  });
  
  document.getElementById('countBadge').textContent = list.length + ' TOTAL';
  
  list.slice(0, 150).forEach(e => {
    const d = document.createElement('div');
    d.className = 'card';
    d.onclick = () => send(e.id, e.name);
    d.innerHTML = `<img src="${e.icon}" data-ff="${e.icon_ff}" loading="lazy" onerror="iconFB(this)">
                   <div class="nm">${e.name}</div><div class="id">${e.id}</div>`;
    g.appendChild(d);
  });
}

function log(s, cls){ 
  const l = document.getElementById('log'); 
  l.innerHTML = `<span class="${cls||''}">${s}</span>`;
}

function send(emote_id, name){
  if(busy) return;
  const tc = document.getElementById('tc').value.trim();
  const uid = document.getElementById('uid').value.trim();
  
  if(!tc || !uid){ log('Team Code & UID required!', 'err'); return; }
  
  busy = true;
  log(`Processing ${name}...`);
  
  fetch(`/mavia?Tc=${tc}&Target_Uid=${uid}&Emote_id=${emote_id}`)
  .then(async r => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Server Error");
    return data;
  })
  .then(j => {
    if(j.ok || j.message) log(`Sent ${name} successfully!`, 'ok');
    else log(`Failed: ${j.error || 'Unknown error'}`, 'err');
    setTimeout(() => { busy = false; }, 1500);
  })
  .catch(e => {
    log(`Error: ${e.message}`, 'err');
    setTimeout(() => { busy = false; }, 1500);
  });
}

render();
</script>
</body>
</html>
'''

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/emotes.js')
def emotes_js():
    return open('/storage/emulated/0/ff_static/emotes.js').read(), 200, {'Content-Type': 'application/javascript'}

@app.route('/mavia')
def mavia_endpoint():
    tc = (request.args.get('Tc') or '').strip()
    em = (request.args.get('Emote_id') or '').strip()
    tu = (request.args.get('Target_Uid') or '').strip()
    if not tc.isdigit() or not em.isdigit(): return jsonify(ok=False, error='Invalid parameters'), 400
    try:
        from app import run_api_emote
        with api_lock: res = run_api_emote(tc, int(em), int(tu) if tu else None)
        return jsonify(res), 200
    except Exception as e: return jsonify(ok=False, error=str(e)), 500

app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)
