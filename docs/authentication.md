# Authentication Guide

This guide explains how to use the simplified authentication system in Meshtopo Gateway Service.

## Overview

Meshtopo uses a simple username/password authentication system instead of OAuth. This provides:

-   **Simplicity**: No external OAuth provider setup required
-   **Security**: bcrypt password hashing with salt
-   **Flexibility**: Per-user CalTopo credentials
-   **Control**: Full control over user accounts and permissions

## User Management

### Adding Users

#### Method 1: Using the User Management Script

```bash
python3 scripts/user_manager.py add
```

This interactive script will prompt you for:

-   Username
-   Password
-   Role (admin/user)
-   CalTopo credentials (optional)

#### Method 2: Manual Configuration

1. Generate a password hash:

    ```bash
    python3 src/web_ui/utils/password.py 'your_password'
    ```

2. Add the user to `config/config.yaml`:
    ```yaml
    users:
        - username: "newuser"
          password_hash: "$2b$12$..." # Generated hash
          role: "user"
          caltopo_credentials:
              credential_id: "ABC123DEF456"
              secret_key: "base64_encoded_secret"
              accessible_maps: ["map-id-1", "map-id-2"]
    ```

### User Roles

-   **admin**: Full access to all features, can manage users
-   **user**: Standard access, limited to their assigned CalTopo maps

### Managing Users

Use the user management script for common operations:

```bash
# Interactive mode
python3 scripts/user_manager.py interactive

# List all users
python3 scripts/user_manager.py list

# Change user password
python3 scripts/user_manager.py password

# Remove user
python3 scripts/user_manager.py remove
```

## CalTopo Integration

### Per-User CalTopo Credentials

Each user can have their own CalTopo service account credentials:

```yaml
caltopo_credentials:
    credential_id: "your_caltopo_credential_id"
    secret_key: "your_caltopo_secret_key"
    accessible_maps: ["map-id-1", "map-id-2"] # Optional: restrict access
```

### Setting Up CalTopo Credentials

1. **Create CalTopo Service Account**:

    - Log into CalTopo
    - Go to Account Settings → API Access
    - Create a new service account
    - Note the credential ID and secret key

2. **Add Credentials to User**:

    - Use the user management script
    - Or edit `config/config.yaml` directly

3. **Test Access**:
    - Log into the web UI
    - Go to Maps page
    - Verify you can see your CalTopo maps

## Security Best Practices

### Password Security

-   Use strong passwords (minimum 12 characters)
-   Include uppercase, lowercase, numbers, and symbols
-   Don't reuse passwords from other services
-   Consider using a password manager

### Configuration Security

-   Keep `config/config.yaml` secure and private
-   Don't commit passwords to version control
-   Use file permissions to restrict access:
    ```bash
    chmod 600 config/config.yaml
    ```

### Session Security

-   Sessions expire after 1 hour by default
-   Use HTTPS in production
-   Enable secure cookies in production

## Troubleshooting

### Common Issues

**"Invalid username or password"**

-   Check username spelling
-   Verify password hash is correct
-   Regenerate password hash if needed

**"CalTopo API not authenticated"**

-   Verify credential ID and secret key
-   Check CalTopo service account is active
-   Ensure credentials are properly formatted

**"No maps available"**

-   Check user has CalTopo credentials
-   Verify accessible_maps list
-   Test CalTopo API connection

### Password Hash Issues

If you need to regenerate a password hash:

```bash
python3 src/web_ui/utils/password.py 'new_password'
```

Then update the user's `password_hash` in `config/config.yaml`.

### Configuration Validation

Test your configuration:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from config.config import Config
config = Config.from_file('config/config.yaml')
print(f'Configuration loaded: {len(config.users)} users')
"
```

## API Access

### Authentication Endpoints

-   `POST /auth/login` - User login
-   `POST /auth/logout` - User logout
-   `GET /auth/status` - Check authentication status
-   `GET /auth/user` - Get current user info

### Session Management

Sessions are managed using Flask sessions with:

-   Secure cookies (HTTPS only in production)
-   HTTP-only cookies
-   Configurable timeout
-   Automatic cleanup

## Development

### Testing Authentication

```python
from src.web_ui.utils.password import hash_password, verify_password

# Test password hashing
password = "test_password"
hashed = hash_password(password)
print(f"Hash: {hashed}")

# Test verification
is_valid = verify_password(password, hashed)
print(f"Valid: {is_valid}")
```

### Adding Authentication to Routes

```python
from flask import Blueprint, redirect, url_for
from ..models.user import UserManager

def require_auth():
    """Require user authentication."""
    user_manager = UserManager()
    if not user_manager.is_authenticated():
        return redirect(url_for("auth.login"))
    return None

@bp.route("/protected")
def protected_route():
    auth_check = require_auth()
    if auth_check:
        return auth_check

    # Your protected route logic here
    return "Protected content"
```

## Support

For issues or questions:

1. Check this documentation
2. Review the configuration examples
3. Test with the user management script
4. Check the logs for error messages
5. Create an issue on GitHub with details
