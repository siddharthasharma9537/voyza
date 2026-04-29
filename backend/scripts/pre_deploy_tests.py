#!/usr/bin/env python
"""
🚀 Pre-Deployment Testing Script for Voyza
──────────────────────────────────────────
Runs all checks before deploying to production.
Works on Windows, Mac, and Linux.

Usage: python scripts/pre_deploy_tests.py
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

# ANSI Colors
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def success(self, message: str):
        print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
        self.passed += 1

    def error(self, message: str):
        print(f"{Colors.RED}❌ {message}{Colors.RESET}")
        self.failed += 1

    def warning(self, message: str):
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
        self.warnings += 1

    def info(self, message: str):
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")

    def section(self, title: str):
        print()
        print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")
        print(f"{Colors.BLUE}{title}{Colors.RESET}")
        print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")

    def summary(self):
        total = self.passed + self.failed + self.warnings
        print()
        print(f"{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  {Colors.GREEN}✅ Passed:   {self.passed}{Colors.RESET}")
        print(f"  {Colors.RED}❌ Failed:   {self.failed}{Colors.RESET}")
        print(f"  {Colors.YELLOW}⚠️  Warnings: {self.warnings}{Colors.RESET}")
        print()

        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ READY FOR DEPLOYMENT{Colors.RESET}")
            if self.warnings == 0:
                print("   All checks passed with no issues!")
            else:
                print(f"   Passed all critical checks. Review {self.warnings} warnings above.")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ NOT READY FOR DEPLOYMENT{Colors.RESET}")
            print(f"   Fix {self.failed} errors before deploying.")
            return 1

def run_command(cmd: list) -> Tuple[bool, str]:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def main():
    result = TestResult()

    # Header
    print(f"{Colors.BLUE}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║  🚀 Voyza Pre-Deployment Test Suite                   ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    # Check working directory
    if not Path("requirements.txt").exists():
        result.error("requirements.txt not found. Run from backend directory.")
        return 1

    # ═══════════════════════════════════════════════════════════════════════

    result.section("📦 Step 1: Environment Setup")

    result.info("Checking Python version...")
    success, output = run_command([sys.executable, "--version"])
    if success:
        result.success(f"Python {output.strip()}")
    else:
        result.error("Python not found")

    result.info("Checking pip...")
    success, output = run_command([sys.executable, "-m", "pip", "--version"])
    if success:
        result.success("pip is available")
    else:
        result.error("pip not found")

    if sys.prefix != sys.base_prefix:
        result.success(f"Virtual environment active: {sys.prefix}")
    else:
        result.warning("Virtual environment not activated (optional)")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("📚 Step 2: Dependency Check")

    result.info("Checking required packages...")
    required_packages = ["fastapi", "sqlalchemy", "pytest", "pydantic", "jose"]

    for package in required_packages:
        success, _ = run_command([sys.executable, "-c", f"import {package}"])
        if success:
            result.success(f"{package} is installed")
        else:
            result.error(f"{package} is NOT installed")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("🔍 Step 3: Syntax & Import Check")

    result.info("Checking Python syntax in app code...")
    syntax_errors = 0
    for py_file in Path("app").rglob("*.py"):
        success, _ = run_command([sys.executable, "-m", "py_compile", str(py_file)])
        if not success:
            syntax_errors += 1
            result.warning(f"Syntax error in {py_file}")

    if syntax_errors == 0:
        result.success("All Python files have valid syntax")
    else:
        result.error(f"{syntax_errors} files have syntax errors")

    result.info("Checking test file syntax...")
    test_syntax_errors = 0
    test_dir = Path("tests")
    if test_dir.exists():
        for py_file in test_dir.rglob("*.py"):
            success, _ = run_command([sys.executable, "-m", "py_compile", str(py_file)])
            if not success:
                test_syntax_errors += 1
                result.warning(f"Syntax error in {py_file}")

        if test_syntax_errors == 0:
            result.success("All test files have valid syntax")
        else:
            result.error(f"{test_syntax_errors} test files have syntax errors")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("🔐 Step 4: Security Checks")

    result.info("Checking for hardcoded secrets...")
    secret_patterns = ["password.*=.*['\"]", "secret.*=.*['\"]", "api_key.*=.*['\"]"]
    secrets_found = 0

    for py_file in Path("app").rglob("*.py"):
        with open(py_file, "r") as f:
            content = f.read()
            if "sk_live" in content or "sk_test" in content:
                result.error(f"API key found in {py_file}")
                secrets_found += 1

    if secrets_found == 0:
        result.success("No obvious hardcoded API keys detected")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("🧪 Step 5: Unit & Integration Tests")

    result.info("Running integration tests (this may take a minute)...")
    success, output = run_command([
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ])

    if success:
        result.success("All integration tests passed")
        # Count tests
        test_count = output.count(" PASSED")
        if test_count > 0:
            result.success(f"Ran {test_count} tests successfully")
    else:
        result.error("Some tests failed")
        # Show last part of output
        lines = output.split("\n")
        print("\nTest output (last 20 lines):")
        for line in lines[-20:]:
            if line.strip():
                print(f"  {line}")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("📋 Step 6: Code Quality Checks")

    result.info("Checking for common issues...")

    # Check for inline imports
    inline_import_count = 0
    for py_file in Path("app/api/v1/endpoints").glob("*.py"):
        with open(py_file, "r") as f:
            for line in f:
                if line.startswith("    from ") and "settings" not in line:
                    inline_import_count += 1

    if inline_import_count <= 5:
        result.success("Inline imports are minimized")
    else:
        result.warning(f"Found {inline_import_count} inline imports")

    # Check for print statements
    print_count = 0
    for py_file in Path("app").rglob("*.py"):
        with open(py_file, "r") as f:
            for line in f:
                if "print(" in line and not line.strip().startswith("#"):
                    print_count += 1

    if print_count == 0:
        result.success("No print statements found (using logging)")
    else:
        result.warning(f"Found {print_count} print() statements (use logging)")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("🔧 Step 7: Configuration Validation")

    result.info("Checking environment configuration...")

    # Check settings import
    success, _ = run_command([
        sys.executable, "-c",
        "from app.core.config import settings"
    ])

    if success:
        result.success("Settings configuration is valid")
    else:
        result.warning("Settings import failed (may be expected if .env not set)")

    # Check for database config
    config_file = Path("app/core/config.py")
    if config_file.exists():
        content = config_file.read_text()
        if "POSTGRES" in content or "DATABASE" in content:
            result.success("Database configuration found")

    # Check for OAuth
    if "GOOGLE_CLIENT_ID" in content or "APPLE_CLIENT_ID" in content:
        result.success("OAuth configurations found")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("📝 Step 8: Documentation Check")

    required_docs = ["tests/README.md", "app/main.py", "app/api/v1/endpoints/auth.py"]

    for doc in required_docs:
        doc_path = Path(doc)
        if doc_path.exists():
            result.success(f"{doc} exists")
        else:
            result.error(f"{doc} is missing")

    # ═══════════════════════════════════════════════════════════════════════

    result.section("📊 Pre-Deployment Summary")

    result.summary()

    # ═══════════════════════════════════════════════════════════════════════

    print()
    print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")
    print(f"{Colors.BLUE}📋 Pre-Deployment Checklist{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")

    checklist = """
Before deploying to production:

☐ All tests pass (run: pytest tests/integration/ -v)
☐ No syntax errors in Python files
☐ No hardcoded secrets or API keys
☐ Environment variables configured (.env file)
☐ Database migrations ready (alembic upgrade head)
☐ Twilio credentials configured (SMS delivery)
☐ Razorpay credentials configured (payments)
☐ OAuth credentials configured (Google, Apple, Facebook)
☐ S3/MinIO bucket configured (file uploads)
☐ SendGrid API key configured (email)
☐ Redis configured (caching and job queues)
☐ Log aggregation configured (structured logging)
☐ Monitoring and alerts configured
☐ Backup strategy in place
☐ Load balancer/proxy configured
☐ SSL certificates configured
☐ CORS origins configured correctly

Key Endpoints to Test After Deployment:
  - POST /api/v1/auth/register/send-phone-otp (phone OTP)
  - POST /api/v1/auth/verify-otp (OTP verification)
  - POST /api/v1/bookings (create booking)
  - GET  /api/v1/vehicles (browse vehicles)
  - POST /api/v1/payments/create-order (payment)
  - GET  /api/v1/owner/cars (owner vehicles)

For More Information:
  - See tests/README.md for test documentation
  - See app/main.py for application setup
  - Check environment variables in app/core/config.py
"""
    print(checklist)

    print(f"{Colors.BLUE}{'─' * 50}{Colors.RESET}")
    print()

    return result.summary()

if __name__ == "__main__":
    sys.exit(main())
