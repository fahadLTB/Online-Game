# golf_isometric.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Isometric Mini Golf", layout="centered")
st.title("⛳ Isometric Mini Golf — Style B")
st.write("Click and drag the ball to set power/direction. Holes, ramps, and obstacles on 3 holes. Enjoy!")

# Embedded HTML + JS (single string)
html_code = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Isometric Mini Golf</title>
<style>
  html,body{margin:0;height:100%;background:linear-gradient(#86c2ff,#dff3ff);}
  #game {
    display:flex;
    align-items:center;
    justify-content:center;
    height:600px;
    width:100%;
    user-select:none;
  }
  canvas{ background:transparent; border-radius:12px; box-shadow: 0 6px 18px rgba(0,0,0,0.15);}
  #ui {
    position:absolute;
    top:18px;
    left:18px;
    font-family:Inter, Arial;
    color:#00334d;
    background: rgba(255,255,255,0.85);
    padding:10px 12px;
    border-radius:10px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
  }
  #msg { margin-top:6px; color:#0b5; font-weight:700; }
  button { margin-top:8px; padding:6px 10px; border-radius:8px; border:0; background:#0077cc; color:white; cursor:pointer;}
  button:active{ transform: translateY(1px);}
  #hint { margin-top:8px; font-size:0.85em; color:#234; opacity:0.9;}
  #powerbar {
    height:8px; width:120px; background:rgba(0,0,0,0.08); border-radius:8px; overflow:hidden; margin-top:8px;
  }
  #power { height:100%; width:0%; background:linear-gradient(90deg,#ffb347,#ffcc33); }
</style>
</head>
<body>
<div id="game">
  <canvas id="c" width="880" height="560"></canvas>
  <div id="ui">
    <div><strong id="holeLabel">Hole 1</strong> — Par <span id="parLabel">3</span></div>
    <div>Strokes: <strong id="strokes">0</strong></div>
    <div id="powerbar"><div id="power"></div></div>
    <div id="msg"></div>
    <div id="hint">Drag ball to aim and release to shoot. Hold longer for more power.</div>
    <button id="reset">Reset Hole</button>
  </div>
</div>

<script>
(function(){
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d', { alpha: true });
  const W = canvas.width, H = canvas.height;

  // ISOMETRIC SETTINGS
  const TILE_W = 64, TILE_H = 32;   // base diamond tile sizes
  const MAP_W = 11, MAP_H = 7;      // grid size
  const ORIGIN_X = W*0.12, ORIGIN_Y = 80; // where grid starts

  // physics
  const FRICTION = 0.992;
  const POWER_SCALE = 0.45; // adjust feel
  const MAX_POWER = 220;

  let holes = buildHoles();
  let holeIndex = 0;
  let strokes = 0;

  // ball state
  let ball = { gx: 1, gy: 1, x:0, y:0, z:0, vx:0, vy:0, vz:0, radius:8 };
  let dragging=false, dragStart=null, lastTime = null;
  let aimPower = 0;

  // UI
  const holeLabel = document.getElementById('holeLabel');
  const parLabel = document.getElementById('parLabel');
  const strokesLabel = document.getElementById('strokes');
  const msg = document.getElementById('msg');
  const powerBar = document.getElementById('power');
  const resetBtn = document.getElementById('reset');

  resetBtn.onclick = () => { resetHole(); }

  function buildHoles(){
    // Each hole: grid of tiles; tile types: 0=flat,1=wall,2=ramp-up,3=ramp-down,4=hole,5=bounce
    // ramps are directional via tile.r: 0/1/2/3 mapping to north/east/south/west
    // We'll place a few obstacles to make it fun.
    const holeA = {
      name: "Cobbled Court",
      par: 3,
      start: {gx:1, gy:3},
      holePos: {gx:9, gy:3},
      tiles: defaultTiles()
    };
    const holeB = {
      name: "Sloped Alley",
      par: 4,
      start:{gx:1, gy:1},
      holePos:{gx:9, gy:5},
      tiles: defaultTiles()
    };
    const holeC = {
      name: "Tricky Terrace",
      par: 5,
      start:{gx:2, gy:5},
      holePos:{gx:9, gy:1},
      tiles: defaultTiles()
    };

    // customize A
    placeRect(holeA.tiles,2,2,2,3,5); // place bumpers along left center
    holeA.tiles[3][5] = {t:1}; // wall
    holeA.tiles[3][4] = {t:5}; // bounce pad
    // add some ramps to B
    holeB.tiles[3][2] = {t:2, r:1}; // ramp up to east
    holeB.tiles[4][2] = {t:3, r:1}; // ramp down from east
    placeRect(holeB.tiles,5,1,2,4,1);
    holeB.tiles[6][3] = {t:5}; // bounce
    // tricky terrace ramps & narrow corridor for C
    holeC.tiles[4][4] = {t:2, r:0};
    holeC.tiles[4][3] = {t:2, r:0};
    holeC.tiles[5][3] = {t:3, r:2};
    placeRect(holeC.tiles,6,2,2,2,1);
    holeC.tiles[7][3] = {t:5};

    // set hole tiles
    holeA.tiles[holeA.holePos.gx][holeA.holePos.gy] = {t:4};
    holeB.tiles[holeB.holePos.gx][holeB.holePos.gy] = {t:4};
    holeC.tiles[holeC.holePos.gx][holeC.holePos.gy] = {t:4};

    return [holeA, holeB, holeC];

    function defaultTiles(){
      const arr = [];
      for(let gx=0; gx<MAP_W; gx++){
        arr[gx] = [];
        for(let gy=0; gy<MAP_H; gy++){
          arr[gx][gy] = {t:0}; // flat
        }
      }
      // perimeter walls
      for(let gx=0; gx<MAP_W; gx++){
        arr[gx][0] = {t:1};
        arr[gx][MAP_H-1] = {t:1};
      }
      for(let gy=0; gy<MAP_H; gy++){
        arr[0][gy] = {t:1};
        arr[MAP_W-1][gy] = {t:1};
      }
      return arr;
    }
    function placeRect(tiles, gx, gy, w, h, tval){
      for(let x=gx; x<gx+w; x++){
        for(let y=gy; y<gy+h; y++){
          if(x>=0 && x<MAP_W && y>=0 && y<MAP_H) tiles[x][y] = {t:tval};
        }
      }
    }
  }

  function initHole(){
    const h = holes[holeIndex];
    holeLabel.innerText = "Hole " + (holeIndex+1) + " — " + h.name;
    parLabel.innerText = h.par;
    strokes = 0; updateStrokes();
    ball.gx = h.start.gx; ball.gy = h.start.gy;
    setBallToTileCenter(ball);
    ball.vx = ball.vy = ball.vz = 0;
    msg.innerText = "Ready!";
    powerBar.style.width = "0%";
  }

  function resetHole(){
    ball.vx = ball.vy = ball.vz = 0;
    const h = holes[holeIndex];
    ball.gx = h.start.gx; ball.gy = h.start.gy;
    setBallToTileCenter(ball);
    strokes = 0; updateStrokes();
    msg.innerText = "Hole reset.";
  }

  function nextHole(){
    holeIndex++;
    if(holeIndex >= holes.length){
      msg.innerText = "Course complete! Great job!";
      holeIndex = 0;
      // show small congrats animation (flash)
      flashCongrats();
    }
    initHole();
  }

  function flashCongrats(){
    let alpha=0; const intr=setInterval(()=>{
      ctx.fillStyle = `rgba(255,255,255,${0.08+alpha})`;
      ctx.fillRect(0,0,W,H);
      alpha += 0.06;
      if(alpha>0.7){ clearInterval(intr); }
    },80);
  }

  function updateStrokes(){ strokesLabel.innerText = strokes; }

  function setBallToTileCenter(b){
    const p = isoToScreen(b.gx, b.gy);
    b.x = p.x; b.y = p.y - (b.z || 0);
  }

  // coordinate transforms
  function isoToScreen(gx, gy){
    // isometric diamond: screenX = ORIGIN_X + (gx - gy)*TILE_W/2
    // screenY = ORIGIN_Y + (gx + gy)*TILE_H/2
    const x = ORIGIN_X + (gx - gy) * (TILE_W/2);
    const y = ORIGIN_Y + (gx + gy) * (TILE_H/2);
    return {x:x, y:y};
  }
  function screenToIso(sx, sy){
    const tx = sx - ORIGIN_X;
    const ty = sy - ORIGIN_Y;
    const gx = (ty/(TILE_H/2) + tx/(TILE_W/2)) / 2;
    const gy = (ty/(TILE_H/2) - tx/(TILE_W/2)) / 2;
    return {gx: Math.round(gx), gy: Math.round(gy)};
  }

  // drawing tile
  function drawTile(gx, gy, tile){
    const p = isoToScreen(gx, gy);
    const x = p.x, y = p.y;
    // draw diamond
    ctx.beginPath();
    ctx.moveTo(x, y - TILE_H/2);
    ctx.lineTo(x + TILE_W/2, y);
    ctx.lineTo(x, y + TILE_H/2);
    ctx.lineTo(x - TILE_W/2, y);
    ctx.closePath();

    // base color by type
    let base = "#bfe3a7";
    if(tile.t === 1) base = "#8a8a8a"; // wall
    if(tile.t === 2) base = "#d2f3ff"; // ramp up (lighter)
    if(tile.t === 3) base = "#b6e6c2"; // ramp down
    if(tile.t === 4) base = "#222222"; // hole (dark)
    if(tile.t === 5) base = "#ffd1d1"; // bounce pad

    ctx.fillStyle = base;
    ctx.fill();

    // outline
    ctx.strokeStyle = "rgba(0,0,0,0.12)";
    ctx.stroke();

    // small highlight
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.fill();
  }

  function drawMap(){
    const tiles = holes[holeIndex].tiles;
    // sort by gx+gy for depth
    for(let s=0; s<MAP_W+MAP_H; s++){
      for(let gx=0; gx<MAP_W; gx++){
        let gy = s - gx;
        if(gy>=0 && gy<MAP_H){
          if(gx>=0 && gx<MAP_W){
            drawTile(gx, gy, tiles[gx][gy]);
            // draw ramps/borders for ramps
            const t = tiles[gx][gy];
            if(t.t === 2 || t.t === 3){
              // simple arrow to show slope
              const p = isoToScreen(gx,gy);
              ctx.fillStyle = "rgba(0,0,0,0.15)";
              ctx.font = "10px Inter, Arial";
              const arrow = (t.t===2) ? "↑" : "↓";
              ctx.fillText(arrow, p.x-4, p.y+3);
            }
            if(t.t === 4){
              const p = isoToScreen(gx,gy);
              ctx.beginPath();
              ctx.arc(p.x, p.y, 10, 0, Math.PI*2);
              ctx.fillStyle = "#111";
              ctx.fill();
              ctx.strokeStyle = "#000";
              ctx.stroke();
            }
            if(t.t === 1){
              // wall block: draw small raised square at center
              const p = isoToScreen(gx,gy);
              ctx.fillStyle = "#666";
              ctx.fillRect(p.x-12, p.y-18, 24, 12);
              ctx.strokeStyle = "#444";
              ctx.strokeRect(p.x-12, p.y-18, 24, 12);
            }
            if(t.t === 5){
              const p = isoToScreen(gx,gy);
              ctx.fillStyle = "#ff6b6b";
              ctx.beginPath();
              ctx.ellipse(p.x, p.y+4, 14,7,0,0,Math.PI*2);
              ctx.fill();
            }
          }
        }
      }
    }
  }

  function drawBall(b){
    // shadow
    ctx.beginPath();
    ctx.ellipse(b.x, b.y + 10, b.radius*1.1, b.radius*0.6, 0, 0, Math.PI*2);
    ctx.fillStyle = "rgba(0,0,0,0.18)";
    ctx.fill();

    // ball with simple shading
    ctx.beginPath();
    ctx.arc(b.x, b.y - b.z, b.radius, 0, Math.PI*2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = "#ccc"; ctx.stroke();

    // shineline
    ctx.beginPath();
    ctx.arc(b.x - b.radius*0.35, b.y - b.z - b.radius*0.2, b.radius*0.4, 0, Math.PI*2);
    ctx.fillStyle = "rgba(255,255,255,0.8)";
    ctx.fill();
  }

  function clear(){
    ctx.clearRect(0,0,W,H);
  }

  function gameTick(t){
    if(!lastTime) lastTime = t;
    const dt = Math.min(40, t - lastTime) / 16.666; // normalize ~60fps
    lastTime = t;

    // update physics
    ball.x += ball.vx * dt;
    ball.y += ball.vy * dt;
    // approximate grid location from screen coords
    const approx = screenToIso(ball.x, ball.y);
    // keep ball inside bounds by reflecting
    if(approx.gx <= 0 || approx.gx >= MAP_W-1 || approx.gy<=0 || approx.gy>=MAP_H-1){
      // bounce from border
      ball.vx *= -0.7; ball.vy *= -0.7;
      ball.x = Math.max(ORIGIN_X - TILE_W/2 + 16, Math.min(ball.x, ORIGIN_X + (MAP_W-1 - 0) * TILE_W/2 + TILE_W/2 - 16));
      ball.y = Math.max(ORIGIN_Y - TILE_H/2 + 16, Math.min(ball.y, ORIGIN_Y + (MAP_W-1 + MAP_H-1) * TILE_H/2 + TILE_H/2 - 16));
    }

    // friction
    ball.vx *= Math.pow(FRICTION, dt);
    ball.vy *= Math.pow(FRICTION, dt);

    // small threshold to stop
    if(Math.abs(ball.vx) < 0.01) ball.vx = 0;
    if(Math.abs(ball.vy) < 0.01) ball.vy = 0;

    // tile interaction
    const tiles = holes[holeIndex].tiles;
    const g = screenToIso(ball.x, ball.y);
    if(g.gx >=0 && g.gx < MAP_W && g.gy>=0 && g.gy<MAP_H){
      const tile = tiles[g.gx][g.gy];
      if(tile.t === 1){
        // Wall: push ball back
        ball.vx *= -0.65; ball.vy *= -0.65;
      }
      if(tile.t === 5){
        // bounce pad — boost speed a little
        ball.vx *= 1.35; ball.vy *= 1.35;
      }
      if(tile.t === 2 || tile.t === 3){
        // ramp: nudge vertical position (z) visually
        if(tile.t===2) ball.z = Math.min(12, ball.z + 0.3);
        else ball.z = Math.max(0, ball.z - 0.3);
      } else {
        // relax z towards 0
        ball.z *= 0.94;
      }
      if(tile.t === 4){
        // hole: if near center and slow, count as in
        const center = isoToScreen(g.gx, g.gy);
        const dx = ball.x - center.x, dy = ball.y - center.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if(dist < 10 && Math.hypot(ball.vx, ball.vy) < 0.6){
          // scored
          msg.innerText = "⛳ Hole in! Good stroke.";
          setTimeout(()=>{ nextHole(); }, 900);
        }
      }
    }

    // render
    clear();
    drawMap();
    drawBall(ball);

    // draw aim line if dragging
    if(dragging && dragStart){
      ctx.beginPath();
      ctx.moveTo(ball.x, ball.y - ball.z);
      ctx.lineTo(dragStart.sx, dragStart.sy);
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.lineWidth = 2;
      ctx.stroke();
      // power indicator circle
      ctx.beginPath();
      ctx.arc(ball.x, ball.y - ball.z, 10 + Math.min(60, aimPower/3), 0, Math.PI*2);
      ctx.fillStyle = "rgba(255,200,60,0.06)";
      ctx.fill();
    }

    requestAnimationFrame(gameTick);
  }

  // input handling
  canvas.addEventListener('pointerdown', function(e){
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    // check distance from ball
    const dx = sx - ball.x, dy = sy - (ball.y - ball.z);
    if(Math.hypot(dx, dy) < 30){
      dragging = true;
      dragStart = {sx:sx, sy:sy, t:Date.now()};
      aimPower = 0;
      msg.innerText = "Aiming...";
    }
  });
  canvas.addEventListener('pointermove', function(e){
    if(!dragging) return;
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    // update aim power visually by distance
    const dx = sx - ball.x, dy = sy - (ball.y - ball.z);
    aimPower = Math.min(MAX_POWER, Math.hypot(dx,dy));
    powerBar.style.width = Math.min(100, Math.round(100 * (aimPower / MAX_POWER))) + "%";
  });
  canvas.addEventListener('pointerup', function(e){
    if(!dragging) return;
    dragging = false;
    const rect = canvas.getBoundingClientRect();
    const sx = e.clientX - rect.left, sy = e.clientY - rect.top;
    const dx = sx - ball.x, dy = sy - (ball.y - ball.z);
    const dist = Math.hypot(dx,dy);
    if(dist < 6){
      msg.innerText = "Tap-drag to shoot (hold to increase power).";
      powerBar.style.width = "0%";
      return;
    }
    // compute power and direction (opposite drag direction)
    const dirx = -dx / dist, diry = -dy / dist;
    const power = Math.min(MAX_POWER, dist) * POWER_SCALE;
    ball.vx += dirx * power / 20;
    ball.vy += diry * power / 20;
    aimPower = 0;
    powerBar.style.width = "0%";
    strokes++;
    updateStrokes();
    msg.innerText = "Shot!";

    // slight camera nudge or particle? (left minimal)
  });

  // initialize
  initHole();
  requestAnimationFrame(gameTick);

})();
</script>
</body>
</html>
"""

# embed the html in the Streamlit app
components.html(html_code, height=640, scrolling=False)

st.markdown("""
**Controls & tips**
- Click and drag the ball away from its center; releasing will shoot **in the opposite** direction of the drag.
- Hold longer (drag farther) for more power. The UI shows a power bar.
- Walls bounce, bounce pads boost speed, ramps change apparent height, and the dark circle is the hole.
- After completing all holes the course will loop back to Hole 1.

If you'd like, I can:
- add multiplayer turns,
- expose strokes to Streamlit state,
- make a mini level editor,
- or export replays / animated GIFs.

Which would you like next?
""")
