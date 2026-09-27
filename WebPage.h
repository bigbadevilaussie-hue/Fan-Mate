#ifndef WEB_PAGE_H
#define WEB_PAGE_H

#include <Arduino.h>

const char INDEX_HTML[] PROGMEM = R"HTMLPAGE(<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>Fan-Mate</title>
<style>
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: #eef1f7;
  color: #1e1e2e;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
}
.wrap {
  max-width: 420px;
  margin: 0 auto;
  padding: 16px 18px 24px;
}
.title {
  text-align: center;
  font-size: 26px;
  font-weight: bold;
  color: #1e66f5;
  margin: 4px 0 2px;
}
.status {
  text-align: center;
  font-size: 12px;
  font-style: italic;
  color: #7a8194;
  margin-bottom: 14px;
  min-height: 16px;
}
.status.turbo {
  font-size: 15px;
  font-weight: bold;
  font-style: normal;
  color: #2f9e44;
}
.card {
  background: #ffffff;
  border: 1px solid #d8dde8;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  text-align: center;
}
.card.split {
  display: flex;
  padding: 0;
}
.col {
  flex: 1;
  padding: 14px 8px;
}
.col + .col {
  border-left: 1px solid #d8dde8;
}
.lbl {
  font-size: 10px;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #7a8194;
  margin-bottom: 4px;
}
.val {
  font-size: 22px;
  font-weight: bold;
  color: #1e1e2e;
}
.val.big { font-size: 34px; }
.val.muted { color: #7a8194; }
.val.green { color: #2f9e44; }
.val.blue  { color: #1e66f5; }
.val.yellow { color: #d99a00; }
.val.orange { color: #e8590c; }
.val.red   { color: #d20f39; }
.sub {
  font-size: 12px;
  color: #7a8194;
  margin-top: 4px;
}
.graph-label {
  font-size: 11px;
  font-weight: bold;
  color: #7a8194;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.graph-value {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
canvas {
  display: block;
  width: 100%;
  height: 110px;
}
.footer {
  text-align: center;
  font-size: 10px;
  color: #7a8194;
  margin-top: 20px;
}
.disconnected { opacity: 0.45; }
</style>
</head>
<body>
<div class="wrap">
  <div class="title">🌀 Fan-Mate</div>
  <div class="status" id="status">connecting…</div>

  <div class="card">
    <div class="lbl">📍 Atkinsons Dam</div>
    <div class="val big" id="outdoor-temp">--.-°</div>
  </div>

  <div class="card">
    <div class="lbl">🌡️ Phone Temperature</div>
    <div class="val big" id="temp">--.-°C</div>
  </div>

  <div class="card split">
    <div class="col">
      <div class="lbl">💨 Fan</div>
      <div class="val" id="fan">--</div>
    </div>
    <div class="col">
      <div class="lbl">⚙️ RPM</div>
      <div class="val" id="rpm">--</div>
    </div>
  </div>

  <div class="card split">
    <div class="col">
      <div class="lbl">📱 Phone</div>
      <div class="val" id="phone">--</div>
    </div>
    <div class="col">
      <div class="lbl">📊 Status</div>
      <div class="val" id="alert">None</div>
    </div>
  </div>

  <div class="card">
    <div class="val" id="clock">--:-- --</div>
  </div>

  <div class="card">
    <div class="graph-label">📥 Network Rate</div>
    <div class="graph-value" id="rate">-- KB/s</div>
    <canvas id="net-graph" width="800" height="200"></canvas>
  </div>

  <div class="card">
    <div class="graph-label">📈 Temperature History</div>
    <canvas id="temp-graph" width="800" height="200"></canvas>
  </div>

  <div class="footer">HTTP · Live view · <span id="fw">v?</span></div>
</div>

<script>
const HIST_LEN = 60;
let tempHist = new Array(HIST_LEN).fill(null);
let netHist  = new Array(HIST_LEN).fill(null);
let threshold = 700;
let tempWarning = 32.0;
let everConnected = false;

function emojiFor(t) {
  if (t === null || t === undefined) return '❔';
  if (t < 30) return '🙂';
  if (t < 33) return '🌡️';
  if (t < 36) return '🥵';
  return '🔥';
}
function fanEmoji(p) {
  if (p === 0) return '💤';
  if (p < 30) return '🍃';
  if (p < 70) return '💨';
  return '🌪️';
}
function clockEmoji() {
  const h = new Date().getHours();
  if (h < 5)  return '🌙';
  if (h < 7)  return '🌅';
  if (h < 10) return '🌄';
  if (h < 12) return '☀️';
  if (h < 14) return '🌞';
  if (h < 17) return '🌤️';
  if (h < 19) return '🌇';
  if (h < 21) return '🌆';
  return '🌙';
}
function fmtTime() {
  const n = new Date();
  let h = n.getHours() % 12 || 12;
  const m = n.getMinutes().toString().padStart(2, '0');
  const ampm = n.getHours() < 12 ? 'AM' : 'PM';
  return h + ':' + m + ' ' + ampm + ' ' + clockEmoji();
}
function tempColor(t) {
  if (t < 25) return 'green';
  if (t < 35) return 'blue';
  if (t < 45) return 'yellow';
  return 'red';
}

function drawGraph(canvasId, data, yMin, yMax, lineColor, fillColor, threshold, xLabels) {
  const c = document.getElementById(canvasId);
  const ctx = c.getContext('2d');
  const W = c.width, H = c.height;
  const padL = 60, padR = 34, padT = 14, padB = 20;
  const pw = W - padL - padR;
  const ph = H - padT - padB;

  ctx.clearRect(0, 0, W, H);
  ctx.font = '20px -apple-system, sans-serif';
  ctx.fillStyle = '#7a8194';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'right';

  ctx.strokeStyle = '#e6e9f0';
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i++) {
    const frac = i / 3;
    const y = padT + frac * ph;
    const v = yMax - frac * (yMax - yMin);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(W - padR, y);
    ctx.stroke();
    ctx.fillText(Math.round(v), padL - 6, y);
  }

  if (threshold !== null && threshold >= yMin && threshold <= yMax) {
    const ty = padT + ph - ((threshold - yMin) / (yMax - yMin)) * ph;
    ctx.strokeStyle = '#d20f39';
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(padL, ty);
    ctx.lineTo(W - padR, ty);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#d20f39';
    ctx.textAlign = 'left';
    ctx.fillText(Math.round(threshold), W - padR + 3, ty);
    ctx.fillStyle = '#7a8194';
    ctx.textAlign = 'right';
  }

  const pts = [];
  const n = data.length;
  for (let i = 0; i < n; i++) {
    const v = data[i];
    if (v === null || v === undefined) continue;
    const x = padL + (i / Math.max(1, n - 1)) * pw;
    const y = padT + ph - ((v - yMin) / (yMax - yMin)) * ph;
    pts.push([x, y]);
  }
  if (pts.length >= 2) {
    ctx.beginPath();
    ctx.moveTo(pts[0][0], padT + ph);
    for (const p of pts) ctx.lineTo(p[0], p[1]);
    ctx.lineTo(pts[pts.length - 1][0], padT + ph);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.strokeStyle = lineColor;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.stroke();
  }

  ctx.fillStyle = '#7a8194';
  ctx.textBaseline = 'top';
  ctx.textAlign = 'left';
  ctx.fillText(xLabels[0], padL, H - padB + 4);
  ctx.textAlign = 'center';
  ctx.fillText(xLabels[1], padL + pw / 2, H - padB + 4);
  ctx.textAlign = 'right';
  ctx.fillText(xLabels[2], W - padR, H - padB + 4);
}
function render(data) {
  const el = id => document.getElementById(id);

  const boost = data.boost || 0;
  const sleep = data.sleep || 0;
  const opal = data.opal !== undefined ? data.opal : 1;
  const statusEl = el('status');
  if (sleep) {
    statusEl.textContent = '💤 sleeping';
    statusEl.className = 'status';
  } else if (boost) {
    statusEl.textContent = '🏎️ TURBO';
    statusEl.className = 'status turbo';
  } else if (!opal) {
    statusEl.textContent = '🔌 opal offline';
    statusEl.className = 'status';
  } else {
    statusEl.textContent = 'connected';
    statusEl.className = 'status';
  }

  if (data.outdoor_c !== undefined && data.outdoor_c > -90) {
    el('outdoor-temp').textContent = data.outdoor_c.toFixed(1) + '°';
  }

  const temp = data.temp;
  if (temp !== null && temp !== undefined) {
    el('temp').textContent = temp.toFixed(1) + '°C  ' + emojiFor(temp);
    el('temp').className = 'val big ' + tempColor(temp);
  }

  const fan = data.fan || 0;
  el('fan').textContent = fan === 0 ? 'OFF ' + fanEmoji(0) : fan + '% ' + fanEmoji(fan);
  el('fan').className = 'val ' + (fan === 0 ? 'muted' : 'green');

  const rpm = data.rpm || 0;
  el('rpm').textContent = rpm;
  el('rpm').className = 'val ' + (rpm > 0 ? 'green' : 'muted');

  el('phone').textContent = data.phone ? 'YES 📱' : 'NO  📴';
  el('phone').className = 'val ' + (data.phone ? 'green' : 'muted');

  const alert = data.alert || 0;
  const stall = data.fan_stall || 0;
  let alertText = 'None';
  let alertCls = 'val muted';
  if (stall) { alertText = 'FAN STALL 🚨'; alertCls = 'val red'; }
  else if (alert >= 3) { alertText = 'Kill 💀'; alertCls = 'val red'; }
  else if (alert === 2) { alertText = 'Oh Shit 🚨'; alertCls = 'val red'; }
  else if (alert === 1) { alertText = 'Warn ⚠️'; alertCls = 'val orange'; }
  else if (boost) { alertText = '🏎️ Boosting'; alertCls = 'val green'; }
  el('alert').textContent = alertText;
  el('alert').className = alertCls;

  el('clock').textContent = fmtTime();

  const rate = data.net_kbps || 0;
  el('rate').textContent = rate >= 1024 ? (rate / 1024).toFixed(2) + ' MB/s' : rate.toFixed(1) + ' KB/s';

  if (data.temp_hist && Array.isArray(data.temp_hist)) tempHist = data.temp_hist;
  if (data.net_hist && Array.isArray(data.net_hist)) netHist = data.net_hist;

  if (data.temp_warning) tempWarning = data.temp_warning;
  if (data.boost_threshold) threshold = data.boost_threshold;

  drawGraph('net-graph', netHist, 0, 2048, '#1e66f5', '#cfe0ff', threshold, ['-15m', '-7m', 'now']);
  drawGraph('temp-graph', tempHist, 15, 45, '#1e66f5', '#cfe0ff', tempWarning, ['-15m', '-7m', 'now']);

  el('fw').textContent = 'v' + (data.fw || '?');
}

async function tick() {
  try {
    const r = await fetch('/status', { cache: 'no-store' });
    if (!r.ok) throw new Error('http ' + r.status);
    const d = await r.json();
    everConnected = true;
    document.querySelector('.wrap').classList.remove('disconnected');
    render(d);
  } catch (e) {
    document.getElementById('status').textContent = 'disconnected';
    if (everConnected) document.querySelector('.wrap').classList.add('disconnected');
  }
}

tick();
setInterval(tick, 5000);
</script>
</body>
</html>
)HTMLPAGE";

#endif
