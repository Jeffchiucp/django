#!/usr/bin/env python3
"""
Detailed pytz Migration Analysis Script
Analyzes Django migrations for pytz usage and provides path recommendations.

Usage:
    python analyze_pytz_migrations.py [--path PROJECT_ROOT]
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict


class MigrationAnalyzer:
    """Analyzes Django migrations for pytz dependencies."""

    def __init__(self, project_root='.'):
        self.project_root = Path(project_root)
        self.results = []

    def analyze_migration(self, filepath):
        """Analyze a single migration file for pytz usage."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Error reading {filepath}: {e}")
            return None

        # Check for pytz import
        has_pytz_import = bool(re.search(r'import pytz|from pytz', content))
        if not has_pytz_import:
            return None

        # Check for RunPython
        has_runpython = 'RunPython' in content

        # Find actual pytz usage
        pytz_calls = re.findall(r'pytz\.\w+(?:\([^)]*\))?', content)

        # Check if pytz is used in RunPython functions
        in_runpython = False
        runpython_functions = []

        if has_runpython:
            # Extract function definitions that might be used in RunPython
            functions = re.findall(
                r'def (\w+)\(apps, schema_editor\):(.*?)(?=\ndef |\nclass |\Z)',
                content,
                re.DOTALL
            )

            for func_name, func_body in functions:
                if 'pytz' in func_body:
                    in_runpython = True
                    # Extract pytz usage lines
                    lines = [line.strip() for line in func_body.split('\n')
                             if 'pytz' in line and line.strip()]
                    runpython_functions.append({
                        'name': func_name,
                        'usage': lines[:3]  # First 3 lines
                    })

        # Determine risk level
        if in_runpython:
            risk = 'HIGH'
        elif pytz_calls:
            risk = 'MEDIUM'
        else:
            risk = 'LOW'

        return {
            'file': str(filepath.relative_to(self.project_root)),
            'has_import': has_pytz_import,
            'has_runpython': has_runpython,
            'in_runpython': in_runpython,
            'pytz_calls': pytz_calls,
            'runpython_functions': runpython_functions,
            'risk': risk,
            'line_count': len(content.split('\n'))
        }

    def scan_project(self):
        """Scan entire project for migrations."""
        print("🔍 Scanning for migrations with pytz usage...\n")

        migration_files = list(self.project_root.rglob('migrations/*.py'))
        total_migrations = len([f for f in migration_files if f.name != '__init__.py'])

        print(f"Found {total_migrations} migration files\n")

        for migration_file in migration_files:
            if migration_file.name == '__init__.py':
                continue

            result = self.analyze_migration(migration_file)
            if result:
                self.results.append(result)

        return self.results

    def print_report(self):
        """Print detailed analysis report."""
        if not self.results:
            print("="*60)
            print("✅ EXCELLENT NEWS!")
            print("="*60)
            print("\nNo migrations use pytz!\n")
            print("📋 Q3 Answer: NO - No RunPython with pytz")
            print("✅ Implication: Safe to leave migrations as-is\n")
            print("🎯 RECOMMENDATION: Path A (Remove pytz)")
            print("   - Update requirements.txt to remove pytz")
            print("   - Test in development environment")
            print("   - Deploy and monitor\n")
            return

        # Categorize results
        high_risk = [r for r in self.results if r['risk'] == 'HIGH']
        medium_risk = [r for r in self.results if r['risk'] == 'MEDIUM']
        low_risk = [r for r in self.results if r['risk'] == 'LOW']

        print("="*60)
        print(f"📊 ANALYSIS RESULTS: {len(self.results)} migrations use pytz")
        print("="*60)
        print()

        # High risk migrations
        if high_risk:
            print(f"🔴 HIGH RISK: {len(high_risk)} migration(s)")
            print("   RunPython functions that USE pytz")
            print("   → These WILL FAIL on fresh database without pytz\n")

            for r in high_risk:
                print(f"   📄 {r['file']}")
                for func in r['runpython_functions']:
                    print(f"      Function: {func['name']}")
                    for line in func['usage']:
                        print(f"         {line}")
                print()

        # Medium risk migrations
        if medium_risk:
            print(f"🟡 MEDIUM RISK: {len(medium_risk)} migration(s)")
            print("   Use pytz but not in RunPython")
            print("   → Might work without pytz (needs testing)\n")

            for r in medium_risk:
                print(f"   📄 {r['file']}")
                if r['pytz_calls']:
                    print(f"      Usage: {', '.join(r['pytz_calls'][:3])}")
                print()

        # Low risk migrations
        if low_risk:
            print(f"🟢 LOW RISK: {len(low_risk)} migration(s)")
            print("   Import pytz but don't use it")
            print("   → Safe to remove import\n")

            for r in low_risk:
                print(f"   📄 {r['file']}")
            print()

        # Print recommendation
        self.print_recommendation(len(high_risk), len(medium_risk), len(low_risk))

    def print_recommendation(self, high, medium, low):
        """Print path recommendation based on analysis."""
        print("="*60)
        print("🎯 RECOMMENDATION")
        print("="*60)
        print()

        total = high + medium + low

        if high >= 4:
            print("📋 Recommended Path: C (Keep pytz)")
            print()
            print("Reasoning:")
            print(f"  • {high} migrations have RunPython with pytz")
            print("  • Creating compatibility layer would be complex")
            print("  • Keeping pytz is lowest risk approach")
            print()
            print("Action Items:")
            print("  1. Keep pytz>=2024.1 in requirements.txt")
            print("  2. Add comment: '# For historical migrations only'")
            print("  3. Update coding guidelines to use zoneinfo in new code")
            print("  4. Document decision in MIGRATION_DECISION_ASSESSMENT.md")
            print()
            print("📋 Q3 Answer: YES (Many migrations)")
            print()

        elif high >= 1:
            print("📋 Recommended Path: B (Compatibility Layer) or C (Keep pytz)")
            print()
            print("Reasoning:")
            print(f"  • {high} migration(s) have RunPython with pytz")
            print("  • Small enough to create compatibility layer")
            print("  • Or keep pytz if you prefer simplicity")
            print()
            print("Path B (Compatibility Layer):")
            print("  1. Create core/migration_utils.py with zoneinfo wrapper")
            print("  2. Update affected migrations to use compatibility layer")
            print("  3. Test on fresh database without pytz")
            print("  4. Remove pytz from requirements.txt")
            print("  Timeline: 3-5 days")
            print()
            print("Path C (Keep pytz):")
            print("  1. Keep pytz>=2024.1 in requirements.txt")
            print("  2. Document decision")
            print("  Timeline: 1 hour")
            print()
            print("📋 Q3 Answer: YES (Few migrations)")
            print()

        elif medium >= 1:
            print("📋 Recommended Path: A (Test removal) or C (Keep pytz)")
            print()
            print("Reasoning:")
            print(f"  • {medium} migration(s) use pytz outside RunPython")
            print("  • Likely safe to remove, but needs testing")
            print("  • No fresh database concerns")
            print()
            print("Action Items:")
            print("  1. Remove pytz from requirements.txt")
            print("  2. Run migrations on fresh test database")
            print("  3. If successful, deploy to production")
            print("  4. If fails, add pytz back (Path C)")
            print()
            print("📋 Q3 Answer: Maybe - Needs testing")
            print()

        else:  # only low risk
            print("📋 Recommended Path: A (Remove pytz)")
            print()
            print("Reasoning:")
            print(f"  • {low} migration(s) only IMPORT pytz (don't use it)")
            print("  • Safe to remove pytz dependency")
            print("  • Clean solution with no risk")
            print()
            print("Action Items:")
            print("  1. Remove pytz from requirements.txt")
            print("  2. Test in development environment")
            print("  3. Deploy to production")
            print()
            print("📋 Q3 Answer: NO - Only unused imports")
            print()

        # Summary table
        print("Summary:")
        print(f"  Total migrations with pytz: {total}")
        print(f"  High risk (RunPython): {high}")
        print(f"  Medium risk (Usage): {medium}")
        print(f"  Low risk (Import only): {low}")
        print()

    def export_json(self, output_file='pytz_analysis.json'):
        """Export results as JSON."""
        import json

        output = {
            'total_migrations': len(self.results),
            'high_risk': len([r for r in self.results if r['risk'] == 'HIGH']),
            'medium_risk': len([r for r in self.results if r['risk'] == 'MEDIUM']),
            'low_risk': len([r for r in self.results if r['risk'] == 'LOW']),
            'migrations': self.results
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"📄 Detailed results exported to {output_file}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze Django migrations for pytz usage'
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

    args = parser.parse_args()

    analyzer = MigrationAnalyzer(args.path)
    analyzer.scan_project()
    analyzer.print_report()

    if args.json:
        analyzer.export_json()


if __name__ == '__main__':
    main()
