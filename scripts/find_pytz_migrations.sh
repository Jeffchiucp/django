#!/bin/bash
# Find pytz usage in Django migrations
# Helps answer Q3: Do migrations have RunPython using pytz?

echo "==================================================="
echo "pytz Usage in Migrations Analysis"
echo "==================================================="
echo ""

echo "=== Step 1: Find migrations with pytz imports ==="
PYTZ_MIGRATIONS=$(find . -path "*/migrations/*.py" -not -path "*/\.*" -exec grep -l "import pytz\|from pytz" {} \;)

if [ -z "$PYTZ_MIGRATIONS" ]; then
    echo "✅ No migrations import pytz!"
    echo "   → Q3 Answer: NO - No RunPython with pytz"
    echo "   → Implication: Safe to leave as-is"
    echo ""
    echo "🎯 RECOMMENDATION: Path A (Remove pytz) or Path C (Keep pytz)"
    exit 0
fi

echo "$PYTZ_MIGRATIONS"
PYTZ_COUNT=$(echo "$PYTZ_MIGRATIONS" | wc -l)
echo ""
echo "Found $PYTZ_COUNT migration(s) with pytz imports"
echo ""

echo "=== Step 2: Find migrations with RunPython ==="
RUNPYTHON_MIGRATIONS=$(find . -path "*/migrations/*.py" -not -path "*/\.*" -exec grep -l "RunPython" {} \;)

if [ -z "$RUNPYTHON_MIGRATIONS" ]; then
    echo "ℹ️  No RunPython migrations found"
    echo "   (pytz imports are likely just unused)"
    echo ""
    echo "🎯 RECOMMENDATION: Path A (Remove pytz) - Just unused imports"
    exit 0
fi

echo "$RUNPYTHON_MIGRATIONS"
RUNPYTHON_COUNT=$(echo "$RUNPYTHON_MIGRATIONS" | wc -l)
echo ""
echo "Found $RUNPYTHON_COUNT migration(s) with RunPython"
echo ""

echo "=== Step 3: Find migrations with BOTH RunPython AND pytz ==="
echo ""

CRITICAL_COUNT=0
for file in $RUNPYTHON_MIGRATIONS; do
    if echo "$PYTZ_MIGRATIONS" | grep -q "$file"; then
        echo "🔴 CRITICAL: $file"
        echo "   Contains RunPython that may use pytz"
        echo ""
        echo "   Preview:"
        grep -n "def \|pytz\." "$file" | head -8 | sed 's/^/   /'
        echo "   ---"
        echo ""
        CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
    fi
done

echo "=== Summary ==="
echo "Migrations with pytz imports: $PYTZ_COUNT"
echo "Migrations with RunPython: $RUNPYTHON_COUNT"
echo "Migrations with BOTH (CRITICAL): $CRITICAL_COUNT"
echo ""

if [ $CRITICAL_COUNT -eq 0 ]; then
    echo "✅ No RunPython migrations use pytz"
    echo "   → Q3 Answer: NO"
    echo "   → Implication: Safe to leave migrations as-is"
    echo ""
    echo "🎯 RECOMMENDATION: Path A (Remove pytz) or Path C (Keep pytz)"
elif [ $CRITICAL_COUNT -le 3 ]; then
    echo "⚠️  $CRITICAL_COUNT migration(s) have RunPython with pytz"
    echo "   → Q3 Answer: YES (Few migrations)"
    echo "   → Implication: Must keep pytz OR create compatibility layer"
    echo ""
    echo "🎯 RECOMMENDATION: Path B (Compatibility layer) or Path C (Keep pytz)"
else
    echo "🔴 $CRITICAL_COUNT migrations have RunPython with pytz"
    echo "   → Q3 Answer: YES (Many migrations)"
    echo "   → Implication: Should keep pytz"
    echo ""
    echo "🎯 RECOMMENDATION: Path C (Keep pytz)"
fi

echo ""
echo "Next step: Run analyze_pytz_migrations.py for detailed analysis"
