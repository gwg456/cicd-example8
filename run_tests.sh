#!/bin/bash
# Test runner script with different test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Running Prefect CI/CD Test Suite${NC}"
echo "=================================="

# Function to run tests
run_tests() {
    local test_type=$1
    local test_args=$2
    
    echo -e "\n${YELLOW}Running $test_type tests...${NC}"
    
    if pytest $test_args; then
        echo -e "${GREEN}✅ $test_type tests passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_type tests failed${NC}"
        return 1
    fi
}

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        run_tests "Unit" "-m unit"
        ;;
    integration)
        run_tests "Integration" "-m integration"
        ;;
    e2e)
        run_tests "End-to-End" "-m e2e"
        ;;
    coverage)
        echo -e "${YELLOW}Running tests with coverage report...${NC}"
        pytest --cov=src --cov-report=term-missing --cov-report=html
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    quick)
        echo -e "${YELLOW}Running quick tests (no slow tests)...${NC}"
        pytest -m "not slow"
        ;;
    ci)
        echo -e "${YELLOW}Running CI test suite...${NC}"
        # Run linting first
        echo "Running linters..."
        flake8 src tests --max-line-length=120 --ignore=E203,W503 || true
        black --check src tests || true
        mypy src --ignore-missing-imports || true
        
        # Run security checks
        echo "Running security checks..."
        bandit -r src -ll || true
        safety check || true
        
        # Run tests with coverage
        pytest --cov=src --cov-report=xml --cov-report=term
        ;;
    all|*)
        # Run all test categories
        run_tests "Unit" "tests/test_config.py tests/test_core.py"
        run_tests "Flow" "tests/test_flows.py"
        run_tests "Deployment" "tests/test_deployment.py"
        
        # Generate coverage report
        echo -e "\n${YELLOW}Generating coverage report...${NC}"
        pytest --cov=src --cov-report=term-missing --quiet
        ;;
esac

echo -e "\n${GREEN}✨ Test suite completed!${NC}"