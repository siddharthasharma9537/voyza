# 🚀 VOYZA LIVE DEPLOYMENT GUIDE

**Domain:** voyzacar.online  
**Status:** Ready for Production  
**Phase:** 3 - KYC Verification & Document Management

---

## 📋 Quick Start (5-10 minutes)

### Option A: Automated Deployment (Recommended)

```bash
# 1. Login to your server
ssh root@your-server-ip

# 2. Clone repository
cd ~ && git clone https://github.com/yourusername/voyza.git && cd voyza

# 3. Configure environment
cp .env.prod .env
nano .env  # Edit with your secure passwords and domain

# 4. Setup SSL (one-time)
sudo certbot certonly --standalone \
  -d voyzacar.online \
  -d www.voyzacar.online \
  -d api.voyzacar.online \
  -d minio.voyzacar.online \
  --email your-email@gmail.com \
  --agree-tos --non-interactive

# 5. Run deployment script
bash deploy.sh

# Done! ✅
```

### Option B: Manual Deployment

See `DEPLOYMENT_GUIDE.md` for detailed step-by-step instructions.

---

## 🔑 Required Passwords (Generate These!)

Before deploying, generate these secure passwords:

```bash
# Database password
openssl rand -base64 16

# MinIO password
openssl rand -base64 16

# Redis password
openssl rand -base64 16

# Secret key for backend
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Add them to `.env` file:

```env
DB_PASSWORD=your_secure_db_password
MINIO_ROOT_PASSWORD=your_secure_minio_password
REDIS_PASSWORD=your_secure_redis_password
SECRET_KEY=your_very_long_secure_secret_key
```

---

## 📊 GoDaddy DNS Setup (voyzacar.online)

### Step 1: Login to GoDaddy
- Visit https://www.godaddy.com
- Login with your account
- Go to "My Products" → "Domain" → "voyzacar.online"

### Step 2: Find Your Server IP
```bash
# On your server
curl ifconfig.me
```

### Step 3: Add DNS Records

**Remove old records, add these:**

| Type  | Name | Value           | TTL  |
|-------|------|-----------------|------|
| A     | @    | YOUR_SERVER_IP  | 3600 |
| A     | www  | YOUR_SERVER_IP  | 3600 |
| A     | api  | YOUR_SERVER_IP  | 3600 |
| A     | minio| YOUR_SERVER_IP  | 3600 |

### Step 4: Verify DNS (After 5-15 minutes)
```bash
nslookup voyzacar.online
# Should show your server IP
```

---

## 📦 Architecture Overview

```
voyzacar.online (Port 80/443 - Nginx)
    ├── Frontend (Port 3000)
    │   └── Next.js React App
    │
    ├── API Backend (Port 8000)
    │   └── FastAPI + PostgreSQL
    │
    ├── MinIO Storage (Port 9000/9001)
    │   └── S3-compatible File Storage
    │
    ├── PostgreSQL (Port 5432 - internal)
    │   └── User, Booking, KYC Data
    │
    └── Redis (Port 6379 - internal)
        └── Cache & Session Storage
```

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] Domain purchased (voyzacar.online) ✅
- [ ] Server created (Ubuntu 20.04+, 4GB+ RAM, 2+ CPU)
- [ ] SSH access to server
- [ ] Generated secure passwords
- [ ] Domain DNS configured
- [ ] Let's Encrypt certificates ready

### During Deployment
- [ ] Clone repository
- [ ] Create .env file with credentials
- [ ] Generate SSL certificates
- [ ] Run deployment script
- [ ] Wait for containers to be healthy
- [ ] Run database migrations

### After Deployment
- [ ] Test frontend: https://voyzacar.online
- [ ] Test API: https://api.voyzacar.online/health
- [ ] Test MinIO: https://minio.voyzacar.online
- [ ] Create MinIO bucket
- [ ] Test KYC document upload
- [ ] Test admin dashboard
- [ ] Setup database backups
- [ ] Monitor logs and health

---

## 🧪 Testing Phase 3 (KYC & Documents)

### Test 1: User Registration

```bash
curl -X POST https://api.voyzacar.online/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "phone": "9876543210",
    "password": "TestPassword123!",
    "role": "customer"
  }'
```

### Test 2: Document Upload

```bash
# 1. Get token from login
# 2. Upload document
curl -X POST https://api.voyzacar.online/api/v1/kyc/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=driving_license" \
  -F "expiry_date=2026-12-31"
```

### Test 3: Check KYC Status

```bash
curl https://api.voyzacar.online/api/v1/kyc/verify-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test 4: Browse Frontend

- Main site: https://voyzacar.online
- KYC page: https://voyzacar.online/kyc
- Admin: https://voyzacar.online/admin/kyc

---

## 📱 Available Endpoints

### Frontend
- **Main:** https://voyzacar.online
- **KYC:** https://voyzacar.online/kyc
- **Admin:** https://voyzacar.online/admin/kyc

### API
- **Base:** https://api.voyzacar.online/api/v1
- **Docs:** https://api.voyzacar.online/docs
- **Health:** https://api.voyzacar.online/health

### Storage
- **MinIO Web:** https://minio.voyzacar.online:9001
- **MinIO S3:** https://minio.voyzacar.online (port 9000)

---

## 🐛 Troubleshooting

### Website Shows "Connection Refused"
```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Check Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx -f
```

### SSL Certificate Error
```bash
# Renew certificate
sudo certbot renew --force-renewal

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Database Connection Failed
```bash
# Check if PostgreSQL is healthy
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Check logs
docker-compose -f docker-compose.prod.yml logs db -f
```

### MinIO Upload Fails
```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# Check logs
docker-compose -f docker-compose.prod.yml logs minio -f
```

---

## 📊 Monitoring & Maintenance

### Daily Checks
```bash
# Service health
docker-compose -f docker-compose.prod.yml ps

# System resource usage
docker stats

# API health
curl https://api.voyzacar.online/health
```

### Weekly Maintenance
```bash
# View logs for errors
docker-compose -f docker-compose.prod.yml logs --since 7d | grep ERROR

# Check disk usage
df -h

# Check backups
ls -la ~/voyza/backups/
```

### Setup Automated Backups
```bash
# Create backup script
cat > ~/voyza/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cd ~/voyza
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U voyza_prod voyza_db \
  | gzip > backups/voyza_db_$DATE.sql.gz
find backups -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x ~/voyza/backup-db.sh

# Schedule daily backup
(crontab -l 2>/dev/null; echo "0 2 * * * ~/voyza/backup-db.sh") | crontab -
```

---

## 🔒 Security Best Practices

1. **Change default credentials**
   - DB user and password
   - MinIO root user and password
   - Redis password
   - Backend SECRET_KEY

2. **Enable firewall**
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw allow 80/tcp  # HTTP
   sudo ufw allow 443/tcp # HTTPS
   sudo ufw enable
   ```

3. **Setup SSL auto-renewal**
   ```bash
   sudo systemctl enable certbot.timer
   sudo systemctl start certbot.timer
   ```

4. **Monitor logs**
   ```bash
   # Check for suspicious activity
   docker-compose -f docker-compose.prod.yml logs api -f | grep -i error
   ```

5. **Regular updates**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Update Docker images
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## 📞 Support Resources

- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Phase 3 Details:** `PHASE3_IMPLEMENTATION.md`
- **API Docs:** https://api.voyzacar.online/docs
- **Docker Docs:** https://docs.docker.com
- **Nginx Docs:** https://nginx.org/en/docs/
- **MinIO Docs:** https://docs.min.io

---

## 🎯 Next Steps After Deployment

### Immediate (Day 1)
1. ✅ Test all Phase 3 features
2. ✅ Verify SSL certificates are working
3. ✅ Setup database backups
4. ✅ Monitor logs for errors

### Short-term (Week 1)
1. Implement photo upload in damage reports
2. Setup email notifications
3. Create admin users
4. Test with real users
5. Collect feedback

### Medium-term (Week 2-4)
1. Phase 4: Reviews & Ratings
2. Payment integration
3. Advanced analytics
4. Performance optimization

### Long-term
1. Machine learning for damage classification
2. Insurance integration
3. Mobile app
4. Expansion to other cities

---

## 🏆 Success Indicators

Your deployment is successful when:

✅ Website loads at https://voyzacar.online  
✅ API responds at https://api.voyzacar.online/health  
✅ Users can register accounts  
✅ Users can upload KYC documents  
✅ Documents are stored in MinIO  
✅ Admin dashboard shows pending documents  
✅ SSL certificates are valid  
✅ Logs show no errors  

---

## 📝 Important Notes

⚠️ **BEFORE GOING LIVE:**
- [ ] Change ALL default passwords
- [ ] Enable firewall
- [ ] Setup SSL auto-renewal
- [ ] Configure database backups
- [ ] Test disaster recovery
- [ ] Review security settings
- [ ] Setup monitoring/alerting

⚠️ **IN PRODUCTION:**
- [ ] Never commit .env to git
- [ ] Never use DEBUG=true
- [ ] Always use HTTPS
- [ ] Monitor logs regularly
- [ ] Update Docker images monthly
- [ ] Backup database daily

---

## 🎉 You're Ready!

Your Voyza platform is now live at:

🌐 **https://voyzacar.online**

🔑 **Admin:** https://voyzacar.online/admin  
📱 **API:** https://api.voyzacar.online  
💾 **Storage:** https://minio.voyzacar.online

---

**Last Updated:** 2026-04-26  
**Phase:** 3 - KYC Verification & Document Management  
**Status:** ✅ Production Ready

For detailed instructions, see `DEPLOYMENT_GUIDE.md`
