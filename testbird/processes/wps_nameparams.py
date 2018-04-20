from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata


import logging
LOGGER = logging.getLogger("PYWPS")


class RunNAME(Process):
    """
    Notes
    -----

    This will take and regurgitate all the parameters required to run NAME.
    It should make it easier to then add in the actual process.
    """
    def __init__(self):
        inputs = [
            LiteralInput('latitude', 'Latitude', data_type='float',
                         abstract="Location of release",
                         default=43.0),
            LiteralInput('longitude','Longitude', data_type='float',
                         abstract="Location of release",
                         default=-75.0),
            LiteralInput('elevation','Elevation', data_type='integer',
                         abstract = "m agl for land, m asl for marine release",
                         default=100, min_occurs=0),
            LiteralInput('elevation_range_min','Elevation Range Min', data_type='integer',
                         abstract="Minimum range of elevation",
                         default=None, min_occurs=0),
            LiteralInput('elevation_range_max', 'Elevation Range Max', data_type='integer',
                         abstract = "Maximum range of elevation",
                         default=None, min_occurs=0),
            LiteralInput('title', 'Title of run', data_type='string',
                         abstract = "Title of run"),
            LiteralInput('runBackwards', 'Run Backwards', data_type='boolean',
                         abstract = 'Whether to run backwards in time (default) or forwards',
                         default = '1', min_occurs=0),
            LiteralInput('time', 'Time to run model over', data_type='integer',
                         abstract = 'Time',
                         default=1),
            LiteralInput('timeFmt','Time format', data_type='string',
                         abstract='choose whether to measure time in hours or days',
                         allowed_values = ['days','hours'], default='days'),
            LiteralInput('elevationOut', 'Elevation averaging ranges', data_type='string',
                         abstract='Elevation range where the particle number is counted (m agl)'
                                  " Example: 0-100",
                         max_occurs=4), # I want ranges, so going to use string format then process the results.
            LiteralInput('resolution','Resolution', data_type='float',
                         abstract='degrees, note the UM global Met data was only 17Km resolution',
                         allowed_values=[0.05,0.25], default=0.25, min_occurs=0),
            LiteralInput('timestamp','timestamp of runs', data_type='string',
                         abstract='how often the prog will run?',
                         allowed_values=['3-hourly','daily']),
            LiteralInput('dailytime','daily run time', data_type='time',
                         abstract='if running daily, at what time will it run'),
            LiteralInput('startdate', 'Start date of runs', data_type='date',
                         abstract='start date of runs'),
            LiteralInput('enddate', 'End date of runs', data_type='date',
                         abstract = 'end date of runs'),
            ]
        outputs = [
            ComplexOutput('output', 'params',
                          abstract="Input parameters in JSON format",
                          as_reference=True,
                          supported_formats=[Format('text/plain')],
                          ),
            ]

        super(RunNAME, self).__init__(
            self._handler,
            identifier='runname',
            title='Run NAME-on-JASMIN',
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


        # Might want to change the elevation input to something similar to this as well so we don't have three separate params

        params = []
        for p in request.inputs:
            if p == 'elevationOut':
                params.append([p, ranges])
            else:
                params.append([p, request.inputs[p][0].data])

        with open('out.txt', 'w') as fout:
            fout.write(str(params))
            response.outputs['output'].file = fout.name
        response.update_status("done", 100)
        return response
