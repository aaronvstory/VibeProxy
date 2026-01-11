#!/bin/bash

# VibeProxy Status Check Script for macOS
# Save to: ~/vibeproxy-status.sh
# Usage: ./vibeproxy-status.sh

echo "╔════════════════════════════════════════════════════════╗"
echo "║        VibeProxy Status Check (macOS)                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TOTAL_TESTS=5

# Test 1: Check if VibeProxy app is running
echo "Test 1/5: Checking if VibeProxy app is running..."
if pgrep -x "VibeProxy" > /dev/null; then
    echo -e "${GREEN}✅ PASS: VibeProxy app is running${NC}"
    PID=$(pgrep -x "VibeProxy")
    echo "   Process ID: $PID"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: VibeProxy app is NOT running${NC}"
    echo -e "${YELLOW}   → Launch: /Applications/VibeProxy.app${NC}"
fi
echo ""

# Test 2: Check if port 8317 is listening
echo "Test 2/5: Checking if port 8317 is listening..."
if lsof -Pi :8317 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS: Port 8317 is listening${NC}"
    echo "   Process:"
    lsof -i :8317 | grep LISTEN | awk '{print "   " $1 " (PID: " $2 ")"}'
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: Port 8317 is NOT listening${NC}"
    echo -e "${YELLOW}   → Check VibeProxy menu bar → Settings → Server should be 'Running'${NC}"
fi
echo ""

# Test 3: Test health endpoint
echo "Test 3/5: Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8317/health 2>/dev/null)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
    echo -e "${GREEN}✅ PASS: Health endpoint responding${NC}"
    echo "   Status: $HTTP_CODE"
    [ -n "$BODY" ] && echo "   Response: $BODY"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  WARNING: Health endpoint returned: $HTTP_CODE${NC}"
    echo "   (This may be normal - not all proxies have /health)"
fi
echo ""

# Test 4: Check SSH Remote Login status
echo "Test 4/5: Checking SSH Remote Login status..."
SSH_STATUS=$(systemsetup -getremotelogin 2>/dev/null | grep -i "on")
if [ -n "$SSH_STATUS" ]; then
    echo -e "${GREEN}✅ PASS: SSH Remote Login is enabled${NC}"
    echo "   Status: $SSH_STATUS"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: SSH Remote Login is disabled${NC}"
    echo -e "${YELLOW}   → Enable: System Settings → Sharing → Remote Login${NC}"
    echo -e "${YELLOW}   → Or run: sudo systemsetup -setremotelogin on${NC}"
fi
echo ""

# Test 5: Show network information
echo "Test 5/5: Network information..."
EN0_IP=$(ipconfig getifaddr en0 2>/dev/null)
EN1_IP=$(ipconfig getifaddr en1 2>/dev/null)

if [ -n "$EN0_IP" ] || [ -n "$EN1_IP" ]; then
    echo -e "${GREEN}✅ PASS: Network interface found${NC}"
    [ -n "$EN0_IP" ] && echo "   en0 (Ethernet/Wi-Fi): $EN0_IP"
    [ -n "$EN1_IP" ] && echo "   en1 (Alternate): $EN1_IP"
    echo ""
    echo "   Use this IP for SSH from Windows:"
    [ -n "$EN0_IP" ] && echo -e "${GREEN}   ssh $(whoami)@$EN0_IP${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL: No network IP found${NC}"
    echo -e "${YELLOW}   → Check network connection${NC}"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════"
echo "Results: $TESTS_PASSED/$TOTAL_TESTS tests passed"
echo "═══════════════════════════════════════════════════════"
echo ""

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 SUCCESS! VibeProxy is ready for Windows connections!${NC}"
    echo ""
    echo "On Windows, run:"
    [ -n "$EN0_IP" ] && echo -e "  ${GREEN}ssh -L 8317:localhost:8317 $(whoami)@$EN0_IP -N${NC}"
    exit 0
elif [ $TESTS_PASSED -gt 0 ]; then
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS - Some tests failed${NC}"
    echo "   Review errors above and fix issues"
    exit 1
else
    echo -e "${RED}❌ FAILURE - All tests failed${NC}"
    echo ""
    echo "Quick fixes:"
    echo "  1. Launch VibeProxy: open /Applications/VibeProxy.app"
    echo "  2. Enable SSH: sudo systemsetup -setremotelogin on"
    echo "  3. Check network: ipconfig getifaddr en0"
    exit 2
fi
