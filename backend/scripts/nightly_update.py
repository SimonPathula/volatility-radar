"""
app/scripts/nightly_update.py

Render Cron Job entry point.
Schedule: 10:00 PM UTC daily  =  3:30 AM IST
(Tuesday's candle closes at 2:30 AM IST → this runs at 3:30 AM IST → safe margin)

What it does:
  1. Ensures unique constraint exists on forex_prices(pair, date)
  2. Fetches last 10 days of prices for all 3 pairs and upserts
  3. Fetches current week's calendar from Forex Factory and upserts
  4. Logs a summary

Render Cron Job config:
  Command : python -m app.scripts.nightly_update
  Schedule: 0 22 * * *   (10 PM UTC = 3:30 AM IST)
"""

import logging
import sys
from datetime import date, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def run():
    log.info("=== Nightly update started ===")

    # ── Step 1: Ensure DB constraint ─────────────────────────────────────────
    from app.services.price_refresher import (
        ensure_unique_constraint,
        refresh_prices_for_range,
        get_latest_db_date,
    )
    from scripts.populate_validation_history import update_validation_history

    ensure_unique_constraint()

    # ── Step 2: Refresh prices ────────────────────────────────────────────────
    today = date.today()

    latest = get_latest_db_date()

    if latest is None:
        log.warning(
            "No existing forex_prices data found."
        )
    else:
        from_date = latest + timedelta(days=1)
        to_date = today
        if from_date <= to_date:
            log.info(
                f"Fetching prices: "
                f"{from_date} → {to_date}"
            )
            refresh_prices_for_range(
                from_date,
                to_date
            )
        else:
            log.info(
                "No missing forex price dates."
            )

    latest = get_latest_db_date()
    log.info(f"Latest price date in DB after refresh: {latest}")

    # ── Step 3: Refresh calendar ──────────────────────────────────────────────
    # Forex Factory scraping — fetches the current week
    try:
        _refresh_calendar()
    except Exception:
        # Calendar failure is non-fatal — prices are more critical
        log.exception(f"Calendar refresh failed (non-fatal)")

    try:
        log.info(
            "Updating validation history..."
        )
        update_validation_history()
        log.info(
            "Validation history updated."
        )
    except Exception:
        log.exception(
            "Validation history update failed"
        )

    log.info("=== Nightly update complete ===")


def _refresh_calendar():
    
    """
    Scrapes current week from Forex Factory and upserts into calendar_events.
    Reuses your existing scraping + preprocessing logic.
    """
    import time
    import random
    import pandas as pd
    from datetime import datetime
    from sqlalchemy import text
    from bs4 import BeautifulSoup
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from app.db.database import engine

    TARGET_CURRENCIES = ["EUR", "USD", "GBP", "JPY"]

    def scrape_day(driver, day_str: str) -> list[dict]:
        url = f"https://www.forexfactory.com/calendar?day={day_str}"
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "calendar__row")))

        for i in range(1, 20):
            driver.execute_script(f"window.scrollTo(0, {i * 250});")
            time.sleep(0.3)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.find_all("tr", class_="calendar__row")
        result = []
        current_date = None

        for row in rows:
            date_cell = row.find("td", class_="calendar__date")
            if date_cell:
                current_date = date_cell.get_text(strip=True, separator=" ")

            currency_handle = row.find("td", class_="calendar__currency")
            if not currency_handle:
                continue

            currency = currency_handle.get_text(strip=True)
            if currency not in TARGET_CURRENCIES:
                continue

            actual   = row.find("td", class_="calendar__actual")
            forecast = row.find("td", class_="calendar__forecast")
            previous = row.find("td", class_="calendar__previous")

            actual_text   = actual.get_text(strip=True)   if actual   else ""
            forecast_text = forecast.get_text(strip=True) if forecast else ""
            previous_text = previous.get_text(strip=True) if previous else ""

            if not actual_text and not forecast_text and not previous_text:
                continue

            impact_cell = row.find("td", class_="calendar__impact")
            impact_text = ""
            if impact_cell:
                img = impact_cell.find("img")
                if img:
                    src = img.get("src", "")
                    if   'gra' in src: 
                        impact_text = "Non-Economic"
                    elif 'yel' in src: 
                        impact_text = "Low"
                    elif 'ora' in src: 
                        impact_text = "Medium"
                    elif "red" in src: 
                        impact_text = "High"

            time_cell = row.find("td", class_="calendar__time")
            event_cell = row.find("td", class_="calendar__event")

            result.append({
                "date":     current_date,
                "time":     time_cell.get_text(strip=True) if time_cell else "",
                "currency": currency,
                "event":    event_cell.get_text(strip=True) if event_cell else "",
                "impact":   impact_text,
                "actual":   actual_text,
                "forecast": forecast_text,
                "previous": previous_text,
            })

        return result

    def preprocess(rows: list[dict]) -> pd.DataFrame:
        import calendar as cal_mod
        import re

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Parse date strings like "Sun Jun 14"
        parts = df["date"].str.split(" ", expand=True)
        month_map = {m: i for i, m in enumerate(cal_mod.month_abbr) if m}
        df["month_num"] = parts[1].map(month_map)
        df["day_num"]   = parts[2].astype(int)

        today = date.today()
        df["year"] = today.year
        # Handle year rollover (December → January)
        df.loc[df["month_num"] < today.month - 1, "year"] = today.year + 1

        df["date"] = pd.to_datetime(
            dict(year=df["year"], month=df["month_num"], day=df["day_num"])
        ).dt.date

        df = df.drop(columns=["month_num", "day_num", "year"], errors="ignore")
        df = df.dropna(subset=["actual", "previous"])
        df["time"] = df["time"].ffill()
        df = df.drop(columns=["forecast"], errors="ignore")
        df = df.drop_duplicates()

        return df

    def upsert_calendar(df: pd.DataFrame):
        if df.empty:
            log.info("Calendar: nothing to upsert")
            return

        sql = text("""
            INSERT INTO calendar_events (date, time, currency, event, impact, actual, previous)
            VALUES (:date, :time, :currency, :event, :impact, :actual, :previous)
            ON DUPLICATE KEY UPDATE
                actual   = VALUES(actual),
                previous = VALUES(previous),
                impact   = VALUES(impact)
        """)

        # Ensure unique key exists on calendar_events too
        check = """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'calendar_events'
              AND index_name = 'uniq_cal_row'
        """
        with engine.begin() as conn:
            cnt = conn.execute(text(check)).fetchone()[0]
            if cnt == 0:
                conn.execute(text(
                    "ALTER TABLE calendar_events "
                    "ADD UNIQUE KEY uniq_cal_row (date, time, currency, event)"
                ))
                log.info("Added UNIQUE KEY uniq_cal_row to calendar_events")

        records = df.to_dict(orient="records")
        with engine.begin() as conn:
            conn.execute(sql, records)
        log.info(f"Calendar: upserted {len(records)} rows")

    # Forex Factory posts next week's events in advance — needed for "tomorrow" predictions
    today = date.today()
    day_str = today.strftime("%b%-d.%Y").lower()
    log.info(f"Scraping Forex Factory day: {day_str}")

    driver = uc.Chrome(version_main=148)
    try:
        rows = scrape_day(driver, day_str)
    finally:
        driver.quit()

    df = preprocess(rows)
    log.info(f"Calendar: {len(df)} rows scraped after preprocessing")
    upsert_calendar(df)

if __name__ == "__main__":
    run()