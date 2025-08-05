# Production Cache Management Guide

## 🚨 Cache Issues in Production

If you encounter incorrect student counts in production, it's likely due to **stale cache data**. Here's how to diagnose and fix it.

## 🔍 Quick Diagnosis

### 1. Check Cache Status
```bash
python cache_monitor.py info
```

This will show:
- ✅ Batches with students (working correctly)
- ⚠️ Batches with 0 students (potential issue)

### 2. Test Fresh Query
```bash
python cache_monitor.py test-batch batch23-27
```

This forces a fresh GraphQL query and shows the real result.

## 🛠️ Fixing Cache Issues

### Option 1: Clear Specific Batch Cache
```bash
python cache_monitor.py clear-batch batch23-27
```

### Option 2: Clear All Cache (Nuclear Option)
```bash
python cache_monitor.py clear-all
```

## 🔧 Prevention Measures

The improved `ApiService` now includes:

1. **Smart Cache Validation**: Won't cache empty results for batches that should have students
2. **Known Empty Batches**: Recognizes batches like `batch22-26` that legitimately have 0 students
3. **Error Handling**: Falls back to cached data if fresh query fails
4. **Warning Logs**: Prints warnings when suspicious results are detected

## 🎯 Common Scenarios

### Scenario 1: Backend Temporarily Down
- **Symptoms**: Cache shows 0 students for a batch that should have students
- **Fix**: Clear cache for that batch
- **Prevention**: Improved error handling prevents caching bad results

### Scenario 2: Network Issues
- **Symptoms**: Timeout errors, inconsistent results
- **Fix**: Clear cache and retry
- **Prevention**: 30-second timeout prevents hanging requests

### Scenario 3: Firestore Issues
- **Symptoms**: GraphQL errors, empty results
- **Fix**: Clear cache and wait for backend to recover
- **Prevention**: Fallback to cached data during errors

## 📊 Monitoring Commands

```bash
# Check all cache status
python cache_monitor.py info

# Test specific batch
python cache_monitor.py test-batch batch23-27

# Clear problematic batch
python cache_monitor.py clear-batch batch23-27

# Nuclear option - clear everything
python cache_monitor.py clear-all
```

## 🚀 Deployment Checklist

Before deploying to production:

1. ✅ Test cache monitor tool
2. ✅ Verify cache validation works
3. ✅ Test error handling scenarios
4. ✅ Document cache management procedures
5. ✅ Set up monitoring alerts for cache issues

## 🔄 Cache Lifecycle

- **Cache Duration**: 24 hours
- **Validation**: Smart validation prevents bad cache entries
- **Fallback**: Uses cached data during errors
- **Recovery**: Automatic fresh queries for suspicious results

## 📝 Log Messages

The system now logs:
- `⚠️ Cache shows 0 students for {batch}, fetching fresh data...`
- `⚠️ Fresh query returned 0 students for {batch}. This might indicate an issue.`
- `❌ Error fetching students for {batch}: {error}`
- `🔄 Falling back to cached data for {batch}`

These logs help identify and debug cache issues in production. 