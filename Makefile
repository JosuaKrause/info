help:
	@echo "The following make targets are available:"
	@echo "install	install general dependencies"
	@echo "create	create all output files"
	@echo "run-web	serves the created files. when exiting it will remove all output files"
	@echo "lint-flake8	run flake8 checker to deteck missing trailing comma"
	@echo "lint-pylint	run linter check using pylint standard"
	@echo "lint-type-check	run type check"
	@echo "lint-all	run all lints"
	@echo "pre-commit 	sort python package imports using isort"

install:
	git submodule update --init --recursive
	pip install --upgrade --progress-bar off pip
	pip install --upgrade --progress-bar off -r requirements.txt

create:
	./create.sh

run-web:
	./run_web.sh

lint-pylint:
	find . \( -name '*.py' -o -name '*.pyi' \) -and -not -path './venv/*' \
	| sort
	find . \( -name '*.py' -o -name '*.pyi' \) -and -not -path './venv/*' \
	| sort | xargs pylint -j 6

lint-type-check:
	mypy . --config-file mypy.ini

lint-flake8:
	flake8 --verbose --select C812,C815,I001,I002,I003,I004,I005 --exclude \
	venv --show-source ./

lint-all: \
	lint-flake8 \
	lint-type-check \
	lint-pylint

pre-commit:
	pre-commit install
	isort .
