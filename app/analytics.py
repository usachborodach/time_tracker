import logging
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required

from .extensions import get_db
from .models import ACTIVITIES

logger = logging.getLogger(__name__)
analytics_bp = Blueprint('analytics', __name__)

WEEKDAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

# Трекаем 07:00–23:00; 00:00–06:59 не хранятся и считаются сном.
TRACKED_HOURS = [f'{h:02d}:00' for h in range(7, 24)]
SLEEP_ACTIVITY = 'Спал'
DEFAULT_SLEEP_HOURS = 7  # 00:00–06:59


def _parse_date(raw, fallback):
    try:
        return datetime.strptime(raw, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return fallback


def _fetch_days(start_date, end_date):
    """Все документы days в диапазоне [start_date; end_date]."""
    db = get_db()
    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)
    return list(
        db.days.find({'date': {'$gte': start_dt, '$lt': end_dt}}).sort('date', 1)
    )


def _aggregate(days):
    daily = []
    totals = Counter()
    wd_hour = defaultdict(lambda: defaultdict(int))

    for doc in days:
        d = doc.get('date')
        if not d:
            continue
        hours_map = doc.get('hours') or {}

        by_act = Counter()
        for hour, activity in hours_map.items():
            if not activity:
                continue
            by_act[activity] += 1
            totals[activity] += 1
            # heatmap только по трекаемому диапазону 07:00–23:00
            wd_hour[d.weekday()][hour] += 1

        # Нетрекаемые 00:00–06:59 по умолчанию = сон
        by_act[SLEEP_ACTIVITY] += DEFAULT_SLEEP_HOURS
        totals[SLEEP_ACTIVITY] += DEFAULT_SLEEP_HOURS

        daily.append({
            'date': d.strftime('%Y-%m-%d'),
            'by_activity': dict(by_act),
            'total': sum(by_act.values()),
        })

    heatmap = []
    heatmap_max = 0
    for wd in range(7):
        row = []
        for hour in TRACKED_HOURS:
            v = wd_hour[wd].get(hour, 0)
            row.append(v)
            heatmap_max = max(heatmap_max, v)
        heatmap.append(row)

    return daily, totals, heatmap, heatmap_max


@analytics_bp.route('/analytics')
@login_required
def analytics():
    today = date.today()
    start = _parse_date(request.args.get('start'), today - timedelta(days=29))
    end = _parse_date(request.args.get('end'), today)
    if start > end:
        start, end = end, start

    days = _fetch_days(start, end)
    daily, totals, heatmap, heatmap_max = _aggregate(days)

    used = [a for a in ACTIVITIES if totals.get(a)]
    others = [a for a in totals if a not in ACTIVITIES]
    ordered_activities = used + others

    total_hours = sum(totals.values())
    days_count = sum(1 for d in daily if d['total'] > 0)
    avg_per_day = round(total_hours / days_count, 1) if days_count else 0
    top_activity, top_hours = (totals.most_common(1)[0] if totals else (None, 0))

    presets = [
        ('7 дней', today - timedelta(days=6), today),
        ('30 дней', today - timedelta(days=29), today),
        ('90 дней', today - timedelta(days=89), today),
        ('Всё время', date(2000, 1, 1), today),
    ]

    return render_template(
        'analytics.html',
        start=start, end=end, presets=presets,
        daily=daily,
        totals=dict(totals),
        ordered_activities=ordered_activities,
        heatmap=heatmap, heatmap_max=heatmap_max,
        weekday_names=WEEKDAY_NAMES, hour_keys=TRACKED_HOURS,
        total_hours=total_hours, days_count=days_count,
        avg_per_day=avg_per_day, top_activity=top_activity, top_hours=top_hours,
        default_sleep_hours=DEFAULT_SLEEP_HOURS,
        sleep_activity=SLEEP_ACTIVITY,
    )