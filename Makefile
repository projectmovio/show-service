.PHONY: test
test:
	pip install -U -r test/unittest/requirements.txt
	pip install -U -r src/layers/databases/requirements.txt
	pip install -U -r src/layers/utils/requirements.txt
	PYTHONPATH=./src/layers/utils/python:./src/lambdas/:./src/layers/databases/python \
		pytest test/unittest --cov-report html --cov=src -vv

.PHONE: generate-hashes
generate-hashes:
	pip install pip-tools
	pip-compile --generate-hashes src/layers/databases/requirements.in --output-file src/layers/databases/requirements.txt --allow-unsafe
	pip-compile --generate-hashes src/layers/utils/requirements.in --output-file src/layers/utils/requirements.txt --allow-unsafe
	pip-compile --generate-hashes deploy/requirements.in --output-file deploy/requirements.txt --allow-unsafe
