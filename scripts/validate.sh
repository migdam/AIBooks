#!/bin/bash
# Validation script for AIBooks

set -e

echo "🔍 AIBooks Validation Script"
echo "=============================="
echo

# Check Python syntax
echo "1️⃣  Checking Python syntax..."
find src -name "*.py" -type f -exec python3 -m py_compile {} \;
echo "✅ All Python files have valid syntax"
echo

# Run basic tests
echo "2️⃣  Running basic functionality tests..."
python3 scripts/test_basic.py
echo

# Check for common issues
echo "3️⃣  Checking for common issues..."

# Check for print statements (should use logger)
print_count=$(grep -r "print(" src --include="*.py" | grep -v "# noqa" | wc -l || true)
if [ "$print_count" -gt 0 ]; then
    echo "⚠️  Warning: Found $print_count print() statements (should use logger)"
else
    echo "✅ No print() statements found"
fi

# Check for TODO comments
todo_count=$(grep -r "TODO" src --include="*.py" | wc -l || true)
if [ "$todo_count" -gt 0 ]; then
    echo "ℹ️  Found $todo_count TODO comments"
else
    echo "✅ No TODO comments"
fi

echo

# Check file structure
echo "4️⃣  Checking project structure..."

required_files=(
    "src/aibooks/__init__.py"
    "src/aibooks/cli.py"
    "src/aibooks/db/models.py"
    "src/aibooks/db/database.py"
    "src/aibooks/parsers/format_detector.py"
    "src/aibooks/parsers/docling_parser.py"
    "src/aibooks/agents/base_agent.py"
    "src/aibooks/core/processor.py"
    "pyproject.toml"
    "README.md"
    ".env.example"
)

all_present=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ Missing: $file"
        all_present=false
    fi
done

echo

if [ "$all_present" = true ]; then
    echo "🎉 Validation complete - all checks passed!"
    exit 0
else
    echo "❌ Validation failed - some files are missing"
    exit 1
fi
