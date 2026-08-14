# Gantt generátor — referenční kód (styl „roadmap")

Odladěné šablony pro generování PowerPoint roadmapy z Planner exportu.
Uprav data (`phaseInfo`, `phaseSplit`) podle konkrétního projektu.

## Krok 1 — Parsování Planner exportu do JSON (Python, OUTSIDE Tasku)

```python
import openpyxl, json, re
from datetime import datetime

SRC = "input/<EXPORT>.xlsx"          # najdi přes Glob input/**/*.xlsx
ws = openpyxl.load_workbook(SRC, data_only=True).worksheets[0]

def euf(v):  return v.strftime('%d.%m.%Y') if isinstance(v, datetime) else str(v)
def dnum(v): m = re.search(r'(\d+)', str(v or '')); return int(m.group(1)) if m else 0

meta = dict(name=ws['B1'].value, owner=ws['B2'].value,
            exported=euf(ws['B7'].value), pstart=euf(ws['B3'].value), pfinish=euf(ws['B4'].value))
tasks = []
for r in range(10, ws.max_row + 1):
    o = ws.cell(r, 2).value; nm = ws.cell(r, 3).value
    s = ws.cell(r, 5).value; f = ws.cell(r, 6).value
    if o is None or nm is None or not isinstance(s, datetime) or not isinstance(f, datetime):
        continue
    tasks.append(dict(
        wbs=str(o), name=str(nm),
        startEU=s.strftime('%d.%m.%Y'), finishEU=f.strftime('%d.%m.%Y'),
        sy=s.year, sm=s.month, sd=s.day, fy=f.year, fm=f.month, fd=f.day,
        dur=dnum(ws.cell(r, 7).value),
        pct=float(ws.cell(r, 9).value or 0), prio=str(ws.cell(r, 10).value or 'Medium'),
        milestone=str(ws.cell(r, 17).value or '').strip().lower() in ('yes', 'ano', 'true'),
        notes=str(ws.cell(r, 18).value or ''), level=str(o).count('.') + 1))
json.dump(dict(meta=meta, tasks=tasks), open('working/gantt_data.json', 'w'), ensure_ascii=False, indent=1)
```

Pozn.: data v E/F jsou `datetime` (NE string) — proto `isinstance(... datetime)`.

## Krok 2 — Generátor PowerPointu (Node / pptxgenjs)

Kompletní odladěný skript níže. Načítá `working/gantt_data.json` a vytvoří:
- **Slide 1** = celkový roadmap (úrovně 1–2, barva pruhu dle stavu plnění),
- **Slide 2** = přehledové karty fází,
- pro každou fázi **popisný slide** + **2 detailní slidy** (roadmap styl,
  barvy pruhů dle typu kroku, plná/světlá výplň dle plnění).

`renderRoadmap(opts)` umí oba režimy: `mode:'overview'` (status barvy) a
`mode:'detail'` (barvy kroků + progress). Pole `phaseInfo` (popisy etap) a
`phaseSplit` (rozdělení etap na 2 slidy) napln dle projektu; popisy GROUNDUJ.

```javascript
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const data = JSON.parse(fs.readFileSync("working/gantt_data.json", "utf8"));
const allTasks = data.tasks;
const meta = data.meta;

// ---------- palette ----------
const C = {
  navy: "0B3D91", title: "0B3D91", ink: "1F2A44",
  yearBand: "1F3864", monthBand: "8EA9DB", phaseRow: "D9E1F2",
  subDone: "2E7D32", subRem: "BDD7EE", phDone: "1B5E20", phRem: "5B9BD5",
  grid: "D9D9D9", gridLine: "C9C9C9", txt: "404040", gray: "595959",
  today: "C00000", card: "F2F5FB", cardLn: "D6E0F2",
  summaryBar: "B7C0CC",   // neutral grey for L2 summary bars in detail
};
const PRIO = { High: "C00000", Medium: "FFC000", Low: "548235" };
const PRIO_CZ = { High: "Vysoká", Medium: "Střední", Low: "Nízká" };

// stage colours (level 3) — distinct hues, one fixed colour per task type
const STAGE = [
  { test: /brq/i,                 color: "1AA39A", label: "BRQ" },    // teal
  { test: /(^|\b)tc(\b|$)/i,      color: "2E74B5", label: "TC" },     // blue
  { test: /hld/i,                 color: "7E5AA8", label: "HLD" },    // purple
  { test: /dev/i,                 color: "5B6B7B", label: "DEV" },    // slate grey
  { test: /test/i,                color: "E8A33D", label: "TEST" },   // amber
  { test: /golive|go live|gl\b/i, color: "3FA45B", label: "GoLive" }, // green
];
const STAGE_OTHER = "8696A7"; // steel grey for non-standard steps (e.g. HyperV)
function stageColor(name) {
  for (const s of STAGE) if (s.test.test(name)) return s.color;
  return STAGE_OTHER;
}
function hasOther(tasks) {
  return tasks.some(t => t.level === 3 && stageColor(t.name) === STAGE_OTHER);
}
function lighten(hex, f) {
  const r = parseInt(hex.slice(0, 2), 16), g = parseInt(hex.slice(2, 4), 16), b = parseInt(hex.slice(4, 6), 16);
  const m = v => Math.round(v + (255 - v) * f).toString(16).padStart(2, "0");
  return m(r) + m(g) + m(b);
}

// ---------- helpers ----------
const mkey = (y, m) => y * 12 + (m - 1);
const ROM = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"];

const pres = new pptxgen();
pres.defineLayout({ name: "W", width: 13.333, height: 7.5 });
pres.layout = "W";
const SW = 13.333;

function timelineRange(tasks) {
  let lo = Infinity, hi = -Infinity;
  tasks.forEach(t => { lo = Math.min(lo, mkey(t.sy, t.sm)); hi = Math.max(hi, mkey(t.fy, t.fm)); });
  const months = [];
  for (let k = lo; k <= hi; k++) months.push({ y: Math.floor(k / 12), m: (k % 12) + 1 });
  return { lo, hi, months, n: hi - lo + 1 };
}

function chip(slide, x, y, label, color, w = 1.15) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h: 0.28, rectRadius: 0.06, fill: { color }, line: { type: "none" } });
  slide.addText(label, { x, y, w, h: 0.28, fontFace: "Calibri", fontSize: 10, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
}

function todayLine(slide, TLX, mw, lo, n, top, bottom) {
  const td = new Date();
  const tk = mkey(td.getFullYear(), td.getMonth() + 1) - lo;
  if (tk < 0 || tk >= n) return;
  const x = TLX + (tk + (td.getDate() - 1) / 30) * mw;
  slide.addShape(pres.ShapeType.line, { x, y: top, w: 0, h: bottom - top, line: { color: C.today, width: 1.25, dashType: "dash" } });
  slide.addText("dnes", { x: x - 0.3, y: bottom, w: 0.6, h: 0.18, fontFace: "Calibri", fontSize: 7, bold: true, color: C.today, align: "center", margin: 0 });
}

// ============================================================
//  GANTT renderer
//   mode 'overview'  -> levels 1 & 2, progress bars, priority dots, % column
//   mode 'detail'    -> levels 2 & 3 (no phase row), stage-coloured bars
//   opts.range       -> optional fixed {lo,months,n} so split slides share an axis
// ============================================================
function renderGantt(opts) {
  const sl = pres.addSlide();
  sl.background = { color: "FFFFFF" };
  const tasks = opts.tasks;
  const { lo, months, n } = opts.range || timelineRange(tasks);

  sl.addText(opts.title, { x: 0.28, y: 0.16, w: 12.7, h: 0.46, fontFace: "Calibri", fontSize: 22, bold: true, color: C.title });
  sl.addText(opts.subtitle, { x: 0.3, y: 0.62, w: 12.7, h: 0.26, fontFace: "Calibri", fontSize: 10, italic: true, color: "808080" });

  const LX = 0.28, WBSX = 0.46, NAMEX = 0.92;
  const NAMEW = opts.mode === "detail" ? 2.25 : 1.95;
  const PCTX = NAMEX + NAMEW + 0.04, PCTW = 0.46;
  const showPct = opts.mode === "overview";
  const showPrio = opts.mode === "overview";
  const leftEnd = showPct ? PCTX + PCTW : NAMEX + NAMEW;
  const TLX = leftEnd + 0.12;
  const TLW = SW - TLX - 0.18;
  const mw = TLW / n;

  const HEADY = 1.0, HBAND = 0.2;
  const ROWY = HEADY + 2 * HBAND;
  const MAXBOTTOM = 7.0;
  const rowH = Math.min(0.30, (MAXBOTTOM - ROWY) / tasks.length);
  const contentBottom = ROWY + tasks.length * rowH;
  const barH = Math.min(0.17, rowH * 0.6);

  const white = { fontFace: "Calibri", color: "FFFFFF", align: "center", valign: "middle", margin: 1 };
  sl.addText(opts.mode === "detail" ? "Úkol" : "Priorita úkolu", { ...white, x: LX - 0.04, y: HEADY, w: leftEnd - LX + 0.04, h: 2 * HBAND, fontSize: 9, bold: true, fill: { color: C.yearBand } });

  let i = 0;
  while (i < n) {
    let j = i;
    while (j + 1 < n && months[j + 1].y === months[i].y) j++;
    const x = TLX + i * mw, w = (j - i + 1) * mw;
    sl.addText(String(months[i].y), { ...white, x, y: HEADY, w, h: HBAND, fontSize: 10, bold: true, fill: { color: C.yearBand }, line: { color: "FFFFFF", width: 0.5 } });
    i = j + 1;
  }
  months.forEach((mo, idx) => {
    sl.addText(ROM[mo.m - 1], { ...white, x: TLX + idx * mw, y: HEADY + HBAND, w: mw, h: HBAND, fontSize: 6, fill: { color: C.monthBand }, line: { color: "FFFFFF", width: 0.3 } });
  });
  months.forEach((mo, idx) => {
    if (mo.m === 1) sl.addShape(pres.ShapeType.line, { x: TLX + idx * mw, y: ROWY, w: 0, h: contentBottom - ROWY, line: { color: C.gridLine, width: 1, dashType: "dash" } });
  });

  tasks.forEach((t, r) => {
    const y = ROWY + r * rowH;
    const isPhase = t.level === 1;
    const isSub = t.level === 2;
    const indent = "  ".repeat(Math.max(0, t.level - (opts.mode === "detail" ? 2 : 1)));

    if (isPhase || (opts.mode === "detail" && isSub)) {
      sl.addShape(pres.ShapeType.rect, { x: LX - 0.06, y, w: leftEnd - LX + 0.06, h: rowH, fill: { color: isPhase ? C.phaseRow : "EDF1F7" }, line: { type: "none" } });
    }
    if (showPrio) {
      sl.addShape(pres.ShapeType.ellipse, { x: LX, y: y + rowH / 2 - 0.06, w: 0.12, h: 0.12, fill: { color: PRIO[t.prio] || PRIO.Medium }, line: { type: "none" } });
    }
    const wbsFs = opts.mode === "detail" ? 7 : 8;
    sl.addText(t.wbs, { x: showPrio ? WBSX : LX + 0.04, y, w: NAMEX - (showPrio ? WBSX : LX), h: rowH, fontFace: "Calibri", fontSize: wbsFs, bold: isPhase || (opts.mode === "detail" && isSub), color: C.txt, align: "left", valign: "middle", margin: 0 });
    const nameFs = opts.mode === "detail" ? (isSub ? 8.5 : 7.5) : (isPhase ? 8.5 : 8);
    let nameLabel = indent + t.name;
    if (opts.mode === "detail" && isSub) nameLabel += `   —   ${Math.round(t.pct * 100)} %`;
    sl.addText(nameLabel, { x: NAMEX, y, w: NAMEW, h: rowH, fontFace: "Calibri", fontSize: nameFs, bold: isPhase || (opts.mode === "detail" && isSub), color: isPhase ? C.navy : (isSub && opts.mode === "detail" ? C.ink : C.txt), align: "left", valign: "middle", margin: 0 });

    if (showPct) {
      sl.addText(Math.round(t.pct * 100) + "%", { x: PCTX, y, w: PCTW, h: rowH, fontFace: "Calibri", fontSize: 8, bold: isPhase, color: t.pct >= 0.5 ? C.subDone : C.txt, align: "center", valign: "middle", margin: 0 });
    }

    const sIdx = mkey(t.sy, t.sm) - lo;
    const fIdx = mkey(t.fy, t.fm) - lo;
    const span = fIdx - sIdx + 1;
    const bx = TLX + sIdx * mw, bw = span * mw, by = y + rowH / 2 - barH / 2;

    if (opts.mode === "overview") {
      const done = Math.round(t.pct * span);
      const remFill = isPhase ? C.phRem : C.subRem;
      const doneFill = isPhase ? C.phDone : C.subDone;
      sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw, h: barH, rectRadius: 0.03, fill: { color: remFill }, line: { color: "FFFFFF", width: 0.5 } });
      if (done > 0) sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: done * mw, h: barH, rectRadius: 0.03, fill: { color: doneFill }, line: { type: "none" } });
    } else {
      const pct = Math.min(1, Math.max(0, t.pct));
      if (isSub) {
        const thin = Math.min(barH, 0.11);
        sl.addShape(pres.ShapeType.rect, { x: bx, y: y + rowH / 2 - thin / 2, w: bw, h: thin, fill: { color: C.summaryBar }, line: { type: "none" } });
        if (pct > 0) sl.addShape(pres.ShapeType.rect, { x: bx, y: y + rowH / 2 - thin / 2, w: bw * pct, h: thin, fill: { color: C.subDone }, line: { type: "none" } });
      } else {
        const col = stageColor(t.name);
        sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw, h: barH, rectRadius: 0.02, fill: { color: lighten(col, 0.62) }, line: { color: "FFFFFF", width: 0.4 } });
        if (pct > 0) sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw * pct, h: barH, rectRadius: 0.02, fill: { color: col }, line: { type: "none" } });
      }
    }
  });

  todayLine(sl, TLX, mw, lo, n, ROWY, contentBottom);

  // legend
  const ly = 7.12;
  let lx = 0.3;
  function leg(color, label, shape) {
    sl.addShape(shape || pres.ShapeType.rect, { x: lx, y: ly, w: 0.16, h: 0.13, fill: { color }, line: { type: "none" } });
    sl.addText(label, { x: lx + 0.2, y: ly - 0.03, w: 2.2, h: 0.2, fontFace: "Calibri", fontSize: 8.5, color: C.txt, valign: "middle", margin: 0 });
    lx += 0.2 + 0.1 + label.length * 0.05 + 0.2;
  }
  if (opts.mode === "overview") {
    leg(C.subDone, "Dokončeno"); leg(C.subRem, "Zbývá");
    leg(PRIO.High, "Vysoká", pres.ShapeType.ellipse); leg(PRIO.Medium, "Střední", pres.ShapeType.ellipse); leg(PRIO.Low, "Nízká", pres.ShapeType.ellipse);
  } else {
    STAGE.forEach(s => leg(s.color, s.label));
    if (hasOther(tasks)) leg(STAGE_OTHER, "ostatní");
  }
  sl.addText("- - - dnes", { x: lx, y: ly - 0.03, w: 1.5, h: 0.2, fontFace: "Calibri", fontSize: 8.5, color: C.today, bold: true, valign: "middle", margin: 0 });
  return sl;
}

// ============================================================
//  ROADMAP renderer — styled overall Gantt (reference look)
// ============================================================
function renderRoadmap(opts) {
  const sl = pres.addSlide();
  sl.background = { color: "FFFFFF" };
  const tasks = opts.tasks;
  const detail = (opts.mode === "detail");
  const { lo, months, n } = opts.range || timelineRange(tasks);

  const NAMEX = 0.55, NAMEW = 2.7;
  const TLX = 3.4, TLW = SW - TLX - 1.15, mw = TLW / n;
  const BANDEND = TLX + n * mw;
  const FLAGY = 0.14, YEARY = 0.66, QY = 0.86, HBAND = 0.2;
  const HEADBOT = QY + HBAND;
  const ROWY = 1.42, ROWBOT = 7.0;
  const rowH = Math.min(0.34, (ROWBOT - ROWY) / tasks.length);
  const contentBottom = ROWY + tasks.length * rowH;
  const barH = Math.min(0.19, rowH * 0.6);

  const DONE = "3FA45B", PROG = "F0A92E", TODO = "3E7CB1";
  const headNavy = "1F3864", qNavy = "3A5A92", orange = "E8730C", purple = "6B4FA0", flagG = "4CA64C";
  const statusColor = p => (p >= 1 ? DONE : p > 0 ? PROG : TODO);
  const frac = (y, m, d) => (mkey(y, m) - lo) + (d - 1) / 30;

  // title block (left column)
  sl.addText(opts.title, { x: 0.4, y: 0.12, w: 2.92, h: 0.4, fontFace: "Calibri", fontSize: detail ? 15 : 17, bold: true, color: C.navy, valign: "middle", margin: 0 });
  if (opts.subtitle) sl.addText(opts.subtitle, { x: 0.4, y: 0.52, w: 2.92, h: 0.46, fontFace: "Calibri", fontSize: 9, italic: true, color: "808080", valign: "top", margin: 0 });
  if (opts.note) sl.addText(opts.note, { x: 0.4, y: 1.0, w: 2.92, h: 0.34, fontFace: "Calibri", fontSize: 8, color: "9A9A9A", valign: "top", margin: 0 });

  // year band
  let i = 0;
  while (i < n) {
    let j = i; while (j + 1 < n && months[j + 1].y === months[i].y) j++;
    const x = TLX + i * mw, w = (j - i + 1) * mw;
    sl.addText(String(months[i].y), { x, y: YEARY, w, h: HBAND, fontFace: "Calibri", fontSize: 11, bold: true, color: "FFFFFF", fill: { color: headNavy }, align: "left", valign: "middle", margin: 6, line: { color: "FFFFFF", width: 0.5 } });
    i = j + 1;
  }
  // quarter band
  i = 0;
  while (i < n) {
    const q = Math.floor((months[i].m - 1) / 3) + 1; let j = i;
    while (j + 1 < n && months[j + 1].y === months[i].y && Math.floor((months[j + 1].m - 1) / 3) + 1 === q) j++;
    const x = TLX + i * mw, w = (j - i + 1) * mw;
    sl.addText("Q" + q, { x, y: QY, w, h: HBAND, fontFace: "Calibri", fontSize: 8.5, color: "FFFFFF", fill: { color: qNavy }, align: "left", valign: "middle", margin: 6, line: { color: "FFFFFF", width: 0.4 } });
    i = j + 1;
  }
  // big orange years (outside the band)
  sl.addText(String(months[0].y), { x: TLX - 1.12, y: YEARY - 0.05, w: 1.0, h: HEADBOT - YEARY + 0.1, fontFace: "Calibri", fontSize: 22, bold: true, color: orange, align: "right", valign: "middle", margin: 0 });
  sl.addText(String(months[n - 1].y), { x: BANDEND + 0.08, y: YEARY - 0.05, w: 1.0, h: HEADBOT - YEARY + 0.1, fontFace: "Calibri", fontSize: 22, bold: true, color: orange, align: "left", valign: "middle", margin: 0 });

  // milestone flags
  function flag(fx, label, date) {
    const x = TLX + fx * mw;
    if (x < TLX - 0.1 || x > BANDEND + 0.1) return;
    sl.addShape(pres.ShapeType.triangle, { x: x - 0.08, y: FLAGY + 0.24, w: 0.16, h: 0.14, rotate: 180, fill: { color: flagG }, line: { type: "none" } });
    const labelX = Math.min(Math.max(x - 1.0, 0.05), SW - 2.05);
    sl.addText([{ text: label, options: { bold: true } }, { text: "\n" + date, options: {} }], { x: labelX, y: FLAGY - 0.08, w: 2.0, h: 0.42, fontFace: "Calibri", fontSize: 8.5, color: "404040", align: "center", valign: "middle", margin: 0 });
  }
  (opts.flags || []).forEach(f => flag(frac(f.y, f.m, f.d), f.label, f.date));

  // rows
  tasks.forEach((t, r) => {
    const y = ROWY + r * rowH;
    const isPhase = t.level === 1;
    const isSub = t.level === 2;
    const bandRow = (!detail && isPhase) || (detail && isSub);
    if (bandRow) sl.addShape(pres.ShapeType.rect, { x: 0.42, y, w: SW - 0.6, h: rowH, fill: { color: "F1F4F9" }, line: { type: "none" } });

    const indent = detail ? (isSub ? "" : "   ") : (isPhase ? "" : "   ");
    const nmBold = (!detail && isPhase) || (detail && isSub);
    sl.addText(indent + t.name, { x: NAMEX, y, w: NAMEW, h: rowH, fontFace: "Calibri", fontSize: nmBold ? 9 : 8.3, bold: nmBold, color: nmBold ? C.navy : C.txt, align: "left", valign: "middle", margin: 0 });

    const bx = TLX + frac(t.sy, t.sm, t.sd) * mw;
    const bex = TLX + (frac(t.fy, t.fm, t.fd) + 1 / 30) * mw;
    const bw = Math.max(0.14, bex - bx);
    const by = y + rowH / 2 - barH / 2;
    const pct = Math.min(1, Math.max(0, t.pct));

    if (bx - 0.55 > NAMEX + NAMEW + 0.1) sl.addShape(pres.ShapeType.line, { x: NAMEX + NAMEW + 0.1, y: y + rowH / 2, w: (bx - 0.55) - (NAMEX + NAMEW + 0.1), h: 0, line: { color: "D2D2D2", width: 0.75, dashType: "sysDot" } });
    sl.addText(Math.round(pct * 100) + " %", { x: bx - 0.56, y, w: 0.5, h: rowH, fontFace: "Calibri", fontSize: 8, color: "8A8A8A", align: "right", valign: "middle", margin: 0 });

    if (!detail) {
      sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw, h: barH, rectRadius: 0.04, fill: { color: statusColor(pct) }, line: { type: "none" } });
      if (bw > 0.5) sl.addText(t.dur + " d", { x: bx, y: by, w: bw, h: barH, fontFace: "Calibri", fontSize: 8, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    } else if (isSub) {
      const thin = Math.min(barH, 0.11);
      sl.addShape(pres.ShapeType.rect, { x: bx, y: y + rowH / 2 - thin / 2, w: bw, h: thin, fill: { color: C.summaryBar }, line: { type: "none" } });
      if (pct > 0) sl.addShape(pres.ShapeType.rect, { x: bx, y: y + rowH / 2 - thin / 2, w: bw * pct, h: thin, fill: { color: C.subDone }, line: { type: "none" } });
    } else {
      const col = stageColor(t.name);
      sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw, h: barH, rectRadius: 0.03, fill: { color: lighten(col, 0.62) }, line: { color: "FFFFFF", width: 0.4 } });
      if (pct > 0) sl.addShape(pres.ShapeType.roundRect, { x: bx, y: by, w: bw * pct, h: barH, rectRadius: 0.03, fill: { color: col }, line: { type: "none" } });
    }

    if (!(detail && isSub) && bex + 0.12 + 1.45 <= SW - 0.05) sl.addText(`${t.startEU} – ${t.finishEU}`, { x: bex + 0.12, y, w: 1.7, h: rowH, fontFace: "Calibri", fontSize: 7.3, color: "707070", align: "left", valign: "middle", margin: 0 });
  });

  // today marker
  const td = new Date();
  const tf = frac(td.getFullYear(), td.getMonth() + 1, td.getDate());
  if (tf >= 0 && tf <= n) {
    const tx = TLX + tf * mw;
    sl.addShape(pres.ShapeType.line, { x: TLX, y: HEADBOT + 0.015, w: tx - TLX, h: 0, line: { color: C.today, width: 2.25 } });
    sl.addShape(pres.ShapeType.triangle, { x: tx - 0.07, y: HEADBOT + 0.03, w: 0.14, h: 0.12, fill: { color: C.today }, line: { type: "none" } });
    sl.addShape(pres.ShapeType.line, { x: tx, y: ROWY, w: 0, h: contentBottom - ROWY, line: { color: C.today, width: 1, dashType: "dash" } });
    sl.addText("Dnes", { x: tx - 0.32, y: HEADBOT + 0.14, w: 0.64, h: 0.16, fontFace: "Calibri", fontSize: 7.5, bold: true, color: C.today, align: "center", margin: 0 });
  }

  // swim-lane label
  sl.addText(opts.swimLabel || "CyberArk", { x: -0.35, y: (ROWY + contentBottom) / 2 - 0.2, w: 1.6, h: 0.4, rotate: 270, fontFace: "Calibri", fontSize: 13, bold: true, color: purple, align: "center", valign: "middle", margin: 0 });

  // legend
  let lx = 0.4; const ly = 7.16;
  function leg(color, label, shape) {
    sl.addShape(shape || pres.ShapeType.rect, { x: lx, y: ly, w: 0.16, h: 0.13, fill: { color }, line: { type: "none" } });
    sl.addText(label, { x: lx + 0.2, y: ly - 0.03, w: 2.0, h: 0.2, fontFace: "Calibri", fontSize: 8.5, color: C.txt, valign: "middle", margin: 0 });
    lx += 0.2 + 0.1 + label.length * 0.05 + 0.22;
  }
  if (!detail) {
    leg(DONE, "Dokončeno"); leg(PROG, "Rozpracováno"); leg(TODO, "Nezahájeno");
    sl.addShape(pres.ShapeType.triangle, { x: lx, y: ly, w: 0.14, h: 0.13, fill: { color: flagG }, line: { type: "none" } });
    sl.addText("Milník", { x: lx + 0.2, y: ly - 0.03, w: 1.2, h: 0.2, fontFace: "Calibri", fontSize: 8.5, color: C.txt, valign: "middle", margin: 0 });
    lx += 0.2 + 0.1 + 6 * 0.05 + 0.22;
  } else {
    STAGE.forEach(s => leg(s.color, s.label));
    if (hasOther(tasks)) leg(STAGE_OTHER, "ostatní");
  }
  sl.addText("— — Dnes", { x: lx, y: ly - 0.03, w: 1.4, h: 0.2, fontFace: "Calibri", fontSize: 8.5, bold: true, color: C.today, valign: "middle", margin: 0 });
  return sl;
}

// ============================================================
//  PHASE descriptions (grounded in M365 docs + export)
// ============================================================
const phaseInfo = {
  "1": { accent: "1F3864", title: "Základní IT a bezpečnostní systémy",
    intro: "Zavedení privilegovaného přístupu (PAM) k základním IT a bezpečnostním systémům CETIN. Etapy běží paralelně — každá onboarduje do CyberArku jednu skupinu systémů.",
    items: [
      ["1.1", "SIEM & PKI", "Řízený privilegovaný přístup k SIEM (QRadar) a k PKI/HSM; napojení auditních logů CyberArku do SIEM."],
      ["1.2", "AD", "Onboarding privilegovaných účtů Active Directory; osobní privilegované účty řízené přes IDM a role."],
      ["1.3", "Core IP", "Klíčové síťové prvky — Cisco ACS/ISE, IP prvky Cisco a HPE IDN — pod správu PAM."],
      ["1.4", "KFA", "Konfigurační automaty — privilegovaný přístup a automatická rotace přihlašovacích údajů."],
      ["1.5", "DB", "Databáze (mj. Oracle) — řízený přístup přes PSM proxy a správa servisních účtů."],
      ["1.6", "GitLab CI/CD", "Bezpečné poskytování credentials do CI/CD pipeline (CP/CCP, Conjur secrets management)."],
      ["1.7", "HyperV DC", "Příprava a migrace datacentra (HW, instalace CBA, migrace JZM) pod správu PAM."],
    ] },
  "2": { accent: "1C7293", title: "Aplikační a identitní platformy",
    intro: "Rozšíření PAM na kontejnerovou platformu OpenShift a hlubší propojení s identitním systémem (IDM).",
    items: [
      ["2.1", "OpenShift prostředí", "Onboarding infrastruktury OpenShift; secrets management pro DevOps (Conjur, REST API)."],
      ["2.2", "OpenShift aplikace", "Napojení aplikací běžících v OpenShiftu na automatizované vyzvedávání credentials (M2M)."],
      ["2.3", "IDM", "Integrace IDM2PAM — automatizovaný životní cyklus privilegovaných účtů: provisioning, role, recertifikace."],
    ] },
  "3": { accent: "7A1F2B", title: "Telco a síťové technologie",
    intro: "Onboarding klíčových telco technologií do PAM napříč hlasovou, rádiovou a transportní vrstvou.",
    items: [
      ["3.1", "Voice", "Hlasové systémy — řízený privilegovaný přístup k prvkům hlasové platformy."],
      ["3.2", "RAN", "Radiová přístupová síť (RAN) — privilegovaný přístup k prvkům sítě pod správu PAM."],
      ["3.3", "WDM", "Optická transportní síť (WDM) — řízený přístup k transportním prvkům."],
    ] },
  "4": { accent: "2C5F2D", title: "Datacentrum a infrastruktura",
    intro: "Zavedení PAM napříč infrastrukturou datových center — od fyzické vrstvy po zálohování.",
    items: [
      ["4.1", "Fyzické servery", "Privilegovaný přístup k fyzickým serverům a jejich management/OOB rozhraním."],
      ["4.2", "Virtualizace", "Virtualizační platformy — správa a rotace privilegovaných účtů."],
      ["4.3", "Storage", "Disková pole a úložiště — řízený privilegovaný přístup."],
      ["4.4", "Backup", "Zálohovací systémy — privilegovaný přístup; data chráněná proti ransomware (úložiště Dell)."],
    ] },
};

// how each phase's etapy split across two detail slides
const phaseSplit = {
  "1": [["1.1", "1.2", "1.3"], ["1.4", "1.5", "1.6", "1.7"]],
  "2": [["2.1", "2.2"], ["2.3"]],
  "3": [["3.1", "3.2"], ["3.3"]],
  "4": [["4.1", "4.2"], ["4.3", "4.4"]],
};

function l2name(wbs) { const t = allTasks.find(x => x.wbs === wbs); return t ? t.name : wbs; }
function phaseMeta(code) {
  const l1 = allTasks.find(t => t.wbs === code);
  return { period: `${l1.startEU} – ${l1.finishEU}`, pct: Math.round(l1.pct * 100) + " %", prio: l1.prio, prioCz: PRIO_CZ[l1.prio] };
}

function descriptionSlide(code) {
  const p = phaseInfo[code];
  const pm = phaseMeta(code);
  const sl = pres.addSlide();
  sl.background = { color: "FFFFFF" };
  sl.addText([
    { text: "Fáze F" + (Number(code) + 3) + "  —  ", options: { bold: true, color: p.accent } },
    { text: p.title, options: { bold: true, color: C.navy } },
  ], { x: 0.5, y: 0.35, w: 12.3, h: 0.55, fontFace: "Calibri", fontSize: 24, align: "left", valign: "middle", margin: 0 });
  sl.addText(`Období ${pm.period}      ·      Plnění ${pm.pct}      ·      Priorita`, { x: 0.5, y: 0.98, w: 9.5, h: 0.3, fontFace: "Calibri", fontSize: 12.5, bold: true, color: C.gray, valign: "middle", margin: 0 });
  chip(sl, 4.45, 1.0, pm.prioCz, PRIO[pm.prio]);
  sl.addText(p.intro, { x: 0.5, y: 1.4, w: 12.3, h: 0.55, fontFace: "Calibri", fontSize: 12.5, italic: true, color: "6B6B6B", valign: "top", margin: 0 });

  const n = p.items.length;
  const cols = n > 4 ? 2 : 1;
  const top = 2.05, bottom = 7.15, vgap = 0.16, hgap = 0.4;
  const rows = Math.ceil(n / cols);
  const cardW = cols === 2 ? (12.3 - hgap) / 2 : 12.3;
  const cardH = (bottom - top - (rows - 1) * vgap) / rows;
  p.items.forEach((it, idx) => {
    const c = idx % cols, r = Math.floor(idx / cols);
    const x = 0.5 + c * (cardW + hgap), y = top + r * (cardH + vgap);
    sl.addShape(pres.ShapeType.roundRect, { x, y, w: cardW, h: cardH, rectRadius: 0.05, fill: { color: C.card }, line: { color: C.cardLn, width: 1 } });
    const dia = Math.min(0.5, cardH * 0.5);
    sl.addShape(pres.ShapeType.ellipse, { x: x + 0.22, y: y + cardH / 2 - dia / 2, w: dia, h: dia, fill: { color: p.accent }, line: { type: "none" } });
    sl.addText(it[0], { x: x + 0.22, y: y + cardH / 2 - dia / 2, w: dia, h: dia, fontFace: "Calibri", fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    const tx = x + 0.22 + dia + 0.25, tw = cardW - (0.22 + dia + 0.25) - 0.25;
    sl.addText(it[1], { x: tx, y: y + 0.14, w: tw, h: 0.34, fontFace: "Calibri", fontSize: 14, bold: true, color: C.ink, valign: "middle", margin: 0 });
    sl.addText(it[2], { x: tx, y: y + 0.5, w: tw, h: cardH - 0.62, fontFace: "Calibri", fontSize: 11.5, color: C.gray, valign: "top", margin: 0 });
  });
}

// ============================================================
//  BUILD DECK
// ============================================================
(function () {
  const ov = allTasks.filter(t => t.level <= 2);
  const startT = ov.reduce((a, b) => (mkey(b.sy, b.sm) < mkey(a.sy, a.sm) ? b : a));
  const pf = (meta.pfinish || "").split(".");
  renderRoadmap({
    tasks: ov, mode: "overview", swimLabel: "CyberArk",
    title: "CyberArk roadmap", subtitle: "celkový harmonogram",
    flags: [
      { y: startT.sy, m: startT.sm, d: startT.sd, label: "Zahájení integrace", date: startT.startEU },
      ...(pf.length === 3 ? [{ y: +pf[2], m: +pf[1], d: +pf[0], label: "Konec projektu", date: meta.pfinish }] : []),
    ],
  });
})();

(function () {
  const ov = pres.addSlide();
  ov.background = { color: "FFFFFF" };
  ov.addText("Projekt CyberArk PAM — logika fází", { x: 0.5, y: 0.4, w: 12.3, h: 0.6, fontFace: "Calibri", fontSize: 28, bold: true, color: C.navy });
  ov.addText("Projekt zavádí systém privilegovaného přístupu (PAM) CyberArk do prostředí CETIN. Po vybudování jádra řešení se integrované systémy zapojují postupně v onboardovacích vlnách — fáze F4 až F7. Každá fáze obsahuje několik paralelně běžících etap; každá etapa prochází kroky BRQ → TC → HLD → DEV → TEST → GoLive.", { x: 0.5, y: 1.05, w: 12.3, h: 0.9, fontFace: "Calibri", fontSize: 13, color: C.gray, valign: "top" });
  const ocW = 5.95, ocH = 2.05, ogap = 0.4;
  const opos = [[0.5, 2.2], [0.5 + ocW + ogap, 2.2], [0.5, 2.2 + ocH + 0.35], [0.5 + ocW + ogap, 2.2 + ocH + 0.35]];
  ["1", "2", "3", "4"].forEach((code, i) => {
    const p = phaseInfo[code], pm = phaseMeta(code);
    const [x, y] = opos[i];
    ov.addShape(pres.ShapeType.roundRect, { x, y, w: ocW, h: ocH, rectRadius: 0.06, fill: { color: C.card }, line: { color: C.cardLn, width: 1 } });
    ov.addShape(pres.ShapeType.roundRect, { x, y, w: 0.12, h: ocH, rectRadius: 0.02, fill: { color: p.accent }, line: { type: "none" } });
    ov.addText([
      { text: "F" + (Number(code) + 3) + "  ", options: { bold: true, fontSize: 20, color: p.accent } },
      { text: p.title, options: { bold: true, fontSize: 15, color: C.ink } },
    ], { x: x + 0.35, y: y + 0.18, w: ocW - 0.6, h: 0.4, fontFace: "Calibri", valign: "middle", margin: 0 });
    ov.addText(`Období ${pm.period}   ·   ${p.items.length} etap`, { x: x + 0.35, y: y + 0.62, w: ocW - 1.7, h: 0.3, fontFace: "Calibri", fontSize: 11, color: C.gray, valign: "middle", margin: 0 });
    chip(ov, x + ocW - 1.3, y + 0.62, pm.prioCz, PRIO[pm.prio]);
    ov.addText(p.items.map(it => it[1]).join("  ·  "), { x: x + 0.35, y: y + 1.05, w: ocW - 0.6, h: 0.85, fontFace: "Calibri", fontSize: 11, italic: true, color: "7A7A7A", valign: "top", margin: 0 });
  });
})();

["1", "2", "3", "4"].forEach(code => {
  descriptionSlide(code);
  const phaseTasks = allTasks.filter(t => t.wbs === code || t.wbs.startsWith(code + "."));
  const range = timelineRange(phaseTasks);              // shared axis for both halves
  const groups = phaseSplit[code];
  const p = phaseInfo[code];
  groups.forEach((grp, gi) => {
    const rows = phaseTasks.filter(t => t.level >= 2 && grp.some(g => t.wbs === g || t.wbs.startsWith(g + ".")));
    const l1 = phaseTasks[0];
    renderRoadmap({
      tasks: rows,
      mode: "detail",
      range,
      swimLabel: `F${Number(code) + 3}`,
      title: `Fáze F${Number(code) + 3} — detail (${gi + 1}/${groups.length})`,
      subtitle: grp.map(l2name).join("  ·  "),
      note: "Výplň pruhu: plná barva = dokončeno, světlá = zbývá",
      flags: [
        { y: l1.sy, m: l1.sm, d: l1.sd, label: "Zahájení fáze", date: l1.startEU },
        { y: l1.fy, m: l1.fm, d: l1.fd, label: "Konec fáze", date: l1.finishEU },
      ],
    });
  });
});

pres.writeFile({ fileName: "output/CyberArk roadmap_prezentace.pptx" }).then(f => console.log("saved", f));

```

## Krok 3 — Spuštění + QA (INSIDE Tasku, přes subagenta)

```
node working/build.js
mkdir -p working .qa
python /opt/workspace-config/.claude/skills/pptx/scripts/office/soffice.py \
  --headless --convert-to pdf --outdir working/ "output/<projekt>_prezentace.pptx"
pdftoppm -jpeg -r 150 "working/<projekt>_prezentace.pdf" .qa/slide
# zkontroluj: oranžové roky mimo navy pás; „Dnes" v mezeře nad řádky; milníky
# neořezané; barvy kroků odlišitelné; plná/světlá výplň; řídké slidy kompaktní;
# nic mimo plátno (≤13.333"). Oprav max 2–3 cykly.
rm -rf .qa working/*.pdf
```

User-facing popisy Bash kroků: „Building your slides", „Checking the slides
for errors", „Saving your slides". Bez internetu, neinstaluj balíčky.

## Tipy k úpravám

- **Granularita osy**: měsíční pozicování, kvartální záhlaví. Pro delší/kratší
  projekty se počet kvartálů přizpůsobí automaticky.
- **Rozdělení detailů**: `phaseSplit` — výchozí `[floor(n/2), ceil(n/2)]`.
- **nIDM / druhá dráha**: pokud přijde druhý export (např. nIDM účty), přidej
  další plaveckou dráhu a propojovací šipku (zatím neimplementováno).
- **Datumy u nejdelších pruhů** se vynechávají, pokud se nevejdou za pruh
  (podmínka `bex + ... <= SW`). Lze zmenšit font nebo dát pod pruh.
