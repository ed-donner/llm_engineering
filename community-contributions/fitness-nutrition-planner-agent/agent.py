
# agent.py
import os, math, json, copy
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ------------------------------
# Data models
# ------------------------------
class UserProfile(BaseModel):
    sex: str = Field(..., description="male or female")
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str = Field(..., description="sedentary, light, moderate, active, very_active")
    goal: str = Field(..., description="lose, maintain, gain")
    dietary_pattern: Optional[str] = Field(None, description="e.g., vegetarian, vegan, halal, kosher")
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    daily_meals: int = 3
    cuisine_prefs: List[str] = Field(default_factory=list)
    time_per_meal_minutes: int = 30
    budget_level: Optional[str] = Field(None, description="low, medium, high")

class MacroTargets(BaseModel):
    tdee: int
    target_kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int

class Meal(BaseModel):
    name: str
    ingredients: List[Dict[str, Any]]  # {item, qty, unit}
    kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    tags: List[str] = Field(default_factory=list)
    instructions: Optional[str] = None

class DayPlan(BaseModel):
    day: str
    meals: List[Meal]
    totals: MacroTargets

class WeekPlan(BaseModel):
    days: List[DayPlan]
    meta: Dict[str, Any]

# ------------------------------
# Tiny in-memory recipe “DB”
# (extend/replace with a real source)
# ------------------------------
RECIPE_DB: List[Meal] = [
    Meal(
        name="Greek Yogurt Parfait",
        ingredients=[{"item":"nonfat greek yogurt","qty":200,"unit":"g"},
                     {"item":"berries","qty":150,"unit":"g"},
                     {"item":"granola","qty":30,"unit":"g"},
                     {"item":"honey","qty":10,"unit":"g"}],
        kcal=380, protein_g=30, carbs_g=52, fat_g=8,
        tags=["vegetarian","breakfast","5-min","no-cook"]
    ),
    Meal(
        name="Tofu Veggie Stir-Fry with Rice",
        ingredients=[{"item":"firm tofu","qty":150,"unit":"g"},
                     {"item":"mixed vegetables","qty":200,"unit":"g"},
                     {"item":"soy sauce (low sodium)","qty":15,"unit":"ml"},
                     {"item":"olive oil","qty":10,"unit":"ml"},
                     {"item":"brown rice (cooked)","qty":200,"unit":"g"}],
        kcal=650, protein_g=28, carbs_g=85, fat_g=20,
        tags=["vegan","gluten-free","dinner","20-min","stovetop","soy"]
    ),
    Meal(
        name="Chicken Quinoa Bowl",
        ingredients=[{"item":"chicken breast","qty":140,"unit":"g"},
                     {"item":"quinoa (cooked)","qty":185,"unit":"g"},
                     {"item":"spinach","qty":60,"unit":"g"},
                     {"item":"olive oil","qty":10,"unit":"ml"},
                     {"item":"lemon","qty":0.5,"unit":"unit"}],
        kcal=620, protein_g=45, carbs_g=55, fat_g=20,
        tags=["gluten-free","dinner","25-min","high-protein","poultry"]
    ),
    Meal(
        name="Lentil Soup + Wholegrain Bread",
        ingredients=[{"item":"lentils (cooked)","qty":200,"unit":"g"},
                     {"item":"vegetable broth","qty":400,"unit":"ml"},
                     {"item":"carrot","qty":80,"unit":"g"},
                     {"item":"celery","qty":60,"unit":"g"},
                     {"item":"onion","qty":60,"unit":"g"},
                     {"item":"wholegrain bread","qty":60,"unit":"g"}],
        kcal=520, protein_g=25, carbs_g=78, fat_g=8,
        tags=["vegan","lunch","30-min","budget"]
    ),
    Meal(
        name="Salmon, Potatoes & Greens",
        ingredients=[{"item":"salmon fillet","qty":150,"unit":"g"},
                     {"item":"potatoes","qty":200,"unit":"g"},
                     {"item":"broccoli","qty":150,"unit":"g"},
                     {"item":"olive oil","qty":10,"unit":"ml"}],
        kcal=680, protein_g=42, carbs_g=52, fat_g=30,
        tags=["gluten-free","dinner","omega-3","fish"]
    ),
    Meal(
        name="Cottage Cheese Bowl",
        ingredients=[{"item":"low-fat cottage cheese","qty":200,"unit":"g"},
                     {"item":"pineapple","qty":150,"unit":"g"},
                     {"item":"chia seeds","qty":15,"unit":"g"}],
        kcal=380, protein_g=32, carbs_g=35, fat_g=10,
        tags=["vegetarian","snack","5-min","high-protein","dairy"]
    ),
]

# ------------------------------
# Tool implementations
# ------------------------------
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9
}

def mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    # BMR (kcal/day)
    if sex.lower().startswith("m"):
        return 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        return 10*weight_kg + 6.25*height_cm - 5*age - 161

def compute_targets(profile: UserProfile) -> MacroTargets:
    bmr = mifflin_st_jeor(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
    tdee = int(round(bmr * ACTIVITY_FACTORS.get(profile.activity_level, 1.2)))
    # goal adjustment
    if profile.goal == "lose":
        target_kcal = max(1200, int(tdee - 400))  # conservative deficit
    elif profile.goal == "gain":
        target_kcal = int(tdee + 300)
    else:
        target_kcal = tdee

    # Macro split (modifiable): P 30%, C 40%, F 30%
    protein_kcal = target_kcal * 0.30
    carbs_kcal   = target_kcal * 0.40
    fat_kcal     = target_kcal * 0.30
    protein_g = int(round(protein_kcal / 4))
    carbs_g   = int(round(carbs_kcal / 4))
    fat_g     = int(round(fat_kcal / 9))

    return MacroTargets(tdee=tdee, target_kcal=target_kcal,
                        protein_g=protein_g, carbs_g=carbs_g, fat_g=fat_g)

def _allowed(meal: Meal, profile: UserProfile) -> bool:
    # dietary patterns/allergies/dislikes filters (simple; extend as needed)
    diet = (profile.dietary_pattern or "").lower()
    if diet == "vegetarian" and ("fish" in meal.tags or "poultry" in meal.tags):
        return False
    if diet == "vegan" and ("dairy" in meal.tags or "fish" in meal.tags or "poultry" in meal.tags):
        return False
    # allergies & dislikes
    for a in profile.allergies:
        if a and a.lower() in meal.name.lower(): return False
        if any(a.lower() in (ing["item"]).lower() for ing in meal.ingredients): return False
        if a.lower() in " ".join(meal.tags).lower(): return False
    for d in profile.dislikes:
        if d and d.lower() in meal.name.lower(): return False
        if any(d.lower() in (ing["item"]).lower() for ing in meal.ingredients): return False
    return True

def meal_db_search(profile: UserProfile, tags: Optional[List[str]] = None) -> List[Meal]:
    tags = tags or []
    out = []
    for m in RECIPE_DB:
        if not _allowed(m, profile):
            continue
        if tags and not any(t in m.tags for t in tags):
            continue
        out.append(m)
    return out or []  # may be empty; agent should handle

def compose_meal_plan(profile: UserProfile, targets: MacroTargets) -> WeekPlan:
    # naive heuristic: pick meals that roughly match per-meal macro budget
    per_meal_kcal = targets.target_kcal / profile.daily_meals
    days = []
    weekdays = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    # simple pools
    breakfasts = meal_db_search(profile, tags=["breakfast","no-cook","5-min"])
    lunches = meal_db_search(profile, tags=["lunch","budget"])
    dinners = meal_db_search(profile, tags=["dinner","high-protein"])

    # fallback to any allowed meals if pools too small
    allowed_all = meal_db_search(profile)
    if len(breakfasts) < 2: breakfasts = allowed_all
    if len(lunches) < 2: lunches = allowed_all
    if len(dinners) < 2: dinners = allowed_all

    for i, day in enumerate(weekdays):
        day_meals = []
        for slot in range(profile.daily_meals):
            pool = breakfasts if slot == 0 else (lunches if slot == 1 else dinners)
            # pick the meal closest in kcal to per_meal_kcal
            pick = min(pool, key=lambda m: abs(m.kcal - per_meal_kcal))
            day_meals.append(copy.deepcopy(pick))
        # compute totals
        kcal = sum(m.kcal for m in day_meals)
        p = sum(m.protein_g for m in day_meals)
        c = sum(m.carbs_g for m in day_meals)
        f = sum(m.fat_g for m in day_meals)
        day_targets = MacroTargets(tdee=targets.tdee, target_kcal=int(round(kcal)),
                                   protein_g=p, carbs_g=c, fat_g=f)
        days.append(DayPlan(day=day, meals=day_meals, totals=day_targets))
    return WeekPlan(days=days, meta={"per_meal_target_kcal": int(round(per_meal_kcal))})

def grocery_list_from_plan(plan: WeekPlan) -> List[Dict[str, Any]]:
    # aggregate identical ingredients
    agg: Dict[Tuple[str,str], float] = {}
    units: Dict[Tuple[str,str], str] = {}
    for d in plan.days:
        for m in d.meals:
            for ing in m.ingredients:
                key = (ing["item"].lower(), ing.get("unit",""))
                agg[key] = agg.get(key, 0) + float(ing.get("qty", 0))
                units[key] = ing.get("unit","")
    items = []
    for (item, unit), qty in sorted(agg.items()):
        items.append({"item": item, "qty": round(qty, 2), "unit": unit})
    return items

def swap_meal(plan: WeekPlan, day: str, meal_index: int, profile: UserProfile) -> WeekPlan:
    # replace one meal by closest-kcal allowed alternative that isn't the same
    day_idx = next((i for i,d in enumerate(plan.days) if d.day.lower().startswith(day[:3].lower())), None)
    if day_idx is None: return plan
    current_meal = plan.days[day_idx].meals[meal_index]
    candidates = [m for m in meal_db_search(profile) if m.name != current_meal.name]
    if not candidates: return plan
    pick = min(candidates, key=lambda m: abs(m.kcal - current_meal.kcal))
    plan.days[day_idx].meals[meal_index] = copy.deepcopy(pick)
    # recalc day totals
    d = plan.days[day_idx]
    kcal = sum(m.kcal for m in d.meals)
    p = sum(m.protein_g for m in d.meals)
    c = sum(m.carbs_g for m in d.meals)
    f = sum(m.fat_g for m in d.meals)
    d.totals = MacroTargets(tdee=d.totals.tdee, target_kcal=kcal, protein_g=p, carbs_g=c, fat_g=f)
    return plan

# ------------------------------
# Agent (LLM + tools)
# ------------------------------
SYS_PROMPT = """You are FitnessPlanner, an agentic planner that:
- Respects dietary patterns, allergies, dislikes, budget, time limits.
- Uses tools to compute targets, assemble a 7-day plan, produce a grocery list, and swap meals on request.
- If a request is unsafe (extreme deficits, medical conditions), warn and suggest professional guidance.
- Keep responses concise and structured (headings + bullet lists)."""

# Tool registry for function-calling
def get_tools_schema():
    return [
        {
            "type": "function",
            "function": {
                "name": "calc_calories_and_macros",
                "description": "Compute TDEE and macro targets from the user's profile.",
                "parameters": {
                    "type":"object",
                    "properties": {"profile":{"type":"object"}},
                    "required":["profile"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compose_meal_plan",
                "description": "Create a 7-day meal plan matching targets and constraints.",
                "parameters": {
                    "type":"object",
                    "properties": {
                        "profile":{"type":"object"},
                        "targets":{"type":"object"}
                    },
                    "required":["profile","targets"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "grocery_list_from_plan",
                "description": "Make a consolidated grocery list from a week plan.",
                "parameters": {
                    "type":"object",
                    "properties": {"plan":{"type":"object"}},
                    "required":["plan"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "swap_meal",
                "description": "Swap a single meal in the plan while keeping macros reasonable.",
                "parameters": {
                    "type":"object",
                    "properties": {
                        "plan":{"type":"object"},
                        "day":{"type":"string"},
                        "meal_index":{"type":"integer","description":"0=breakfast,1=lunch,2=dinner"},
                        "profile":{"type":"object"}
                    },
                    "required":["plan","day","meal_index","profile"]
                }
            }
        }
    ]

class FitnessPlannerAgent:
    def __init__(self, model: Optional[str] = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.plan_cache: Optional[WeekPlan] = None
        self.targets_cache: Optional[MacroTargets] = None

    # Tool dispatch
    def _call_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name == "calc_calories_and_macros":
            profile = UserProfile(**args["profile"])
            targets = compute_targets(profile)
            self.targets_cache = targets
            return targets.model_dump_json()
        elif name == "compose_meal_plan":
            profile = UserProfile(**args["profile"])
            targets = MacroTargets(**args["targets"])
            plan = compose_meal_plan(profile, targets)
            self.plan_cache = plan
            return plan.model_dump_json()
        elif name == "grocery_list_from_plan":
            plan = WeekPlan(**args["plan"])
            items = grocery_list_from_plan(plan)
            return json.dumps(items)
        elif name == "swap_meal":
            plan = WeekPlan(**args["plan"])
            profile = UserProfile(**args["profile"])
            day = args["day"]
            idx = args["meal_index"]
            new_plan = swap_meal(plan, day, idx, profile)
            self.plan_cache = new_plan
            return new_plan.model_dump_json()
        else:
            return json.dumps({"error":"unknown tool"})

    def chat(self, user_message: str, profile: Optional[UserProfile] = None) -> str:
        messages = [{"role":"system","content":SYS_PROMPT}]
        if profile:
            messages.append({"role":"user","content":f"User profile: {profile.model_dump_json()}"} )
        messages.append({"role":"user","content":user_message})

        # First call
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=get_tools_schema(),
            tool_choice="auto",
            temperature=0.3
        )

        # Handle tool calls (simple, single-step or brief multi-step)
        messages_llm = messages + [{"role":"assistant","content":resp.choices[0].message.content or "",
                                    "tool_calls":resp.choices[0].message.tool_calls}]
        if resp.choices[0].message.tool_calls:
            for tc in resp.choices[0].message.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                out = self._call_tool(name, args)
                messages_llm.append({
                    "role":"tool",
                    "tool_call_id":tc.id,
                    "name":name,
                    "content":out
                })

            # Finalization
            resp2 = self.client.chat.completions.create(
                model=self.model,
                messages=messages_llm,
                temperature=0.2
            )
            return resp2.choices[0].message.content

        return resp.choices[0].message.content

# ------------------------------
# Quick CLI demo
# ------------------------------
if __name__ == "__main__":
    profile = UserProfile(
        sex="female", age=45, height_cm=152, weight_kg=62,
        activity_level="light", goal="maintain",
        dietary_pattern="vegetarian", allergies=[], dislikes=[],
        daily_meals=3, cuisine_prefs=["mediterranean"], time_per_meal_minutes=25, budget_level="medium"
    )
    agent = FitnessPlannerAgent()
    print(agent.chat("Create my 7-day plan and grocery list.", profile))
