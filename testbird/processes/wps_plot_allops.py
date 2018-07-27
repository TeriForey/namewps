from pywps import Process
from pywps import ComplexOutput, Format, FORMATS
from pywps import LiteralInput
from pywps.app.Common import Metadata
from pywps.exceptions import InvalidParameterValue

from pynameplot import Name, drawMap, Sum
from pynameplot.namereader import util

from datetime import datetime
import shutil
import os
import calendar
import glob
import tempfile
from testbird.utils import getjasminconfigs, get_num_dates

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
            LiteralInput('filelocation', 'NAME run ID', data_type='string',
                         abstract="Run ID that identifies the NAME output files"),
            LiteralInput('summarise', 'Summarise data', data_type='string',
                         abstract='Plot summaries of each day/week/month',
                         allowed_values=['NA', 'day', 'week', 'month', 'all'], default='NA'),
            LiteralInput('timestamp', 'Plot specific date and time', data_type='dateTime',
                         abstract="Plot only a specific timestamp. Excludes the creation of summary plots. "
                                  "Format: YYYY-MM-DD HH:MM",
                         min_occurs=0),
            LiteralInput('station', 'Mark release location', data_type='boolean',
                         abstract='Mark the location of release onto the image',
                         min_occurs=0),
            LiteralInput('projection', 'Projection', data_type='string',
                         abstract='Map projection', allowed_values=['cyl', 'npstere', 'spstere'], min_occurs=0),
            LiteralInput('lon_bounds', 'Longitudinal boundary', data_type='string',
                         abstract='X-axis: Min and Max longitude to plot. Format: Min,Max', min_occurs=0),
            LiteralInput('lat_bounds', 'Latitudinal boundary', data_type='string',
                         abstract='Y-axis: Min and Max latitude boundary. Format: Min,Max', min_occurs=0),
            LiteralInput('scale', 'Particle concentration scale', data_type='string',
                         abstract='Particle concentration scale. If no value is set, it will autoscale. '
                                  'Format: Min,Max',
                         min_occurs=0),
            LiteralInput('colormap', 'Colour map', data_type='string',
                         abstract='Matplotlib color map name', default='coolwarm', min_occurs=0,
                         allowed_values=['coolwarm', 'viridis', 'rainbow']),
            ]
        outputs = [
            ComplexOutput('FileContents', 'Plot file(s)',
                          abstract="Plot files",
                          supported_formats=[Format('application/x-zipped-shp'),
                                             Format('text/plain'),
                                             Format('image/png'),
                                             FORMATS.GEOTIFF],
                          as_reference=True),
            ]

        super(PlotAll, self).__init__(
            self._handler,
            identifier='plotall',
            title='Plot NAME results - Concentration',
            abstract="PNG plots are generated from the NAME output files",
            version='0.1',
            metadata=[
                Metadata('NAME-on-JASMIN guide', 'http://jasmin.ac.uk/jasmin-users/stories/processing/'),
                Metadata('Colour maps', 'https://matplotlib.org/users/colormaps.html'),
            ],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):

        jasconfigs = getjasminconfigs()
        rundir = os.path.join(jasconfigs.get('jasmin', 'outputdir'), request.inputs['filelocation'][0].data)
        LOGGER.debug("Working Directory for plots: %s" % rundir)

        # Parse NAME run input params
        inputs = {}
        with open(os.path.join(rundir, 'user_input_parameters.txt'), 'r') as ins:
            for l in ins:
                data = l.rstrip().split(': ')
                inputs[data[0]] = data[1]

        # Parse input params into plot options
        plotoptions = {}
        plotoptions['outdir'] = os.path.join(rundir, "plots_{}".format(datetime.strftime(datetime.now(), "%s")))
        for p in request.inputs:
            if p == "timestamp" or p == "filelocation" or p == "summarise":
                continue
            elif p == 'lon_bounds' or p == 'lat_bounds':
                statcoords = request.inputs[p][0].data.split(',')
                plotoptions[p] = (int(statcoords[0].strip()), int(statcoords[1].strip()))
            elif p == 'scale':
                statcoords = request.inputs[p][0].data.split(',')
                plotoptions[p] = (float(statcoords[0].strip()), float(statcoords[1].strip()))
            elif p == "station" and request.inputs[p][0].data == True:
                plotoptions[p] = (float(inputs['longitude']), float(inputs['latitude']))
            else:
                plotoptions[p] = request.inputs[p][0].data

        files = glob.glob(os.path.join(rundir, 'outputs', '*_group*.txt'))
        if len(files) == 0:
            raise InvalidParameterValue("Unable to find any output files. File names must be named '*_group*.txt'")

        if 'timestamp' in request.inputs:
            request.inputs['summarise'][0].data = 'NA'

        LOGGER.debug("Plot options: %s" % plotoptions)

        response.update_status("Processed plot parameters", 5)

        tot_plots = get_num_dates(start=datetime.strptime(inputs['startdate'], "%Y-%m-%d"),
                                  end=datetime.strptime(inputs['enddate'], "%Y-%m-%d"),
                                  sum=request.inputs['summarise'][0].data,
                                  type=inputs['timestamp'])

        # We need to find all the groups and loop through them one at a time!
        groups = {}
        for filename in os.listdir(os.path.join(rundir, 'outputs')):
            groupnum = filename[14]
            try:
                groupnum = int(groupnum)
            except:
                raise Exception("Cannot identify groupnumber %s" % groupnum)

            if groupnum in groups:
                shutil.copy(os.path.join(rundir, 'outputs', filename), groups[groupnum])
            else:
                groups[groupnum] = tempfile.mkdtemp()
                shutil.copy(os.path.join(rundir, 'outputs', filename), groups[groupnum])

        ngroups = len(groups)
        tot_plots = tot_plots * ngroups
        plots_made = 0

        response.update_status("Plotting", 10)

        oldper = 10

        for groupnum, tmpdir in sorted(groups.items()):
            if request.inputs['summarise'][0].data != 'NA':
                s = Sum(tmpdir)

            if request.inputs['summarise'][0].data == 'week':
                for week in range(1, 53):
                    s.sumWeek(week)
                    if len(s.files) == 0:
                        LOGGER.debug("No files found for week %s" % week)
                        continue
                    plotoptions['caption'] = "{} {} {} {}: {} week {} sum (UTC)".format(s.runname, s.averaging,
                                                                                        s.altitude, s.direction,
                                                                                        s.year, week)
                    plotoptions['outfile'] = "{}_{}_{}_{}_weekly.png".format(s.runname, s.altitude.strip('()'),
                                                                             s.year, week)
                    try:
                        drawMap(s, 'total', **plotoptions)
                        LOGGER.debug("Plotted %s" % plotoptions['outfile'])
                    except:
                        LOGGER.error("Failed to plot %s" % plotoptions['outfile'])
                    plots_made += 1
                    newper = 10+int((plots_made/float(tot_plots))*85)
                    if oldper != newper:
                        response.update_status("Plotting", newper)
                        oldper = newper

            elif request.inputs['summarise'][0].data == 'month':
                for month in range(1, 13):
                    s.sumMonth(str(month))
                    if len(s.files) == 0:
                        LOGGER.debug("No files found for month %s" % month)
                        continue
                    plotoptions['caption'] = "{} {} {} {}: {} {} sum (UTC)".format(s.runname, s.averaging, s.altitude,
                                                                             s.direction, s.year,
                                                                             calendar.month_name[month])
                    plotoptions['outfile'] = "{}_{}_{}_{}_monthly.png".format(s.runname, s.altitude.strip('()'),
                                                                              s.year, month)
                    try:
                        drawMap(s, 'total', **plotoptions)
                        LOGGER.debug("Plotted %s" % plotoptions['outfile'])
                    except:
                        LOGGER.error("Failed to plot %s" % plotoptions['outfile'])
                    plots_made += 1
                    newper = 10 + int((plots_made / float(tot_plots)) * 85)
                    if oldper != newper:
                        response.update_status("Plotting", newper)
                        oldper = newper

            elif request.inputs['summarise'][0].data == 'all':
                s.sumAll()
                plotoptions['caption'] = "{} {} {} {}: Summed (UTC)".format(s.runname, s.averaging, s.altitude,
                                                                            s.direction)
                plotoptions['outfile'] = "{}_{}_summed_all.png".format(s.runname, s.altitude.strip('()'))
                try:
                    drawMap(s, 'total', **plotoptions)
                    LOGGER.debug("Plotted %s" % plotoptions['outfile'])
                except:
                    LOGGER.error("Failed to plot %s" % plotoptions['outfile'])
                plots_made += 1
                newper = 10 + int((plots_made / float(tot_plots)) * 85)
                if oldper != newper:
                    response.update_status("Plotting", newper)
                    oldper = newper
            else:
                for filename in os.listdir(tmpdir):
                    if '_group' in filename and filename.endswith('.txt'):
                        if request.inputs['summarise'][0].data == 'day':
                            #s = Sum(tmpdir)
                            date = util.shortname(filename)
                            s.sumDay(date)
                            plotoptions['caption'] = "{} {} {} {}: {}{}{} day sum (UTC)".format(s.runname, s.averaging,
                                                                                          s.altitude, s.direction,
                                                                                          s.year, s.month, s.day)
                            plotoptions['outfile'] = "{}_{}_{}{}{}_daily.png".format(s.runname, s.altitude.strip('()'),
                                                                                     s.year, s.month, s.day)
                            try:
                                drawMap(s, 'total', **plotoptions)
                                LOGGER.debug("Plotted %s" % plotoptions['outfile'])
                            except:
                                LOGGER.error("Failed to plot %s" % plotoptions['outfile'])
                            plots_made += 1
                            newper = 10 + int((plots_made / float(tot_plots)) * 85)
                            if oldper != newper:
                                response.update_status("Plotting", newper)
                                oldper = newper
                        elif request.inputs['summarise'][0].data == 'NA':
                            n = Name(os.path.join(tmpdir, filename))
                            if 'timestamp' in request.inputs:
                                timestamp = datetime.strftime(request.inputs['timestamp'][0].data, "%d/%m/%Y %H:%M UTC")
                                LOGGER.debug("Reformatted time: %s" % timestamp)
                                if timestamp in n.timestamps:
                                    try:
                                        drawMap(n, timestamp, **plotoptions)
                                        LOGGER.debug("Plotted %s" % timestamp)
                                    except:
                                        LOGGER.error("Failed to plot %s" % timestamp)
                                    plots_made += 1
                                    newper = 10 + int((plots_made / float(tot_plots)) * 85)
                                    if oldper != newper:
                                        response.update_status("Plotting", newper)
                                        oldper = newper
                                    break
                            else:
                                for column in n.timestamps:
                                    try:
                                        drawMap(n, column, **plotoptions)
                                        LOGGER.debug("Plotted %s" % column)
                                    except:
                                        LOGGER.error("Failed to plot %s" % column)
                                    plots_made += 1
                                    newper = 10 + int((plots_made / float(tot_plots)) * 85)
                                    if oldper != newper:
                                        response.update_status("Plotting", newper)
                                        oldper = newper

            # Finished plotting so will now delete temp directory
            shutil.rmtree(tmpdir)

        # Outputting different response based on the number of plots generated
        response.update_status("Formatting output", 95)
        if not os.path.exists(plotoptions['outdir']):
            LOGGER.debug("Did not create any plots")
            response.outputs['FileContents'].data_format = FORMATS.TEXT
            response.outputs['FileContents'].data = "No plots created, check input options"
        else:
            if len(os.listdir(plotoptions['outdir'])) == 1:
                LOGGER.debug("Only one output plot")
                response.outputs['FileContents'].data_format = Format('image/png')
                response.outputs['FileContents'].file = os.path.join(plotoptions['outdir'],
                                                                     os.listdir(plotoptions['outdir'])[0])
            else:
                zippedfile = "{}_plots".format(request.inputs['filelocation'][0].data)
                shutil.make_archive(zippedfile, 'zip', plotoptions['outdir'])
                LOGGER.debug("Zipped file: %s (%s bytes)" % (zippedfile+'.zip', os.path.getsize(zippedfile+'.zip')))
                response.outputs['FileContents'].data_format = FORMATS.SHP
                response.outputs['FileContents'].file = zippedfile + '.zip'

        response.update_status("done", 100)
        return response
