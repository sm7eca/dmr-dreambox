
import pytest
import requests
from time import sleep
from typing import Dict

BASE_URL = "http://localhost/api/v1"


def test_sysinfo():
	response = requests.get(url=f"{BASE_URL}/system/info")
	assert response.status_code == 200

def test_docs():
	response = requests.get(url=f"{BASE_URL}/docs")
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
def test_repeater_master(master_id: int, expected_status: int, expected_len: int):
	response = requests.get(url=f"{BASE_URL}/repeater/master/{master_id}?limit=5&skip=0")
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len


@pytest.mark.parametrize(
	argnames="call_sign,expected_status,expected_len",
	argvalues=[
		("PI1SPA", 200, 1),
		("DL7MCK", 204, 0),
		("AVQ", 200, 2)
	],
	ids=[
		"callsign_valid",
		"callsign_invalid",
		"callsign_regex"
	]
)
def test_repeater_callsign(call_sign: str, expected_status: int, expected_len: int):
	response = requests.get(url=f"{BASE_URL}/repeater/callsign/{call_sign}")
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len

def test_invalid_api_endpoint_exception_covered():
	response = requests.get(url=f"{BASE_URL}/repeater/dmr/A87987d9a8s7d9?lim=12")
	assert response.status_code == 404

def test_no_repeater_dmr_id():
	response = requests.get(url=f"{BASE_URL}/repeater/dmr/2407099")
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
def test_repeater_dmrid(dmr_id: int, expected_status: int, expected_len: int):
	response = requests.get(url=f"{BASE_URL}/dmr/{dmr_id}")
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
	response = requests.get(url=f"{BASE_URL}/repeater/location?city=Gothenburg&country=SE&distance=40")
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
def test_hotspot(callsign: str, expected_status: int):
	"""
	Given a valid callsign, we expected that will receive a number of hotspots
	"""
	response = requests.get(url=f"{BASE_URL}/hotspot/callsign/{callsign}")
	assert response.status_code == expected_status


def test_redirect_root():
	"""Given a GET request sent towards root, we expect to be redirected to /docs"""

	# call the UUT
	response = requests.get(url=BASE_URL, allow_redirects=True)

	# assert results
	assert response.status_code == 200
	assert response.url == f"{BASE_URL}/docs"
	assert response.history[0].is_redirect
	assert response.history[0].status_code == 301


@pytest.mark.parametrize(
	argnames="longitude,latitude,distance,limit,expected_status",
	argvalues=[
		(12.4605814, 56.8984846, 99, None, 200),
		(12.4605814, 56.8984846, 99, 5, 200),
		(12.4605814, 56.8984846, 300, 5, 422)
	],
	ids=[
		"falkenberg+99,no-limit",
		"falkenberg+99,limit:5",
		"falkenberg+99,distance-invalid"
	]
)
def test_repeater_location(longitude, latitude, distance, limit, expected_status):
	"""
	Given a location in Falkenberg, there is no DMR enabled
	repeater in that area
	"""

	req_url = f"{BASE_URL}/repeater/location" + \
				 f"?longitude={longitude}&latitude={latitude}&distance={distance}"

	if limit:
		req_url += f"&limit={limit}"

	response = requests.get(url=req_url)

	# assert results
	assert response.status_code == expected_status

	if limit and expected_status == 200:
		assert response.json()
		assert len(response.json()) == limit

def test_request_limiter():
	"""
	Given that we have configured the NGINX proxy with request limiting
	we should never receive 503, instead requests are delayed before served
	"""
	sleep(4)
	counter = 20
	url = f"{BASE_URL}/system/info"
	while counter > 0:
		counter -= 1
		response = requests.get(url=url)
		if response.status_code != 200:
			break

		continue

	assert counter <= 11, "we expect 9 request/s to be handled before receiving 503"
