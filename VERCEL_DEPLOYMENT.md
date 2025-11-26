# Vercel Deployment Guide

## Important Notes

⚠️ **Limitations of Vercel Serverless Functions:**

1. **SQLite Database**: Vercel's serverless functions have a read-only filesystem (except `/tmp`). The SQLite database (`albums.db`) will not persist between deployments. Consider using:
   - Vercel Postgres (recommended)
   - External database service (Supabase, PlanetScale, etc.)
   - Vercel KV (Redis) for simple data storage

2. **File Storage**: The `covers/` directory won't persist. Consider using:
   - Vercel Blob Storage
   - Cloudinary
   - AWS S3
   - Or serve covers from a CDN

3. **File Watcher**: The `watcher.py` file system watcher won't work on Vercel. You'll need to use:
   - Scheduled functions (Vercel Cron)
   - Webhooks
   - Manual rescan via API

4. **Music Library**: The app expects a local `D:\Music` directory which won't exist on Vercel. You'll need to:
   - Store music metadata in a database
   - Use a cloud storage service for music files
   - Or modify the app to work with remote music libraries

## Deployment Steps

1. **Build the frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Ensure all files are committed**:
   ```bash
   git add .
   git commit -m "Add Vercel configuration"
   git push
   ```

3. **Deploy to Vercel**:
   - Connect your GitHub repository to Vercel
   - Vercel will automatically detect the `vercel.json` configuration
   - Set environment variables in Vercel dashboard if needed

4. **Environment Variables** (set in Vercel dashboard):
   - `DB_PATH`: Path to database (consider using a cloud database)
   - `MUSIC_ROOT`: Music library path (may need to be cloud-based)
   - `ENABLE_WATCHER`: Set to `false` (file watcher won't work)

## Troubleshooting

If you see "Not Found" errors:

1. **Check that frontend is built**: Ensure `frontend/dist/` exists with built files
2. **Check Vercel logs**: Look at function logs in Vercel dashboard
3. **Verify routes**: Check that `vercel.json` routes are correct
4. **Check Python version**: Ensure `runtime.txt` specifies Python version if needed

## Recommended Architecture Changes

For a production Vercel deployment, consider:

1. **Database**: Migrate from SQLite to Vercel Postgres or another cloud database
2. **Storage**: Move covers to Vercel Blob Storage or Cloudinary
3. **Music Library**: Store metadata in database, serve files from CDN
4. **File Scanning**: Replace file watcher with scheduled functions or webhooks

