all : test

build:
	poetry build

test: build
	poetry run pytest

upload: build test
	poetry publish -u __token__ -p $(PYPI_TOKEN)

.PHONY: build upload
