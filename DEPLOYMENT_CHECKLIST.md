# 🚀 Voyza Deployment Checklist - voyzacar.online

**Goal:** Deploy Phase 3 to production with free tier services  
**Services:** Vercel (Frontend) + Railway (Backend) + Firebase (Storage) + MongoDB (Optional)

---

## Phase 1: Code & Repository ✅

- [x] Phase 3 code implemented (KYC, Damage Reports, Document Management)
- [x] All files pushed to GitHub
- [x] GitHub URL: https://github.com/siddharthasharma9537/voyza
- [x] Vercel configuration files created (.vercelignore, vercel.json)
- [x] Railway configuration files created (railway.json, .railwayignore)

---

## Phase 2: Frontend Deployment (Vercel)

### Setup
- [ ] Go to https://vercel.com
- [ ] Sign up / Login with GitHub
- [ ] Select organization: **siddharthasharma9537**
- [ ] Click "Add New" → "Project"
- [ ] Import **voyza** repository

### Configuration
- [ ] Root Directory: `./frontend-web`
- [ ] Framework: Next.js (auto-detected)
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `.next`

### Environment Variables (in Vercel Dashboard)
- [ ] `NEXT_PUBLIC_API_URL` = `https://api.voyzacar.online`
- [ ] `NEXT_PUBLIC_DOMAIN` = `voyzacar.online`

### Deployment
- [ ] Click "Deploy"
- [ ] Wait for build to complete (2-3 min)
- [ ] Get temporary Vercel domain (voyza-xxx.vercel.app)
- [ ] Test at temporary domain

### Custom Domain Connection
- [ ] In Vercel: Settings → Domains
- [ ] Add domain: `voyzacar.online`
- [ ] Get Vercel's nameservers (or CNAME)
- [ ] In GoDaddy: Update nameservers to Vercel's
- [ ] Wait for DNS propagation (5-15 min)
- [ ] Test: https://voyzacar.online

### Verification
- [ ] Frontend loads: ✅ https://voyzacar.online
- [ ] Can access KYC page: ✅ https://voyzacar.online/kyc
- [ ] Can access admin: ✅ https://voyzacar.online/admin/kyc

---

## Phase 3: Backend Deployment (Railway)

### Account & Project Setup
- [ ] Go to https://railway.app
- [ ] Click "Start Project"
- [ ] Choose "Deploy from GitHub"
- [ ] Authorize Railway
- [ ] Select organization: **siddharthasharma9537**
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose **voyza** repository
- [ ] Select **backend** as root directory

### Build & Deploy
- [ ] Railway auto-detects Dockerfile
- [ ] Build starts automatically (5-10 min)
- [ ] Monitor build logs
- [ ] Deployment completes

### Database Setup
- [ ] In Railway: Click "+ Add Service"
- [ ] Select "PostgreSQL"
- [ ] Database creates automatically
- [ ] `DATABASE_URL` auto-set in Variables

### Environment Variables (in Railway Dashboard)

**Security Keys:**
- [ ] Generate SECRET_KEY: `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`
- [ ] Add `SECRET_KEY` = [generated key]

**Domain & CORS:**
- [ ] `DOMAIN_NAME` = `voyzacar.online`
- [ ] `FRONTEND_URL` = `https://voyzacar.online`
- [ ] `CORS_ORIGINS` = `https://voyzacar.online,https://www.voyzacar.online`

**API Configuration:**
- [ ] `API_HOST` = `0.0.0.0`
- [ ] `API_PORT` = `8000`
- [ ] `DEBUG` = `false`
- [ ] `ENVIRONMENT` = `production`

**Database:**
- [ ] `DATABASE_URL` = [auto-filled by Railway]

**File Storage (Choose one):**
- [ ] Option A: Firebase (free tier)
  - [ ] `FIREBASE_API_KEY` = [your key]
  - [ ] `FIREBASE_PROJECT_ID` = [your project]
  - [ ] `FIREBASE_STORAGE_BUCKET` = [your bucket]
- [ ] Option B: MinIO (self-hosted)
  - [ ] `AWS_S3_ENDPOINT` = [your endpoint]
  - [ ] `MINIO_ROOT_USER` = `minioadmin`
  - [ ] `MINIO_ROOT_PASSWORD` = [secure password]

### Custom Domain Configuration
- [ ] In Railway: Settings → Domains
- [ ] Click "+ New Domain"
- [ ] Enter: `api.voyzacar.online`
- [ ] Get CNAME record from Railway
- [ ] In GoDaddy DNS: Add CNAME
  - Name: `api`
  - Value: [Railway CNAME]
  - TTL: 3600
- [ ] Save in GoDaddy
- [ ] Wait for DNS propagation (5-15 min)

### Database Migration
- [ ] Wait for backend to start
- [ ] Run migrations:
  ```bash
  cd ~/voyza/backend
  railroad exec alembic upgrade head
  ```
  Or via Railway CLI
- [ ] Verify migration completed

### Verification
- [ ] API health: ✅ https://api.voyzacar.online/health
- [ ] API docs: ✅ https://api.voyzacar.online/docs
- [ ] Can see API endpoints in Swagger UI

---

## Phase 4: Storage Setup (Firebase or MinIO)

### Option A: Firebase (Recommended for Free Tier)

- [ ] Go to https://firebase.google.com
- [ ] Click "Go to console"
- [ ] Create new project
- [ ] Enable Storage
- [ ] Create storage bucket (choose region nearest to users)
- [ ] Get API credentials:
  - [ ] API Key
  - [ ] Project ID
  - [ ] Storage Bucket name
- [ ] Add credentials to Railway Variables
- [ ] Test file upload via API

### Option B: MinIO (Self-Hosted Alternative)

- [ ] Deploy MinIO on separate service or VPS
- [ ] Or use existing MinIO instance
- [ ] Create bucket: `voyza-documents`
- [ ] Generate credentials
- [ ] Add to Railway Variables
- [ ] Test file upload

---

## Phase 5: GoDaddy DNS Configuration

### Update All DNS Records

**Remove old records, add these:**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 3600 |
| CNAME | www | voyzacar.online | 3600 |
| CNAME | api | [Railway CNAME] | 3600 |
| CNAME | minio | [MinIO CNAME if using] | 3600 |

### Verification
```bash
# Test DNS propagation
nslookup voyzacar.online
nslookup api.voyzacar.online
dig voyzacar.online
```

---

## Phase 6: Complete End-to-End Testing

### Frontend Testing
- [ ] Visit https://voyzacar.online
- [ ] Page loads without errors
- [ ] Navigation works
- [ ] Responsive design (test on mobile)

### Authentication Testing
- [ ] User registration works
- [ ] Login works
- [ ] Token stored properly
- [ ] Can access protected routes

### KYC Testing
- [ ] Can navigate to KYC page
- [ ] Can upload documents
- [ ] API receives upload request
- [ ] Admin can see pending documents
- [ ] Admin can verify/reject documents

### File Storage Testing
- [ ] Documents uploaded to storage
- [ ] Can retrieve document via signed URL
- [ ] File integrity verified

### API Testing
```bash
# Test all Phase 3 endpoints
curl -X POST https://api.voyzacar.online/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "phone": "9876543210",
    "password": "TestPass123!",
    "role": "customer"
  }'

# Document upload
curl -X POST https://api.voyzacar.online/api/v1/kyc/documents \
  -H "Authorization: Bearer [TOKEN]" \
  -F "file=@test.pdf" \
  -F "document_type=driving_license" \
  -F "expiry_date=2026-12-31"

# Check status
curl https://api.voyzacar.online/api/v1/kyc/verify-status \
  -H "Authorization: Bearer [TOKEN]"
```

---

## Phase 7: Monitoring & Maintenance

### Logging Setup
- [ ] Vercel: View logs in dashboard
- [ ] Railway: View logs in dashboard
- [ ] Monitor error rates
- [ ] Check performance metrics

### Backup Configuration
- [ ] Railway: Database backups auto-enabled
- [ ] Firebase: Backups configured
- [ ] Test backup restoration

### Security Checklist
- [ ] All credentials changed from defaults
- [ ] .env not committed to Git
- [ ] SSL certificates valid (auto-renewed)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Security headers present

### Scheduled Tasks
- [ ] Backup: Daily at 2 AM
- [ ] Health checks: Every 5 minutes
- [ ] Log rotation: Automatic
- [ ] Updates: Weekly

---

## Deployment Status Summary

| Component | Status | URL |
|-----------|--------|-----|
| Frontend | ⬜ Not Started | https://voyzacar.online |
| Backend | ⬜ Not Started | https://api.voyzacar.online |
| Database | ⬜ Not Started | (Internal) |
| Storage | ⬜ Not Started | Firebase/MinIO |
| DNS | ⬜ Not Started | GoDaddy |
| Monitoring | ⬜ Not Started | Vercel/Railway Dashboards |

---

## Estimated Timeline

- **Phase 2 (Vercel):** 10-15 minutes
- **Phase 3 (Railway):** 15-20 minutes
- **Phase 4 (Firebase):** 10 minutes
- **Phase 5 (DNS):** 15 minutes (+ 5-15 min propagation)
- **Phase 6 (Testing):** 20 minutes
- **Phase 7 (Monitoring):** 10 minutes

**Total:** 1.5-2 hours (mostly waiting for builds and DNS propagation)

---

## Important Notes

⚠️ **BEFORE GOING LIVE:**
- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY
- [ ] Enable HTTPS (auto-done by Vercel/Railway)
- [ ] Test disaster recovery
- [ ] Review security settings
- [ ] Setup monitoring alerts

⚠️ **IN PRODUCTION:**
- [ ] Never expose .env file
- [ ] Keep DEBUG = false
- [ ] Monitor logs regularly
- [ ] Backup database daily
- [ ] Update dependencies monthly
- [ ] Monitor costs (free tier limits)

---

## Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app
- **Firebase Docs:** https://firebase.google.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Next.js Docs:** https://nextjs.org/docs

---

**Last Updated:** 2026-04-26  
**Status:** Ready to Deploy  
**Next Step:** Start Phase 2 (Vercel Frontend Deployment)

🚀 **Let's go live!**
