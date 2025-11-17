# Django 5.2 Migration Testing Strategy

**For:** Banking Application Migration (Django 4.2 → 5.2)
**Risk Level:** High (Financial application)
**Testing Duration:** 6-8 weeks
**Test Coverage Goal:** 95%+

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Pyramid Structure](#test-pyramid-structure)
3. [Testing Phases](#testing-phases)
4. [Test Categories](#test-categories)
5. [Banking-Specific Test Scenarios](#banking-specific-test-scenarios)
6. [Performance Testing](#performance-testing)
7. [Security Testing](#security-testing)
8. [Test Automation](#test-automation)

---

## Testing Philosophy

### For Banking Applications

**Principle 1: Zero Tolerance for Data Errors**
- Transaction amounts must be exact (decimal precision)
- Timestamps must be accurate (timezone aware)
- Financial calculations must be verifiable

**Principle 2: Test in Isolation, Then Integrate**
- Test each Django version upgrade separately
- Test each breaking change category independently
- Then test full integration

**Principle 3: Production-Like Testing**
- Use production data volumes (anonymized)
- Test with production traffic patterns
- Simulate production load

---

## Test Pyramid Structure

```
           /\
          /  \
         / E2E \              10% - End-to-End Tests
        /------\
       /        \
      / Integration \         30% - Integration Tests
     /------------\
    /              \
   / Unit Tests     \        60% - Unit Tests
  /__________________\
```

### Distribution for Banking Apps

| Test Type | Percentage | Count (estimated) | Focus |
|-----------|-----------|-------------------|-------|
| **Unit Tests** | 60% | ~600 tests | Business logic, calculations, validators |
| **Integration Tests** | 30% | ~300 tests | Database, APIs, services, third-party |
| **E2E Tests** | 10% | ~100 tests | Critical user journeys, transactions |

---

## Testing Phases

### Phase 1: Pre-Migration Baseline (Week 1)

**Goal:** Establish current state metrics

```bash
# Run comprehensive test suite on Django 4.2
python manage.py test --verbosity=2 --parallel=4 --timing

# Document baseline metrics
- Total tests: _____
- Pass rate: _____%
- Execution time: _____ seconds
- Coverage: _____%
- Flaky tests: _____
```

**Deliverables:**
- [ ] Baseline test report
- [ ] Test coverage report (HTML)
- [ ] Performance benchmarks
- [ ] List of known failing/flaky tests

---

### Phase 2: Django 5.0 Migration Testing (Week 2-3)

**Goal:** Validate Django 5.0 upgrade

#### 2.1 Unit Test Execution

```bash
# Upgrade to Django 5.0
pip install Django==5.0

# Run tests with deprecation warnings
python -Wd manage.py test --verbosity=2

# Expected failures: pytz-related, USE_TZ, aggregates
# Fix each failure, document changes
```

**Critical Tests to Verify:**
- [ ] Timezone handling tests (pytz → zoneinfo)
- [ ] Model field validation tests
- [ ] Form rendering tests
- [ ] Admin interface tests
- [ ] API serialization tests

---

#### 2.2 Integration Test Execution

```python
# tests/integration/test_django_50_compatibility.py

from django.test import TransactionTestCase
from zoneinfo import ZoneInfo
from decimal import Decimal

class Django50CompatibilityTests(TransactionTestCase):
    """Test Django 5.0 specific changes."""

    def test_zoneinfo_transaction_timestamps(self):
        """Verify transactions use zoneinfo correctly."""
        from django.utils import timezone

        eastern = ZoneInfo('America/New_York')
        now = timezone.now().astimezone(eastern)

        transaction = Transaction.objects.create(
            amount=Decimal('100.00'),
            timestamp=now
        )

        # Verify timezone is preserved
        self.assertEqual(
            transaction.timestamp.tzinfo.key,
            'America/New_York'
        )

    def test_postgres_aggregate_null_handling(self):
        """Verify ArrayAgg returns None, not []."""
        from django.contrib.postgres.aggregates import ArrayAgg

        # Query with no results
        result = Account.objects.filter(
            id=-999
        ).aggregate(tags=ArrayAgg('tags'))

        # Should be None in Django 5.0, was [] in 4.2
        self.assertIsNone(result['tags'])

    def test_form_div_rendering(self):
        """Verify forms render with div structure."""
        from django.forms import Form, CharField

        class TestForm(Form):
            name = CharField(max_length=100)

        form = TestForm()
        html = form.as_div()

        # Should contain div tags, not table
        self.assertIn('<div>', html)
        self.assertNotIn('<table>', html)
```

---

#### 2.3 Critical Path Testing

**Banking Critical Paths to Test:**

1. **User Authentication**
   ```
   Test: Login → Dashboard → Logout
   Verify: Session handling, timezone display, CSRF tokens
   ```

2. **Transaction Creation**
   ```
   Test: Create Debit → Verify Balance → Create Credit → Verify Balance
   Verify: Decimal precision, timestamp accuracy, balance calculation
   ```

3. **EOD Processing**
   ```
   Test: Trigger EOD batch → Verify cutoff time → Check calculations
   Verify: Timezone handling (5PM ET = 10PM UTC), interest calculation
   ```

---

### Phase 3: Django 5.1 Migration Testing (Week 4-5)

**Goal:** Validate Django 5.1 upgrade

```bash
# Upgrade to Django 5.1
pip install Django==5.1

# Run full test suite
python manage.py test --verbosity=2 --parallel=4
```

**Django 5.1 Specific Tests:**

```python
# tests/compatibility/test_django_51.py

class Django51CompatibilityTests(TransactionTestCase):
    """Test Django 5.1 specific changes."""

    def test_secret_key_fallbacks(self):
        """Verify SECRET_KEY_FALLBACKS behavior."""
        from django.conf import settings

        # Should work with current SECRET_KEY
        self.assertIsNotNone(settings.SECRET_KEY)

    def test_select_for_update_behavior(self):
        """Verify select_for_update() with PostgreSQL."""
        # Test locking behavior hasn't changed
        account = Account.objects.select_for_update().get(id=1)
        self.assertIsNotNone(account)
```

---

### Phase 4: Django 5.2 Migration Testing (Week 6-7)

**Goal:** Validate Django 5.2 upgrade (final target)

```bash
# Upgrade to Django 5.2
pip install Django==5.2

# Run full test suite
python manage.py test --verbosity=2 --parallel=4 --timing

# Run with coverage
coverage run --source='.' manage.py test
coverage report --skip-covered
coverage html
```

**Django 5.2 Specific Tests:**

```python
# tests/compatibility/test_django_52.py

class Django52CompatibilityTests(TransactionTestCase):
    """Test Django 5.2 specific changes."""

    def test_database_connection_health_checks(self):
        """Verify connection health checks."""
        from django.db import connection

        # Test health check feature
        self.assertTrue(connection.ensure_connection())

    def test_enhanced_model_validation(self):
        """Verify enhanced validation errors."""
        transaction = Transaction(amount=Decimal('-10.00'))

        with self.assertRaises(ValidationError) as cm:
            transaction.full_clean()

        # Should have clear error message
        self.assertIn('amount', cm.exception.message_dict)
```

---

### Phase 5: Staging Environment Testing (Week 8-9)

**Goal:** Full system integration testing in production-like environment

#### 5.1 Deployment to Staging

```bash
# Deploy checklist
- [ ] Database backup created
- [ ] Migrations applied successfully
- [ ] Static files collected
- [ ] Services restarted (web, workers, scheduler)
- [ ] Health checks passing
```

#### 5.2 Smoke Tests

```bash
# Run smoke tests immediately after deployment
python manage.py test tests.smoke --failfast

# Expected runtime: < 5 minutes
# Expected pass rate: 100%
```

**Smoke Test Coverage:**
```python
# tests/smoke/test_critical_paths.py

from django.test import TransactionTestCase

class SmokeTests(TransactionTestCase):
    """Fast tests for critical functionality."""

    def test_database_connection(self):
        """Database is accessible."""
        self.assertTrue(Account.objects.exists())

    def test_user_can_login(self):
        """Users can authenticate."""
        response = self.client.post('/login/', {
            'username': 'test_user',
            'password': 'test_pass'
        })
        self.assertEqual(response.status_code, 302)

    def test_transaction_creation(self):
        """Transactions can be created."""
        account = Account.objects.first()
        transaction = Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            type='CREDIT'
        )
        self.assertIsNotNone(transaction.id)

    def test_api_health(self):
        """API endpoints are responsive."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
```

---

#### 5.3 Full Regression Testing

```bash
# Run complete test suite in staging
python manage.py test --verbosity=2 --parallel=4

# Run for multiple iterations to catch flaky tests
for i in {1..5}; do
    echo "Test run $i"
    python manage.py test --shuffle
done
```

**Success Criteria:**
- [ ] 100% pass rate across all runs
- [ ] No new flaky tests
- [ ] Execution time within 20% of baseline
- [ ] No memory leaks detected

---

## Test Categories

### 1. Unit Tests (60% of total)

#### 1.1 Model Tests

```python
# tests/unit/test_models.py

from django.test import TestCase
from decimal import Decimal

class TransactionModelTests(TestCase):
    """Test Transaction model."""

    def test_transaction_creation(self):
        """Transaction can be created with valid data."""
        account = Account.objects.create(name='Test Account')
        transaction = Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            type='DEBIT'
        )

        self.assertEqual(transaction.amount, Decimal('100.00'))
        self.assertEqual(transaction.type, 'DEBIT')

    def test_transaction_amount_precision(self):
        """Transaction amount maintains 2 decimal places."""
        account = Account.objects.create(name='Test Account')
        transaction = Transaction.objects.create(
            account=account,
            amount=Decimal('100.123'),  # 3 decimals
            type='DEBIT'
        )

        # Should round to 2 decimals
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('100.12'))

    def test_transaction_timestamp_timezone_aware(self):
        """Transaction timestamps are timezone-aware."""
        from django.utils import timezone

        transaction = Transaction.objects.create(
            account=Account.objects.create(name='Test'),
            amount=Decimal('100.00'),
            type='DEBIT'
        )

        # Timestamp should be aware
        self.assertIsNotNone(transaction.timestamp.tzinfo)

    def test_negative_amount_validation(self):
        """Negative amounts are rejected."""
        from django.core.exceptions import ValidationError

        transaction = Transaction(
            account=Account.objects.create(name='Test'),
            amount=Decimal('-10.00'),
            type='DEBIT'
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()
```

---

#### 1.2 Business Logic Tests

```python
# tests/unit/test_business_logic.py

from django.test import TestCase
from decimal import Decimal

class InterestCalculationTests(TestCase):
    """Test interest calculation business logic."""

    def test_daily_interest_calculation(self):
        """Daily interest is calculated correctly."""
        account = Account.objects.create(
            name='Savings Account',
            balance=Decimal('10000.00'),
            interest_rate=Decimal('0.05')  # 5% APR
        )

        # Calculate daily interest
        daily_interest = account.calculate_daily_interest()

        # Expected: 10000 * 0.05 / 365 = 1.369863...
        expected = Decimal('1.37')  # Rounded to 2 decimals
        self.assertEqual(daily_interest, expected)

    def test_compound_interest_yearly(self):
        """Yearly compound interest is calculated correctly."""
        account = Account.objects.create(
            balance=Decimal('10000.00'),
            interest_rate=Decimal('0.05')
        )

        # After 1 year with daily compounding
        final_balance = account.calculate_compound_interest(days=365)

        # Expected: 10000 * (1 + 0.05/365)^365 ≈ 10512.67
        expected = Decimal('10512.67')
        self.assertEqual(final_balance, expected)
```

---

#### 1.3 Utility Function Tests

```python
# tests/unit/test_utils.py

from django.test import TestCase
from zoneinfo import ZoneInfo
from datetime import datetime

class TimezoneUtilsTests(TestCase):
    """Test timezone utility functions."""

    def test_convert_to_eastern(self):
        """UTC time converts correctly to Eastern."""
        from utils.timezone import convert_to_eastern

        utc_time = datetime(2025, 1, 15, 22, 0, 0, tzinfo=ZoneInfo('UTC'))
        eastern_time = convert_to_eastern(utc_time)

        # 10PM UTC = 5PM ET (5 hour difference)
        self.assertEqual(eastern_time.hour, 17)

    def test_eod_cutoff_time(self):
        """EOD cutoff time is 5PM ET."""
        from utils.timezone import get_eod_cutoff
        from datetime import date

        cutoff = get_eod_cutoff(date(2025, 1, 15))

        # Should be 5PM ET
        eastern = cutoff.astimezone(ZoneInfo('America/New_York'))
        self.assertEqual(eastern.hour, 17)
        self.assertEqual(eastern.minute, 0)
```

---

### 2. Integration Tests (30% of total)

#### 2.1 Database Integration Tests

```python
# tests/integration/test_database.py

from django.test import TransactionTestCase
from decimal import Decimal

class DatabaseIntegrationTests(TransactionTestCase):
    """Test database operations."""

    def test_transaction_atomicity(self):
        """Failed transaction rolls back all changes."""
        from django.db import transaction

        account = Account.objects.create(
            name='Test Account',
            balance=Decimal('1000.00')
        )

        try:
            with transaction.atomic():
                # Create transaction
                Transaction.objects.create(
                    account=account,
                    amount=Decimal('100.00'),
                    type='DEBIT'
                )

                # Update balance
                account.balance -= Decimal('100.00')
                account.save()

                # Simulate error
                raise Exception('Simulated error')
        except Exception:
            pass

        # Balance should be unchanged
        account.refresh_from_db()
        self.assertEqual(account.balance, Decimal('1000.00'))

        # Transaction should not exist
        self.assertEqual(Transaction.objects.count(), 0)

    def test_concurrent_transaction_handling(self):
        """Concurrent transactions don't cause race conditions."""
        from django.db import connection
        from threading import Thread

        account = Account.objects.create(
            name='Test',
            balance=Decimal('1000.00')
        )

        def create_transaction():
            Transaction.objects.create(
                account=Account.objects.select_for_update().get(id=account.id),
                amount=Decimal('100.00'),
                type='DEBIT'
            )

        # Create 10 concurrent transactions
        threads = [Thread(target=create_transaction) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly 10 transactions
        self.assertEqual(Transaction.objects.count(), 10)
```

---

#### 2.2 API Integration Tests

```python
# tests/integration/test_api.py

from rest_framework.test import APITestCase
from decimal import Decimal

class APIIntegrationTests(APITestCase):
    """Test REST API endpoints."""

    def setUp(self):
        """Create test user and authenticate."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)

    def test_transaction_create_api(self):
        """Transaction can be created via API."""
        account = Account.objects.create(
            user=self.user,
            name='Test Account'
        )

        response = self.client.post('/api/transactions/', {
            'account': account.id,
            'amount': '100.00',
            'type': 'DEBIT'
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Decimal(response.data['amount']),
            Decimal('100.00')
        )

    def test_transaction_list_filtering(self):
        """Transactions can be filtered by date range."""
        account = Account.objects.create(user=self.user, name='Test')

        # Create transactions
        Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            type='DEBIT'
        )

        response = self.client.get('/api/transactions/', {
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        })

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['results']), 0)

    def test_api_timestamp_serialization(self):
        """API returns ISO 8601 timestamps with timezone."""
        account = Account.objects.create(user=self.user, name='Test')
        transaction = Transaction.objects.create(
            account=account,
            amount=Decimal('100.00'),
            type='DEBIT'
        )

        response = self.client.get(f'/api/transactions/{transaction.id}/')

        # Should include timezone offset
        # Example: "2025-01-15T10:30:00-05:00"
        self.assertRegex(
            response.data['timestamp'],
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}'
        )
```

---

### 3. End-to-End Tests (10% of total)

```python
# tests/e2e/test_user_journeys.py

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class UserJourneyTests(StaticLiveServerTestCase):
    """Test complete user journeys."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Setup Selenium WebDriver
        from selenium import webdriver
        cls.selenium = webdriver.Chrome()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_user_login_to_transaction_creation(self):
        """User can login and create transaction."""
        # Navigate to login page
        self.selenium.get(f'{self.live_server_url}/login/')

        # Fill in login form
        username_input = self.selenium.find_element(By.NAME, 'username')
        username_input.send_keys('testuser')

        password_input = self.selenium.find_element(By.NAME, 'password')
        password_input.send_keys('testpass')

        # Submit form
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Wait for redirect to dashboard
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.ID, 'dashboard'))
        )

        # Navigate to transactions
        self.selenium.find_element(By.LINK_TEXT, 'Transactions').click()

        # Create new transaction
        self.selenium.find_element(By.LINK_TEXT, 'New Transaction').click()

        # Fill in transaction form
        amount_input = self.selenium.find_element(By.NAME, 'amount')
        amount_input.send_keys('100.00')

        # Submit
        self.selenium.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        # Verify success message
        WebDriverWait(self.selenium, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )

        success_message = self.selenium.find_element(By.CLASS_NAME, 'success-message')
        self.assertIn('Transaction created successfully', success_message.text)
```

---

## Banking-Specific Test Scenarios

### Critical Financial Scenarios

#### 1. Decimal Precision Tests

```python
class DecimalPrecisionTests(TestCase):
    """Test decimal precision for financial calculations."""

    def test_transaction_amount_precision(self):
        """Amounts maintain exactly 2 decimal places."""
        amounts = [
            ('100.12', Decimal('100.12')),
            ('100.123', Decimal('100.12')),  # Rounds down
            ('100.125', Decimal('100.13')),  # Rounds up
            ('100.999', Decimal('101.00')),  # Rounds up
        ]

        for input_amount, expected in amounts:
            account = Account.objects.create(name='Test')
            transaction = Transaction.objects.create(
                account=account,
                amount=Decimal(input_amount),
                type='DEBIT'
            )
            transaction.refresh_from_db()
            self.assertEqual(transaction.amount, expected)

    def test_interest_calculation_precision(self):
        """Interest calculations are precise."""
        account = Account.objects.create(
            balance=Decimal('10000.00'),
            interest_rate=Decimal('0.0512')  # 5.12% APR
        )

        interest = account.calculate_daily_interest()

        # Should maintain precision
        self.assertIsInstance(interest, Decimal)
        self.assertEqual(interest.as_tuple().exponent, -2)  # 2 decimal places
```

---

#### 2. Timezone Critical Tests

```python
class TimezoneCriticalTests(TransactionTestCase):
    """Test timezone-critical banking operations."""

    def test_eod_processing_cutoff_eastern_time(self):
        """EOD processing uses correct cutoff (5PM ET)."""
        from zoneinfo import ZoneInfo
        from datetime import datetime

        # Create transaction at 4:59 PM ET (should be included in EOD)
        eastern = ZoneInfo('America/New_York')
        dt_before = datetime(2025, 1, 15, 16, 59, 0, tzinfo=eastern)

        transaction_before = Transaction.objects.create(
            account=Account.objects.create(name='Test'),
            amount=Decimal('100.00'),
            type='DEBIT',
            timestamp=dt_before
        )

        # Create transaction at 5:01 PM ET (should NOT be included)
        dt_after = datetime(2025, 1, 15, 17, 1, 0, tzinfo=eastern)

        transaction_after = Transaction.objects.create(
            account=Account.objects.create(name='Test'),
            amount=Decimal('200.00'),
            type='DEBIT',
            timestamp=dt_after
        )

        # Run EOD for Jan 15, 2025
        from tasks import run_eod_processing
        eod_results = run_eod_processing(date(2025, 1, 15))

        # Should include transaction before 5PM
        self.assertIn(transaction_before.id, eod_results['processed_transactions'])

        # Should NOT include transaction after 5PM
        self.assertNotIn(transaction_after.id, eod_results['processed_transactions'])
```

---

#### 3. Balance Reconciliation Tests

```python
class BalanceReconciliationTests(TransactionTestCase):
    """Test balance calculations are accurate."""

    def test_balance_matches_transaction_sum(self):
        """Account balance equals sum of all transactions."""
        account = Account.objects.create(
            name='Test Account',
            balance=Decimal('0.00')
        )

        # Create various transactions
        transactions = [
            ('CREDIT', Decimal('1000.00')),
            ('DEBIT', Decimal('250.50')),
            ('CREDIT', Decimal('500.25')),
            ('DEBIT', Decimal('100.00')),
        ]

        for type, amount in transactions:
            Transaction.objects.create(
                account=account,
                amount=amount,
                type=type
            )

            # Update balance
            if type == 'CREDIT':
                account.balance += amount
            else:
                account.balance -= amount
            account.save()

        # Calculate expected balance
        expected_balance = Decimal('1000.00') + Decimal('500.25') - Decimal('250.50') - Decimal('100.00')

        # Verify balance
        account.refresh_from_db()
        self.assertEqual(account.balance, expected_balance)
        self.assertEqual(account.balance, Decimal('1149.75'))
```

---

## Performance Testing

### Load Testing with Locust

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between, events
from decimal import Decimal
import random

class BankingUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login on start."""
        response = self.client.post("/api/token/", {
            "username": "load_test_user",
            "password": "load_test_pass"
        })
        self.token = response.json()['access']
        self.client.headers = {
            'Authorization': f'Bearer {self.token}'
        }

    @task(5)
    def view_account(self):
        """View account details (most common operation)."""
        account_id = random.randint(1, 1000)
        self.client.get(f"/api/accounts/{account_id}/")

    @task(3)
    def view_transactions(self):
        """View transaction history."""
        account_id = random.randint(1, 1000)
        self.client.get(f"/api/accounts/{account_id}/transactions/")

    @task(2)
    def create_transaction(self):
        """Create new transaction."""
        account_id = random.randint(1, 1000)
        self.client.post("/api/transactions/", {
            "account": account_id,
            "amount": str(Decimal(random.uniform(10, 1000)).quantize(Decimal('0.01'))),
            "type": random.choice(["DEBIT", "CREDIT"])
        })

    @task(1)
    def generate_report(self):
        """Generate account statement."""
        account_id = random.randint(1, 1000)
        self.client.post(f"/api/accounts/{account_id}/statement/", {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary when test stops."""
    print("\n" + "="*50)
    print("Load Test Summary")
    print("="*50)
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failures: {environment.stats.total.num_failures}")
    print(f"Median response time: {environment.stats.total.median_response_time}ms")
    print(f"95th percentile: {environment.stats.total.get_response_time_percentile(0.95)}ms")
    print("="*50)
```

**Run Load Test:**
```bash
# Ramp up to 1000 users over 5 minutes
locust -f tests/load/locustfile.py \
    --host=https://staging.bank.com \
    --users=1000 \
    --spawn-rate=10 \
    --run-time=1h
```

**Performance Targets:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Median response time | < 100ms | > 150ms |
| 95th percentile | < 200ms | > 300ms |
| 99th percentile | < 500ms | > 1000ms |
| Error rate | < 0.1% | > 0.5% |
| Throughput | > 100 req/sec | < 80 req/sec |

---

## Security Testing

### Security Test Checklist

```python
# tests/security/test_security.py

from django.test import TestCase

class SecurityTests(TestCase):
    """Security-focused tests."""

    def test_csrf_protection(self):
        """CSRF tokens are required for POST requests."""
        response = self.client.post('/transactions/create/', {
            'account': 1,
            'amount': '100.00'
        })

        # Should be forbidden without CSRF token
        self.assertEqual(response.status_code, 403)

    def test_authentication_required(self):
        """Protected endpoints require authentication."""
        response = self.client.get('/api/accounts/')

        # Should be unauthorized
        self.assertEqual(response.status_code, 401)

    def test_sql_injection_protection(self):
        """SQL injection attempts are blocked."""
        response = self.client.get('/api/transactions/', {
            'search': "'; DROP TABLE transactions; --"
        })

        # Should not cause error
        self.assertEqual(response.status_code, 200)

        # Table should still exist
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'transactions'"
            )
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

    def test_xss_protection(self):
        """XSS attempts are escaped."""
        account = Account.objects.create(
            name='<script>alert("XSS")</script>'
        )

        response = self.client.get(f'/accounts/{account.id}/')

        # Should be escaped in HTML
        self.assertContains(
            response,
            '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
        )
        self.assertNotContains(
            response,
            '<script>alert("XSS")</script>',
            html=True
        )
```

---

## Test Automation

### CI/CD Integration

```yaml
# .github/workflows/django-tests.yml

name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          coverage run --source='.' manage.py test --verbosity=2

      - name: Generate coverage report
        run: |
          coverage report --skip-covered
          coverage html

      - name: Upload coverage
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: htmlcov/
```

---

## Test Execution Schedule

### Daily (Automated)
```bash
# Run on every commit
- Unit tests (fast, < 5 minutes)
- Linting and code style checks
- Security vulnerability scan
```

### Weekly (Automated)
```bash
# Run every Sunday night
- Full test suite (all tests)
- Integration tests
- Performance benchmarks
- Code coverage report
```

### Before Release (Manual)
```bash
# Before each deployment
- Full regression testing
- E2E tests
- Load testing (1 hour)
- Security testing
- Manual exploratory testing
```

---

## Success Criteria Summary

### Must Have (Go/No-Go)
- [ ] 100% of unit tests passing
- [ ] 100% of integration tests passing
- [ ] 100% of critical path E2E tests passing
- [ ] Zero P0 security vulnerabilities
- [ ] Performance within 10% of baseline
- [ ] Zero timezone-related errors
- [ ] Zero financial calculation errors

### Should Have
- [ ] > 95% test coverage
- [ ] < 5 flaky tests
- [ ] All deprecation warnings resolved
- [ ] Load test passes with 1000 concurrent users

### Nice to Have
- [ ] > 98% test coverage
- [ ] Zero flaky tests
- [ ] All tests run in < 10 minutes

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for Use
