import os
import stat
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

    # TODO: Need to pull in jasmin config file and set the output dir accordingly
    outputdir = os.path.join(jasconfigs.get('jasmin', 'outputdir'),
                             "{}{}_{}_{}".format(runtype, params['time'], params['timestamp'], params['title']))
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    # Will loop through all the dates in range, including the final day
    for cur_date in daterange(params['startdate'],
                              params['enddate'] + timedelta(days=1)):
        with open(os.path.join(outputdir, "{}Run_{}_{}.txt".format(runtype, params['title'],
                                                                   datetime.strftime(cur_date, "%Y%m%d"))),
                  'w') as fout:
            fout.write(generate_inputfile(params, cur_date))

    with open(os.path.join(outputdir, 'script.sh'), 'w') as fout:
        fout.write(write_file(params))

    st = os.stat(os.path.join(outputdir, 'script.sh'))
    os.chmod(os.path.join(outputdir, 'script.sh'), st.st_mode | 0111)

    """
    Going to 'create' an output file that we will then plot, treating it as though it were an actual result.
    """
    fakefile = os.path.join(jasconfigs.get('jasmin', 'outputdir'), '20171101_output.txt')

    n = Name(fakefile)
    mapfile = "ExamplePlot.png"
    drawMap(n, n.timestamps[0], outfile=mapfile)

    # TODO: Need to trim directory name, report only user/run specific details

    # Zip all the output files into one directory to be served back to the user.
    zippedfile = "{}_{}_{}".format(runtype, params['timestamp'], params['title'])
    shutil.make_archive(zippedfile, 'zip', outputdir)

    return outputdir, zippedfile, mapfile
