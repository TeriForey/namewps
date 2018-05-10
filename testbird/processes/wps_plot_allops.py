from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput, BoundingBoxInput
from pywps.exceptions import InvalidParameterValue
from pywps.app.Common import Metadata

from testbird.write_inputfile import generate_inputfile
from testbird.write_scriptfile import write_file
from testbird.utils import daterange
from testbird.run_name import run_name
from pynameplot import Name, drawMap, Sum
from pynameplot.namereader import util

from datetime import datetime, timedelta
import shutil
import os

import logging
LOGGER = logging.getLogger("PYWPS")


class PlotAll(Process):
    """
    Notes
    -----

    From a directory of NAME output files we can generate all possible plots
    """
    def __init__(self):
        inputs = [
            LiteralInput('filelocation', 'Output file location', data_type='string',
                         abstract="Run ID that identifies the output file locations"),
            LiteralInput('timestamp', 'Plot specific timestamp', data_type='dateTime',
                         abstract="Plot only a specific date and time. Excludes the creation of summary plots",
                         min_occurs=0),
            LiteralInput('summarise', 'Summarise by', data_type='string',
                         abstract='Plot summaries of each day/week/month/year',
                         allowed_values=['NA', 'day', 'week', 'month', 'year', 'all'], default='NA'),
            LiteralInput('station', 'Release location', data_type='string',
                         abstract='Location of release (X, Y)', min_occurs=0)
            ]
        outputs = [
            ComplexOutput('FileContents', 'All plot files (zipped)',
                          abstract="All plot files (zipped)",
                          supported_formats=[Format('application/x-zipped-shp')],
                          as_reference=True),
            # ComplexOutput('SinglePlot', 'A single output plot',
            #               abstract='One output plot',
            #               supported_formats=[Format('image/tiff')],
            #               as_reference=True),
            ]

        super(PlotAll, self).__init__(
            self._handler,
            identifier='plotall',
            title='Plot NAME results - advanced',
            abstract="PNG plots are generated from the NAME output files",
            version='0.1',
            metadata=[
                Metadata('NAME-on-JASMIN guide', 'http://jasmin.ac.uk/jasmin-users/stories/processing/'),
            ],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):


        plotoptions = {}
        plotoptions['outdir'] = "Allplots"
        for p in request.inputs:
            if p == "timestamp" or p == "filelocation" or p == "summarise":
                continue
            plotoptions[p] = request.inputs[p][0].data

        outdir = "Allplots"

        if request.inputs['summarise'][0].data == 'week':
            s = Sum(request.inputs['filelocation'][0].data)
            column = 'total'
            for week in range(1, 52):
                s.sumWeek(week)
                if len(s.files) == 0:
                    LOGGER.debug("No files found for week %s" % (week))
                    continue
                plotoptions['caption'] = "{} {} {} {}: {} week {} sum".format(s.runname, s.averaging, s.altitude,
                                                                              s.direction, s.year, week)
                plotoptions['outfile'] = "{}_{}_{}_weekly.png".format(s.runname, s.year, week)
                drawMap(s, column, **plotoptions)
        else:
            for filename in os.listdir(request.inputs['filelocation'][0].data):
                if filename.endswith('.txt'):
                    if request.inputs['summarise'][0].data == 'day':
                        s = Sum(request.inputs['filelocation'][0].data)
                        date = util.shortname(filename)
                        s.sumDay(date)
                        plotoptions['caption'] = "{} {} {} {}: {}{}{} day sum".format(s.runname, s.averaging,
                                                                                      s.altitude, s.direction,
                                                                                      s.year, s.month, s.day)
                        plotoptions['outfile'] = "{}_{}{}{}_daily.png".format(s.runname, s.year, s.month, s.day)
                        drawMap(s, 'total', **plotoptions)
                    elif request.inputs['summarise'][0].data == 'NA':
                        n = Name(os.path.join(request.inputs['filelocation'][0].data, filename))
                        if 'timestamp' in request.inputs:
                            timestamp = datetime.strftime(request.inputs['timestamp'][0].data, "%d/%m/%Y %H:%M UTC")
                            LOGGER.debug("Reformatted time: %s" % (timestamp))
                            if timestamp in n.timestamps:
                                drawMap(n, timestamp, **plotoptions)
                        else:
                            for column in n.timestamps:
                                drawMap(n, column, **plotoptions)

        zippedfile = "plots"
        shutil.make_archive(zippedfile, 'zip', outdir)

        LOGGER.debug("Zipped file: %s (%s bytes)" % (zippedfile+'.zip', os.path.getsize(zippedfile+'.zip')))

        response.outputs['FileContents'].file = zippedfile + '.zip'

        response.update_status("done", 100)
        return response
