# Voyza Deployment Guide: voyzacar.online

**Status:** Phase 3 - KYC & Document Management (Ready for Live Deployment)

This guide walks you through deploying the Voyza platform on your server with the custom domain `voyzacar.online`.

---

## Prerequisites

### Server Requirements
- **OS:** Ubuntu 20.04 LTS or higher
- **RAM:** Minimum 4GB (8GB recommended)
- **CPU:** 2 cores minimum (4 recommended)
- **Disk:** 20GB SSD minimum
- **Docker:** Latest version
- **Docker Compose:** v2.0+

### Domain Setup
- Domain purchased: ✅ voyzacar.online (from GoDaddy)
- SSL certificates: Required (Let's Encrypt)
- DNS configured: Required

---

## Part 1: Server Setup

### Step 1.1: Install Docker & Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker --version

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

### Step 1.2: Clone Project Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/yourusername/voyza.git
cd voyza

# Create necessary directories
mkdir -p nginx/conf.d ssl backups
chmod 755 backups
```

### Step 1.3: Install Certbot for SSL Certificates

```bash
sudo apt install certbot python3-certbot-nginx -y

# Create certificates for your domain (do this BEFORE starting containers)
sudo certbot certonly --standalone \
  -d voyzacar.online \
  -d www.voyzacar.online \
  -d api.voyzacar.online \
  -d minio.voyzacar.online \
  --email your-email@gmail.com \
  --agree-tos \
  --non-interactive

# Verify certificates created
sudo ls -la /etc/letsencrypt/live/voyzacar.online/
```

---

## Part 2: DNS Configuration (GoDaddy)

### Step 2.1: Login to GoDaddy

1. Go to GoDaddy.com and login
2. Navigate to "My Products"
3. Click "Domain" under voyzacar.online

### Step 2.2: Update DNS Records

Create these DNS records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 3600 |
| A | www | YOUR_SERVER_IP | 3600 |
| A | api | YOUR_SERVER_IP | 3600 |
| A | minio | YOUR_SERVER_IP | 3600 |
| CNAME | admin | voyzacar.online | 3600 |

**Where to find YOUR_SERVER_IP:**
```bash
# Get your server's public IP
curl ifconfig.me
```

### Step 2.3: Wait for DNS Propagation

```bash
# Check DNS propagation (wait ~5-15 minutes)
nslookup voyzacar.online
dig voyzacar.online

# Should show your server IP
```

---

## Part 3: Environment Configuration

### Step 3.1: Create Production .env File

```bash
# Copy template
cp .env.prod .env

# Edit with your values
nano .env
```

**Update these values in .env:**

```env
# Database
DB_USER=voyza_prod
DB_PASSWORD=SecurePassword123!@#

# MinIO
MINIO_ROOT_USER=voyza_admin
MINIO_ROOT_PASSWORD=SecurePassword456!@#

# Redis
REDIS_PASSWORD=SecurePassword789!@#

# Backend Secret (Generate new)
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Domain
DOMAIN_NAME=voyzacar.online
CORS_ORIGINS=https://voyzacar.online,https://www.voyzacar.online,https://api.voyzacar.online

# Email (optional - for notifications)
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### Step 3.2: Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 << 'EOF'
import secrets
print("SECRET_KEY=" + secrets.token_urlsafe(32))
EOF

# Generate database password
python3 << 'EOF'
import secrets
print("DB_PASSWORD=" + secrets.token_urlsafe(16))
EOF
```

---

## Part 4: Start Services

### Step 4.1: Start Containers in Production Mode

```bash
# Navigate to project directory
cd ~/voyza

# Build images (first time only)
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 4.2: Verify All Services Are Running

```bash
# Check if all containers are healthy
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                      STATUS
# voyza-postgres-prod       Up (healthy)
# voyza-minio-prod          Up (healthy)
# voyza-redis-prod          Up (healthy)
# voyza-api-prod            Up (healthy)
# voyza-web-prod            Up (healthy)
# voyza-nginx-prod          Up
```

### Step 4.3: Verify Website is Live

```bash
# Test frontend
curl https://voyzacar.online
# Should return HTML

# Test API
curl https://api.voyzacar.online/health
# Should return {"status":"ok"}

# Test MinIO (should be accessible)
curl https://minio.voyzacar.online
# Should return MinIO response
```

---

## Part 5: Create MinIO Bucket

### Step 5.1: Access MinIO Console

1. Open browser: https://minio.voyzacar.online:9001
2. Login with credentials from .env:
   - Username: MINIO_ROOT_USER
   - Password: MINIO_ROOT_PASSWORD

### Step 5.2: Create Document Bucket

1. Click "+ Create bucket"
2. Name: `voyza-documents`
3. Click "Create bucket"
4. Set bucket versioning:
   - Select bucket
   - Go to "Settings"
   - Enable "Versioning"

### Step 5.3: Set Bucket Policy

1. Select bucket `voyza-documents`
2. Go to "Admin" → "Users"
3. Create IAM user:
   - Access Key: Same as MINIO_ROOT_USER
   - Secret Key: Same as MINIO_ROOT_PASSWORD

---

## Part 6: Database Setup

### Step 6.1: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Check migration status
docker-compose -f docker-compose.prod.yml exec api alembic current
```

### Step 6.2: Verify Database Connection

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec db psql -U voyza_prod -d voyza_db

# List tables
\dt

# Exit
\q
```

---

## Part 7: Testing Phase 3 (KYC & Documents)

### Step 7.1: Register Test Users

```bash
# Test user registration (customer)
curl -X POST https://api.voyzacar.online/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Customer",
    "phone": "9876543210",
    "password": "TestPass123!",
    "role": "customer"
  }'

# Test user registration (owner)
curl -X POST https://api.voyzacar.online/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test Owner",
    "phone": "9876543211",
    "password": "TestPass123!",
    "role": "owner"
  }'
```

### Step 7.2: Test KYC Document Upload

```bash
# Get auth token first (see login endpoint)

# Upload document
curl -X POST https://api.voyzacar.online/api/v1/kyc/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your-image.jpg" \
  -F "document_type=driving_license" \
  -F "expiry_date=2026-12-31"

# Check KYC status
curl https://api.voyzacar.online/api/v1/kyc/verify-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 7.3: Test Frontend

```bash
# Open in browser
https://voyzacar.online

# Test KYC page
https://voyzacar.online/kyc

# Test admin dashboard
https://voyzacar.online/admin/kyc
```

---

## Part 8: SSL & Security

### Step 8.1: Set Up Auto-Renewal for SSL

```bash
# Create renewal script
sudo tee /etc/cron.d/certbot-renewal > /dev/null << EOF
0 3 * * * root certbot renew --quiet && docker-compose -f ~/voyza/docker-compose.prod.yml restart nginx
EOF

# Verify cron job
sudo crontab -l
```

### Step 8.2: Enable Firewall

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 8.3: Set Up Fail2Ban (Optional but Recommended)

```bash
# Install
sudo apt install fail2ban -y

# Create local config
sudo tee /etc/fail2ban/jail.local > /dev/null << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[recidive]
enabled = true
EOF

# Start service
sudo systemctl restart fail2ban
sudo systemctl status fail2ban
```

---

## Part 9: Monitoring & Maintenance

### Step 9.1: Set Up Log Rotation

```bash
# Docker logs are automatically managed
# Check current usage
docker system df

# Clean up old images/containers (if needed)
docker system prune -a --volumes
```

### Step 9.2: Set Up Database Backups

```bash
# Create backup script
mkdir -p ~/voyza/backups

cat > ~/voyza/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f ~/voyza/docker-compose.prod.yml exec -T db pg_dump -U voyza_prod voyza_db \
  | gzip > ~/voyza/backups/voyza_db_$DATE.sql.gz

# Keep only last 30 days
find ~/voyza/backups -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: voyza_db_$DATE.sql.gz"
EOF

chmod +x ~/voyza/backup-db.sh

# Schedule daily backup at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * ~/voyza/backup-db.sh") | crontab -
```

### Step 9.3: Monitor Services

```bash
# Check container health
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs api -f

# Resource usage
docker stats

# API health check
curl https://api.voyzacar.online/health
```

---

## Part 10: Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Rebuild containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U voyza_prod -d voyza_db -c "\l"
```

### SSL Certificate Issues

```bash
# Check certificate validity
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### MinIO/S3 Connection Error

```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# Verify credentials in .env
grep MINIO .env

# Check MinIO logs
docker-compose -f docker-compose.prod.yml logs minio
```

---

## Part 11: Post-Deployment Checklist

- [ ] Domain points to server IP
- [ ] SSL certificates installed and auto-renewing
- [ ] All containers running and healthy
- [ ] Frontend accessible at https://voyzacar.online
- [ ] API accessible at https://api.voyzacar.online
- [ ] MinIO accessible at https://minio.voyzacar.online
- [ ] Database backups configured
- [ ] Firewall enabled
- [ ] KYC documents can be uploaded and stored in MinIO
- [ ] Admin dashboard accessible
- [ ] Logs being monitored

---

## Part 12: Next Steps & Future Enhancements

### Phase 3 Completion
- ✅ KYC Document Management
- ✅ Damage Reporting
- ✅ MinIO S3-compatible Storage
- ✅ Production Nginx Setup

### Phase 4 (Reviews & Ratings)
- [ ] Rating system implementation
- [ ] Review moderation
- [ ] Reputation tracking

### Optional Enhancements
- [ ] Email notifications
- [ ] SMS notifications (Twilio)
- [ ] Payment integration (Razorpay)
- [ ] Analytics dashboard
- [ ] Automated ML for damage classification

---

## Support & Documentation

- **Project Documentation:** `/docs`
- **Phase 3 Details:** `PHASE3_IMPLEMENTATION.md`
- **API Documentation:** `https://api.voyzacar.online/docs`
- **MinIO Documentation:** https://docs.min.io

---

## Important Security Notes

1. **Change default credentials** in .env before deploying
2. **Use strong passwords** (at least 16 characters, mixed case, numbers, symbols)
3. **Never commit .env to Git** - use .env.example instead
4. **Regularly update Docker images** for security patches
5. **Monitor logs** for suspicious activity
6. **Set up backups** and test restore process regularly
7. **Use HTTPS everywhere** - HTTP redirects automatically
8. **Enable rate limiting** - Nginx config includes DDoS protection

---

## Success! 🎉

Your Voyza platform is now live at:
- **Website:** https://voyzacar.online
- **API:** https://api.voyzacar.online
- **MinIO:** https://minio.voyzacar.online
- **Admin:** https://voyzacar.online/admin

Next steps:
1. Test all Phase 3 features
2. Collect user feedback
3. Plan Phase 4 (Reviews & Ratings)
4. Monitor performance and logs

---

*Last Updated: 2026-04-26*  
*Deployment Guide for voyzacar.online*
