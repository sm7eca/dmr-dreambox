
import pytest
import requests
from typing import Dict


def test_sysinfo():
	response = requests.get(url="http://localhost/system/info")
	assert response.status_code == 200

def test_docs():
	response = requests.get(url="http://localhost/docs")
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
	response = requests.get(url=f"http://localhost/repeater/master/{master_id}?limit=5&skip=0")
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len


@pytest.mark.parametrize(
	argnames="call_sign,expected_status,expected_len",
	argvalues=[
		("PI1SPA", 200, 1),
		("DL7MCK", 204, 0)
	],
	ids=[
		"valid_callsign",
		"invalid_callsign"
	]
)
def test_repeater_callsign(call_sign: str, expected_status: int, expected_len: int):
	response = requests.get(url=f"http://localhost/repeater/callsign/{call_sign}")
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert len(response.json()) == expected_len



@pytest.mark.parametrize(
	argnames="dmr_id,expected_status,expected_len",
	argvalues=[
		(204342, 200, 1),
		(999999, 204, 0),
		(240701, 200, 1)
	],
	ids=[
		"valid_dmr_id",
		"invalid_dmr_id",
		"check_tgs"
	]
)
def test_repeater_dmrid(dmr_id: int, expected_status: int, expected_len: int):
	response = requests.get(url=f"http://localhost/repeater/dmr/{dmr_id}")
	assert response.status_code == expected_status
	if response.status_code == 200:
		assert not isinstance(response.json(), list)
		assert isinstance(response.json(), dict)
		
		# check talk groups
		repeater = response.json()
		assert isinstance(repeater['tg'], list)

		# check max_ts
		assert repeater['max_ts'] == len(set([tg['ts'] for tg in repeater['tg']]))
		
		# ensure that we have removed "ts" from Repeater response model
		assert "ts" not in repeater.keys()

		# check whether we have removed repeater ID and master ID from TG
		for tg in repeater["tg"]:
			assert "master_id" not in tg.keys(), "unexpected key \"master_id\""
			assert "rep_id" not in tg.keys(), "unexpected key \"rep_id\""


def test_repeater_location():
	response = requests.get(url=f"http://localhost/repeater/location?city=Gothenburg&country=SE&distance=40")
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
	response = requests.get(url=f"http://localhost/hotspot/callsign/{callsign}")
	assert response.status_code == expected_status


def test_redirect_root():
	"""Given a GET request sent towards root, we expect to be redirected to /docs"""

	# call the UUT
	response = requests.get(url=f"http://localhost", allow_redirects=True)
	
	# assert results
	assert response.status_code == 200
	assert response.url == "http://localhost/docs"
	assert response.history[0].is_redirect
	assert response.history[0].status_code == 307
