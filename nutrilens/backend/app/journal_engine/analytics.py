"""
NutriLens – Food Journal Analytics Engine (Day 8)
Computes daily summaries, weekly/monthly longitudinal aggregations,
and user-goal comparisons without fabricating medical targets.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.journal import FoodJournalEntry
from app.models.product import Product
from app.models.user import UserProfile
from app.schemas.journal import (
    CalculatedNutrients,
    JournalEntryResponse,
    DailyMealGroup,
    NutrientTotalDetail,
    GoalProgressItem,
    DailyJournalSummaryResponse,
    DailyTrendItem,
    WeeklyAnalyticsResponse,
    MonthlyAnalyticsResponse,
    FrequentProductItem,
    FrequentProductsResponse,
)
from app.journal_engine.calculator import calculate_entry_nutrients, NUTRIENT_FIELDS

DISCLAIMER_TEXT = (
    "NutriLens nutritional benchmarks reflect general population reference intakes "
    "(such as standard WHO and ICMR-NIN guidelines) and do not constitute medical advice, "
    "therapeutic prescriptions, or diagnostic recommendations."
)

MEAL_CONFIG = [
    ("breakfast", "Breakfast"),
    ("lunch", "Lunch"),
    ("dinner", "Dinner"),
    ("snack", "Snacks"),
    ("other", "Other"),
]


def entry_to_response(entry: FoodJournalEntry) -> JournalEntryResponse:
    """Transforms a FoodJournalEntry database model into JournalEntryResponse with scaled nutrients."""
    nutrients = calculate_entry_nutrients(
        nutrition_facts=entry.product.nutrition_facts if entry.product else None,
        total_weight_g=entry.total_weight_g,
    )

    return JournalEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        product_id=entry.product_id,
        product_name=entry.product.name if entry.product else "Unknown Product",
        product_brand=entry.product.brand if entry.product else None,
        product_category=entry.product.category if entry.product else None,
        product_image_url=entry.product.label_image_url if entry.product else None,
        consumed_at=entry.consumed_at,
        meal_type=entry.meal_type or "snack",
        quantity=entry.quantity,
        serving_unit=entry.serving_unit,
        serving_size_g=entry.serving_size_g,
        total_weight_g=entry.total_weight_g,
        notes=entry.notes,
        nutrients=nutrients,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def build_daily_summary(
    entries: List[FoodJournalEntry],
    target_date: str,
    user_profile: Optional[UserProfile] = None,
) -> DailyJournalSummaryResponse:
    """
    Builds the daily nutritional summary, grouped by meal type, with complete totals
    and transparent accounting of declared vs missing nutrients.
    """
    meals_dict: Dict[str, DailyMealGroup] = {}
    for key, label in MEAL_CONFIG:
        meals_dict[key] = DailyMealGroup(
            meal_type=key,
            label=label,
            entries=[],
            total_calories=0.0,
            total_weight_g=0.0,
        )

    # Accumulators for nutrients
    nutrient_sums: Dict[str, float] = {field: 0.0 for field, _ in NUTRIENT_FIELDS}
    nutrient_declared: Dict[str, int] = {field: 0 for field, _ in NUTRIENT_FIELDS}
    nutrient_missing: Dict[str, int] = {field: 0 for field, _ in NUTRIENT_FIELDS}

    total_weight = 0.0

    for entry in entries:
        resp = entry_to_response(entry)
        meal_key = (entry.meal_type or "snack").lower()
        if meal_key not in meals_dict:
            meal_key = "other"

        meals_dict[meal_key].entries.append(resp)
        meals_dict[meal_key].total_weight_g = round(meals_dict[meal_key].total_weight_g + entry.total_weight_g, 2)
        total_weight = round(total_weight + entry.total_weight_g, 2)

        if resp.nutrients.energy_kcal is not None:
            meals_dict[meal_key].total_calories = round(
                meals_dict[meal_key].total_calories + resp.nutrients.energy_kcal, 1
            )

        # Accumulate each nutrient
        for field, _ in NUTRIENT_FIELDS:
            val = getattr(resp.nutrients, field, None)
            if val is not None:
                nutrient_sums[field] += val
                nutrient_declared[field] += 1
            else:
                nutrient_missing[field] += 1

    # Format nutrient details
    nutrient_units = {
        "energy_kcal": "kcal",
        "total_fat_g": "g",
        "saturated_fat_g": "g",
        "trans_fat_g": "g",
        "cholesterol_mg": "mg",
        "carbohydrates_g": "g",
        "total_sugar_g": "g",
        "added_sugar_g": "g",
        "dietary_fibre_g": "g",
        "protein_g": "g",
        "sodium_mg": "mg",
        "calcium_mg": "mg",
        "iron_mg": "mg",
        "vitamin_c_mg": "mg",
    }

    totals: Dict[str, NutrientTotalDetail] = {}
    for field, _ in NUTRIENT_FIELDS:
        decl = nutrient_declared[field]
        miss = nutrient_missing[field]
        if decl > 0:
            total_val = round(nutrient_sums[field], 1 if field == "energy_kcal" else 2)
        else:
            total_val = None

        totals[field] = NutrientTotalDetail(
            total=total_val,
            unit=nutrient_units.get(field, "g"),
            declared_items=decl,
            missing_items=miss,
        )

    # Evaluate goal progress against user profile preferences
    goal_progress: List[GoalProgressItem] = []
    active_goals = []
    if user_profile and user_profile.nutrition_goals:
        active_goals = [str(g).lower() for g in user_profile.nutrition_goals]

    monitored = []
    if user_profile and user_profile.monitored_nutrients:
        monitored = [str(m).lower() for m in user_profile.monitored_nutrients]

    # Evaluate Sugar
    if any("sugar" in g for g in active_goals) or "sugar" in monitored:
        sugar_tot = totals["total_sugar_g"].total
        if sugar_tot is not None:
            if sugar_tot <= 50.0:
                st = "on_track"
                msg = f"Logged sugar ({sugar_tot}g) is within standard general population reference limit (≤ 50g)."
            elif sugar_tot <= 65.0:
                st = "caution"
                msg = f"Logged sugar ({sugar_tot}g) is approaching general reference limit (≤ 50g)."
            else:
                st = "exceeded"
                msg = f"Logged sugar ({sugar_tot}g) exceeds the general guideline reference benchmark (≤ 50g)."
            goal_progress.append(
                GoalProgressItem(
                    goal_key="low_sugar",
                    goal_label="Low Sugar",
                    current_value=sugar_tot,
                    target_benchmark=50.0,
                    unit="g",
                    status=st,
                    message=msg,
                )
            )

    # Evaluate Sodium
    if any("sodium" in g for g in active_goals) or "sodium" in monitored:
        sod_tot = totals["sodium_mg"].total
        if sod_tot is not None:
            if sod_tot <= 2000.0:
                st = "on_track"
                msg = f"Logged sodium ({sod_tot}mg) is within standard WHO guideline benchmark (≤ 2000mg)."
            elif sod_tot <= 2300.0:
                st = "caution"
                msg = f"Logged sodium ({sod_tot}mg) is near the upper limit benchmark (≤ 2000mg)."
            else:
                st = "exceeded"
                msg = f"Logged sodium ({sod_tot}mg) exceeds standard guideline reference benchmark (≤ 2000mg)."
            goal_progress.append(
                GoalProgressItem(
                    goal_key="low_sodium",
                    goal_label="Low Sodium",
                    current_value=sod_tot,
                    target_benchmark=2000.0,
                    unit="mg",
                    status=st,
                    message=msg,
                )
            )

    # Evaluate Protein
    if any("protein" in g for g in active_goals) or "protein" in monitored:
        prot_tot = totals["protein_g"].total
        if prot_tot is not None:
            if prot_tot >= 50.0:
                st = "on_track"
                msg = f"Logged protein ({prot_tot}g) meets general adult reference guideline (≥ 50g)."
            elif prot_tot >= 30.0:
                st = "caution"
                msg = f"Moderate protein logged ({prot_tot}g); general adult reference guideline is ≥ 50g."
            else:
                st = "info"
                msg = f"Logged protein ({prot_tot}g) is below the general adult reference target (≥ 50g)."
            goal_progress.append(
                GoalProgressItem(
                    goal_key="high_protein",
                    goal_label="High Protein",
                    current_value=prot_tot,
                    target_benchmark=50.0,
                    unit="g",
                    status=st,
                    message=msg,
                )
            )

    # Evaluate Fibre
    if any("fiber" in g or "fibre" in g for g in active_goals) or "fibre" in monitored or "fiber" in monitored:
        fib_tot = totals["dietary_fibre_g"].total
        if fib_tot is not None:
            if fib_tot >= 25.0:
                st = "on_track"
                msg = f"Logged dietary fibre ({fib_tot}g) meets standard adult reference guideline (≥ 25g)."
            elif fib_tot >= 15.0:
                st = "caution"
                msg = f"Moderate dietary fibre logged ({fib_tot}g); below the recommended 25g daily reference."
            else:
                st = "info"
                msg = f"Logged fibre ({fib_tot}g) is below standard adult reference guideline (≥ 25g)."
            goal_progress.append(
                GoalProgressItem(
                    goal_key="high_fiber",
                    goal_label="High Fibre",
                    current_value=fib_tot,
                    target_benchmark=25.0,
                    unit="g",
                    status=st,
                    message=msg,
                )
            )

    # Evaluate Saturated Fat
    if any("fat" in g for g in active_goals) or "fat" in monitored:
        sat_tot = totals["saturated_fat_g"].total
        if sat_tot is not None:
            if sat_tot <= 20.0:
                st = "on_track"
                msg = f"Logged saturated fat ({sat_tot}g) is within standard guideline limit (≤ 20g)."
            else:
                st = "caution"
                msg = f"Logged saturated fat ({sat_tot}g) exceeds general reference limit (≤ 20g)."
            goal_progress.append(
                GoalProgressItem(
                    goal_key="low_fat",
                    goal_label="Low Saturated Fat",
                    current_value=sat_tot,
                    target_benchmark=20.0,
                    unit="g",
                    status=st,
                    message=msg,
                )
            )

    return DailyJournalSummaryResponse(
        date=target_date,
        total_entries=len(entries),
        total_weight_g=total_weight,
        meals=meals_dict,
        totals=totals,
        goal_progress=goal_progress,
        disclaimer=DISCLAIMER_TEXT,
    )


def build_weekly_analytics(
    entries: List[FoodJournalEntry],
    start_date: date,
    end_date: date,
) -> WeeklyAnalyticsResponse:
    """
    Computes 7-day longitudinal daily trend series and average consumption metrics.
    """
    # Group entries by date
    days_map: Dict[str, List[FoodJournalEntry]] = {}
    curr = start_date
    while curr <= end_date:
        days_map[curr.isoformat()] = []
        curr += timedelta(days=1)

    for entry in entries:
        d_str = entry.consumed_at.strftime("%Y-%m-%d") if isinstance(entry.consumed_at, datetime) else str(entry.consumed_at)[:10]
        if d_str in days_map:
            days_map[d_str].append(entry)

    daily_trends: List[DailyTrendItem] = []
    tot_calories: List[float] = []
    tot_sugar: List[float] = []
    tot_sodium: List[float] = []
    tot_protein: List[float] = []
    tot_fibre: List[float] = []
    tot_fat: List[float] = []
    tot_carbs: List[float] = []

    active_days_count = 0
    total_meals_count = 0

    for d_str in sorted(days_map.keys()):
        d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
        day_entries = days_map[d_str]
        total_meals_count += len(day_entries)
        if day_entries:
            active_days_count += 1

        cal_sum = 0.0
        cal_count = 0
        sug_sum = 0.0
        sug_count = 0
        sod_sum = 0.0
        sod_count = 0
        pro_sum = 0.0
        pro_count = 0
        fib_sum = 0.0
        fib_count = 0
        fat_sum = 0.0
        fat_count = 0
        car_sum = 0.0
        car_count = 0

        for e in day_entries:
            nutrients = calculate_entry_nutrients(
                nutrition_facts=e.product.nutrition_facts if e.product else None,
                total_weight_g=e.total_weight_g,
            )
            if nutrients.energy_kcal is not None:
                cal_sum += nutrients.energy_kcal
                cal_count += 1
            if nutrients.total_sugar_g is not None:
                sug_sum += nutrients.total_sugar_g
                sug_count += 1
            if nutrients.sodium_mg is not None:
                sod_sum += nutrients.sodium_mg
                sod_count += 1
            if nutrients.protein_g is not None:
                pro_sum += nutrients.protein_g
                pro_count += 1
            if nutrients.dietary_fibre_g is not None:
                fib_sum += nutrients.dietary_fibre_g
                fib_count += 1
            if nutrients.total_fat_g is not None:
                fat_sum += nutrients.total_fat_g
                fat_count += 1
            if nutrients.carbohydrates_g is not None:
                car_sum += nutrients.carbohydrates_g
                car_count += 1

        cal_val = round(cal_sum, 1) if cal_count > 0 else (0.0 if not day_entries else None)
        sug_val = round(sug_sum, 2) if sug_count > 0 else (0.0 if not day_entries else None)
        sod_val = round(sod_sum, 2) if sod_count > 0 else (0.0 if not day_entries else None)
        pro_val = round(pro_sum, 2) if pro_count > 0 else (0.0 if not day_entries else None)
        fib_val = round(fib_sum, 2) if fib_count > 0 else (0.0 if not day_entries else None)
        fat_val = round(fat_sum, 2) if fat_count > 0 else (0.0 if not day_entries else None)
        car_val = round(car_sum, 2) if car_count > 0 else (0.0 if not day_entries else None)

        if cal_val is not None and cal_val > 0:
            tot_calories.append(cal_val)
        if sug_val is not None and sug_val > 0:
            tot_sugar.append(sug_val)
        if sod_val is not None and sod_val > 0:
            tot_sodium.append(sod_val)
        if pro_val is not None and pro_val > 0:
            tot_protein.append(pro_val)
        if fib_val is not None and fib_val > 0:
            tot_fibre.append(fib_val)
        if fat_val is not None and fat_val > 0:
            tot_fat.append(fat_val)
        if car_val is not None and car_val > 0:
            tot_carbs.append(car_val)

        daily_trends.append(
            DailyTrendItem(
                date=d_str,
                day_name=d_obj.strftime("%a"),
                entry_count=len(day_entries),
                calories=cal_val,
                sugar_g=sug_val,
                sodium_mg=sod_val,
                protein_g=pro_val,
                fibre_g=fib_val,
                fat_g=fat_val,
                carbs_g=car_val,
            )
        )

    divisor = max(1, active_days_count)
    averages = {
        "calories": round(sum(tot_calories) / divisor, 1) if tot_calories else None,
        "sugar_g": round(sum(tot_sugar) / divisor, 2) if tot_sugar else None,
        "sodium_mg": round(sum(tot_sodium) / divisor, 2) if tot_sodium else None,
        "protein_g": round(sum(tot_protein) / divisor, 2) if tot_protein else None,
        "fibre_g": round(sum(tot_fibre) / divisor, 2) if tot_fibre else None,
        "fat_g": round(sum(tot_fat) / divisor, 2) if tot_fat else None,
        "carbs_g": round(sum(tot_carbs) / divisor, 2) if tot_carbs else None,
    }

    return WeeklyAnalyticsResponse(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        daily_trends=daily_trends,
        averages=averages,
        active_days=active_days_count,
        total_logged_meals=total_meals_count,
        disclaimer=DISCLAIMER_TEXT,
    )


def build_monthly_analytics(
    entries: List[FoodJournalEntry],
    year: int,
    month: int,
    start_date: date,
    end_date: date,
) -> MonthlyAnalyticsResponse:
    """
    Computes monthly longitudinal daily trend series and average consumption metrics.
    """
    days_map: Dict[str, List[FoodJournalEntry]] = {}
    curr = start_date
    while curr <= end_date:
        days_map[curr.isoformat()] = []
        curr += timedelta(days=1)

    for entry in entries:
        d_str = entry.consumed_at.strftime("%Y-%m-%d") if isinstance(entry.consumed_at, datetime) else str(entry.consumed_at)[:10]
        if d_str in days_map:
            days_map[d_str].append(entry)

    daily_trends: List[DailyTrendItem] = []
    tot_calories: List[float] = []
    tot_sugar: List[float] = []
    tot_sodium: List[float] = []
    tot_protein: List[float] = []
    tot_fibre: List[float] = []

    active_days_count = 0
    total_meals_count = 0

    for d_str in sorted(days_map.keys()):
        d_obj = datetime.strptime(d_str, "%Y-%m-%d").date()
        day_entries = days_map[d_str]
        total_meals_count += len(day_entries)
        if day_entries:
            active_days_count += 1

        cal_sum = 0.0
        cal_count = 0
        sug_sum = 0.0
        sug_count = 0
        sod_sum = 0.0
        sod_count = 0
        pro_sum = 0.0
        pro_count = 0
        fib_sum = 0.0
        fib_count = 0

        for e in day_entries:
            nutrients = calculate_entry_nutrients(
                nutrition_facts=e.product.nutrition_facts if e.product else None,
                total_weight_g=e.total_weight_g,
            )
            if nutrients.energy_kcal is not None:
                cal_sum += nutrients.energy_kcal
                cal_count += 1
            if nutrients.total_sugar_g is not None:
                sug_sum += nutrients.total_sugar_g
                sug_count += 1
            if nutrients.sodium_mg is not None:
                sod_sum += nutrients.sodium_mg
                sod_count += 1
            if nutrients.protein_g is not None:
                pro_sum += nutrients.protein_g
                pro_count += 1
            if nutrients.dietary_fibre_g is not None:
                fib_sum += nutrients.dietary_fibre_g
                fib_count += 1

        cal_val = round(cal_sum, 1) if cal_count > 0 else (0.0 if not day_entries else None)
        sug_val = round(sug_sum, 2) if sug_count > 0 else (0.0 if not day_entries else None)
        sod_val = round(sod_sum, 2) if sod_count > 0 else (0.0 if not day_entries else None)
        pro_val = round(pro_sum, 2) if pro_count > 0 else (0.0 if not day_entries else None)
        fib_val = round(fib_sum, 2) if fib_count > 0 else (0.0 if not day_entries else None)

        if cal_val is not None and cal_val > 0:
            tot_calories.append(cal_val)
        if sug_val is not None and sug_val > 0:
            tot_sugar.append(sug_val)
        if sod_val is not None and sod_val > 0:
            tot_sodium.append(sod_val)
        if pro_val is not None and pro_val > 0:
            tot_protein.append(pro_val)
        if fib_val is not None and fib_val > 0:
            tot_fibre.append(fib_val)

        daily_trends.append(
            DailyTrendItem(
                date=d_str,
                day_name=d_obj.strftime("%d"),
                entry_count=len(day_entries),
                calories=cal_val,
                sugar_g=sug_val,
                sodium_mg=sod_val,
                protein_g=pro_val,
                fibre_g=fib_val,
            )
        )

    divisor = max(1, active_days_count)
    averages = {
        "calories": round(sum(tot_calories) / divisor, 1) if tot_calories else None,
        "sugar_g": round(sum(tot_sugar) / divisor, 2) if tot_sugar else None,
        "sodium_mg": round(sum(tot_sodium) / divisor, 2) if tot_sodium else None,
        "protein_g": round(sum(tot_protein) / divisor, 2) if tot_protein else None,
        "fibre_g": round(sum(tot_fibre) / divisor, 2) if tot_fibre else None,
    }

    return MonthlyAnalyticsResponse(
        year=year,
        month=month,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        daily_trends=daily_trends,
        averages=averages,
        active_days=active_days_count,
        total_logged_meals=total_meals_count,
        disclaimer=DISCLAIMER_TEXT,
    )


def get_frequently_consumed_products(
    db: Session,
    user_id: str,
    limit: int = 10,
) -> FrequentProductsResponse:
    """
    Returns the user's most frequently logged packaged products.
    """
    results = (
        db.query(
            FoodJournalEntry.product_id,
            func.count(FoodJournalEntry.id).label("log_count"),
            func.sum(FoodJournalEntry.total_weight_g).label("total_weight"),
            func.max(FoodJournalEntry.consumed_at).label("last_consumed"),
        )
        .filter(FoodJournalEntry.user_id == user_id)
        .group_by(FoodJournalEntry.product_id)
        .order_by(desc("log_count"))
        .limit(limit)
        .all()
    )

    items: List[FrequentProductItem] = []
    for pid, count, total_wt, last_cons in results:
        prod = db.query(Product).filter(Product.id == pid).first()
        items.append(
            FrequentProductItem(
                product_id=pid,
                product_name=prod.name if prod else "Unknown Product",
                product_brand=prod.brand if prod else None,
                product_category=prod.category if prod else None,
                product_image_url=prod.label_image_url if prod else None,
                log_count=count,
                total_weight_g=round(float(total_wt or 0.0), 2),
                last_consumed_at=last_cons,
            )
        )

    return FrequentProductsResponse(items=items)
