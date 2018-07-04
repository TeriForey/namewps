import os
from .utils import getjasminconfigs
from .utils import estimatereq

def write_file(params, maxruns):
    """
    This will write the shell script file that will be used on JASMIN to run NAME
    :param params: the input parameters from the WPS process
    :param maxruns: the last run index
    :return: a string of file contents
    """

    jasminconfigs = getjasminconfigs()

    userdir = jasminconfigs.get('jasmin', 'userdir')
    workdir = os.path.join(userdir, 'WPStest', params['runid'])
    namedir = jasminconfigs.get('jasmin', 'namedir')
    topodir = jasminconfigs.get('jasmin', 'topodir')

    lines = []

    queue, walltime, mem = estimatereq(params['time'])
    if params['timeFmt'] == 'hours':
        queue, walltime, mem = estimatereq(params['time']/float(24))

    # First we set the BSUB options

    lines.append("#!/bin/bash")
    lines.append("#BSUB -q {}".format(queue))
    lines.append("#BSUB -oo r-%J-%I.out")
    lines.append("#BSUB -eo r-%J-%I.err")
    lines.append("#BSUB -W {}".format(walltime))
    lines.append('#BSUB -R "rusage[mem={}]"'.format(mem))
    lines.append("#BSUB -M {}".format(mem))
    lines.append("#BSUB -J {}[1-{}]".format(params['runid'], maxruns))

    # Then import system environment

    lines.append("# Set system variables")
    lines.append(". /etc/profile")
    lines.append("# Load Intel compiler module")
    lines.append("module load intel/13.1")

    # Then we set the directories

    lines.append("NAMEIIIDIR='{}'".format(namedir))
    lines.append("TOPOGDIR='{}'".format(topodir))
    lines.append("WORKDIR='{}'".format(workdir))

    # Move to correct directory

    lines.append("# Switch to working directory")
    lines.append("cd ${WORKDIR}")

    # Run NAME

    lines.append("echo '=============================='")
    lines.append('echo "Running NAME on input ${LSB_JOBINDEX}"')
    lines.append("echo '=============================='")
    lines.append("${NAMEIIIDIR}/Executables_Linux/nameiii_64bit_par.exe  inputs/input${LSB_JOBINDEX}.txt")

    # Remove Met files

    lines.append("echo 'Removing met files'")
    lines.append("rm ${WORKDIR}/met_data/input${LSB_JOBINDEX}/*.*")

    # Finish

    lines.append("echo 'Script completed'")
    lines.append("# -------------------------------- END -------------------------------")
    lines.append("exit 0")

    return "\n\n".join(lines)
