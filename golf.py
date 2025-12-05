import streamlit as st
import numpy as np
from streamlit_drawable_canvas import st_canvas
import time

st.set_page_config(page_title="Mini Golf", layout="wide")

# ------------------- Physics helpers --------------------
def vec(angle_deg):
    r = np.deg2rad(angle_deg)
    return np.array([np.cos(r), np.sin(r)])

def step_ball(pos, vel, dt, friction, wind):
    vel = vel + wind * dt
    speed = np.linalg.norm(vel)
    if speed > 0:
        vel -= friction * vel / speed * dt
    if np.linalg.norm(vel) < 0.1:
        vel = np.array([0.0, 0.0])
    pos = pos + vel * dt
    return pos, vel

# ---------------------- Holes ----------------------------
holes = [
    {"name":"Hole 1","start":np.array([50,250]),"hole":np.array([450,250]),"par":3},
    {"name":"Hole 2","start":np.array([70,70]),"hole":np.array([430,350]),"par":4},
    {"name":"Hole 3","start":np.array([250,50]),"hole":np.array([460,60]),"par":5},
]

# ---------------- Session state --------------------------
if "index" not in st.session_state:
    st.session_state.index = 0
if "pos" not in st.session_state:
    st.session_state.pos = holes[0]["start"].copy()
if "vel" not in st.session_state:
    st.session_state.vel = np.array([0.0, 0.0])
if "strokes" not in st.session_state:
    st.session_state.strokes = 0
if "finished" not in st.session_state:
    st.session_state.finished = False

# ---------------- UI -------------------------------
left, right = st.columns([2, 1])

hole = holes[st.session_state.index]

with right:
    st.subheader("Controls")
    st.write(f"**Hole {st.session_state.index+1}: {hole['name']}**")
    st.write(f"**Par:** {hole['par']}")

    angle = st.slider("Angle", 0, 360, 0)
    power = st.slider("Power", 0, 100, 40)

    random_wind = st.checkbox("Random wind", True)
    wind = np.random.uniform(-20, 20, 2) if random_wind else np.array([
        st.slider("Wind X", -20, 20, 0),
        st.slider("Wind Y", -20, 20, 0)
    ])
    wind = wind / 10  # scale

    shoot = st.button("🏌 Shoot")
    reset = st.button("🔁 Reset Game")

    if reset:
        st.session_state.index = 0
        st.session_state.pos = holes[0]["start"].copy()
        st.session_state.vel = np.array([0,0])
        st.session_state.strokes = 0
        st.session_state.finished = False
        st.rerun()

# ---------------- Canvas (draw course) --------------------
with left:
    canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_color="black",
        background_color="#00aa00",
        height=400,
        width=500,
        drawing_mode="transform",
        key="canvas"
    )

# Draw start, hole, ball on canvas
if canvas.image_data is not None:
    import cv2
    img = canvas.image_data.copy()

    # Start point
    cv2.circle(img, hole["start"].astype(int), 8, (0,0,0), -1)

    # Hole
    cv2.circle(img, hole["hole"].astype(int), 10, (255,255,255), 2)

    # Ball
    cv2.circle(img, st.session_state.pos.astype(int), 8, (0,0,255), -1)

    st.image(img)

# ----------------- Shooting logic ------------------------
if shoot and not st.session_state.finished:
    st.session_state.strokes += 1

    max_speed = 80
    vel = vec(angle) * (power/100*max_speed)

    dt = 0.05
    friction = 8
    pos = st.session_state.pos.copy()

    placeholder = st.empty()

    for _ in range(500):
        pos, vel = step_ball(pos, vel, dt, friction, wind)

        # Keep inside field
        pos[0] = max(10, min(490, pos[0]))
        pos[1] = max(10, min(390, pos[1]))

        # Check hole
        if np.linalg.norm(pos - hole["hole"]) < 12:
            pos = hole["hole"].copy()
            st.session_state.pos = pos
            st.success(f"⛳ Hole completed in {st.session_state.strokes} strokes!")

            st.session_state.index += 1
            if st.session_state.index >= len(holes):
                st.balloons()
                st.session_state.finished = True
            else:
                st.session_state.pos = holes[st.session_state.index]["start"].copy()
                st.session_state.strokes = 0

            st.rerun()

        # Update display
        frame = canvas.image_data.copy()
        frame = frame if frame is not None else np.zeros((400,500,3),dtype=np.uint8)
        import cv2
        cv2.circle(frame, pos.astype(int), 8, (0,0,255), -1)
        cv2.circle(frame, hole["hole"].astype(int), 10, (255,255,255), 2)
        placeholder.image(frame)

        time.sleep(0.01)

    st.session_state.pos = pos
    st.session_state.vel = vel

