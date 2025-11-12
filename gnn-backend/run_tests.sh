#!/bin/bash
#
# Test Runner Script for Oil GNN Prediction Backend
# Runs unit tests, integration tests, and E2E tests
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}Oil GNN Prediction - Test Suite${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# Change to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r tests/requirements-test.txt

# Check environment variables
echo -e "\n${BLUE}Checking environment variables...${NC}"

if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  ALPHA_VANTAGE_API_KEY not set${NC}"
    echo -e "   Some tests will be skipped"
else
    echo -e "${GREEN}✓ ALPHA_VANTAGE_API_KEY is set${NC}"
fi

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_APPLICATION_CREDENTIALS not set${NC}"
    echo -e "   GCS-related tests will be skipped"
else
    echo -e "${GREEN}✓ GOOGLE_APPLICATION_CREDENTIALS is set${NC}"
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
VERBOSE="${2:-}"

echo -e "\n${BLUE}=====================================================================${NC}"
echo -e "${BLUE}Running Tests: $TEST_TYPE${NC}"
echo -e "${BLUE}=====================================================================${NC}"

# Set pytest options
PYTEST_OPTS="-v -s --tb=short"
if [ "$VERBOSE" = "-v" ] || [ "$VERBOSE" = "--verbose" ]; then
    PYTEST_OPTS="-vv -s --tb=long"
fi

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "\n${GREEN}Running Unit Tests (Data Pipeline)${NC}"
        pytest tests/test_data_pipeline.py $PYTEST_OPTS
        ;;
    
    inference)
        echo -e "\n${GREEN}Running Inference Tests${NC}"
        pytest tests/test_inference.py $PYTEST_OPTS
        ;;
    
    e2e)
        echo -e "\n${GREEN}Running End-to-End Tests${NC}"
        pytest tests/test_e2e.py $PYTEST_OPTS
        ;;
    
    all)
        echo -e "\n${GREEN}1/3: Running Unit Tests (Data Pipeline)${NC}"
        pytest tests/test_data_pipeline.py $PYTEST_OPTS
        
        echo -e "\n${GREEN}2/3: Running Inference Tests${NC}"
        pytest tests/test_inference.py $PYTEST_OPTS
        
        echo -e "\n${GREEN}3/3: Running End-to-End Tests${NC}"
        pytest tests/test_e2e.py $PYTEST_OPTS
        ;;
    
    coverage)
        echo -e "\n${GREEN}Running Tests with Coverage${NC}"
        pytest tests/ --cov=. --cov-report=html --cov-report=term $PYTEST_OPTS
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo -e "Usage: $0 [unit|inference|e2e|all|coverage] [-v|--verbose]"
        exit 1
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo -e "\n${BLUE}=====================================================================${NC}"
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${BLUE}=====================================================================${NC}"
else
    echo -e "\n${BLUE}=====================================================================${NC}"
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${BLUE}=====================================================================${NC}"
    exit 1
fi

# Deactivate virtual environment
deactivate
