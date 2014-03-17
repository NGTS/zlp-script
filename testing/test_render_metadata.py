from ngts_catalogue.metadata import Metadata
import pytest
import json

Metadata.filename = '/tmp/metadata.json'

@pytest.fixture
def success():
    return {
            'success': True,
            'pv2_1': 13.2,
            'pv2_3': 14.2,
            'pv2_5': 15.2,
            }

@pytest.fixture
def failure():
    return {'success': False, 
            'reason': 'Failed to solve wcs',
            }

def verify(passed):
    with open(Metadata.filename) as infile:
        assert json.load(infile) == passed

def test_success_case(success):
    passed = [success]
    m = Metadata(passed).render()
    verify(passed)


def test_failure_case(failure):
    passed = [failure]
    m = Metadata(passed).render()
    verify(passed)

def test_both_cases(success, failure):
    passed = [success, failure]
    m = Metadata(passed).render()
    verify(passed)
