.PHONE: generate-hashes
generate-hashes:
	pip install pip-tools
	pip-compile --generate-hashes src/layers/databases/requirements.in --output-file src/layers/databases/requirements.txt
	pip-compile --generate-hashes src/layers/utils/requirements.in --output-file src/layers/utils/requirements.txt
	pip-compile --generate-hashes deploy/requirements.in --output-file deploy/requirements.txt
