"""
Tests for superuser authentication exclusivity.
Verifies that the configuration-based password is no longer accepted 
once a custom password hash is stored in the database.
"""

from unittest.mock import MagicMock
import bcrypt
from src.web.auth import is_valid_superuser_password

def test_auth_exclusivity():
    """Verify that hash-based password excludes config-based password."""
    # Setup mock gateway app
    gateway_app = MagicMock()
    
    # Define passwords
    config_pass = "default_config_password"
    custom_pass = "my_custom_secure_password"
    wrong_pass = "completely_wrong"
    
    # 1. Test with ONLY config password present
    gateway_app.web_config = {}
    gateway_app.config.web.admin_password = config_pass
    
    assert is_valid_superuser_password(config_pass, gateway_app) is True
    assert is_valid_superuser_password(wrong_pass, gateway_app) is False
    
    # 2. Test with BOTH config password and custom hash present
    # Create hash for custom password
    salt = bcrypt.gensalt()
    custom_hash = bcrypt.hashpw(custom_pass.encode("utf-8"), salt).decode("utf-8")
    
    gateway_app.web_config = {"admin_password_hash": custom_hash}
    
    # Config password should now be REJECTED (exclusivity)
    assert is_valid_superuser_password(config_pass, gateway_app) is False
    
    # Custom password should be ACCEPTED
    assert is_valid_superuser_password(custom_pass, gateway_app) is True
    
    # Wrong password should still be REJECTED
    assert is_valid_superuser_password(wrong_pass, gateway_app) is False

def test_auth_no_password_configured():
    """Verify behavior when no password sources are available."""
    gateway_app = MagicMock()
    gateway_app.web_config = {}
    gateway_app.config.web.admin_password = None
    
    assert is_valid_superuser_password("any_password", gateway_app) is False
