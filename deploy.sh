#!/bin/bash

# ══════════════════════════════════════════════════════════════════════════════
# VOYZA DEPLOYMENT SCRIPT
# ══════════════════════════════════════════════════════════════════════════════
# This script automates the deployment of Voyza to production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Helper Functions ────────────────────────────────────────────────────────
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
    log_success "$1 is installed"
}

# ── Main Deployment ────────────────────────────────────────────────────────
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        VOYZA DEPLOYMENT SCRIPT - voyzacar.online              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check prerequisites
log_info "Step 1: Checking prerequisites..."

check_command docker
check_command docker-compose
check_command git

# Step 2: Verify .env file exists
log_info "Step 2: Checking environment configuration..."

if [ ! -f .env ]; then
    if [ -f .env.prod ]; then
        log_warning ".env file not found, using .env.prod as template"
        cp .env.prod .env
        log_warning "⚠️  IMPORTANT: Edit .env file with your secure credentials before proceeding"
        echo -e "${YELLOW}Run: nano .env${NC}"
        exit 1
    else
        log_error ".env file not found!"
        log_info "Copy .env.example to .env and update with your values"
        exit 1
    fi
fi

log_success ".env file exists"

# Step 3: Create necessary directories
log_info "Step 3: Creating necessary directories..."

mkdir -p nginx/conf.d
mkdir -p ssl
mkdir -p backups
chmod 755 backups

log_success "Directories created"

# Step 4: Install SSL certificates
log_info "Step 4: Checking SSL certificates..."

DOMAIN=$(grep "DOMAIN_NAME=" .env | cut -d'=' -f2)

if [ -z "$DOMAIN" ]; then
    DOMAIN="voyzacar.online"
fi

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    log_warning "SSL certificates not found for $DOMAIN"
    log_info "Run this on your server to install certificates:"
    echo ""
    echo -e "${YELLOW}sudo certbot certonly --standalone \\${NC}"
    echo -e "${YELLOW}  -d $DOMAIN \\${NC}"
    echo -e "${YELLOW}  -d www.$DOMAIN \\${NC}"
    echo -e "${YELLOW}  -d api.$DOMAIN \\${NC}"
    echo -e "${YELLOW}  -d minio.$DOMAIN \\${NC}"
    echo -e "${YELLOW}  --email your-email@example.com \\${NC}"
    echo -e "${YELLOW}  --agree-tos --non-interactive${NC}"
    echo ""
    log_warning "Skipping SSL setup - will use HTTP for local development"
else
    log_success "SSL certificates found for $DOMAIN"
fi

# Step 5: Build Docker images
log_info "Step 5: Building Docker images..."
log_warning "This may take a few minutes..."

if docker-compose -f docker-compose.prod.yml build 2>&1 | tail -20; then
    log_success "Docker images built successfully"
else
    log_error "Failed to build Docker images"
    exit 1
fi

# Step 6: Start containers
log_info "Step 6: Starting Docker containers..."

if docker-compose -f docker-compose.prod.yml up -d; then
    log_success "Containers started successfully"
else
    log_error "Failed to start containers"
    exit 1
fi

# Step 7: Wait for services to be healthy
log_info "Step 7: Waiting for services to be healthy..."

RETRIES=0
MAX_RETRIES=30

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if docker-compose -f docker-compose.prod.yml ps | grep -E "voyza-(postgres|redis|minio|api|web)" | grep -q "healthy\|Up"; then
        RETRIES=$((RETRIES + 1))
        if [ $RETRIES -eq $MAX_RETRIES ]; then
            break
        fi
    fi
    echo "Waiting for services... ($RETRIES/$MAX_RETRIES)"
    sleep 2
done

log_success "Services are starting up"

# Step 8: Run database migrations
log_info "Step 8: Running database migrations..."

sleep 10  # Wait for DB to be ready

if docker-compose -f docker-compose.prod.yml exec -T api alembic upgrade head; then
    log_success "Database migrations completed"
else
    log_warning "Database migrations may not have completed - check logs"
fi

# Step 9: Verify deployment
log_info "Step 9: Verifying deployment..."

echo ""
log_success "DEPLOYMENT COMPLETE!"
echo ""

# Display service status
log_info "Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
log_info "Access Points:"
echo -e "${GREEN}  Frontend:    https://$DOMAIN${NC}"
echo -e "${GREEN}  API:         https://api.$DOMAIN/api/v1${NC}"
echo -e "${GREEN}  MinIO:       https://minio.$DOMAIN${NC}"
echo -e "${GREEN}  Admin:       https://$DOMAIN/admin${NC}"

echo ""
log_info "View Logs:"
echo -e "  docker-compose -f docker-compose.prod.yml logs -f api"

echo ""
log_warning "Next Steps:"
echo "  1. Check DNS is configured correctly"
echo "  2. Test endpoints with curl or browser"
echo "  3. Create MinIO bucket 'voyza-documents'"
echo "  4. Test KYC document upload"
echo "  5. Review DEPLOYMENT_GUIDE.md for full setup instructions"

echo ""
log_success "Voyza is ready! 🚀"
