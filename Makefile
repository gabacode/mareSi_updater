.PHONY: venv_check
venv_check:
	@if [ -d "venv" ]; then \
		echo "Virtual environment found."; \
	else \
		echo "Virtual environment not found. Please run 'make install' first."; \
		exit 1; \
	fi


.PHONY: update
update: venv_check
	@echo "Running update.py..."
	@bash -c "source venv/bin/activate && OPENSSL_CONF=config/openssl.cnf python3 ./update2.py"

.PHONY: diff
diff: venv_check
	@echo "Running diff.py..."
	@bash -c "source venv/bin/activate && python3 ./diff.py"

.PHONY: install
install:
	@echo "Creating virtual environment..."
	@python3 -m venv venv
	@echo "Activating virtual environment and installing dependencies..."
	@bash -c "source venv/bin/activate && pip install -r requirements.txt"
	@echo "Done."
