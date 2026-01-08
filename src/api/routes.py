"""
API routes for BotForm2.

RESTful API endpoints for bot management.
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel

from ..utils.id_generator import id_generator
from ..utils.auth import auth_manager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

def require_admin(_request: Request):
    """Check if user is admin."""
    session_token = _request.cookies.get('session_token')
    if auth_manager.is_admin(session_token) == False:
        raise HTTPException(status_code=403, detail="Admin access required")



# Request/Response models
class BotCreate(BaseModel):
    name: str
    bot_type: str
    target_user_url: str
    max_trade_value: Optional[float] = 500.0
    min_trade_value: Optional[float] = 50.0
    copy_ratio: Optional[float] = 0.5
    stop_loss_percentage: Optional[float] = 10.0
    max_daily_loss: Optional[float] = 1000.0
    notes: Optional[str] = ''


class BotUpdate(BaseModel):
    name: Optional[str] = None
    max_trade_value: Optional[float] = None
    min_trade_value: Optional[float] = None
    copy_ratio: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    max_daily_loss: Optional[float] = None
    notes: Optional[str] = None


class BotStart(BaseModel):
    mode: str  # 'paper' or 'production'


class NotesUpdate(BaseModel):
    notes: str


# Bot management endpoints
@router.get("/bots")
async def get_bots(request: Request, status: Optional[str] = None, sort_by: Optional[str] = None):
    """Get all bots with optional filtering and sorting."""
    try:
        db_manager = request.app.state.db_manager
        bots = await db_manager.get_all_bots(_status=status, _sort_by=sort_by)
        return {"bots": bots}

    except Exception as e:
        logger.error("Error getting bots: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bots")
async def create_bot(request: Request, bot_data: BotCreate):
    """Create a new bot."""
    try:
        db_manager = request.app.state.db_manager
        bot_manager = request.app.state.bot_manager

        # Extract user address from URL or direct input
        import re
        direct_match = re.match(r'^(0x[a-fA-F0-9]{40})$', bot_data.target_user_url.strip())
        if direct_match is not None:
            user_address = direct_match.group(1)
        else:
            url_match = re.search(r'/(user|profile)/(0x[a-fA-F0-9]{40})', bot_data.target_user_url)
            if url_match is not None:
                user_address = url_match.group(2)
            else:
                user_address = None

        # Generate bot ID
        bot_id = id_generator.generate_bot_id()

        # Prepare bot data for database
        bot_dict = {
            'bot_id': bot_id,
            'name': bot_data.name,
            'bot_type': bot_data.bot_type,
            'status': 'inactive',
            'target_user_url': bot_data.target_user_url,
            'target_user_address': user_address,
            'max_trade_value': bot_data.max_trade_value,
            'min_trade_value': bot_data.min_trade_value,
            'copy_ratio': bot_data.copy_ratio,
            'stop_loss_percentage': bot_data.stop_loss_percentage,
            'max_daily_loss': bot_data.max_daily_loss,
            'notes': bot_data.notes
        }

        # Create in database
        created_bot = await db_manager.create_bot(bot_dict)

        # Create bot instance in manager
        await bot_manager.create_bot(created_bot)

        return created_bot

    except Exception as e:
        logger.error("Error creating bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}")
async def get_bot(request: Request, bot_id: str):
    """Get specific bot details."""
    try:
        db_manager = request.app.state.db_manager
        bot = await db_manager.get_bot(bot_id)

        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")

        return bot

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bots/{bot_id}")
async def update_bot(request: Request, bot_id: str, update_data: BotUpdate):
    """Update bot configuration."""
    try:
        db_manager = request.app.state.db_manager

        # Filter out None values
        update_dict = {}
        if update_data.name is not None:
            update_dict['name'] = update_data.name
        if update_data.max_trade_value is not None:
            update_dict['max_trade_value'] = update_data.max_trade_value
        if update_data.min_trade_value is not None:
            update_dict['min_trade_value'] = update_data.min_trade_value
        if update_data.copy_ratio is not None:
            update_dict['copy_ratio'] = update_data.copy_ratio
        if update_data.stop_loss_percentage is not None:
            update_dict['stop_loss_percentage'] = update_data.stop_loss_percentage
        if update_data.max_daily_loss is not None:
            update_dict['max_daily_loss'] = update_data.max_daily_loss
        if update_data.notes is not None:
            update_dict['notes'] = update_data.notes

        updated_bot = await db_manager.update_bot(bot_id, update_dict)

        if updated_bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")

        return updated_bot

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bots/{bot_id}")
async def delete_bot(request: Request, bot_id: str):
    """Delete a bot."""
    try:
        db_manager = request.app.state.db_manager
        bot_manager = request.app.state.bot_manager

        # Remove from bot manager
        await bot_manager.remove_bot(bot_id)

        # Delete from database
        result = await db_manager.delete_bot(bot_id)

        if result == 0:
            raise HTTPException(status_code=404, detail="Bot not found")

        return {"success": True, "message": "Bot deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bots/{bot_id}/start")
async def start_bot(request: Request, bot_id: str, start_data: BotStart):
    """Start a bot in specified mode."""
    try:
        db_manager = request.app.state.db_manager
        bot_manager = request.app.state.bot_manager

        # Get bot from manager or create it
        bot = bot_manager.get_bot(bot_id)
        if bot is None:
            # Load from database and create instance
            bot_data = await db_manager.get_bot(bot_id)
            if bot_data is None:
                raise HTTPException(status_code=404, detail="Bot not found")
            bot = await bot_manager.create_bot(bot_data)

        # Start bot
        await bot_manager.start_bot(bot_id, _mode=start_data.mode)

        # Update database status
        await db_manager.update_bot(bot_id, {'status': start_data.mode})

        return {"success": True, "bot_id": bot_id, "status": start_data.mode}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bots/{bot_id}/stop")
async def stop_bot(request: Request, bot_id: str):
    """Stop a running bot."""
    try:
        db_manager = request.app.state.db_manager
        bot_manager = request.app.state.bot_manager

        # Stop bot
        await bot_manager.stop_bot(bot_id)

        # Update database status
        await db_manager.update_bot(bot_id, {'status': 'inactive'})

        return {"success": True, "bot_id": bot_id, "status": "inactive"}

    except Exception as e:
        logger.error("Error stopping bot: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# Performance endpoints
@router.get("/performance/aggregate")
async def get_aggregate_performance(request: Request, mode: Optional[str] = None, period: Optional[str] = '1d'):
    """Get aggregated performance data for charts."""
    try:
        # Placeholder implementation
        return {
            "data": [],
            "mode": mode,
            "period": period
        }

    except Exception as e:
        logger.error("Error getting aggregate performance: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}/performance")
async def get_bot_performance(request: Request, bot_id: str, period: Optional[str] = '24h'):
    """Get bot-specific performance history."""
    try:
        db_manager = request.app.state.db_manager
        performance_data = await db_manager.get_performance_history(bot_id, _period=period)

        return {"bot_id": bot_id, "period": period, "data": performance_data}

    except Exception as e:
        logger.error("Error getting bot performance: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bots/{bot_id}/trades")
async def get_bot_trades(request: Request, bot_id: str, limit: Optional[int] = 50, offset: Optional[int] = 0, status: Optional[str] = None):
    """Get trade history for a bot."""
    try:
        db_manager = request.app.state.db_manager
        trades = await db_manager.get_bot_trades(bot_id, _limit=limit, _offset=offset, _status=status)

        return {"bot_id": bot_id, "trades": trades, "count": len(trades)}

    except Exception as e:
        logger.error("Error getting bot trades: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/all")
async def get_all_trades(request: Request, limit: Optional[int] = 50, offset: Optional[int] = 0, status: Optional[str] = None):
    """Get trade history across all bots."""
    try:
        db_manager = request.app.state.db_manager
        trades = await db_manager.get_all_trades(_limit=limit, _offset=offset, _status=status)

        return {"trades": trades, "count": len(trades)}

    except Exception as e:
        logger.error("Error getting all trades: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# Notes endpoint
@router.put("/bots/{bot_id}/notes")
async def update_notes(request: Request, bot_id: str, notes_data: NotesUpdate):
    """Update bot notes."""
    try:
        db_manager = request.app.state.db_manager
        updated_bot = await db_manager.update_bot(bot_id, {'notes': notes_data.notes})

        if updated_bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")

        return {"success": True, "bot_id": bot_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating notes: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# Shutdown endpoint
@router.post("/shutdown")
async def shutdown_all_bots(request: Request):
    """Gracefully stop all running bots."""
    try:
        bot_manager = request.app.state.bot_manager

        stopped_count = 0
        bot_ids = list(bot_manager.active_bots.keys())

        i = 0
        for bot_id in bot_ids:
            try:
                await bot_manager.stop_bot(bot_id)
                stopped_count = stopped_count + 1
            except Exception as e:
                logger.error("Error stopping bot {}: {}".format(bot_id, str(e)))
            i = i + 1

        return {
            "success": True,
            "message": "Shutdown initiated",
            "bots_stopped": stopped_count,
            "total_bots": len(bot_ids)
        }

    except Exception as e:
        logger.error("Error during shutdown: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# User validation endpoint
@router.post("/validate-user")
async def validate_user(request: Request, target_user_url: str = Body(..., embed=True)):
    """Validate a Polymarket user address before creating bot."""
    try:
        polymarket_client = request.app.state.polymarket_client

        # Extract address from URL or use direct address input
        import re

        # First check if it's already a direct address (0x...)
        direct_match = re.match(r'^(0x[a-fA-F0-9]{40})$', target_user_url.strip())
        if direct_match is not None:
            user_address = direct_match.group(1)
        else:
            # Try to extract from URL format
            url_match = re.search(r'/user/(0x[a-fA-F0-9]{40})', target_user_url)
            if url_match is None:
                return {
                    "valid": False,
                    "message": "Invalid format. Expected: 0x... or https://polymarket.com/user/0x...",
                    "address": None
                }
            user_address = url_match.group(1)

        # Validate the address
        result = await polymarket_client.validate_user_address(user_address)

        # Include the extracted address in response
        if result.get('valid') == True:
            result['address'] = user_address

        return result

    except Exception as e:
        logger.error("Error validating user: {}".format(str(e)))
        return {
            "valid": False,
            "message": "Validation error: {}".format(str(e)),
            "address": None
        }


# Get user recent activity
@router.get("/user-activity/{user_address}")
async def get_user_activity(request: Request, user_address: str, limit: Optional[int] = 10):
    """Get recent trading activity for a user."""
    try:
        polymarket_client = request.app.state.polymarket_client

        activities = await polymarket_client.get_user_recent_activity(user_address, _limit=limit)

        return {
            "user_address": user_address,
            "activities": activities,
            "count": len(activities)
        }

    except Exception as e:
        logger.error("Error getting user activity: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# Trade management endpoints
class TradeClose(BaseModel):
    exit_price: float


@router.post("/trades/{trade_id}/close")
async def close_trade(request: Request, trade_id: str, close_data: TradeClose):
    """Close an open trade with specified exit price."""
    try:
        bot_manager = request.app.state.bot_manager
        db_manager = request.app.state.db_manager

        # Get trade to find which bot owns it
        trades = await db_manager.get_all_trades()
        trade = next((t for t in trades if t['trade_id'] == trade_id), None)

        if trade is None:
            raise HTTPException(status_code=404, detail="Trade not found")

        if trade['status'] != 'open':
            raise HTTPException(status_code=400, detail="Trade is not open")

        # Get bot instance
        bot = bot_manager.get_bot(trade['bot_id'])
        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Close the trade
        closed_trade = await bot.close_trade(trade_id, close_data.exit_price)

        if closed_trade is None:
            raise HTTPException(status_code=500, detail="Failed to close trade")

        return {"success": True, "trade": closed_trade}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error closing trade: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet/total")
async def get_total_wallet_balance(request: Request):
    """Get total paper trading wallet balance across all bots."""
    try:
        db_manager = request.app.state.db_manager
        total_balance = await db_manager.get_total_paper_wallet_balance()

        return {
            "total_balance": total_balance,
            "currency": "USD"
        }

    except Exception as e:
        logger.error("Error getting total wallet balance: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wallet/{bot_id}/reset")
async def reset_wallet_balance(request: Request, bot_id: str):
    """Reset bot's paper trading wallet to initial balance or custom amount."""
    try:
        db_manager = request.app.state.db_manager

        # Check if bot exists
        bot = await db_manager.get_bot(bot_id)
        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")

        # Get optional custom amount from request body
        body = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        custom_amount = body.get('amount')

        # Validate custom amount if provided
        if custom_amount is not None:
            try:
                custom_amount = float(custom_amount)
                if custom_amount < 0:
                    raise HTTPException(status_code=400, detail="Amount must be non-negative")
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="Invalid amount format")

        # Reset wallet
        updated_bot = await db_manager.reset_paper_wallet(bot_id, custom_amount)

        return {
            "success": True,
            "bot_id": bot_id,
            "new_balance": float(updated_bot['paper_wallet_balance'])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting wallet: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wallet/reset-all-paper")
async def reset_all_paper_wallets(request: Request):
    """Reset all active paper trading bots' wallets to $1000."""
    require_admin(request)
    try:
        db_manager = request.app.state.db_manager

        # Get all bots in paper mode
        all_bots = await db_manager.get_all_bots()
        paper_bots = [bot for bot in all_bots if bot['status'] == 'paper']

        # Reset each paper bot's wallet to $1000
        reset_count = 0
        for bot in paper_bots:
            await db_manager.reset_paper_wallet(bot['bot_id'], 1000.0)
            reset_count = reset_count + 1

        logger.info("Reset {} paper trading bot wallets to $1000".format(reset_count))

        return {
            "success": True,
            "bots_reset": reset_count,
            "message": "Reset {} paper trading bot(s) to $1000.00".format(reset_count)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting all paper wallets: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


# User management endpoints (admin only)
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'guest'


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None


@router.get("/users")
async def get_users(request: Request):
    """Get all users (admin only)."""
    require_admin(request)
    try:
        db_manager = request.app.state.db_manager
        users = await db_manager.get_all_users()
        return {"users": users}

    except Exception as e:
        logger.error("Error getting users: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
async def create_user(request: Request, user_data: UserCreate):
    """Create a new user (admin only)."""
    require_admin(request)
    try:
        db_manager = request.app.state.db_manager

        # Validate role
        if user_data.role not in ['admin', 'guest']:
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'guest'")

        # Check if username already exists
        existing_user = await db_manager.get_user_by_username(user_data.username)
        if existing_user is not None:
            raise HTTPException(status_code=400, detail="Username already exists")

        # Create user
        user = await db_manager.create_user(
            _username=user_data.username,
            _password=user_data.password,
            _role=user_data.role
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating user: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(request: Request, user_id: str, user_data: UserUpdate):
    """Update user (admin only)."""
    require_admin(request)
    try:
        db_manager = request.app.state.db_manager

        # Build update dict
        update_dict = {}
        if user_data.password is not None:
            # Hash the password
            update_dict['password_hash'] = auth_manager.hash_password(user_data.password)
        if user_data.role is not None:
            if user_data.role not in ['admin', 'guest']:
                raise HTTPException(status_code=400, detail="Role must be 'admin' or 'guest'")
            update_dict['role'] = user_data.role

        if len(update_dict) == 0:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update user
        updated_user = await db_manager.update_user(user_id, update_dict)

        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: str):
    """Delete user (admin only)."""
    require_admin(request)
    try:
        db_manager = request.app.state.db_manager

        # Get user to check if it's the admin user
        user = await db_manager.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent deletion of admin user
        if user['username'] == 'admin':
            raise HTTPException(status_code=400, detail="Cannot delete the admin user")

        # Delete user
        result = await db_manager.delete_user(user_id)

        if result == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"success": True, "message": "User deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting user: {}".format(str(e)))
        raise HTTPException(status_code=500, detail=str(e))
