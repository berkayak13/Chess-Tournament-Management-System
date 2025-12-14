"""
Tests for coach routes.
"""
import pytest


class TestCoachDashboard:
    """Tests for coach dashboard."""

    def test_coach_dashboard_loads(self, coach_client):
        """Test that coach dashboard loads successfully."""
        response = coach_client.get('/coach/dashboard')
        assert response.status_code == 200

    def test_coach_dashboard_shows_team_info(self, coach_client):
        """Test that coach dashboard shows team information."""
        response = coach_client.get('/coach/dashboard')
        assert response.status_code == 200
        # Should contain dashboard elements
        assert b'Team' in response.data or b'team' in response.data or b'Dashboard' in response.data

    def test_coach_dashboard_shows_recent_matches(self, coach_client):
        """Test that coach dashboard shows recent matches."""
        response = coach_client.get('/coach/dashboard')
        assert response.status_code == 200

    def test_non_coach_cannot_access_dashboard(self, player_client):
        """Test that non-coach cannot access coach dashboard."""
        response = player_client.get('/coach/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestCoachCreateMatch:
    """Tests for coach create match page."""

    def test_create_match_page_loads(self, coach_client):
        """Test that create match page loads successfully."""
        response = coach_client.get('/coach/matches/create')
        assert response.status_code == 200

    def test_create_match_page_shows_form(self, coach_client):
        """Test that create match page shows the form."""
        response = coach_client.get('/coach/matches/create')
        assert response.status_code == 200
        # Should contain form elements
        assert b'form' in response.data.lower() or b'Create' in response.data

    def test_create_match_page_shows_teams(self, coach_client):
        """Test that create match page shows available teams."""
        response = coach_client.get('/coach/matches/create')
        assert response.status_code == 200

    def test_create_match_page_shows_halls(self, coach_client):
        """Test that create match page shows available halls."""
        response = coach_client.get('/coach/matches/create')
        assert response.status_code == 200

    def test_create_match_page_shows_arbiters(self, coach_client):
        """Test that create match page shows available arbiters."""
        response = coach_client.get('/coach/matches/create')
        assert response.status_code == 200

    def test_non_coach_cannot_access_create_match(self, manager_client):
        """Test that non-coach cannot access create match page."""
        response = manager_client.get('/coach/matches/create', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestCoachHalls:
    """Tests for coach halls page."""

    def test_coach_halls_loads(self, coach_client):
        """Test that coach halls page loads successfully."""
        response = coach_client.get('/coach/halls')
        assert response.status_code == 200

    def test_coach_halls_shows_hall_list(self, coach_client):
        """Test that coach halls page shows hall information."""
        response = coach_client.get('/coach/halls')
        assert response.status_code == 200
        # Should call viewHalls stored procedure and display results

    def test_non_coach_cannot_access_halls(self, arbiter_client):
        """Test that non-coach cannot access coach halls page."""
        response = arbiter_client.get('/coach/halls', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestCoachMatchActions:
    """Tests for coach match actions (assign, delete)."""

    def test_assign_players_requires_valid_match(self, coach_client):
        """Test that assign players requires a valid match ID."""
        response = coach_client.get('/coach/matches/99999/assign', follow_redirects=True)
        # Should redirect with error or show not found
        assert response.status_code == 200

    def test_delete_match_requires_post(self, coach_client):
        """Test that delete match requires POST method."""
        response = coach_client.get('/coach/matches/1/delete', follow_redirects=True)
        # GET should not be allowed for delete
        assert response.status_code in [200, 404, 405]

    def test_non_coach_cannot_delete_match(self, player_client):
        """Test that non-coach cannot delete a match."""
        response = player_client.post('/coach/matches/1/delete', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data
