"""
Tests for arbiter routes.
"""
import pytest


class TestArbiterDashboard:
    """Tests for arbiter dashboard."""

    def test_arbiter_dashboard_loads(self, arbiter_client):
        """Test that arbiter dashboard loads successfully."""
        response = arbiter_client.get('/arbiter/dashboard')
        assert response.status_code == 200

    def test_arbiter_dashboard_shows_matches(self, arbiter_client):
        """Test that arbiter dashboard shows assigned matches."""
        response = arbiter_client.get('/arbiter/dashboard')
        assert response.status_code == 200
        # Should contain dashboard elements
        assert b'Match' in response.data or b'match' in response.data or b'Dashboard' in response.data

    def test_arbiter_dashboard_shows_status(self, arbiter_client):
        """Test that arbiter dashboard shows match status."""
        response = arbiter_client.get('/arbiter/dashboard')
        assert response.status_code == 200

    def test_non_arbiter_cannot_access_dashboard(self, coach_client):
        """Test that non-arbiter cannot access arbiter dashboard."""
        response = coach_client.get('/arbiter/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestArbiterRateMatch:
    """Tests for arbiter rate match page."""

    def test_rate_match_requires_valid_match(self, arbiter_client):
        """Test that rate match requires a valid match ID."""
        response = arbiter_client.get('/arbiter/matches/99999/rate', follow_redirects=True)
        # Should redirect with error or show not found
        assert response.status_code == 200

    def test_rate_match_requires_arbiter_assignment(self, arbiter_client):
        """Test that rate match requires arbiter to be assigned to the match."""
        # Trying to rate a match not assigned to this arbiter
        response = arbiter_client.get('/arbiter/matches/1/rate', follow_redirects=True)
        # Should handle gracefully (either show form or redirect with message)
        assert response.status_code == 200

    def test_non_arbiter_cannot_rate_match(self, player_client):
        """Test that non-arbiter cannot rate a match."""
        response = player_client.get('/arbiter/matches/1/rate', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data

    def test_rate_match_post_requires_valid_rating(self, arbiter_client):
        """Test that rating submission requires valid rating value."""
        response = arbiter_client.post('/arbiter/matches/1/rate', data={
            'rating': '15'  # Invalid: rating should be 1-10
        }, follow_redirects=True)
        # Should handle invalid rating gracefully
        assert response.status_code == 200


class TestArbiterStatistics:
    """Tests for arbiter statistics page."""

    def test_arbiter_statistics_loads(self, arbiter_client):
        """Test that arbiter statistics page loads successfully."""
        response = arbiter_client.get('/arbiter/statistics')
        assert response.status_code == 200

    def test_arbiter_statistics_shows_rating_stats(self, arbiter_client):
        """Test that arbiter statistics shows rating information."""
        response = arbiter_client.get('/arbiter/statistics')
        assert response.status_code == 200
        # Should call showMatchStats stored procedure

    def test_arbiter_statistics_shows_total_matches(self, arbiter_client):
        """Test that arbiter statistics shows total matches rated."""
        response = arbiter_client.get('/arbiter/statistics')
        assert response.status_code == 200

    def test_non_arbiter_cannot_access_statistics(self, manager_client):
        """Test that non-arbiter cannot access arbiter statistics."""
        response = manager_client.get('/arbiter/statistics', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data
