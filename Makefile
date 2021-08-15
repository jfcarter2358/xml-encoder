.PHONY: pypi-build pypi-test pypi-upload test
SHELL := /bin/bash

pypi-build: # Build package for PyPI
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine check dist/*

pypi-test: ## Test PyPI upload
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

pypi-upload: ## Upload package to PyPI
	twine upload dist/*

build-linux: ## Build linux binary
	docker run -v "$$(pwd):/src/xml_encoder" johncarterodg/pyinstaller-linux:python-3.7.9_pyinstaller-4.1
	mv dist/linux/__init__ dist/linux/xml_encoder

build-windows: ## Build windows binary
	docker run -v "$$(pwd):/src/xml_encoder" johncarterodg/pyinstaller-windows:python-3.7.9_pyinstaller-4.1
	mv dist/linux/__init__ dist/linux/xml_encoder

build-alpine: ## Build apline binary
	docker run -v "$$(pwd):/src/" johncarterodg/pyinstaller-alpine:python-3.7.9-pyinstaller-4.1 --noconfirm --onefile --log-level DEBUG --clean src/xml_encoder/__init__.py
	mkdir dist/alpine
	mv dist/__init__ dist/alpine/xml_encoder

test: ## Run test encoding and decoding
	rm -rf test_encoded || true
	rm -rf test_decoded || true
	mkdir test_encoded
	mkdir test_decoded
	python3 src/xml_encoder/__init__.py encode dir test_xml test_encoded
	python3 src/xml_encoder/__init__.py decode dir test_encoded test_decoded
	diff -bB <(sed 's/^[ \t]*//' test_xml/OnJobChange.bpmn) <(sed 's/^[ \t]*//' test_decoded/OnJobChange.xml)

lint:  ## Lint the source code
	pylint -j 0 src/ --rcfile=.pylintrc --ignore=tests

format:  ## Format the source code
	autoflake --remove-all-unused-imports --recursive --in-place src/
	isort .
	black .