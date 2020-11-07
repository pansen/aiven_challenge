SHELL := /bin/bash
export PYTHONUNBUFFERED := 1

export POETRY_VIRTUALENVS_IN_PROJECT=true

PYTHON_GLOBAL := $(shell /usr/bin/which python3.8)
POETRY := $(PYTHON_GLOBAL) -m poetry

.DEFAULT_GOAL := dev.build

.PHONY: bootstrap
bootstrap:
	$(PYTHON_GLOBAL) -m pip install --user --upgrade \
		setuptools \
		wheel \
		six \
		poetry

.env:
	cp .env.example .env

.PHONY: build
build: .env
	$(POETRY) install --no-dev

.PHONY: dev.build
dev.build: .env
	$(POETRY) install

.PHONY: dev.update
dev.update:
	$(POETRY) update

.PHONY: black
black:
	.venv/bin/black \
		--line-length 120 \
		--target-version py38 \
		pansen

.PHONY: test
test: black
	.venv/bin/pytest pansen


.PHONY: dev.run
dev.run:
	.venv/bin/pansen_aiven


.PHONY: clean
clean: pyc-clean
	rm -rf \
		.env \
		.venv \
		.mypy_cache \
		./*".egg-info"

.PHONY: pyc-clean
pyc-clean:
	@find ./ -type d -name __pycache__ | xargs -P 20 rm -rf
	@find ./ -name '*.pyc'             | xargs -P 20 rm -rf

