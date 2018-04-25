from datetime import datetime

def write_file(params, cur_date):
    """
    This will write the shell script file that will be used on JASMIN to run NAME
    :param params: the input parameters from the WPS process
    :param cur_date: the current running date
    :return: a string of file contents
    """

    runtype = "FWD"
    if params['runBackwards']:
        runtype = "BCK"

    workdir = "/group_workspaces/jasmin/name/cache/users/tforey/WPStest/{}_{}_{}".format(runtype, params['timestamp'],
                                                                                         params['title'])
    namedir = "/group_workspaces/jasmin/name/code/NAMEIII_v7_2_lotus"
    topodir = "/group_workspaces/jasmin/name/code/NAMEIII_v7_2_lotus/Resources/Topog"
    metdir = workdir + "/met_data"
    storedir = workdir + "/output/"

    lines = []

    lines.append("# Set system variables")
    lines.append(". /etc/profile")
    lines.append("# Load Intel compiler module")
    lines.append("module load intel/13.1")

    # First we set the directories

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

    # Set input file

    lines.append("# set input filename for NAME run")
    lines.append("input_file='{}Run_{}_{}.txt'".format(runtype, params['title'],
                                                                datetime.strftime(cur_date, "%Y%m%d")))
    lines.append("# copy input file to right location")
    lines.append("cp $1 ${input_file}")
    # lines.append("# set error filename for NAME run")
    # lines.append("error_file='{}Run_{}_{}Error.txt'".format(runtype, params['title'],
    #                                                           datetime.strftime(cur_date, "%Y%m%d")))

    # Run NAME

    lines.append("echo '=============================='")
    lines.append("echo 'Running NAME for {}'".format(datetime.strftime(cur_date, "%d/%m/%Y")))
    lines.append("echo '=============================='")
    lines.append("${NAMEIIIDIR}/Executables_Linux/nameiii_64bit_par.exe  ${input_file}")

    # Rename output files

    lines.append("# rename each file by start_date so dont overwrite")
    for groupnum in range(1,len(params['elevationOut'])+1):
        lines.append("cp -f ${WORKDIR}/group%s_* ${WORKDIR}/%s_group%s_%s.txt" % (groupnum, params['title'],
                                                                                  groupnum,
                                                                                  datetime.strftime(cur_date, "%Y%m%d")))

    # Finish

    lines.append("echo 'Script $0 completing at {}' ".format(datetime.now()))
    lines.append("# -------------------------------- END -------------------------------")
    lines.append("exit 0")

    return "\n\n".join(lines)
