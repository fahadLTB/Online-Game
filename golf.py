import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="2D Flight & Landing Simulator", layout="wide")
st.title("✈️ 2D Flight & Landing Simulator (Streamlit)")

st.markdown(
"""
**How to play:** Use W/S for throttle, A/D to pitch up/down, toggle Flaps (F) and Gear (G).  
Try taking off, fly a pattern and land on the runway. Press **R** to reset.
"""
)

html = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>2D Flight Simulator</title>
<style>
  html,body { margin:0; height:100%; background: linear-gradient(#87ceeb, #dff6ff); font-family: Arial, sans-serif; }
  #wrap { display:flex; gap:16px; padding:12px; align-items:flex-start; }
  canvas { background: linear-gradient(#87ceeb, #bfefff 60%, #8ed17a 61%, #67c25a 100%); border-radius:8px; box-shadow: 0 8px 24px rgba(0,0,0,0.15); }
  #hud { width:320px; color:#012; }
  .panel { background: rgba(255,255,255,0.9); padding:10px; border-radius:8px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); margin-bottom:10px; }
  .meter { font-weight:700; font-size:18px; }
  .small { font-size:13px; color:#234; }
  button { padding:8px 10px; border-radius:6px; border:0; background:#0077cc; color:white; cursor:pointer; }
  .status-good { color: green; font-weight:700; }
  .status-bad  { color: red; font-weight:700; }
  .controls { font-size:13px; color:#234; line-height:1.5; }
</style>
</head>
<body>
<div id="wrap">
  <canvas id="c" width="1100" height="560"></canvas>
  <div id="hud">
    <div class="panel">
      <div class="meter">SPEED: <span id="speed">0</span> kt</div>
      <div class="meter">ALT: <span id="alt">0</span> ft</div>
      <div class="meter">VS: <span id="vs">0</span> ft/s</div>
      <div class="meter">PITCH: <span id="pitch">0</span>°</div>
      <div class="meter">THROTTLE: <span id="th">0</span>%</div>
      <div class="small">Flaps: <span id="flaps">UP</span> | Gear: <span id="gear">UP</span></div>
      <hr/>
      <div id="landing-status" class="small">Landing: <span id="land-ok" class="status-bad">N/A</span></div>
    </div>

    <div class="panel controls">
      <strong>Controls</strong><br/>
      W / ↑ — Throttle up<br/>
      S / ↓ — Throttle down<br/>
      A / ← — Pitch up (pull)<br/>
      D / → — Pitch down (push)<br/>
      F — Toggle flaps<br/>
      G — Toggle gear<br/>
      Space — Auto-flare assist<br/>
      R — Reset plane
    </div>

    <div class="panel">
      <strong>Tips</strong>
      <ul>
        <li>Use runway (drawn on ground). Build speed for takeoff.</li>
        <li>Deploy flaps to reduce stall speed before landing but they add drag.</li>
        <li>Touch down with gear down, low sink rate & slow speed.</li>
      </ul>
      <button id="reset">Reset (R)</button>
    </div>
  </div>
</div>

<script>
(() => {
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;

  // WORLD UNITS: 1 px horizontally ~ 1 ft (approx) for simplicity
  // Ground Y coordinate (sea level)
  const GROUND_Y = H * 0.78;
  const RUNWAY_LEN = 2000; // in simulation horizontal px/ft
  const RUNWAY_X = 120; // starting x of runway
  const runwayCenter = GROUND_Y - 6;

  // PLANE STATE (2D simplified longitudinal dynamics)
  let plane = {
    x: RUNWAY_X + 120,   // horizontal position (ft)
    y: GROUND_Y - 10,    // vertical position (px) - lower is higher altitude
    vx: 0,               // forward speed px/s (ft/s)
    vy: 0,               // vertical speed px/s (ft/s)
    pitch: 0,            // degrees (positive = nose up)
    throttle: 0.0,       // 0..1
    mass: 5000,          // arbitrary mass factor
    flaps: 0,            // 0 (up), 1 (partial), 2 (full)
    gear: true,          // gear down or up (start down)
    onGround: true,
  };

  // PHYSICS params (tweak for fun)
  const GRAVITY = 32.174; // ft/s^2
  const DT = 0.016; // 60 fps ~ 1/60
  const THRUST_MAX = 40000; // arbitrary thrust units
  const DRAG_COEFF = 0.0025; // drag ~ k * v^2
  const LIFT_COEFF_BASE = 0.0005; // lift proportional to v^2 * CL
  const FLAP_LIFT_BONUS = [0, 0.6, 1.1]; // increases lift coefficient
  const FLAP_DRAG_PENALTY = [1.0, 1.4, 1.9];

  // Safe landing thresholds
  const SAFE_TOUCH_SPEED = 70; // ft/s (~42 kt) - safe touchdown speed
  const SAFE_SINK_RATE = 5.0;  // ft/s downward velocity allowed
  const SAFE_PITCH = 10;       // degrees max nose-up at touchdown

  // Visual scaling: convert world alt to displayed "altitude" in feet
  function computeAltitude() {
    // approximate altitude above ground in feet proportional to vertical px difference
    return Math.max(0, Math.round((GROUND_Y - plane.y)));
  }

  // Keyboard controls
  const keys = {};
  window.addEventListener('keydown', (e) => { keys[e.key.toLowerCase()] = true; if(e.key === ' ') e.preventDefault(); });
  window.addEventListener('keyup', (e) => { keys[e.key.toLowerCase()] = false; });

  // UI elements
  const speedEl = document.getElementById('speed');
  const altEl = document.getElementById('alt');
  const vsEl = document.getElementById('vs');
  const pitchEl = document.getElementById('pitch');
  const thEl = document.getElementById('th');
  const flapsEl = document.getElementById('flaps');
  const gearEl = document.getElementById('gear');
  const landOkEl = document.getElementById('land-ok');
  const resetBtn = document.getElementById('reset');

  resetBtn.onclick = resetPlane;

  // reset to start
  function resetPlane(){
    plane.x = RUNWAY_X + 120;
    plane.y = GROUND_Y - 10;
    plane.vx = 0;
    plane.vy = 0;
    plane.pitch = 2;
    plane.throttle = 0;
    plane.flaps = 0;
    plane.gear = true;
    plane.onGround = true;
  }
  resetPlane();

  // physics helpers
  function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
  function deg2rad(d){ return d * Math.PI/180; }

  // main update
  function step(dt){
    // Controls
    if (keys['w'] || keys['arrowup']) { plane.throttle = clamp(plane.throttle + 0.6*dt, 0, 1); }
    if (keys['s'] || keys['arrowdown']) { plane.throttle = clamp(plane.throttle - 0.8*dt, 0, 1); }
    if (keys['a'] || keys['arrowleft']) { plane.pitch = clamp(plane.pitch + 18*dt, -20, 30); }
    if (keys['d'] || keys['arrowright']) { plane.pitch = clamp(plane.pitch - 18*dt, -20, 30); }

    // toggles (press to toggle)
    if (keys['f'] && !keys._f_handled){ plane.flaps = (plane.flaps + 1) % 3; keys._f_handled = true; }
    if (!keys['f']) keys._f_handled = false;
    if (keys['g'] && !keys._g_handled){ plane.gear = !plane.gear; keys._g_handled = true; }
    if (!keys['g']) keys._g_handled = false;
    if (keys['r']) resetPlane();

    // auto-flare assist (space) - small auto-pull when near runway to reduce sink
    const autoFlare = keys[' '];

    // Aerodynamics (very simplified)
    const speed = Math.max(0.1, Math.hypot(plane.vx, plane.vy)); // ft/s
    const thrust = THRUST_MAX * plane.throttle * (1 - 0.6*(plane.flaps/2)); // reduce thrust with flaps deployed
    // convert thrust (horizontal forward)
    // drag ~ k * v^2 * flap_penalty
    const flapDrag = FLAP_DRAG_PENALTY[plane.flaps];
    const drag = DRAG_COEFF * flapDrag * speed * speed;

    // lift ~ base * v^2 * (angle of attack factor)
    // angle of attack approximated by pitch (in radians) clamped
    const aoa = clamp(plane.pitch * 0.01745, -0.6, 0.6);
    const lift = LIFT_COEFF_BASE * (1 + FLAP_LIFT_BONUS[plane.flaps]) * speed*speed * Math.max(0, Math.cos(aoa*0.5));

    // resolve forces into accelerations (horizontal & vertical)
    // thrust produces acceleration in direction of fuselage (pitch)
    const pitchRad = deg2rad(plane.pitch);
    const thrust_x = thrust * Math.cos(pitchRad) / plane.mass;
    const thrust_y = -thrust * Math.sin(pitchRad) / plane.mass;

    const drag_accel = drag / plane.mass;
    const ax = thrust_x - drag_accel * (plane.vx / speed);
    const ay = thrust_y + (lift / plane.mass) - GRAVITY * 1.0; // gravity downward

    // integrate velocities
    plane.vx += ax * dt;
    plane.vy += ay * dt;

    // integrate position
    plane.x += plane.vx * dt;
    plane.y += plane.vy * dt;

    // ground collision (simple terrain: runway area is flat; grass slightly bumpy)
    if (plane.y >= GROUND_Y - 4) {
      // we've hit the ground - check if runway zone
      // runway occupies horizontal area (RUNWAY_X .. RUNWAY_X + RUNWAY_LEN)
      const onRunway = (plane.x >= RUNWAY_X && plane.x <= RUNWAY_X + RUNWAY_LEN);
      // compute vertical speed (positive downwards in pixel coords because y increases downwards)
      const sinkRate = plane.vy; // in px/s (ft/s)
      // success conditions
      const touchSpeed = Math.hypot(plane.vx, plane.vy);
      const pitchOk = Math.abs(plane.pitch) <= SAFE_PITCH;
      const sinkOk = sinkRate >= -SAFE_SINK_RATE; // vy negative upwards; when landing vy small negative acceptable -> we allow small negative magnitude
      const speedOk = Math.hypot(plane.vx, plane.vy) <= SAFE_TOUCH_SPEED;
      if (onRunway && plane.gear && pitchOk && sinkOk && speedOk) {
        // gentle landing - stop and mark on ground
        plane.y = GROUND_Y - 4;
        plane.vx *= 0.2;
        plane.vy = 0;
        plane.onGround = true;
        // indicate success in UI
        landStatus = { ok: true, msg: "Successful landing!" };
      } else {
        // hard landing or off-runway
        plane.y = GROUND_Y - 4;
        plane.vy = 0;
        plane.onGround = true;
        // big bounce if too hard
        if (!onRunway || !plane.gear || !pitchOk || !sinkOk || !speedOk) {
          plane.vx *= 0.5;
          plane.vy = -Math.abs(plane.vx) * 0.15;
          landStatus = { ok: false, msg: "Hard landing / off-runway! Try again." };
          // if very violent, crash (reduce speed near 0)
          const severity = Math.hypot(plane.vx, plane.vy);
          if (severity > 200) {
            plane.vx = 0;
            plane.vy = 0;
            landStatus = { ok:false, msg: "Aircraft destroyed (crash)." };
          }
        } else {
          landStatus = { ok: true, msg: "Landed (but check runway conditions)." };
        }
      }
    } else {
      plane.onGround = false;
      landStatus = { ok: null, msg: "In flight" };
    }

    // autopilot flare assist: if close to runway (x ahead) and altitude low and space pressed, automatically reduce sink
    if (autoFlare && plane.x > RUNWAY_X + 200 && plane.x < RUNWAY_X + RUNWAY_LEN && computeAltitude() < 80) {
      plane.vy = Math.max(plane.vy, -2.2);
      plane.pitch = Math.max(plane.pitch, 2);
    }

    // Update HUD
    const speedKts = Math.round(Math.max(0, plane.vx) * 0.592484); // convert ft/s->kts approx
    document.getElementById('speed').innerText = speedKts;
    document.getElementById('alt').innerText = Math.round(computeAltitude());
    document.getElementById('vs').innerText = Math.round(-plane.vy * 1); // positive up in text? show sink negative downwards
    document.getElementById('pitch').innerText = Math.round(plane.pitch);
    document.getElementById('th').innerText = Math.round(plane.throttle * 100);
    flapsEl.innerText = (plane.flaps === 0 ? "UP" : (plane.flaps === 1 ? "1" : "FULL"));
    gearEl.innerText = (plane.gear ? "DOWN" : "UP");

    // landing status message
    const ls = document.getElementById('land-ok');
    if (landStatus.ok === true) { ls.innerText = landStatus.msg; ls.className = 'status-good'; }
    else if (landStatus.ok === false) { ls.innerText = landStatus.msg; ls.className = 'status-bad'; }
    else { ls.innerText = landStatus.msg; ls.className = ''; }
  }

  // drawing functions
  function draw() {
    // sky gradient is handled by CSS, clear lower portion
    ctx.clearRect(0, 0, W, H);

    // draw ground (hills and runway)
    // sky strip
    ctx.fillStyle = '#bfefff';
    ctx.fillRect(0, 0, W, GROUND_Y - 140);

    // distant hills
    ctx.fillStyle = '#8fcf7a';
    ctx.beginPath();
    ctx.ellipse(W*0.2, GROUND_Y - 60, 300, 140, 0, 0, Math.PI*2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(W*0.6, GROUND_Y - 30, 360, 160, 0, 0, Math.PI*2);
    ctx.fill();

    // ground foreground
    ctx.fillStyle = '#6ec44b';
    ctx.fillRect(0, GROUND_Y - 20, W, H - (GROUND_Y - 20));

    // runway strip
    ctx.fillStyle = '#333';
    ctx.fillRect(RUNWAY_X, runwayCenter - 8, RUNWAY_LEN, 40);
    // runway centerline dashed
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 3;
    ctx.setLineDash([20, 18]);
    ctx.beginPath();
    ctx.moveTo(RUNWAY_X, runwayCenter + 12);
    ctx.lineTo(RUNWAY_X + RUNWAY_LEN, runwayCenter + 12);
    ctx.stroke();
    ctx.setLineDash([]);

    // runway markings (threshold)
    ctx.fillStyle = 'white';
    for (let i=0;i<12;i++){
      ctx.fillRect(RUNWAY_X + 30 + i*26, runwayCenter - 10, 16, 6);
    }

    // draw plane (simple 2D sprite rotated by pitch)
    ctx.save();
    ctx.translate(plane.x, plane.y);
    ctx.rotate(-deg2rad(plane.pitch)); // negative because canvas y-down
    // fuselage
    ctx.fillStyle = '#fff';
    ctx.strokeStyle = '#222';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(0, 0, 36, 10, 0, 0, Math.PI*2);
    ctx.fill();
    ctx.stroke();
    // cockpit
    ctx.fillStyle = '#66aaff';
    ctx.fillRect(6, -6, 12, 8);
    // wings
    ctx.fillStyle = '#ddd';
    ctx.fillRect(-8, -2, -30, 6);
    ctx.fillRect(-8, -2, 30, 6);
    // tail
    ctx.fillStyle = '#fff';
    ctx.fillRect(-36, -6, -12, 4);
    // gear (simple)
    if (plane.gear) {
      ctx.fillStyle = '#222';
      ctx.fillRect(-8, 12, 4, 8);
      ctx.fillRect(8, 12, 4, 8);
    }
    // flaps visual (trailing edge)
    if (plane.flaps) {
      ctx.fillStyle = '#ccc';
      ctx.fillRect(-20, 8, 12, 3);
      ctx.fillRect(8, 8, 12, 3);
    }
    ctx.restore();

    // HUD - small artificial horizon line
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.font = '13px Arial';
    ctx.fillText('Position: ' + Math.round(plane.x) + ' ft', 8, 18);
    ctx.fillText('Throttle: ' + Math.round(plane.throttle*100) + '%', 8, 36);
  }

  // main loop
  let last = performance.now();
  function loop(t){
    const dt = Math.min(0.05, (t - last)/1000);
    last = t;
    // update controls & physics
    step(dt);
    draw();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  // small touch events support
  let touchState = { active:false, sx:0, sy:0 };
  canvas.addEventListener('touchstart', (e) => {
    e.preventDefault();
    const t0 = e.touches[0];
    touchState.active = true; touchState.sx = t0.clientX; touchState.sy = t0.clientY;
  }, {passive:false});
  canvas.addEventListener('touchend', (e) => { touchState.active = false; }, {passive:false});

  // expose simple console-friendly info for debugging
  window.planeSim = plane;

})();
</script>
</body>
</html>
"""

components.html(html, height=640, scrolling=False)

st.markdown("""
**Notes & limitations**
- This is a **2D longitudinal (side-on) simplified simulator** — it keeps the core feel of flight dynamics (thrust, drag, lift ~ v², pitch affects climb/descent).
- It's **not** a full flight dynamics engine; for professional-level simulation you'd integrate a physics library or use an existing flight sim (eg. X-Plane SDK).
- If you want, I can:
  - Add runway approach guidance (glideslope + localizer HUD),
  - Implement crosswind effects and crosswind runway landings,
  - Add instruments (altimeter, VSI, airspeed indicator, attitude indicator),
  - Add throttle/mixture engine failures, engine startup, weight & balance, flaps/trim controls,
  - Convert to a 3D WebGL basic cockpit view,
  - Export landing logs (touchdown speed, sink rate).
Which enhancements do you want next?
""")
