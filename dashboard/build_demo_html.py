"""Build the single-file BreedForward demo from results/advance2008.csv and results_summary/stage4_sampling_curve.csv.

    python dashboard/build_demo_html.py   (from the repo root) -> results/breedforward_demo.html

The output embeds the 8,014-line advancement table (predictions + real 2008 yields). It is a team/judging-room
file and stays under results/ (gitignored). No network, no server: double-click to open.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ADV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/advance2008.csv")
CURVE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("results_summary/stage4_sampling_curve.csv")
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("results/breedforward_demo.html")

adv = pd.read_csv(ADV, dtype={"LINE_ID": str, "POP": str})
z = lambda s: ((s - s.mean()) / s.std()).round(3)
cols = {
    "id": adv.LINE_ID.tolist(),
    "pop": adv.POP.tolist(),
    "hg": adv.HG.astype(int).tolist(),
    "yld": adv.pred_yld.round(2).tolist(),
    "mst": adv.pred_mst.round(3).tolist(),
    "twt": adv.pred_twt.round(3).tolist(),
    "erm": adv.pred_erm.round(3).tolist(),
    "lodg": adv.pop_lodging_obs.round(2).tolist(),
    "obs": adv.obs_yld_2008.round(2).tolist(),
    "z": {k: z(adv[c]).tolist() for k, c in [("yld", "pred_yld"), ("twt", "pred_twt"), ("mst", "pred_mst"), ("erm", "pred_erm"), ("lodg", "pop_lodging_obs")]},
}
curve = pd.read_csv(CURVE)
c = curve[(curve.trait == "YLD") & (curve.scheme == "sib")].sort_values("frac")
curve_js = {"frac": c.frac.tolist(), "r": c.r.round(3).tolist(), "gain": c.gain.round(2).tolist(),
            "plots": c.plots_used.astype(int).tolist(), "gain_max": round(float(c.gain_max.mean()), 2)}
data_js = json.dumps(cols, separators=(",", ":"))
curve_js = json.dumps(curve_js, separators=(",", ":"))

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BreedForward demo</title>
<style>
:root{
  --bg:#FCFCFB; --card:#FFFFFF; --ink:#1A1A1A; --ink2:#4A4A4A; --muted:#7A7A7A; --line:#E3E3E0; --grid:#ECECEA;
  --navy:#1B2A4A; --green:#2E6B3A; --blue:#0072B2; --blue2:#7FB6DB; --blue3:#CFE3F1; --ctx:#C4C4C0; --warn:#D55E00; --warnbg:#FBEDE4; --gold:#C9A227;
  --radius:12px; --shadow:0 1px 2px rgba(0,0,0,.06),0 4px 14px rgba(0,0,0,.05);
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#141518; --card:#1D1F24; --ink:#EDEDEA; --ink2:#C7C7C2; --muted:#9A9A95; --line:#2E3138; --grid:#262930;
  --navy:#C9D4EA; --green:#8FCB9B; --blue:#4DA3E0; --blue2:#2F6E9C; --blue3:#23445C; --ctx:#4A4C52; --warn:#F08A4B; --warnbg:#3A2416; --gold:#E0BD5A;
}}
:root[data-theme="dark"]{
  --bg:#141518; --card:#1D1F24; --ink:#EDEDEA; --ink2:#C7C7C2; --muted:#9A9A95; --line:#2E3138; --grid:#262930;
  --navy:#C9D4EA; --green:#8FCB9B; --blue:#4DA3E0; --blue2:#2F6E9C; --blue3:#23445C; --ctx:#4A4C52; --warn:#F08A4B; --warnbg:#3A2416; --gold:#E0BD5A;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:20px 16px 48px}
header{display:flex;align-items:baseline;gap:18px;flex-wrap:wrap;margin-bottom:14px}
.brand{font-weight:800;font-size:26px;letter-spacing:-.02em}
.brand b{color:var(--navy)} .brand i{color:var(--green);font-style:normal}
.scen{color:var(--ink2);font-size:16px}
.grid{display:grid;grid-template-columns:340px 1fr;gap:16px}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:16px}
h2{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0 0 10px;font-weight:700}
h3{margin:0 0 6px;font-size:18px;font-weight:700}
.sub{color:var(--ink2);font-size:14px;margin:0 0 10px}
.presets{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.presets button{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 10px;border-radius:999px;cursor:pointer;font-size:13px}
.presets button[aria-pressed="true"]{background:var(--blue);border-color:var(--blue);color:#fff}
.sl{margin:8px 0 10px}
.sl label{display:flex;justify-content:space-between;font-size:13px;color:var(--ink2);margin-bottom:2px}
.sl label output{font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600}
.sl input[type=range]{width:100%;accent-color:var(--blue)}
.sl.dis{opacity:.55}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:12px}
@media (max-width:700px){.tiles{grid-template-columns:repeat(2,1fr)}}
.tile{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:12px 14px}
.tile .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.tile .v{font-size:28px;font-weight:800;font-variant-numeric:tabular-nums;letter-spacing:-.02em;line-height:1.2}
.tile .v.neg{color:var(--warn)}
.tile .d{font-size:12px;color:var(--ink2)}
.warn{display:none;background:var(--warnbg);border:1px solid var(--warn);color:var(--ink);border-radius:10px;padding:10px 12px;margin-bottom:12px;font-size:14px}
.warn.on{display:flex;gap:10px;align-items:flex-start}
.warn .ic{color:var(--warn);font-weight:800}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:12px;flex-wrap:wrap}
.tabs button{background:none;border:0;border-bottom:2px solid transparent;padding:8px 12px;color:var(--ink2);cursor:pointer;font-size:14px;margin-bottom:-1px}
.tabs button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--blue);font-weight:700}
.panel{display:none}.panel.on{display:block}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
select,input[type=search]{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px;font-size:14px}
.btn{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 10px;border-radius:8px;cursor:pointer;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--grid);text-align:right;white-space:nowrap}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2),th:nth-child(3),td:nth-child(3){text-align:left}
th{position:sticky;top:0;background:var(--card);color:var(--muted);font-weight:600;font-size:12px}
tr.adv td:first-child{box-shadow:inset 3px 0 0 var(--blue)}
.tw{max-height:520px;overflow:auto;border:1px solid var(--line);border-radius:10px}
.note{color:var(--muted);font-size:12.5px;margin-top:8px}
svg text{font-family:inherit;fill:var(--ink2);font-size:12px}
svg .ax{stroke:var(--line)} svg .gr{stroke:var(--grid)}
.tt{position:fixed;pointer-events:none;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 9px;font-size:12.5px;box-shadow:var(--shadow);display:none;z-index:10;max-width:260px}
.tt b{font-weight:700}
.legend{display:flex;gap:14px;font-size:12.5px;color:var(--ink2);margin:6px 0 2px;flex-wrap:wrap}
.legend span::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px;background:var(--c)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media (max-width:900px){.two{grid-template-columns:1fr}}
kbd{font:12px ui-monospace,Menlo,Consolas,monospace;background:var(--grid);padding:1px 5px;border-radius:4px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="brand"><b>Breed</b><i>Forward</i></div>
  <div class="scen">January 2008. The plots are cut. Which of these 8,014 lines advance?</div>
</header>

<div class="grid">
  <aside class="card">
    <h2>The breeder's lever: index weights</h2>
    <div class="presets" id="presets">
      <button data-p="default" aria-pressed="true">default</button>
      <button data-p="yield" aria-pressed="false">yield only</button>
      <button data-p="equal" aria-pressed="false">equal weights</button>
      <button data-p="custom" aria-pressed="false">custom</button>
    </div>
    <div id="sliders"></div>
    <div class="sl">
      <label><span>share of candidates to advance</span><output id="fracOut">20%</output></label>
      <input type="range" id="frac" min="5" max="50" step="5" value="20">
    </div>
    <p class="note">Weights apply to z-scores of each trait. Predictions are as of January 2008: mean of the phenotyped siblings plus a within-family marker model. Observed 2008 yield is used only to score the choice.</p>
  </aside>

  <main>
    <div class="tiles">
      <div class="tile"><div class="k">candidate lines</div><div class="v" id="tN"></div><div class="d">held-out half of every 2008 family</div></div>
      <div class="tile"><div class="k">advanced</div><div class="v" id="tK"></div><div class="d" id="tKd"></div></div>
      <div class="tile"><div class="k">realised 2008 yield gain</div><div class="v" id="tG"></div><div class="d">advanced set mean minus all-candidate mean, bu/ac</div></div>
      <div class="tile"><div class="k">of perfect foresight</div><div class="v" id="tP"></div><div class="d" id="tPd"></div></div>
    </div>
    <div class="warn" id="warn"><span class="ic">!</span><span id="warnTxt"></span></div>

    <div class="card">
      <div class="tabs" role="tablist">
        <button role="tab" aria-selected="true" data-t="list">Advancement list</button>
        <button role="tab" aria-selected="false" data-t="fam">Family view</button>
        <button role="tab" aria-selected="false" data-t="qual">How good is the prediction</button>
        <button role="tab" aria-selected="false" data-t="curve">The sampling curve</button>
      </div>

      <section class="panel on" id="p-list">
        <div class="row">
          <select id="popSel"><option value="">all families</option></select>
          <input type="search" id="q" placeholder="find a line id">
          <button class="btn" id="dl">download full ranked list (CSV)</button>
          <span class="note" id="listNote"></span>
        </div>
        <div class="tw"><table id="tbl"><thead><tr>
          <th>rank</th><th>line</th><th>family</th><th>HG</th><th>pred yield</th><th>pred MST</th><th>pred TWT</th><th>pred ERM</th><th>family lodging</th><th>index</th><th>advance</th><th>obs 2008 yield</th>
        </tr></thead><tbody></tbody></table></div>
        <p class="note">pred_* are model predictions made with January 2008 information. Yields are deviations from the environment by tester mean, bu/ac. Blue bar = advanced under the current weights.</p>
      </section>

      <section class="panel" id="p-fam">
        <h3>Families, not lines, carry most of the signal</h3>
        <p class="sub">Each dot is a family: mean predicted yield of its candidates against their mean observed 2008 yield. Dot size = number of candidate lines. Hover for the family.</p>
        <div class="legend"><span style="--c:var(--blue)">most of the family advanced</span><span style="--c:var(--blue2)">some advanced</span><span style="--c:var(--ctx)">none advanced</span></div>
        <div id="famChart"></div>
        <div class="tw" style="max-height:300px;margin-top:12px"><table id="famTbl"><thead><tr><th>family</th><th>HG</th><th>lines</th><th>advanced</th><th>share</th><th>pred yield</th><th>obs 2008 yield</th><th>lodging</th></tr></thead><tbody></tbody></table></div>
      </section>

      <section class="panel" id="p-qual">
        <h3 id="qualTitle"></h3>
        <p class="sub">Every candidate line: predicted against observed 2008 yield. Real signal, lots of noise. The ceiling is r about 0.68 because each 2008 line mean rests on about five plots.</p>
        <div class="legend"><span style="--c:var(--blue)">advanced under current weights</span><span style="--c:var(--ctx)">not advanced</span></div>
        <div id="qualChart"></div>
      </section>

      <section class="panel" id="p-curve">
        <h3>Ten percent of every family buys most of the gain</h3>
        <p class="sub">Phenotype a random share of each 2008 family, predict the rest from the family mean, advance the top 20%, score on real 2008 yield. Mean of three draws. This is the answer to the plot-cut question.</p>
        <div class="two"><div id="curveGain"></div><div id="curveR"></div></div>
        <p class="note">Zero percent is the genotype-only model (r 0.13, +1.7 bu/ac). Perfect foresight would be +12.7. The advancement list uses the 50% split with within-family markers added on top.</p>
      </section>
    </div>
  </main>
</div>
</div>
<div class="tt" id="tt"></div>

<script>
const D = __DATA__;
const CURVE = __CURVE__;
const N = D.id.length;
const KEYS = ["yld","twt","mst","erm","lodg"];
const LAB = {yld:"yield (predicted)", twt:"test weight (predicted)", mst:"moisture (predicted, negative = drier is better)", erm:"maturity (predicted, negative = earlier is better)", lodg:"family lodging (observed, negative = less is better)"};
const PRESETS = {default:{yld:.5,twt:.1,mst:-.15,erm:-.05,lodg:-.2}, yield:{yld:1,twt:0,mst:0,erm:0,lodg:0}, equal:{yld:.2,twt:.2,mst:-.2,erm:-.2,lodg:-.2}};
let preset = "default", W = {...PRESETS.default}, frac = 0.20;
let order = [], advanced = new Uint8Array(N), rankOf = new Int32Array(N), idx = new Float32Array(N);
const $ = s => document.querySelector(s);
const fmt = (x,d=2) => (x>=0?"+":"") + x.toFixed(d);
const obsMean = D.obs.reduce((a,b)=>a+b,0)/N;
const pct=(arr,q)=>{const a=[...arr].sort((x,y)=>x-y); return a[Math.min(a.length-1,Math.floor(q*a.length))];};
const XR=[Math.floor(pct(D.yld,0.002)), Math.ceil(pct(D.yld,0.998))], YR=[Math.floor(pct(D.obs,0.002)/5)*5, Math.ceil(pct(D.obs,0.998)/5)*5];
const oracleGain = (() => { const s=[...D.obs].sort((a,b)=>b-a); return k => s.slice(0,k).reduce((a,b)=>a+b,0)/k - obsMean; })();

// ---------- sliders ----------
const sl = $("#sliders");
KEYS.forEach(k => {
  const d = document.createElement("div"); d.className="sl"; d.id="sl-"+k;
  d.innerHTML = `<label><span>${LAB[k]}</span><output id="o-${k}"></output></label><input type="range" id="w-${k}" min="-0.5" max="1" step="0.05">`;
  sl.appendChild(d);
  d.querySelector("input").addEventListener("input", e => { W[k] = +e.target.value; render(); });
});
$("#presets").addEventListener("click", e => {
  const b = e.target.closest("button"); if(!b) return;
  preset = b.dataset.p; if (PRESETS[preset]) W = {...PRESETS[preset]};
  [...$("#presets").children].forEach(x => x.setAttribute("aria-pressed", x===b));
  render();
});
$("#frac").addEventListener("input", e => { frac = +e.target.value/100; render(); });
$("#popSel").addEventListener("change", renderTable);
$("#q").addEventListener("input", renderTable);
document.querySelectorAll(".tabs button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".tabs button").forEach(x => x.setAttribute("aria-selected", x===b));
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("on", p.id==="p-"+b.dataset.t));
  drawCharts();
}));
(() => { const pops=[...new Set(D.pop)].sort(); const s=$("#popSel"); pops.forEach(p=>{const o=document.createElement("option");o.value=p;o.textContent=p;s.appendChild(o);}); })();

// ---------- compute ----------
function compute(){
  for (let i=0;i<N;i++){ let s=0; for (const k of KEYS) s += W[k]*D.z[k][i]; idx[i]=s; }
  order = Array.from({length:N},(_,i)=>i).sort((a,b)=>idx[b]-idx[a]);
  const K = Math.round(frac*N);
  advanced.fill(0); let sum=0;
  order.forEach((i,r)=>{ rankOf[i]=r+1; if(r<K){advanced[i]=1; sum+=D.obs[i];} });
  return {K, gain: sum/K - obsMean, oracle: oracleGain(K)};
}
let S;
const REF = (() => { const w=PRESETS.default; const v=new Float32Array(N); for(let i=0;i<N;i++){let t=0; for(const k of KEYS) t+=w[k]*D.z[k][i]; v[i]=t;} const o=Array.from({length:N},(_,i)=>i).sort((a,b)=>v[b]-v[a]); const K=Math.round(0.2*N); let s=0; for(let r=0;r<K;r++) s+=D.obs[o[r]]; return s/K-obsMean; })();
function render(){
  KEYS.forEach(k => { const el=$("#w-"+k); el.value=W[k]; el.disabled = preset!=="custom"; $("#o-"+k).textContent=W[k].toFixed(2); $("#sl-"+k).classList.toggle("dis", preset!=="custom"); });
  $("#fracOut").textContent = Math.round(frac*100)+"%";
  S = compute();
  $("#tN").textContent = N.toLocaleString();
  $("#tK").textContent = S.K.toLocaleString(); $("#tKd").textContent = `top ${Math.round(frac*100)}% by index`;
  const g=$("#tG"); g.textContent = fmt(S.gain)+" bu/ac"; g.classList.toggle("neg", S.gain<0);
  $("#tP").textContent = Math.round(100*S.gain/S.oracle)+"%"; $("#tPd").textContent = `perfect foresight: ${fmt(S.oracle)} bu/ac`;
  const lost = 1 - S.gain/REF; $("#warn").classList.toggle("on", S.gain < 0.6*REF);
  $("#warnTxt").innerHTML = `These weights give up <b>${Math.round(100*lost)}%</b> of the gain the default index realises (${fmt(REF)} bu/ac). Maturity and moisture now weigh as much as yield, so the index favours early, dry lines over high-yielding ones.`;
  renderTable(); drawCharts();
}

// ---------- table ----------
function renderTable(){
  const pop=$("#popSel").value, q=$("#q").value.trim().toLowerCase();
  let rows = order.filter(i => (!pop || D.pop[i]===pop) && (!q || D.id[i].toLowerCase().includes(q)));
  const total = rows.length; rows = rows.slice(0,300);
  $("#tbl tbody").innerHTML = rows.map(i => `<tr class="${advanced[i]?"adv":""}"><td>${rankOf[i]}</td><td>${D.id[i]}</td><td>${D.pop[i]}</td><td>${D.hg[i]}</td><td>${D.yld[i].toFixed(2)}</td><td>${D.mst[i].toFixed(2)}</td><td>${D.twt[i].toFixed(2)}</td><td>${D.erm[i].toFixed(2)}</td><td>${D.lodg[i].toFixed(2)}</td><td>${idx[i].toFixed(2)}</td><td>${advanced[i]?"yes":""}</td><td>${D.obs[i].toFixed(2)}</td></tr>`).join("");
  $("#listNote").textContent = total>300 ? `showing 300 of ${total.toLocaleString()} (download for all)` : `${total.toLocaleString()} lines`;
}
$("#dl").addEventListener("click", () => {
  const h="rank,LINE_ID,POP,HG,pred_yld,pred_mst,pred_twt,pred_erm,pop_lodging_obs,index,advance,obs_yld_2008\n";
  const body = order.map(i=>[rankOf[i],D.id[i],D.pop[i],D.hg[i],D.yld[i],D.mst[i],D.twt[i],D.erm[i],D.lodg[i],idx[i].toFixed(3),advanced[i]?1:0,D.obs[i]].join(",")).join("\n");
  const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([h+body],{type:"text/csv"})); a.download="advance2008_ranked.csv"; a.click();
});

// ---------- charts ----------
const tt=$("#tt");
function showTT(e,html){ tt.innerHTML=html; tt.style.display="block"; const x=Math.min(e.clientX+14, innerWidth-280), y=Math.min(e.clientY+14, innerHeight-80); tt.style.left=x+"px"; tt.style.top=y+"px"; }
function hideTT(){ tt.style.display="none"; }
function scale(d0,d1,r0,r1){ const f=v=>r0+(v-d0)/(d1-d0)*(r1-r0); f.ticks=n=>{const step=nice((d1-d0)/n); const out=[]; for(let t=Math.ceil(d0/step)*step; t<=d1+1e-9; t+=step) out.push(+t.toFixed(6)); return out;}; return f; }
function nice(x){ const p=Math.pow(10,Math.floor(Math.log10(x))); const m=x/p; return (m<1.5?1:m<3.5?2:m<7.5?5:10)*p; }
function frame(w,h,m,xs,ys,xl,yl,xfmt=v=>v,yfmt=v=>v){
  let s=`<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w}px;display:block">`;
  ys.ticks(5).forEach(t=>{const y=ys(t); s+=`<line class="gr" x1="${m.l}" x2="${w-m.r}" y1="${y}" y2="${y}"/><text x="${m.l-8}" y="${y+4}" text-anchor="end">${yfmt(t)}</text>`;});
  xs.ticks(6).forEach(t=>{const x=xs(t); s+=`<text x="${x}" y="${h-m.b+18}" text-anchor="middle">${xfmt(t)}</text>`;});
  s+=`<line class="ax" x1="${m.l}" x2="${w-m.r}" y1="${h-m.b}" y2="${h-m.b}"/>`;
  s+=`<text x="${(m.l+w-m.r)/2}" y="${h-4}" text-anchor="middle">${xl}</text>`;
  s+=`<text transform="translate(14,${(m.t+h-m.b)/2}) rotate(-90)" text-anchor="middle">${yl}</text>`;
  return s;
}
let famCache=null;
function families(){
  const f=new Map();
  for(let i=0;i<N;i++){ let o=f.get(D.pop[i]); if(!o){o={pop:D.pop[i],hg:D.hg[i],n:0,adv:0,py:0,oy:0,lodg:D.lodg[i]}; f.set(D.pop[i],o);} o.n++; o.adv+=advanced[i]; o.py+=D.yld[i]; o.oy+=D.obs[i]; }
  return [...f.values()].map(o=>({...o, py:o.py/o.n, oy:o.oy/o.n, share:o.adv/o.n}));
}
function drawCharts(){
  const on = document.querySelector(".panel.on").id;
  if(on==="p-fam") drawFam(); else if(on==="p-qual") drawQual(); else if(on==="p-curve") drawCurve();
}
function drawFam(){
  const F=families(); const w=900,h=420,m={l:56,r:16,t:12,b:44};
  const fx=Math.ceil(Math.max(...F.map(f=>Math.abs(f.py)))), fy=Math.ceil(Math.max(...F.map(f=>Math.abs(f.oy)))/5)*5;
  const xs=scale(-fx,fx,m.l,w-m.r), ys=scale(-fy,fy,h-m.b,m.t);
  let s=frame(w,h,m,xs,ys,"family mean predicted yield, bu/ac (deviation)","family mean observed 2008 yield");
  s+=`<line class="ax" x1="${xs(0)}" x2="${xs(0)}" y1="${m.t}" y2="${h-m.b}" stroke-dasharray="3 3"/><line class="ax" x1="${m.l}" x2="${w-m.r}" y1="${ys(0)}" y2="${ys(0)}" stroke-dasharray="3 3"/>`;
  F.sort((a,b)=>b.n-a.n).forEach((f,j)=>{ const r=Math.max(4,Math.sqrt(f.n)*1.6); const col=f.share>=.5?"var(--blue)":f.share>0?"var(--blue2)":"var(--ctx)";
    s+=`<circle data-j="${j}" cx="${xs(f.py)}" cy="${ys(f.oy)}" r="${r}" fill="${col}" fill-opacity=".8" stroke="var(--card)" stroke-width="1.5"/>`; });
  s+="</svg>"; const el=$("#famChart"); el.innerHTML=s;
  el.querySelectorAll("circle").forEach(c=>{ const f=F[+c.dataset.j]; c.addEventListener("mousemove",e=>showTT(e,`<b>${f.pop}</b> (HG ${f.hg})<br>${f.n} candidate lines, ${f.adv} advanced (${Math.round(100*f.share)}%)<br>pred ${fmt(f.py)}, observed 2008 ${fmt(f.oy)} bu/ac<br>family lodging ${f.lodg.toFixed(2)}`)); c.addEventListener("mouseleave",hideTT); });
  $("#famTbl tbody").innerHTML = F.sort((a,b)=>b.oy-a.oy).map(f=>`<tr><td>${f.pop}</td><td>${f.hg}</td><td>${f.n}</td><td>${f.adv}</td><td>${Math.round(100*f.share)}%</td><td>${f.py.toFixed(2)}</td><td>${f.oy.toFixed(2)}</td><td>${f.lodg.toFixed(2)}</td></tr>`).join("");
}
function pearson(a,b){ let n=a.length,sa=0,sb=0; for(let i=0;i<n;i++){sa+=a[i];sb+=b[i];} sa/=n;sb/=n; let xy=0,xx=0,yy=0; for(let i=0;i<n;i++){const u=a[i]-sa,v=b[i]-sb; xy+=u*v;xx+=u*u;yy+=v*v;} return xy/Math.sqrt(xx*yy); }
function drawQual(){
  const r=pearson(D.yld,D.obs); $("#qualTitle").textContent=`Predicted against observed 2008 yield, r = ${r.toFixed(2)}`;
  const w=900,h=440,m={l:56,r:16,t:12,b:44}; const xs=scale(XR[0],XR[1],m.l,w-m.r), ys=scale(YR[0],YR[1],h-m.b,m.t);
  let s=frame(w,h,m,xs,ys,"predicted yield, bu/ac (deviation)","observed 2008 yield, bu/ac (deviation)");
  const pts=[]; for(let i=0;i<N;i++) if(!advanced[i]) pts.push(i); for(let i=0;i<N;i++) if(advanced[i]) pts.push(i);
  pts.forEach(i=>{ s+=`<circle data-i="${i}" cx="${xs(Math.max(XR[0],Math.min(XR[1],D.yld[i])))}" cy="${ys(Math.max(YR[0],Math.min(YR[1],D.obs[i])))}" r="${advanced[i]?3.2:2.4}" fill="${advanced[i]?"var(--blue)":"var(--ctx)"}" fill-opacity="${advanced[i]?.75:.5}"/>`; });
  const ma=[0,0],mb=[0,0]; for(let i=0;i<N;i++){ if(advanced[i]){ma[0]+=D.yld[i];ma[1]+=D.obs[i];} else {mb[0]+=D.yld[i];mb[1]+=D.obs[i];} }
  const ka=S.K, kb=N-S.K; ma[0]/=ka;ma[1]/=ka;mb[0]/=kb;mb[1]/=kb;
  s+=`<line x1="${m.l}" x2="${w-m.r}" y1="${ys(ma[1])}" y2="${ys(ma[1])}" stroke="var(--blue)" stroke-width="2"/><text x="${m.l+6}" y="${ys(ma[1])-7}" style="fill:var(--ink);font-weight:700">advanced set mean ${fmt(ma[1])}</text>`;
  s+=`<line x1="${m.l}" x2="${w-m.r}" y1="${ys(mb[1])}" y2="${ys(mb[1])}" stroke="var(--muted)" stroke-width="2"/><text x="${m.l+6}" y="${ys(mb[1])+15}" style="fill:var(--ink)">rest mean ${fmt(mb[1])}</text>`;
  s+="</svg>"; const el=$("#qualChart"); el.innerHTML=s;
  el.addEventListener("mousemove", e=>{ const c=e.target.closest("circle"); if(!c) return hideTT(); const i=+c.dataset.i; showTT(e,`<b>${D.id[i]}</b> (${D.pop[i]})<br>rank ${rankOf[i]}${advanced[i]?", advanced":""}<br>predicted ${fmt(D.yld[i])}, observed ${fmt(D.obs[i])} bu/ac`); });
  el.addEventListener("mouseleave", hideTT);
}
function drawCurve(){
  const C=CURVE; const fr=[0,...C.frac], gain=[1.7,...C.gain], rr=[0.13,...C.r], plots=[0,...C.plots];
  const mk=(id,ys0,ys1,vals,yl,ref)=>{ const w=440,h=300,m={l:52,r:16,t:16,b:44}; const xs=scale(0,80,m.l,w-m.r), ys=scale(ys0,ys1,h-m.b,m.t);
    let s=frame(w,h,m,xs,ys,"share of each family phenotyped, %",yl,v=>v,v=>ref?v.toFixed(0):v.toFixed(1));
    if(ref){ s+=`<line x1="${m.l}" x2="${w-m.r}" y1="${ys(C.gain_max)}" y2="${ys(C.gain_max)}" stroke="var(--muted)" stroke-dasharray="4 3"/><text x="${w-m.r-4}" y="${ys(C.gain_max)-5}" text-anchor="end">perfect foresight ${fmt(C.gain_max,1)}</text>`; }
    const path=fr.map((f,i)=>`${i?"L":"M"}${xs(f*100)},${ys(vals[i])}`).join(""); s+=`<path d="${path}" fill="none" stroke="var(--blue)" stroke-width="2.5" stroke-linejoin="round"/>`;
    fr.forEach((f,i)=>{ s+=`<circle data-i="${i}" cx="${xs(f*100)}" cy="${ys(vals[i])}" r="5" fill="var(--blue)" stroke="var(--card)" stroke-width="2"/>`; });
    const j=1; s+=`<text x="${xs(fr[j]*100)+8}" y="${ys(vals[j])-10}" style="fill:var(--ink);font-weight:700">10%: ${ref?fmt(vals[j],1)+" bu/ac":"r "+vals[j].toFixed(2)}</text>`;
    s+="</svg>"; const el=$(id); el.innerHTML=s;
    el.querySelectorAll("circle").forEach(c=>{ const i=+c.dataset.i; c.addEventListener("mousemove",e=>showTT(e,`<b>${Math.round(fr[i]*100)}% of each family</b> (${plots[i].toLocaleString()} plots)<br>r ${rr[i].toFixed(2)}, realised gain ${fmt(gain[i],1)} bu/ac`)); c.addEventListener("mouseleave",hideTT); });
  };
  mk("#curveGain",0,14,gain,"realised 2008 gain, bu/ac (top 20% advanced)",true);
  mk("#curveR",0,0.5,rr,"accuracy, r with observed 2008 yield",false);
}
render();
</script>
</body>
</html>
"""
OUT.write_text(HTML.replace("__DATA__", data_js).replace("__CURVE__", curve_js), encoding="utf-8")
print(OUT, f"{OUT.stat().st_size/1e6:.2f} MB")
