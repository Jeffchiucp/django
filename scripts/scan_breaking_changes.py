#!/usr/bin/env python3
"""
Django 5.0 Breaking Changes Scanner

Comprehensive scanner for detecting Django 5.0 breaking changes in your codebase.
Run this before upgrading from Django 4.2 to 5.0.

Usage:
    python scan_breaking_changes.py [--path PROJECT_ROOT] [--json] [--verbose]
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict


class BreakingChangeScanner:
    """Scan Django project for Django 5.0 breaking changes."""

    def __init__(self, project_root='.', verbose=False):
        self.project_root = Path(project_root)
        self.verbose = verbose
        self.results = defaultdict(list)
        self.file_count = 0

    def scan_all(self):
        """Run all breaking change scans."""
        print("🔍 Scanning for Django 5.0 breaking changes...\n")
        print(f"Project root: {self.project_root.absolute()}\n")

        self.scan_pytz_usage()
        self.scan_postgres_aggregates()
        self.scan_use_tz_setting()
        self.scan_update_or_create()
        self.scan_form_rendering()
        self.scan_uuid_fields()
        self.scan_deprecated_features()
        self.scan_admin_templates()
        self.scan_removed_features()

        self.print_report()

    def scan_pytz_usage(self):
        """Scan for pytz usage (CRITICAL)."""
        if self.verbose:
            print("Scanning for pytz usage...")

        for py_file in self.project_root.rglob('*.py'):
            # Skip migrations, virtual envs, and cache
            if any(part in py_file.parts for part in ['migrations', 'venv', '.venv', '__pycache__']):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                # Check for pytz imports
                if re.search(r'import pytz|from pytz', content):
                    self.results['pytz_import'].append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'severity': 'CRITICAL',
                        'category': 'P0'
                    })

                # Check for is_dst parameter
                for i, line in enumerate(lines, 1):
                    if 'is_dst' in line:
                        self.results['is_dst_param'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': i,
                            'code': line.strip(),
                            'severity': 'CRITICAL',
                            'category': 'P0'
                        })

                # Check for make_aware with timezone and is_dst
                if re.search(r'make_aware.*is_dst', content):
                    self.results['make_aware_is_dst'].append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'severity': 'CRITICAL',
                        'category': 'P0'
                    })

            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {py_file}: {e}")

    def scan_postgres_aggregates(self):
        """Scan for PostgreSQL aggregate usage."""
        if self.verbose:
            print("Scanning for PostgreSQL aggregates...")

        aggregates = ['ArrayAgg', 'StringAgg', 'JSONBAgg']

        for py_file in self.project_root.rglob('*.py'):
            if any(part in py_file.parts for part in ['venv', '.venv', '__pycache__']):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for agg in aggregates:
                    for i, line in enumerate(lines, 1):
                        if agg in line and 'import' not in line.lower():
                            self.results[f'{agg}_usage'].append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': i,
                                'code': line.strip(),
                                'severity': 'MEDIUM',
                                'category': 'P1'
                            })
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {py_file}: {e}")

    def scan_use_tz_setting(self):
        """Check USE_TZ setting."""
        if self.verbose:
            print("Checking USE_TZ setting...")

        settings_files = list(self.project_root.rglob('settings*.py'))

        for settings_file in settings_files:
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                if re.search(r'USE_TZ\s*=\s*False', content):
                    self.results['use_tz_false'].append({
                        'file': str(settings_file.relative_to(self.project_root)),
                        'severity': 'CRITICAL',
                        'category': 'P0',
                        'note': 'USE_TZ=True is now the default'
                    })
                elif 'USE_TZ' not in content:
                    self.results['use_tz_missing'].append({
                        'file': str(settings_file.relative_to(self.project_root)),
                        'severity': 'MEDIUM',
                        'category': 'P1',
                        'note': 'USE_TZ will default to True in Django 5.0'
                    })
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {settings_file}: {e}")

    def scan_update_or_create(self):
        """Scan for update_or_create with create_defaults field name."""
        if self.verbose:
            print("Scanning for update_or_create usage...")

        # Find models with create_defaults field
        for py_file in self.project_root.rglob('models.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if re.search(r'create_defaults\s*=\s*models\.', line):
                        self.results['create_defaults_field'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': i,
                            'code': line.strip(),
                            'severity': 'MEDIUM',
                            'category': 'P1',
                            'note': 'Must use create_defaults__exact in update_or_create()'
                        })
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {py_file}: {e}")

    def scan_form_rendering(self):
        """Scan for form rendering patterns."""
        if self.verbose:
            print("Scanning for form rendering...")

        for html_file in self.project_root.rglob('*.html'):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if re.search(r'\.as_table|\.as_p|\.as_ul', line):
                        self.results['form_rendering'].append({
                            'file': str(html_file.relative_to(self.project_root)),
                            'line': i,
                            'severity': 'MEDIUM',
                            'category': 'P1',
                            'note': 'Default rendering changed to div-based'
                        })
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {html_file}: {e}")

    def scan_uuid_fields(self):
        """Scan for UUIDField usage (MariaDB 10.7+ issue)."""
        if self.verbose:
            print("Scanning for UUIDField usage...")

        for py_file in self.project_root.rglob('models.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if 'UUIDField' in line and 'import' not in line:
                        self.results['uuid_field'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': i,
                            'code': line.strip(),
                            'severity': 'MEDIUM',
                            'category': 'P1',
                            'note': 'MariaDB 10.7+ uses UUID column type (breaking change)'
                        })
            except Exception as e:
                if self.verbose:
                    print(f"  Error reading {py_file}: {e}")

    def scan_admin_templates(self):
        """Scan for custom admin templates."""
        if self.verbose:
            print("Scanning for admin templates...")

        admin_templates = list(self.project_root.rglob('templates/admin/**/*.html'))

        if admin_templates:
            for template in admin_templates:
                self.results['admin_templates'].append({
                    'file': str(template.relative_to(self.project_root)),
                    'severity': 'MEDIUM',
                    'category': 'P1',
                    'note': 'Review for HTML structure changes (h1→div, div→main/header)'
                })

    def scan_deprecated_features(self):
        """Scan for deprecated features."""
        if self.verbose:
            print("Scanning for deprecated features...")

        deprecated_patterns = {
            'cx_Oracle': {
                'pattern': r'import cx_Oracle|from cx_Oracle',
                'severity': 'LOW',
                'category': 'P2',
                'note': 'Use oracledb 1.3.2+ instead'
            },
            'DjangoDivFormRenderer': {
                'pattern': r'DjangoDivFormRenderer|Jinja2DivFormRenderer',
                'severity': 'LOW',
                'category': 'P2',
                'note': 'Transitional renderers deprecated'
            },
            'format_html_no_args': {
                'pattern': r'format_html\(\s*\)',
                'severity': 'LOW',
                'category': 'P2',
                'note': 'format_html() requires args or kwargs'
            },
            'Prefetch.get_current_queryset': {
                'pattern': r'get_current_queryset\(',
                'severity': 'LOW',
                'category': 'P2',
                'note': 'Method deprecated'
            },
        }

        for name, config in deprecated_patterns.items():
            for py_file in self.project_root.rglob('*.py'):
                if any(part in py_file.parts for part in ['venv', '.venv', '__pycache__']):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if re.search(config['pattern'], content):
                        self.results[f'deprecated_{name}'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'severity': config['severity'],
                            'category': config['category'],
                            'note': config['note']
                        })
                except Exception as e:
                    if self.verbose:
                        print(f"  Error reading {py_file}: {e}")

    def scan_removed_features(self):
        """Scan for features removed in Django 5.0."""
        if self.verbose:
            print("Scanning for removed features...")

        removed_patterns = {
            'SERIALIZE_test_setting': {
                'pattern': r'SERIALIZE\s*=',
                'file_pattern': 'settings*.py',
                'note': 'SERIALIZE test setting removed'
            },
            'django.utils.datetime_safe': {
                'pattern': r'from django\.utils import datetime_safe|import django\.utils\.datetime_safe',
                'file_pattern': '*.py',
                'note': 'Module removed, use datetime instead'
            },
            'BaseForm._html_output': {
                'pattern': r'\._html_output\(',
                'file_pattern': '*.py',
                'note': 'Method removed'
            },
        }

        for name, config in removed_patterns.items():
            for py_file in self.project_root.rglob(config['file_pattern']):
                if any(part in py_file.parts for part in ['venv', '.venv', '__pycache__']):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if re.search(config['pattern'], content):
                        self.results[f'removed_{name}'].append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'severity': 'CRITICAL',
                            'category': 'P0',
                            'note': config['note']
                        })
                except Exception as e:
                    if self.verbose:
                        print(f"  Error reading {py_file}: {e}")

    def print_report(self):
        """Print comprehensive scan results."""
        print("\n" + "="*70)
        print("DJANGO 5.0 BREAKING CHANGES SCAN RESULTS")
        print("="*70 + "\n")

        if not self.results:
            print("✅ No breaking changes detected!")
            print("\nYour codebase appears to be compatible with Django 5.0.\n")
            print("Recommended next steps:")
            print("1. Create Django 5.0 development environment")
            print("2. Run full test suite")
            print("3. Manual testing of critical features")
            return

        # Categorize by priority
        p0_issues = defaultdict(list)
        p1_issues = defaultdict(list)
        p2_issues = defaultdict(list)

        for key, items in self.results.items():
            for item in items:
                category = item.get('category', 'P2')
                if category == 'P0':
                    p0_issues[key].extend([item])
                elif category == 'P1':
                    p1_issues[key].extend([item])
                else:
                    p2_issues[key].extend([item])

        # Print P0: Critical Issues
        if p0_issues:
            print("🔴 CRITICAL ISSUES (P0 - Must Fix Before Upgrade)\n")
            self._print_issues(p0_issues, show_details=True)

        # Print P1: Important Changes
        if p1_issues:
            print("\n🟡 IMPORTANT CHANGES (P1 - Should Fix)\n")
            self._print_issues(p1_issues, show_details=False)

        # Print P2: Deprecations
        if p2_issues:
            print("\n🟢 DEPRECATED FEATURES (P2 - Plan for Future)\n")
            self._print_issues(p2_issues, show_details=False)

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)

        total_files = len(set(
            item['file'] for items in self.results.values() for item in items
        ))

        print(f"Files scanned: {total_files}")
        print(f"Critical issues (P0): {sum(len(v) for v in p0_issues.values())}")
        print(f"Important changes (P1): {sum(len(v) for v in p1_issues.values())}")
        print(f"Deprecations (P2): {sum(len(v) for v in p2_issues.values())}")
        print()

        # Recommendations
        print("RECOMMENDED NEXT STEPS:")
        print()

        if p0_issues:
            print("1. ❗ Fix all P0 critical issues before upgrading")
            print("   - These WILL break your application in Django 5.0")
            print()

        if p1_issues:
            print("2. ⚠️  Review P1 important changes")
            print("   - These MAY cause issues depending on your code")
            print()

        if p2_issues:
            print("3. 📋 Plan for P2 deprecations")
            print("   - These will be removed in Django 6.0")
            print()

        print("4. 📖 Review full report: BREAKING_CHANGES_REVIEW.md")
        print("5. 🧪 Create test environment and run tests")
        print("6. 📊 Fill out MIGRATION_DECISION_ASSESSMENT.md")
        print()

    def _print_issues(self, issues_dict, show_details=False):
        """Print issues with optional details."""
        for key, items in sorted(issues_dict.items()):
            issue_name = key.replace('_', ' ').title()
            print(f"  {issue_name}: {len(items)} occurrence(s)")

            if show_details:
                for item in items[:5]:  # Show first 5
                    print(f"    📄 {item['file']}", end='')
                    if 'line' in item:
                        print(f":{item['line']}", end='')
                    print()
                    if 'code' in item:
                        print(f"       {item['code'][:80]}")
                    if 'note' in item:
                        print(f"       Note: {item['note']}")

                if len(items) > 5:
                    print(f"    ... and {len(items) - 5} more")
            else:
                # Just show file count
                unique_files = len(set(item['file'] for item in items))
                print(f"    Affected files: {unique_files}")

            print()

    def export_json(self, output_file='breaking_changes_scan.json'):
        """Export results as JSON."""
        import json

        output = {
            'scan_date': str(Path.ctime(Path(__file__))),
            'project_root': str(self.project_root.absolute()),
            'summary': {
                'total_issues': sum(len(v) for v in self.results.values()),
                'p0_critical': sum(
                    len(v) for v in self.results.values()
                    if v and v[0].get('category') == 'P0'
                ),
                'p1_important': sum(
                    len(v) for v in self.results.values()
                    if v and v[0].get('category') == 'P1'
                ),
                'p2_deprecated': sum(
                    len(v) for v in self.results.values()
                    if v and v[0].get('category') == 'P2'
                ),
            },
            'issues': dict(self.results)
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n📄 Detailed results exported to {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Scan Django project for Django 5.0 breaking changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan_breaking_changes.py
  python scan_breaking_changes.py --path /path/to/project
  python scan_breaking_changes.py --json --verbose
        """
    )
    parser.add_argument(
        '--path',
        default='.',
        help='Path to Django project root (default: current directory)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Export results as JSON'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output'
    )

    args = parser.parse_args()

    scanner = BreakingChangeScanner(args.path, verbose=args.verbose)
    scanner.scan_all()

    if args.json:
        scanner.export_json()


if __name__ == '__main__':
    main()
