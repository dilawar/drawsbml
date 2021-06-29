all : test

build:
	poetry build

develop: build
	poetry install

test: develop
	poetry run pytest


upload: build test
	poetry publish -u __token__ -p $(PYPI_TOKEN)


.PHONY: build upload
