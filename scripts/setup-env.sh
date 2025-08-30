#!/bin/bash

# Environment Setup Script for Real-time Recommendation Engine
# This script prepares the development environment

set -e

echo "🚀 Setting up Real-time Recommendation Engine development environment..."
echo "======================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if running on supported OS
check_os() {
    print_section "Checking Operating System"
    case "$OSTYPE" in
        linux-gnu*) 
            print_status "Running on Linux"
            OS="linux"
            ;;
        darwin*) 
            print_status "Running on macOS"
            OS="macos"
            ;;
        msys*|cygwin*|mingw*) 
            print_status "Running on Windows"
            OS="windows"
            ;;
        *) 
            print_error "Unsupported operating system: $OSTYPE"
            exit 1
            ;;
    esac
}

# Check if required tools are installed
check_requirements() {
    print_section "Checking Required Tools"
    
    local missing_tools=()
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        docker_version=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_status "Docker found: $docker_version"
        
        # Check if Docker daemon is running
        if ! docker info >/dev/null 2>&1; then
            print_error "Docker daemon is not running. Please start Docker."
            exit 1
        fi
    else
        missing_tools+=("docker")
    fi
    
    # Check Docker Compose
    if command -v docker-compose >/dev/null 2>&1; then
        compose_version=$(docker-compose --version | cut -d' ' -f4 | cut -d',' -f1)
        print_status "Docker Compose found: $compose_version"
    elif docker compose version >/dev/null 2>&1; then
        compose_version=$(docker compose version --short)
        print_status "Docker Compose found: $compose_version"
    else
        missing_tools+=("docker-compose")
    fi
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        python_version=$(python3 --version | cut -d' ' -f2)
        print_status "Python found: $python_version"
    elif command -v python >/dev/null 2>&1; then
        python_version=$(python --version | cut -d' ' -f2)
        print_status "Python found: $python_version"
    else
        missing_tools+=("python3")
    fi
    
    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        node_version=$(node --version)
        print_status "Node.js found: $node_version"
    else
        missing_tools+=("node")
    fi
    
    # Check Rust
    if command -v rustc >/dev/null 2>&1; then
        rust_version=$(rustc --version | cut -d' ' -f2)
        print_status "Rust found: $rust_version"
    else
        missing_tools+=("rust")
    fi
    
    # Check .NET
    if command -v dotnet >/dev/null 2>&1; then
        dotnet_version=$(dotnet --version)
        print_status ".NET found: $dotnet_version"
    else
        missing_tools+=("dotnet")
    fi
    
    # Check Make
    if command -v make >/dev/null 2>&1; then
        print_status "Make found"
    else
        print_warning "Make not found. Some convenience commands may not work."
    fi
    
    # Check curl
    if command -v curl >/dev/null 2>&1; then
        print_status "curl found"
    else
        missing_tools+=("curl")
    fi
    
    # Check jq for JSON processing
    if command -v jq >/dev/null 2>&1; then
        print_status "jq found"
    else
        print_warning "jq not found. JSON output may not be formatted nicely."
    fi
    
    # Report missing tools
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_error "Please install the missing tools and run this script again."
        echo ""
        print_section "Installation Instructions"
        for tool in "${missing_tools[@]}"; do
            case $tool in
                docker)
                    echo "Docker: https://docs.docker.com/get-docker/"
                    ;;
                docker-compose)
                    echo "Docker Compose: https://docs.docker.com/compose/install/"
                    ;;
                python3)
                    echo "Python: https://www.python.org/downloads/"
                    ;;
                node)
                    echo "Node.js: https://nodejs.org/"
                    ;;
                rust)
                    echo "Rust: https://rustup.rs/"
                    ;;
                dotnet)
                    echo ".NET: https://dotnet.microsoft.com/download"
                    ;;
                curl)
                    echo "curl: Usually available via package manager (apt, brew, etc.)"
                    ;;
            esac
        done
        exit 1
    fi
    
    print_status "All required tools are installed!"
}

# Setup environment file
setup_env_file() {
    print_section "Setting up Environment Configuration"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env file from .env.example"
        else
            print_error ".env.example file not found!"
            exit 1
        fi
    else
        print_warning ".env file already exists. Skipping..."
    fi
}

# Create necessary directories
create_directories() {
    print_section "Creating Project Directories"
    
    directories=(
        "datasets/generated"
        "datasets/sample"
        "logs"
        "infrastructure/postgres"
        "services/ml-service/app"
        "services/ml-service/tests"
        "services/api-gateway/src"
        "services/api-gateway/tests"
        "services/user-service/Controllers"
        "services/user-service/Models" 
        "services/user-service/Services"
        "services/cache-service/src"
        "services/cache-service/tests"
        "k8s/kafka"
        "k8s/redis"
        "k8s/services"
        "docs/diagrams"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        fi
    done
}

# Setup Git configuration
setup_git() {
    print_section "Setting up Git Configuration"
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_warning "Not in a Git repository. Skipping Git setup..."
        return
    fi
    
    # Set up git hooks directory
    if [ ! -d ".git/hooks" ]; then
        mkdir -p .git/hooks
    fi
    
    # Create pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for Real-time Recommendation Engine

echo "🔍 Running pre-commit checks..."

# Check for secrets in code
if grep -r "password\|secret\|key" --include="*.py" --include="*.js" --include="*.cs" --include="*.rs" --exclude=".env.example" .; then
    echo "⚠️  Potential secrets found in code. Please review."
fi

# Format Python code with black (if available)
if command -v black >/dev/null 2>&1; then
    echo "🔧 Formatting Python code..."
    find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -exec black {} +
fi

echo "✅ Pre-commit checks complete!"
EOF

    chmod +x .git/hooks/pre-commit
    print_status "Git pre-commit hook created"
    
    # Set up git message template
    cat > .gitmessage << 'EOF'
# <type>: <subject>
#
# <body>
#
# <footer>

# Type should be one of the following:
# * feat: A new feature
# * fix: A bug fix
# * docs: Documentation only changes
# * style: Changes that do not affect the meaning of the code
# * refactor: A code change that neither fixes a bug nor adds a feature
# * perf: A code change that improves performance
# * test: Adding missing tests or correcting existing tests
# * chore: Changes to the build process or auxiliary tools
EOF

    git config commit.template .gitmessage
    print_status "Git commit template configured"
}

# Setup Python environment
setup_python() {
    print_section "Setting up Python Environment"
    
    if [ -d "services/ml-service" ]; then
        cd services/ml-service
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            python3 -m venv venv
            print_status "Created Python virtual environment"
        fi
        
        # Create requirements.txt if it doesn't exist
        if [ ! -f "requirements.txt" ]; then
            cat > requirements.txt << 'EOF'
# FastAPI and dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Redis
redis==5.0.1
hiredis==2.2.3

# Kafka
kafka-python==2.0.2

# ML and Data Processing
numpy==1.24.3
pandas==2.1.4
scikit-learn==1.3.2
scipy==1.11.4

# Monitoring and Logging
structlog==23.2.0
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Development
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
EOF
            print_status "Created requirements.txt for ML service"
        fi
        
        cd ../..
    fi
}

# Setup Node.js environment
setup_nodejs() {
    print_section "Setting up Node.js Environment"
    
    if [ -d "services/api-gateway" ]; then
        cd services/api-gateway
        
        # Create package.json if it doesn't exist
        if [ ! -f "package.json" ]; then
            cat > package.json << 'EOF'
{
  "name": "recommendation-api-gateway",
  "version": "1.0.0",
  "description": "API Gateway for Real-time Recommendation Engine",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "lint": "eslint src/",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "redis": "^4.6.11",
    "kafkajs": "^2.2.4",
    "axios": "^1.6.2",
    "winston": "^3.11.0",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "jest": "^29.7.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0",
    "supertest": "^6.3.3"
  }
}
EOF
            print_status "Created package.json for API gateway"
        fi
        
        cd ../..
    fi
}

# Final validation
final_validation() {
    print_section "Final Validation"
    
    # Check if essential files exist
    essential_files=(
        ".env"
        "docker-compose.yml"
        "Makefile"
        "infrastructure/kafka/topics-setup.sh"
    )
    
    for file in "${essential_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "✓ $file exists"
        else
            print_error "✗ $file is missing"
            exit 1
        fi
    done
}

# Main execution
main() {
    check_os
    check_requirements
    setup_env_file
    create_directories
    setup_git
    setup_python
    setup_nodejs
    final_validation
    
    print_section "Setup Complete!"
    echo ""
    echo "🎉 Your development environment is ready!"
    echo ""
    echo "Next steps:"
    echo "1. Review and edit .env file with your configuration"
    echo "2. Start the development environment: make dev-up"
    echo "3. Load sample data: make load-sample-data"
    echo "4. Check service health: make health-check"
    echo ""
    echo "📚 Documentation: docs/"
    echo "🐛 Issues: https://github.com/YOUR_USERNAME/realtime-recommendation-engine/issues"
    echo ""
    print_status "Happy coding! 🚀"
}

# Run main function
main "$@"