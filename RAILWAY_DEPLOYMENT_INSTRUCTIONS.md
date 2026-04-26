# Railway Backend Deployment - Complete Setup

## Quick Start (5 minutes)

### Step 1: Go to Railway Dashboard
1. Open https://railway.app
2. Sign in with GitHub (account: siddharthasharma9537)

### Step 2: Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Select **voyza** repository
4. Choose **backend** as root directory
5. Click "Deploy"

Railway will automatically:
- Detect the Dockerfile
- Build the backend application
- Create a PostgreSQL database
- Set `DATABASE_URL` environment variable

### Step 3: Configure Environment Variables

In Railway Dashboard → Variables tab, add:

#### Essential Security Variables
```
SECRET_KEY=<generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'>
DEBUG=false
ENVIRONMENT=production
```

#### Domain & CORS
```
DOMAIN_NAME=voyzacar.online
FRONTEND_URL=https://voyzacar.online
CORS_ORIGINS=https://voyzacar.online,https://www.voyzacar.online
```

#### API Configuration
```
API_HOST=0.0.0.0
SKIP_DATABASE_URL_DEFAULT_POSTGRES=true
```

#### File Storage (Choose ONE)

**Option A: Firebase (Recommended for Free Tier)**
```
FIREBASE_API_KEY=<your Firebase API key>
FIREBASE_PROJECT_ID=<your Firebase project ID>
FIREBASE_STORAGE_BUCKET=<your-bucket.appspot.com>
```

**Option B: MinIO (Self-hosted)**
```
AWS_S3_ENDPOINT=https://minio.yourdomain.com
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=<secure password>
AWS_S3_BUCKET_NAME=voyza-documents
```

#### Payment & SMS (Optional)
```
RAZORPAY_KEY_ID=<test key>
RAZORPAY_KEY_SECRET=<test secret>
TWILIO_ACCOUNT_SID=<Twilio account>
TWILIO_AUTH_TOKEN=<Twilio token>
TWILIO_FROM_NUMBER=+1234567890
```

#### Email Configuration (Optional)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<Gmail app password>
EMAILS_FROM_EMAIL=noreply@voyza.app
```

### Step 4: Connect Custom Domain

1. Go to **Settings** → **Domains** in Railway project
2. Click "+ New Domain"
3. Enter: `api.voyzacar.online`
4. Copy the CNAME record provided

#### Update GoDaddy DNS:
1. Go to https://godaddy.com
2. Navigate to **My Products** → **Domains** → **voyzacar.online**
3. Click **DNS** settings
4. Add CNAME record:
   ```
   Name: api
   Value: <Railway CNAME from step above>
   TTL: 3600
   ```
5. Save and wait 5-15 minutes for propagation

### Step 5: Database Migration

Once the backend is deployed:

#### Option A: Via Railway CLI
```bash
railway login
cd ~/voyza/backend
railway exec alembic upgrade head
```

#### Option B: Via SSH (if available)
```bash
# Find connection details in Railway dashboard
alembic upgrade head
```

#### Option C: Trigger via Application
The application should auto-run migrations on startup if configured.

### Step 6: Verify Deployment

Test your API:

```bash
# Health check
curl https://api.voyzacar.online/health

# API documentation
open https://api.voyzacar.online/docs

# Test user registration
curl -X POST https://api.voyzacar.online/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "phone": "9876543210",
    "password": "TestPass123!",
    "role": "customer"
  }'
```

## Troubleshooting

### Database Connection Error
- **Issue:** Backend crashes with database connection error
- **Solution:** 
  1. Verify PostgreSQL service is running (check Railway dashboard)
  2. Confirm `DATABASE_URL` is set in Variables
  3. Check if migrations need to run

### Build Failures
- Check Railway build logs in dashboard
- Verify Dockerfile is correct
- Ensure all requirements are in `requirements.txt`

### Domain Not Resolving
- Wait 5-15 minutes for DNS propagation
- Clear browser cache and try again
- Verify CNAME record is correctly set in GoDaddy

### API Returns 404
- Verify custom domain is correctly configured in Railway
- Check if backend service is in "Running" state
- Try accessing via the temporary Railway domain first

## Production Checklist

- [ ] `SECRET_KEY` is unique and secure (not the default)
- [ ] `DEBUG` is set to `false`
- [ ] `CORS_ORIGINS` contains only your domain
- [ ] File storage (Firebase or MinIO) is configured
- [ ] Custom domain is set up and DNS propagated
- [ ] Database migrations have run successfully
- [ ] Health endpoint responds at `/health`
- [ ] API documentation is accessible at `/docs`
- [ ] Test user registration works
- [ ] Frontend can connect to backend API

## Cost Management

Railway free tier includes:
- $5/month usage credit
- 100 hours/month runtime
- PostgreSQL database
- Custom domain support

For production use:
- Monitor usage in Railway dashboard
- Set up usage alerts
- Consider upgrading to Hobby tier ($5/month) for more resources

## Support

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- Railway Support: https://railway.app/support
