# =========================
# 🧩 Setup and Installation
# =========================

install:
	@echo "🚀 Installing project in editable mode..."
	pip install -e .

init:
	@echo "🧹 Cleaning environment and setting up fresh virtual environment..."
	rm -rf .venv
	python3.10 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip setuptools wheel
	. .venv/bin/activate && make install

# =========================
# 🧹 Clean Up Persistent Data (Qdrant, Index DB, Storage)
# =========================

clean_data:
	@echo "🧹 Cleaning old Qdrant and index databases..."
	rm -rf persistent_db/vector_db/qdrant_server
	rm -rf persistent_db/index_db/llamaindex
	rm -rf storage
	rm -f logs/qdrant_initialized.marker
	@echo "✅ Clean up completed."

reset_data: kill_all_qdrant clean_data
	@echo "🔄 Data storage has been reset. Start services with 'make start' to reload data."

# =========================
# 🚀 Qdrant Vector DB Controls
# =========================

check_running_qdrant:
	@echo "🔍 Checking for running Qdrant instances..."
	@QDRANT_PIDS=$$(pgrep -f "qdrant --config-path" || echo ""); \
	if [ -n "$$QDRANT_PIDS" ]; then \
		echo "✅ Found running Qdrant instances:"; \
		for pid in $$QDRANT_PIDS; do \
			CMD=$$(ps -p $$pid -o command= | sed "s|$$PWD/|./|g" | sed "s|$$HOME|~|g"); \
			echo "  - PID: $$pid, Command: $$CMD"; \
		done; \
		echo "   Use 'make kill_all_qdrant' to forcefully terminate all instances"; \
	else \
		echo "ℹ️ No running Qdrant instances found"; \
	fi

kill_all_qdrant:
	@echo "🛑 Forcefully terminating all Qdrant instances..."
	@QDRANT_PIDS=$$(pgrep -f "qdrant --config-path" || echo ""); \
	if [ -n "$$QDRANT_PIDS" ]; then \
		for pid in $$QDRANT_PIDS; do \
			echo "  - Killing PID: $$pid"; \
			kill -9 $$pid; \
		done; \
		echo "✅ All Qdrant instances terminated"; \
		rm -f logs/qdrant.pid; \
	else \
		echo "ℹ️ No running Qdrant instances found"; \
	fi

start_qdrant_foreground:
	@echo "🚀 Starting Qdrant vector database in foreground (press Ctrl+C to stop)..."
	$(eval QDRANT_BIN := $(HOME)/Documents/Apps/qdrant/bin/qdrant)
	$(eval QDRANT_CONFIG := $(shell pwd)/config/qdrant_config.yaml)
	@echo "📝 Using config: qdrant_config.yaml"
	$(QDRANT_BIN) --config-path $(QDRANT_CONFIG)

# Function to modify the start_qdrant target in the Makefile

start_qdrant: kill_all_qdrant
	@echo "🚀 Starting Qdrant vector database..."
	$(eval QDRANT_BIN := $(HOME)/Documents/Apps/qdrant/bin/qdrant)
	$(eval QDRANT_CONFIG := $(shell pwd)/config/qdrant_config.yaml)
	$(eval LOG_DIR := $(shell pwd)/logs)
	@mkdir -p $(LOG_DIR)
	$(eval QDRANT_LOG := $(LOG_DIR)/qdrant_$(shell date +%Y%m%d_%H%M%S).log)
	$(eval LOG_NAME := $(shell basename $(QDRANT_LOG)))
	@echo "📝 Using config: config/qdrant_config.yaml"
	@echo "📝 Logs will be saved to: logs/$(LOG_NAME)"
	@# Run with relative paths in output
	@$(QDRANT_BIN) --config-path $(QDRANT_CONFIG) > $(QDRANT_LOG) 2>&1 & echo $$! > $(LOG_DIR)/qdrant.pid
	@chmod 644 $(LOG_DIR)/qdrant.pid
	@sleep 2
	@PID=$$(cat $(LOG_DIR)/qdrant.pid 2>/dev/null || echo "unknown"); \
	if kill -0 $$PID 2>/dev/null; then \
		echo "✅ Qdrant started with PID $$PID"; \
		echo "⏳ Waiting for Qdrant to be ready..."; \
		for i in {1..10}; do \
			if curl -s http://localhost:6333/collections > /dev/null; then \
				echo "✅ Qdrant is ready!"; \
				break; \
			else \
				echo "⌛ Attempt $$i: Waiting for Qdrant..."; \
				sleep 1; \
			fi; \
		done; \
	else \
		echo "❌ Qdrant failed to start. Check logs at logs/$(LOG_NAME)"; \
		echo ""; \
		echo "🔍 Last 10 lines of log:"; \
		tail -n 10 $(QDRANT_LOG); \
	fi

stop_qdrant:
	@echo "🛑 Stopping Qdrant vector database..."
	@if [ -f logs/qdrant.pid ]; then \
		if kill -0 $$(cat logs/qdrant.pid 2>/dev/null) 2>/dev/null; then \
			kill $$(cat logs/qdrant.pid); \
			echo "✅ Qdrant stopped (PID: $$(cat logs/qdrant.pid))"; \
		else \
			echo "⚠️ Qdrant process not found (PID: $$(cat logs/qdrant.pid))"; \
		fi; \
		rm -f logs/qdrant.pid; \
	else \
		echo "⚠️ Qdrant PID file not found, trying to find by process..."; \
		QDRANT_PID=$$(pgrep -f "qdrant --config-path"); \
		if [ -n "$$QDRANT_PID" ]; then \
			kill $$QDRANT_PID; \
			echo "✅ Qdrant stopped (PID: $$QDRANT_PID)"; \
		else \
			echo "⚠️ No running Qdrant process found"; \
		fi; \
	fi

restart_qdrant: stop_qdrant start_qdrant
	@echo "🔄 Qdrant has been restarted"

qdrant_status:
	@echo "🔍 Checking Qdrant status..."
	@QDRANT_PID=""; \
	if [ -f logs/qdrant.pid ]; then \
		QDRANT_PID=$$(cat logs/qdrant.pid 2>/dev/null); \
		if [ -n "$$QDRANT_PID" ] && kill -0 $$QDRANT_PID 2>/dev/null; then \
			echo "✅ Qdrant is running (PID: $$QDRANT_PID)"; \
			echo "📊 Collections:"; \
			curl -s http://localhost:6333/collections | grep -o '"name":"[^"]*"' | cut -d':' -f2 | tr -d '"' | sed 's/^/  - /'; \
		else \
			echo "❌ Qdrant process is dead but PID file exists (PID: $$QDRANT_PID)"; \
			echo "   Run 'make restart_qdrant' to fix this."; \
		fi; \
	else \
		QDRANT_PIDS=$$(pgrep -f "qdrant --config-path" || echo ""); \
		if [ -n "$$QDRANT_PIDS" ]; then \
			echo "✅ Qdrant is running (PIDs: $$QDRANT_PIDS) but PID file is missing"; \
			echo "   Creating PID file for first instance..."; \
			FIRST_PID=$$(echo $$QDRANT_PIDS | tr ' ' '\n' | head -n 1); \
			echo $$FIRST_PID > logs/qdrant.pid; \
			echo "📊 Collections:"; \
			curl -s http://localhost:6333/collections | grep -o '"name":"[^"]*"' | cut -d':' -f2 | tr -d '"' | sed 's/^/  - /'; \
		else \
			echo "❌ Qdrant is not running"; \
		fi; \
	fi

qdrant_logs:
	@echo "📋 Recent Qdrant logs:"
	@LOG_FILES=$$(ls -t logs/qdrant_*.log 2>/dev/null | head -n1); \
	if [ -n "$$LOG_FILES" ]; then \
		echo "📝 Showing last 20 lines from $$(basename $$LOG_FILES)"; \
		tail -n 20 $$LOG_FILES; \
	else \
		echo "❌ No Qdrant log files found"; \
	fi

# =========================
# 🚀 Run Application (Clean start)
# =========================

start:
	@echo "🚀 Starting services..."
	bash scripts/start_services.sh

start_app_only: ensure_qdrant_running
	@echo "🚀 Starting FastAPI application only..."
	. .venv/bin/activate && python -m app.main --host 0.0.0.0 --port 8000

ensure_qdrant_running:
	@echo "🔍 Ensuring Qdrant is running..."
	@if ! curl -s http://localhost:6333/collections > /dev/null; then \
		echo "⚠️ Qdrant is not running. Starting it..."; \
		make start_qdrant; \
	else \
		echo "✅ Qdrant is already running"; \
	fi

# =========================
# 📥 Data Loader
# =========================

load_data: ensure_qdrant_running
	@echo "📦 Loading data into vector store..."
	. .venv/bin/activate && python -m app.data_loader.load_data
	@echo "Qdrant data initialization completed at $$(date)" > logs/qdrant_initialized.marker
	@echo "📝 Marker created at: qdrant_initialized.marker"

force_reload_data: ensure_qdrant_running
	@echo "🔄 Forcing data reload..."
	@echo "🧹 Removing initialization marker..."
	rm -f logs/qdrant_initialized.marker
	@echo "🗑️ Cleaning existing collection..."
	curl -X DELETE "http://localhost:6333/collections/llamaindex-docs" > /dev/null 2>&1 || true
	@echo "📦 Loading fresh data..."
	make load_data

# =========================
# 🧩 Utilities (Optional)
# =========================

# fmt:
#   @echo "🧹 Formatting code with black..."
#   black .

# lint:
#   @echo "🧪 Running lint checks..."
#   ruff check .

# test:
#   @echo "🧪 Running tests..."
#   pytest