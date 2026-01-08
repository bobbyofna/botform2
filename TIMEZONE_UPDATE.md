# Timezone & Market Name Updates - Quick Reference

## What Changed

### 1. Market Names Now Show Correctly
**Before:** `Market: 0x1234abcd...`
**After:** `Bitcoin Up or Down - January 8, 4AM ET`

The bot now extracts the `title` field directly from Polymarket's activity feed, which contains the human-readable market name.

### 2. All Times Display in New York (ET)
**Before:** `2h ago` or server-local time
**After:** `Jan 8, 2026, 02:45:30 PM ET`

All timestamps now show:
- Exact time to the second
- New York timezone (ET/EDT)
- "ET" suffix for clarity

### 3. Database Still Stores UTC
- Backend continues using UTC (server time)
- No changes to database storage
- Frontend handles timezone conversion

## Code Changes

### Files Modified
1. `src/bots/copy_bot.py` - Market name extraction priority
2. `templates/index.html` - Timestamp formatting with NY timezone
3. `templates/bot_detail.html` - Timestamp formatting with NY timezone
4. `CHANGES.md` - Full documentation

### Key Updates

**Copy Bot** ([src/bots/copy_bot.py](src/bots/copy_bot.py:468-490)):
```python
# Now prioritizes market_title from activity feed
market_name = _trade_data.get('market_title')  # Gets "Bitcoin Up or Down - January 8, 4AM ET"
```

**Frontend Timestamps** ([templates/index.html](templates/index.html:660-669)):
```javascript
return date.toLocaleString('en-US', {
    timeZone: 'America/New_York',  // Force NY timezone
    // ... formatting options
}) + ' ET';
```

## Why These Changes

### Market Names
- Polymarket's activity feed includes the full market title
- This title matches what users see on Polymarket's website
- More readable than market IDs or generic descriptions

### New York Timezone
- Polymarket uses ET in their market names ("4AM ET")
- Consistency between market titles and timestamps
- Standard timezone for US-based prediction markets
- Works regardless of where the server is located

## Testing

To verify the changes work:
1. Look at any recent activity entry - should show full market name
2. Check timestamp format - should end with "ET"
3. Compare timestamp with Polymarket's website - should match (accounting for ET)

## Technical Details

### Timezone Conversion Flow
```
Database (UTC) → JavaScript new Date() → toLocaleString({timeZone: 'America/New_York'}) → Display with "ET"
```

### Market Name Priority
```
1. activity.title (from Polymarket feed)
2. API call to get_market_info()
3. Fallback to "Unknown Market"
```

### Daylight Saving Time
JavaScript automatically handles EST/EDT conversion:
- November-March: EST (UTC-5)
- March-November: EDT (UTC-4)
