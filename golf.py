import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Mini Golf — Streamlit", layout="wide")

# Single-file Streamlit app that embeds a JS canvas mini-golf game.
# Save this file and run: `streamlit run streamlit_golf_game.py`

GAME_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    html, body { height: 100%; margin: 0; background: #0b1220; }
    #game { width: 100%; height: 100%; display: block; }
    .hud { position: absolute; left: 12px; top: 10px; z-index: 10; color: white; font-family: Inter, Roboto, sans-serif;}
    .hud .item { margin-bottom: 6px; background: rgba(0,0,0,0.45); padding: 8px 12px; border-radius: 10px; }
    .levelBadge { font-weight: 700; }
    /* remove selection and gestures while playing */
    * { -webkit-user-select:none; -ms-user-select:none; user-select:none; -webkit-touch-callout:none; -webkit-tap-highlight-color: transparent; }
  </style>
</head>
<body>
  <canvas id="game" style=\"touch-action:none; margin-top:120px;\"></canvas>
  <div class="hud">
    <div class="item" id="level">LEVEL 1</div>
    <div class="item" id="strokes">STROKES: 0</div>
    <div class="item" id="best">BEST: -</div>
  </div>

<script>
(() => {
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  let DPR = window.devicePixelRatio || 1;

  function fitCanvas() {
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(300, Math.floor(rect.width * DPR));
    canvas.height = Math.max(300, Math.floor(rect.height * DPR));
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener('resize', fitCanvas);
  fitCanvas();

  // --- Simple level format ---
  // Each level: { start: [x,y], hole: [x,y], obstacles: [{x,y,w,h,angle}] , bounds: [w,h] }
  const LEVELS = [
    {
      name: '1',
      start: [120, 240],
      hole: [520, 80],
      bounds: [canvas.width / DPR, canvas.height / DPR],
      obstacles: [
        {x: 300, y: 200, w: 200, h: 16, angle: 0},
        {x: 180, y: 360, w: 110, h: 16, angle: -0.4}
      ]
    },
    {
      name: '2',
      start: [80, 120],
      hole: [560, 360],
      bounds: [canvas.width / DPR, canvas.height / DPR],
      obstacles: [
        {x: 200, y: 120, w: 16, h: 160, angle: 0},
        {x: 360, y: 280, w: 220, h: 16, angle: 0.2},
        {x: 480, y: 120, w: 120, h: 16, angle: -0.4}
      ]
    },
    {
      name: '3',
      start: [60, 420],
      hole: [580, 60],
      bounds: [canvas.width / DPR, canvas.height / DPR],
      obstacles: [
        {x: 160, y: 240, w: 200, h: 16, angle: 0.4},
        {x: 360, y: 140, w: 16, h: 200, angle: 0},
        {x: 420, y: 360, w: 200, h: 16, angle: -0.25}
      ]
    }
  ];

  // Scaling between game coords and canvas pixels.
  let scaleX = 1, scaleY = 1;

  // Game state
  let currentLevel = 0;
  let strokes = 0;
  let bests = Array(LEVELS.length).fill(null);

  // ball
  const BALL_RADIUS = 8;
  let ball = {x:0,y:0, vx:0, vy:0};

  // physics
  const FRICTION = 0.97; // increased friction so ball stops faster // velocity multiplier per frame
  const STOP_V = 0.03;

  // interaction
  let isDragging = false;
  let dragStart = null; // {x,y}
  let dragPos = null;

  // convenience
  const hudLevel = document.getElementById('level');
  const hudStrokes = document.getElementById('strokes');
  const hudBest = document.getElementById('best');

  function resetBallForLevel(i) {
    const L = LEVELS[i];
    ball.x = L.start[0];
    ball.y = L.start[1];
    ball.vx = 0; ball.vy = 0;
  }

  function resizeToLevel() {
    const L = LEVELS[currentLevel];
    // scale to fit canvas while preserving aspect
    scaleX = canvas.width / DPR / L.bounds[0];
    scaleY = canvas.height / DPR / L.bounds[1];
  }

  function screenToGame(px, py) {
    const rect = canvas.getBoundingClientRect();
    const x = (px - rect.left) / (rect.width) * LEVELS[currentLevel].bounds[0];
    const y = (py - rect.top) / (rect.height) * LEVELS[currentLevel].bounds[1];
    return {x,y};
  }

  function drawRoundedRect(x,y,w,h,r) {
    ctx.beginPath();
    ctx.moveTo(x+r,y);
    ctx.arcTo(x+w,y,x+w,y+h,r);
    ctx.arcTo(x+w,y+h,x,y+h,r);
    ctx.arcTo(x,y+h,x,y,r);
    ctx.arcTo(x,y,x+w,y,r);
    ctx.closePath();
    ctx.fill();
  }

  function drawLevel() {
    const L = LEVELS[currentLevel];
    // GRASS TEXTURE
    const imgSize = 60;
    const grassCanvas = document.createElement('canvas');
    grassCanvas.width = imgSize;
    grassCanvas.height = imgSize;
    const gctx = grassCanvas.getContext('2d');

    // base grass color
    gctx.fillStyle = '#2e6b2e';
    gctx.fillRect(0, 0, imgSize, imgSize);

    // random lighter blades
    for (let i = 0; i < 80; i++) {
      gctx.strokeStyle = 'rgba(255,255,255,0.08)';
      gctx.lineWidth = 1;
      const x = Math.random() * imgSize;
      const y = Math.random() * imgSize;
      const len = 4 + Math.random() * 6;
      gctx.beginPath();
      gctx.moveTo(x, y);
      gctx.lineTo(x + (Math.random()*2-1)*2, y - len);
      gctx.stroke();
    }

    // apply as repeating pattern
    const pattern = ctx.createPattern(grassCanvas, 'repeat');
    ctx.fillStyle = pattern;
    ctx.fillRect(0, 0, canvas.width / DPR, canvas.height / DPR);

    // fairway border
    ctx.save();
    ctx.fillStyle = '#1b391b';
    ctx.globalAlpha = 0.2;
    ctx.fillRect(6,6,canvas.width/DPR-12, canvas.height/DPR-12);
    ctx.restore();

    // obstacles
    ctx.fillStyle = '#7b5b3b';
    L.obstacles.forEach(ob => {
      ctx.save();
      ctx.translate(ob.x, ob.y);
      ctx.rotate(ob.angle);
      drawRoundedRect(-ob.w/2, -ob.h/2, ob.w, ob.h, 6);
      ctx.restore();
    });

    // hole
    ctx.save();
    ctx.beginPath();
    ctx.fillStyle = '#000';
    ctx.arc(L.hole[0], L.hole[1], 10, 0, Math.PI*2);
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#fff4';
    ctx.stroke();
    ctx.restore();
  }

  function drawBall() {
    ctx.save();
    // Soft shadow
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 3;
    ctx.shadowOffsetY = 3;

    ctx.beginPath();
    ctx.fillStyle = '#fff';
    ctx.arc(ball.x, ball.y, BALL_RADIUS, 0, Math.PI*2);
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = '#bbb';
    ctx.stroke();
    ctx.restore();
}

  function drawAiming() {
    if (!isDragging || !dragStart || !dragPos) return;

    const dx = dragPos.x - dragStart.x;
    const dy = dragPos.y - dragStart.y;
    const dist = Math.hypot(dx,dy);
    const maxPower = 18;
    const power = Math.min(dist/6, maxPower);
    const ang = Math.atan2(dy, dx);
    const arrowLen = power * 10;

    // --- GLOW ---
    ctx.save();
    ctx.shadowColor = 'rgba(255,255,255,0.9)';
    ctx.shadowBlur = 12;
    ctx.lineWidth = 5;
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.beginPath();
    ctx.moveTo(ball.x, ball.y);
    ctx.lineTo(ball.x + arrowLen * Math.cos(ang), ball.y + arrowLen * Math.sin(ang));
    ctx.stroke();

    // Arrow tip
    ctx.beginPath();
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    const tipX = ball.x + arrowLen * Math.cos(ang);
    const tipY = ball.y + arrowLen * Math.sin(ang);
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX - 10 * Math.cos(ang - Math.PI/6), tipY - 10 * Math.sin(ang - Math.PI/6));
    ctx.lineTo(tipX - 10 * Math.cos(ang + Math.PI/6), tipY - 10 * Math.sin(ang + Math.PI/6));
    ctx.closePath();
    ctx.fill();
    ctx.restore();

    // --- POWER BAR ---
    const barX = 20;
    const barY = canvas.height / DPR - 40;
    const barW = canvas.width / DPR - 40;
    const barH = 12;

    ctx.save();
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.fillRect(barX, barY, barW, barH);

    const fillW = (power / maxPower) * barW;
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.fillRect(barX, barY, fillW, barH);
    ctx.restore();
}

  function reflectIfCollide(ob) {
    // approximate obstacle as oriented rectangle; reflect ball vector simple by axis
    // transform ball into obstacle local coords
    const cos = Math.cos(-ob.angle), sin = Math.sin(-ob.angle);
    const lx = cos*(ball.x - ob.x) - sin*(ball.y - ob.y);
    const ly = sin*(ball.x - ob.x) + cos*(ball.y - ob.y);
    const hw = ob.w/2 + BALL_RADIUS;
    const hh = ob.h/2 + BALL_RADIUS;
    if (lx > -hw && lx < hw && ly > -hh && ly < hh) {
      // simple push out along smaller penetration axis
      const px = Math.min(hw - lx, hw + lx);
      const py = Math.min(hh - ly, hh + ly);
      if (px < py) {
        // reflect vx along local x
        const localVx = cos*ball.vx + sin*ball.vy;
        const localVy = -sin*ball.vx + cos*ball.vy;
        // invert x velocity
        const newLocalVx = -localVx * 0.8;
        // convert back
        ball.vx = cos*newLocalVx - sin*localVy;
        ball.vy = sin*newLocalVx + cos*localVy;
        // nudge out
        const sign = lx>0?1:-1;
        ball.x += sign * (hw - Math.abs(lx)) * 0.9 * (cos);
        ball.y += sign * (hw - Math.abs(lx)) * 0.9 * (-sin);
      } else {
        // invert y velocity
        const localVx = cos*ball.vx + sin*ball.vy;
        const localVy = -sin*ball.vx + cos*ball.vy;
        const newLocalVy = -localVy * 0.8;
        ball.vx = cos*localVx - sin*newLocalVy;
        ball.vy = sin*localVx + cos*newLocalVy;
        const sign = ly>0?1:-1;
        ball.x += sign * (hh - Math.abs(ly)) * 0.9 * ( -sin );
        ball.y += sign * (hh - Math.abs(ly)) * 0.9 * ( cos );
      }
    }
  }

  function updatePhysics() {
    // move
    ball.x += ball.vx;
    ball.y += ball.vy;

    // bounds
    const L = LEVELS[currentLevel];
    if (ball.x < BALL_RADIUS) { ball.x = BALL_RADIUS; ball.vx = -ball.vx * 0.6; }
    if (ball.y < BALL_RADIUS) { ball.y = BALL_RADIUS; ball.vy = -ball.vy * 0.6; }
    if (ball.x > L.bounds[0] - BALL_RADIUS) { ball.x = L.bounds[0] - BALL_RADIUS; ball.vx = -ball.vx * 0.6; }
    if (ball.y > L.bounds[1] - BALL_RADIUS) { ball.y = L.bounds[1] - BALL_RADIUS; ball.vy = -ball.vy * 0.6; }

    // obstacles
    L.obstacles.forEach(ob => reflectIfCollide(ob));

    // friction
    ball.vx *= FRICTION;
    ball.vy *= FRICTION;

    if (Math.hypot(ball.vx, ball.vy) < STOP_V) { ball.vx = 0; ball.vy = 0; }
  }

  function checkHole() {
    const L = LEVELS[currentLevel];
    const d = Math.hypot(ball.x - L.hole[0], ball.y - L.hole[1]);
    if (d < 12 && Math.hypot(ball.vx, ball.vy) < 0.8) {
      // level complete
      setTimeout(() => {
        // record best
        if (bests[currentLevel] === null || strokes < bests[currentLevel]) bests[currentLevel] = strokes;
        // advance level
        currentLevel = (currentLevel + 1) % LEVELS.length;
        strokes = 0;
        resetBallForLevel(currentLevel);
        updateHUD();
      }, 350);
    }
  }

  function updateHUD() {
    hudLevel.innerText = 'LEVEL ' + LEVELS[currentLevel].name;
    hudStrokes.innerText = 'STROKES: ' + strokes;
    const b = bests[currentLevel];
    hudBest.innerText = 'BEST: ' + (b === null ? '-' : b);
  }

  // Add STOP button
  const stopBtn = document.createElement('div');
  stopBtn.innerText = 'STOP';
  stopBtn.style.position = 'absolute';
  stopBtn.style.right = '12px';
  stopBtn.style.top = '80px';
  stopBtn.style.padding = '10px 16px';
  stopBtn.style.fontFamily = 'Inter, sans-serif';
  stopBtn.style.color = 'white';
  stopBtn.style.background = 'rgba(0,0,0,0.45)';
  stopBtn.style.borderRadius = '10px';
  stopBtn.style.zIndex = 20;
  stopBtn.style.cursor = 'pointer';
  stopBtn.addEventListener('click', ()=>{ ball.vx = 0; ball.vy = 0; });
  document.body.appendChild(stopBtn);

  // input handlers for mouse and touch
  function onPointerDown(e) {
    e.preventDefault();
    let p = null;
    if (e.touches) {
      p = screenToGame(e.touches[0].clientX, e.touches[0].clientY);
    } else {
      p = screenToGame(e.clientX, e.clientY);
    }
    // only allow drag if click is near the ball or ball is stopped
    const d = Math.hypot(p.x - ball.x, p.y - ball.y);
    if (true) {
      isDragging = true;
      dragStart = {x: ball.x, y: ball.y};
      dragPos = p;
    }
  }
  function onPointerMove(e) {
    if (!isDragging) return;
    e.preventDefault();
    let p = null;
    if (e.touches) {
      p = screenToGame(e.touches[0].clientX, e.touches[0].clientY);
    } else {
      p = screenToGame(e.clientX, e.clientY);
    }
    dragPos = p;
  }
  function onPointerUp(e) {
    if (!isDragging) return;
    e.preventDefault();
    // compute power
    const dx = dragStart.x - dragPos.x;
    const dy = dragStart.y - dragPos.y;
    const dist = Math.hypot(dx,dy);
    if (dist > 4) {
      const maxPower = 18;
      const power = Math.min(dist/6, maxPower);
      // direction
      const nx = dx / dist;
      const ny = dy / dist;
      ball.vx = nx * power;
      ball.vy = ny * power;
      strokes += 1;
      updateHUD();
    }
    isDragging = false;
    dragStart = null;
    dragPos = null;
  }

  // attach both mouse and touch
  canvas.addEventListener('mousedown', onPointerDown);
  window.addEventListener('mousemove', onPointerMove);
  window.addEventListener('mouseup', onPointerUp);
  canvas.addEventListener('touchstart', onPointerDown, {passive:false});
  window.addEventListener('touchmove', onPointerMove, {passive:false});
  window.addEventListener('touchend', onPointerUp, {passive:false});

  // keyboard for quick reset/skip
  window.addEventListener('keydown', (e)=>{
    if (e.key === 'r') { resetBallForLevel(currentLevel); strokes = 0; updateHUD(); }
    if (e.key === 'n') { currentLevel = (currentLevel+1) % LEVELS.length; resetBallForLevel(currentLevel); strokes = 0; updateHUD(); }
  });

  // start
  resetBallForLevel(currentLevel);
  resizeToLevel();
  updateHUD();

  function loop() {
    fitCanvas();
    resizeToLevel();
    // clear
    ctx.clearRect(0,0,canvas.width/DPR, canvas.height/DPR);
    // draw
    drawLevel();
    drawBall();
    drawAiming();

    updatePhysics();
    checkHole();

    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
</script>
</body>
</html>
"""

st.markdown("", unsafe_allow_html=True)
# Render the game full-width. adjust height if needed.
html(GAME_HTML, height=720, scrolling=False)

# Minimal footer to keep it only the game screen as requested
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
