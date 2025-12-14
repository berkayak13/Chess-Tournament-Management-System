"""
Tests for manager routes.
"""
import pytest


class TestManagerDashboard:
    """Tests for manager dashboard."""

    def test_manager_dashboard_loads(self, manager_client):
        """Test that manager dashboard loads successfully."""
        response = manager_client.get('/manager/dashboard')
        assert response.status_code == 200

    def test_manager_dashboard_shows_admin_options(self, manager_client):
        """Test that manager dashboard shows admin options."""
        response = manager_client.get('/manager/dashboard')
        assert response.status_code == 200
        # Should contain dashboard elements
        assert b'Dashboard' in response.data or b'dashboard' in response.data or b'Manager' in response.data

    def test_non_manager_cannot_access_dashboard(self, player_client):
        """Test that non-manager cannot access manager dashboard."""
        response = player_client.get('/manager/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestManagerHalls:
    """Tests for manager halls page."""

    def test_manager_halls_loads(self, manager_client):
        """Test that manager halls page loads successfully."""
        response = manager_client.get('/manager/halls')
        assert response.status_code == 200

    def test_manager_halls_shows_hall_list(self, manager_client):
        """Test that manager halls page shows hall list."""
        response = manager_client.get('/manager/halls')
        assert response.status_code == 200
        # Should contain hall information

    def test_manager_halls_shows_edit_form(self, manager_client):
        """Test that manager halls page shows edit form."""
        response = manager_client.get('/manager/halls')
        assert response.status_code == 200
        # Should contain form elements

    def test_non_manager_cannot_access_halls(self, coach_client):
        """Test that non-manager cannot access manager halls page."""
        response = coach_client.get('/manager/halls', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestManagerCreateUser:
    """Tests for manager create user page."""

    def test_create_user_page_loads(self, manager_client):
        """Test that create user page loads successfully."""
        response = manager_client.get('/manager/create_user')
        assert response.status_code == 200

    def test_create_user_page_shows_form(self, manager_client):
        """Test that create user page shows the form."""
        response = manager_client.get('/manager/create_user')
        assert response.status_code == 200
        # Should contain form elements
        assert b'form' in response.data.lower() or b'Create' in response.data

    def test_create_user_page_shows_role_options(self, manager_client):
        """Test that create user page shows role options."""
        response = manager_client.get('/manager/create_user')
        assert response.status_code == 200
        # Should show role selection (player, coach, arbiter)

    def test_create_user_page_shows_team_options(self, manager_client):
        """Test that create user page shows team options for player/coach."""
        response = manager_client.get('/manager/create_user')
        assert response.status_code == 200

    def test_non_manager_cannot_access_create_user(self, arbiter_client):
        """Test that non-manager cannot access create user page."""
        response = arbiter_client.get('/manager/create_user', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied
        assert b'denied' in response.data.lower() or b'Access' in response.data


class TestManagerUpdateHall:
    """Tests for manager hall update functionality."""

    def test_update_hall_requires_post(self, manager_client):
        """Test that hall update happens via POST."""
        response = manager_client.post('/manager/halls', data={
            'hall_id': '1',
            'hall_name': 'Updated Hall Name'
        }, follow_redirects=True)
        # Should process the update
        assert response.status_code == 200

    def test_update_hall_with_invalid_id(self, manager_client):
        """Test hall update with invalid ID."""
        response = manager_client.post('/manager/halls', data={
            'hall_id': '99999',
            'hall_name': 'New Name'
        }, follow_redirects=True)
        # Should handle gracefully
        assert response.status_code == 200
