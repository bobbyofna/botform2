# BotForm2 Server Management Makefile
# Provides easy commands for managing the server process

PYTHON = venv/Scripts/pythonw.exe
PORT = 8000
PG_SERVICE = postgresql-x64-18

.PHONY: stop start restart reboot status

stop:
	@for /f "tokens=5" %%a in ('netstat -aon ^| find "8000" ^| find "LISTENING"') do @taskkill /f /pid %%a 2>nul

start:
	start /B $(PYTHON) run.py > server.log 2>&1

restart:
	@for /f "tokens=5" %a in ('netstat -aon | find "8000" ^| find "LISTENING"') do taskkill /f /pid %a
	start /B $(PYTHON) run.py > server.log 2>&1

reboot:
	@net stop postgresql-x64-18
	@net start postgresql-x64-18
	@for /f "tokens=5" %%a in ('netstat -aon ^| find "8000" ^| find "LISTENING"') do @taskkill /f /pid %%a 2>nul
	start /B $(PYTHON) run.py > server.log 2>&1

status:
	@echo BotForm2 Status Check
	@echo =====================
	@echo.
	@echo PostgreSQL Service:
	@sc query $(PG_SERVICE) | findstr STATE
	@echo.
	@echo Port $(PORT) Status:
	@netstat -ano | findstr :$(PORT) | findstr LISTENING >nul 2>&1 && echo Server is RUNNING on port $(PORT) || echo Port $(PORT) is AVAILABLE
	@echo.
	@echo Server Health:
	@curl -s http://127.0.0.1:$(PORT)/health 2>nul || echo Server not responding
	@echo.
	@echo Active Bots:
	@curl -s http://127.0.0.1:$(PORT)/api/bots 2>nul | findstr "bot_id" || echo No bots or server not running
