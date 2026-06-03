
# app.py
import json
import streamlit as st
from agent import FitnessPlannerAgent, UserProfile, WeekPlan

st.set_page_config(page_title="Fitness & Nutrition Planner Agent", layout="wide")

st.title("🏋️ Fitness & Nutrition Planner Agent")

with st.sidebar:
    st.header("Your Profile")
    sex = st.selectbox("Sex", ["female","male"])
    age = st.number_input("Age", 18, 90, 45)
    height_cm = st.number_input("Height (cm)", 120, 220, 152)
    weight_kg = st.number_input("Weight (kg)", 35.0, 200.0, 62.0)
    activity_level = st.selectbox("Activity Level", ["sedentary","light","moderate","active","very_active"], index=1)
    goal = st.selectbox("Goal", ["lose","maintain","gain"], index=1)
    dietary_pattern = st.selectbox("Dietary Pattern", ["none","vegetarian","vegan","halal","kosher"], index=1)
    if dietary_pattern == "none": dietary_pattern = None
    allergies = st.text_input("Allergies (comma-separated)", "")
    dislikes = st.text_input("Dislikes (comma-separated)", "")
    daily_meals = st.slider("Meals per day", 2, 5, 3)
    time_per_meal_minutes = st.slider("Time per meal (min)", 5, 90, 25)
    budget_level = st.selectbox("Budget", ["medium","low","high"], index=0)
    cuisine_prefs = st.text_input("Cuisine prefs (comma-separated)", "mediterranean")

    build_btn = st.button("Generate 7-Day Plan")

agent = FitnessPlannerAgent()

if build_btn:
    profile = UserProfile(
        sex=sex, age=int(age), height_cm=float(height_cm), weight_kg=float(weight_kg),
        activity_level=activity_level, goal=goal, dietary_pattern=dietary_pattern,
        allergies=[a.strip() for a in allergies.split(",") if a.strip()],
        dislikes=[d.strip() for d in dislikes.split(",") if d.strip()],
        daily_meals=int(daily_meals), cuisine_prefs=[c.strip() for c in cuisine_prefs.split(",") if c.strip()],
        time_per_meal_minutes=int(time_per_meal_minutes), budget_level=budget_level
    )
    st.session_state["profile_json"] = profile.model_dump_json()
    with st.spinner("Planning your week..."):
        result = agent.chat("Create my 7-day plan and grocery list.", profile)
    st.session_state["last_response"] = result

if "last_response" in st.session_state:
    st.subheader("Plan & Groceries")
    st.markdown(st.session_state["last_response"])

st.divider()
st.subheader("Tweaks")
col1, col2, col3 = st.columns(3)
with col1:
    day = st.selectbox("Day to change", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
with col2:
    meal_index = st.selectbox("Meal slot", ["Breakfast (0)","Lunch (1)","Dinner (2)"])
    meal_index = int(meal_index[-2])  # 0/1/2
with col3:
    swap_btn = st.button("Swap Meal")

if swap_btn and agent.plan_cache:
    profile_json = st.session_state.get("profile_json")
    if not profile_json:
        st.warning("Please generate a plan first.")
    else:
        new_plan_json = agent._call_tool("swap_meal", {
            "plan": agent.plan_cache.model_dump(),
            "day": day,
            "meal_index": meal_index,
            "profile": json.loads(profile_json)
        })
        agent.plan_cache = WeekPlan(**json.loads(new_plan_json))
        summary = agent.chat(f"Update summary for {day}: show the swapped meal and new day totals.")
        st.session_state["last_response"] = summary
        st.markdown(summary)
