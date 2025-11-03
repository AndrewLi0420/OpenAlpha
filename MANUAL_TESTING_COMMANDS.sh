#!/bin/bash
# Manual Testing Commands for Registration Endpoint
# Make sure your backend server is running: uvicorn app.main:app --reload

echo "========================================="
echo "Test 1: Valid Registration (should return 201)"
echo "========================================="
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n"

echo "========================================="
echo "Test 2: Invalid Email Format (should return 400)"
echo "========================================="
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "notanemail",
    "password": "SecurePass123!"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n"

echo "========================================="
echo "Test 3: Weak Password (should return 400)"
echo "========================================="
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "short"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n"

echo "========================================="
echo "Test 4: Duplicate Email (should return 400)"
echo "========================================="
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "AnotherPass123!"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n"
echo "========================================="
echo "Testing Complete!"
echo "========================================="

