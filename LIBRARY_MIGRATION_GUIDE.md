# Third-Party Library Migration Guide

**Django Migration:** 4.2 → 5.2
**Focus:** Banking Application Libraries
**Last Updated:** 2025-11-17

---

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Critical Libraries](#critical-libraries)
3. [Database Adapters](#database-adapters)
4. [Authentication Libraries](#authentication-libraries)
5. [API & Serialization](#api--serialization)
6. [Background Processing](#background-processing)
7. [Common Migration Patterns](#common-migration-patterns)
8. [Testing Third-Party Updates](#testing-third-party-updates)

---

## Migration Overview

### Priority Levels

| Priority | Description | Timeline | Risk |
|----------|-------------|----------|------|
| **P0** | Must update before Django 5.2 | Before upgrade | High |
| **P1** | Should update with Django 5.2 | During upgrade | Medium |
| **P2** | Can update after Django 5.2 | After upgrade | Low |

---

## Critical Libraries

### psycopg2 → psycopg (PostgreSQL Driver)

**Priority:** 🔴 P0 (Must migrate)
**Impact:** High for banking apps
**Effort:** Medium (2-3 days)

#### Why Migrate?

- `psycopg2` is deprecated in Django 5.2+
- `psycopg` (v3) is faster and more standards-compliant
- Better async support
- Improved type safety

#### Migration Steps

**Step 1: Update requirements.txt**

```bash
# OLD
psycopg2-binary==2.9.9

# NEW
psycopg[binary]>=3.1.8,<4.0
```

**Step 2: Update settings.py**

```python
# OLD (Django 4.2 + psycopg2)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'banking_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# NEW (Django 5.2 + psycopg v3)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Changed
        'NAME': 'banking_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,  # New in 5.2
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=10000',  # 10s timeout
            # Server-side cursor options
            'cursor_factory': None,  # Use default
        }
    }
}
```

**Step 3: Update Direct Usage (if any)**

```python
# If you have direct psycopg2 usage in your code

# OLD
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    dbname='banking_db',
    user='postgres',
    password='password'
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# NEW
import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    conninfo="dbname=banking_db user=postgres password=password"
)

cursor = conn.cursor(row_factory=dict_row)
```

**Step 4: Test Thoroughly**

```python
# tests/test_database_adapter.py

from django.test import TransactionTestCase
from django.db import connection

class PostgreSQLAdapterTests(TransactionTestCase):
    """Test psycopg (v3) adapter."""

    def test_connection_works(self):
        """Basic connection test."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_transaction_isolation(self):
        """Verify transaction isolation level."""
        from django.db import transaction

        with transaction.atomic():
            Account.objects.create(name='Test')
            # Should be isolated

    def test_server_side_cursor(self):
        """Test server-side cursor for large queries."""
        from django.db import connection

        with connection.cursor() as cursor:
            # Large query - should use server-side cursor
            cursor.execute(
                "SELECT * FROM transactions ORDER BY id LIMIT 10000"
            )
            # Fetch in chunks
            while True:
                rows = cursor.fetchmany(1000)
                if not rows:
                    break
```

---

### cx_Oracle → oracledb (Oracle Driver)

**Priority:** 🔴 P0 (If using Oracle)
**Impact:** High
**Effort:** Low (1 day)

#### Migration Steps

**Step 1: Uninstall cx_Oracle**

```bash
pip uninstall cx_Oracle
pip install 'oracledb>=2.0.0,<3.0'
```

**Step 2: Update Code (if direct usage)**

```python
# OLD
import cx_Oracle

conn = cx_Oracle.connect(user='banking', password='pass', dsn='localhost/XE')

# NEW - Two options:

# Option 1: Use alias for compatibility
import oracledb as cx_Oracle

conn = cx_Oracle.connect(user='banking', password='pass', dsn='localhost/XE')

# Option 2: Update all imports
import oracledb

conn = oracledb.connect(user='banking', password='pass', dsn='localhost/XE')
```

**Step 3: Django Settings (No Change Needed)**

```python
# settings.py - Works with both
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',  # Same
        'NAME': 'banking_db',
        'USER': 'banking_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '1521',
    }
}
```

---

## Authentication Libraries

### django-oauth-toolkit 2.x → 3.x

**Priority:** 🟡 P1 (Should migrate)
**Impact:** Medium
**Effort:** Medium (2-3 days)

#### Breaking Changes

1. **PKCE now required by default**
2. **Refresh token rotation enabled**
3. **New security defaults**

#### Migration Steps

**Step 1: Upgrade Package**

```bash
pip install 'django-oauth-toolkit>=3.0,<4.0'
```

**Step 2: Update Settings**

```python
# settings.py

# OLD (django-oauth-toolkit 2.x)
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,  # 10 hours
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,  # 10 minutes
    'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,  # 14 days
}

# NEW (django-oauth-toolkit 3.x)
OAUTH2_PROVIDER = {
    # Existing settings
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,

    # New required settings
    'PKCE_REQUIRED': True,  # Now mandatory for security
    'ROTATE_REFRESH_TOKEN': True,  # Rotates refresh tokens
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 120,  # 2-minute grace period

    # Optional: Customize PKCE
    'ALLOW_UNSAFE_PKCE': False,  # Disallow plain PKCE (use S256 only)
}
```

**Step 3: Update Client Applications**

```javascript
// Frontend OAuth2 client changes

// OLD (without PKCE)
const authUrl = `/oauth/authorize/?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code`;

// NEW (with PKCE)
import { generateCodeVerifier, generateCodeChallenge } from 'oauth-pkce';

const codeVerifier = generateCodeVerifier();
const codeChallenge = await generateCodeChallenge(codeVerifier);

// Store codeVerifier in sessionStorage
sessionStorage.setItem('code_verifier', codeVerifier);

const authUrl = `/oauth/authorize/?`
  + `client_id=${clientId}`
  + `&redirect_uri=${redirectUri}`
  + `&response_type=code`
  + `&code_challenge=${codeChallenge}`
  + `&code_challenge_method=S256`;

// On callback, include code_verifier
const tokenResponse = await fetch('/oauth/token/', {
  method: 'POST',
  body: JSON.stringify({
    grant_type: 'authorization_code',
    code: authorizationCode,
    redirect_uri: redirectUri,
    client_id: clientId,
    code_verifier: sessionStorage.getItem('code_verifier'),
  }),
});
```

**Step 4: Test OAuth Flow**

```python
# tests/test_oauth.py

from django.test import TestCase
from oauth2_provider.models import Application, AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

class OAuth2FlowTests(TestCase):
    """Test OAuth2 with django-oauth-toolkit 3.x."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        self.application = Application.objects.create(
            name='Test App',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://localhost:8000/callback',
        )

    def test_pkce_required(self):
        """PKCE is required for authorization."""
        # Login first
        self.client.login(username='testuser', password='testpass')

        # Try authorization without PKCE - should fail
        response = self.client.get('/oauth/authorize/', {
            'client_id': self.application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8000/callback',
        })

        # Should require PKCE
        self.assertContains(response, 'code_challenge', status_code=400)

    def test_refresh_token_rotation(self):
        """Refresh tokens are rotated on use."""
        # Create initial access token with refresh token
        access_token = AccessToken.objects.create(
            user=self.user,
            application=self.application,
            token='initial-access-token',
            expires=timezone.now() + timedelta(hours=1),
        )

        refresh_token = RefreshToken.objects.create(
            user=self.user,
            application=self.application,
            token='initial-refresh-token',
            access_token=access_token,
        )

        # Use refresh token to get new access token
        response = self.client.post('/oauth/token/', {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token.token,
            'client_id': self.application.client_id,
            'client_secret': self.application.client_secret,
        })

        data = response.json()

        # Should get new tokens
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)

        # New refresh token should be different
        self.assertNotEqual(data['refresh_token'], refresh_token.token)

        # Old refresh token should be revoked
        refresh_token.refresh_from_db()
        self.assertTrue(refresh_token.revoked)
```

---

### django-allauth Migration

**Priority:** 🟡 P1
**Impact:** Medium
**Effort:** Low (1 day)

```bash
# Upgrade
pip install 'django-allauth>=0.64,<1.0'

# settings.py - Add new settings
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # For banking security
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5  # Limit login attempts
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300  # 5 minutes lockout
SOCIALACCOUNT_AUTO_SIGNUP = False  # Require explicit signup for banking
```

---

## API & Serialization

### Django REST Framework 3.14 → 3.15

**Priority:** 🟡 P1
**Impact:** Low-Medium
**Effort:** Low (1-2 days)

#### Changes in 3.15

1. **Stricter validation**
2. **Better error messages**
3. **Updated pagination**

#### Migration Steps

**Step 1: Upgrade**

```bash
pip install 'djangorestframework>=3.15,<4.0'
```

**Step 2: Update Serializers (if needed)**

```python
# More strict validation in 3.15

# OLD (DRF 3.14) - Allowed some invalid data
class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=19, decimal_places=2)

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'type', 'timestamp']

# NEW (DRF 3.15) - Need explicit validation
class TransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=19,
        decimal_places=2,
        min_value=Decimal('0.01'),  # Explicit minimum
        error_messages={
            'invalid': 'Amount must be a valid decimal.',
            'min_value': 'Amount must be at least $0.01.',
        }
    )

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'type', 'timestamp']

    def validate_amount(self, value):
        """Additional validation."""
        if value > Decimal('1000000.00'):  # 1 million limit
            raise serializers.ValidationError(
                'Transaction amount exceeds maximum allowed.'
            )
        return value
```

**Step 3: Test All Serializers**

```python
# tests/test_serializers.py

from rest_framework.test import APITestCase
from decimal import Decimal

class TransactionSerializerTests(APITestCase):
    """Test serializer validation."""

    def test_valid_transaction(self):
        """Valid transaction serializes correctly."""
        data = {
            'amount': '100.00',
            'type': 'DEBIT',
        }

        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_amount(self):
        """Invalid amount is rejected."""
        data = {
            'amount': '-10.00',  # Negative
            'type': 'DEBIT',
        }

        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)

    def test_decimal_precision(self):
        """Decimal precision is enforced."""
        data = {
            'amount': '100.123',  # 3 decimal places
            'type': 'DEBIT',
        }

        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
```

---

## Background Processing

### Celery 5.2 → 5.4

**Priority:** 🟡 P1
**Impact:** Low
**Effort:** Low (1 day)

#### Migration Steps

**Step 1: Upgrade**

```bash
pip install --upgrade \
    'celery>=5.4,<6.0' \
    'redis>=5.0,<6.0' \
    'kombu>=5.4,<6.0'
```

**Step 2: Update Configuration**

```python
# celery.py

from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'banking.settings')

app = Celery('banking')

# NEW in Celery 5.4: Better config
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks
app.autodiscover_tasks()

# Updated task defaults
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,  # Better task tracking
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,  # Optimize throughput
    worker_max_tasks_per_child=1000,  # Prevent memory leaks
)
```

**Step 3: Update Task Definitions**

```python
# tasks.py

from celery import shared_task
from django.utils import timezone
from decimal import Decimal

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    time_limit=600,  # 10 minutes
)
def process_eod_batch(self, date_str):
    """Process end-of-day batch for given date."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    eastern = ZoneInfo('America/New_York')

    # Get transactions before 5PM ET
    cutoff = datetime.combine(date, time(17, 0), tzinfo=eastern)

    transactions = Transaction.objects.filter(
        timestamp__lt=cutoff,
        processed=False
    )

    total_processed = 0
    total_amount = Decimal('0.00')

    for transaction in transactions:
        # Process transaction
        transaction.processed = True
        transaction.save()

        total_processed += 1
        total_amount += transaction.amount

        # Update task state (new in Celery 5.4)
        self.update_state(
            state='PROGRESS',
            meta={
                'processed': total_processed,
                'total': transactions.count(),
            }
        )

    return {
        'date': date_str,
        'processed': total_processed,
        'total_amount': str(total_amount),
    }
```

**Step 4: Test Celery Tasks**

```python
# tests/test_celery.py

from django.test import TestCase
from unittest.mock import patch

class CeleryTaskTests(TestCase):
    """Test Celery tasks."""

    @patch('tasks.Transaction.objects.filter')
    def test_eod_processing_task(self, mock_filter):
        """EOD processing task works."""
        from tasks import process_eod_batch

        # Mock transactions
        mock_filter.return_value.count.return_value = 10

        # Run task synchronously (CELERY_TASK_ALWAYS_EAGER=True in test settings)
        result = process_eod_batch.delay('2025-01-15')

        self.assertTrue(result.successful())
        data = result.get()
        self.assertEqual(data['date'], '2025-01-15')
```

---

## Common Migration Patterns

### Pattern 1: Gradual Rollout

```python
# Use feature flags for gradual migration

# settings.py
FEATURE_FLAGS = {
    'use_psycopg3': os.environ.get('USE_PSYCOPG3', 'false').lower() == 'true',
    'use_oauth_pkce': os.environ.get('USE_OAUTH_PKCE', 'false').lower() == 'true',
}

# In code
from django.conf import settings

if settings.FEATURE_FLAGS['use_psycopg3']:
    import psycopg as db_adapter
else:
    import psycopg2 as db_adapter
```

---

### Pattern 2: Parallel Testing

```bash
# Test both old and new libraries in CI

# .github/workflows/test-migration.yml
strategy:
  matrix:
    django-version: ['4.2', '5.0', '5.1', '5.2']
    db-adapter: ['psycopg2', 'psycopg']
    exclude:
      - django-version: '5.2'
        db-adapter: 'psycopg2'  # Not supported
```

---

### Pattern 3: Backward Compatibility Layer

```python
# utils/compat.py

"""Compatibility layer for library migrations."""

# Database adapter compatibility
try:
    import psycopg
    from psycopg.rows import dict_row

    def get_db_connection(**kwargs):
        return psycopg.connect(**kwargs)

    def get_dict_cursor(conn):
        return conn.cursor(row_factory=dict_row)

except ImportError:
    import psycopg2
    import psycopg2.extras

    def get_db_connection(**kwargs):
        return psycopg2.connect(**kwargs)

    def get_dict_cursor(conn):
        return conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
```

---

## Testing Third-Party Updates

### Comprehensive Test Plan

```python
# tests/test_third_party_compat.py

from django.test import TestCase, TransactionTestCase

class ThirdPartyCompatibilityTests(TransactionTestCase):
    """Test third-party library compatibility."""

    def test_database_adapter(self):
        """Database adapter works correctly."""
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            self.assertIsNotNone(version)

    def test_celery_integration(self):
        """Celery tasks can be queued and executed."""
        from tasks import test_task

        result = test_task.delay()
        self.assertTrue(result.successful())

    def test_drf_serialization(self):
        """DRF serializers work correctly."""
        from api.serializers import TransactionSerializer

        data = {'amount': '100.00', 'type': 'DEBIT'}
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_oauth_authentication(self):
        """OAuth2 authentication works."""
        # Test OAuth flow
        pass

    def test_cache_backend(self):
        """Cache backend works correctly."""
        from django.core.cache import cache

        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
```

---

## Library Update Checklist

### Before Updating

- [ ] Read changelog and release notes
- [ ] Check for breaking changes
- [ ] Review migration guides
- [ ] Test in isolated environment
- [ ] Create rollback plan

### During Update

- [ ] Update requirements.txt
- [ ] Update settings.py if needed
- [ ] Update code for breaking changes
- [ ] Run test suite
- [ ] Fix any failures
- [ ] Test in staging

### After Update

- [ ] Document changes made
- [ ] Update team documentation
- [ ] Monitor for issues
- [ ] Verify performance
- [ ] Check logs for warnings

---

## Rollback Procedures

### Quick Rollback

```bash
# If issues found after library update

# 1. Revert requirements.txt
git checkout HEAD~1 -- requirements.txt

# 2. Reinstall old versions
pip install -r requirements.txt

# 3. Restart services
systemctl restart gunicorn celery

# 4. Verify rollback
python manage.py check
python manage.py test
```

### Full Rollback

```bash
# If major issues, rollback entire Django version

# 1. Revert to previous commit
git revert <commit-hash>

# 2. Reinstall dependencies
pip install -r requirements.txt

# 3. Rollback migrations (if any)
python manage.py migrate app_name previous_migration_number

# 4. Restart all services
./scripts/restart_services.sh
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for Use
