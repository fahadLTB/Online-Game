# streamlit_golf.py
"""
Mini Golf — Streamlit
Run: streamlit run streamlit_golf.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Mini Golf", layout="wide")

# -------------------------
# Utility / Physics
# -------------------------
def vec_from_angle_deg(angle_deg):
    rad = np.deg2rad(angle_deg)
    return np.array([np.cos(rad), np.sin(rad)])

def step_ball(pos, vel, dt, friction_coef, wind):
    # pos, vel: 2D numpy arrays
    # friction reduces speed each step; simple Euler integration
    vel = vel + wind * dt
    speed = np.linalg.norm(vel)
    if speed > 1e-6:
        # apply friction as opposing acceleration
        friction_acc = -friction_coef * vel / speed
    else:
        friction_acc = np.array([0.0, 0.0])
    vel = vel + friction_acc * dt
    # clamp very small velocities to zero
    if np.linalg.norm(vel) < 1e-3:
        vel = np.array([0.0, 0.0])
    pos = pos + vel * dt
    return pos, vel

# -------------------------
# Course definitions
# -------------------------
def default_holes():
    # Each hole: dict with 'start', 'hole', 'par', 'bounds' (xmin,xmax,ymin,ymax)
    return [
        {
            "name": "Green 1",
            "start": np.array([10.0, 25.0]),
            "hole": np.array([90.0, 25.0]),
            "par": 3,
            "bounds": (0, 100, 0, 50),
            "obstacles": []  # future use
        },
        {
            "name": "Green 2",
            "start": np.array([10.0, 10.0]),
            "hole": np.array([80.0, 40.0]),
            "par": 4,
            "bounds": (0, 100, 0, 50),
            "obstacles": []
        },
        {
            "name": "Green 3",
            "start": np.array([50.0, 45.0]),
            "hole": np.array([95.0, 5.0]),
            "par": 5,
            "bounds": (0, 100, 0, 50),
            "obstacles": []
        }
    ]

# -------------------------
# Session state init
# -------------------------
if "holes" not in st.session_state:
    st.session_state.holes = default_holes()
if "hole_idx" not in st.session_state:
    st.session_state.hole_idx = 0
if "pos" not in st.session_state:
    st.session_state.pos = st.session_state.holes[st.session_state.hole_idx]["start"].copy()
if "vel" not in st.session_state:
    st.session_state.vel = np.array([0.0, 0.0])
if "strokes" not in st.session_state:
    st.session_state.strokes = 0
if "history" not in st.session_state:
    st.session_state.history = []  # list of (hole_idx, strokes, par, result)
if "game_over" not in st.session_state:
    st.session_state.game_over = False

# Reset button
def reset_game():
    st.session_state.holes = default_holes()
    st.session_state.hole_idx = 0
    st.session_state.pos = st.session_state.holes[0]["start"].copy()
    st.session_state.vel = np.array([0.0, 0.0])
    st.session_state.strokes = 0
    st.session_state.history = []
    st.session_state.game_over = False

# Next hole
def next_hole():
    st.session_state.history.append({
        "hole": st.session_state.hole_idx,
        "strokes": st.session_state.strokes,
        "par": st.session_state.holes[st.session_state.hole_idx]["par"]
    })
    st.session_state.hole_idx += 1
    if st.session_state.hole_idx >= len(st.session_state.holes):
        st.session_state.game_over = True
    else:
        h = st.session_state.holes[st.session_state.hole_idx]
        st.session_state.pos = h["start"].copy()
        st.session_state.vel = np.array([0.0, 0.0])
        st.session_state.strokes = 0

# -------------------------
# UI layout
# -------------------------
st.title("⛳ Mini Golf — Playable in Streamlit")
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Controls")
    hole = st.session_state.holes[st.session_state.hole_idx]
    st.markdown(f"**Hole:** {st.session_state.hole_idx + 1} — {hole['name']}")
    st.markdown(f"**Par:** {hole['par']}")

    angle = st.slider("Angle (degrees)", min_value=0, max_value=360, value=0, step=1, help="0° is to the right (positive x); angles increase counterclockwise.")
    power = st.slider("Power", min_value=0, max_value=100, value=40, step=1)
    wind_enabled = st.checkbox("Random wind each shot", value=True)
    wind_x = st.slider("Wind X component (-20..20)", -20, 20, 0) if not wind_enabled else None
    wind_y = st.slider("Wind Y component (-20..20)", -20, 20, 0) if not wind_enabled else None

    shoot = st.button("🏌️ Shoot!")
    reset = st.button("🔁 Reset Game")
    if reset:
        reset_game()

    st.markdown("---")
    st.subheader("Score")
    st.write(f"Strokes this hole: **{st.session_state.strokes}**")
    completed = len(st.session_state.history)
    if completed > 0:
        rows = []
        for rec in st.session_state.history:
            idx = rec["hole"] + 1
            rows.append(f"Hole {idx}: {rec['strokes']} (par {rec['par']})")
        st.markdown("\n".join(rows))
    if st.session_state.game_over:
        st.success("🏆 Course complete! Final results:")
        total_strokes = sum(r["strokes"] for r in st.session_state.history)
        total_par = sum(r["par"] for r in st.session_state.history)
        st.write(f"Total strokes: **{total_strokes}** — Par: **{total_par}**")

with col1:
    # Drawing area
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bounds = hole["bounds"]
    xmin, xmax, ymin, ymax = bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.set_title(f"Hole {st.session_state.hole_idx + 1}: {hole['name']}")
    ax.set_xticks([])
    ax.set_yticks([])

    # draw course edges
    ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, lw=2))

    # draw hole
    hole_pos = hole["hole"]
    ax.plot(hole_pos[0], hole_pos[1], marker='o', markersize=12, markeredgecolor='black', markerfacecolor='none')
    ax.plot(hole_pos[0], hole_pos[1], marker='.', markersize=6, color='black')

    # draw start
    start_pos = hole["start"]
    ax.plot(start_pos[0], start_pos[1], marker='s', markersize=8, color='green')

    # draw ball at current position
    if "pos" in st.session_state:
        bp = st.session_state.pos
        ax.plot(bp[0], bp[1], marker='o', markersize=8, color='red')

    st.pyplot(fig)

# -------------------------
# Shooting / Simulation
# -------------------------
if shoot and not st.session_state.game_over:
    # compute wind
    if wind_enabled:
        wind = np.random.uniform(-10, 10, size=2)  # wind acceleration in x/y units
    else:
        wind = np.array([wind_x / 5.0, wind_y / 5.0])  # scale down user values
    # initial velocity: map power (0..100) to speed (0..max_speed)
    max_speed = 120.0  # tune for feel
    speed = (power / 100.0) * max_speed
    direction = vec_from_angle_deg(angle)
    vel = direction * speed
    st.session_state.vel = vel.copy()
    st.session_state.strokes += 1

    # simulate until rest or hole-in
    dt = 0.05
    friction_coef = 1.8  # larger -> stops faster
    hole_radius = 3.5
    pos = st.session_state.pos.copy()
    vel = st.session_state.vel.copy()

    # prepare animation area
    anim_placeholder = st.empty()
    max_steps = 1800  # cap safety
    trail = [pos.copy()]

    for step in range(max_steps):
        pos, vel = step_ball(pos, vel, dt, friction_coef, wind * 0.1)
        trail.append(pos.copy())

        # bounce from walls (simple reflect)
        if pos[0] < xmin:
            pos[0] = xmin
            vel[0] = -vel[0] * 0.5
        if pos[0] > xmax:
            pos[0] = xmax
            vel[0] = -vel[0] * 0.5
        if pos[1] < ymin:
            pos[1] = ymin
            vel[1] = -vel[1] * 0.5
        if pos[1] > ymax:
            pos[1] = ymax
            vel[1] = -vel[1] * 0.5

        # check hole
        if np.linalg.norm(pos - hole_pos) <= hole_radius:
            # ball in hole
            pos = hole_pos.copy()
            st.session_state.pos = pos
            st.session_state.vel = np.array([0.0, 0.0])
            anim_fig, anim_ax = plt.subplots(figsize=(8, 4.2))
            anim_ax.set_xlim(xmin, xmax)
            anim_ax.set_ylim(ymin, ymax)
            anim_ax.set_aspect("equal")
            anim_ax.set_xticks([])
            anim_ax.set_yticks([])
            anim_ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, lw=2))
            anim_ax.plot(hole_pos[0], hole_pos[1], marker='o', markersize=12, markeredgecolor='black', markerfacecolor='none')
            anim_ax.plot(hole_pos[0], hole_pos[1], marker='.', markersize=6, color='black')
            anim_ax.plot(np.array(trail)[:,0], np.array(trail)[:,1], lw=1)
            anim_ax.plot(pos[0], pos[1], marker='o', markersize=12, color='gold')
            anim_placeholder.pyplot(anim_fig)
            time.sleep(0.3)
            st.success(f"⛳️ Hole completed in {st.session_state.strokes} strokes (par {hole['par']})")
            next_hole()
            break

        # update plot frame
        anim_fig, anim_ax = plt.subplots(figsize=(8, 4.2))
        anim_ax.set_xlim(xmin, xmax)
        anim_ax.set_ylim(ymin, ymax)
        anim_ax.set_aspect("equal")
        anim_ax.set_xticks([])
        anim_ax.set_yticks([])
        anim_ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, lw=2))
        anim_ax.plot(hole_pos[0], hole_pos[1], marker='o', markersize=12, markeredgecolor='black', markerfacecolor='none')
        anim_ax.plot(start_pos[0], start_pos[1], marker='s', markersize=8, color='green')
        anim_ax.plot(np.array(trail)[:,0], np.array(trail)[:,1], lw=1)
        anim_ax.plot(pos[0], pos[1], marker='o', markersize=8, color='red')

        # small overlay showing wind arrow & vector
        wcenter = np.array([xmin + 6, ymax - 6])
        anim_ax.arrow(wcenter[0], wcenter[1], wind[0], wind[1], head_width=1, head_length=1.5, length_includes_head=True)
        anim_ax.text(wcenter[0], wcenter[1] - 3, "Wind", fontsize=8)

        anim_placeholder.pyplot(anim_fig)
        time.sleep(0.02)

        # stop if ball nearly stopped
        if np.linalg.norm(vel) < 1e-2:
            st.info("Ball stopped.")
            st.session_state.pos = pos
            st.session_state.vel = vel
            break
    else:
        # if loop exhausted
        st.warning("Simulation max steps reached; stopping ball.")
        st.session_state.pos = pos
        st.session_state.vel = vel

    # refresh the static drawing of the course in the column
    with col1:
        fig2, ax2 = plt.subplots(figsize=(8, 4.2))
        ax2.set_xlim(xmin, xmax)
        ax2.set_ylim(ymin, ymax)
        ax2.set_aspect("equal")
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, lw=2))
        ax2.plot(hole_pos[0], hole_pos[1], marker='o', markersize=12, markeredgecolor='black', markerfacecolor='none')
        ax2.plot(start_pos[0], start_pos[1], marker='s', markersize=8, color='green')
        ax2.plot(np.array(trail)[:,0], np.array(trail)[:,1], lw=1)
        ax2.plot(st.session_state.pos[0], st.session_state.pos[1], marker='o', markersize=8, color='red')
        st.pyplot(fig2)

# If not shooting and not game over, show a friendly hint
if not st.session_state.game_over and not st.session_state.vel.any():
    st.caption("Adjust angle & power, then press *Shoot!* Tip: try small power for short putts, larger power for long drives.")

# End of file
