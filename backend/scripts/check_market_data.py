#!/usr/bin/env python3
"""Script to check if market data collection is working"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Import all models to ensure SQLAlchemy can resolve relationships
from app.users.models import User  # noqa: F401
from app.models import (  # noqa: F401
    UserPreferences,
    Stock,
    MarketData,
    SentimentData,
    Recommendation,
    UserStockTracking,
)

from app.db.config import async_session_maker, engine
from app.crud.market_data import (
    get_market_data_count,
    get_stock_ids_with_market_data,
    get_latest_market_data,
    get_stocks_with_stale_data,
)
from app.crud.stocks import get_all_stocks, get_stock_count
from sqlalchemy import func, select
from app.models.market_data import MarketData
from app.models.stock import Stock


async def check_market_data_status():
    """Check market data collection status and display statistics"""
    print("=" * 60)
    print("Market Data Collection Status Check")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # 1. Check total stocks vs market data records
        total_stocks = await get_stock_count(session)
        total_market_records = await get_market_data_count(session)
        stocks_with_data = await get_stock_ids_with_market_data(session)
        stocks_with_data_count = len(stocks_with_data)
        
        print(f"\n[1] Stock & Market Data Overview:")
        print(f"   - Total stocks in database: {total_stocks}")
        print(f"   - Stocks with market data: {stocks_with_data_count}")
        print(f"   - Stocks without market data: {total_stocks - stocks_with_data_count}")
        print(f"   - Total market data records: {total_market_records}")
        
        if total_market_records == 0:
            print("\n⚠️  No market data found in database!")
            print("   - Run: python scripts/collect_market_data.py")
            print("   - Check application logs for errors")
            print("   - Verify stocks are loaded in database")
            return
        
        # 2. Check most recent market data
        result = await session.execute(
            select(MarketData)
            .order_by(MarketData.timestamp.desc())
            .limit(10)
        )
        recent = result.scalars().all()
        print(f"\n[2] Most Recent Market Data (last 10 records):")
        for record in recent:
            stock_result = await session.execute(
                select(Stock).where(Stock.id == record.stock_id)
            )
            stock = stock_result.scalar_one_or_none()
            symbol = stock.symbol if stock else "Unknown"
            print(f"   - {symbol}: ${float(record.price):.2f} "
                  f"(volume: {record.volume:,}, time: {record.timestamp})")
        
        # 3. Check data freshness (last 24 hours)
        one_day_ago_aware = datetime.now(timezone.utc) - timedelta(hours=24)
        one_day_ago = one_day_ago_aware.replace(tzinfo=None)
        result = await session.execute(
            select(func.count(MarketData.id))
            .where(MarketData.timestamp >= one_day_ago)
        )
        recent_count = result.scalar_one() or 0
        print(f"\n[3] Data Freshness:")
        print(f"   - Records in last 24 hours: {recent_count}")
        
        # Check today's data
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_naive = today_start.replace(tzinfo=None)
        result = await session.execute(
            select(func.count(MarketData.id))
            .where(MarketData.timestamp >= today_start_naive)
        )
        today_count = result.scalar_one() or 0
        print(f"   - Records from today: {today_count}")
        
        if today_count == 0:
            print("   ⚠️  No data collected today - collection may not be running")
        else:
            print("   ✓ Recent data collection appears to be working")
        
        # 4. Check sample stocks with latest data
        stocks = await get_all_stocks(session)
        if stocks:
            print(f"\n[4] Sample Stocks - Latest Market Data:")
            sample_stocks = stocks[:10]  # Check first 10 stocks
            for stock in sample_stocks:
                latest = await get_latest_market_data(session, stock.id)
                if latest:
                    print(f"   ✓ {stock.symbol} ({stock.company_name}): "
                          f"${float(latest.price):.2f} @ {latest.timestamp}")
                else:
                    print(f"   ✗ {stock.symbol} ({stock.company_name}): No data")
        
        # 5. Check stale data (stocks without recent updates)
        stale_stocks = await get_stocks_with_stale_data(session, max_age_hours=24)
        print(f"\n[5] Stale Data Check (no update in last 24 hours):")
        print(f"   - Stocks with stale/missing data: {len(stale_stocks)}")
        if len(stale_stocks) > 0 and len(stale_stocks) <= 20:
            print(f"   - Stale stocks:")
            for stock_id, last_update in stale_stocks[:20]:
                stock_result = await session.execute(
                    select(Stock).where(Stock.id == stock_id)
                )
                stock = stock_result.scalar_one_or_none()
                symbol = stock.symbol if stock else "Unknown"
                if last_update:
                    print(f"     - {symbol}: last update {last_update}")
                else:
                    print(f"     - {symbol}: no data")
        elif len(stale_stocks) > 20:
            print(f"   - Showing first 20 of {len(stale_stocks)} stale stocks:")
            for stock_id, last_update in stale_stocks[:20]:
                stock_result = await session.execute(
                    select(Stock).where(Stock.id == stock_id)
                )
                stock = stock_result.scalar_one_or_none()
                symbol = stock.symbol if stock else "Unknown"
                if last_update:
                    print(f"     - {symbol}: last update {last_update}")
                else:
                    print(f"     - {symbol}: no data")
        
        # 6. Check price statistics
        result = await session.execute(
            select(
                func.min(MarketData.price).label("min_price"),
                func.max(MarketData.price).label("max_price"),
                func.avg(MarketData.price).label("avg_price"),
            )
        )
        stats = result.one()
        print(f"\n[6] Price Statistics (all records):")
        print(f"   - Min price: ${float(stats.min_price):.2f}")
        print(f"   - Max price: ${float(stats.max_price):.2f}")
        print(f"   - Average price: ${float(stats.avg_price):.2f}")
        
        # 7. Success rate calculation
        success_rate = (stocks_with_data_count / total_stocks * 100) if total_stocks > 0 else 0
        print(f"\n[7] Collection Success Rate:")
        print(f"   - Stocks with data: {stocks_with_data_count}/{total_stocks} ({success_rate:.1f}%)")
        print(f"   - Stocks without data: {total_stocks - stocks_with_data_count} ({100 - success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("   ✓ Good collection coverage!")
        elif success_rate >= 50:
            print("   ⚠️  Moderate collection coverage - some stocks may be delisted")
        else:
            print("   ⚠️  Low collection coverage - check for issues")
    
    # Cleanup
    await engine.dispose()
    print("\n" + "=" * 60)
    print("Status check complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_market_data_status())

