#!/usr/bin/env python3
"""Script to generate and view recommendations"""
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
from app.services.recommendation_service import generate_recommendations
from app.crud.recommendations import get_recommendations
from app.core.config import settings
from sqlalchemy import select


async def main():
    """Generate and display recommendations"""
    print("=" * 60)
    print("Recommendation Generation & Viewing")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # 1. Get or find a user (prefer superuser)
        print("\n[Step 1] Finding user...")
        print("-" * 60)
        
        # Try to find superuser first
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Get first user if superuser doesn't exist
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
        
        if not user:
            print("✗ No users found in database!")
            print("  The superuser should be created automatically on server startup.")
            print("  Check your .env file for FIRST_SUPERUSER_EMAIL and FIRST_SUPERUSER_PASSWORD")
            return 1
        
        print(f"✓ Using user: {user.email} (ID: {user.id})")
        
        # 2. Generate recommendations
        print("\n[Step 2] Generating recommendations...")
        print("-" * 60)
        print("This may take a minute (processing stocks, running ML predictions)...")
        
        try:
            recommendations = await generate_recommendations(
                session=session,
                user_id=user.id,
                daily_target_count=10,
                use_ensemble=True,
            )
            
            print(f"✓ Generated {len(recommendations)} recommendations")
            
            if len(recommendations) == 0:
                print("\n⚠ No recommendations generated. Possible reasons:")
                print("  - ML models not loaded (restart backend server after training)")
                print("  - No market data available")
                print("  - All stocks filtered by user preferences")
                print("  - Prediction failures (check backend logs)")
                return 1
            
        except Exception as e:
            print(f"✗ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # 3. Fetch and display recommendations
        print("\n[Step 3] Fetching recommendations from database...")
        print("-" * 60)
        
        try:
            all_recs = await get_recommendations(
                session=session,
                user_id=user.id,
                sort_by="confidence",
                sort_direction="desc",
            )
            
            print(f"\n✓ Found {len(all_recs)} total recommendations for this user")
            
            if all_recs:
                print("\n" + "=" * 60)
                print("RECOMMENDATIONS (sorted by confidence, highest first)")
                print("=" * 60)
                
                for idx, rec in enumerate(all_recs[:20], 1):  # Show top 20
                    print(f"\n[{idx}] {rec.stock.symbol} - {rec.stock.company_name}")
                    print(f"    Signal: {rec.signal.upper()}")
                    print(f"    Confidence: {rec.confidence_score:.3f}")
                    print(f"    Risk Level: {rec.risk_level.value}")
                    if rec.sentiment_score:
                        print(f"    Sentiment: {rec.sentiment_score:.3f}")
                    print(f"    Holding Period: {rec.holding_period.value}")
                    print(f"    Date: {rec.created_at}")
                    if rec.explanation:
                        # Truncate long explanations
                        explanation = rec.explanation[:200] + "..." if len(rec.explanation) > 200 else rec.explanation
                        print(f"    Explanation: {explanation}")
                
                if len(all_recs) > 20:
                    print(f"\n... and {len(all_recs) - 20} more recommendations")
            else:
                print("\n⚠ No recommendations found in database")
                print("  Recommendations may have been generated but not saved, or")
                print("  they may have been filtered out by tier restrictions.")
        
        except Exception as e:
            print(f"✗ Failed to fetch recommendations: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # Cleanup
    await engine.dispose()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    print("\n💡 Tip: You can also view recommendations via:")
    print("  - API: GET /api/v1/recommendations (requires authentication)")
    print("  - Frontend: http://localhost:5173 (if running)")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

