# Django 5.2 Upgrade Guide for Banking Applications

**Current Version:** Django 4.2 LTS
**Target Version:** Django 5.2
**Upgrade Path:** 4.2 → 5.0 → 5.1 → 5.2 (or direct 4.2 → 5.2)
**Application Type:** Banking/Financial (High-risk, Low-tolerance)
**Python Version:** 3.11+

---

## Table of Contents

1. [Version Upgrade Path](#version-upgrade-path)
2. [Django 5.2 New Features](#django-52-new-features)
3. [Breaking Changes by Version](#breaking-changes-by-version)
4. [Testing Strategy](#testing-strategy)
5. [Dependencies & Libraries](#dependencies--libraries)
6. [Migration Timeline](#migration-timeline)

---

## Version Upgrade Path

### Recommended Approach: Incremental Upgrades

```
Django 4.2 LTS (Current)
    ↓
Django 5.0 (Stabilize for 2-4 weeks)
    ↓
Django 5.1 (Stabilize for 2-4 weeks)
    ↓
Django 5.2 (Final target)
```

**Why Incremental?**
- ✅ Isolate issues to specific version changes
- ✅ Easier rollback if problems found
- ✅ Team can learn new features gradually
- ✅ Lower risk for banking applications

### Alternative: Direct Upgrade (Higher Risk)

```
Django 4.2 LTS → Django 5.2 (Direct jump)
```

**When to Use:**
- Small codebase (< 50k lines)
- Comprehensive test coverage (> 90%)
- Dedicated 3-month migration project
- Strong rollback plan

---

## Django 5.2 New Features

### Major New Features

#### 1. **Database Connection Management**
- Persistent database connections with better pooling
- Connection health checks
- Better handling of stale connections

**Banking Impact:** 🟡 Medium
- Improved performance for high-transaction systems
- Better connection reliability

**Action Required:**
```python
# settings.py - Review connection settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'banking_db',
        'CONN_MAX_AGE': 600,  # Review this value
        'CONN_HEALTH_CHECKS': True,  # New in 5.2
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

---

#### 2. **Async ORM Improvements**
- More async query operations
- Async prefetch_related improvements
- Better async transaction support

**Banking Impact:** 🟢 Low (if not using async)
- Can adopt gradually
- No breaking changes for sync code

**Example:**
```python
# New async capabilities
async def get_account_with_transactions(account_id):
    account = await Account.objects.select_related('user').aget(id=account_id)
    transactions = await Transaction.objects.filter(account=account).afetch_all()
    return account, transactions
```

---

#### 3. **Enhanced Model Field Validation**
- Better validation error messages
- Field-level constraint validation
- Improved JSONField validation

**Banking Impact:** 🟡 Medium
- Better error handling for financial data
- More explicit validation errors

**Example:**
```python
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Transaction(models.Model):
    amount = models.DecimalField(
        max_digits=19,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        error_messages={
            'invalid': 'Transaction amount must be a valid decimal.',
            'min_value': 'Transaction amount must be at least $0.01.'
        }
    )
```

---

#### 4. **Admin Enhancements**
- Improved accessibility (ARIA attributes)
- Better mobile responsiveness
- Enhanced filter UI with facet counts

**Banking Impact:** 🟢 Low
- Better user experience for admin users
- No code changes required (unless custom admin)

---

#### 5. **Security Improvements**
- Enhanced CSRF protection
- Better password validation
- Improved session security

**Banking Impact:** 🔴 High
- Review all security settings
- Test authentication flows thoroughly

---

## Breaking Changes by Version

### Django 5.0 Breaking Changes (Must Address First)

#### Critical (P0)
1. **pytz support removed** → Use zoneinfo
2. **USE_TZ default is True** → Review all datetime handling
3. **is_dst parameter removed** → Update all timezone functions
4. **PostgreSQL aggregates return None** → Handle null values
5. **MySQL 8.0.11+ required** → Upgrade database
6. **SQLite 3.27.0+ required** → Check version

#### Important (P1)
1. **Form rendering changed to div-based** → Update CSS
2. **Admin template structure changed** → Review custom admin
3. **UUIDField on MariaDB 10.7+** → Create compatibility field

**Full details:** See BREAKING_CHANGES_REVIEW.md

---

### Django 5.1 Breaking Changes

#### Critical (P0)
1. **Changed:** Default `SECRET_KEY_FALLBACKS` behavior
2. **Removed:** Deprecated `FileField.primary_key` support
3. **Changed:** Admin site login template path

#### Important (P1)
1. **Changed:** QuerySet.select_for_update() behavior with PostgreSQL
2. **Updated:** Admin CSS class names for better accessibility
3. **Changed:** Form error rendering includes ARIA attributes

**Scanner:**
```bash
python scripts/scan_django_51_changes.py
```

---

### Django 5.2 Breaking Changes

#### Critical (P0)
1. **Changed:** Database connection pooling defaults
2. **Updated:** Transaction isolation level handling
3. **Changed:** Cache key validation (stricter)

#### Important (P1)
1. **Updated:** Admin responsive breakpoints
2. **Changed:** Model validation runs during save() by default
3. **Updated:** JSONField serialization format

**Scanner:**
```bash
python scripts/scan_django_52_changes.py
```

---

## Testing Strategy

### Phase 1: Automated Testing (Weeks 1-2)

#### 1.1 Unit Tests
**Goal:** All unit tests pass at each version

```bash
# Test suite execution plan
# 1. Django 4.2 baseline
python manage.py test --verbosity=2 --parallel=4
# Document pass rate: _____% (baseline)

# 2. Upgrade to Django 5.0
pip install Django==5.0
python manage.py test --verbosity=2 --parallel=4
# Fix failures, document changes

# 3. Upgrade to Django 5.1
pip install Django==5.1
python manage.py test --verbosity=2 --parallel=4
# Fix failures, document changes

# 4. Upgrade to Django 5.2
pip install Django==5.2
python manage.py test --verbosity=2 --parallel=4
# Fix failures, document changes
```

**Success Criteria:**
- [ ] 100% of tests passing
- [ ] No new deprecation warnings
- [ ] Test execution time within 20% of baseline
- [ ] No flaky tests introduced

---

#### 1.2 Integration Tests
**Focus:** Database, external services, third-party integrations

```python
# tests/integration/test_django_52_compatibility.py

from django.test import TransactionTestCase
from decimal import Decimal

class Django52CompatibilityTests(TransactionTestCase):
    """Test Django 5.2 specific changes."""

    def test_database_connection_health_checks(self):
        """Verify connection health checks work."""
        from django.db import connection

        # Test connection is healthy
        self.assertTrue(connection.ensure_connection())

    def test_postgresql_aggregate_null_handling(self):
        """Verify aggregates handle None correctly."""
        from django.contrib.postgres.aggregates import ArrayAgg

        # Should return None, not []
        result = Account.objects.filter(
            id=-999
        ).aggregate(tags=ArrayAgg('tags'))

        self.assertIsNone(result['tags'])

    def test_timezone_handling_with_zoneinfo(self):
        """Verify timezone handling with zoneinfo."""
        from zoneinfo import ZoneInfo
        from django.utils import timezone

        tz = ZoneInfo('America/New_York')
        dt = timezone.now().astimezone(tz)

        # Should work without pytz
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo.key, 'America/New_York')
```

**Test Coverage:**
- [ ] Database connection pooling
- [ ] Timezone handling (pytz → zoneinfo)
- [ ] PostgreSQL aggregates (None handling)
- [ ] Transaction isolation levels
- [ ] Cache operations
- [ ] Session management
- [ ] File storage operations

---

#### 1.3 Performance Testing
**Goal:** No performance regression

```python
# tests/performance/test_django_52_performance.py

import time
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings

class PerformanceTests(TestCase):
    """Performance benchmarking for Django 5.2."""

    def test_query_performance_baseline(self):
        """Benchmark query performance."""
        # Create test data
        accounts = [Account(name=f'Account {i}') for i in range(1000)]
        Account.objects.bulk_create(accounts)

        # Benchmark query
        start = time.time()
        list(Account.objects.select_related('user').all()[:100])
        elapsed = time.time() - start

        # Should complete in < 100ms
        self.assertLess(elapsed, 0.1)

    def test_transaction_processing_performance(self):
        """Benchmark transaction creation."""
        account = Account.objects.create(name='Test Account')

        start = time.time()
        for i in range(100):
            Transaction.objects.create(
                account=account,
                amount=Decimal('100.00'),
                type='DEBIT'
            )
        elapsed = time.time() - start

        # Should complete in < 500ms for 100 transactions
        self.assertLess(elapsed, 0.5)
```

**Metrics to Track:**

| Metric | Baseline (4.2) | Target (5.2) | Threshold |
|--------|----------------|--------------|-----------|
| Query execution time | 50ms | 50ms | < 55ms (+10%) |
| Transaction processing | 200ms | 200ms | < 220ms (+10%) |
| Admin page load | 150ms | 150ms | < 165ms (+10%) |
| API response time | 100ms | 100ms | < 110ms (+10%) |
| Database connections | 10 | 10 | < 15 (+50%) |
| Memory usage | 500MB | 500MB | < 550MB (+10%) |

---

### Phase 2: Manual Testing (Weeks 3-4)

#### 2.1 Banking Critical Paths

**Test Scenarios:**

1. **User Authentication & Authorization**
   ```
   Test Cases:
   - [ ] User login with valid credentials
   - [ ] User login with invalid credentials
   - [ ] Multi-factor authentication flow
   - [ ] Password reset flow
   - [ ] Session timeout handling
   - [ ] Permission-based access control
   ```

2. **Transaction Processing**
   ```
   Test Cases:
   - [ ] Create debit transaction
   - [ ] Create credit transaction
   - [ ] Transaction timestamp accuracy (timezone testing)
   - [ ] Transaction rollback on error
   - [ ] Concurrent transaction handling
   - [ ] Transaction history query performance
   ```

3. **End-of-Day (EOD) Processing**
   ```
   Test Cases:
   - [ ] EOD batch processing
   - [ ] Timezone handling (5PM ET = 10PM UTC)
   - [ ] Interest calculation accuracy
   - [ ] Report generation
   - [ ] Balance reconciliation
   ```

4. **Financial Calculations**
   ```
   Test Cases:
   - [ ] Interest calculation (precision to 2 decimals)
   - [ ] Fee calculation
   - [ ] Currency conversion (if applicable)
   - [ ] Tax calculation
   - [ ] Balance calculation
   ```

5. **Reporting & Exports**
   ```
   Test Cases:
   - [ ] Transaction reports (CSV, PDF)
   - [ ] Account statements
   - [ ] Regulatory reports
   - [ ] Data export functionality
   - [ ] Report date range handling (timezone aware)
   ```

6. **Admin Interface**
   ```
   Test Cases:
   - [ ] User management
   - [ ] Transaction management
   - [ ] Custom admin actions
   - [ ] Filter functionality
   - [ ] Search functionality
   - [ ] Bulk operations
   ```

---

#### 2.2 Edge Cases & Error Handling

```
Critical Edge Cases:
- [ ] Timezone boundary testing (DST transitions)
- [ ] Leap year date handling
- [ ] Maximum decimal precision (19 digits, 2 decimals)
- [ ] Concurrent user access
- [ ] Database connection failures
- [ ] External API failures
- [ ] Invalid input data handling
- [ ] Unicode character handling in names/addresses
```

---

#### 2.3 Browser Compatibility (Admin Interface)

```
Test Browsers:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Android)
```

---

### Phase 3: Staging Environment Testing (Weeks 5-6)

#### 3.1 Full System Integration

```bash
# Staging deployment checklist
- [ ] Deploy Django 5.2 to staging
- [ ] Run database migrations
- [ ] Verify all services start correctly
- [ ] Run full test suite in staging
- [ ] Load test with production-like data volume
- [ ] Monitor for 7 days
```

#### 3.2 Data Migration Validation

```python
# scripts/validate_data_migration.py

from django.core.management.base import BaseCommand
from decimal import Decimal

class Command(BaseCommand):
    help = 'Validate data after Django 5.2 migration'

    def handle(self, *args, **options):
        # Check transaction timestamps
        transactions_with_naive_dt = Transaction.objects.filter(
            created_at__isnull=False
        ).extra(
            where=["created_at AT TIME ZONE 'UTC' = created_at"]
        ).count()

        if transactions_with_naive_dt > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Found {transactions_with_naive_dt} transactions '
                    'with naive datetimes'
                )
            )
            return

        # Check decimal precision
        invalid_amounts = Transaction.objects.filter(
            amount__isnull=False
        ).extra(
            where=["CAST(amount AS TEXT) ~ '\\.\\d{3,}'"]
        ).count()

        if invalid_amounts > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'Found {invalid_amounts} transactions '
                    'with invalid decimal precision'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS('All data validation checks passed')
        )
```

---

#### 3.3 Performance Benchmarking

```bash
# Use locust or similar for load testing
# tests/load/locustfile.py

from locust import HttpUser, task, between
from decimal import Decimal
import random

class BankingUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        self.client.post("/login/", {
            "username": "test_user",
            "password": "test_password"
        })

    @task(3)
    def view_account(self):
        """View account details."""
        self.client.get("/accounts/1/")

    @task(2)
    def view_transactions(self):
        """View transaction history."""
        self.client.get("/transactions/")

    @task(1)
    def create_transaction(self):
        """Create a new transaction."""
        self.client.post("/transactions/create/", {
            "account": 1,
            "amount": Decimal(random.uniform(10, 1000)),
            "type": random.choice(["DEBIT", "CREDIT"])
        })

# Run load test
# locust -f tests/load/locustfile.py --host=https://staging.bank.com
```

**Load Test Targets:**
- 1,000 concurrent users
- 95th percentile response time < 200ms
- Error rate < 0.1%
- Sustained load for 1 hour

---

### Phase 4: Production Rollout (Weeks 7-9)

#### 4.1 Pre-Production Checklist

```
- [ ] All staging tests passed
- [ ] Performance benchmarks met
- [ ] Security audit completed
- [ ] Database backup verified
- [ ] Rollback plan tested
- [ ] Monitoring dashboards configured
- [ ] Team trained on changes
- [ ] Stakeholder sign-off obtained
- [ ] Communication plan ready
- [ ] Deployment window scheduled (low-traffic time)
```

---

#### 4.2 Deployment Steps

```bash
# 1. Pre-deployment
- [ ] Final database backup
- [ ] Put site in maintenance mode
- [ ] Stop background jobs (Celery)

# 2. Deployment
- [ ] Deploy new code
- [ ] Run migrations: python manage.py migrate
- [ ] Collect static files: python manage.py collectstatic --noinput
- [ ] Run post-deployment checks

# 3. Post-deployment
- [ ] Start services
- [ ] Remove maintenance mode
- [ ] Monitor for 15 minutes
- [ ] Run smoke tests
- [ ] Monitor for 24 hours intensive
- [ ] Monitor for 7 days ongoing
```

---

#### 4.3 Post-Deployment Monitoring

**Critical Metrics (First 24 Hours):**

```python
# monitoring/django_52_metrics.py

CRITICAL_METRICS = {
    'error_rate': {
        'baseline': 0.05,  # 0.05% error rate
        'alert_threshold': 0.10,  # Alert if > 0.10%
        'rollback_threshold': 0.20,  # Rollback if > 0.20%
    },
    'response_time_p95': {
        'baseline': 200,  # 200ms
        'alert_threshold': 250,  # Alert if > 250ms
        'rollback_threshold': 400,  # Rollback if > 400ms
    },
    'database_connections': {
        'baseline': 50,
        'alert_threshold': 80,
        'rollback_threshold': 95,
    },
    'transaction_processing_time': {
        'baseline': 150,  # 150ms
        'alert_threshold': 200,
        'rollback_threshold': 300,
    },
    'timezone_errors': {
        'baseline': 0,
        'alert_threshold': 0,
        'rollback_threshold': 1,  # Any timezone error triggers rollback
    }
}
```

**Monitoring Checklist:**
- [ ] Error logs (real-time for first 4 hours)
- [ ] Performance metrics (every 5 minutes)
- [ ] Database query performance
- [ ] Memory usage
- [ ] CPU usage
- [ ] API response times
- [ ] Background job success rate
- [ ] User authentication success rate
- [ ] Transaction processing accuracy

---

## Dependencies & Libraries

See DEPENDENCIES_COMPATIBILITY.md for full details.

### Critical Dependencies

| Package | 4.2 Version | 5.2 Compatible | Notes |
|---------|-------------|-----------------|-------|
| Django | 4.2.x | 5.2.x | Core framework |
| psycopg2 | 2.9.x | 3.1.x | PostgreSQL adapter (major upgrade) |
| celery | 5.2.x | 5.4.x | Background tasks |
| redis | 4.5.x | 5.0.x | Cache backend |
| djangorestframework | 3.14.x | 3.15.x | API framework |
| django-oauth-toolkit | 2.2.x | 3.0.x | OAuth2 provider |
| pytz | 2023.3 | N/A | **Remove or keep for migrations** |

**Next Steps:**
1. Review DEPENDENCIES_COMPATIBILITY.md
2. Run dependency scanner
3. Create upgrade matrix

---

## Migration Timeline

### Complete Timeline: 4.2 → 5.2

**Total Duration:** 9-12 weeks

```
Week 1-2:   Django 5.0 upgrade + testing
Week 3-4:   Django 5.1 upgrade + testing
Week 5-6:   Django 5.2 upgrade + testing
Week 7-8:   Staging validation
Week 9-10:  Production deployment + monitoring
Week 11-12: Post-deployment stabilization
```

**See MIGRATION_TIMELINE.md for detailed Gantt charts.**

---

## Next Steps

1. **Read this guide completely**
2. **Review DEPENDENCIES_COMPATIBILITY.md** (next document)
3. **Run scanning tools** to assess current state
4. **Fill out MIGRATION_DECISION_ASSESSMENT.md**
5. **Create project timeline** based on your findings
6. **Get stakeholder approval**
7. **Begin Phase 1 testing**

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for Use
