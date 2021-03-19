
import pytest

def pytest_addoption(parser):
	""" provide a new command line parameter """
	parser.addoption(
		"--host",
		default="localhost",
		help="host: IP addr or hostname for DUT"
	)


@pytest.fixture
def hostname(request):
	return request.config.getoption("--host")
