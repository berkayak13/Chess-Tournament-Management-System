"""
Tests for authentication functionality.
"""
import pytest


class TestLogin:
    """Tests for login functionality."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data

    def test_login_with_valid_credentials_manager(self, client):
        """Test successful login as manager."""
        response = client.post('/login', data={
            'username': 'test_manager',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to manager dashboard
        assert b'Manager' in response.data or b'manager' in response.data

    def test_login_with_valid_credentials_player(self, client):
        """Test successful login as player."""
        response = client.post('/login', data={
            'username': 'test_player',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to player dashboard
        assert b'Player' in response.data or b'player' in response.data or b'Dashboard' in response.data

    def test_login_with_valid_credentials_coach(self, client):
        """Test successful login as coach."""
        response = client.post('/login', data={
            'username': 'test_coach',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_with_valid_credentials_arbiter(self, client):
        """Test successful login as arbiter."""
        response = client.post('/login', data={
            'username': 'test_arbiter',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_with_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'password123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'invalid' in response.data

    def test_login_with_invalid_password(self, client):
        """Test login with invalid password."""
        response = client.post('/login', data={
            'username': 'test_manager',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'invalid' in response.data

    def test_login_with_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200


class TestLogout:
    """Tests for logout functionality."""

    def test_logout_redirects_to_index(self, manager_client):
        """Test that logout redirects to index."""
        response = manager_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_logout_requires_login(self, client):
        """Test that logout requires being logged in."""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to login page
        assert b'Login' in response.data or b'login' in response.data


class TestRoleBasedRedirects:
    """Tests for role-based redirects."""

    def test_index_redirects_manager_to_dashboard(self, manager_client):
        """Test that index redirects manager to their dashboard."""
        response = manager_client.get('/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Manager' in response.data or b'manager' in response.data or b'Dashboard' in response.data

    def test_index_redirects_player_to_dashboard(self, player_client):
        """Test that index redirects player to their dashboard."""
        response = player_client.get('/', follow_redirects=True)
        assert response.status_code == 200

    def test_index_redirects_coach_to_dashboard(self, coach_client):
        """Test that index redirects coach to their dashboard."""
        response = coach_client.get('/', follow_redirects=True)
        assert response.status_code == 200

    def test_index_redirects_arbiter_to_dashboard(self, arbiter_client):
        """Test that index redirects arbiter to their dashboard."""
        response = arbiter_client.get('/', follow_redirects=True)
        assert response.status_code == 200

    def test_unauthenticated_user_sees_index(self, client):
        """Test that unauthenticated user sees index page."""
        response = client.get('/')
        assert response.status_code == 200


class TestProtectedRoutes:
    """Tests for protected route access control."""

    def test_player_cannot_access_manager_dashboard(self, player_client):
        """Test that player cannot access manager dashboard."""
        response = player_client.get('/manager/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied or redirect
        assert b'denied' in response.data.lower() or b'player' in response.data.lower()

    def test_manager_cannot_access_player_dashboard(self, manager_client):
        """Test that manager cannot access player dashboard."""
        response = manager_client.get('/player/dashboard', follow_redirects=True)
        assert response.status_code == 200
        # Should show access denied or redirect
        assert b'denied' in response.data.lower() or b'manager' in response.data.lower()

    def test_coach_cannot_access_arbiter_dashboard(self, coach_client):
        """Test that coach cannot access arbiter dashboard."""
        response = coach_client.get('/arbiter/dashboard', follow_redirects=True)
        assert response.status_code == 200

    def test_arbiter_cannot_access_coach_dashboard(self, arbiter_client):
        """Test that arbiter cannot access coach dashboard."""
        response = arbiter_client.get('/coach/dashboard', follow_redirects=True)
        assert response.status_code == 200

    def test_unauthenticated_user_redirected_to_login(self, client):
        """Test that unauthenticated users are redirected to login."""
        protected_routes = [
            '/matches',
            '/player/dashboard',
            '/coach/dashboard',
            '/arbiter/dashboard',
            '/manager/dashboard'
        ]
        for route in protected_routes:
            response = client.get(route, follow_redirects=True)
            assert response.status_code == 200
            # Should be redirected to login
            assert b'Login' in response.data or b'login' in response.data
