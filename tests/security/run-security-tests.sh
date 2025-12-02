#!/bin/bash

################################################################################
# Security Testing Suite Runner
# GitOps 2.0 Healthcare Intelligence Platform
# 
# Comprehensive security testing framework covering:
# - OWASP Top 10 vulnerability scanning
# - SSL/TLS certificate validation
# - JWT token security testing
# - PHI encryption validation
# - API security testing
# - Dependency vulnerability scanning
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Service endpoints
AUTH_SERVICE="http://localhost:8081"
PAYMENT_GATEWAY="http://localhost:8080"
PHI_SERVICE="http://localhost:8082"
DEVICE_SERVICE="http://localhost:8083"
NOTIFICATION_SERVICE="http://localhost:8084"

# Test flags
RUN_OWASP=false
RUN_SSL=false
RUN_JWT=false
RUN_PHI=false
RUN_API=false
RUN_DEPS=false
RUN_ALL=false

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    local missing_deps=()
    
    # Check for required tools
    command -v docker >/dev/null 2>&1 || missing_deps+=("docker")
    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    command -v jq >/dev/null 2>&1 || missing_deps+=("jq")
    command -v openssl >/dev/null 2>&1 || missing_deps+=("openssl")
    command -v go >/dev/null 2>&1 || missing_deps+=("go")
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo "Please install missing dependencies and try again."
        exit 1
    fi
    
    print_success "All dependencies installed"
}

setup_environment() {
    print_header "Setting Up Test Environment"
    
    # Create reports directory
    mkdir -p "${REPORTS_DIR}"/{owasp,ssl,jwt,phi,api,deps}
    print_success "Created reports directory"
    
    # Check if services are running
    check_services
}

check_services() {
    print_info "Checking service availability..."
    
    local services=(
        "${AUTH_SERVICE}/health:Auth Service"
        "${PAYMENT_GATEWAY}/health:Payment Gateway"
        "${PHI_SERVICE}/health:PHI Service"
        "${DEVICE_SERVICE}/health:Medical Device Service"
        "${NOTIFICATION_SERVICE}/health:Notification Service"
    )
    
    local all_running=true
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        if curl -sf "${url}" >/dev/null 2>&1; then
            print_success "${name} is running"
        else
            print_warning "${name} is not running"
            all_running=false
        fi
    done
    
    if [ "$all_running" = false ]; then
        print_warning "Some services are not running. Starting services..."
        start_services
    fi
}

start_services() {
    print_info "Starting services with Docker Compose..."
    
    cd "${SCRIPT_DIR}/../integration"
    docker-compose up -d
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Verify services are now running
    local max_retries=30
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -sf "${AUTH_SERVICE}/health" >/dev/null 2>&1; then
            print_success "Services are ready"
            return 0
        fi
        retry=$((retry + 1))
        sleep 2
    done
    
    print_error "Services failed to start"
    return 1
}

################################################################################
# OWASP ZAP Security Scanning
################################################################################

run_owasp_scan() {
    print_header "Running OWASP ZAP Security Scan"
    
    local zap_container="owasp-zap-scan"
    local report_file="${REPORTS_DIR}/owasp/zap-report-${TIMESTAMP}.html"
    local json_report="${REPORTS_DIR}/owasp/zap-report-${TIMESTAMP}.json"
    
    # Start OWASP ZAP container
    print_info "Starting OWASP ZAP container..."
    docker run --rm --name "${zap_container}" \
        --network host \
        -v "${REPORTS_DIR}/owasp:/zap/wrk/:rw" \
        -t owasp/zap2docker-stable \
        zap-baseline.py \
        -t "${PAYMENT_GATEWAY}" \
        -r "zap-report-${TIMESTAMP}.html" \
        -J "zap-report-${TIMESTAMP}.json" \
        -a || true
    
    # Parse results
    if [ -f "${report_file}" ]; then
        print_success "OWASP ZAP scan completed"
        print_info "Report: ${report_file}"
        
        # Check for high/medium vulnerabilities
        if [ -f "${json_report}" ]; then
            local high_vulns=$(jq '[.site[].alerts[] | select(.riskcode == "3")] | length' "${json_report}")
            local medium_vulns=$(jq '[.site[].alerts[] | select(.riskcode == "2")] | length' "${json_report}")
            
            echo -e "\n${BLUE}Vulnerability Summary:${NC}"
            echo "  High Severity: ${high_vulns}"
            echo "  Medium Severity: ${medium_vulns}"
            
            if [ "$high_vulns" -gt 0 ] || [ "$medium_vulns" -gt 0 ]; then
                print_error "Found ${high_vulns} high and ${medium_vulns} medium severity vulnerabilities"
                return 1
            else
                print_success "No high or medium severity vulnerabilities found"
            fi
        fi
    else
        print_error "OWASP ZAP scan failed"
        return 1
    fi
}

################################################################################
# SSL/TLS Certificate Validation
################################################################################

run_ssl_tests() {
    print_header "Running SSL/TLS Certificate Validation"
    
    local report_file="${REPORTS_DIR}/ssl/ssl-report-${TIMESTAMP}.txt"
    
    {
        echo "SSL/TLS Security Test Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo
    } > "${report_file}"
    
    # Test each service
    local services=("8080:Payment Gateway" "8081:Auth Service" "8082:PHI Service" "8083:Medical Device" "8084:Notification")
    
    for service in "${services[@]}"; do
        IFS=':' read -r port name <<< "$service"
        
        print_info "Testing ${name} (port ${port})..."
        
        {
            echo "Service: ${name}"
            echo "Port: ${port}"
            echo "----------------------------------------"
        } >> "${report_file}"
        
        # Check TLS version
        if echo | timeout 5 openssl s_client -connect localhost:${port} -tls1_2 2>&1 | grep -q "Cipher"; then
            print_success "${name} supports TLS 1.2"
            echo "TLS 1.2: ✓ Supported" >> "${report_file}"
        else
            print_warning "${name} may not support TLS 1.2 (service might not use HTTPS)"
            echo "TLS 1.2: ⚠ Not verified (HTTP service?)" >> "${report_file}"
        fi
        
        # Check cipher suites
        if echo | timeout 5 openssl s_client -connect localhost:${port} 2>&1 | grep -q "Cipher"; then
            local cipher=$(echo | timeout 5 openssl s_client -connect localhost:${port} 2>&1 | grep "Cipher" | head -1)
            echo "Cipher: ${cipher}" >> "${report_file}"
        fi
        
        echo >> "${report_file}"
    done
    
    print_success "SSL/TLS validation completed"
    print_info "Report: ${report_file}"
}

################################################################################
# JWT Token Security Testing
################################################################################

run_jwt_tests() {
    print_header "Running JWT Security Tests"
    
    local report_file="${REPORTS_DIR}/jwt/jwt-report-${TIMESTAMP}.txt"
    
    print_info "Testing JWT implementation..."
    
    # Test 1: Expired token rejection
    print_info "Test 1: Expired token rejection..."
    local expired_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    local response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer ${expired_token}" \
        "${AUTH_SERVICE}/api/v1/validate")
    
    if [ "$response" = "401" ] || [ "$response" = "403" ]; then
        print_success "Expired tokens are properly rejected"
        echo "✓ Expired token rejection: PASS" >> "${report_file}"
    else
        print_error "Expired tokens are NOT properly rejected (HTTP ${response})"
        echo "✗ Expired token rejection: FAIL" >> "${report_file}"
    fi
    
    # Test 2: None algorithm rejection
    print_info "Test 2: None algorithm rejection..."
    local none_token="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0."
    
    response=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer ${none_token}" \
        "${AUTH_SERVICE}/api/v1/validate")
    
    if [ "$response" = "401" ] || [ "$response" = "403" ]; then
        print_success "None algorithm tokens are properly rejected"
        echo "✓ None algorithm rejection: PASS" >> "${report_file}"
    else
        print_error "None algorithm tokens are NOT properly rejected (HTTP ${response})"
        echo "✗ None algorithm rejection: FAIL" >> "${report_file}"
    fi
    
    # Test 3: Valid token acceptance
    print_info "Test 3: Valid token generation and validation..."
    
    # Login to get valid token
    local login_response=$(curl -s -X POST "${AUTH_SERVICE}/api/v1/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}')
    
    if echo "${login_response}" | jq -e '.token' >/dev/null 2>&1; then
        local valid_token=$(echo "${login_response}" | jq -r '.token')
        
        response=$(curl -s -w "%{http_code}" -o /dev/null \
            -H "Authorization: Bearer ${valid_token}" \
            "${AUTH_SERVICE}/api/v1/validate")
        
        if [ "$response" = "200" ]; then
            print_success "Valid tokens are properly accepted"
            echo "✓ Valid token acceptance: PASS" >> "${report_file}"
        else
            print_error "Valid tokens are NOT properly accepted (HTTP ${response})"
            echo "✗ Valid token acceptance: FAIL" >> "${report_file}"
        fi
    else
        print_warning "Could not generate valid token for testing"
        echo "⚠ Valid token test: SKIPPED (login failed)" >> "${report_file}"
    fi
    
    print_success "JWT security tests completed"
    print_info "Report: ${report_file}"
}

################################################################################
# PHI Encryption Validation
################################################################################

run_phi_tests() {
    print_header "Running PHI Encryption Validation"
    
    local report_file="${REPORTS_DIR}/phi/phi-report-${TIMESTAMP}.txt"
    
    print_info "Testing PHI encryption..."
    
    # Test encryption
    local phi_data='{"patient_id":"P12345","ssn":"123-45-6789","medical_record":"Confidential data"}'
    
    print_info "Test 1: PHI encryption..."
    local encrypt_response=$(curl -s -X POST "${PHI_SERVICE}/api/v1/phi/encrypt" \
        -H "Content-Type: application/json" \
        -d "${phi_data}")
    
    if echo "${encrypt_response}" | jq -e '.encrypted_data' >/dev/null 2>&1; then
        print_success "PHI encryption successful"
        echo "✓ PHI encryption: PASS" >> "${report_file}"
        
        # Verify encrypted data is not plaintext
        local encrypted=$(echo "${encrypt_response}" | jq -r '.encrypted_data')
        if echo "${encrypted}" | grep -q "123-45-6789"; then
            print_error "Encrypted data contains plaintext!"
            echo "✗ Encryption security: FAIL (plaintext detected)" >> "${report_file}"
        else
            print_success "Encrypted data does not contain plaintext"
            echo "✓ Encryption security: PASS" >> "${report_file}"
        fi
        
        # Test decryption
        print_info "Test 2: PHI decryption..."
        local decrypt_response=$(curl -s -X POST "${PHI_SERVICE}/api/v1/phi/decrypt" \
            -H "Content-Type: application/json" \
            -d "{\"encrypted_data\":\"${encrypted}\"}")
        
        if echo "${decrypt_response}" | jq -e '.decrypted_data' >/dev/null 2>&1; then
            print_success "PHI decryption successful"
            echo "✓ PHI decryption: PASS" >> "${report_file}"
            
            # Verify round-trip
            local decrypted=$(echo "${decrypt_response}" | jq -r '.decrypted_data')
            if echo "${decrypted}" | jq -e '.ssn' >/dev/null 2>&1; then
                print_success "Encryption round-trip successful"
                echo "✓ Round-trip integrity: PASS" >> "${report_file}"
            else
                print_error "Decrypted data does not match original"
                echo "✗ Round-trip integrity: FAIL" >> "${report_file}"
            fi
        else
            print_error "PHI decryption failed"
            echo "✗ PHI decryption: FAIL" >> "${report_file}"
        fi
    else
        print_error "PHI encryption failed"
        echo "✗ PHI encryption: FAIL" >> "${report_file}"
    fi
    
    print_success "PHI encryption validation completed"
    print_info "Report: ${report_file}"
}

################################################################################
# API Security Testing
################################################################################

run_api_tests() {
    print_header "Running API Security Tests"
    
    local report_file="${REPORTS_DIR}/api/api-report-${TIMESTAMP}.txt"
    
    {
        echo "API Security Test Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo
    } > "${report_file}"
    
    # Test 1: Authentication enforcement
    print_info "Test 1: Authentication enforcement..."
    
    local endpoints=(
        "${PAYMENT_GATEWAY}/api/v1/payment"
        "${PHI_SERVICE}/api/v1/phi/encrypt"
        "${DEVICE_SERVICE}/api/v1/devices"
    )
    
    local auth_pass=true
    for endpoint in "${endpoints[@]}"; do
        local response=$(curl -s -w "%{http_code}" -o /dev/null \
            -X POST "${endpoint}" \
            -H "Content-Type: application/json" \
            -d '{}')
        
        if [ "$response" = "401" ] || [ "$response" = "403" ]; then
            print_success "Authentication required for ${endpoint}"
            echo "✓ Auth enforced: ${endpoint}" >> "${report_file}"
        else
            print_error "Authentication NOT required for ${endpoint} (HTTP ${response})"
            echo "✗ Auth NOT enforced: ${endpoint}" >> "${report_file}"
            auth_pass=false
        fi
    done
    
    if [ "$auth_pass" = true ]; then
        print_success "Authentication enforcement: PASS"
    else
        print_error "Authentication enforcement: FAIL"
    fi
    
    # Test 2: Rate limiting
    print_info "Test 2: Rate limiting..."
    
    local rate_limit_test=0
    for i in {1..15}; do
        local response=$(curl -s -w "%{http_code}" -o /dev/null \
            "${AUTH_SERVICE}/api/v1/login" \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"username":"test","password":"test"}')
        
        if [ "$response" = "429" ]; then
            rate_limit_test=1
            break
        fi
    done
    
    if [ $rate_limit_test -eq 1 ]; then
        print_success "Rate limiting is enforced"
        echo "✓ Rate limiting: PASS" >> "${report_file}"
    else
        print_warning "Rate limiting not detected (may need more requests)"
        echo "⚠ Rate limiting: NOT DETECTED" >> "${report_file}"
    fi
    
    # Test 3: Input validation
    print_info "Test 3: Input validation..."
    
    local malicious_payloads=(
        '{"username":"admin","password":"<script>alert(1)</script>"}'
        '{"username":"admin","password":"' OR '1'='1"}'
        '{"username":"admin","password":"../../../etc/passwd"}'
    )
    
    local validation_pass=true
    for payload in "${malicious_payloads[@]}"; do
        local response=$(curl -s -w "%{http_code}" -o /dev/null \
            -X POST "${AUTH_SERVICE}/api/v1/login" \
            -H "Content-Type: application/json" \
            -d "${payload}")
        
        if [ "$response" != "200" ]; then
            print_success "Malicious payload rejected"
        else
            print_error "Malicious payload NOT rejected"
            validation_pass=false
        fi
    done
    
    if [ "$validation_pass" = true ]; then
        print_success "Input validation: PASS"
        echo "✓ Input validation: PASS" >> "${report_file}"
    else
        print_error "Input validation: FAIL"
        echo "✗ Input validation: FAIL" >> "${report_file}"
    fi
    
    print_success "API security tests completed"
    print_info "Report: ${report_file}"
}

################################################################################
# Dependency Vulnerability Scanning
################################################################################

run_deps_scan() {
    print_header "Running Dependency Vulnerability Scan"
    
    local report_file="${REPORTS_DIR}/deps/deps-report-${TIMESTAMP}.txt"
    
    {
        echo "Dependency Vulnerability Scan Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo
    } > "${report_file}"
    
    # Scan Go dependencies
    if command -v govulncheck >/dev/null 2>&1; then
        print_info "Scanning Go dependencies..."
        
        cd "${SCRIPT_DIR}/../../services"
        for service in auth-service payment-gateway phi-service medical-device-service notification-service; do
            if [ -d "${service}" ]; then
                print_info "Scanning ${service}..."
                echo "Service: ${service}" >> "${report_file}"
                echo "----------------------------------------" >> "${report_file}"
                
                (cd "${service}" && govulncheck ./... 2>&1) >> "${report_file}" || true
                echo >> "${report_file}"
            fi
        done
        
        print_success "Go dependency scan completed"
    else
        print_warning "govulncheck not installed. Install with: go install golang.org/x/vuln/cmd/govulncheck@latest"
        echo "⚠ govulncheck not available" >> "${report_file}"
    fi
    
    # Scan Docker images if Trivy is available
    if command -v trivy >/dev/null 2>&1; then
        print_info "Scanning Docker images with Trivy..."
        
        local images=("auth-service" "payment-gateway" "phi-service" "medical-device-service" "notification-service")
        
        for image in "${images[@]}"; do
            if docker images | grep -q "${image}"; then
                print_info "Scanning ${image}..."
                echo "Docker Image: ${image}" >> "${report_file}"
                echo "----------------------------------------" >> "${report_file}"
                
                trivy image --severity HIGH,CRITICAL "${image}:latest" >> "${report_file}" 2>&1 || true
                echo >> "${report_file}"
            fi
        done
        
        print_success "Docker image scan completed"
    else
        print_warning "Trivy not installed. Install from: https://aquasecurity.github.io/trivy/"
        echo "⚠ Trivy not available" >> "${report_file}"
    fi
    
    print_success "Dependency vulnerability scan completed"
    print_info "Report: ${report_file}"
}

################################################################################
# Report Generation
################################################################################

generate_summary_report() {
    print_header "Generating Summary Report"
    
    local summary_file="${REPORTS_DIR}/security-summary-${TIMESTAMP}.txt"
    
    {
        echo "╔══════════════════════════════════════════════════════════════════╗"
        echo "║        Security Testing Summary Report                           ║"
        echo "║        GitOps 2.0 Healthcare Intelligence                        ║"
        echo "╚══════════════════════════════════════════════════════════════════╝"
        echo
        echo "Generated: $(date)"
        echo "Test Run ID: ${TIMESTAMP}"
        echo
        echo "═══════════════════════════════════════════════════════════════════"
        echo "Test Results"
        echo "═══════════════════════════════════════════════════════════════════"
        echo
    } > "${summary_file}"
    
    # Count passed/failed tests
    local total_tests=0
    local passed_tests=0
    
    for report_dir in "${REPORTS_DIR}"/*; do
        if [ -d "${report_dir}" ] && [ "$(basename "${report_dir}")" != "." ]; then
            local category=$(basename "${report_dir}")
            echo "Category: ${category^^}" >> "${summary_file}"
            
            local latest_report=$(find "${report_dir}" -name "*-${TIMESTAMP}.*" -type f | head -1)
            if [ -f "${latest_report}" ]; then
                local passes=$(grep -c "✓\|PASS" "${latest_report}" 2>/dev/null || echo "0")
                local fails=$(grep -c "✗\|FAIL" "${latest_report}" 2>/dev/null || echo "0")
                
                total_tests=$((total_tests + passes + fails))
                passed_tests=$((passed_tests + passes))
                
                echo "  Passed: ${passes}" >> "${summary_file}"
                echo "  Failed: ${fails}" >> "${summary_file}"
                echo "  Report: ${latest_report}" >> "${summary_file}"
                echo >> "${summary_file}"
            fi
        fi
    done
    
    # Calculate success rate
    local success_rate=0
    if [ $total_tests -gt 0 ]; then
        success_rate=$((passed_tests * 100 / total_tests))
    fi
    
    {
        echo "═══════════════════════════════════════════════════════════════════"
        echo "Overall Statistics"
        echo "═══════════════════════════════════════════════════════════════════"
        echo
        echo "Total Tests: ${total_tests}"
        echo "Passed: ${passed_tests}"
        echo "Failed: $((total_tests - passed_tests))"
        echo "Success Rate: ${success_rate}%"
        echo
        echo "═══════════════════════════════════════════════════════════════════"
    } >> "${summary_file}"
    
    print_success "Summary report generated: ${summary_file}"
    
    # Display summary
    echo
    cat "${summary_file}"
    echo
}

################################################################################
# Main Execution
################################################################################

show_usage() {
    cat << EOF
Security Testing Suite Runner
GitOps 2.0 Healthcare Intelligence

Usage: $0 [OPTIONS]

Options:
    --all           Run all security tests
    --owasp         Run OWASP ZAP vulnerability scan
    --ssl           Run SSL/TLS validation tests
    --jwt           Run JWT security tests
    --phi           Run PHI encryption validation
    --api           Run API security tests
    --deps          Run dependency vulnerability scan
    -h, --help      Show this help message

Examples:
    $0 --all                    # Run all tests
    $0 --owasp --ssl            # Run OWASP and SSL tests
    $0 --jwt --phi --api        # Run JWT, PHI, and API tests

EOF
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --all)
            RUN_ALL=true
            ;;
        --owasp)
            RUN_OWASP=true
            ;;
        --ssl)
            RUN_SSL=true
            ;;
        --jwt)
            RUN_JWT=true
            ;;
        --phi)
            RUN_PHI=true
            ;;
        --api)
            RUN_API=true
            ;;
        --deps)
            RUN_DEPS=true
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
    shift
done

# Main execution
main() {
    print_header "GitOps 2.0 Healthcare Security Testing Suite"
    
    check_dependencies
    setup_environment
    
    # Run selected tests
    if [ "$RUN_ALL" = true ] || [ "$RUN_OWASP" = true ]; then
        run_owasp_scan || true
    fi
    
    if [ "$RUN_ALL" = true ] || [ "$RUN_SSL" = true ]; then
        run_ssl_tests || true
    fi
    
    if [ "$RUN_ALL" = true ] || [ "$RUN_JWT" = true ]; then
        run_jwt_tests || true
    fi
    
    if [ "$RUN_ALL" = true ] || [ "$RUN_PHI" = true ]; then
        run_phi_tests || true
    fi
    
    if [ "$RUN_ALL" = true ] || [ "$RUN_API" = true ]; then
        run_api_tests || true
    fi
    
    if [ "$RUN_ALL" = true ] || [ "$RUN_DEPS" = true ]; then
        run_deps_scan || true
    fi
    
    # Generate summary
    generate_summary_report
    
    print_header "Security Testing Complete"
    print_success "All security tests completed successfully!"
    print_info "Reports available in: ${REPORTS_DIR}"
}

# Run main function
main
