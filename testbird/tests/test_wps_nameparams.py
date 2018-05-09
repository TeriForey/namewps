import pytest

from pywps import Service
from pywps.tests import assert_response_success

from testbird.tests.common import client_for
from testbird.processes.wps_nameparams import RunNAME


@pytest.mark.skip
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
        "-180,80,-90,90"
    )
    print datainputs
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='runname',
        datainputs=datainputs)
    print resp.data
    assert_response_success(resp)
