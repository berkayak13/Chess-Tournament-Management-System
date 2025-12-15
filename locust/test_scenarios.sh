#!/bin/bash
# ============================================================================
# Chess Tournament Management System - Load Test Scenarios
# ============================================================================
#
# This script provides predefined test scenarios for different testing types:
# 1. Baseline Test - Establish normal performance metrics
# 2. Load Test - Test with expected normal load
# 3. Stress Test - Push system to its limits
# 4. Spike Test - Sudden traffic spikes
# 5. Endurance Test - Sustained load over time
#
# Usage:
#   ./test_scenarios.sh baseline
#   ./test_scenarios.sh load
#   ./test_scenarios.sh stress
#   ./test_scenarios.sh spike
#   ./test_scenarios.sh endurance
#
# Requirements:
#   - Locust installed (pip install -r requirements.txt)
#   - Application running on http://localhost:8080 (or set HOST variable)
#   - Python 3.7+
# ============================================================================

set -e

# Configuration
HOST="${HOST:-http://localhost:8080}"
RESULTS_DIR="test_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$RESULTS_DIR"

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_app_running() {
    print_header "Checking if application is running..."
    if curl -s -f -o /dev/null "$HOST"; then
        print_success "Application is running at $HOST"
        return 0
    else
        print_error "Application is not accessible at $HOST"
        print_warning "Please start the application first"
        return 1
    fi
}

start_resource_monitor() {
    local duration=$1
    local test_name=$2

    print_success "Starting resource monitoring for ${duration}s..."

    python monitor_resources.py \
        --interval 1 \
        --duration "$duration" \
        --output "$RESULTS_DIR/resources_${test_name}_${TIMESTAMP}.json" &

    MONITOR_PID=$!
    echo $MONITOR_PID
}

wait_for_monitor() {
    local pid=$1
    if ps -p "$pid" > /dev/null 2>&1; then
        wait "$pid"
        print_success "Resource monitoring completed"
    fi
}

# Test Scenarios
# ============================================================================

baseline_test() {
    print_header "BASELINE TEST"
    echo "Purpose: Establish baseline performance metrics with minimal load"
    echo "Duration: 2 minutes"
    echo "Users: 1-5 users"
    echo "Spawn rate: 1 user/second"
    echo ""

    if ! check_app_running; then
        return 1
    fi

    DURATION=120
    MONITOR_PID=$(start_resource_monitor $DURATION "baseline")

    print_success "Starting baseline test..."

    locust -f locustfile.py \
        --host="$HOST" \
        --users 5 \
        --spawn-rate 1 \
        --run-time "${DURATION}s" \
        --headless \
        --html "$RESULTS_DIR/baseline_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/baseline_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Baseline test completed!"
    echo "Results saved with prefix: baseline_${TIMESTAMP}"
}

load_test() {
    print_header "LOAD TEST"
    echo "Purpose: Test system under expected production load"
    echo "Duration: 5 minutes"
    echo "Users: 10-50 users (average load)"
    echo "Spawn rate: 5 users/second"
    echo ""

    if ! check_app_running; then
        return 1
    fi

    DURATION=300
    MONITOR_PID=$(start_resource_monitor $DURATION "load")

    print_success "Starting load test..."

    locust -f locustfile.py \
        --host="$HOST" \
        --users 50 \
        --spawn-rate 5 \
        --run-time "${DURATION}s" \
        --headless \
        --html "$RESULTS_DIR/load_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/load_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Load test completed!"
    echo "Results saved with prefix: load_${TIMESTAMP}"
}

stress_test() {
    print_header "STRESS TEST"
    echo "Purpose: Find system breaking point and resource limits"
    echo "Duration: 7 minutes"
    echo "Users: Ramp from 50 to 200 users"
    echo "Spawn rate: 10 users/second"
    echo ""

    if ! check_app_running; then
        return 1
    fi

    DURATION=420
    MONITOR_PID=$(start_resource_monitor $DURATION "stress")

    print_success "Starting stress test..."
    print_warning "This test will push your system to its limits!"

    locust -f locustfile.py \
        --host="$HOST" \
        --users 200 \
        --spawn-rate 10 \
        --run-time "${DURATION}s" \
        --headless \
        --html "$RESULTS_DIR/stress_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/stress_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Stress test completed!"
    echo "Results saved with prefix: stress_${TIMESTAMP}"
}

spike_test() {
    print_header "SPIKE TEST"
    echo "Purpose: Test system behavior under sudden traffic spikes"
    echo "Duration: 4 minutes"
    echo "Pattern: 5 users → spike to 100 → back to 5"
    echo ""

    if ! check_app_running; then
        return 1
    fi

    print_success "Starting spike test (3 stages)..."

    # Stage 1: Normal load (1 min)
    print_success "Stage 1/3: Normal load (5 users, 60s)..."
    MONITOR_PID=$(start_resource_monitor 60 "spike_stage1")

    locust -f locustfile.py \
        --host="$HOST" \
        --users 5 \
        --spawn-rate 2 \
        --run-time 60s \
        --headless \
        --html "$RESULTS_DIR/spike_stage1_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/spike_stage1_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"

    # Stage 2: Spike (2 min)
    print_success "Stage 2/3: Traffic spike (100 users, 120s)..."
    MONITOR_PID=$(start_resource_monitor 120 "spike_stage2")

    locust -f locustfile.py \
        --host="$HOST" \
        --users 100 \
        --spawn-rate 20 \
        --run-time 120s \
        --headless \
        --html "$RESULTS_DIR/spike_stage2_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/spike_stage2_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"

    # Stage 3: Recovery (1 min)
    print_success "Stage 3/3: Recovery (5 users, 60s)..."
    MONITOR_PID=$(start_resource_monitor 60 "spike_stage3")

    locust -f locustfile.py \
        --host="$HOST" \
        --users 5 \
        --spawn-rate 2 \
        --run-time 60s \
        --headless \
        --html "$RESULTS_DIR/spike_stage3_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/spike_stage3_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Spike test completed!"
    echo "Results saved with prefix: spike_stage*_${TIMESTAMP}"
}

endurance_test() {
    print_header "ENDURANCE TEST (SOAK TEST)"
    echo "Purpose: Test system stability over extended period"
    echo "Duration: 30 minutes"
    echo "Users: 30 users (sustained)"
    echo "Spawn rate: 3 users/second"
    echo ""
    print_warning "This test will run for 30 minutes!"

    if ! check_app_running; then
        return 1
    fi

    DURATION=1800
    MONITOR_PID=$(start_resource_monitor $DURATION "endurance")

    print_success "Starting endurance test..."

    locust -f locustfile.py \
        --host="$HOST" \
        --users 30 \
        --spawn-rate 3 \
        --run-time "${DURATION}s" \
        --headless \
        --html "$RESULTS_DIR/endurance_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/endurance_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Endurance test completed!"
    echo "Results saved with prefix: endurance_${TIMESTAMP}"
}

custom_test() {
    print_header "CUSTOM TEST"
    echo "Purpose: Run custom test with specified parameters"
    echo ""

    read -p "Number of users: " USERS
    read -p "Spawn rate (users/second): " SPAWN_RATE
    read -p "Duration (seconds): " DURATION
    read -p "Test name: " TEST_NAME

    if ! check_app_running; then
        return 1
    fi

    MONITOR_PID=$(start_resource_monitor $DURATION "$TEST_NAME")

    print_success "Starting custom test..."

    locust -f locustfile.py \
        --host="$HOST" \
        --users "$USERS" \
        --spawn-rate "$SPAWN_RATE" \
        --run-time "${DURATION}s" \
        --headless \
        --html "$RESULTS_DIR/${TEST_NAME}_${TIMESTAMP}.html" \
        --csv "$RESULTS_DIR/${TEST_NAME}_${TIMESTAMP}" \
        --loglevel INFO

    wait_for_monitor "$MONITOR_PID"
    print_success "Custom test completed!"
    echo "Results saved with prefix: ${TEST_NAME}_${TIMESTAMP}"
}

run_all_tests() {
    print_header "RUNNING ALL TEST SCENARIOS"
    print_warning "This will run all tests sequentially. Total time: ~50 minutes"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Aborted"
        return 1
    fi

    baseline_test
    sleep 30  # Cool down
    load_test
    sleep 30
    stress_test
    sleep 60
    spike_test
    # Skip endurance test by default
    # endurance_test

    print_header "ALL TESTS COMPLETED"
    echo "Results saved in: $RESULTS_DIR"
}

show_help() {
    cat << EOF
Chess Tournament Load Test Scenarios

Usage:
    ./test_scenarios.sh [scenario]

Available Scenarios:
    baseline    - Baseline test (2 min, 5 users)
    load        - Load test (5 min, 50 users)
    stress      - Stress test (7 min, up to 200 users)
    spike       - Spike test (4 min, sudden traffic spikes)
    endurance   - Endurance test (30 min, 30 users sustained)
    custom      - Custom test with your parameters
    all         - Run all tests (except endurance)
    help        - Show this help message

Environment Variables:
    HOST        - Target host (default: http://localhost:8080)

Examples:
    ./test_scenarios.sh baseline
    HOST=http://localhost:5000 ./test_scenarios.sh load
    ./test_scenarios.sh custom

Results:
    All results are saved in the '$RESULTS_DIR' directory
    - HTML reports: *_TIMESTAMP.html
    - CSV data: *_TIMESTAMP_stats.csv
    - Resource usage: resources_*_TIMESTAMP.json
    - Performance metrics: performance_results_*.json

EOF
}

# Main script
# ============================================================================

case "${1:-help}" in
    baseline)
        baseline_test
        ;;
    load)
        load_test
        ;;
    stress)
        stress_test
        ;;
    spike)
        spike_test
        ;;
    endurance)
        endurance_test
        ;;
    custom)
        custom_test
        ;;
    all)
        run_all_tests
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown scenario: $1"
        show_help
        exit 1
        ;;
esac

print_header "Test Complete"
echo "Results directory: $RESULTS_DIR"
echo ""
echo "Next steps:"
echo "  1. Review HTML report: open $RESULTS_DIR/*.html"
echo "  2. Analyze metrics: python analyze_results.py"
echo "  3. Generate slide content: python generate_slides.py"
