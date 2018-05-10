from pywps import Process
from pywps import ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata

from testbird.run_name import run_name

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
                         abstract="Weather station of release",
                         allowed_values=['CAPEVERDE','BEIJING']),
            LiteralInput('runBackwards', 'Run Backwards', data_type='boolean',
                         abstract = 'Whether to run backwards in time (default) or forwards',
                         default = '1', min_occurs=0),
            LiteralInput('time', 'Time to run model over', data_type='integer',
                         abstract = 'Number of days model will run over',
                         allowed_values=[1,5,10], default=1, min_occurs=0),
            LiteralInput('elevationOut', 'Elevation averaging ranges', data_type='string',
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
            LiteralOutput('FileDir', 'Output file directory', data_type='string',
                          abstract='Location of output files'),
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
            abstract="Passes input arguments onto NAME",
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

        if params['title'] == "CAPEVERDE":
            params['longitude'] = -24.867222
            params['latitude'] = 16.863611
            params['domain'] = [-30.0, -120.0, 90.0, 80.0] # minY,minX,maxY,maxX
        elif params['title'] == "BEIJING":
            params['longitude'] = 100.9
            params['latitude'] = 36.28
            params['domain'] = [-10.0, 30.0, 80.0, 170.0]

        params['elevation'] = 10
        params['timeFmt'] = "days"
        params['timestamp'] = '3-hourly'

        outdir, zippedfile, mapfile = run_name(params)

        response.outputs['FileContents'].file = zippedfile + '.zip'
        response.outputs['FileDir'].data = outdir
        response.outputs['ExamplePlot'].file = mapfile

        response.update_status("done", 100)
        return response
