
import pytest
import requests
from time import sleep
from typing import Dict

API_ROOT = "api/v1"


def test_sysinfo(hostname):
	url = f"http://{hostname}/{API_ROOT}/system/info"
	response = requests.get(url=url)
	assert response.status_code == 200
	assert response.json()
	data = response.json()
	assert "user" in data.keys()
	assert "repeater" in data.keys()

def test_docs(hostname):
	url = f"http://{hostname}/{API_ROOT}/docs"
	response = requests.get(url=url)
	assert response.status_code == 200


@pytest.mark.parametrize(
	argnames="master_id,expected_status,expected_len",
	argvalues=[
		(2401, 200, 5),
		(0, 422, 0)
	],
	ids=[
		"valid master_id",
		"invalid master_id"
	]
)
def test_repeater_master(master_id: int, expected_status: int, expected_len: int, hostname):
	url = f"http://{hostname}/{API_ROOT}/repeater/master/{master_id}?limit=5&skip=0"
	response = requests.get(url=url)
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len


@pytest.mark.parametrize(
	argnames="call_sign,expected_status,expected_len",
	argvalues=[
		("PI1SPA", 200, 1),
		("DL7MCK", 204, 0),
		("AVQ", 204, 2)
	],
	ids=[
		"callsign_valid",
		"callsign_invalid_204",
		"callsign_short_204"
	]
)
def test_repeater_callsign(call_sign: str, expected_status: int, expected_len: int, hostname):
	url = f"http://{hostname}/{API_ROOT}/repeater/callsign/{call_sign}"
	response = requests.get(url=url)
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len

def test_invalid_api_endpoint_exception_covered(hostname):
	url = f"http://{hostname}/{API_ROOT}/repeater/dmr/A87987d9a8s7d9?lim=12"
	response = requests.get(url)
	assert response.status_code == 404

def test_no_repeater_dmr_id(hostname):
	url = f"http://{hostname}/{API_ROOT}/repeater/dmr/2407099"
	response = requests.get(url)
	assert response.status_code == 404

@pytest.mark.parametrize(
	argnames="dmr_id,expected_status,expected_len",
	argvalues=[
		(204342, 200, 1),
		(999999, 204, 0),
		(240701, 200, 1),
		(240048111, 200, 1)
	],
	ids=[
		"valid_dmr_id",
		"invalid_dmr_id",
		"check_tgs",
		"check_hotspot"
	]
)
def test_repeater_dmrid(dmr_id: int, expected_status: int, expected_len: int, hostname):
	url = f"http://{hostname}/{API_ROOT}/dmr/{dmr_id}"
	response = requests.get(url)
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert not isinstance(response.json(), list)
		assert isinstance(response.json(), dict)

		# check talk groups
		repeater = response.json()
		assert isinstance(repeater, dict)

		assert "num_tg" in repeater.keys()
		assert "tg" in repeater.keys()

		assert isinstance(repeater['tg'], list)
		assert len(repeater['tg']) == repeater['num_tg']

		# check max_ts
		assert repeater['max_ts'] == len(set([tg['ts'] for tg in repeater['tg']]))

		# ensure that we have removed "ts" from Repeater response model
		assert "ts" not in repeater.keys()

		# check whether we have removed repeater ID and master ID from TG
		for tg in repeater["tg"]:
			assert "master_id" not in tg.keys(), "unexpected key \"master_id\""
			assert "rep_id" not in tg.keys(), "unexpected key \"rep_id\""


def test_repeater_location():
	url = f"http://{hostname}/{API_ROOT}/repeater/location?city=Gothenburg&country=SE&distance=40"
	response = requests.get(url)
	assert response.status_code == 501


@pytest.mark.parametrize(
	argnames="callsign,expected_status",
	argvalues=[
		("PI1SPA", 204),
		("SM7ECA", 200)
	],
	ids=[
		"invalid callsign",
		"valid callsign"
	]
)
def test_hotspot(callsign: str, expected_status: int, hostname):
	"""
	Given a valid callsign, we expected that will receive a number of hotspots
	"""
	url = f"http://{hostname}/{API_ROOT}/hotspot/callsign/{callsign}"
	response = requests.get(url)
	assert response.status_code == expected_status


def test_redirect_root(hostname):
	"""Given a GET request sent towards root, we expect to be redirected to /docs"""

	# call the UUT
	url = f"http://{hostname}/{API_ROOT}"
	response = requests.get(url=url, allow_redirects=True)

	# assert results
	assert response.status_code == 200
	assert response.url == f"{url}/docs"
	assert response.history[0].is_redirect
	assert response.history[0].status_code == 301


@pytest.mark.parametrize(
	argnames="qth,long,lat,distance,limit,expected_status",
	argvalues=[
		("Jo67AP18", None, None, 99, None, 200),
		("JO67AP", None, None, 99, 3, 200),
		("JO67AP", None, None, 300, 5, 422),
		("JO6", None, None, 90, 5, 422),
		(None, 12.033, 57.7601, 90, 5, 200),
		(None, None, None, 90, None, 422)
	],
	ids=[
		"qth,Moelndal+99,valid,no-limit",
		"qth,Moelndal+99,valid,limit3",
		"qth,Moelndal+300,invalid-distance",
		"qth,Moelndal,invalid_format",
		"loc,Moelndal,",
		"invalid,noQth,noLoc"
	]
)
def test_repeater_location(qth, long, lat, distance, limit, expected_status, hostname):
	"""
	Given a location in Falkenberg, there is no DMR enabled
	repeater in that area
	"""
	url = f"http://{hostname}/{API_ROOT}"
	if qth:
		req_url = f"{url}/repeater/location" + \
				    f"?qth_locator={qth}&distance={distance}"
	elif long and lat:
		req_url = f"{url}/repeater/location" + \
				    f"?longitude={long}&latitude={lat}&distance={distance}"
	else:
		req_url = f"{url}/repeater/location"

	if limit:
		req_url += f"&limit={limit}"

	response = requests.get(url=req_url)

	# assert results
	assert response.status_code == expected_status

	if limit and expected_status == 200:
		assert response.json()
		assert len(response.json()) == limit

@pytest.mark.parametrize(
	argnames="dmr_id, expected_status",
	argvalues=[
		(2400011, 200),
		(0, 422)
	],
	ids=[
		"valid => 200",
		"invalid => 422"
	]
)
def test_user_dmrid(dmr_id, expected_status, hostname):
	"""
	Given a valid user DMR ID, I expect the UUT to return a User response
	"""
	sleep(2)
	req_url = f"http://{hostname}/{API_ROOT}/user/{dmr_id}"

	response = requests.get(url=req_url)

	assert response.status_code == expected_status
	if expected_status == 200:
		assert response.json()
		data = response.json()
		assert data['call_sign'] == "SM0TSC"

def test_request_limiter(hostname):
	"""
	Given that we have configured the NGINX proxy with request limiting
	we should never receive 503, instead requests are delayed before served
	"""
	sleep(4)
	counter = 20
	url = f"http://{hostname}/{API_ROOT}/system/info"
	while counter > 0:
		counter -= 1
		response = requests.get(url=url)
		if response.status_code != 200:
			break

		continue

	assert counter <= 11, "we expect 9 request/s to be handled before receiving 503"
