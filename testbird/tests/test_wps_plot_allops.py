import pytest

from pywps import Service
from pywps.tests import assert_response_success

from testbird.tests.common import client_for
from testbird.processes.wps_plot_allops import PlotAll


@pytest.mark.online
def test_wps_plot_allops_simple():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={}".format(
        "BCK_3-hourly_CAPEVERDE",
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_timestamp():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};timestamp={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "2017-11-01 12:00"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_daysum():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};summarise={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "day"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_weeksum():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};summarise={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "week"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_monthsum():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};summarise={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "month"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_allsum():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};summarise={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "all"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)


@pytest.mark.online
def test_wps_plot_allops_noplotcreated():
    client = client_for(Service(processes=[PlotAll()]))
    datainputs = "filelocation={};timestamp={}".format(
        "BCK_3-hourly_CAPEVERDE",
        "2018-05-12 13:00"
    )
    resp = client.get(
        service='wps', request='execute', version='1.0.0',
        identifier='plotall',
        datainputs=datainputs)
    assert_response_success(resp)
