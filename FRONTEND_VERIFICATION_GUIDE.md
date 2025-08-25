# 🔍 Frontend Verification Guide - Sliding Window Analysis

## 🎯 How to Verify Everything Works as the Client Expects

### Step 1: Open the Web Interface
1. Open your browser and go to: **http://localhost:80**
2. You should see the "Compliance Dashboard" with a modern interface
3. Click on **"Stream Monitor"** in the sidebar

### Step 2: Verify the Analysis Configuration Panel

**What to Look For:**
- Analysis Configuration card should show:
  - **Window Size**: 150 tokens
  - **Analysis Frequency**: Every 25 tokens  
  - **Risk Threshold**: 1.0
  - **Efficiency Gain**: 25x fewer calls

**Client Question Answered:** *"What parameters are being used for analysis?"*

### Step 3: Test Safe Content (Should Pass)

**Test Message:**
```
I am working on a technical project about machine learning algorithms. The team is developing new approaches for natural language processing. We are focusing on transformer architectures and attention mechanisms. This research could help improve AI systems for various applications. Our goal is to create more efficient and accurate models that can understand context better and provide more helpful responses to users.
```

**What Should Happen:**
1. Enter the message in the text area
2. Click "Send Message"
3. **Watch for window analysis events:**
   - You should see "Analysis Windows" section populate with buttons
   - Each button shows "W1: 0.00", "W2: 0.00", etc. (green buttons = safe)
   - Should see 15-20 windows analyzed
4. **Message should stream through successfully**

**Client Questions Answered:**
- ✅ *"What set of tokens is being analyzed?"* → Click any window button to see exact text
- ✅ *"How was the decision made?"* → Each window shows pattern/Presidio scores
- ✅ *"Was it passed/blocked?"* → Green buttons = passed, message streams

### Step 4: Test Risky Content (Should Block)

**Test Message:**
```
Hello, my name is John Smith and my social security number is 123-45-6789. I work at Acme Corp and my email is john.smith@acme.com. I need to process credit card 4532-1234-5678-9012 for customer Alice Johnson whose phone is (555) 123-4567.
```

**What Should Happen:**
1. Enter the PII-rich message
2. Click "Send Message"  
3. **Should see immediate blocking:**
   - Red error message: "Request blocked due to compliance policy violation"
   - Risk score shown (should be > 1.0)
   - No streaming content

**Client Questions Answered:**
- ✅ *"Was it passed/blocked?"* → Clear blocking message with risk score
- ✅ *"How was the decision made?"* → Shows specific risk score threshold exceeded

### Step 5: Inspect Window Analysis Details

**After running the safe content test:**
1. Look for the "Analysis Windows" section with numbered buttons
2. **Click on any window button** (W1, W2, W3, etc.)
3. **Verify the detailed panel shows:**
   - Position in stream (e.g., "Position: 25")
   - Window size (e.g., "Size: 150 tokens")
   - Pattern Score (e.g., "0.000")
   - Presidio Score (e.g., "0.000")
   - **Analyzed Text**: The exact 150-token chunk that was analyzed
   - **Triggered Rules**: Any compliance rules that fired

**Client Questions Answered:**
- ✅ *"What set of tokens is being analyzed?"* → Shows exact text chunks
- ✅ *"How was the decision made?"* → Shows individual scores and rules

### Step 6: Verify Efficiency Claims

**In the Analysis Configuration panel:**
- Should show "25x fewer calls" 
- Compare to old approach: If message has 500 tokens
  - **Old**: 500 analysis calls (1 per token)
  - **New**: 20 analysis calls (1 per 25 tokens)
  - **Efficiency**: 25x improvement ✅

### Step 7: Test Real-time Updates

1. **Send the safe message again**
2. **Watch the interface in real-time:**
   - Configuration panel updates
   - Window buttons appear progressively
   - Stream content appears word by word
   - **This proves real-time analysis transparency**

### Step 8: Verify Different Content Types

**Test these additional scenarios:**

**Medical Content (Should Block):**
```
Patient John Doe has diabetes and his medical record number is MR123456. His insurance ID is INS-789-012 and he lives at 123 Main Street.
```

**Financial Content (Should Block):**
```
Account number 1234567890 with routing number 021000021 belongs to customer with SSN 987-65-4321.
```

**Technical Content (Should Pass):**
```
Our API uses JWT tokens for authentication. The system processes requests through microservices architecture with Docker containers. We implement rate limiting and caching for performance optimization.
```

## 🎯 Key Success Indicators

### ✅ Configuration Transparency
- [ ] Analysis parameters clearly displayed
- [ ] Efficiency improvements quantified
- [ ] Real-time updates working

### ✅ Window Analysis Visibility  
- [ ] Individual windows shown as clickable buttons
- [ ] Exact analyzed text visible
- [ ] Scores and rules displayed

### ✅ Decision Making Transparency
- [ ] Clear pass/block decisions
- [ ] Risk scores shown
- [ ] Blocking reasons provided

### ✅ Real-time Performance
- [ ] Streaming works smoothly
- [ ] Analysis happens in real-time
- [ ] No noticeable delays

### ✅ Compliance Accuracy
- [ ] PII content correctly blocked
- [ ] Safe content correctly passed
- [ ] Risk thresholds working

## 🚨 If Something Doesn't Work

### Frontend Not Loading
```bash
# Check containers
docker ps

# Restart if needed
docker-compose restart frontend
```

### API Not Responding
```bash
# Check API health
curl http://localhost:8000/health

# Restart if needed
docker-compose restart api
```

### No Window Analysis Events
1. Check browser developer console for errors
2. Verify API is returning window_analysis events:
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "test message"}' -N
```

## 🎉 Success Criteria Met

When you complete this verification, you can confidently tell the client:

1. **✅ "What tokens are being analyzed?"** 
   → Fully visible through interactive window inspection

2. **✅ "How was the decision made?"**
   → Complete transparency with scores, rules, and thresholds

3. **✅ "Was it passed/blocked?"**
   → Clear visual indicators and detailed explanations

4. **✅ Efficiency Proven**
   → 25x improvement demonstrated with real metrics

5. **✅ Production Ready**
   → Professional interface suitable for engineer demonstrations

**The sliding window analysis system is working exactly as the client expects!** 🚀
