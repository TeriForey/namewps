import os
import shutil
import subprocess
import time
from datetime import timedelta, datetime
from pynameplot import Name, drawMap

from .utils import daterange, getjasminconfigs
from .write_inputfile import generate_inputfile
from .write_scriptfile import write_file


def run_name(params, response):
    """
    This is the function to actually run NAME
    :param params: input parameters
    :param response: the WPS response object
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

    # Will write a file that lists all the input parameters
    with open(os.path.join(params['outputdir'], 'user_input_parameters.txt'), 'w') as ins:
        for p in sorted(params):
            if p == 'outputdir':
                continue
            ins.write("%s: %s\n" % (p, params[p]))

    # Will loop through all the dates in range, including the final day
    for i, cur_date in enumerate(daterange(params['startdate'], params['enddate'] + timedelta(days=1))):
        os.makedirs(os.path.join(params['outputdir'], 'met_data', "input{}".format(i+1)))
        with open(os.path.join(params['outputdir'], "inputs", "input{}.txt".format(i+1)), 'w') as fout:
            fout.write(generate_inputfile(params, cur_date, i+1))

    with open(os.path.join(params['outputdir'], 'script.bsub'), 'w') as fout:
        fout.write(write_file(params, i+1))

    response.update_status("Input files created", 10)

    # TODO: We'll insert the commands to run NAME here.
    # cat = subprocess.Popen(['cat', os.path.join(params['outputdir'], 'script.bsub')], stdout=subprocess.PIPE)
    # runbsub = subprocess.Popen('bsub', stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=cat.stdout)
    # sout, serr = runbsub.communicate()
    # jobid = sout.split(' ')[1].replace('>', '').replace('<', '')
    # jobrunning = True
    # while jobrunning:
    #     time.sleep(30)
    #     checkjob = subprocess.check_output('bjobs')
    #     if jobid in checkjob:
    #         print("Job %s is still running" % jobid)
    #           processesrunning = 0
    #           for l in checkjob.split('\n'):
    #               if jobid in l:
    #                   processesrunning += 1
    #           percentcomplete = (((i+1)-processesrunning)/float(i+1))*85
    #           response.update_status("Running NAME", 10+percentcomplete)
    #     else:
    #         jobrunning = False

    response.update_status("NAME simulation finished", 95)

    # TODO: Need to replace this with an actual result file
    fakefile = os.path.join(jasconfigs.get('jasmin', 'outputdir'), '20171101_output.txt')

    n = Name(fakefile)
    mapfile = "ExamplePlot.png"
    drawMap(n, n.timestamps[0], outfile=mapfile)

    # Zip all the output files into one directory to be served back to the user.
    zippedfile = params['runid']
    shutil.make_archive(zippedfile, 'zip', params['outputdir'])

    return params['runid'], zippedfile, mapfile
