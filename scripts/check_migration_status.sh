#!/bin/bash
# Check Django migration status
# Helps answer Q1: Are all migrations applied in production?

echo "==================================================="
echo "Django Migration Status Check"
echo "==================================================="
echo ""

echo "=== All Migrations ==="
python manage.py showmigrations

echo ""
echo "=== Summary ==="
TOTAL=$(python manage.py showmigrations | grep -E "^\[" | wc -l)
APPLIED=$(python manage.py showmigrations | grep "\[X\]" | wc -l)
UNAPPLIED=$(python manage.py showmigrations | grep "\[ \]" | wc -l)

echo "Total migrations: $TOTAL"
echo "Applied: $APPLIED"
echo "Unapplied: $UNAPPLIED"

echo ""
if [ $UNAPPLIED -eq 0 ]; then
    echo "✅ All migrations applied!"
    echo "   → Q1 Answer: YES - All migrations in production"
    echo "   → Implication: Safer to leave migrations as-is"
else
    echo "⚠️  $UNAPPLIED migrations not yet applied"
    echo "   → Q1 Answer: NO - Some migrations pending"
    echo "   → Implication: Need to keep pytz or add compatibility"
    echo ""
    echo "=== Unapplied Migrations ==="
    python manage.py showmigrations | grep "\[ \]"
fi
