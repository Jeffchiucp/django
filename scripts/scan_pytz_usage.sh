#!/bin/bash
# Scan for pytz usage in application code (excluding migrations)

echo "=================================================================="
echo "Django 5.0 Breaking Change: pytz Support Removed"
echo "=================================================================="
echo ""
echo "Scanning for pytz usage in application code..."
echo ""

# Count files
PYTZ_IMPORTS=$(find . -name "*.py" ! -path "*/migrations/*" ! -path "*/.venv/*" ! -path "*/venv/*" -exec grep -l "import pytz\|from pytz" {} \; 2>/dev/null)
PYTZ_COUNT=$(echo "$PYTZ_IMPORTS" | grep -c "\.py" 2>/dev/null || echo "0")

echo "=== 1. Files importing pytz (excluding migrations) ==="
if [ "$PYTZ_COUNT" -gt 0 ]; then
    echo "🔴 Found $PYTZ_COUNT file(s) with pytz imports:"
    echo "$PYTZ_IMPORTS"
else
    echo "✅ No pytz imports found in application code"
fi
echo ""

echo "=== 2. is_dst parameter usage ==="
IS_DST=$(grep -rn "is_dst" --include="*.py" . 2>/dev/null | grep -v ".pyc" | grep -v migrations)
if [ -n "$IS_DST" ]; then
    echo "🔴 Found is_dst parameter usage:"
    echo "$IS_DST"
else
    echo "✅ No is_dst parameter usage found"
fi
echo ""

echo "=== 3. pytz.timezone() calls ==="
PYTZ_TZ=$(grep -rn "pytz\.timezone" --include="*.py" . 2>/dev/null | grep -v migrations | grep -v ".pyc")
if [ -n "$PYTZ_TZ" ]; then
    echo "🔴 Found pytz.timezone() calls:"
    echo "$PYTZ_TZ"
else
    echo "✅ No pytz.timezone() calls found"
fi
echo ""

echo "=== 4. make_aware() with is_dst ==="
MAKE_AWARE_DST=$(grep -rn "make_aware.*is_dst" --include="*.py" . 2>/dev/null | grep -v ".pyc")
if [ -n "$MAKE_AWARE_DST" ]; then
    echo "🔴 Found make_aware() with is_dst:"
    echo "$MAKE_AWARE_DST"
else
    echo "✅ No make_aware() with is_dst found"
fi
echo ""

echo "=================================================================="
echo "SUMMARY"
echo "=================================================================="

TOTAL_ISSUES=0
[ "$PYTZ_COUNT" -gt 0 ] && TOTAL_ISSUES=$((TOTAL_ISSUES + PYTZ_COUNT))
[ -n "$IS_DST" ] && TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
[ -n "$PYTZ_TZ" ] && TOTAL_ISSUES=$((TOTAL_ISSUES + 1))

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo "✅ No pytz usage found in application code!"
    echo ""
    echo "RECOMMENDATION: Safe to proceed with Django 5.0 upgrade"
else
    echo "🔴 Found pytz usage in application code"
    echo ""
    echo "REQUIRED ACTIONS:"
    echo "1. Replace 'import pytz' with 'from zoneinfo import ZoneInfo'"
    echo "2. Replace 'pytz.timezone(name)' with 'ZoneInfo(name)'"
    echo "3. Remove 'is_dst' parameter from all function calls"
    echo "4. Keep pytz in requirements.txt for migrations (see MIGRATION_DECISION_ASSESSMENT.md)"
    echo ""
    echo "Example migration:"
    echo "  # Before (Django 4.2)"
    echo "  import pytz"
    echo "  tz = pytz.timezone('America/New_York')"
    echo "  dt = make_aware(naive_dt, timezone=tz, is_dst=None)"
    echo ""
    echo "  # After (Django 5.0+)"
    echo "  from zoneinfo import ZoneInfo"
    echo "  tz = ZoneInfo('America/New_York')"
    echo "  dt = make_aware(naive_dt, timezone=tz)"
fi
echo ""
