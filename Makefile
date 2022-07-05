# Inspired by https://github.com/trezor/trezor-firmware/blob/master/Makefile

## Help message

.PHONY: help
help: ## show this help and exit
	@awk -f ./help.awk $(MAKEFILE_LIST)

PY_FILES = ./tests

.PHONY: style
style: ## run Python code formatters
	black --version
	isort --version-number
	@echo [BLACK]
	@black $(PY_FILES)
	@echo [ISORT]
	@isort --profile black $(PY_FILES)

.PHONY: venv
venv: VENV_DIR = venv
venv: ## create Python virtual environment
	python3 -m venv --clear --upgrade-deps $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && python3 -m pip install -r requirements.txt

.PHONY: tests
tests: ## run all tests
	@echo [DESKTOP TESTS]
	pytest $(PY_FILES)
	@echo [MOBILE TESTS]
	pytest --device="Pixel 2" $(PY_FILES)
