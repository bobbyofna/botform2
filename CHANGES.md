# Trade Display Improvements - January 8, 2026

## Summary
Enhanced trade and activity displays across homepage and bot pages to show more meaningful, detailed information about bets and their outcomes. All timestamps now display in New York (ET) timezone while maintaining UTC storage in the database.

## Changes Made

### 1. Database Schema Updates
- **File**: `src/database/schema.sql`
- **Migration**: `migrations/add_market_metadata.sql`
- Added `market_name` field (TEXT) to store descriptive names of markets (e.g., "Will Bitcoin reach $100k by December?" instead of just a market ID)
- Expanded `outcome` field from VARCHAR(50) to VARCHAR(255) to support longer outcome names (like player names in sports betting)
- Added `close_value` field (DECIMAL 10,2) to store the total value when a position was closed
- Added comments to clarify each field's purpose

### 2. Polymarket API Client Enhancements
- **File**: `src/api/polymarket.py`
- Updated `get_market_info()` method to fetch market details from multiple Polymarket API endpoints:
  - Gamma API: `https://gamma-api.polymarket.com/markets/{id}`
  - CLOB API: `https://clob.polymarket.com/markets/{id}`
  - Search API: `https://gamma-api.polymarket.com/markets?id={id}`
- Returns market question/title/description for display purposes

### 3. Trade Recording Updates
- **File**: `src/bots/copy_bot.py`
- Updated `_execute_paper_trade()` to prioritize market title from Polymarket activity data
  - Uses `title` field from activity feed (e.g., "Bitcoin Up or Down - January 8, 4AM ET")
  - Falls back to API lookup if title not available
  - Final fallback to 'Unknown Market' if both fail
- Updated `close_trade()` to calculate and store `close_value` when positions are closed
- All timestamps stored in UTC (server local time) using `datetime.utcnow()`

### 4. Database Manager Updates
- **File**: `src/database/manager.py`
- Updated `record_trade()` query to include new `market_name` and `close_value` fields

### 5. Frontend Display Improvements

#### Homepage (`templates/index.html`)
- **Timestamp Display**: Changed from relative time ("2h ago") to exact timestamps with seconds in New York timezone ("Jan 8, 2026, 02:45:30 PM ET")
- **Timezone**: All times displayed in America/New_York timezone (ET/EDT) regardless of server location
- **Market Display**: Shows descriptive market name from Polymarket (e.g., "Bitcoin Up or Down - January 8, 4AM ET")
- **Outcome Display**: Shows the specific outcome (e.g., "BUBLIK" for tennis player names, "Up"/"Down" for price predictions)
- **Closed Trades Display**:
  - Shows bet amount and close value separately
  - Displays profit/loss in both dollars and percentage (+$15.50 / +15.5%)
  - Shows opened timestamp, closed timestamp, and duration (e.g., "2d 5h 30m")
- **Open Trades Display**:
  - Shows "Bet Amount" instead of "Amount" for clarity
  - Shows "Entry Price" instead of just "Price"
  - Displays exact timestamp when position was opened

#### Bot Detail Page (`templates/bot_detail.html`)
- Applied same improvements as homepage to:
  - Bot Recent Activity section
  - Open Bets section
  - Closed Bets section
- **Target User Activity Display**:
  - Shows market name/title instead of market ID
  - Shows total bet amount (price × size) instead of separate price and size
  - Uses exact timestamps instead of relative time
  - Shows BUY/SELL badge with color coding

## What Each Field Means

### Understanding "Outcome"
The `outcome` field shows what was bet on within a market:
- For YES/NO markets: "YES" or "NO"
- For sports: Player/team names (e.g., "BUBLIK" for tennis player)
- For price predictions: Specific price ranges or levels
- For categorical markets: Specific option names

### Display Changes

#### Old Display (Closed Trade):
```
Bot Name | Paper | Closed
Market: 0x1234abcd...
Outcome: BUBLIK
2h ago

Amount: $100.00
Price: 0.650
P/L: $15.50
```

#### New Display (Closed Trade):
```
Bot Name | Paper | Closed
Bitcoin Up or Down - January 8, 4AM ET
Outcome: Up

Opened: Jan 8, 2026, 12:30:15 PM ET
Closed: Jan 8, 2026, 02:45:30 PM ET
Duration: 2h 15m

Bet: $100.00
Close: $115.50
+$15.50 (+15.5%)
```

#### Old Display (Open Trade):
```
Bot Name | Paper | Open
Market: 0x1234abcd...
Outcome: YES
Just now

Amount: $50.00
Price: 0.420
```

#### New Display (Open Trade):
```
Bot Name | Paper | Open
Bitcoin Up or Down - January 9, 12PM ET
Outcome: Up
Opened: Jan 8, 2026, 02:45:30 PM ET

Bet Amount: $50.00
Entry Price: 0.420
```

## Benefits

1. **Clarity**: Users can immediately see what they bet on without clicking through to Polymarket
2. **Consistent Timezone**: All times shown in New York ET for consistency with Polymarket's convention
3. **Better Time Tracking**: Exact timestamps to the second allow for precise record-keeping and analysis
4. **Improved P&L Display**: Percentage gains/losses give better context than dollar amounts alone
5. **Duration Tracking**: See how long positions were held for closed trades
6. **No More Confusing IDs**: Market names are human-readable (e.g., "Bitcoin Up or Down - January 8, 4AM ET")
7. **Server Independence**: Database stores UTC, frontend displays NY time - works regardless of server location

## Backward Compatibility

- Existing trades without `market_name` will fall back to showing outcome name
- Existing trades without `close_value` will show $0.00 for closed positions
- All changes are additive - no data loss
- Migration script safely adds new columns without affecting existing data

## Timezone Architecture

### Storage (Backend)
- Database stores all timestamps in **UTC** (server local time)
- Python uses `datetime.utcnow()` for consistency
- PostgreSQL `TIMESTAMP` columns (without timezone) store UTC values
- Server location (Ireland/UTC) doesn't affect this

### Display (Frontend)
- JavaScript converts UTC timestamps to **America/New_York** timezone
- All displayed times show "ET" suffix
- Browser's `toLocaleString()` with `timeZone: 'America/New_York'` handles conversion
- Automatically adjusts for EST/EDT (daylight saving time)

### Why This Works
- **Database**: UTC is the universal standard for storage
- **User Experience**: NY time matches Polymarket's convention and market naming
- **Portability**: Server can be anywhere - Ireland, US, Asia - display stays consistent

## Testing Recommendations

1. Open a new paper trade and verify market name is captured correctly (e.g., "Bitcoin Up or Down - January 8, 4AM ET")
2. Close an existing trade and verify close_value and timestamps are recorded
3. Check homepage "Recent Activity" displays with "ET" timezone suffix
4. Check bot detail page sections display formatted correctly in NY timezone
5. Verify target user activity shows market names from Polymarket API
6. Confirm all timestamps show seconds precision (e.g., "02:45:30 PM ET")

## Future Enhancements

Potential improvements for future iterations:
- Add market category/tag display (Sports, Crypto, Politics, etc.)
- Show position size (number of shares) in addition to dollar amounts
- Add current market price for open positions
- Display unrealized P&L for open trades
- Add filters by market type or time range
