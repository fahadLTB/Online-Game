import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Mini Golf", layout="wide")

html_code = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {
    margin: 0;
    overflow: hidden;
    background: #2ecc71;
  }
  canvas {
    background: #27ae60;
    display: block;
    margin: auto;
    border: 3px solid white;
    border-radius: 15px;
  }
  #ui {
    text-align: center;
    font-family: Arial;
    margin-top: 8px;
    color: white;
    font-size: 18px;
  }
</style>
</head>
<body>

<canvas id="golf"></canvas>
<div id="ui">Drag mouse to aim — Release to shoot</div>

<script>
const canvas = document.getElementById("golf");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth * 0.7;
    canvas.height = window.innerHeight * 0.75;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// ---------------------- GAME VARIABLES --------------------------
let ball = { x: 120, y: 200, radius: 10, vx: 0, vy: 0 };
let hole = { x: 600, y: 200, radius: 12 };

let isDragging = false;
let startDrag = { x: 0, y: 0 };
let strokes = 0;

// ---------------------- GAME LOOP -------------------------------
function update() {
    // friction
    ball.vx *= 0.98;
    ball.vy *= 0.98;

    // move ball
    ball.x += ball.vx;
    ball.y += ball.vy;

    // walls
    if (ball.x < ball.radius) { ball.x = ball.radius; ball.vx *= -0.6; }
    if (ball.x > canvas.width - ball.radius) { ball.x = canvas.width - ball.radius; ball.vx *= -0.6; }
    if (ball.y < ball.radius) { ball.y = ball.radius; ball.vy *= -0.6; }
    if (ball.y > canvas.height - ball.radius) { ball.y = canvas.height - ball.radius; ball.vy *= -0.6; }

    // hole detection
    let dx = ball.x - hole.x;
    let dy = ball.y - hole.y;
    if (Math.sqrt(dx*dx + dy*dy) < hole.radius) {
        ball.vx = 0;
        ball.vy = 0;
        ctx.fillStyle = "white";
        ctx.font = "28px Arial";
        ctx.fillText("⛳ HOLE IN! Strokes: " + strokes, 20, 40);
        return; // freeze game
    }

    draw();
    requestAnimationFrame(update);
}

// ---------------------- DRAW ------------------------------
function draw() {
    ctx.clearRect(0,0,canvas.width,canvas.height);

    // hole
    ctx.beginPath();
    ctx.fillStyle = "black";
    ctx.arc(hole.x, hole.y, hole.radius, 0, Math.PI*2);
    ctx.fill();

    // ball
    ctx.beginPath();
    ctx.fillStyle = "white";
    ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI*2);
    ctx.fill();

    // aim line
    if (isDragging) {
        ctx.beginPath();
        ctx.moveTo(ball.x, ball.y);
        ctx.lineTo(startDrag.x, startDrag.y);
        ctx.strokeStyle = "red";
        ctx.lineWidth = 3;
        ctx.stroke();
    }
}

// ---------------------- MOUSE INPUT -----------------------
canvas.addEventListener("mousedown", (e) => {
    let rect = canvas.getBoundingClientRect();
    let mx = e.clientX - rect.left;
    let my = e.clientY - rect.top;

    let d = Math.sqrt((mx - ball.x)**2 + (my - ball.y)**2);
    if (d < ball.radius + 5) {
        isDragging = true;
        startDrag.x = mx;
        startDrag.y = my;
    }
});

canvas.addEventListener("mousemove", (e) => {
    if (isDragging) {
        let rect = canvas.getBoundingClientRect();
        startDrag.x = e.clientX - rect.left;
        startDrag.y = e.clientY - rect.top;
    }
});

canvas.addEventListener("mouseup", (e) => {
    if (isDragging) {
        let dx = ball.x - startDrag.x;
        let dy = ball.y - startDrag.y;
        ball.vx = dx * 0.15;
        ball.vy = dy * 0.15;

        strokes++;
    }
    isDragging = false;
});

draw();
update();
</script>

</body>
</html>
"""

components.html(html_code, height=700, scrolling=False)
