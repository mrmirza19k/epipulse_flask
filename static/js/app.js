/**
 * EpiPulse AI — Frontend Application
 * Flask + Vanilla JS + Plotly.js
 */

// ─── PLOTLY DEFAULTS ─────────────────────────────────────────────────────────
const THEME = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(13,27,42,0.8)",
  font: { family: "Space Grotesk", color: "#c8dae8", size: 11 },
  margin: { l: 50, r: 20, t: 40, b: 50 },
  xaxis: { gridcolor: "#1e3a5f", zerolinecolor: "#1e3a5f", tickfont: { color: "#7eb8d4" } },
  yaxis: { gridcolor: "#1e3a5f", zerolinecolor: "#1e3a5f", tickfont: { color: "#7eb8d4" } },
};

const COLORS = {
  primary: "#00d4ff", Low: "#2ecc71", Moderate: "#f39c12",
  High: "#e67e22", Critical: "#e74c3c",
  models: { ARIMA: "#ff6b6b", Prophet: "#a29bfe", LSTM: "#00cec9", Ensemble: "#fdcb6e" },
};

const DISEASE_PALETTE = ["#00d4ff","#a29bfe","#2ecc71","#fdcb6e","#e84393","#fd79a8","#74b9ff"];

// ─── STATE ────────────────────────────────────────────────────────────────────
const state = {
  disease: null, district: null, horizon: 14,
  dateStart: null, dateEnd: null,
  activeTab: "trends", filterLevels: new Set(["Critical","High","Moderate","Low"]),
  riskData: [], alertsData: [],
};

// ─── UTILS ────────────────────────────────────────────────────────────────────
function qs(sel) { return document.querySelector(sel); }
function qsa(sel) { return document.querySelectorAll(sel); }

function params() {
  const p = new URLSearchParams({
    disease: state.disease, district: state.district,
    horizon: state.horizon, start: state.dateStart, end: state.dateEnd,
  });
  return p.toString();
}

async function fetchAPI(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function fmt(n) {
  if (n == null || n === undefined) return "—";
  if (typeof n === "number") return n.toLocaleString();
  return n;
}

function riskBadge(level) {
  return `<span class="badge badge-${level}">${level}</span>`;
}

function plotly(id, traces, layout, config = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  Plotly.react(el, traces, { ...THEME, ...layout }, {
    responsive: true, displayModeBar: false, ...config
  });
}

// ─── INIT ─────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const meta = await fetchAPI("/api/meta");
    // Populate selects
    const selD = qs("#sel-disease"), selDist = qs("#sel-district");
    meta.diseases.forEach(d => { selD.add(new Option(d, d)); });
    meta.districts.forEach(d => { selDist.add(new Option(d, d)); });
    state.disease = meta.diseases[0];
    state.district = meta.districts[0];
    state.dateStart = meta.date_min;
    state.dateEnd   = meta.date_max;
    qs("#date-start").value = meta.date_min;
    qs("#date-end").value   = meta.date_max;
    qs("#date-start").min   = meta.date_min;
    qs("#date-start").max   = meta.date_max;
    qs("#date-end").min     = meta.date_min;
    qs("#date-end").max     = meta.date_max;

    bindEvents();
    await refresh();
  } catch(e) {
    console.error(e);
  } finally {
    qs("#loading").classList.add("hidden");
  }
}

// ─── EVENT BINDING ────────────────────────────────────────────────────────────
function bindEvents() {
  qs("#sel-disease").addEventListener("change", e => { state.disease = e.target.value; refresh(); });
  qs("#sel-district").addEventListener("change", e => { state.district = e.target.value; refreshTab(); });
  qs("#date-start").addEventListener("change", e => { state.dateStart = e.target.value; refresh(); });
  qs("#date-end").addEventListener("change", e => { state.dateEnd = e.target.value; refresh(); });
  qs("#menu-btn").addEventListener("click", toggleSidebar);

  qsa(".horizon-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      qsa(".horizon-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.horizon = parseInt(btn.dataset.val);
      if (state.activeTab === "forecast") renderForecast();
    });
  });

  qsa(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      qsa(".tab-btn").forEach(b => b.classList.remove("active"));
      qsa(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      state.activeTab = btn.dataset.tab;
      qs(`#tab-${state.activeTab}`).classList.add("active");
      refreshTab();
    });
  });

  qsa(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.classList.toggle("active");
      const lv = btn.dataset.level;
      if (state.filterLevels.has(lv)) state.filterLevels.delete(lv);
      else state.filterLevels.add(lv);
      renderAlertCards();
    });
  });
}

function toggleSidebar() {
  qs("#sidebar").classList.toggle("hidden");
  qs("#main").classList.toggle("full");
}

// ─── REFRESH LOGIC ────────────────────────────────────────────────────────────
async function refresh() {
  await Promise.all([renderKPI(), renderStatusBanner(), refreshTab()]);
}

async function refreshTab() {
  switch(state.activeTab) {
    case "trends":    await renderTrends();    break;
    case "forecast":  await renderForecast();  break;
    case "risk":      await renderRisk();      break;
    case "geo":       await renderGeo();       break;
    case "alerts":    await renderAlerts();    break;
    case "analytics": await renderAnalytics(); break;
  }
}

// ─── KPI ──────────────────────────────────────────────────────────────────────
async function renderKPI() {
  try {
    const s = await fetchAPI(`/api/summary?${params()}`);
    qs("#kpi-cases-val").textContent = s.total_cases_7d.toLocaleString();
    qs("#kpi-hosp-val").textContent  = s.total_hospitalizations_7d.toLocaleString();
    qs("#kpi-districts-val").textContent = s.active_districts;
    qs("#kpi-risk-val").textContent  = s.highest_risk_district;
    qs("#kpi-disease-val").textContent = s.most_active_disease;
    const pct = s.change_pct;
    const delta = qs("#kpi-cases-delta");
    delta.textContent = `${pct >= 0 ? "↑" : "↓"} ${Math.abs(pct)}% vs prev week`;
    delta.style.color  = pct >= 0 ? "#e74c3c" : "#2ecc71";
  } catch(e) { console.error("KPI error", e); }
}

// ─── STATUS BANNER ─────────────────────────────────────────────────────────────
async function renderStatusBanner() {
  try {
    const d = await fetchAPI(`/api/alerts?${params()}`);
    const s = d.system_status;
    const banner = qs("#status-banner");
    const colorMap = { "CRITICAL":"#e74c3c","HIGH ALERT":"#e67e22","WATCH":"#f39c12","Normal":"#2ecc71" };
    const col = colorMap[s.level] || "#2ecc71";
    banner.style.borderLeftColor = col;
    banner.style.background = `rgba(${hexToRgb(col)},0.07)`;
    banner.style.color = col;
    qs("#status-text").innerHTML = `🛰️ SYSTEM STATUS · <strong>${s.level}</strong> · ${s.message}`;
    state.alertsData = d;
  } catch(e) { console.error("Status error", e); }
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}

// ─── TAB 1: TRENDS ────────────────────────────────────────────────────────────
async function renderTrends() {
  qs("#trends-header").textContent = `📈 ${state.disease} Trend — ${state.district}`;
  try {
    const d = await fetchAPI(`/api/trends?${params()}`);
    const s = d.series;
    if (!s.length) return;

    const dates = s.map(r => r.date);
    const cases = s.map(r => r.cases);
    const anomalies = s.filter(r => r.anomaly_combined);

    const traces = [
      {
        x: dates, y: cases, type: "scatter", mode: "lines",
        name: "Daily Cases",
        line: { color: COLORS.primary, width: 2 },
        fill: "tozeroy", fillcolor: "rgba(0,212,255,0.08)"
      },
      {
        x: anomalies.map(r=>r.date), y: anomalies.map(r=>r.cases),
        mode: "markers", name: "⚠️ Anomaly",
        marker: { color: "#e74c3c", size: 9, symbol: "triangle-up",
                  line: { width: 2, color: "#ff6b6b" } }
      },
    ];

    // Rolling averages (subplot row 2 simulated with secondary traces)
    if (s[0]?.rolling_avg_7d != null) {
      traces.push({
        x: dates, y: s.map(r=>r.rolling_avg_7d),
        name: "7-Day Avg", line: { color:"#00ff88", width:2 },
        type:"scatter", mode:"lines", yaxis:"y2"
      });
    }
    if (s[0]?.rolling_avg_14d != null) {
      traces.push({
        x: dates, y: s.map(r=>r.rolling_avg_14d),
        name: "14-Day Avg", line: { color:"#ffaa00", width:2, dash:"dash" },
        type:"scatter", mode:"lines", yaxis:"y2"
      });
    }
    if (s[0]?.humidity != null) {
      traces.push({
        x: dates, y: s.map(r=>r.humidity),
        name: "Humidity %", line: { color:"#7eb8d4", width:1.5 },
        type:"scatter", mode:"lines", yaxis:"y3"
      });
    }
    if (s[0]?.temperature != null) {
      traces.push({
        x: dates, y: s.map(r=>r.temperature),
        name: "Temp °C", line: { color:"#ff7675", width:1.5 },
        type:"scatter", mode:"lines", yaxis:"y3"
      });
    }

    plotly("chart-trends", traces, {
      height: 500,
      legend: { orientation:"h", y:-0.12, bgcolor:"rgba(0,0,0,0)" },
      yaxis:  { title: "Cases", gridcolor:"#1e3a5f", domain:[0.55,1] },
      yaxis2: { title: "Rolling Avg", gridcolor:"#1e3a5f", domain:[0.28,0.52], anchor:"x" },
      yaxis3: { title: "Env", gridcolor:"#1e3a5f", domain:[0,0.25], anchor:"x" },
      xaxis:  { gridcolor:"#1e3a5f" },
      title:  { text: `${state.disease} — ${state.district}`, font:{ color:"#7eb8d4", size:12 } }
    });

    // Anomaly table
    renderAnomalyTable(d.anomaly_summary);
  } catch(e) { console.error("Trends error", e); }
}

function renderAnomalyTable(rows) {
  if (!rows.length) {
    qs("#anomaly-table").innerHTML = `<div style="padding:1rem;color:#7eb8d4;">No significant anomalies detected.</div>`;
    return;
  }
  const cols = ["district","disease","total_anomalies","latest_anomaly","max_cases","avg_zscore"];
  const labels = ["District","Disease","Anomalies","Latest","Max Cases","Avg Z-Score"];
  qs("#anomaly-table").innerHTML = buildTable(rows, cols, labels);
}

// ─── TAB 2: FORECAST ─────────────────────────────────────────────────────────
async function renderForecast() {
  qs("#forecast-header").textContent = `🔮 Forecast — ${state.district} · ${state.disease}`;
  try {
    const d = await fetchAPI(`/api/forecast?${params()}`);
    if (d.error) {
      qs("#chart-forecast").innerHTML = `<div style="padding:2rem;color:#f39c12;">${d.error}</div>`;
      return;
    }

    const traces = [{
      x: d.historical_dates, y: d.historical_cases,
      name: "Historical", type:"scatter", mode:"lines",
      line: { color: COLORS.primary, width:2.5 }
    }];

    for (const [model, result] of Object.entries(d.models)) {
      const col = COLORS.models[model] || "#fff";
      const dash = model === "Ensemble" ? "solid" : "dot";
      const width = model === "Ensemble" ? 3 : 1.5;
      traces.push({
        x: d.future_dates, y: result.mean,
        name: `${model} Forecast`, type:"scatter", mode:"lines",
        line: { color: col, dash, width }
      });
      if (model === "Ensemble") {
        traces.push({
          x: [...d.future_dates, ...d.future_dates.slice().reverse()],
          y: [...result.upper, ...result.lower.slice().reverse()],
          fill: "toself", fillcolor: "rgba(253,203,110,0.12)",
          line: { color:"rgba(0,0,0,0)" }, name:"90% CI", showlegend:true
        });
      }
    }

    // Vertical line at forecast start
    traces.push({
      x: [d.historical_dates.at(-1), d.historical_dates.at(-1)],
      y: [0, Math.max(...d.historical_cases) * 1.3],
      mode:"lines", name:"Forecast Start", showlegend:false,
      line: { color:"rgba(255,255,255,0.2)", dash:"dash" }
    });

    plotly("chart-forecast", traces, {
      height: 440,
      legend: { orientation:"h", y:-0.12, bgcolor:"rgba(0,0,0,0)" },
      title: { text:`${state.horizon}-Day Forecast`, font:{ color:"#7eb8d4", size:12 } }
    });

    // Metrics table
    if (Object.keys(d.metrics).length) {
      const metricRows = Object.entries(d.metrics).map(([model, m]) => ({
        Model: model, MAE: m.MAE, RMSE: m.RMSE, MAPE: `${m.MAPE}%`
      }));
      qs("#metrics-table").innerHTML = buildTable(metricRows, ["Model","MAE","RMSE","MAPE"], ["Model","MAE","RMSE","MAPE"]);
    } else {
      qs("#metrics-table").innerHTML = `<div style="padding:1rem;color:#7eb8d4;">Insufficient data for backtesting.</div>`;
    }

    // Forecast values table
    const ensemble = d.models["Ensemble"];
    const fRows = d.future_dates.map((dt, i) => ({
      Date: dt,
      "Predicted Cases": Math.round(ensemble.mean[i]),
      "Lower": Math.round(ensemble.lower[i]),
      "Upper": Math.round(ensemble.upper[i]),
    }));
    qs("#forecast-table").innerHTML = buildTable(fRows, ["Date","Predicted Cases","Lower","Upper"], ["Date","Predicted Cases","Lower Bound","Upper Bound"]);
  } catch(e) { console.error("Forecast error", e); }
}

// ─── TAB 3: RISK ─────────────────────────────────────────────────────────────
async function renderRisk() {
  qs("#risk-header").textContent = `⚠️ District Risk — ${state.disease}`;
  try {
    const data = await fetchAPI(`/api/risk?${params()}`);
    state.riskData = data;
    if (!data.length) { qs("#chart-gauge").innerHTML = `<div style="padding:2rem;color:#f39c12;">No data.</div>`; return; }

    const top = data[0];

    // Gauge
    plotly("chart-gauge", [{
      type:"indicator", mode:"gauge+number",
      value: top.risk_score,
      title: { text:`<b>${top.district}</b><br><span style="font-size:11px">${state.disease} Risk</span>`, font:{ color:"#c8dae8" } },
      gauge: {
        axis: { range:[0,100], tickcolor:"#7eb8d4" },
        bar:  { color: COLORS[top.risk_level] },
        steps:[
          {range:[0,30],  color:"#0a2010"},
          {range:[30,60], color:"#1a2a00"},
          {range:[60,80], color:"#2a1800"},
          {range:[80,100],color:"#2a0800"},
        ],
      },
      number: { font:{ color: COLORS[top.risk_level] } }
    }], { height:280, margin:{l:20,r:20,t:60,b:20} });

    // Surge info
    qs("#surge-info").innerHTML = `
      <div class="surge-item">Highest Risk District: <span>${top.district}</span></div>
      <div class="surge-item">Risk Level: <span>${top.risk_level}</span></div>
      <div class="surge-item">Risk Score: <span>${top.risk_score}/100</span></div>
    `;

    // Bar chart
    const barColors = data.map(r => COLORS[r.risk_level] || COLORS.primary);
    plotly("chart-risk-bar", [{
      type:"bar", x: data.map(r=>r.district), y: data.map(r=>r.risk_score),
      marker: { color: barColors },
      text: data.map(r=>r.risk_score.toFixed(1)), textposition:"outside"
    }], {
      height:280, title:{ text:"Risk Score by District", font:{color:"#7eb8d4",size:12} },
      shapes: [
        {type:"line",y0:30,y1:30,x0:0,x1:1,xref:"paper",line:{color:"#2ecc71",dash:"dot",width:1}},
        {type:"line",y0:60,y1:60,x0:0,x1:1,xref:"paper",line:{color:"#f39c12",dash:"dot",width:1}},
        {type:"line",y0:80,y1:80,x0:0,x1:1,xref:"paper",line:{color:"#e74c3c",dash:"dot",width:1}},
      ],
    });

    // Risk table
    const cols = ["district","risk_level","risk_score","trend_score","env_score","geo_score","avg_cases","total_cases_7d"];
    const labels = ["District","Level","Score","Trend","Env","Geo","Avg Cases","7d Cases"];
    const formatted = data.map(r => ({
      ...r,
      risk_level: riskBadge(r.risk_level),
      risk_score: r.risk_score?.toFixed(1),
      trend_score: r.trend_score?.toFixed(1),
      env_score: r.env_score?.toFixed(1),
      geo_score: r.geo_score?.toFixed(1),
    }));
    qs("#risk-table").innerHTML = buildTable(formatted, cols, labels, true);

    // Radar
    const top5 = data.slice(0, 5);
    const radarTraces = top5.map((r, i) => ({
      type:"scatterpolar",
      r: [r.trend_score||0, r.env_score||0, r.geo_score||0, r.anomaly_score_component||0, r.trend_score||0],
      theta: ["Trend","Environment","Geographic","Anomaly","Trend"],
      name: r.district, fill:"toself", opacity:0.6,
      line:{ color: DISEASE_PALETTE[i] }
    }));
    plotly("chart-radar", radarTraces, {
      height:380,
      polar:{ bgcolor:"rgba(13,27,42,0.8)", radialaxis:{visible:true,range:[0,100],gridcolor:"#1e3a5f"}, angularaxis:{gridcolor:"#1e3a5f"} },
      legend:{ bgcolor:"rgba(0,0,0,0)" }
    });
  } catch(e) { console.error("Risk error", e); }
}

// ─── TAB 4: GEO ──────────────────────────────────────────────────────────────
async function renderGeo() {
  qs("#geo-header").textContent = `🗺️ Geographic Risk — ${state.disease}`;
  try {
    const data = await fetchAPI(`/api/risk?${params()}`);
    if (!data.length) return;

    // Scatter mapbox using open-street-map (no token needed for basic)
    const mapTrace = {
      type:"scattermapbox",
      lat: data.map(r=>r.lat), lon: data.map(r=>r.lon),
      mode:"markers",
      marker:{
        size: data.map(r => 10 + r.risk_score / 4),
        color: data.map(r=>r.risk_score),
        colorscale:[[0,"#2ecc71"],[0.3,"#f39c12"],[0.6,"#e67e22"],[1,"#e74c3c"]],
        cmin:0, cmax:100,
        colorbar:{ title:"Risk", tickfont:{color:"#c8dae8"}, titlefont:{color:"#c8dae8"} },
        opacity:0.85,
      },
      text: data.map(r=>`<b>${r.district}</b><br>Risk: ${r.risk_score?.toFixed(1)}<br>Level: ${r.risk_level}<br>7d Cases: ${r.total_cases_7d}`),
      hovertemplate:"%{text}<extra></extra>",
    };
    const mapEl = document.getElementById("chart-map");
    Plotly.react(mapEl, [mapTrace], {
      mapbox:{ style:"carto-darkmatter", center:{lat:30.9,lon:75.8}, zoom:6.8 },
      paper_bgcolor:"rgba(0,0,0,0)",
      font:{family:"Space Grotesk",color:"#c8dae8"},
      margin:{l:0,r:0,t:30,b:0},
      height:450,
      title:{text:`${state.disease} Risk Map — Punjab`,font:{color:"#7eb8d4",size:12}},
    }, { responsive:true, displayModeBar:false });

    // Treemap
    plotly("chart-treemap", [{
      type:"treemap",
      labels: data.map(r=>r.district),
      parents: data.map(()=>""),
      values: data.map(r=>r.total_cases_7d),
      marker:{
        colors: data.map(r=>r.risk_score),
        colorscale:[[0,"#0a2010"],[0.5,"#4a2800"],[1,"#6a0000"]],
        cmin:0,cmax:100,
      },
      textinfo:"label+value",
      hovertemplate:"<b>%{label}</b><br>7d Cases: %{value}<extra></extra>",
    }], { height:300, margin:{l:5,r:5,t:30,b:5} });

    // Spread trajectory — use trend data per district
    const trendData = await fetchAPI(`/api/trends?disease=${state.disease}&start=${state.dateStart}&end=${state.dateEnd}&district=${state.district}`);
    // We don't have multi-district trend in single call; use risk scores over time as approximation
    // Instead, build simple bar from risk data
    plotly("chart-spread", [{
      type:"bar", orientation:"h",
      x: data.map(r=>r.avg_cases), y: data.map(r=>r.district),
      marker:{ color: data.map(r=>COLORS[r.risk_level]||COLORS.primary) },
      text: data.map(r=>r.avg_cases.toFixed(1)), textposition:"outside",
    }], {
      height:300, title:{text:"Avg Cases/Day by District",font:{color:"#7eb8d4",size:12}},
      margin:{l:90,r:30,t:40,b:40},
    });
  } catch(e) { console.error("Geo error", e); }
}

// ─── TAB 5: ALERTS ────────────────────────────────────────────────────────────
async function renderAlerts() {
  qs("#alerts-header").textContent = `🚨 Active Alerts — ${state.disease}`;
  try {
    let d = state.alertsData;
    if (!d || !d.alerts) d = await fetchAPI(`/api/alerts?${params()}`);
    state.alertsData = d;
    renderAlertCards();
    renderCrossDisease(d.cross_disease);
  } catch(e) { console.error("Alerts error", e); }
}

function renderAlertCards() {
  const d = state.alertsData;
  if (!d) return;
  const filtered = (d.alerts || []).filter(a => state.filterLevels.has(a.risk_level));
  const container = qs("#alerts-container");
  if (!filtered.length) {
    container.innerHTML = `<div class="alert-card" style="border-left-color:#2ecc71;color:#2ecc71;">✅ No active alerts for selected filters.</div>`;
    return;
  }
  container.innerHTML = filtered.map(a => `
    <div class="alert-card" style="border-left-color:${a.color};">
      <div class="alert-header">
        <span class="alert-title" style="color:${a.color};">${a.emoji} ${a.district} — ${a.risk_level} Risk</span>
        <span class="alert-meta">${a.timestamp} · Score: ${a.risk_score.toFixed(0)}/100</span>
      </div>
      <div class="alert-body">${a.message}</div>
    </div>
  `).join("");
}

function renderCrossDisease(cross) {
  if (!cross || !cross.length) return;
  // Build pivot
  const districts = [...new Set(cross.flat().map(r=>r.district))].sort();
  const diseases   = [...new Set(cross.flat().map(r=>r.disease))].sort();
  const lookup = {};
  cross.flat().forEach(r => { lookup[`${r.district}||${r.disease}`] = r.risk_score; });
  const z = districts.map(dist => diseases.map(dis => lookup[`${dist}||${dis}`] || 0));

  plotly("chart-crossdisease", [{
    type:"heatmap", z, x:diseases, y:districts,
    colorscale:[[0,"#0a2010"],[0.3,"#1a3a00"],[0.6,"#4a2800"],[1,"#6a0000"]],
    zmin:0, zmax:100,
    colorbar:{ title:"Risk", tickfont:{color:"#c8dae8"}, titlefont:{color:"#c8dae8"} },
    hovertemplate:"District: %{y}<br>Disease: %{x}<br>Risk: %{z:.1f}<extra></extra>",
  }], {
    height:380, title:{text:"Risk Score: Districts × Diseases",font:{color:"#7eb8d4",size:12}},
    margin:{l:100,r:20,t:40,b:80},
  });
}

// ─── TAB 6: ANALYTICS ────────────────────────────────────────────────────────
async function renderAnalytics() {
  try {
    const d = await fetchAPI(`/api/analytics?${params()}`);

    // Pie
    plotly("chart-pie", [{
      type:"pie",
      labels: d.disease_totals.map(r=>r.disease),
      values: d.disease_totals.map(r=>r.cases),
      marker:{ colors:DISEASE_PALETTE },
      textinfo:"label+percent",
      textfont:{ color:"#c8dae8" },
      hole:0.35,
    }], { height:320, margin:{l:10,r:10,t:30,b:10}, showlegend:false });

    // Monthly bar
    const diseases = [...new Set(d.monthly_trend.map(r=>r.disease))];
    const months   = [...new Set(d.monthly_trend.map(r=>r.month_year))].sort();
    const monthlyTraces = diseases.map((dis, i) => {
      const rows = d.monthly_trend.filter(r=>r.disease===dis);
      const map  = Object.fromEntries(rows.map(r=>[r.month_year,r.cases]));
      return {
        type:"bar", name:dis,
        x:months, y:months.map(m=>map[m]||0),
        marker:{ color:DISEASE_PALETTE[i] }
      };
    });
    plotly("chart-monthly", monthlyTraces, {
      height:320, barmode:"stack",
      legend:{bgcolor:"rgba(0,0,0,0)"},
      margin:{l:50,r:10,t:30,b:60},
    });

    // Correlation heatmap
    const labels = d.corr_labels;
    const z = labels.map(a => labels.map(b => (d.corr_matrix[a]||{})[b] || 0));
    plotly("chart-corr", [{
      type:"heatmap", z, x:labels, y:labels,
      colorscale:"RdBu", zmin:-1, zmax:1,
      colorbar:{tickfont:{color:"#c8dae8"},title:"r"},
      text: z.map(row=>row.map(v=>v.toFixed(2))),
      texttemplate:"%{text}", textfont:{size:10,color:"#c8dae8"},
    }], { height:350, margin:{l:120,r:10,t:30,b:90} });

    // Hospital burden
    const hosp = d.hospital_burden.sort((a,b)=>b.total_hosp-a.total_hosp);
    plotly("chart-hosp", [{
      type:"bar", orientation:"h",
      x:hosp.map(r=>r.total_hosp), y:hosp.map(r=>r.district),
      marker:{ color:hosp.map(r=>r.hosp_rate), colorscale:"Reds", cmin:0, cmax:25,
               colorbar:{title:"Rate%",tickfont:{color:"#c8dae8"},titlefont:{color:"#c8dae8"}} },
      text:hosp.map(r=>r.total_hosp.toLocaleString()), textposition:"outside",
    }], { height:320, margin:{l:90,r:30,t:30,b:40}, title:{text:"Total Hospitalizations",font:{color:"#7eb8d4",size:12}} });

    // Positivity rate
    const pr = d.positivity_rate;
    plotly("chart-posrate", [{
      type:"scatter", mode:"lines",
      x:pr.map(r=>r.date), y:pr.map(r=>r.positive_rate),
      fill:"tozeroy", fillcolor:"rgba(162,155,254,0.1)",
      line:{color:"#a29bfe",width:2}, name:"Positivity Rate"
    }], {
      height:320,
      shapes:[{ type:"line",y0:5,y1:5,x0:0,x1:1,xref:"paper",line:{color:"#e74c3c",dash:"dash",width:1} }],
      annotations:[{x:0.02,y:5.5,xref:"paper",yref:"y",text:"WHO 5% threshold",showarrow:false,font:{color:"#e74c3c",size:10}}],
      title:{text:"Test Positivity Rate Trend",font:{color:"#7eb8d4",size:12}},
    });
  } catch(e) { console.error("Analytics error", e); }
}

// ─── TABLE BUILDER ────────────────────────────────────────────────────────────
function buildTable(rows, cols, labels, raw=false) {
  if (!rows.length) return `<div style="padding:1rem;color:#7eb8d4;">No data available.</div>`;
  const thead = labels.map(l=>`<th>${l}</th>`).join("");
  const tbody = rows.map(r => {
    const cells = cols.map(c => {
      const v = r[c];
      return `<td>${v == null ? "—" : raw ? v : fmt(v)}</td>`;
    }).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  return `<table><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
}

// ─── BOOT ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", init);
