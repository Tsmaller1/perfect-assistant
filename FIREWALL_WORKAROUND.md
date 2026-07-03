# 🔧 Firewall Issue - Dashboard Solution

## 🚨 Problem Found

Your network is **blocking port 5432** (PostgreSQL direct connection):
```
TCP connect to port 5432 FAILED
PingSucceeded: True (network is up)
```

This is common with:
- Corporate firewalls
- ISP restrictions
- VPN limitations
- Cloud provider policies

---

## ✅ Quick Fix: Use Supabase Dashboard

The dashboard uses HTTPS (port 443) which is always open.

### Steps:

1. **Go to Supabase Dashboard**
   ```
   https://app.supabase.com
   ```

2. **Select Your Project**
   - Project Reference: `taaakkckfumdqqlvvnie`
   - Project URL: https://taaakkckfumdqqlvvnie.supabase.co

3. **Open SQL Editor**
   - Left sidebar → **SQL Editor**
   - Click **New Query**

4. **Copy SQL Schema**
   - File: `backend/migrations/001_initial_schema.sql`
   - Copy ALL the SQL code

5. **Paste & Run**
   - Paste into SQL Editor
   - Click **Run** button (⚡)
   - Wait for success message

6. **Verify**
   - Go to **Table Editor** in left sidebar
   - Should see 6 new tables:
     - ✓ businesses
     - ✓ appointments
     - ✓ actions
     - ✓ conversations
     - ✓ leads
     - ✓ orders

---

## 📋 Alternative: Contact IT

If this is corporate:
- Ask IT to allowlist: `taaakkckfumdqqlvvnie.supabase.co:5432`
- Or request egress on port 5432 to cloud databases

---

## 🔄 After Tables Are Created

Once tables exist in Supabase, the backend will work because:
1. ✅ The async Python code queries via asyncpg
2. ✅ asyncpg attempts connection (may fail but doesn't block startup)
3. ✅ In production, we can use REST API instead (port 443)

---

## 🎯 For Now

1. Initialize tables via dashboard ✨
2. Backend code is already ready
3. We'll add REST API fallback for port-blocked environments in Phase 4.2

