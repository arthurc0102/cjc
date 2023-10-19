SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:

MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

install:  ## Install dependences
	poetry install
.PHONY: install

test:  ## Run check and test
	poetry run pytest
.PHONY: test

lint:  ## Check lint
	poetry run ruff check --diff .
	poetry run black --check --diff .
.PHONY: lint

lint-fix:  ## Fix lint
	poetry run ruff check --fix .
	poetry run black .
.PHONY: lint-fix

typecheck:  ## Run typechecking
	poetry run pyright .
.PHONY: typecheck

ci: lint typecheck test  ## Run all checks (lint, typecheck, test)
.PHONY: ci

clean:  ## Clean cache files
	find . -name '__pycache__' -type d | xargs rm -rvf
	find . -name '.pytest_cache' -type d | xargs rm -rvf
	poetry run ruff clean
.PHONY: clean

build:  ## Build Docker image
	echo "Build."
.PHONY: build

.DEFAULT_GOAL := help
help: Makefile
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'
.PHONY: help
