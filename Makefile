test:
	cd tests/test_project && pip install -r requirements.txt && cd ../.. && pytest

install_testapp:
	cd tests/test_project && pip install -r requirements.txt