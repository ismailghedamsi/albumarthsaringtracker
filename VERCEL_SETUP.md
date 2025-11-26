# How to Configure Vercel Project Settings

## Accessing Vercel Dashboard Settings

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Find Your Project**: Click on `albumarthsaringtracker`
3. **Open Settings**: Click on the **"Settings"** tab (top navigation)
4. **Configure Project**:
   - **General Settings**: 
     - Framework Preset: Leave as "Other" or "None"
     - Root Directory: Leave empty (or set to `.` if needed)
     - Build Command: Leave empty (Vercel will auto-detect)
     - Output Directory: Leave empty
     - Install Command: Leave empty
   
   - **Environment Variables**: Add any needed variables:
     - `DB_PATH` (if you want to override default)
     - `MUSIC_ROOT` (if needed)
     - `ENABLE_WATCHER=false` (file watcher won't work on Vercel)

## Important Notes

- **No Build Command Needed**: Vercel will automatically detect Python and install dependencies from `requirements.txt`
- **The `vercel.json` file handles routing**: You don't need to configure routes in the dashboard
- **After pushing changes**: Vercel will automatically redeploy

## Troubleshooting "Not Found" Error

### Step 1: Check Deployment Status
1. Go to https://vercel.com/dashboard
2. Click on your project `albumarthsaringtracker`
3. Click on the **"Deployments"** tab
4. Click on the latest deployment (top of the list)
5. Check the **"Build Logs"** tab for any errors during build

### Step 2: Check Function Logs
1. In the same deployment page, click **"Functions"** tab
2. Look for `api/index.py` in the list
3. Click on it to see function logs
4. Look for any Python errors or import errors

### Step 3: Test API Endpoints
Try these URLs to test if the Flask app is running:

- **Health Check**: `https://albumarthsaringtracker.vercel.app/api/health`
  - Should return: `{"status": "ok", "message": "Flask app is running"}`
  
- **Stats Endpoint**: `https://albumarthsaringtracker.vercel.app/api/stats`
  - Should return album statistics (may fail if database doesn't exist)

- **Root**: `https://albumarthsaringtracker.vercel.app/`
  - Should serve the React frontend

### Step 4: Common Issues

**Issue: "Module not found" errors**
- Solution: Make sure `requirements.txt` includes all dependencies
- Check that all Python files are committed to git

**Issue: "Function not found"**
- Solution: Verify `api/index.py` exists and is committed
- Check that `vercel.json` points to `api/index.py`

**Issue: "Database error"**
- Solution: This is expected - SQLite won't work on Vercel
- You'll need to migrate to a cloud database (Vercel Postgres, etc.)

**Issue: "Static files not found"**
- Solution: Make sure `frontend/dist` is built and committed
- Run `cd frontend && npm run build` locally and commit the dist folder

### Step 5: Verify Configuration Files

Make sure these files exist in your repository:
- ✅ `vercel.json` (in root)
- ✅ `api/index.py` (serverless function)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `frontend/dist/` (built React app)

### Step 6: Force Redeploy

If you made changes:
1. Push to GitHub: `git push`
2. Vercel will auto-deploy, OR
3. Go to Vercel dashboard → Your project → "Deployments" → Click "Redeploy"

## Current Configuration

The project is configured to:
- Use `@vercel/python` runtime
- Route all requests through `api/index.py`
- Serve the Flask app as a serverless function

