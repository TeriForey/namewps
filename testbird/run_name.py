import os
import shutil
from datetime import timedelta, datetime
from pynameplot import Name, drawMap

from .utils import daterange, getjasminconfigs
from .write_inputfile import generate_inputfile
from .write_scriptfile import write_file


def run_name(params):
    """
    This is the function to actually run NAME
    :param params: input parameters
    :return: names of the output dir and zipped file
    """

    # replace any white space in title with underscores
    params['title'] = params['title'].replace(' ', '_')
    params['title'] = params['title'].replace(',', '')
    params['title'] = params['title'].replace('(', '')
    params['title'] = params['title'].replace(')', '')

    runtype = "FWD"
    if params['runBackwards']:
        runtype = "BCK"

    jasconfigs = getjasminconfigs()

    runtime = datetime.strftime(datetime.now(), "%s")
    params['runid'] = "{}{}_{}_{}_{}".format(runtype, params['time'], params['timestamp'], params['title'], runtime)

    params['outputdir'] = os.path.join(jasconfigs.get('jasmin', 'outputdir'), params['runid'])

    if not os.path.exists(params['outputdir']):
        os.makedirs(params['outputdir'])
        os.makedirs(os.path.join(params['outputdir'], 'inputs'))
        os.makedirs(os.path.join(params['outputdir'], 'outputs'))
    # Will loop through all the dates in range, including the final day
    for i, cur_date in enumerate(daterange(params['startdate'], params['enddate'] + timedelta(days=1))):
        os.makedirs(os.path.join(params['outputdir'], 'met_data', "input{}".format(i+1)))
        with open(os.path.join(params['outputdir'], "inputs", "input{}.txt".format(i+1)), 'w') as fout:
            fout.write(generate_inputfile(params, cur_date, i+1))

    with open(os.path.join(params['outputdir'], 'script.bsub'), 'w') as fout:
        fout.write(write_file(params, i+1))

    """
    We'll insert the commands to run NAME here. 
    """

    """
    Going to 'create' an output file that we will then plot, treating it as though it were an actual result.
    """
    fakefile = os.path.join(jasconfigs.get('jasmin', 'outputdir'), '20171101_output.txt')

    n = Name(fakefile)
    mapfile = "ExamplePlot.png"
    drawMap(n, n.timestamps[0], outfile=mapfile)

    # Zip all the output files into one directory to be served back to the user.
    zippedfile = params['runid']
    shutil.make_archive(zippedfile, 'zip', params['outputdir'])

    return params['runid'], zippedfile, mapfile
