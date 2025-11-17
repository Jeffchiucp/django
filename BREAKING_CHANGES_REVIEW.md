# Django 5.0 Breaking Changes Review Framework

**Target Migration:** Django 4.2 → 5.0 → 5.2
**Application Type:** Banking Application (High-risk, Low-tolerance)
**Python Version:** 3.11
**Review Date:** 2025-11-17

---

## Table of Contents

1. [Review Methodology](#review-methodology)
2. [Critical Breaking Changes](#critical-breaking-changes)
3. [Impact Assessment Matrix](#impact-assessment-matrix)
4. [Testing Strategy](#testing-strategy)
5. [Code Scanning Scripts](#code-scanning-scripts)
6. [Checklist by Category](#checklist-by-category)

---

## Review Methodology

### 5-Step Review Process

```
Step 1: Categorize Changes
    ↓
Step 2: Scan Codebase for Impact
    ↓
Step 3: Assess Risk & Priority
    ↓
Step 4: Create Mitigation Plan
    ↓
Step 5: Test & Validate
```

### Change Categories

| Category | Risk Level | Review Priority | Examples |
|----------|------------|----------------|----------|
| **Removed Features** | 🔴 HIGH | P0 - Must fix | pytz support removed |
| **Changed Defaults** | 🟡 MEDIUM | P1 - Should fix | `USE_TZ=True` default |
| **API Changes** | 🟡 MEDIUM | P1 - Should fix | Method signatures |
| **Deprecated Features** | 🟢 LOW | P2 - Plan for future | Will break in Django 6.0 |
| **New Features** | 🔵 INFO | P3 - Optional | Can adopt later |

---

## Critical Breaking Changes

### 🔴 P0: Must Fix Before Upgrade

These will break your application immediately:

#### 1. pytz Support Removed (CRITICAL for Banking Apps)

**What Changed:**
```python
# ❌ Django 4.2 (REMOVED in 5.0)
import pytz
from django.utils.timezone import make_aware

tz = pytz.timezone('America/New_York')
dt = make_aware(naive_dt, timezone=tz, is_dst=None)

# ✅ Django 5.0+ (Required)
from zoneinfo import ZoneInfo
from django.utils.timezone import make_aware

tz = ZoneInfo('America/New_York')
dt = make_aware(naive_dt, timezone=tz)  # No is_dst parameter
```

**Impact:** 🔴 **CRITICAL** for banking apps with timezone-aware transactions

**How to Find:**
```bash
# Search for pytz usage
grep -r "import pytz" --include="*.py" . | grep -v migrations | grep -v ".pyc"
grep -r "from pytz" --include="*.py" . | grep -v migrations | grep -v ".pyc"

# Search for is_dst parameter
grep -r "is_dst" --include="*.py" .
```

**Migration Strategy:**
- ✅ Keep pytz for old migrations (as discussed)
- ✅ Update all application code to use zoneinfo
- ✅ Remove `is_dst` parameter from all function calls

---

#### 2. `USE_TZ` Default Changed to `True`

**What Changed:**
```python
# Django 4.2 default
USE_TZ = False  # Naive datetimes

# Django 5.0 default
USE_TZ = True   # Timezone-aware datetimes
```

**Impact:** 🔴 **CRITICAL** if you were using `USE_TZ=False`

**How to Check:**
```bash
grep "USE_TZ" settings.py
```

**Action Required:**
- If you explicitly set `USE_TZ=False`, you MUST review all datetime handling
- Banking apps should use `USE_TZ=True` (best practice)
- Audit all datetime comparisons and database queries

---

#### 3. MySQL 8.0.11+ Required

**What Changed:**
- Django 4.2: Supported MySQL 5.7+
- Django 5.0: Requires MySQL 8.0.11+

**Impact:** 🟡 **MEDIUM** - Infrastructure change required

**How to Check:**
```bash
# On database server
mysql --version
# OR in Django
python manage.py dbshell
SELECT VERSION();
```

**Action Required:**
- Upgrade MySQL to 8.0.11+ before Django upgrade
- Test all queries after MySQL upgrade

---

#### 4. SQLite 3.27.0+ Required

**What Changed:**
- Django 4.2: SQLite 3.21.0+
- Django 5.0: SQLite 3.27.0+

**Impact:** 🟢 **LOW** - Usually not production database

**How to Check:**
```python
import sqlite3
print(sqlite3.sqlite_version)
```

---

#### 5. Removed: `django.contrib.postgres` Aggregates Return Behavior

**What Changed:**
```python
# Django 4.2
ArrayAgg('field')     # Returns [] when no rows
StringAgg('field')    # Returns '' when no rows

# Django 5.0
ArrayAgg('field')     # Returns None when no rows
StringAgg('field')    # Returns None when no rows
```

**Impact:** 🟡 **MEDIUM** if using PostgreSQL aggregates

**How to Find:**
```bash
grep -r "ArrayAgg\|JSONBAgg\|StringAgg" --include="*.py" .
```

**Action Required:**
```python
# Update code to handle None
from django.contrib.postgres.aggregates import ArrayAgg

# Before (may break)
tags = Model.objects.aggregate(tags=ArrayAgg('tag'))['tags']
for tag in tags:  # ❌ Will fail if tags is None
    ...

# After (safe)
tags = Model.objects.aggregate(tags=ArrayAgg('tag'))['tags']
for tag in tags or []:  # ✅ Handle None
    ...
```

---

#### 6. Integer Validation on SQLite (64-bit)

**What Changed:**
- Django now validates integers as 64-bit on SQLite
- Previously allowed values outside 64-bit range

**Impact:** 🟢 **LOW** - Good change for data integrity

**How to Test:**
```python
# Check if you have any integer fields with extreme values
from django.db.models import Max, Min

for model in apps.get_models():
    for field in model._meta.fields:
        if isinstance(field, models.IntegerField):
            max_val = model.objects.aggregate(Max(field.name))
            min_val = model.objects.aggregate(Min(field.name))
            # Check if within 64-bit range
```

---

### 🟡 P1: Should Fix (May Cause Issues)

#### 7. QuerySet.update_or_create() with `create_defaults` Field

**What Changed:**
```python
class MyModel(models.Model):
    create_defaults = models.CharField(max_length=100)  # Field named "create_defaults"

# Django 4.2
MyModel.objects.update_or_create(
    name='test',
    create_defaults='value'  # This set the field
)

# Django 5.0 (create_defaults is now a parameter)
MyModel.objects.update_or_create(
    name='test',
    create_defaults__exact='value'  # Must use __exact lookup
)
```

**Impact:** 🟡 **MEDIUM** if you have a field named `create_defaults`

**How to Find:**
```bash
grep -r "create_defaults\s*=" --include="*.py" models.py
```

---

#### 8. UUIDField on MariaDB 10.7+

**What Changed:**
- Django 4.2: `UUIDField` → `CHAR(32)` on MariaDB
- Django 5.0: `UUIDField` → `UUID` column on MariaDB 10.7+

**Impact:** 🟡 **MEDIUM** if using MariaDB 10.7+ with UUIDs

**Action Required:**
```python
# Create a compatibility field
class Char32UUIDField(models.UUIDField):
    def db_type(self, connection):
        return "char(32)"

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        if value is not None:
            value = value.hex
        return value

# Replace in models
class MyModel(models.Model):
    # Before
    # uuid = models.UUIDField(primary_key=True)

    # After
    uuid = Char32UUIDField(primary_key=True)  # Maintains CHAR(32)
```

**How to Check:**
```bash
# Check if using MariaDB
python manage.py dbshell
SELECT VERSION();  # Check for MariaDB 10.7+

# Find UUIDField usage
grep -r "UUIDField" --include="*.py" models.py
```

---

#### 9. Form Rendering Changes (Accessibility)

**What Changed:**
```html
<!-- Django 4.2: Default table rendering -->
<tr><th><label>Field:</label></th><td><input></td></tr>

<!-- Django 5.0: Default div rendering -->
<div><label>Field:</label><input aria-describedby="..."></div>
```

**Impact:** 🟡 **MEDIUM** - May break custom CSS/templates

**How to Check:**
```bash
# Find custom form templates
find templates/ -name "*.html" -exec grep -l "as_table\|as_p\|as_ul" {} \;
```

**Action Required:**
- Review all form templates
- Update CSS for div-based rendering
- Test accessibility features

---

#### 10. Admin Template Changes

**What Changed:**
```html
<!-- Django 4.2 -->
<h1>{{ site_header }}</h1>
<div id="content">...</div>

<!-- Django 5.0 -->
<header><div>{{ site_header }}</div></header>
<main id="content">...</main>
```

**Impact:** 🟡 **MEDIUM** - Custom admin templates may break

**How to Find:**
```bash
find templates/admin/ -name "*.html"
grep -r "site_header" templates/
```

---

### 🟢 P2: Plan for Future (Deprecated in 5.0)

#### 11. cx_Oracle Deprecated (Use oracledb)

**What Changed:**
- `cx_Oracle` is deprecated
- Use `oracledb` 1.3.2+ instead

**Impact:** 🟢 **LOW** if using Oracle, 🔵 **NONE** if not

**How to Check:**
```bash
pip list | grep cx_Oracle
grep -r "cx_Oracle" requirements.txt
```

**Action:**
```bash
# Uninstall cx_Oracle
pip uninstall cx_Oracle

# Install oracledb
pip install oracledb>=1.3.2
```

---

#### 12. URLField Default Scheme Change (Django 6.0)

**What Changed:**
- Django 5.0: Default scheme is "http" (with deprecation warning)
- Django 6.0: Default scheme will be "https"

**Impact:** 🟢 **LOW** - Prepare for Django 6.0

**Action:**
```python
# settings.py
# Opt into future behavior now
FORMS_URLFIELD_ASSUME_HTTPS = True
```

---

## Impact Assessment Matrix

### Severity Scoring

| Factor | Weight | Your Score | Notes |
|--------|--------|------------|-------|
| **pytz Usage** | ×10 | ___/10 | How much pytz in application code? |
| **PostgreSQL Aggregates** | ×5 | ___/10 | ArrayAgg, StringAgg usage? |
| **Custom Forms** | ×3 | ___/10 | Custom form templates? |
| **Admin Customization** | ×3 | ___/10 | Custom admin templates? |
| **Oracle Database** | ×2 | ___/10 | Using cx_Oracle? |
| **MariaDB 10.7+** | ×5 | ___/10 | Using UUIDField on MariaDB? |

**Total Risk Score:** _______/450

**Risk Levels:**
- 0-100: 🟢 Low Risk - Few breaking changes
- 101-250: 🟡 Medium Risk - Several areas need attention
- 251-450: 🔴 High Risk - Significant migration effort required

---

## Testing Strategy

### Phase 1: Static Analysis (Week 1)

Run all code scanning scripts (see below) to identify affected code.

**Deliverable:** Impact report with list of files to change

---

### Phase 2: Development Environment (Week 2)

1. Create Django 5.0 development environment
2. Run test suite
3. Document all failures
4. Fix P0 issues

**Deliverable:** All tests passing in dev

---

### Phase 3: Manual Testing (Week 3-4)

Focus on banking-critical features:

- [ ] User authentication/authorization
- [ ] Transaction processing
- [ ] Date/time handling (especially timezones)
- [ ] Financial calculations
- [ ] Report generation
- [ ] Admin interface
- [ ] API endpoints
- [ ] Background jobs (Celery)

**Deliverable:** Manual test results documented

---

### Phase 4: Staging Deployment (Week 5-6)

1. Deploy to staging
2. Run full regression test suite
3. Performance benchmarking
4. Security audit

**Deliverable:** Staging sign-off

---

## Code Scanning Scripts

### Script 1: Detect pytz Usage

```bash
#!/bin/bash
# scan_pytz_usage.sh

echo "=== Scanning for pytz usage in application code ==="
echo ""

echo "Files importing pytz (excluding migrations):"
find . -name "*.py" ! -path "*/migrations/*" -exec grep -l "import pytz\|from pytz" {} \;

echo ""
echo "is_dst parameter usage:"
grep -r "is_dst" --include="*.py" . | grep -v ".pyc"

echo ""
echo "pytz.timezone() usage:"
grep -r "pytz\.timezone" --include="*.py" . | grep -v migrations | grep -v ".pyc"

echo ""
echo "RECOMMENDATION: Replace all with zoneinfo"
```

---

### Script 2: Detect PostgreSQL Aggregate Usage

```bash
#!/bin/bash
# scan_postgres_aggregates.sh

echo "=== Scanning for PostgreSQL aggregate usage ==="
echo ""

echo "ArrayAgg usage:"
grep -rn "ArrayAgg" --include="*.py" . | grep -v ".pyc"

echo ""
echo "StringAgg usage:"
grep -rn "StringAgg" --include="*.py" . | grep -v ".pyc"

echo ""
echo "JSONBAgg usage:"
grep -rn "JSONBAgg" --include="*.py" . | grep -v ".pyc"

echo ""
echo "RECOMMENDATION: Update to handle None return value"
```

---

### Script 3: Comprehensive Breaking Change Scanner

```python
#!/usr/bin/env python3
# scan_breaking_changes.py

"""
Scan Django project for Django 5.0 breaking changes.
"""

import os
import re
from pathlib import Path
from collections import defaultdict


class BreakingChangeScanner:
    """Scan for Django 5.0 breaking changes."""

    def __init__(self, project_root='.'):
        self.project_root = Path(project_root)
        self.results = defaultdict(list)

    def scan_all(self):
        """Run all scans."""
        print("🔍 Scanning for Django 5.0 breaking changes...\n")

        self.scan_pytz_usage()
        self.scan_postgres_aggregates()
        self.scan_use_tz_setting()
        self.scan_update_or_create()
        self.scan_form_rendering()
        self.scan_uuid_fields()
        self.scan_deprecated_features()

        self.print_report()

    def scan_pytz_usage(self):
        """Scan for pytz usage."""
        print("Scanning for pytz usage...")

        for py_file in self.project_root.rglob('*.py'):
            if 'migrations' in py_file.parts:
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                if re.search(r'import pytz|from pytz', content):
                    self.results['pytz_import'].append(str(py_file))

                if 'is_dst' in content:
                    lines = [i+1 for i, line in enumerate(content.split('\n'))
                            if 'is_dst' in line]
                    self.results['is_dst_param'].append(f"{py_file}:{lines}")

            except Exception:
                pass

    def scan_postgres_aggregates(self):
        """Scan for PostgreSQL aggregate usage."""
        print("Scanning for PostgreSQL aggregates...")

        aggregates = ['ArrayAgg', 'StringAgg', 'JSONBAgg']

        for py_file in self.project_root.rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                for agg in aggregates:
                    if agg in content:
                        lines = [i+1 for i, line in enumerate(content.split('\n'))
                                if agg in line]
                        self.results[f'{agg}_usage'].append(f"{py_file}:{lines}")
            except Exception:
                pass

    def scan_use_tz_setting(self):
        """Check USE_TZ setting."""
        print("Checking USE_TZ setting...")

        settings_files = list(self.project_root.rglob('settings*.py'))

        for settings_file in settings_files:
            try:
                with open(settings_file, 'r') as f:
                    content = f.read()

                if re.search(r'USE_TZ\s*=\s*False', content):
                    self.results['use_tz_false'].append(str(settings_file))
                elif 'USE_TZ' not in content:
                    self.results['use_tz_missing'].append(str(settings_file))
            except Exception:
                pass

    def scan_update_or_create(self):
        """Scan for update_or_create with create_defaults field."""
        print("Scanning for update_or_create usage...")

        # First find models with create_defaults field
        models_with_field = []
        for py_file in self.project_root.rglob('models.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                if re.search(r'create_defaults\s*=\s*models\.', content):
                    models_with_field.append(str(py_file))
            except Exception:
                pass

        if models_with_field:
            self.results['create_defaults_field'] = models_with_field

    def scan_form_rendering(self):
        """Scan for form rendering."""
        print("Scanning for form rendering...")

        for html_file in self.project_root.rglob('*.html'):
            try:
                with open(html_file, 'r') as f:
                    content = f.read()

                if re.search(r'\.as_table|\.as_p|\.as_ul', content):
                    self.results['form_rendering'].append(str(html_file))
            except Exception:
                pass

    def scan_uuid_fields(self):
        """Scan for UUIDField usage."""
        print("Scanning for UUIDField usage...")

        for py_file in self.project_root.rglob('models.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                if 'UUIDField' in content:
                    lines = [i+1 for i, line in enumerate(content.split('\n'))
                            if 'UUIDField' in line]
                    self.results['uuid_field'].append(f"{py_file}:{lines}")
            except Exception:
                pass

    def scan_deprecated_features(self):
        """Scan for deprecated features."""
        print("Scanning for deprecated features...")

        deprecated_patterns = {
            'cx_Oracle': r'import cx_Oracle|from cx_Oracle',
            'DjangoDivFormRenderer': r'DjangoDivFormRenderer',
            'format_html_no_args': r'format_html\(\s*\)',
        }

        for name, pattern in deprecated_patterns.items():
            for py_file in self.project_root.rglob('*.py'):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                    if re.search(pattern, content):
                        self.results[f'deprecated_{name}'].append(str(py_file))
                except Exception:
                    pass

    def print_report(self):
        """Print scan results."""
        print("\n" + "="*70)
        print("DJANGO 5.0 BREAKING CHANGES SCAN RESULTS")
        print("="*70 + "\n")

        if not self.results:
            print("✅ No breaking changes detected!\n")
            return

        # Priority 0: Critical issues
        critical_issues = []

        if self.results.get('pytz_import'):
            critical_issues.append(('pytz Usage', self.results['pytz_import']))

        if self.results.get('is_dst_param'):
            critical_issues.append(('is_dst Parameter', self.results['is_dst_param']))

        if self.results.get('use_tz_false'):
            critical_issues.append(('USE_TZ=False', self.results['use_tz_false']))

        if critical_issues:
            print("🔴 CRITICAL ISSUES (P0 - Must Fix)\n")
            for issue_name, files in critical_issues:
                print(f"  {issue_name}:")
                for f in files[:5]:  # Show first 5
                    print(f"    - {f}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
                print()

        # Priority 1: Important changes
        important_issues = []

        for key in ['ArrayAgg_usage', 'StringAgg_usage', 'JSONBAgg_usage']:
            if self.results.get(key):
                important_issues.append((key.replace('_usage', ''), self.results[key]))

        if self.results.get('create_defaults_field'):
            important_issues.append(('create_defaults Field', self.results['create_defaults_field']))

        if self.results.get('uuid_field'):
            important_issues.append(('UUIDField (MariaDB)', self.results['uuid_field']))

        if important_issues:
            print("🟡 IMPORTANT CHANGES (P1 - Should Fix)\n")
            for issue_name, files in important_issues:
                print(f"  {issue_name}:")
                for f in files[:3]:
                    print(f"    - {f}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")
                print()

        # Priority 2: Deprecations
        deprecated_issues = []

        for key in self.results:
            if key.startswith('deprecated_'):
                deprecated_issues.append((key.replace('deprecated_', ''), self.results[key]))

        if deprecated_issues:
            print("🟢 DEPRECATED FEATURES (P2 - Plan for Future)\n")
            for issue_name, files in deprecated_issues:
                print(f"  {issue_name}:")
                for f in files[:3]:
                    print(f"    - {f}")
                if len(files) > 3:
                    print(f"    ... and {len(files) - 3} more")
                print()

        # Summary
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total issues found: {sum(len(v) for v in self.results.values())}")
        print(f"Critical (P0): {len(critical_issues)}")
        print(f"Important (P1): {len(important_issues)}")
        print(f"Deprecated (P2): {len(deprecated_issues)}")
        print()
        print("Next steps:")
        print("1. Review all P0 critical issues")
        print("2. Create migration plan for P1 important changes")
        print("3. Plan deprecation updates for P2 features")
        print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Scan for Django 5.0 breaking changes')
    parser.add_argument('--path', default='.', help='Project root path')
    args = parser.parse_args()

    scanner = BreakingChangeScanner(args.path)
    scanner.scan_all()
```

---

## Checklist by Category

### Database Changes

- [ ] MySQL version >= 8.0.11
- [ ] SQLite version >= 3.27.0 (if used)
- [ ] Oracle using `oracledb` not `cx_Oracle`
- [ ] UUIDField on MariaDB 10.7+ handled
- [ ] Integer field values within 64-bit range

### Timezone Changes (CRITICAL)

- [ ] All `import pytz` replaced with `from zoneinfo import ZoneInfo`
- [ ] All `is_dst` parameters removed
- [ ] `USE_TZ=True` in settings (or explicitly set)
- [ ] All datetime handling reviewed
- [ ] Transaction timestamps tested
- [ ] EOD processing verified

### PostgreSQL Changes (if applicable)

- [ ] `ArrayAgg` returns `None` handled
- [ ] `StringAgg` returns `None` handled
- [ ] `JSONBAgg` returns `None` handled
- [ ] All aggregate queries tested

### Forms & Templates

- [ ] Form rendering updated (div-based default)
- [ ] Custom form templates reviewed
- [ ] CSS updated for new structure
- [ ] Accessibility features tested (`aria-describedby`, `aria-invalid`)

### Admin Interface

- [ ] Custom admin templates updated
- [ ] `site_header` in `<div>` not `<h1>`
- [ ] `<main>` and `<header>` tags used
- [ ] Custom admin CSS reviewed

### Models

- [ ] `update_or_create()` with `create_defaults` field name
- [ ] `GeneratedField` opportunities identified (optional)
- [ ] `db_default` parameter considered (optional)

### Testing

- [ ] All tests passing in Django 5.0 environment
- [ ] Manual testing completed
- [ ] Performance benchmarking done
- [ ] Security audit completed

---

## Summary: Recommended Approach

### For Banking Applications

**Phase 1: Assessment (1-2 weeks)**
1. Run all scanning scripts
2. Complete impact assessment matrix
3. Document all breaking changes affecting your code

**Phase 2: Fix Critical Issues (2-3 weeks)**
1. Fix all P0 issues (pytz, USE_TZ, aggregates)
2. Run test suite continuously
3. Manual testing of critical paths

**Phase 3: Staging Validation (2-3 weeks)**
1. Deploy to staging
2. Full regression testing
3. Performance validation

**Phase 4: Production (1 week)**
1. Planned deployment
2. Intensive monitoring
3. Rollback plan ready

**Total Timeline:** 6-9 weeks for Django 5.0 alone

---

## Risk Mitigation

### Rollback Plan

```bash
# If issues found in production:

# 1. Quick rollback
git revert <commit-hash>
pip install Django==4.2.X
python manage.py migrate

# 2. Database rollback (if schema changes)
python manage.py migrate <app> <previous_migration>

# 3. Full environment rollback
# Restore from backup
# Redeploy previous version
```

### Monitoring Checklist

After deployment, monitor for 7 days:

- [ ] Error rate < 0.1%
- [ ] Response time within 10% of baseline
- [ ] No timezone-related bugs reported
- [ ] Transaction processing accurate
- [ ] All financial calculations correct
- [ ] No customer complaints

---

**Created:** 2025-11-17
**Version:** 1.0
**Status:** Ready for Use
