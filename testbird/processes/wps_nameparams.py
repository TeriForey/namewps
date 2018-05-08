from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput, BoundingBoxInput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata

from testbird.write_inputfile import generate_inputfile
from testbird.write_scriptfile import write_file
from testbird.utils import daterange

from datetime import datetime, timedelta
import os
import stat
import shutil

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
            LiteralInput('title', 'Title of run', data_type='string',
                         abstract="Title of run"),
            LiteralInput('longitude', 'Longitude', data_type='float',
                         abstract="Location of release",
                         default=-24.867222),
            LiteralInput('latitude', 'Latitude', data_type='float',
                         abstract="Location of release",
                         default=16.863611),
            BoundingBoxInput('domain', 'Domain coordinates', crss=['epsg:4326'],
                         abstract='Coordinates to search within',
                         min_occurs=1),
            LiteralInput('elevation','Elevation', data_type='integer',
                         abstract = "release elevation, m agl for land, m asl for marine release",
                         default=10, min_occurs=0),
            LiteralInput('elevation_range_min','Elevation Range Min', data_type='integer',
                         abstract="Minimum range of elevation",
                         default=None, min_occurs=0),
            LiteralInput('elevation_range_max', 'Elevation Range Max', data_type='integer',
                         abstract = "Maximum range of elevation",
                         default=None, min_occurs=0),

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
                         default='0-100', min_occurs=1, max_occurs=4), # I want ranges, so going to use string format then process the results.
            LiteralInput('resolution','Resolution', data_type='float',
                         abstract='degrees, note the UM global Met data was only 17Km resolution',
                         allowed_values=[0.05,0.25], default=0.25, min_occurs=0),
            LiteralInput('timestamp','timestamp of runs', data_type='string',
                         abstract='how often the prog will run?',
                         allowed_values=['3-hourly','daily']),
            LiteralInput('dailytime','daily run time', data_type='time',
                         abstract='if running daily, at what time will it run',
                         min_occurs = 0),
            LiteralInput('startdate', 'Start date of runs', data_type='date',
                         abstract='start date of runs'),
            LiteralInput('enddate', 'End date of runs', data_type='date',
                         abstract = 'end date of runs'),
            ]
        outputs = [
            LiteralOutput('FileDir', 'Output file directory', data_type='string',
                          abstract='Location of output files'),
            ComplexOutput('FileContents', 'Output files (zipped)',
                          abstract="Output files (zipped)",
                          supported_formats=[Format('application/x-zipped-shp')]),
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

        LOGGER.debug("domains: %s" % (request.inputs['domain'][0].data))
        domains = []
        for val in request.inputs['domain'][0].data:
            ## Values appear to be coming in as minY, minX, maxY, maxX
            domains.append(float(val))

        # Process the string of domains into a list of floats.
        # domains = []
        # if ',' not in request.inputs['domain'][0].data:
        #     raise InvalidParameterValue("The domain coordinates must be split using a ','")
        # for val in request.inputs['domain'][0].data.split(','):
        #     domains.append(float(val))
        # if len(domains) != 4:
        #     raise InvalidParameterValue("There must be four coordinates entered, minX,maxX,minY,maxY")

        # Might want to change the elevation input to something similar to this as well so we don't have three separate params

        params = dict()
        for p in request.inputs:
            if p == 'elevationOut':
                params[p] = ranges
            elif p == 'domain':
                params[p] = domains
            else:
                params[p] = request.inputs[p][0].data

        runtype = "FWD"
        if params['runBackwards']:
            runtype = "BCK"

        outputdir = os.path.join("/home/t/trf5/birdhouse/testoutputs", "{}_{}_{}".format(runtype, params['timestamp'], params['title']))
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        # Will loop through all the dates in range, including the final day
        for cur_date in daterange(request.inputs['startdate'][0].data,
                                  request.inputs['enddate'][0].data + timedelta(days=1)):
            with open(os.path.join(outputdir, "{}Run_{}_{}.txt".format(runtype, params['title'],
                                               datetime.strftime(cur_date, "%Y%m%d"))), 'w') as fout:
                fout.write(generate_inputfile(params, cur_date))

        with open(os.path.join(outputdir, 'script.sh'), 'w') as fout:
            fout.write(write_file(params))

        st = os.stat(os.path.join(outputdir, 'script.sh'))
        os.chmod(os.path.join(outputdir, 'script.sh'), st.st_mode | 0111)

        response.outputs['FileDir'].data = outputdir

        # Zip all the output files into one directory to be served back to the user.
        zippedfile = "{}_{}_{}".format(runtype, params['timestamp'], params['title'])
        shutil.make_archive(zippedfile, 'zip', outputdir)

        response.outputs['FileContents'].file = zippedfile+'.zip'

        response.update_status("done", 100)
        return response
