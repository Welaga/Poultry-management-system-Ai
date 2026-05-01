"""Analytics, predictive insights and performance scoring."""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.bird import BirdBatch, MortalityRecord
from app.models.egg import EggRecord, EggSale
from app.models.feed import FeedConsumption, FeedPurchase, FeedInventory
from app.models.health import HealthRecord


class AnalyticsService:
    @staticmethod
    def farm_performance_score(db: Session) -> dict:
        """Compute a 0-100 farm performance score based on multiple factors."""
        score = 100
        factors = []

        # 1. Mortality factor (last 30 days)
        thirty = date.today() - timedelta(days=30)
        total_birds = db.query(func.sum(BirdBatch.initial_count)).scalar() or 0
        recent_deaths = (
            db.query(func.sum(MortalityRecord.count))
            .filter(MortalityRecord.death_date >= thirty)
            .scalar()
            or 0
        )
        if total_birds > 0:
            mortality_rate = (recent_deaths / total_birds) * 100
            if mortality_rate > 10:
                score -= 30
                factors.append({"name": "mortality", "impact": -30, "value": f"{mortality_rate:.1f}%"})
            elif mortality_rate > 5:
                score -= 15
                factors.append({"name": "mortality", "impact": -15, "value": f"{mortality_rate:.1f}%"})
            elif mortality_rate > 2:
                score -= 5
                factors.append({"name": "mortality", "impact": -5, "value": f"{mortality_rate:.1f}%"})
            else:
                factors.append({"name": "mortality", "impact": 0, "value": f"{mortality_rate:.1f}%"})

        # 2. Egg production (last 7 days vs live birds)
        live_birds = db.query(func.sum(BirdBatch.current_count)).scalar() or 0
        seven = date.today() - timedelta(days=7)
        recent_eggs = (
            db.query(func.sum(EggRecord.good_eggs))
            .filter(EggRecord.collection_date >= seven)
            .scalar()
            or 0
        )
        if live_birds > 0:
            avg_per_day = recent_eggs / 7
            production_rate = (avg_per_day / live_birds) * 100
            if production_rate < 30:
                score -= 20
                factors.append({"name": "egg_production", "impact": -20, "value": f"{production_rate:.1f}%"})
            elif production_rate < 50:
                score -= 10
                factors.append({"name": "egg_production", "impact": -10, "value": f"{production_rate:.1f}%"})
            elif production_rate < 70:
                factors.append({"name": "egg_production", "impact": 0, "value": f"{production_rate:.1f}%"})
            else:
                score += 5
                factors.append({"name": "egg_production", "impact": 5, "value": f"{production_rate:.1f}%"})

        # 3. Active disease cases
        active_diseases = (
            db.query(func.count(HealthRecord.id))
            .filter(HealthRecord.status == "ongoing")
            .scalar()
            or 0
        )
        if active_diseases >= 3:
            score -= 15
            factors.append({"name": "active_diseases", "impact": -15, "value": active_diseases})
        elif active_diseases > 0:
            score -= 5
            factors.append({"name": "active_diseases", "impact": -5, "value": active_diseases})
        else:
            factors.append({"name": "active_diseases", "impact": 0, "value": 0})

        # 4. Feed stock health
        low_stock = (
            db.query(func.count(FeedInventory.id))
            .filter(FeedInventory.quantity_kg < 50)
            .scalar()
            or 0
        )
        if low_stock > 0:
            score -= 10
            factors.append({"name": "feed_stock", "impact": -10, "value": f"{low_stock} low"})
        else:
            factors.append({"name": "feed_stock", "impact": 0, "value": "OK"})

        score = max(0, min(100, score))
        rating = "Excellent" if score >= 85 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
        return {"score": score, "rating": rating, "factors": factors}

    @staticmethod
    def predict_next_week_eggs(db: Session) -> dict:
        """Simple linear regression on last 30 days of egg data to predict next 7 days."""
        thirty = date.today() - timedelta(days=30)
        records = (
            db.query(EggRecord.collection_date, func.sum(EggRecord.good_eggs))
            .filter(EggRecord.collection_date >= thirty)
            .group_by(EggRecord.collection_date)
            .order_by(EggRecord.collection_date)
            .all()
        )

        if len(records) < 5:
            return {
                "prediction": 0,
                "daily_avg": 0,
                "method": "insufficient_data",
                "confidence": "low",
                "history_days": len(records),
            }

        # Simple linear regression: y = mx + b
        n = len(records)
        xs = list(range(n))
        ys = [int(r[1] or 0) for r in records]

        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((xs[i] - x_mean) * (ys[i] - y_mean) for i in range(n))
        den = sum((xs[i] - x_mean) ** 2 for i in range(n)) or 1
        m = num / den
        b = y_mean - m * x_mean

        next7 = [max(0, m * (n + i) + b) for i in range(7)]
        prediction = int(sum(next7))

        return {
            "prediction": prediction,
            "daily_avg": round(prediction / 7, 1),
            "method": "linear_regression",
            "confidence": "medium" if n >= 14 else "low",
            "history_days": n,
            "trend": "increasing" if m > 0.5 else "decreasing" if m < -0.5 else "stable",
            "slope": round(m, 3),
        }

    @staticmethod
    def revenue_summary(db: Session, days: int = 30) -> dict:
        start = date.today() - timedelta(days=days)
        revenue = (
            db.query(func.sum(EggSale.total_amount))
            .filter(EggSale.sale_date >= start)
            .scalar()
            or 0
        )
        feed_cost = (
            db.query(func.sum(FeedPurchase.total_cost))
            .filter(FeedPurchase.purchase_date >= start)
            .scalar()
            or 0
        )
        health_cost = (
            db.query(func.sum(HealthRecord.cost))
            .filter(HealthRecord.diagnosis_date >= start)
            .scalar()
            or 0
        )
        expenses = float(feed_cost) + float(health_cost)
        profit = float(revenue) - expenses
        return {
            "period_days": days,
            "revenue": float(revenue),
            "feed_cost": float(feed_cost),
            "health_cost": float(health_cost),
            "expenses": expenses,
            "profit": profit,
            "profit_margin": round((profit / revenue) * 100, 2) if revenue > 0 else 0,
        }

    @staticmethod
    def insights(db: Session) -> list:
        """Generate actionable insights for the dashboard."""
        out = []
        # Mortality
        seven = date.today() - timedelta(days=7)
        recent = (
            db.query(func.sum(MortalityRecord.count))
            .filter(MortalityRecord.death_date >= seven)
            .scalar()
            or 0
        )
        if recent > 30:
            out.append({"icon": "warning", "type": "warning",
                        "text": f"High mortality this week: {recent} birds. Inspect ventilation and water quality."})

        # Eggs
        recent_eggs = (
            db.query(func.sum(EggRecord.good_eggs))
            .filter(EggRecord.collection_date >= seven)
            .scalar()
            or 0
        )
        live = db.query(func.sum(BirdBatch.current_count)).scalar() or 0
        if live > 0:
            rate = (recent_eggs / 7) / live * 100
            if rate < 50:
                out.append({"icon": "info", "type": "info",
                            "text": f"Egg production at {rate:.1f}%. Review feed quality and lighting (16h light recommended)."})
            elif rate >= 80:
                out.append({"icon": "success", "type": "success",
                            "text": f"Excellent egg production at {rate:.1f}%."})

        # Feed
        low = db.query(FeedInventory).filter(FeedInventory.quantity_kg < 50).all()
        for item in low:
            out.append({"icon": "warning", "type": "warning",
                        "text": f"Restock {item.feed_type}: only {item.quantity_kg:.1f} kg remaining."})

        # Active diseases
        diseases = db.query(HealthRecord).filter(HealthRecord.status == "ongoing").all()
        if diseases:
            names = ", ".join({d.disease_name for d in diseases[:3]})
            out.append({"icon": "warning", "type": "warning",
                        "text": f"{len(diseases)} ongoing health case(s): {names}. Isolate affected birds."})

        if not out:
            out.append({"icon": "success", "type": "success", "text": "All farm metrics look healthy."})
        return out
