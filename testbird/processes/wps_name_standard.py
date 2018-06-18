from pywps import Process
from pywps import ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata

from testbird.run_name import run_name
from datetime import timedelta

import logging
LOGGER = logging.getLogger("PYWPS")


class RunNAMEstandard(Process):
    """
    Notes
    -----

    This will take and regurgitate all the parameters required to run NAME.
    It should make it easier to then add in the actual process.
    """
    def __init__(self):
        inputs = [
            LiteralInput('title', 'Release Station', data_type='string',
                         abstract="standard location of release",
                         allowed_values=[
                            'Cape Verde',
                            'Beijing Tower',
                            'Beijing Pinggu',
                            'Delhi, Kashmere gate',
                            'Bachok, Malaysia',
                            'Cape Fuguei, Taiwan',
                            'Ho Chi Minh City, Vietnam',
                            'Hanoi, Vietnam',
                            'Halley',
                            'Weybourne',
                            'BT Tower (150m)',
                            'North Kensington',
                            'Penlee (PML)']),
            LiteralInput('runBackwards', 'Run Backwards', data_type='boolean',
                         abstract = 'Whether to run backwards in time or forwards',
                         default = '1', min_occurs=0),
            LiteralInput('time', 'Run Time', data_type='integer',
                         abstract = 'Number of days model will run over',
                         allowed_values=[1,5,10,12], default=1, min_occurs=0),
            LiteralInput('elevationOut', 'Output elevation averaging ranges', data_type='string',
                         abstract='Elevation range where the particle number is counted (m agl)'
                                  " Example: 0-100",
                         default='0-100', min_occurs=1, max_occurs=4), # I want ranges, so going to use string format then process the results.
            LiteralInput('resolution','Resolution', data_type='float',
                         abstract='degrees, note the UM global Met data was only 17Km resolution',
                         allowed_values=[0.05,0.25], default=0.25, min_occurs=0),
            LiteralInput('startdate', 'Start date of runs', data_type='date',
                         abstract='start date of runs (YYYY-MM-DD)'),
            LiteralInput('enddate', 'End date of runs', data_type='date',
                         abstract = 'end date of runs (YYYY-MM-DD)')
            ]
        outputs = [
            LiteralOutput('runid', 'Run ID', data_type='string',
                          abstract='Unique run identifier, this is needed to create plots'),
            ComplexOutput('FileContents', 'Output files (zipped)',
                          abstract="Output files (zipped)",
                          supported_formats=[Format('application/x-zipped-shp')],
                          as_reference=True),
            ComplexOutput('ExamplePlot', 'Example Plot of initial time point',
                          abstract='Example plot of initial time point',
                          supported_formats=[Format('image/tiff')],
                          as_reference=True),
            ]

        super(RunNAMEstandard, self).__init__(
            self._handler,
            identifier='runnamestd',
            title='Run NAME-on-JASMIN - Standard',
            abstract="Run NAME 3-hourly from a choice of standard release locations",
            version='0.1',
            metadata=[
                Metadata('NAME-on-JASMIN guide', 'http://jasmin.ac.uk/jasmin-users/stories/processing/'),
            ],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):

        # Need to process the elevationOut inputs from a list of strings, into an array of tuples.
        ranges = []
        for elevationrange in request.inputs['elevationOut']:
            if '-' in elevationrange.data:
                minrange, maxrange = elevationrange.data.split('-')
                ranges.append((int(minrange), int(maxrange))) # need to error catch int() and min < max
            else:
                raise InvalidParameterValue(
                    'The value "{}" does not contain a "-" character to define a range, '
                    'e.g. 0-100'.format(elevationrange.data))

        params = dict()
        for p in request.inputs:
            if p == 'elevationOut':
                params[p] = ranges
            else:
                params[p] = request.inputs[p][0].data

        # Need to test start and end dates make sense relative to each other
        if params['startdate'] >= params['enddate'] + timedelta(days=1):
            raise InvalidParameterValue("The end date is earlier than the start date!")

        if (params['enddate'] + timedelta(days=1)) - params['startdate'] >= timedelta(days=93):
            raise InvalidParameterValue("Can only run across a maximum of three months in one go")

        params['elevation'] = 10
        params['timeFmt'] = "days"
        params['timestamp'] = '3-hourly'

        if params['title'] == "Cape Verde":
            params['longitude'] = -24.867222
            params['latitude'] = 16.863611
            params['domain'] = [-30.0, -120.0, 90.0, 80.0] # minY,minX,maxY,maxX
        elif params['title'] == "Beijing Tower":
            params['longitude'] = 116.377
            params['latitude'] = 39.975
            if params['time'] == 1:
                params['domain'] = [-10.0, 40.0, 80.0, 180.0]
            elif params['time'] == 5:
                params['domain'] = [-10.0, 10.0, 90.0, 180.0]
            elif params['time'] == 10:
                params['domain'] = [-10.0, -60.0, 90.0, 180.0]
        elif params['title'] == 'Halley':
            params['longitude'] = 26.16667
            params['latitude'] = -75.58333
            params['domain'] = [-90.0, -179.875, 0.0, 179.9]
        elif params['title'] == 'Weybourne':
            params['longitude'] = 1.1219
            params['latitude'] = 52.9503
            params['domain'] = [20.0, -140.0, 90.0, 90.0]
        elif params['title'] == 'North Kensington':
            params['longitude'] = -0.154988
            params['latitude'] = 51.522398
            params['domain'] = [20.0, -140.0, 90.0, 90.0]
        elif params['title'] == 'Penlee (PML)':
            params['longitude'] = -4.1931
            params['latitude'] = 50.3189
            params['domain'] = [20.0, -100.0, 90.0, 80.0]
        elif params['title'] == 'Beijing Pinggu':
            params['longitude'] = 117.0406996
            params['latitude'] = 40.1659
            if params['time'] == 1:
                params['domain'] = [-10.0, 40.0, 80.0, 180.0]
            elif params['time'] == 5:
                params['domain'] = [-10.0, 10.0, 90.0, 180.0]
            elif params['time'] == 10:
                params['domain'] = [-10.0, -60.0, 90.0, 180.0]
        elif params['title'] == 'BT Tower (150m)':
            params['longitude'] = -0.13888
            params['latitude'] = 51.5215
            params['domain'] = [20.0, -140.0, 90.0, 90.0]
            params['elevation'] = 150
        elif params['title'] == 'Delhi, Kashmere gate':
            params['longitude'] = 77.23184
            params['latitude'] = 28.6644
            params['domain'] = [-20.0, 0.0, 60.0, 180.0]
        elif params['title'] == "Bachok, Malaysia":
            params['longitude'] = 102.425
            params['latitude'] = 6.009
            params['domain'] = [-45.0, 65.0, 80.0, 195.0]
        elif params['title'] == 'Cape Fuguei, Taiwan':
            params['longitude'] = 121.538
            params['latitude'] = 25.297
            params['domain'] = [-45.0, 65.0, 80.0, 195.0]
        elif params['title'] == 'Ho Chi Minh City, Vietnam':
            params['longitude'] = 106.4057
            params['latitude'] = 10.4544
            params['domain'] = [-45.0, 65.0, 80.0, 195.0]
        elif params['title'] == 'Hanoi, Vietnam':
            params['longitude'] = 105.4902
            params['latitude'] = 21.0024
            params['domain'] = [-45.0, 65.0, 80.0, 195.0]

        response.update_status("Processed parameters", 5)

        outdir, zippedfile, mapfile = run_name(params, response)

        response.outputs['FileContents'].file = zippedfile + '.zip'
        response.outputs['runid'].data = outdir
        response.outputs['ExamplePlot'].file = mapfile

        response.update_status("done", 100)
        return response
