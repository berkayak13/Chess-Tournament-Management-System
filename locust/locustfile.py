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
"""

from locust import HttpUser, task, between, tag
import random
import logging

# Suppress some logging noise
logging.getLogger("urllib3").setLevel(logging.WARNING)


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
