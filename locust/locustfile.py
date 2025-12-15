"""
Chess Tournament Management System - Load Tests

This Locust file defines load test scenarios for the application.
Run with: locust -f locustfile.py --host=http://localhost:8080

Test scenarios:
- Player browsing (most common)
- Coach operations (matches, halls)
- Arbiter operations (rating matches)
- Manager operations (user management, stats)
- API endpoint testing

Performance Metrics Collected:
- Request latency (p50, p95, p99)
- Throughput (requests/second)
- Error rates
- Response time distribution
"""

from locust import HttpUser, task, between, tag, events
from locust.runners import MasterRunner, LocalRunner
import random
import logging
import time
import json
import os
from datetime import datetime

# Suppress some logging noise
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Performance metrics storage
performance_metrics = {
    'start_time': None,
    'end_time': None,
    'total_requests': 0,
    'total_failures': 0,
    'response_times': [],
    'requests_per_second': [],
    'errors_by_type': {},
    'endpoint_metrics': {}
}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize metrics collection when test starts."""
    performance_metrics['start_time'] = datetime.now()
    logging.info(f"Performance test started at {performance_metrics['start_time']}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Save metrics when test stops."""
    performance_metrics['end_time'] = datetime.now()

    # Calculate summary statistics
    stats = environment.stats

    # Save detailed metrics to file
    results_dir = 'test_results'
    os.makedirs(results_dir, exist_ok=True)

    timestamp = performance_metrics['start_time'].strftime('%Y%m%d_%H%M%S')
    results_file = f"{results_dir}/performance_results_{timestamp}.json"

    summary = {
        'test_info': {
            'start_time': performance_metrics['start_time'].isoformat(),
            'end_time': performance_metrics['end_time'].isoformat(),
            'duration_seconds': (performance_metrics['end_time'] - performance_metrics['start_time']).total_seconds(),
            'host': environment.host
        },
        'overall_stats': {
            'total_requests': stats.total.num_requests,
            'total_failures': stats.total.num_failures,
            'failure_rate': stats.total.fail_ratio,
            'average_response_time': stats.total.avg_response_time,
            'min_response_time': stats.total.min_response_time,
            'max_response_time': stats.total.max_response_time,
            'median_response_time': stats.total.median_response_time,
            'avg_content_length': stats.total.avg_content_length,
            'requests_per_second': stats.total.total_rps,
            'total_rps': stats.total.current_rps
        },
        'percentiles': {
            'p50': stats.total.get_response_time_percentile(0.5),
            'p75': stats.total.get_response_time_percentile(0.75),
            'p90': stats.total.get_response_time_percentile(0.90),
            'p95': stats.total.get_response_time_percentile(0.95),
            'p99': stats.total.get_response_time_percentile(0.99)
        },
        'endpoint_details': {}
    }

    # Per-endpoint statistics
    for name, endpoint_stats in stats.entries.items():
        summary['endpoint_details'][name] = {
            'num_requests': endpoint_stats.num_requests,
            'num_failures': endpoint_stats.num_failures,
            'avg_response_time': endpoint_stats.avg_response_time,
            'min_response_time': endpoint_stats.min_response_time,
            'max_response_time': endpoint_stats.max_response_time,
            'median_response_time': endpoint_stats.median_response_time,
            'requests_per_second': endpoint_stats.total_rps,
            'failure_rate': endpoint_stats.fail_ratio,
            'percentiles': {
                'p50': endpoint_stats.get_response_time_percentile(0.5),
                'p95': endpoint_stats.get_response_time_percentile(0.95),
                'p99': endpoint_stats.get_response_time_percentile(0.99)
            }
        }

    # Save to file
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2)

    logging.info(f"Performance metrics saved to {results_file}")

    # Print summary to console
    print("\n" + "="*80)
    print("PERFORMANCE TEST SUMMARY")
    print("="*80)
    print(f"Duration: {summary['test_info']['duration_seconds']:.2f} seconds")
    print(f"Total Requests: {summary['overall_stats']['total_requests']}")
    print(f"Total Failures: {summary['overall_stats']['total_failures']}")
    print(f"Failure Rate: {summary['overall_stats']['failure_rate']*100:.2f}%")
    print(f"Requests/Second: {summary['overall_stats']['requests_per_second']:.2f}")
    print(f"\nResponse Times:")
    print(f"  Average: {summary['overall_stats']['average_response_time']:.2f} ms")
    print(f"  Median (p50): {summary['percentiles']['p50']:.2f} ms")
    print(f"  p95: {summary['percentiles']['p95']:.2f} ms")
    print(f"  p99: {summary['percentiles']['p99']:.2f} ms")
    print("="*80 + "\n")


class ChessUser(HttpUser):
    """Base class with common functionality."""

    abstract = True
    wait_time = between(1, 5)

    def login(self, username, password):
        """Perform login and return success status."""
        response = self.client.post("/login", data={
            "username": username,
            "password": password
        }, allow_redirects=False)
        return response.status_code in [200, 302]

    def logout(self):
        """Perform logout."""
        self.client.get("/logout", allow_redirects=False)


class PlayerUser(ChessUser):
    """Simulates player behavior - most common user type."""

    weight = 5  # Most common user type

    # Test credentials (from seed data)
    player_credentials = [
        ("magnus", "1234"),
        ("hikaru", "1234"),
        ("fabiano", "1234"),
        ("ding", "1234"),
        ("anish", "1234"),
    ]

    def on_start(self):
        """Login as a player on user start."""
        creds = random.choice(self.player_credentials)
        self.username = creds[0]
        if not self.login(creds[0], creds[1]):
            logging.warning(f"Failed to login as player {creds[0]}")

    def on_stop(self):
        """Logout on user stop."""
        self.logout()

    @task(5)
    @tag("player", "dashboard")
    def view_dashboard(self):
        """View player dashboard."""
        self.client.get("/player/dashboard", name="/player/dashboard")

    @task(4)
    @tag("player", "matches")
    def view_matches(self):
        """View player matches."""
        self.client.get("/player/matches", name="/player/matches")

    @task(3)
    @tag("player", "statistics")
    def view_statistics(self):
        """View player statistics."""
        self.client.get("/player/statistics", name="/player/statistics")

    @task(2)
    @tag("player", "opponents")
    def view_opponents(self):
        """View player opponents (co-player statistics)."""
        self.client.get("/player/opponents", name="/player/opponents")

    @task(2)
    @tag("common", "matches")
    def view_all_matches(self):
        """View all matches."""
        self.client.get("/matches", name="/matches")


class CoachUser(ChessUser):
    """Simulates coach behavior."""

    weight = 2

    coach_credentials = [
        ("coach_alpha", "1234"),
        ("coach_beta", "1234"),
    ]

    def on_start(self):
        """Login as a coach."""
        creds = random.choice(self.coach_credentials)
        self.username = creds[0]
        if not self.login(creds[0], creds[1]):
            logging.warning(f"Failed to login as coach {creds[0]}")

    def on_stop(self):
        self.logout()

    @task(4)
    @tag("coach", "dashboard")
    def view_dashboard(self):
        """View coach dashboard."""
        self.client.get("/coach/dashboard", name="/coach/dashboard")

    @task(3)
    @tag("coach", "halls")
    def view_halls(self):
        """View halls information."""
        self.client.get("/coach/halls", name="/coach/halls")

    @task(2)
    @tag("coach", "create_match")
    def view_create_match_form(self):
        """View create match form."""
        self.client.get("/coach/create_match", name="/coach/create_match")

    @task(1)
    @tag("api", "tables")
    def get_hall_tables(self):
        """Get tables for a random hall via API."""
        hall_id = random.randint(1, 5)
        self.client.get(f"/api/halls/{hall_id}/tables",
                        name="/api/halls/[id]/tables")


class ArbiterUser(ChessUser):
    """Simulates arbiter behavior."""

    weight = 2

    arbiter_credentials = [
        ("arbiter1", "1234"),
        ("arbiter2", "1234"),
    ]

    def on_start(self):
        """Login as an arbiter."""
        creds = random.choice(self.arbiter_credentials)
        self.username = creds[0]
        if not self.login(creds[0], creds[1]):
            logging.warning(f"Failed to login as arbiter {creds[0]}")

    def on_stop(self):
        self.logout()

    @task(4)
    @tag("arbiter", "dashboard")
    def view_dashboard(self):
        """View arbiter dashboard."""
        self.client.get("/arbiter/dashboard", name="/arbiter/dashboard")

    @task(3)
    @tag("arbiter", "statistics")
    def view_statistics(self):
        """View arbiter statistics."""
        self.client.get("/arbiter/statistics", name="/arbiter/statistics")

    @task(2)
    @tag("common", "matches")
    def view_matches(self):
        """View all matches."""
        self.client.get("/matches", name="/matches")


class ManagerUser(ChessUser):
    """Simulates manager behavior."""

    weight = 1

    manager_credentials = [
        ("admin", "1234"),
    ]

    def on_start(self):
        """Login as a manager."""
        creds = random.choice(self.manager_credentials)
        self.username = creds[0]
        if not self.login(creds[0], creds[1]):
            logging.warning(f"Failed to login as manager {creds[0]}")

    def on_stop(self):
        self.logout()

    @task(4)
    @tag("manager", "dashboard")
    def view_dashboard(self):
        """View manager dashboard."""
        self.client.get("/manager/dashboard", name="/manager/dashboard")

    @task(3)
    @tag("manager", "halls")
    def view_halls(self):
        """View and manage halls."""
        self.client.get("/manager/halls", name="/manager/halls")

    @task(2)
    @tag("manager", "create_user")
    def view_create_user_form(self):
        """View create user form."""
        self.client.get("/manager/create_user", name="/manager/create_user")

    @task(2)
    @tag("manager", "stats")
    def view_admin_stats(self):
        """View admin statistics page."""
        self.client.get("/admin/stats", name="/admin/stats")


class AnonymousUser(ChessUser):
    """Simulates anonymous (not logged in) user behavior."""

    weight = 3

    @task(5)
    @tag("anonymous", "homepage")
    def view_homepage(self):
        """View homepage."""
        self.client.get("/", name="/")

    @task(3)
    @tag("anonymous", "login")
    def view_login_page(self):
        """View login page."""
        self.client.get("/login", name="/login")

    @task(1)
    @tag("anonymous", "login_attempt")
    def attempt_login(self):
        """Attempt to login (simulates user trying to login)."""
        self.client.post("/login", data={
            "username": "test_user",
            "password": "wrong_password"
        }, name="/login [POST]")


class APIUser(ChessUser):
    """Dedicated API testing user."""

    weight = 1

    def on_start(self):
        """Login to access API."""
        if not self.login("coach_alpha", "1234"):
            logging.warning("Failed to login for API testing")

    def on_stop(self):
        self.logout()

    @task(5)
    @tag("api", "tables")
    def get_hall_tables_random(self):
        """Get tables for random halls."""
        hall_id = random.randint(1, 10)
        self.client.get(f"/api/halls/{hall_id}/tables",
                        name="/api/halls/[id]/tables")

    @task(1)
    @tag("api", "tables")
    def get_hall_tables_sequential(self):
        """Get tables for all halls sequentially."""
        for hall_id in range(1, 6):
            self.client.get(f"/api/halls/{hall_id}/tables",
                            name="/api/halls/[id]/tables")


# Custom load test shapes
class StagesShape:
    """
    Custom load test shape with stages.
    Use with: locust -f locustfile.py --host=http://localhost:8080

    Stages:
    1. Ramp up to 10 users over 30 seconds
    2. Stay at 10 users for 1 minute
    3. Ramp up to 50 users over 1 minute
    4. Stay at 50 users for 2 minutes
    5. Ramp down to 10 users over 30 seconds
    6. Stay at 10 users for 1 minute
    7. Stop
    """

    stages = [
        {"duration": 30, "users": 10, "spawn_rate": 1},
        {"duration": 90, "users": 10, "spawn_rate": 1},
        {"duration": 150, "users": 50, "spawn_rate": 2},
        {"duration": 270, "users": 50, "spawn_rate": 2},
        {"duration": 300, "users": 10, "spawn_rate": 2},
        {"duration": 360, "users": 10, "spawn_rate": 1},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None
