"""PDF report generation using reportlab."""
from datetime import date, timedelta
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

from app.models.bird import BirdBatch, MortalityRecord
from app.models.egg import EggRecord, EggSale
from app.models.feed import FeedPurchase, FeedConsumption, FeedInventory
from app.models.health import HealthRecord, Vaccination


class ReportService:
    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="FarmTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1f6f3b"),
            alignment=1,
            spaceAfter=12,
        ))
        styles.add(ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#1f6f3b"),
            spaceBefore=14,
            spaceAfter=8,
        ))
        return styles

    @staticmethod
    def _table_style():
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6f3b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f9f5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f9f5")]),
        ])

    @staticmethod
    def daily_report(db: Session, target_date: date | None = None) -> bytes:
        target = target_date or date.today()
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = ReportService._styles()
        story = []

        story.append(Paragraph("Poultry Farm - Daily Report", styles["FarmTitle"]))
        story.append(Paragraph(f"Date: {target.isoformat()}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Birds
        story.append(Paragraph("Bird Status", styles["SectionHeading"]))
        total = db.query(func.sum(BirdBatch.initial_count)).scalar() or 0
        live = db.query(func.sum(BirdBatch.current_count)).scalar() or 0
        dead = total - live
        deaths_today = (
            db.query(func.sum(MortalityRecord.count))
            .filter(MortalityRecord.death_date == target)
            .scalar() or 0
        )
        bird_data = [
            ["Metric", "Count"],
            ["Total birds (initial)", total],
            ["Live birds", live],
            ["Total deaths", dead],
            ["Deaths today", deaths_today],
        ]
        t = Table(bird_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)
        story.append(Spacer(1, 12))

        # Eggs
        story.append(Paragraph("Egg Production (Today)", styles["SectionHeading"]))
        eggs = (
            db.query(
                func.sum(EggRecord.total_eggs),
                func.sum(EggRecord.broken_eggs),
                func.sum(EggRecord.good_eggs),
            )
            .filter(EggRecord.collection_date == target)
            .first()
        )
        total_e = eggs[0] or 0
        broken_e = eggs[1] or 0
        good_e = eggs[2] or 0
        sales_today = (
            db.query(func.sum(EggSale.quantity), func.sum(EggSale.total_amount))
            .filter(EggSale.sale_date == target)
            .first()
        )
        sold_e = sales_today[0] or 0
        revenue_e = sales_today[1] or 0

        egg_data = [
            ["Metric", "Value"],
            ["Total eggs collected", total_e],
            ["Broken", broken_e],
            ["Good eggs", good_e],
            ["Eggs sold", sold_e],
            ["Revenue", f"${float(revenue_e):.2f}"],
        ]
        t = Table(egg_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)
        story.append(Spacer(1, 12))

        # Feed
        story.append(Paragraph("Feed Consumption (Today)", styles["SectionHeading"]))
        consumed = (
            db.query(FeedConsumption.feed_type, func.sum(FeedConsumption.quantity_kg))
            .filter(FeedConsumption.consumption_date == target)
            .group_by(FeedConsumption.feed_type)
            .all()
        )
        feed_data = [["Feed Type", "Consumed (kg)"]]
        for ft, qty in consumed:
            feed_data.append([ft, f"{qty:.2f}"])
        if len(feed_data) == 1:
            feed_data.append(["No consumption recorded", "-"])
        t = Table(feed_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)

        story.append(Spacer(1, 12))
        story.append(Paragraph("Generated by Poultry Management System", styles["Italic"]))

        doc.build(story)
        return buf.getvalue()

    @staticmethod
    def weekly_report(db: Session) -> bytes:
        end = date.today()
        start = end - timedelta(days=7)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = ReportService._styles()
        story = []

        story.append(Paragraph("Poultry Farm - Weekly Report", styles["FarmTitle"]))
        story.append(Paragraph(f"Period: {start.isoformat()} to {end.isoformat()}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Bird summary
        story.append(Paragraph("Bird Summary", styles["SectionHeading"]))
        batches = db.query(BirdBatch).all()
        bird_data = [["Batch", "Breed", "Initial", "Current", "Deaths"]]
        for b in batches:
            deaths = b.initial_count - b.current_count
            bird_data.append([b.batch_code, b.breed, b.initial_count, b.current_count, deaths])
        if len(bird_data) == 1:
            bird_data.append(["No batches", "-", "-", "-", "-"])
        t = Table(bird_data, colWidths=[3 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)
        story.append(Spacer(1, 12))

        # Mortality
        story.append(Paragraph("Mortality (last 7 days)", styles["SectionHeading"]))
        morts = (
            db.query(MortalityRecord.death_date, func.sum(MortalityRecord.count))
            .filter(MortalityRecord.death_date >= start)
            .group_by(MortalityRecord.death_date)
            .order_by(MortalityRecord.death_date)
            .all()
        )
        m_data = [["Date", "Deaths"]]
        for d, c in morts:
            m_data.append([str(d), c])
        if len(m_data) == 1:
            m_data.append(["No deaths", "0"])
        t = Table(m_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)
        story.append(Spacer(1, 12))

        # Egg production
        story.append(Paragraph("Daily Egg Production", styles["SectionHeading"]))
        eggs = (
            db.query(EggRecord.collection_date, func.sum(EggRecord.good_eggs))
            .filter(EggRecord.collection_date >= start)
            .group_by(EggRecord.collection_date)
            .order_by(EggRecord.collection_date)
            .all()
        )
        e_data = [["Date", "Good Eggs"]]
        total_eggs = 0
        for d, c in eggs:
            e_data.append([str(d), c])
            total_eggs += c or 0
        e_data.append(["TOTAL", total_eggs])
        t = Table(e_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)

        doc.build(story)
        return buf.getvalue()

    @staticmethod
    def financial_summary(db: Session, days: int = 30) -> bytes:
        end = date.today()
        start = end - timedelta(days=days)
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)
        styles = ReportService._styles()
        story = []

        story.append(Paragraph("Poultry Farm - Financial Summary", styles["FarmTitle"]))
        story.append(Paragraph(f"Period: {start.isoformat()} to {end.isoformat()} ({days} days)", styles["Normal"]))
        story.append(Spacer(1, 14))

        revenue = (
            db.query(func.sum(EggSale.total_amount))
            .filter(EggSale.sale_date >= start)
            .scalar() or 0
        )
        feed_cost = (
            db.query(func.sum(FeedPurchase.total_cost))
            .filter(FeedPurchase.purchase_date >= start)
            .scalar() or 0
        )
        health_cost = (
            db.query(func.sum(HealthRecord.cost))
            .filter(HealthRecord.diagnosis_date >= start)
            .scalar() or 0
        )
        vacc_cost = (
            db.query(func.sum(Vaccination.cost))
            .filter(Vaccination.scheduled_date >= start)
            .scalar() or 0
        )

        expenses = float(feed_cost) + float(health_cost) + float(vacc_cost)
        profit = float(revenue) - expenses
        margin = (profit / float(revenue) * 100) if revenue else 0

        fin_data = [
            ["Metric", "Amount"],
            ["Revenue (egg sales)", f"${float(revenue):.2f}"],
            ["Feed costs", f"${float(feed_cost):.2f}"],
            ["Health/treatment costs", f"${float(health_cost):.2f}"],
            ["Vaccination costs", f"${float(vacc_cost):.2f}"],
            ["Total expenses", f"${expenses:.2f}"],
            ["Net profit", f"${profit:.2f}"],
            ["Profit margin", f"{margin:.1f}%"],
        ]
        t = Table(fin_data, colWidths=[8 * cm, 4 * cm])
        t.setStyle(ReportService._table_style())
        story.append(t)

        doc.build(story)
        return buf.getvalue()
