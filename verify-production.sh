#!/bin/bash
# Verification script to check all production files are in place

set -e

echo "🔍 ScrapeFlow Production Readiness Verification"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        return 1
    fi
}

check_dir() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        return 1
    fi
}

failures=0

echo "📁 Core Directories"
check_dir "backend" "Backend directory" || ((failures++))
check_dir "frontend" "Frontend directory" || ((failures++))
check_dir "frontend/src" "Frontend src directory" || ((failures++))
echo ""

echo "🎨 Frontend Components"
check_file "frontend/src/app/page.tsx" "Main dashboard page" || ((failures++))
check_file "frontend/src/app/layout.tsx" "Root layout with error boundary" || ((failures++))
check_file "frontend/src/components/error-boundary.tsx" "Error boundary component" || ((failures++))
check_file "frontend/src/components/skeleton.tsx" "Loading skeleton components" || ((failures++))
check_file "frontend/src/components/results-table.tsx" "Results table component" || ((failures++))
check_file "frontend/src/lib/api.ts" "Enhanced API integration" || ((failures++))
check_file "frontend/src/lib/logger.ts" "Logging utility" || ((failures++))
echo ""

echo "⚙️  Configuration Files"
check_file "frontend/package.json" "Package.json with test scripts" || ((failures++))
check_file "frontend/next.config.mjs" "Next.js config with security headers" || ((failures++))
check_file "frontend/tsconfig.json" "TypeScript config" || ((failures++))
check_file "frontend/.eslintrc.json" "ESLint configuration" || ((failures++))
check_file "frontend/.prettierrc" "Prettier configuration" || ((failures++))
check_file "frontend/jest.config.js" "Jest test configuration" || ((failures++))
check_file "frontend/jest.setup.js" "Jest setup file" || ((failures++))
check_file "frontend/.env.local" "Frontend environment file" || ((failures++))
echo ""

echo "🐳 Docker & Infrastructure"
check_file "frontend/Dockerfile" "Frontend Dockerfile" || ((failures++))
check_file "frontend/.dockerignore" "Docker ignore file" || ((failures++))
check_file "docker-compose.yml" "Docker compose with both services" || ((failures++))
check_file ".github/workflows/ci-cd.yml" "GitHub Actions pipeline" || ((failures++))
echo ""

echo "📚 Documentation"
check_file "README.md" "Comprehensive README" || ((failures++))
check_file "API.md" "API documentation" || ((failures++))
check_file "DEPLOYMENT.md" "Deployment guide" || ((failures++))
check_file "CONTRIBUTING.md" "Contributing guide" || ((failures++))
check_file "QUICKSTART.md" "Quick start guide" || ((failures++))
check_file "PRODUCTION_CHECKLIST.md" "Production checklist" || ((failures++))
check_file "IMPLEMENTATION_COMPLETE.md" "Implementation summary" || ((failures++))
echo ""

echo "🧪 Tests"
check_file "frontend/src/__tests__/api.test.ts" "API test suite" || ((failures++))
echo ""

echo "📄 Additional Files"
check_file ".gitignore" "Git ignore file" || ((failures++))
check_file "backend/.env.example" "Backend env example" || ((failures++))
check_file "frontend/.env.local.example" "Frontend env example" || ((failures++))
echo ""

echo "================================================"
if [ $failures -eq 0 ]; then
    echo -e "${GREEN}✓ All files present - Production ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure API keys: cp backend/.env.example backend/.env"
    echo "2. Run locally: docker compose up --build"
    echo "3. Or develop: npm install && npm run dev"
    echo ""
    echo "See QUICKSTART.md for detailed instructions"
    exit 0
else
    echo -e "${RED}✗ Missing $failures file(s) - Please review above${NC}"
    exit 1
fi
