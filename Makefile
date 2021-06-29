all : test

build:
	poetry build

test: build
	poetry run pytest

upload: build test
	poetry publish

.PHONY: build upload
