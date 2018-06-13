import os
from .utils import getjasminconfigs

def write_file(params, maxruns):
    """
    This will write the shell script file that will be used on JASMIN to run NAME
    :param params: the input parameters from the WPS process
    :param maxruns: the last run index
    :return: a string of file contents
    """

    runtype = "FWD"
    if params['runBackwards']:
        runtype = "BCK"

    jasminconfigs = getjasminconfigs()

    userdir = jasminconfigs.get('jasmin', 'userdir')
    workdir = os.path.join(userdir, 'WPStest', params['runid'])
    namedir = jasminconfigs.get('jasmin', 'namedir')
    topodir = jasminconfigs.get('jasmin', 'topodir')
    metdir = os.path.join(userdir, 'met_data', 'input${LSB_JOBINDEX}')
    storedir = os.path.join(workdir, "outputs")

    lines = []

    # First we set the BSUB options

    lines.append("#!/bin/bash")
    lines.append("#BSUB -q short-serial")
    lines.append("#BSUB -o run-%I.out")
    lines.append("#BSUB -e run-%I.err")
    lines.append("#BSUB -W 03:00")
    lines.append('#BSUB -R "rusage[mem=8000]"')
    lines.append("#BSUB -M 8000000")
    lines.append("#BSUB -J {}[1-{}]".format(params['runid'], maxruns))

    # Then import system environment

    lines.append("# Set system variables")
    lines.append(". /etc/profile")
    lines.append("# Load Intel compiler module")
    lines.append("module load intel/13.1")

    # Then we set the directories

    lines.append("SCRIPTDIR=$PWD")
    lines.append("NAMEIIIDIR='{}'".format(namedir))
    lines.append("TOPOGDIR='{}'".format(topodir))
    lines.append("METDIR='{}'".format(metdir))
    lines.append("WORKDIR='{}'".format(workdir))
    lines.append("STOREDIR='{}'".format(storedir))

    # Create the new directories

    lines.append("# Create working directory for NAME runs")
    lines.append("mkdir -p ${WORKDIR}")
    lines.append("# Create store directory for NAME runs")
    lines.append("mkdir -p ${STOREDIR}")
    lines.append("# Create local met directory")
    lines.append("mkdir -p ${METDIR}")
    lines.append("# Switch to working directory")
    lines.append("cd ${WORKDIR}")

    # Run NAME

    lines.append("echo '=============================='")
    lines.append("echo 'Running NAME on ${LSB_JOBINDEX}'")
    lines.append("echo '=============================='")
    lines.append("${NAMEIIIDIR}/Executables_Linux/nameiii_64bit_par.exe  inputs/input${LSB_JOBINDEX}.txt")

    # Finish

    lines.append("echo 'Script completed'")
    lines.append("# -------------------------------- END -------------------------------")
    lines.append("exit 0")

    return "\n\n".join(lines)
