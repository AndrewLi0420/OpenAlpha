#!/usr/bin/env python3
"""Diagnostic script to identify why recommendation generation is failing"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

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
from app.services.ml_service import are_models_loaded, initialize_models, predict_stock
from app.crud.stocks import get_all_stocks
from app.crud.market_data import get_market_data_count, get_stock_ids_with_market_data, get_latest_market_data
from app.core.config import settings
from sqlalchemy import select


async def diagnose():
    """Run diagnostics on recommendation system"""
    print("=" * 60)
    print("Recommendation System Diagnostics")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    async with async_session_maker() as session:
        # 1. Check ML models
        print("\n[1] Checking ML Models...")
        print("-" * 60)
        models_loaded = are_models_loaded()
        print(f"   Models loaded: {models_loaded}")
        
        if not models_loaded:
            issues.append("ML models are not loaded")
            print("   ⚠️  Attempting to initialize models...")
            try:
                init_results = initialize_models()
                nn_status = init_results["neural_network"]
                rf_status = init_results["random_forest"]
                
                print(f"   Neural Network: {'✓ Loaded' if nn_status['loaded'] else '✗ Failed'}")
                if not nn_status['loaded']:
                    print(f"     Error: {nn_status.get('error', 'Unknown')}")
                
                print(f"   Random Forest: {'✓ Loaded' if rf_status['loaded'] else '✗ Failed'}")
                if not rf_status['loaded']:
                    print(f"     Error: {rf_status.get('error', 'Unknown')}")
                
                if not nn_status['loaded'] and not rf_status['loaded']:
                    issues.append("Both ML models failed to load")
                elif not nn_status['loaded'] or not rf_status['loaded']:
                    warnings.append("One ML model failed to load (will use available model)")
            except Exception as e:
                issues.append(f"Model initialization failed: {e}")
                print(f"   ✗ Initialization error: {e}")
        else:
            print("   ✓ Models are loaded")
        
        # 2. Check stocks
        print("\n[2] Checking Stocks...")
        print("-" * 60)
        stocks = await get_all_stocks(session)
        print(f"   Total stocks: {len(stocks)}")
        
        if len(stocks) == 0:
            issues.append("No stocks in database")
        else:
            print(f"   ✓ Stocks available")
        
        # 3. Check market data
        print("\n[3] Checking Market Data...")
        print("-" * 60)
        market_data_count = await get_market_data_count(session)
        stocks_with_data = await get_stock_ids_with_market_data(session)
        
        print(f"   Total market data records: {market_data_count}")
        print(f"   Stocks with market data: {len(stocks_with_data)}")
        
        if market_data_count == 0:
            issues.append("No market data in database")
        elif len(stocks_with_data) < 10:
            warnings.append(f"Only {len(stocks_with_data)} stocks have market data (may limit recommendations)")
        else:
            print(f"   ✓ Sufficient market data available")
        
        # 4. Test prediction on a sample stock
        print("\n[4] Testing ML Prediction...")
        print("-" * 60)
        
        if models_loaded and len(stocks_with_data) > 0:
            # Get first stock with market data
            test_stock = None
            for stock in stocks:
                if stock.id in stocks_with_data:
                    test_stock = stock
                    break
            
            if test_stock:
                print(f"   Testing with stock: {test_stock.symbol} ({test_stock.company_name})")
                try:
                    # Check if stock has latest market data
                    latest_md = await get_latest_market_data(session, test_stock.id)
                    if latest_md is None:
                        issues.append(f"Stock {test_stock.symbol} has no latest market data")
                        print(f"   ✗ No latest market data for {test_stock.symbol}")
                    else:
                        print(f"   ✓ Latest market data found (price: ${float(latest_md.price):.2f})")
                    
                    # Try prediction
                    print(f"   Attempting prediction...")
                    prediction = await predict_stock(
                        session=session,
                        stock_id=test_stock.id,
                        use_ensemble=True,
                    )
                    
                    print(f"   ✓ Prediction successful!")
                    print(f"     Signal: {prediction['signal']}")
                    print(f"     Confidence: {prediction['confidence_score']:.3f}")
                    print(f"     Model used: {prediction.get('model_used', 'unknown')}")
                    
                except Exception as e:
                    issues.append(f"Prediction failed for {test_stock.symbol}: {e}")
                    print(f"   ✗ Prediction failed: {e}")
                    import traceback
                    print(f"   Traceback:")
                    traceback.print_exc()
            else:
                warnings.append("No stocks with market data found for testing")
        else:
            if not models_loaded:
                warnings.append("Skipping prediction test (models not loaded)")
            if len(stocks_with_data) == 0:
                warnings.append("Skipping prediction test (no stocks with market data)")
        
        # 5. Check user
        print("\n[5] Checking User...")
        print("-" * 60)
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
        
        if not user:
            issues.append("No users found in database")
            print("   ✗ No users found")
        else:
            print(f"   ✓ User found: {user.email} (ID: {user.id})")
        
        # 6. Summary
        print("\n" + "=" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        if issues:
            print("\n❌ CRITICAL ISSUES (must fix):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        if warnings:
            print("\n⚠️  WARNINGS (may cause issues):")
            for i, warning in enumerate(warnings, 1):
                print(f"   {i}. {warning}")
        
        if not issues and not warnings:
            print("\n✓ All checks passed! Recommendation system should work.")
        elif not issues:
            print("\n⚠️  Some warnings but no critical issues. System may work with limitations.")
        else:
            print("\n❌ Critical issues found. Please fix these before generating recommendations.")
        
        # 7. Recommendations
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        
        if "ML models are not loaded" in str(issues):
            print("\n1. Fix ML Models:")
            print("   - Check that models exist in ml-models/ directory")
            print("   - Run: ls -lh ml-models/")
            print("   - If missing, train models: python scripts/train_models.py")
            print("   - Restart backend server after training")
        
        if "No market data" in str(issues):
            print("\n2. Fix Market Data:")
            print("   - Run: python scripts/collect_market_data.py")
            print("   - Or backfill historical data: python scripts/backfill_yfinance.py --months 6")
        
        if "No stocks" in str(issues):
            print("\n3. Fix Stocks:")
            print("   - Import stocks: python manage.py import-stocks")
        
        if "No users" in str(issues):
            print("\n4. Fix Users:")
            print("   - Superuser should be created automatically on server startup")
            print("   - Check .env file for FIRST_SUPERUSER_EMAIL and FIRST_SUPERUSER_PASSWORD")
    
    # Cleanup
    await engine.dispose()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(diagnose())

