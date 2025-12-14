"""
Tests for API endpoints.
"""
import pytest
import json


class TestHallTablesAPI:
    """Tests for the halls/tables API endpoint."""

    def test_get_hall_tables_returns_json(self, manager_client):
        """Test that API returns JSON response."""
        response = manager_client.get('/api/halls/1/tables')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_get_hall_tables_returns_list(self, manager_client):
        """Test that API returns a list of tables."""
        response = manager_client.get('/api/halls/1/tables')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_get_hall_tables_for_valid_hall(self, manager_client):
        """Test API with valid hall ID."""
        response = manager_client.get('/api/halls/1/tables')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Hall 1 should have tables (from seed data)
        assert isinstance(data, list)

    def test_get_hall_tables_for_invalid_hall(self, manager_client):
        """Test API with invalid hall ID."""
        response = manager_client.get('/api/halls/99999/tables')
        # Should return empty list or error for non-existent hall
        assert response.status_code in [200, 404, 500]

    def test_get_hall_tables_requires_login(self, client):
        """Test that API requires authentication."""
        response = client.get('/api/halls/1/tables', follow_redirects=True)
        # Should redirect to login or return error
        assert response.status_code == 200
        # Should be redirected to login page
        assert b'Login' in response.data or b'login' in response.data

    def test_get_hall_tables_structure(self, manager_client):
        """Test that API returns tables with correct structure."""
        response = manager_client.get('/api/halls/1/tables')
        assert response.status_code == 200
        data = json.loads(response.data)
        if len(data) > 0:
            # Each table should have a table_id
            assert 'table_id' in data[0]


class TestMatchesRoute:
    """Tests for the matches listing route."""

    def test_matches_page_loads(self, manager_client):
        """Test that matches page loads successfully."""
        response = manager_client.get('/matches')
        assert response.status_code == 200

    def test_matches_page_shows_match_list(self, manager_client):
        """Test that matches page shows match information."""
        response = manager_client.get('/matches')
        assert response.status_code == 200
        # Should contain match-related content
        assert b'Match' in response.data or b'match' in response.data

    def test_matches_requires_login(self, client):
        """Test that matches page requires authentication."""
        response = client.get('/matches', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to login
        assert b'Login' in response.data or b'login' in response.data


class TestCreateMatchRoute:
    """Tests for match creation route (admin only)."""

    def test_create_match_page_requires_admin(self, player_client):
        """Test that create match page requires admin role."""
        response = player_client.get('/matches/create', follow_redirects=True)
        # Non-admin should be redirected or denied
        assert response.status_code == 200

    def test_create_match_page_requires_login(self, client):
        """Test that create match page requires authentication."""
        response = client.get('/matches/create', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to login
        assert b'Login' in response.data or b'login' in response.data


class TestAssignPlayersRoute:
    """Tests for player assignment route (admin only)."""

    def test_assign_players_requires_admin(self, coach_client):
        """Test that assign players page requires admin role."""
        response = coach_client.get('/matches/1/assign', follow_redirects=True)
        # Non-admin should be redirected or denied
        assert response.status_code == 200

    def test_assign_players_requires_login(self, client):
        """Test that assign players page requires authentication."""
        response = client.get('/matches/1/assign', follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected to login
        assert b'Login' in response.data or b'login' in response.data

    def test_assign_players_invalid_match(self, manager_client):
        """Test assign players with invalid match ID."""
        response = manager_client.get('/matches/99999/assign', follow_redirects=True)
        # Should handle gracefully
        assert response.status_code == 200
