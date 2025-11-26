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

## Troubleshooting

If you still see "Not Found":

1. **Check Deployment Logs**:
   - Go to your project → "Deployments" tab
   - Click on the latest deployment
   - Check "Function Logs" for errors

2. **Verify Files Are Committed**:
   - Make sure `vercel.json` and `api/index.py` are in your repository
   - Push any changes: `git push`

3. **Check Function Logs**:
   - In Vercel dashboard → Your project → "Functions" tab
   - Look for any errors in `api/index.py`

4. **Test the Function Directly**:
   - Try accessing: `https://albumarthsaringtracker.vercel.app/api/stats`
   - This should hit the Flask API directly

## Current Configuration

The project is configured to:
- Use `@vercel/python` runtime
- Route all requests through `api/index.py`
- Serve the Flask app as a serverless function

