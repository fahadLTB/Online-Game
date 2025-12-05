import streamlit as st
import random
import math

# Course data - 18 holes
COURSES = {
    "Pine Valley": [
        {"par": 4, "distance": 350, "difficulty": "medium"},
        {"par": 3, "distance": 180, "difficulty": "hard"},
        {"par": 5, "distance": 520, "difficulty": "easy"},
        {"par": 4, "distance": 380, "difficulty": "medium"},
        {"par": 3, "distance": 165, "difficulty": "medium"},
        {"par": 4, "distance": 410, "difficulty": "hard"},
        {"par": 5, "distance": 540, "difficulty": "medium"},
        {"par": 4, "distance": 395, "difficulty": "medium"},
        {"par": 3, "distance": 200, "difficulty": "hard"},
        {"par": 4, "distance": 360, "difficulty": "easy"},
        {"par": 5, "distance": 510, "difficulty": "easy"},
        {"par": 4, "distance": 425, "difficulty": "hard"},
        {"par": 3, "distance": 175, "difficulty": "medium"},
        {"par": 4, "distance": 390, "difficulty": "medium"},
        {"par": 4, "distance": 370, "difficulty": "easy"},
        {"par": 3, "distance": 190, "difficulty": "hard"},
        {"par": 5, "distance": 560, "difficulty": "medium"},
        {"par": 4, "distance": 445, "difficulty": "hard"},
    ]
}

CLUBS = {
    "Driver": {"distance": 240, "accuracy": 0.7},
    "3-Wood": {"distance": 220, "accuracy": 0.75},
    "5-Iron": {"distance": 180, "accuracy": 0.8},
    "7-Iron": {"distance": 150, "accuracy": 0.85},
    "9-Iron": {"distance": 120, "accuracy": 0.9},
    "Pitching Wedge": {"distance": 100, "accuracy": 0.92},
    "Sand Wedge": {"distance": 80, "accuracy": 0.88},
    "Putter": {"distance": 30, "accuracy": 0.95},
}

def init_game():
    """Initialize a new game"""
    st.session_state.course_name = "Pine Valley"
    st.session_state.current_hole = 0
    st.session_state.scores = []
    st.session_state.strokes = 0
    st.session_state.distance_remaining = COURSES["Pine Valley"][0]["distance"]
    st.session_state.position = "tee"  # tee, fairway, rough, green, bunker
    st.session_state.shot_history = []
    st.session_state.game_over = False

def calculate_shot(club, power, course_hole):
    """Calculate the result of a shot"""
    club_stats = CLUBS[club]
    base_distance = club_stats["distance"]
    accuracy = club_stats["accuracy"]
    
    # Power affects distance (0.5 to 1.5x)
    distance_multiplier = 0.5 + (power / 100)
    actual_distance = base_distance * distance_multiplier
    
    # Accuracy affects whether shot goes straight
    accuracy_roll = random.random()
    
    # Determine new position
    remaining = st.session_state.distance_remaining - actual_distance
    
    if remaining <= 0:
        # On or past the green
        if club == "Putter":
            # Putting
            putt_success = random.random() < (accuracy + 0.05)
            if putt_success:
                return "hole", 0, "⛳ Ball in the hole!"
            else:
                return "green", abs(remaining) + random.randint(5, 15), "📍 Close! Try another putt."
        else:
            return "green", abs(remaining) + random.randint(10, 30), "🟢 On the green!"
    else:
        # Still approaching
        if accuracy_roll < accuracy:
            # Good shot
            difficulty = course_hole["difficulty"]
            if difficulty == "easy" or accuracy_roll < accuracy * 0.8:
                return "fairway", remaining, "✅ Nice shot! Ball on the fairway."
            else:
                return "rough", remaining, "⚠️ In the rough - harder next shot."
        else:
            # Poor accuracy
            if random.random() < 0.3:
                return "bunker", remaining + random.randint(10, 30), "🏖️ In the bunker!"
            else:
                return "rough", remaining + random.randint(5, 20), "🌿 In the rough!"

def get_position_emoji(position):
    """Get emoji for current position"""
    emojis = {
        "tee": "🏌️",
        "fairway": "🟢",
        "rough": "🌿",
        "green": "🟢",
        "bunker": "🏖️",
        "hole": "⛳"
    }
    return emojis.get(position, "⛳")

# Initialize
if 'current_hole' not in st.session_state:
    init_game()

# Page setup
st.set_page_config(page_title="Golf Game", page_icon="⛳", layout="wide")

st.title("⛳ Golf Game")
st.markdown("**Welcome to Pine Valley Golf Course!**")

# Game over check
if st.session_state.game_over:
    st.success("🎉 Round Complete!")
    
    total_score = sum(st.session_state.scores)
    total_par = sum(hole["par"] for hole in COURSES["Pine Valley"])
    score_vs_par = total_score - total_par
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Score", total_score)
    with col2:
        st.metric("Par", total_par)
    with col3:
        if score_vs_par == 0:
            st.metric("Result", "Even Par!", delta=0)
        elif score_vs_par < 0:
            st.metric("Result", f"{abs(score_vs_par)} Under Par! 🏆", delta=score_vs_par)
        else:
            st.metric("Result", f"{score_vs_par} Over Par", delta=score_vs_par)
    
    st.subheader("📊 Scorecard")
    
    # Display scorecard
    holes_per_row = 9
    for start in range(0, 18, holes_per_row):
        cols = st.columns(holes_per_row)
        for i in range(holes_per_row):
            hole_num = start + i
            if hole_num < 18:
                with cols[i]:
                    hole = COURSES["Pine Valley"][hole_num]
                    score = st.session_state.scores[hole_num]
                    par = hole["par"]
                    diff = score - par
                    
                    if diff == -2:
                        badge = "🦅 Eagle"
                    elif diff == -1:
                        badge = "🐦 Birdie"
                    elif diff == 0:
                        badge = "✅ Par"
                    elif diff == 1:
                        badge = "⚠️ Bogey"
                    else:
                        badge = f"❌ +{diff}"
                    
                    st.metric(f"Hole {hole_num + 1}", f"{score}", delta=f"Par {par}")
                    st.caption(badge)
    
    if st.button("🔄 New Round", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.stop()

# Current hole info
current_hole = COURSES["Pine Valley"][st.session_state.current_hole]
hole_num = st.session_state.current_hole + 1

st.markdown("---")

# Hole info
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Hole", f"{hole_num}/18")
with col2:
    st.metric("Par", current_hole["par"])
with col3:
    st.metric("Distance", f"{current_hole['distance']} yds")
with col4:
    st.metric("Strokes", st.session_state.strokes)

# Current position
st.markdown(f"### {get_position_emoji(st.session_state.position)} Current Position: {st.session_state.position.title()}")
st.progress(min(1.0, 1 - (st.session_state.distance_remaining / current_hole['distance'])))
st.write(f"**{st.session_state.distance_remaining:.0f} yards** to the hole")

# Shot history for this hole
if st.session_state.shot_history:
    with st.expander("📝 Shot History (This Hole)"):
        for i, shot in enumerate(st.session_state.shot_history, 1):
            st.write(f"{i}. {shot}")

st.markdown("---")

# Club selection and shot
if st.session_state.position != "hole":
    st.subheader("🏌️ Take Your Shot")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Recommend club based on distance
        recommended = "Driver"
        for club, stats in CLUBS.items():
            if st.session_state.distance_remaining <= stats["distance"] * 1.2:
                recommended = club
                break
        
        if st.session_state.position == "green":
            recommended = "Putter"
        
        selected_club = st.selectbox(
            "Select Club",
            options=list(CLUBS.keys()),
            index=list(CLUBS.keys()).index(recommended)
        )
        
        club_info = CLUBS[selected_club]
        st.info(f"📏 {selected_club}: ~{club_info['distance']} yards, {int(club_info['accuracy']*100)}% accuracy")
        
        power = st.slider("Shot Power (%)", 50, 100, 90, 5)
        
        estimated_distance = club_info['distance'] * (0.5 + power/100)
        st.caption(f"Estimated distance: {estimated_distance:.0f} yards")
    
    with col2:
        st.write("### 🎯 Course Info")
        difficulty_colors = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        st.write(f"Difficulty: {difficulty_colors[current_hole['difficulty']]} {current_hole['difficulty'].title()}")
        
        if st.session_state.position == "rough":
            st.warning("⚠️ In rough: reduced accuracy")
        elif st.session_state.position == "bunker":
            st.error("🏖️ In bunker: use Sand Wedge!")
    
    if st.button("⛳ Take Shot", use_container_width=True, type="primary"):
        # Calculate shot result
        new_position, new_distance, message = calculate_shot(selected_club, power, current_hole)
        
        st.session_state.strokes += 1
        st.session_state.position = new_position
        st.session_state.distance_remaining = new_distance
        
        # Record shot
        shot_record = f"{selected_club} ({power}%) - {message}"
        st.session_state.shot_history.append(shot_record)
        
        # Check if hole is complete
        if new_position == "hole":
            st.session_state.scores.append(st.session_state.strokes)
            
            # Move to next hole or end game
            if st.session_state.current_hole < 17:
                st.success(f"✅ Hole {hole_num} complete! Score: {st.session_state.strokes} (Par {current_hole['par']})")
                if st.button("➡️ Next Hole"):
                    st.session_state.current_hole += 1
                    st.session_state.strokes = 0
                    next_hole = COURSES["Pine Valley"][st.session_state.current_hole]
                    st.session_state.distance_remaining = next_hole["distance"]
                    st.session_state.position = "tee"
                    st.session_state.shot_history = []
                    st.rerun()
            else:
                st.session_state.game_over = True
                st.rerun()
        else:
            st.rerun()

# Scorecard summary
with st.sidebar:
    st.subheader("📊 Current Scorecard")
    if st.session_state.scores:
        for i, score in enumerate(st.session_state.scores):
            hole = COURSES["Pine Valley"][i]
            diff = score - hole["par"]
            color = "🟢" if diff <= 0 else "🔴" if diff > 1 else "🟡"
            st.write(f"{color} Hole {i+1}: {score} (Par {hole['par']})")
        
        total = sum(st.session_state.scores)
        total_par = sum(COURSES["Pine Valley"][i]["par"] for i in range(len(st.session_state.scores)))
        st.markdown("---")
        st.metric("Total Score", total, delta=total - total_par)
    else:
        st.write("No holes completed yet")
    
    st.markdown("---")
    if st.button("🔄 Restart Round"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
