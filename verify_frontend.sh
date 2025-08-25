#!/bin/bash
# Quick Frontend Verification Script
# This script helps you verify the sliding window analysis frontend

echo "🔍 Frontend Verification Checklist"
echo "=================================="
echo ""

# Check if services are running
echo "1. ✅ Checking Services..."
if curl -s http://localhost:80 > /dev/null; then
    echo "   ✅ Frontend: Running on http://localhost:80"
else
    echo "   ❌ Frontend: Not accessible"
fi

if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ API: Running on http://localhost:8000"
else
    echo "   ❌ API: Not accessible"
fi

echo ""
echo "2. 🎯 Manual Verification Steps:"
echo "   1. Open http://localhost:80 in your browser"
echo "   2. Click 'Stream Monitor' in the sidebar"
echo "   3. Look for 'Analysis Configuration' panel showing:"
echo "      - Window Size: 150 tokens"
echo "      - Analysis Frequency: Every 25 tokens"
echo "      - Efficiency Gain: 25x fewer calls"
echo ""

echo "3. 🧪 Test Safe Content:"
echo "   Copy and paste this message:"
echo "   'I am working on a technical project about machine learning algorithms. The team is developing new approaches for natural language processing. We are focusing on transformer architectures and attention mechanisms.'"
echo ""
echo "   Expected Results:"
echo "   ✅ Message should stream through successfully"
echo "   ✅ Analysis Windows section should show green buttons (W1, W2, W3...)"
echo "   ✅ Click any window button to see analyzed text"
echo ""

echo "4. 🚨 Test Risky Content:"
echo "   Copy and paste this message:"
echo "   'My name is John Smith and my SSN is 123-45-6789. Email: john@test.com'"
echo ""
echo "   Expected Results:"
echo "   ❌ Should be blocked with red error message"
echo "   ❌ Should show risk score > 1.0"
echo ""

echo "5. 🔍 Verify Window Analysis Details:"
echo "   - After testing safe content, click any green window button"
echo "   - Should show detailed analysis panel with:"
echo "     ✅ Position in stream"
echo "     ✅ Pattern and Presidio scores"
echo "     ✅ Exact analyzed text (150-token chunk)"
echo "     ✅ Any triggered rules"
echo ""

echo "6. ✅ Success Indicators:"
echo "   [ ] Configuration panel shows 25x efficiency gain"
echo "   [ ] Safe content passes with green window buttons"
echo "   [ ] Risky content gets blocked with clear message"
echo "   [ ] Window details show exact analyzed text"
echo "   [ ] Real-time streaming works smoothly"
echo ""

echo "🎉 If all checks pass, your sliding window analysis is working perfectly!"
echo "The client requirements are fully met and ready for demo!"
