# Railway Backend Deployment Guide

**Platform:** Railway.app  
**Service:** FastAPI Backend  
**Domain:** api.voyzacar.online  
**Database:** PostgreSQL (Railway Plugin)

---

## Step 1: Create Railway Account

1. Go to https://railway.app
2. Click **"Start Project"**
3. Choose **"Deploy from GitHub"**
4. Authorize Railway to access your GitHub account
5. Select organization: **siddharthasharma9537**

---

## Step 2: Create New Project

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find and select **voyza** repository
4. Select **backend** directory as the root
5. Click **"Deploy"**

Railway will automatically detect the Dockerfile and start building.

---

## Step 3: Add PostgreSQL Database

1. In your Railway project, click **"+ Add Service"**
2. Select **"PostgreSQL"**
3. Railway will create a PostgreSQL database
4. The `DATABASE_URL` will be automatically set as an environment variable

---

## Step 4: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

### Essential Variables
```
SECRET_KEY=<generate-new-secret-key>
DOMAIN_NAME=voyzacar.online
FRONTEND_URL=https://voyzacar.online
CORS_ORIGINS=https://voyzacar.online,https://www.voyzacar.online
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
ENVIRONMENT=production
```

### Database (Auto-set by Railway)
```
DATABASE_URL=<automatically provided>
```

### File Storage (Choose one)

**Option A: Firebase (Recommended for Free Tier)**
```
FIREBASE_API_KEY=your_firebase_key
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_bucket.appspot.com
```

**Option B: MinIO (Self-hosted)**
```
AWS_S3_ENDPOINT=https://minio.yourdomain.com
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_password
AWS_S3_BUCKET_NAME=voyza-documents
```

### Generate SECRET_KEY
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

---

## Step 5: Connect Custom Domain

1. In Railway project, go to **Settings** tab
2. Find **Domains** section
3. Click **"+ New Domain"**
4. Enter: `api.voyzacar.online`
5. Railway will provide CNAME record

### Configure in GoDaddy
1. Go to https://godaddy.com
2. Navigate to **My Products** → **Domains** → **voyzacar.online**
3. Click **DNS** settings
4. Add CNAME record:
   - **Name:** api
   - **Value:** [Railway CNAME provided]
   - **TTL:** 3600
5. Save and wait 5-15 minutes for propagation

---

## Step 6: Database Migration

After deployment, run migrations:

```bash
# In your local terminal
cd ~/voyza/backend

# SSH into Railway (or use Railway CLI)
# Find the connection details in Railway dashboard

# Run migrations
alembic upgrade head
```

Or via Railway CLI:
```bash
railway exec alembic upgrade head
```

---

## Step 7: Verify Deployment

Test your API:

```bash
# Health check
curl https://api.voyzacar.online/health

# Should respond with: {"status":"ok"}

# API documentation
# Open: https://api.voyzacar.online/docs
```

---

## Step 8: Monitor & Maintain

### View Logs
1. Go to Railway project dashboard
2. Click **Backend service** → **Logs** tab
3. View real-time logs

### Common Issues & Fixes

**Database Connection Error:**
- Verify DATABASE_URL is set in Variables
- Check PostgreSQL service is running
- Restart backend service

**Port Already in Use:**
- Railway automatically assigns PORT
- Check that API_PORT is set to `$PORT` environment variable

**Domain Not Working:**
- Wait 5-15 minutes for DNS propagation
- Clear browser cache
- Verify CNAME record in GoDaddy

**File Upload Issues:**
- Check Firebase/MinIO credentials
- Verify bucket exists and permissions are set
- Check CORS configuration in storage service

---

## Railway Pricing Notes

**Free Tier Includes:**
- $5/month usage credit
- 100 hours/month runtime
- Enough for testing and low-traffic production
- PostgreSQL database included
- Custom domain support

**To Add More Resources:**
- Upgrade to Hobby tier ($5/month)
- Pay for additional usage as needed

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Deploy frontend to Vercel
3. ✅ Deploy backend to Railway
4. ⬜ Setup database in MongoDB Atlas (or use Railway PostgreSQL)
5. ⬜ Setup Firebase for file storage (or continue with MinIO)
6. ⬜ Connect both services
7. ⬜ Test Phase 3 endpoints
8. ⬜ Configure GoDaddy DNS for all subdomains
9. ⬜ Setup monitoring and backups
10. ⬜ Go live!

---

## Support

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- Contact Railway Support: https://railway.app/support
