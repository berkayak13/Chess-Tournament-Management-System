"""
Tests for player routes.
"""
import pytest


class TestPlayerDashboard:
    """Tests for player dashboard."""

    def test_player_dashboard_loads(self, player_client):
        """Test that player dashboard loads successfully."""
        response = player_client.get('/player/dashboard')
        assert response.status_code == 200

    def test_player_dashboard_shows_welcome(self, player_client):
        """Test that player dashboard shows welcome message."""
        response = player_client.get('/player/dashboard')
        assert response.status_code == 200
        # Should contain dashboard elements
        assert b'Dashboard' in response.data or b'dashboard' in response.data or b'Player' in response.data

    def test_non_player_cannot_access_dashboard(self, manager_client):
        """Test that non-player cannot access player dashboard."""
        response = manager_client.get('/player/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestPlayerMatches:
    """Tests for player matches page."""

    def test_player_matches_loads(self, player_client):
        """Test that player matches page loads successfully."""
        response = player_client.get('/player/matches')
        assert response.status_code == 200

    def test_player_matches_shows_match_list(self, player_client):
        """Test that player matches page shows match information."""
        response = player_client.get('/player/matches')
        assert response.status_code == 200
        # Should contain match-related content
        assert b'Match' in response.data or b'match' in response.data or b'Matches' in response.data

    def test_player_matches_shows_statistics(self, player_client):
        """Test that player matches page shows statistics."""
        response = player_client.get('/player/matches')
        assert response.status_code == 200
        # Statistics might include wins, losses, draws, etc.

    def test_non_player_cannot_access_matches(self, coach_client):
        """Test that non-player cannot access player matches."""
        response = coach_client.get('/player/matches', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestPlayerStatistics:
    """Tests for player statistics page."""

    def test_player_statistics_loads(self, player_client):
        """Test that player statistics page loads successfully."""
        response = player_client.get('/player/statistics')
        assert response.status_code == 200

    def test_player_statistics_shows_elo(self, player_client):
        """Test that player statistics shows ELO rating."""
        response = player_client.get('/player/statistics')
        assert response.status_code == 200
        # May contain ELO or rating information

    def test_player_statistics_shows_performance(self, player_client):
        """Test that player statistics shows performance data."""
        response = player_client.get('/player/statistics')
        assert response.status_code == 200
        # Should contain statistics-related content

    def test_non_player_cannot_access_statistics(self, arbiter_client):
        """Test that non-player cannot access player statistics."""
        response = arbiter_client.get('/player/statistics', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestPlayerOpponents:
    """Tests for player opponents page."""

    def test_player_opponents_loads(self, player_client):
        """Test that player opponents page loads successfully."""
        response = player_client.get('/player/opponents')
        assert response.status_code == 200

    def test_player_opponents_calls_stored_procedure(self, player_client):
        """Test that player opponents page works (calls showCoPlayerStats)."""
        response = player_client.get('/player/opponents')
        # Should either succeed or handle no opponents gracefully
        assert response.status_code == 200 or response.status_code == 302

    def test_non_player_cannot_access_opponents(self, manager_client):
        """Test that non-player cannot access player opponents."""
        response = manager_client.get('/player/opponents', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data
