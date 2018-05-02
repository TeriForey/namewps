from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput, BoundingBoxInput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata

from testbird.write_inputfile import generate_inputfile
from testbird.write_scriptfile import write_file
from testbird.utils import daterange

from datetime import datetime, timedelta
import shutil
import os

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
                         allowed_values=[1,5,10]),
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
                          supported_formats=[Format('application/x-zipped-shp')]),
            ]

        super(RunNAMEstandard, self).__init__(
            self._handler,
            identifier='runnamestd',
            title='Run standard NAME-on-JASMIN',
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

        params = dict()
        for p in request.inputs:
            if p == 'elevationOut':
                params[p] = ranges
            else:
                params[p] = request.inputs[p][0].data

        if params['title'] == "CAPEVERDE":
            params['longitude'] = 16.863611
            params['latitude'] = -24.867222
            params['domain'] = [-30.0, -120.0, 90.0, 80.0] # minY,minX,maxY,maxX
        elif params['title'] == "BEIJING":
            params['longitude'] = 100.9
            params['latitude'] = 36.28
            params['domain'] = [-10.0, 30.0, 80.0, 170.0]

        params['elevation'] = 100
        params['timeFmt'] = "days"
        params['timestamp'] = '3-hourly'


        runtype = "FWD"
        if params['runBackwards']:
            runtype = "BCK"

        outputdir = os.path.join("/home/t/trf5/birdhouse/testoutputs",
                                 "{}_{}_{}".format(runtype, params['timestamp'], params['title']))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        # Will loop through all the dates in range, including the final day
        for cur_date in daterange(request.inputs['startdate'][0].data,
                                  request.inputs['enddate'][0].data + timedelta(days=1)):
            with open(os.path.join(outputdir, "{}Run_{}_{}.txt".format(runtype, params['title'],
                                                                       datetime.strftime(cur_date, "%Y%m%d"))),
                      'w') as fout:
                fout.write(generate_inputfile(params, cur_date))

        with open(os.path.join(outputdir, 'script.txt'), 'w') as fout:
            fout.write(write_file(params))

        response.outputs['FileDir'].data = outputdir

        # Zip all the output files into one directory to be served back to the user.
        zippedfile = "{}_{}_{}".format(runtype, params['timestamp'], params['title'])
        shutil.make_archive(zippedfile, 'zip', outputdir)

        response.outputs['FileContents'].file = zippedfile + '.zip'

        response.update_status("done", 100)
        return response
