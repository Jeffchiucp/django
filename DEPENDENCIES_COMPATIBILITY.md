# Dependencies Compatibility Matrix

**Django Migration:** 4.2 LTS → 5.0 → 5.1 → 5.2
**Python Version:** 3.11+
**Target:** Banking Application
**Last Updated:** 2025-11-17

---

## Table of Contents

1. [Core Dependencies](#core-dependencies)
2. [Database Drivers](#database-drivers)
3. [Django Extensions](#django-extensions)
4. [REST Framework & API](#rest-framework--api)
5. [Authentication & Security](#authentication--security)
6. [Background Tasks & Caching](#background-tasks--caching)
7. [Testing & Development](#testing--development)
8. [Monitoring & Logging](#monitoring--logging)
9. [Upgrade Path](#upgrade-path)
10. [Breaking Changes](#breaking-changes)

---

## Core Dependencies

### Django Framework

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Action Required |
|---------|------------|------------|------------|------------|------------------|-----------------|
| **Django** | 4.2.x | 5.0.x | 5.1.x | 5.2.x | YES - Major | See BREAKING_CHANGES_REVIEW.md |
| **Python** | 3.8-3.12 | 3.10-3.12 | 3.10-3.13 | 3.11-3.13 | YES - Drop 3.8-3.9 | Upgrade Python to 3.11+ |

**Upgrade Command:**
```bash
# Django 4.2 → 5.0
pip install 'Django>=5.0,<5.1'

# Django 5.0 → 5.1
pip install 'Django>=5.1,<5.2'

# Django 5.1 → 5.2
pip install 'Django>=5.2,<5.3'
```

---

## Database Drivers

### PostgreSQL

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **psycopg2** | 2.9.x | 2.9.x | 2.9.x | **Deprecated** | YES - Move to psycopg | Legacy driver |
| **psycopg2-binary** | 2.9.x | 2.9.x | 2.9.x | **Deprecated** | YES - Move to psycopg | Development only |
| **psycopg** (v3) | Not supported | 3.0.x | 3.1.x | 3.1.x+ | NO | **Recommended** |

**Migration Path:**

```python
# OLD: requirements.txt (Django 4.2)
psycopg2-binary==2.9.9

# NEW: requirements.txt (Django 5.2)
psycopg[binary]>=3.1.8,<4.0

# Or for production (compiled)
psycopg>=3.1.8,<4.0
```

**Code Changes Required:**

```python
# Django 4.2 with psycopg2
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Old
        'NAME': 'banking_db',
    }
}

# Django 5.2 with psycopg (v3)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Updated
        'NAME': 'banking_db',
        'OPTIONS': {
            # psycopg3-specific options
            'connect_timeout': 10,
            'options': '-c statement_timeout=10000',  # 10 second timeout
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,  # New in Django 5.2
    }
}
```

**⚠️ Important for Banking Apps:**
- Test connection pooling thoroughly
- Verify transaction isolation levels
- Test connection health checks

---

### MySQL / MariaDB

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **mysqlclient** | 2.1.x | 2.2.x | 2.2.x | 2.2.x+ | NO | **Recommended** |
| **PyMySQL** | 1.0.x | 1.1.x | 1.1.x | 1.1.x | NO | Alternative |
| **MySQL** (Server) | 5.7+ | **8.0.11+** | 8.0.11+ | 8.0.11+ | YES | Upgrade DB first |
| **MariaDB** (Server) | 10.4+ | 10.5+ | 10.5+ | 10.5+ | NO | |

**Upgrade Command:**
```bash
pip install 'mysqlclient>=2.2.0,<3.0'
```

**Database Upgrade Required:**
```bash
# Check MySQL version
mysql --version

# Must be >= 8.0.11 for Django 5.0+
# Upgrade MySQL before upgrading Django!
```

---

### Oracle

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **cx_Oracle** | 8.3+ | **Deprecated** | **Removed** | **Removed** | YES - Removed | Don't use |
| **oracledb** | Not supported | 1.3.2+ | 1.4.x | 2.0.x | NO | **Use this** |

**Migration Required:**

```bash
# Uninstall cx_Oracle
pip uninstall cx_Oracle

# Install oracledb
pip install 'oracledb>=2.0.0,<3.0'
```

```python
# No code changes needed in Django settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',  # Same
        'NAME': 'banking_db',
    }
}

# But update any direct imports
# OLD
import cx_Oracle

# NEW
import oracledb as cx_Oracle  # Can use alias for compatibility
```

---

## Django Extensions

### Essential Packages

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **django-extensions** | 3.2.x | 3.2.x | 3.2.x | 3.2.x+ | ✅ Compatible | Dev tools |
| **django-debug-toolbar** | 4.2.x | 4.2.x | 4.3.x | 4.4.x | ✅ Compatible | Debug only |
| **django-crispy-forms** | 2.0.x | 2.1.x | 2.1.x | 2.3.x | ⚠️ Update | Form rendering |
| **django-filter** | 23.3 | 23.5 | 24.2 | 24.3 | ✅ Compatible | Filtering |
| **django-environ** | 0.11.x | 0.11.x | 0.11.x | 0.11.x | ✅ Compatible | Environment vars |

**Upgrade Commands:**
```bash
pip install --upgrade \
    'django-extensions>=3.2' \
    'django-debug-toolbar>=4.4' \
    'django-crispy-forms>=2.3' \
    'django-filter>=24.3' \
    'django-environ>=0.11'
```

---

### Forms & Templates

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Action Required |
|---------|------------|------------|------------|------------|------------------|-----------------|
| **django-crispy-forms** | 2.0.x | 2.1.x | 2.1.x | 2.3.x | YES | Update templates |
| **crispy-bootstrap4** | 1.0.x | 2.0.x | 2.0.x | 2.0.x | YES | Template system changed |
| **crispy-bootstrap5** | 0.7.x | 2.0.x | 2.0.x | 2.0.x | YES | Recommended |

**Template Migration:**

```python
# settings.py - Django 4.2
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# settings.py - Django 5.2
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# requirements.txt
# OLD
django-crispy-forms==2.0
crispy-bootstrap4==1.0.2

# NEW
django-crispy-forms>=2.3
crispy-bootstrap5>=2.0
```

---

## REST Framework & API

### Django REST Framework

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **djangorestframework** | 3.14.x | 3.14.x | 3.15.x | 3.15.x+ | ✅ Compatible | API framework |
| **drf-spectacular** | 0.26.x | 0.27.x | 0.27.x | 0.28.x | ✅ Compatible | OpenAPI schema |
| **django-cors-headers** | 4.3.x | 4.3.x | 4.4.x | 4.4.x | ✅ Compatible | CORS handling |
| **djangorestframework-simplejwt** | 5.3.x | 5.3.x | 5.3.x | 5.4.x | ✅ Compatible | JWT auth |

**Upgrade Commands:**
```bash
pip install --upgrade \
    'djangorestframework>=3.15' \
    'drf-spectacular>=0.28' \
    'django-cors-headers>=4.4' \
    'djangorestframework-simplejwt>=5.4'
```

**Breaking Changes:**

```python
# DRF 3.15 - Updated serializer validation

# OLD (Django 4.2 / DRF 3.14)
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

# NEW (Django 5.2 / DRF 3.15)
# No changes needed, but validation is stricter
# Test all serializers thoroughly
```

---

## Authentication & Security

### OAuth & Social Auth

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **django-oauth-toolkit** | 2.2.x | 2.3.x | 2.4.x | 3.0.x | YES - Major | OAuth2 provider |
| **django-allauth** | 0.57.x | 0.58.x | 0.63.x | 0.64.x | YES | Social auth |
| **social-auth-app-django** | 5.4.x | 5.4.x | 5.4.x | 5.4.x | NO | Alternative |

**django-oauth-toolkit Migration:**

```python
# requirements.txt
# OLD
django-oauth-toolkit==2.2.0

# NEW
django-oauth-toolkit>=3.0.0,<4.0

# settings.py changes
# OLD (Django 4.2 / django-oauth-toolkit 2.2)
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,
}

# NEW (Django 5.2 / django-oauth-toolkit 3.0)
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 1209600,
    # New setting in 3.0
    'ROTATE_REFRESH_TOKEN': True,
    'PKCE_REQUIRED': True,  # More secure
}
```

---

### Two-Factor Authentication

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **django-otp** | 1.2.x | 1.3.x | 1.4.x | 1.5.x | ✅ Compatible | TOTP/HOTP |
| **qrcode** | 7.4.x | 7.4.x | 7.4.x | 7.4.x | ✅ Compatible | QR generation |

```bash
pip install --upgrade 'django-otp>=1.5' 'qrcode>=7.4'
```

---

## Background Tasks & Caching

### Celery

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **celery** | 5.2.x | 5.3.x | 5.3.x | 5.4.x | NO | Task queue |
| **redis** | 4.5.x | 4.6.x | 5.0.x | 5.0.x+ | NO | Broker/backend |
| **kombu** | 5.3.x | 5.3.x | 5.3.x | 5.4.x | NO | Messaging |

**Upgrade Commands:**
```bash
pip install --upgrade \
    'celery>=5.4.0,<6.0' \
    'redis>=5.0.0,<6.0' \
    'kombu>=5.4.0,<6.0'
```

**Testing Celery with Django 5.2:**

```python
# settings.py - Verify configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'  # Important: Use UTC for consistency
CELERY_ENABLE_UTC = True

# Test task
from celery import shared_task

@shared_task
def test_django_52_task():
    """Test Celery works with Django 5.2."""
    from django.utils import timezone
    return f"Task executed at {timezone.now()}"
```

---

### Caching

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Breaking Changes | Notes |
|---------|------------|------------|------------|------------|------------------|-------|
| **django-redis** | 5.3.x | 5.4.x | 5.4.x | 5.4.x | NO | Redis cache backend |
| **redis** | 4.5.x | 4.6.x | 5.0.x | 5.0.x+ | NO | Python client |

**Cache Configuration:**

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            # New in Django 5.2: Better key validation
            'KEY_PREFIX': 'banking',
            'VERSION': 1,
        }
    }
}

# Test caching
from django.core.cache import cache

def test_cache():
    cache.set('test_key', 'test_value', 300)
    value = cache.get('test_key')
    assert value == 'test_value'
```

---

## Testing & Development

### Testing Frameworks

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **pytest** | 7.4.x | 8.0.x | 8.2.x | 8.3.x | ✅ Compatible | Test framework |
| **pytest-django** | 4.5.x | 4.7.x | 4.8.x | 4.9.x | ✅ Compatible | Django integration |
| **pytest-cov** | 4.1.x | 5.0.x | 5.0.x | 6.0.x | ✅ Compatible | Coverage |
| **factory-boy** | 3.3.x | 3.3.x | 3.3.x | 3.3.x | ✅ Compatible | Test factories |
| **faker** | 19.x | 25.x | 26.x | 28.x | ✅ Compatible | Fake data |

**Upgrade Commands:**
```bash
pip install --upgrade \
    'pytest>=8.3' \
    'pytest-django>=4.9' \
    'pytest-cov>=6.0' \
    'factory-boy>=3.3' \
    'faker>=28.0'
```

---

### Code Quality

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **black** | 23.x | 24.x | 24.x | 24.x | ✅ Compatible | Code formatter |
| **flake8** | 6.1.x | 7.0.x | 7.1.x | 7.1.x | ✅ Compatible | Linter |
| **pylint** | 2.17.x | 3.2.x | 3.2.x | 3.3.x | ✅ Compatible | Static analysis |
| **mypy** | 1.6.x | 1.11.x | 1.11.x | 1.13.x | ✅ Compatible | Type checking |

---

## Monitoring & Logging

### Application Monitoring

| Package | Django 4.2 | Django 5.0 | Django 5.1 | Django 5.2 | Status | Notes |
|---------|------------|------------|------------|------------|--------|-------|
| **sentry-sdk** | 1.38.x | 1.45.x | 2.0.x | 2.18.x | ⚠️ Update | Error tracking |
| **django-prometheus** | 2.3.x | 2.3.x | 2.3.x | 2.3.x | ✅ Compatible | Metrics |
| **structlog** | 23.x | 24.x | 24.x | 24.x | ✅ Compatible | Structured logging |

**Sentry Configuration:**

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    environment="production",
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% profiling
    # New in Django 5.2: Better error capturing
    send_default_pii=False,  # Banking compliance
    before_send=before_send_callback,  # Filter sensitive data
)
```

---

## Upgrade Path

### Step-by-Step Dependency Upgrade

#### Step 1: Upgrade Python (if needed)

```bash
# Check current version
python --version

# If < 3.11, upgrade Python first
# Ubuntu/Debian
sudo apt install python3.11

# macOS
brew install python@3.11

# Create new virtual environment
python3.11 -m venv venv_django52
source venv_django52/bin/activate
```

---

#### Step 2: Upgrade to Django 5.0

```bash
# Install Django 5.0
pip install 'Django>=5.0,<5.1'

# Upgrade compatible packages
pip install --upgrade \
    'psycopg[binary]>=3.1.8' \
    'djangorestframework>=3.14' \
    'celery>=5.3' \
    'redis>=4.6'

# Run tests
python manage.py test

# Fix any failures
```

---

#### Step 3: Upgrade to Django 5.1

```bash
# Install Django 5.1
pip install 'Django>=5.1,<5.2'

# Upgrade packages that need it
pip install --upgrade \
    'djangorestframework>=3.15' \
    'sentry-sdk>=2.0'

# Run tests
python manage.py test
```

---

#### Step 4: Upgrade to Django 5.2 (Final)

```bash
# Install Django 5.2
pip install 'Django>=5.2,<5.3'

# Upgrade all packages to latest compatible versions
pip install --upgrade \
    'psycopg>=3.1.8' \
    'djangorestframework>=3.15' \
    'celery>=5.4' \
    'redis>=5.0' \
    'sentry-sdk>=2.18'

# Run full test suite
python manage.py test --verbosity=2

# Generate new requirements.txt
pip freeze > requirements_django52.txt
```

---

## Breaking Changes

### Critical Breaking Changes by Package

#### psycopg2 → psycopg (v3)

**Impact:** 🔴 High for banking apps

**Changes:**
- Different connection parameter format
- Connection pooling works differently
- Server-side cursors API changed

**Migration:**

```python
# OLD: psycopg2
import psycopg2

conn = psycopg2.connect(
    dbname='banking_db',
    user='postgres',
    password='password',
    host='localhost'
)

# NEW: psycopg (v3)
import psycopg

conn = psycopg.connect(
    "dbname=banking_db user=postgres password=password host=localhost"
)

# Or with connection dict
conn = psycopg.connect(
    conninfo="",
    dbname='banking_db',
    user='postgres',
    password='password',
    host='localhost'
)
```

**Testing:**
- Test all direct database connections
- Verify connection pooling behavior
- Test transaction isolation levels

---

#### django-oauth-toolkit 2.x → 3.x

**Impact:** 🟡 Medium

**Changes:**
- PKCE now required by default
- Refresh token rotation enabled
- New security defaults

**Migration:**

```python
# settings.py
OAUTH2_PROVIDER = {
    # Existing settings
    'ACCESS_TOKEN_EXPIRE_SECONDS': 36000,

    # New required settings in 3.0
    'PKCE_REQUIRED': True,  # Now mandatory
    'ROTATE_REFRESH_TOKEN': True,  # Security improvement
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 120,  # Grace period
}
```

**Testing:**
- Test OAuth2 authorization flow
- Verify refresh token rotation
- Test PKCE flow with clients

---

### Deprecation Warnings

**Packages to Watch:**

```python
# Run Django with warnings enabled
python -Wd manage.py runserver

# Common deprecation warnings:
# 1. psycopg2 → psycopg
# 2. cx_Oracle → oracledb
# 3. Old-style Celery task decorators
# 4. Deprecated DRF pagination styles
```

---

## Recommended Final requirements.txt

```txt
# Django 5.2 Banking Application Requirements

# Core
Django>=5.2,<5.3
python-decouple>=3.8  # Environment variables

# Database
psycopg[binary]>=3.1.8,<4.0  # PostgreSQL driver
pytz>=2024.1  # Keep for legacy migrations only

# REST API
djangorestframework>=3.15,<4.0
drf-spectacular>=0.28  # OpenAPI schema
django-cors-headers>=4.4

# Authentication
django-oauth-toolkit>=3.0,<4.0
django-otp>=1.5  # 2FA
djangorestframework-simplejwt>=5.4

# Background Tasks
celery>=5.4,<6.0
redis>=5.0,<6.0
kombu>=5.4,<6.0

# Caching
django-redis>=5.4

# Forms & Templates
django-crispy-forms>=2.3
crispy-bootstrap5>=2.0

# Utilities
django-extensions>=3.2
django-filter>=24.3
django-environ>=0.11

# Monitoring & Logging
sentry-sdk>=2.18
structlog>=24.0

# Development & Testing (dev-requirements.txt)
pytest>=8.3
pytest-django>=4.9
pytest-cov>=6.0
factory-boy>=3.3
faker>=28.0
django-debug-toolbar>=4.4

# Code Quality
black>=24.0
flake8>=7.1
pylint>=3.3
mypy>=1.13
```

---

## Compatibility Testing Checklist

### Before Upgrading Each Version

- [ ] Read release notes thoroughly
- [ ] Check each package's changelog
- [ ] Test in isolated virtual environment
- [ ] Run full test suite
- [ ] Test in staging environment
- [ ] Performance benchmark
- [ ] Security audit
- [ ] Update documentation

### After Each Upgrade

- [ ] All tests passing (100%)
- [ ] No deprecation warnings
- [ ] Performance within 10% of baseline
- [ ] Security scan passes
- [ ] Dependencies updated
- [ ] requirements.txt updated
- [ ] Documentation updated

---

## Quick Reference: Incompatible Packages

**Do NOT Use with Django 5.2:**

| Package | Reason | Alternative |
|---------|--------|-------------|
| **psycopg2** | Deprecated | Use `psycopg` (v3) |
| **cx_Oracle** | Removed | Use `oracledb` |
| **django-suit** | Not updated | Use default admin or `grappelli` |
| **django-reversion < 5.0** | Incompatible | Upgrade to 5.0+ |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for Use
**Next Review:** After Django 5.3 release
