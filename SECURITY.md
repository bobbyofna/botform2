# BotForm2 Security Documentation

## Authentication System

### Login Credentials

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`

⚠️ **IMPORTANT**: Change this password in production!

### How to Change Password

1. Generate a new password hash:
```bash
venv/bin/python3 -c "import bcrypt; print(bcrypt.hashpw(b'your_new_password', bcrypt.gensalt()).decode())"
```

2. Update the hash in `src/api/auth_routes.py`:
```python
VALID_CREDENTIALS = {
    'admin': '$2b$12$...'  # Your new hash here
}
```

3. Restart the server:
```bash
sudo make restart
```

## Security Features

### 1. Session-Based Authentication

- **Session Duration**: 1 hour (3600 seconds) - configurable via `SESSION_TIMEOUT` in `.env`
- **Session Storage**: In-memory (use Redis for production)
- **Cookie Settings**: HTTP-only, SameSite=Lax
- **Auto-Extension**: Sessions extend on activity

### 2. Brute Force Protection

- **Max Attempts**: 5 failed login attempts before lockout
- **Lockout Duration**: 5 minutes (300 seconds)
- **Per-Username Tracking**: Each username tracked separately
- **Auto-Reset**: Lockout clears after timeout period

Configuration in `.env`:
```
MAX_LOGIN_ATTEMPTS=5
LOGIN_TIMEOUT=300
```

### 3. Rate Limiting

Implemented using SlowAPI middleware:
- Prevents DoS attacks
- Configurable per-endpoint
- Based on IP address

### 4. Security Headers

All responses include:
- `X-Content-Type-Options: nosniff` - Prevents MIME sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - XSS protection
- `Referrer-Policy: strict-origin-when-cross-origin` - Referrer policy

### 5. Protected Routes

**Public routes** (no authentication required):
- `/health` - Health check
- `/login` - Login page
- `/api/auth/login` - Login endpoint
- `/api/auth/session` - Session check
- `/static/*` - Static files

**Protected routes** (authentication required):
- `/` - Dashboard
- `/bot/{bot_id}` - Bot detail pages
- `/api/bots` - All bot management endpoints
- All other API endpoints

## Network Security

### Port Configuration

- **HTTP Port**: 80 (standard, no port needed in URL)
- **Binding**: 0.0.0.0 (accepts connections from all interfaces)
- **AWS Security Group**: Port 80 allowed (HTTP), Port 443 ready for HTTPS

### HTTPS/SSL (Production Recommendation)

For production, implement HTTPS:

1. **Option 1: Nginx Reverse Proxy**
```bash
# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Configure nginx to proxy to port 80
```

2. **Option 2: AWS Application Load Balancer**
- Create ALB with SSL certificate
- Route HTTPS:443 → EC2:80
- Enable WAF for additional protection

## Access URLs

**Current Public Access:**
- HTTP: `http://52.30.244.75`
- Login: `http://52.30.244.75/login`
- API: `http://52.30.244.75/api/*`

## Security Best Practices

### Immediate Actions Required

1. **Change Default Password**
   ```bash
   # Generate new hash and update auth_routes.py
   venv/bin/python3 -c "import bcrypt; print(bcrypt.hashpw(b'strong_password_here', bcrypt.gensalt()).decode())"
   ```

2. **Update Secret Key**
   Edit `.env`:
   ```
   SECRET_KEY=your-long-random-secret-key-here
   ```
   Generate with:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Enable HTTPS** (for production)
   - Get SSL certificate
   - Configure reverse proxy or ALB
   - Update security headers

### Production Checklist

- [ ] Change default admin password
- [ ] Update SECRET_KEY in .env
- [ ] Set ENV=production in .env
- [ ] Implement HTTPS
- [ ] Move session storage to Redis
- [ ] Move credentials to database
- [ ] Enable VPN requirement (optional)
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules
- [ ] Regular security audits
- [ ] Implement backup strategy

### Optional: VPN Protection

To require VPN access:

1. Edit `.env`:
```
REQUIRE_VPN=true
ALLOWED_VPN_IPS=your.vpn.ip.range/24
```

2. Restart server:
```bash
sudo make restart
```

## Session Management

### Check Active Sessions

Sessions are stored in memory. To view (for debugging):
```python
from src.utils.auth import active_sessions
print(active_sessions)
```

### Clear All Sessions

Restart the server:
```bash
sudo make restart
```

## Monitoring Failed Logins

Failed login attempts are tracked in-memory:
```python
from src.utils.auth import failed_login_attempts
print(failed_login_attempts)
```

## API Authentication

### Login
```bash
curl -X POST http://52.30.244.75/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt
```

### Access Protected Endpoints
```bash
curl -b cookies.txt http://52.30.244.75/api/bots
```

### Logout
```bash
curl -X POST http://52.30.244.75/api/auth/logout \
  -b cookies.txt
```

### Check Session
```bash
curl http://52.30.244.75/api/auth/session -b cookies.txt
```

## Troubleshooting

### Locked Out After Failed Logins

Wait 5 minutes or restart server:
```bash
sudo make restart
```

### Session Expired

Sessions last 1 hour. Simply log in again.

### Can't Access After Login

Check that cookies are being sent:
```bash
curl -v -b cookies.txt http://52.30.244.75/
```

## Security Incident Response

If you suspect a security breach:

1. **Immediate Actions**:
   ```bash
   # Stop the server
   sudo make stop

   # Change all credentials
   # Review logs
   tail -100 server.log

   # Restart with new credentials
   sudo make start
   ```

2. **Review Access Logs**: Check `/var/log/nginx/access.log` (if using nginx)

3. **Update Security**: Patch vulnerabilities, update dependencies

## Compliance Notes

- **Data Storage**: Currently in-memory, consider encryption for production
- **Password Policy**: Enforce strong passwords
- **Audit Logging**: Implement comprehensive logging for production
- **Data Retention**: Define and implement retention policies

## Support

For security issues or questions:
- Review this documentation
- Check server logs: `make logs`
- Update dependencies: `venv/bin/pip install --upgrade -r requirements.txt`
