from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Any, Tuple

from flask import Flask, jsonify, render_template, request


app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)


@dataclass
class UserProfile:
    age: int
    sex: str  # "male" or "female"
    height_cm: float
    weight_kg: float
    activity_level: str  # sedentary, light, moderate, active, very_active
    goal: str  # lose, maintain, gain
    weekly_change_kg: float  # positive number, interpreted by goal
    dietary_preference: str | None = None


ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def calculate_bmr(profile: UserProfile) -> float:
    # Mifflin-St Jeor Equation
    if profile.sex.lower() == "male":
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age + 5
    else:
        return 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age - 161


def activity_factor(level: str) -> float:
    return ACTIVITY_FACTORS.get(level.lower(), 1.55)


def compute_target_calories(profile: UserProfile) -> Tuple[float, float, float]:
    bmr = calculate_bmr(profile)
    tdee = bmr * activity_factor(profile.activity_level)

    # safe bounds
    min_cal_by_sex = 1500 if profile.sex.lower() == "male" else 1200
    min_cal_safe = max(min_cal_by_sex, bmr * 1.1)
    max_cal_safe = tdee + 800  # reasonable surplus upper bound

    if profile.goal == "maintain":
        target = tdee
    else:
        # 1 kg fat ≈ 7700 kcal
        daily_delta = (profile.weekly_change_kg * 7700) / 7.0
        # clamp aggressive changes
        if profile.goal == "lose":
            daily_delta = clamp(daily_delta, 0, 1000)  # cap deficit at 1000 kcal/day
            target = tdee - daily_delta
        else:  # gain
            daily_delta = clamp(daily_delta, 0, 800)  # cap surplus
            target = tdee + daily_delta

    target = clamp(target, min_cal_safe, max_cal_safe)
    return bmr, tdee, target


def compute_macros(profile: UserProfile, calories: float) -> Dict[str, Any]:
    # Protein and fat set by weight; carbs fill remaining
    weight = profile.weight_kg
    if profile.goal == "lose":
        protein_g = 2.0 * weight
        fat_g = 0.8 * weight
    elif profile.goal == "gain":
        protein_g = 1.8 * weight
        fat_g = 1.0 * weight
    else:
        protein_g = 1.6 * weight
        fat_g = 0.9 * weight

    # Adjust for dietary preference
    pref = (profile.dietary_preference or "balanced").lower()
    if pref in ("high_protein", "keto", "low_carb"):
        protein_g *= 1.1
    if pref in ("keto", "low_carb"):
        fat_g *= 1.1

    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9
    remaining_kcal = max(0.0, calories - protein_kcal - fat_kcal)
    carbs_g = remaining_kcal / 4

    # Round sensibly
    def r(x: float) -> int:
        return int(round(x))

    total_from_macros = protein_kcal + fat_kcal + carbs_g * 4

    return {
        "protein_g": r(protein_g),
        "fat_g": r(fat_g),
        "carbs_g": r(carbs_g),
        "calories_from_macros": r(total_from_macros),
    }


def build_daily_plan(profile: UserProfile, calories: float) -> Dict[str, Any]:
    macros = compute_macros(profile, calories)

    # Simple lifestyle suggestions
    steps_target = 8000 if profile.goal == "lose" else 7000
    water_liters = max(2.0, round(profile.weight_kg * 0.03, 1))

    # Provide a simple split into 3 meals + 1 snack
    meal_split = {
        "breakfast": 0.25,
        "lunch": 0.35,
        "snack": 0.1,
        "dinner": 0.30,
    }
    meals = {
        name: int(round(calories * frac)) for name, frac in meal_split.items()
    }

    return {
        "calories": int(round(calories)),
        "macros": macros,
        "meals": meals,
        "steps_target": steps_target,
        "water_liters": water_liters,
        "notes": _build_notes(profile),
    }


def _build_notes(profile: UserProfile) -> list[str]:
    notes = [
        "Prioritize whole foods and consistent meal times.",
        "Aim for 7-9 hours of sleep; it impacts hunger and recovery.",
        "Progressive overload strength training 2-3x/week supports fat loss.",
    ]
    if profile.goal == "lose":
        notes.append("A sustainable loss rate is 0.25–0.75 kg per week.")
    if (profile.dietary_preference or "").lower() in ("vegetarian", "vegan"):
        notes.append("Ensure adequate B12/iron sources; favor legumes, tofu, tempeh.")
    return notes


def build_week_plan(daily: Dict[str, Any]) -> Dict[str, Any]:
    # Add small day-to-day variation for realism
    base = daily["calories"]
    spread = [-100, -50, 0, 0, 50, 75, -25]
    days = [
        {
            "day": i + 1,
            "calories": base + spread[i],
        }
        for i in range(7)
    ]
    return {
        "days": days,
        "avg_calories": int(round(sum(d["calories"] for d in days) / 7)),
    }


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/plan")
def plan_api():
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}

    try:
        profile = UserProfile(
            age=int(data.get("age", 30)),
            sex=str(data.get("sex", "male")).lower(),
            height_cm=float(data.get("height_cm", 175)),
            weight_kg=float(data.get("weight_kg", 70)),
            activity_level=str(data.get("activity_level", "moderate")).lower(),
            goal=str(data.get("goal", "lose")).lower(),
            weekly_change_kg=abs(float(data.get("weekly_change_kg", 0.5))),
            dietary_preference=(data.get("dietary_preference") or "balanced"),
        )
        if profile.sex not in ("male", "female"):
            raise ValueError("sex must be 'male' or 'female'")
        if profile.activity_level not in ACTIVITY_FACTORS:
            raise ValueError("invalid activity_level")
        if profile.goal not in ("lose", "maintain", "gain"):
            raise ValueError("invalid goal")
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400

    bmr, tdee, target = compute_target_calories(profile)
    daily = build_daily_plan(profile, target)
    week = build_week_plan(daily)

    response = {
        "inputs": {
            "age": profile.age,
            "sex": profile.sex,
            "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg,
            "activity_level": profile.activity_level,
            "goal": profile.goal,
            "weekly_change_kg": profile.weekly_change_kg,
            "dietary_preference": profile.dietary_preference,
        },
        "metrics": {
            "bmr": int(round(bmr)),
            "tdee": int(round(tdee)),
            "target_calories": daily["calories"],
        },
        "daily_plan": daily,
        "week_plan": week,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

