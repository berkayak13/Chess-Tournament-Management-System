# Chess Tournament Management System - Performance Testing Guide

Complete guide for running performance tests and analyzing system robustness.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Scenarios](#test-scenarios)
3. [Metrics Collected](#metrics-collected)
4. [Running Tests](#running-tests)
5. [Analyzing Results](#analyzing-results)
6. [Understanding Results](#understanding-results)
7. [Creating Presentation Slides](#creating-presentation-slides)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd locust/
pip install -r requirements.txt
```

### 2. Start Your Application

```bash
# In the project root
python app.py
# Application should be running on http://localhost:8080
```

### 3. Run a Test

```bash
# Make script executable
chmod +x test_scenarios.sh

# Run baseline test
./test_scenarios.sh baseline
```

### 4. View Results

```bash
# Open HTML report
open test_results/baseline_*.html

# Analyze metrics
python analyze_results.py
```

## 📊 Test Scenarios

We provide 5 predefined test scenarios:

### 1. **Baseline Test** (2 minutes)
- **Purpose:** Establish baseline performance metrics
- **Users:** 5 concurrent users
- **Use Case:** Normal, minimal load
- **Command:** `./test_scenarios.sh baseline`

### 2. **Load Test** (5 minutes)
- **Purpose:** Test under expected production load
- **Users:** 50 concurrent users
- **Use Case:** Average daily traffic
- **Command:** `./test_scenarios.sh load`

### 3. **Stress Test** (7 minutes)
- **Purpose:** Find system breaking point
- **Users:** Up to 200 concurrent users
- **Use Case:** Peak traffic, Black Friday scenarios
- **Command:** `./test_scenarios.sh stress`

### 4. **Spike Test** (4 minutes, 3 stages)
- **Purpose:** Test recovery from traffic spikes
- **Pattern:** 5 → 100 → 5 users
- **Use Case:** Viral content, sudden popularity
- **Command:** `./test_scenarios.sh spike`

### 5. **Endurance Test** (30 minutes)
- **Purpose:** Test stability over extended period
- **Users:** 30 concurrent users sustained
- **Use Case:** Detect memory leaks, degradation
- **Command:** `./test_scenarios.sh endurance`

## 📈 Metrics Collected

### Independent Variables (What We Control)
- **Request Load:** Number of concurrent users
- **Request Rate:** Spawn rate (users/second)
- **Test Duration:** How long the test runs
- **User Behavior:** Mix of different user types

### Dependent Variables (What We Measure)

#### 1. **Request Latency**
- **p50 (Median):** 50% of requests faster than this
- **p95:** 95% of requests faster than this
- **p99:** 99% of requests faster than this (outliers)
- **Average:** Mean response time
- **Min/Max:** Range of response times

#### 2. **Throughput**
- **Requests per Second (RPS):** System capacity
- **Total Requests:** Volume handled
- **Requests per Endpoint:** Distribution of traffic

#### 3. **Error Rates**
- **Failure Rate:** Percentage of failed requests
- **Error Types:** HTTP 500, timeouts, connection errors
- **Failed Endpoints:** Which endpoints fail under load

#### 4. **Resource Usage** (from monitor_resources.py)
- **CPU Utilization:** Percentage usage over time
- **Memory Usage:** RAM consumption
- **Network I/O:** Bandwidth utilization
- **Disk I/O:** Read/write operations

## 🏃 Running Tests

### Method 1: Predefined Scenarios (Recommended)

```bash
# Run a specific scenario
./test_scenarios.sh baseline
./test_scenarios.sh load
./test_scenarios.sh stress

# Run all scenarios (except endurance)
./test_scenarios.sh all
```

### Method 2: Manual Locust Command

```bash
# Web UI mode (interactive)
locust -f locustfile.py --host=http://localhost:8080

# Then open http://localhost:8089 to configure and start test

# Headless mode (no UI)
locust -f locustfile.py \
    --host=http://localhost:8080 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 300s \
    --headless \
    --html test_results/my_test.html \
    --csv test_results/my_test
```

### Method 3: Resource Monitoring Only

```bash
# Monitor system resources
python monitor_resources.py --interval 1 --duration 300

# Monitor Docker container
python monitor_resources.py --container chess-tournament-app --duration 300
```

### Method 4: Custom Test

```bash
./test_scenarios.sh custom
# Follow prompts to specify users, duration, etc.
```

## 🔍 Analyzing Results

### Automatic Analysis

```bash
# Analyze all test results
python analyze_results.py

# Analyze specific results
python analyze_results.py --results test_results/load_*.json

# Compare two tests
python analyze_results.py --compare test1.json test2.json
```

### Manual Analysis

1. **Open HTML Reports**
   ```bash
   open test_results/*.html
   ```
   - View charts, graphs, and statistics
   - See request distribution
   - Identify slow endpoints

2. **Review CSV Data**
   ```bash
   # Statistics file
   cat test_results/baseline_*_stats.csv

   # Failures file
   cat test_results/baseline_*_failures.csv
   ```

3. **Check Resource Usage**
   ```bash
   cat test_results/resources_*.json | python -m json.tool
   ```

## 📖 Understanding Results

### What Good Performance Looks Like

✅ **Success Criteria:**
- **Failure Rate:** < 1%
- **p95 Response Time:** < 1000ms (1 second)
- **p99 Response Time:** < 3000ms (3 seconds)
- **Throughput:** Meets expected traffic
- **CPU Usage:** < 70% on average
- **Memory Usage:** Stable (no growth over time)

### Warning Signs

⚠️ **Performance Issues:**
- Failure rate > 5%
- p95 > 2000ms
- p99 > 5000ms
- Increasing response times over test duration
- CPU consistently > 80%
- Memory growing continuously (memory leak)

### Common Patterns

**1. Database Bottleneck**
- Symptoms: High response times, low throughput
- Solution: Optimize queries, add indexes, connection pooling

**2. Memory Leak**
- Symptoms: Memory usage grows over time
- Solution: Profile application, fix resource cleanup

**3. CPU Bound**
- Symptoms: CPU at 100%, response times increase with load
- Solution: Optimize code, horizontal scaling

**4. Network Bottleneck**
- Symptoms: High network I/O, timeouts
- Solution: Use CDN, optimize payload size

## 🎯 Creating Presentation Slides

### Slide Structure

#### **Slide 1: Overview**
```
Title: Performance Testing Methodology

Content:
- Tool: Locust (Python-based load testing)
- Approach: Realistic user behavior simulation
- Metrics: Latency, Throughput, Error Rates, Resource Usage
- Test Types: Baseline, Load, Stress, Spike, Endurance
```

#### **Slide 2: Test Scenarios**
```
Title: Test Scenarios Executed

Table:
┌─────────────┬──────────┬─────────┬──────────┐
│ Scenario    │ Duration │ Users   │ Purpose  │
├─────────────┼──────────┼─────────┼──────────┤
│ Baseline    │ 2 min    │ 5       │ Normal   │
│ Load        │ 5 min    │ 50      │ Expected │
│ Stress      │ 7 min    │ 200     │ Peak     │
│ Spike       │ 4 min    │ 5→100→5 │ Recovery │
└─────────────┴──────────┴─────────┴──────────┘
```

#### **Slide 3: Independent & Dependent Variables**
```
Title: Variables Analyzed

Independent Variables (Controlled):
• Request Load (5-200 concurrent users)
• Test Duration (2-30 minutes)
• User Behavior Mix (Player, Coach, Arbiter, Manager)

Dependent Variables (Measured):
• Request Latency (p50, p95, p99)
• Throughput (requests/second)
• Error Rate (% failed requests)
• CPU & Memory Usage
```

#### **Slide 4: Key Results - Throughput**
```
Title: Throughput Analysis

Chart: Bar chart showing RPS for each scenario
Data from: test_results/slide_data.json

Example:
Baseline:   45.2 req/s
Load:      120.5 req/s
Stress:    180.3 req/s (degraded at 200 users)
```

#### **Slide 5: Response Time Distribution**
```
Title: Response Time Percentiles

Chart: Line graph showing p50, p95, p99 across scenarios

Table:
┌──────────┬──────┬──────┬──────┐
│ Scenario │ p50  │ p95  │ p99  │
├──────────┼──────┼──────┼──────┤
│ Baseline │  45ms│  80ms│ 120ms│
│ Load     │  85ms│ 250ms│ 450ms│
│ Stress   │ 420ms│1200ms│2500ms│
└──────────┴──────┴──────┴──────┘
```

#### **Slide 6: Error Analysis**
```
Title: Error Rates Under Load

Chart: Stacked bar chart of success vs failures

Key Findings:
• Baseline: 0% failure rate
• Load: 0.5% failure rate (within acceptable limits)
• Stress: 12% failure rate at 200 users (system limit reached)
```

#### **Slide 7: Resource Utilization**
```
Title: CPU & Memory Usage

Dual-axis chart:
- CPU % (left axis)
- Memory % (right axis)

Observations:
• CPU peaks at 85% during stress test
• Memory stable (no leaks detected)
• System scales well up to 150 concurrent users
```

#### **Slide 8: Bottleneck Identification**
```
Title: Performance Bottlenecks

Slowest Endpoints (from analysis):
1. /admin/stats - avg 450ms (database aggregation)
2. /player/statistics - avg 320ms (complex queries)
3. /coach/dashboard - avg 180ms

Recommendations:
✓ Add Redis caching for /admin/stats
✓ Optimize player statistics queries
✓ Implement query result caching
```

#### **Slide 9: Spike Test Results**
```
Title: System Recovery from Traffic Spike

Timeline graph showing:
- Stage 1: Normal (5 users) - stable performance
- Stage 2: Spike (100 users) - degraded but functional
- Stage 3: Recovery (5 users) - returns to normal

Key Metric: Recovery Time = 15 seconds

Conclusion: System handles spikes gracefully
```

#### **Slide 10: Conclusions & Recommendations**
```
Title: Summary & Next Steps

System Performance:
✓ Handles 150 concurrent users effectively
✓ Low failure rate under normal load
✓ Good response times (p95 < 300ms at 50 users)
⚠ Degrades beyond 150 users

Recommendations:
1. Implement caching (Redis) for read-heavy endpoints
2. Optimize database queries (add indexes)
3. Consider horizontal scaling for >150 users
4. Monitor memory usage in production
5. Set up auto-scaling triggers at 70% CPU
```

### Generating Slide Data

```bash
# Run analysis to generate slide_data.json
python analyze_results.py

# The file test_results/slide_data.json contains:
# - Aggregated metrics
# - Per-test summaries
# - Key performance indicators
# - Ready for visualization
```

### Tips for Effective Slides

1. **Use Visual Charts**
   - Bar charts for comparisons
   - Line graphs for trends
   - Heatmaps for distribution

2. **Highlight Key Numbers**
   - Use large fonts for critical metrics
   - Color code: Green (good), Yellow (warning), Red (issues)

3. **Tell a Story**
   - Start with methodology
   - Show results progressively
   - End with actionable insights

4. **Include Screenshots**
   - Locust web UI during test
   - HTML report graphs
   - Resource monitoring dashboards

## 🛠️ Troubleshooting

### Application Not Responding

```bash
# Check if app is running
curl http://localhost:8080

# Check logs
tail -f ../logs/app.log  # if you have logging
```

### Resource Monitor Fails

```bash
# Install system monitoring tools
pip install psutil

# For Docker monitoring
pip install docker

# Check Docker is running
docker ps
```

### Test Results Not Saved

```bash
# Create results directory
mkdir -p test_results

# Check permissions
chmod 755 test_results
```

### Low Performance in Tests

```bash
# Increase database connection pool
# Restart application with production settings
# Check for other processes consuming resources
```

## 📚 Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://www.guru99.com/performance-testing.html)
- [Understanding Percentiles](https://www.elastic.co/blog/averages-can-dangerous-use-percentile)

## 🤝 Contributing

To add new test scenarios:

1. Edit `locustfile.py` to add new user classes
2. Add scenario to `test_scenarios.sh`
3. Document expected behavior
4. Run and validate

## 📞 Support

If you encounter issues:

1. Check this README
2. Review `test_results/` for error logs
3. Check application logs
4. Verify all dependencies are installed

---

**Happy Testing! 🚀**
