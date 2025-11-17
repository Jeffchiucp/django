#!/bin/bash
# Scan for PostgreSQL aggregate usage that changed in Django 5.0

echo "=================================================================="
echo "Django 5.0 Breaking Change: PostgreSQL Aggregates Return None"
echo "=================================================================="
echo ""
echo "In Django 5.0, ArrayAgg/StringAgg/JSONBAgg return None instead of"
echo "empty values when no rows match."
echo ""

FOUND_ISSUES=0

echo "=== 1. ArrayAgg usage ==="
ARRAYAGG=$(grep -rn "ArrayAgg" --include="*.py" . 2>/dev/null | grep -v ".pyc" | grep -v "# After")
if [ -n "$ARRAYAGG" ]; then
    echo "🟡 Found ArrayAgg usage:"
    echo "$ARRAYAGG"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo "✅ No ArrayAgg usage found"
fi
echo ""

echo "=== 2. StringAgg usage ==="
STRINGAGG=$(grep -rn "StringAgg" --include="*.py" . 2>/dev/null | grep -v ".pyc")
if [ -n "$STRINGAGG" ]; then
    echo "🟡 Found StringAgg usage:"
    echo "$STRINGAGG"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo "✅ No StringAgg usage found"
fi
echo ""

echo "=== 3. JSONBAgg usage ==="
JSONBAGG=$(grep -rn "JSONBAgg" --include="*.py" . 2>/dev/null | grep -v ".pyc")
if [ -n "$JSONBAGG" ]; then
    echo "🟡 Found JSONBAgg usage:"
    echo "$JSONBAGG"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo "✅ No JSONBAgg usage found"
fi
echo ""

echo "=================================================================="
echo "SUMMARY"
echo "=================================================================="

if [ $FOUND_ISSUES -eq 0 ]; then
    echo "✅ No PostgreSQL aggregates found"
    echo ""
    echo "No action required."
else
    echo "🟡 Found PostgreSQL aggregate usage"
    echo ""
    echo "REQUIRED ACTIONS:"
    echo "Update code to handle None return values"
    echo ""
    echo "Example fix:"
    echo "  # Before (Django 4.2 - may break in 5.0)"
    echo "  tags = Model.objects.aggregate(tags=ArrayAgg('tag'))['tags']"
    echo "  for tag in tags:  # ❌ Fails if tags is None"
    echo "      ..."
    echo ""
    echo "  # After (Django 5.0 compatible)"
    echo "  tags = Model.objects.aggregate(tags=ArrayAgg('tag'))['tags']"
    echo "  for tag in tags or []:  # ✅ Handle None"
    echo "      ..."
    echo ""
    echo "  # Or with default"
    echo "  from django.contrib.postgres.aggregates import ArrayAgg"
    echo "  from django.db.models import Value"
    echo "  from django.db.models.functions import Coalesce"
    echo ""
    echo "  tags = Model.objects.aggregate("
    echo "      tags=Coalesce(ArrayAgg('tag'), Value([]))"
    echo "  )['tags']"
fi
echo ""
