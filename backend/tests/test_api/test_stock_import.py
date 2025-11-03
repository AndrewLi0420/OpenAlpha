"""Integration tests for stock import service"""
import csv
import tempfile
from pathlib import Path

import pytest

from app.services.stock_import_service import import_stocks_from_csv
from app.services.stock_validation_service import validate_all, validate_stock_completeness
from app.crud.stocks import get_stock_by_symbol, get_stock_count


@pytest.mark.asyncio
async def test_import_stocks_from_csv(db_session):
    """Test importing stocks from CSV file"""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['AAPL', 'Apple Inc.', 'Technology', '1'])
        writer.writerow(['MSFT', 'Microsoft Corporation', 'Technology', '2'])
        writer.writerow(['GOOGL', 'Alphabet Inc.', 'Technology', '3'])
        csv_path = f.name
    
    try:
        # Import stocks
        stats = await import_stocks_from_csv(db_session, csv_path)
        
        assert stats['imported'] == 3
        assert stats['updated'] == 0
        assert stats['errors'] == 0
        
        # Verify stocks were imported
        stock1 = await get_stock_by_symbol(db_session, 'AAPL')
        assert stock1 is not None
        assert stock1.company_name == 'Apple Inc.'
        assert stock1.sector == 'Technology'
        assert stock1.fortune_500_rank == 1
        
        stock2 = await get_stock_by_symbol(db_session, 'MSFT')
        assert stock2 is not None
        assert stock2.fortune_500_rank == 2
        
        # Verify count
        count = await get_stock_count(db_session)
        assert count >= 3
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_import_stocks_idempotent(db_session):
    """Test that re-importing doesn't create duplicates"""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['AAPL', 'Apple Inc.', 'Technology', '1'])
        csv_path = f.name
    
    try:
        # First import
        stats1 = await import_stocks_from_csv(db_session, csv_path)
        assert stats1['imported'] == 1
        
        # Second import (should update, not create)
        stats2 = await import_stocks_from_csv(db_session, csv_path)
        assert stats2['imported'] == 0
        assert stats2['updated'] == 1
        
        # Verify only one stock exists
        count = await get_stock_count(db_session)
        assert count == 1
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_import_stocks_handles_missing_fields(db_session):
    """Test import handles missing optional fields"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['AAPL', 'Apple Inc.', '', ''])  # Missing optional fields
        writer.writerow(['MSFT', 'Microsoft Corporation', 'Technology', ''])  # Missing rank
        csv_path = f.name
    
    try:
        stats = await import_stocks_from_csv(db_session, csv_path)
        
        assert stats['imported'] == 2
        assert stats['errors'] == 0
        
        # Verify stocks imported with None for optional fields
        stock1 = await get_stock_by_symbol(db_session, 'AAPL')
        assert stock1.sector is None
        assert stock1.fortune_500_rank is None
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_import_stocks_handles_invalid_rows(db_session):
    """Test import handles invalid CSV rows gracefully"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['AAPL', 'Apple Inc.', 'Technology', '1'])  # Valid
        writer.writerow(['', 'Missing Symbol Inc.', 'Tech', '2'])  # Missing symbol
        writer.writerow(['MSFT', '', 'Technology', '3'])  # Missing company_name
        writer.writerow(['GOOGL', 'Alphabet Inc.', 'Technology', 'invalid'])  # Invalid rank
        csv_path = f.name
    
    try:
        stats = await import_stocks_from_csv(db_session, csv_path)
        
        # Should import 1 valid, skip 3 invalid
        assert stats['imported'] == 1
        assert stats['errors'] == 3  # 3 invalid rows
        
        # Verify valid stock imported
        stock = await get_stock_by_symbol(db_session, 'AAPL')
        assert stock is not None
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_import_stocks_case_insensitive_symbol(db_session):
    """Test import handles case-insensitive symbols"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['aapl', 'Apple Inc.', 'Technology', '1'])  # Lowercase
        csv_path = f.name
    
    try:
        stats = await import_stocks_from_csv(db_session, csv_path)
        assert stats['imported'] == 1
        
        # Verify symbol is uppercased
        stock = await get_stock_by_symbol(db_session, 'AAPL')
        assert stock is not None
        assert stock.symbol == 'AAPL'
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_validation_after_import(db_session):
    """Test validation after importing stocks"""
    # Create CSV with 5 stocks
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        for i in range(1, 6):
            writer.writerow([f'STOCK{i}', f'Company {i} Inc.', 'Technology', i])
        csv_path = f.name
    
    try:
        # Import
        await import_stocks_from_csv(db_session, csv_path)
        
        # Validate
        validation = await validate_all(db_session, expected_count=5)
        
        # All checks should pass
        assert validation['checks']['completeness']['valid']
        assert validation['checks']['required_fields']['valid']
        assert validation['checks']['data_types']['valid']
        assert validation['checks']['symbol_format']['valid']
    finally:
        Path(csv_path).unlink()


@pytest.mark.asyncio
async def test_validation_completeness_check(db_session):
    """Test completeness validation"""
    # Import some stocks
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['symbol', 'company_name', 'sector', 'fortune_500_rank'])
        writer.writerow(['AAPL', 'Apple Inc.', 'Technology', '1'])
        csv_path = f.name
    
    try:
        await import_stocks_from_csv(db_session, csv_path)
        
        # Validate with wrong expected count
        result = await validate_stock_completeness(db_session, expected_count=500)
        assert result['valid'] is False
        assert result['actual_count'] == 1
        assert result['expected_count'] == 500
        
        # Validate with correct expected count
        result2 = await validate_stock_completeness(db_session, expected_count=1)
        assert result2['valid'] is True
    finally:
        Path(csv_path).unlink()

