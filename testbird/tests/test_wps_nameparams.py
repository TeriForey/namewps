import pytest

from pywps import Service
from pywps.tests import assert_response_success

from testbird.tests.common import client_for
from testbird.processes.wps_nameparams import RunNAME


@pytest.mark.skip(reason="need to figure out how bounding box is output")
def test_wps_nameparams():
    client = client_for(Service(processes=[RunNAME()]))
    datainputs = "title={};runBackwards={};time={};elevationOut={};resolution={};startdate={};enddate={};" \
                 "domain={}".format(
        "CAPEVERDE",
        "true",
        "1",
        "0-100",
        "0.25",
        "2017-11-01",
        "2017-11-02",
        "[-180,80,-90,90]"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='runname',
        datainputs=datainputs)
    assert_response_success(resp)
