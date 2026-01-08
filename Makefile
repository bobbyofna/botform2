# BotForm2 Server Management Makefile
# Ubuntu/Linux version
# Provides easy commands for managing the server process

PYTHON = venv/bin/python3
PORT = 80
PG_SERVICE = postgresql

.PHONY: stop start restart reboot status logs setup-users install

install:
	@echo "Installing dependencies..."
	@$(PYTHON) -m pip install -q -r requirements.txt
	@echo "✓ Dependencies installed"

setup-users:
	@echo "Setting up initial users..."
	@$(PYTHON) setup_initial_users.py

stop:
	@echo "Stopping BotForm2 server..."
	@if lsof -ti:$(PORT) > /dev/null 2>&1; then \
		kill -TERM $$(lsof -ti:$(PORT)) 2>/dev/null && echo "✓ Server stopped" || echo "✗ Failed to stop server"; \
	else \
		echo "Server is not running on port $(PORT)"; \
	fi

start:
	@echo "Starting BotForm2 server..."
	@if lsof -ti:$(PORT) > /dev/null 2>&1; then \
		echo "✗ Server already running on port $(PORT)"; \
		echo "  Use 'make stop' first or 'make restart' to restart"; \
		exit 1; \
	else \
		nohup $(PYTHON) run.py > server.log 2>&1 & \
		echo "✓ Server starting in background..."; \
		sleep 2; \
		if lsof -ti:$(PORT) > /dev/null 2>&1; then \
			echo "✓ Server is running on port $(PORT)"; \
			echo "  PID: $$(lsof -ti:$(PORT))"; \
		else \
			echo "✗ Server failed to start. Check server.log for details"; \
			tail -20 server.log; \
			exit 1; \
		fi \
	fi

restart:
	@echo "Restarting BotForm2 server..."
	@$(MAKE) stop
	@sleep 1
	@$(MAKE) start

reboot:
	@echo "Rebooting PostgreSQL and BotForm2..."
	@sudo systemctl restart $(PG_SERVICE)
	@echo "✓ PostgreSQL restarted"
	@$(MAKE) restart

status:
	@echo "========================================"
	@echo "BotForm2 Status Check"
	@echo "========================================"
	@echo ""
	@echo "PostgreSQL Service:"
	@systemctl is-active --quiet $(PG_SERVICE) && echo "  ✓ Running" || echo "  ✗ Stopped"
	@echo ""
	@echo "Port $(PORT) Status:"
	@if lsof -ti:$(PORT) > /dev/null 2>&1; then \
		echo "  ✓ Server is RUNNING on port $(PORT)"; \
		echo "  PID: $$(lsof -ti:$(PORT))"; \
	else \
		echo "  ✗ Port $(PORT) is AVAILABLE (server not running)"; \
	fi
	@echo ""
	@echo "Server Health:"
	@curl -s http://localhost:$(PORT)/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "  ✗ Server not responding"
	@echo ""
	@echo "Active Bots:"
	@curl -s http://localhost:$(PORT)/api/bots 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20 || echo "  ✗ Cannot retrieve bot status"
	@echo ""

logs:
	@echo "Tailing server logs (Ctrl+C to exit)..."
	@tail -f server.log
