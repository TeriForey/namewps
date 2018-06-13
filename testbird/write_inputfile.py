# encoding: utf8

import os
import re
import logging
import datetime as dt

from .utils import get_Mk_global, get_Met_vals, getjasminconfigs

LOGGER = logging.getLogger("PYWPS")


def generate_hourlys(params, index, cur_date, start_hour, stop_hour):
    """
    This will add the SourceTermAndOutputRequest_Template text into the file for each hour it needs to be run.
    :param params: input parameters
    :param index: sample index number
    :param cur_date: current datetime object
    :param start_hour: starting hour
    :param stop_hour: stopping hour
    :return:
    """

    SamplingPeriod_Stop = cur_date + dt.timedelta(hours=stop_hour)
    SamplingPeriod_Start = cur_date + dt.timedelta(hours=start_hour)

    strings = []

    strings.append("""
! Source term and output requests for sampling period {}: {} --> {}""".format(
        index, dt.datetime.strftime(SamplingPeriod_Start, '%d/%m/%Y %H:%M'),
        dt.datetime.strftime(SamplingPeriod_Stop, '%d/%m/%Y %H:%M')))

    Z = params['elevation']
    dZ = 0.0
    if 'elevation_range_min' in params:
        dZ = params['elevation_range_max'] - params['elevation_range_min']
        Z = params['elevation_range_min'] + dZ/2


    strings.append("""
Sources:
Name,           Start Time,          Stop Time,           # Particles,      Source Strength,   Shape,  H-Coord, Z-Coord,       Set of Locations, Location, dH-Metres?, dZ-Metres?,     Z,   dX,   dY,    dZ, Angle, Top Hat, Plume Rise?, Temperature, Volume Flow Rate,  Max Age
SourceID1_{}, {}, {}, {}, TRACER1 1.0 g/s,  Cuboid, Lat-Long,   m agl,  Receptor Locations, {},        No,        Yes,  {},  2.5,  2.5, {},   0.0,     Yes,          No,         273.0,              0.0, infinity""".format(
        index,
        dt.datetime.strftime(SamplingPeriod_Start, '%d/%m/%Y %H:%M'),
        dt.datetime.strftime(SamplingPeriod_Stop, '%d/%m/%Y %H:%M'),
        params['npart'],
        params['title'],
        Z, # Z
        dZ, # dZ
        ))

    strings.append("""
Output Requirements - Fields: 
Name,                             Quantity,      Species,                  Source, H-Grid, Z-Grid,        T-Grid, BL Average, T Av Or Int,          Av Time,  # Av Times, Sync?, Output Route, Across,  Separate File, Output Format, Output Group""")


    for nzgrids in range(1, len(params['elevationOut']) + 1):
        strings.append("Req{}_{}, Air concentration, TRACER1, SourceID1_{}, HGrid1, ZGrid{}, TGrid{},         No,"
                       "         Int, {}:00, {},    No,            D,     TZ,  Z,          IA, {}_group{}".format(nzgrids,
            index,index, nzgrids, index, params['runDuration'], params['runDuration']*params['ntimesperhour'],
            dt.datetime.strftime(cur_date, "%Y%m%d"), nzgrids))


    return "\n".join(strings)+"\n"



def generate_coords(params, cur_date):

    # Values come in as minY,minX,maxY,maxX
    CompDom_Xmin = params['domain'][1]
    CompDom_Xmax = params['domain'][3]
    CompDom_Ymin = params['domain'][0]
    CompDom_Ymax = params['domain'][2]

    coordsstrings = []

    coordsstrings.append("""
Horizontal Coordinate Systems:
Name
Lat-Long

Vertical Coordinate Systems:
Name
m agl
m asl

Locations: Receptor Locations
Name,         H-Coord,             X,             Y,
{}, Lat-Long, {}, {},
""".format(params['title'], params['longitude'], params['latitude']))

    grid1_nX = abs((CompDom_Xmin - CompDom_Xmax) * 1/params['resolution'])
    grid1_nY = abs((CompDom_Ymin - CompDom_Ymax) * 1/params['resolution'])

    coordsstrings.append("""
Horizontal Grids:
Name,    H-Coord,         nX,         nY,         dX,         dY,        X Min,        Y Min,
HGrid1, Lat-Long,     {},     {},     {},     {},     {},     {},
""".format(grid1_nX, grid1_nY, params['resolution'], params['resolution'], CompDom_Xmin, CompDom_Ymin))

    coordsstrings.append("""
Vertical Grids:
Name,   Z-Coord,  nZ,      Z0,      dZ,""")

    nzgrids = 0
    for minele, maxele in params['elevationOut']:
        nzgrids += 1
        dZ = maxele - minele
        Z0 = minele + (dZ/2)
        coordsstrings.append("ZGrid{},   m agl,   1,    {},   {},".format(nzgrids, Z0, dZ))

    if params['timeFmt'] == "days":
        maxagehours = params['time']*24
    else:
        maxagehours = params['time']

    if params['timestamp'] == '3-hourly':
        runDuration = maxagehours + 3
        params['runDuration'] = runDuration
        coordsstrings.append("""
Temporal Grids:
Name,                      nt,     dt,               t0,""")
        if params['runBackwards']:
            for i in range(1,9):
                coordsstrings.append("TGrid{},              1,  03:00,   {},".format(i,
                                                                                     dt.datetime.strftime(
                                                                                         cur_date - dt.timedelta(
                                                                                             days=params['time']),
                                                                                         '%d/%m/%Y %H:%M')
                                                                                     ))
                cur_date = cur_date + dt.timedelta(hours=3)
        else:
            for i in range(1,9):
                cur_date = cur_date + dt.timedelta(hours=3)
                coordsstrings.append("TGrid{},              1,  03:00,   {},".format(i,
                                                                                     dt.datetime.strftime(
                                                                                         cur_date + dt.timedelta(
                                                                                             days=params['time']),
                                                                                         '%d/%m/%Y %H:%M')
                                                                                     ))


    else:
        runDuration = maxagehours + params['dailyreleaselen']
        params['runDuration'] = runDuration
        coordsstrings.append("""
Temporal Grids:
Name,                      nt,     dt,               t0,
TGrid1,              1,  {}:00,   {},
""".format(str(params['dailyreleaselen']).zfill(2), dt.datetime.strftime(cur_date - dt.timedelta(days=params['time']), '%d/%m/%Y %H:%M')))

    coordsstrings.append("""
Domains:
Name,              H Unbounded?,  H-Coord,          X Min,          X Max,          Y Min,          Y Max, Z Unbounded?, Z-Coord,   Z Max, T Unbounded?, Start Time, End Time,  Max Travel Time,
Dispersion Domain,           No, Lat-Long,    {},   {},   {},   {},           No,   m asl, 15000.0,          Yes,           ,         , {}:00,
""".format(CompDom_Xmin, CompDom_Xmax, CompDom_Ymin, CompDom_Ymax, runDuration))


    return "\n".join(coordsstrings)


def generate_inputfile(params, rundate, i):

    """
    This will take the input parameters and generate the appropriate file for running NAME
    :param params: Dictionary of input parameters
    :param rundate: Current date
    :param i: run index
    :return: file contents
    """

    nthreads = 1 # Taken from original script file
    ParticlesPerSource = '10000/hr'
    MaxNumParticles = 1000000
    SyncTime_Minutes = 15
    nIntTimesPerHour = 4
    if params['timestamp'] == '3-hourly':
        SamplingPeriod_Hours = 3 # Is this specific to running it 3-hourly??
    else:
        SamplingPeriod_Hours = params['dailyreleaselen']

    backwards = "No"
    runtype = "FWD"
    if params['runBackwards']:
        backwards = "Yes"
        runtype= "BCK"

    # This will need editing, will need loggedin username, and a run id sub dir.

    jasminconfigs = getjasminconfigs()

    userdir = jasminconfigs.get('jasmin', 'userdir')
    workdir = os.path.join(userdir, 'WPStest', params['runid'])

    utilsdir = jasminconfigs.get('jasmin', 'utilsdir')
    namedir = jasminconfigs.get('jasmin', 'namedir')
    topodir = jasminconfigs.get('jasmin', 'topodir')
    metdir = os.path.join(workdir, "met_data", "input{}".format(i))

    cur_date = dt.datetime.combine(rundate, dt.time(0))
    if 'dailytime' in params and params['timestamp'] == 'daily':
        cur_date = dt.datetime.combine(rundate, params['dailytime'])

    start_globalMk = get_Mk_global(cur_date + dt.timedelta(days=1))
    end_globalMK = get_Mk_global(cur_date - dt.timedelta(days=params['time']))

    if start_globalMk == 0 or end_globalMK == 0:
        raise Exception("Date is before the earliest available Global met data")
    elif start_globalMk != end_globalMK:
        raise Exception("The start and stop dates of the NAME run do not use the same 'Mk' Global met data")

    MetVals = get_Met_vals(start_globalMk)

    MetDefnFile = os.path.join(namedir, "Resources", "Defns", MetVals['MetDefnFileName'])
    MetDeclnFile = os.path.join(utilsdir, "MetDeclarations", MetVals['MetDeclFileName'])
    MetRestoreScript = os.path.join(userdir, "MetRestore_JASMIN.ksh")

    params['npart'] = ParticlesPerSource
    params['ntimesperhour'] = nIntTimesPerHour

    header = """
  ******************************************************************************
!
! Project: Template files and scripts for research users on NAME-JASMIN
!
! File:    Input file for run {}
!
! Authors: Andrew Jones, Atmospheric Dispersion, UK Met Office
!          Teri Forey, ReSET, University of Leicester
!
! Date:    Generated by NAME WPS for release on {}
! ******************************************************************************

Main Options:
Absolute or Relative Time?, Fixed Met?, Flat Earth?,    Run Name,       Random Seed, Max # Sources, Backwards?
                  Absolute,         No,          No,          {},             Fixed,            24,        {}

Restart File Options:
# Cases Between Writes, Time Between Writes, Delete Old Files?, Write On Suspend?,
                      ,                    ,                  ,                  ,

Multiple Case Options:
Dispersion Options Ensemble Size, Met Ensemble Size,
                               1,                 1,

OpenMP Options:
Use OpenMP?,    Threads, Parallel MetRead, Parallel MetProcess,
         No,         {},               No,                  No,
""".format(params['runid'], dt.datetime.strftime(cur_date, "%d/%m/%Y"), params['title'], backwards, nthreads)

    inandout = """
Output Options:
Folder
{}

Input Files:
File names
{}
""".format(os.path.join(workdir, 'outputs'), MetDefnFile)

    coordstr = generate_coords(params, cur_date)

    footer = """
Species:
        Name, Category, Half Life, UV Loss Rate, Surface Resistance, Deposition Velocity,  Molecular Weight, Material Unit
TRACER1,    Tracer,    Stable,     0.00E+00,                   ,                 0.0,            0,             g

Species Uses:
Species,     On Particles?, On Fields?, Advect Field?
TRACER1,          Yes,         No,            No

Sets of Dispersion Options:
Max # Particles,   Max # Full Particles, Skew Time, Velocity Memory Time, Mesoscale Velocity Memory Time, Inhomogeneous Time, DeltaOpt,     Sync Time, Time of Fixed Met, Computational Domain, Puff Interval, Deep Convection?, Radioactive Decay?, Agent Decay?, Dry Deposition?, Wet Deposition?, Turbulence?, Mesoscale Motions?, Chemistry? 
{},                    2,     00:00,                00:00,                          00:00,              00:00,        1,      00:{},                  ,    Dispersion Domain,         00:00,               No,                 No,           No,              Yes,              Yes,         Yes,                Yes,         No 
""".format(MaxNumParticles, SyncTime_Minutes)

    hourstrings = []
    samplingPeriodIndex = 0
    hour_stop = 0
    hour_start = SamplingPeriod_Hours
    while(hour_stop < 24):
        samplingPeriodIndex += 1

        if params['runBackwards']:
            hourstrings.append(generate_hourlys(params, samplingPeriodIndex, cur_date, hour_start, hour_stop))
        else:
            hourstrings.append(generate_hourlys(params, samplingPeriodIndex, cur_date, hour_stop, hour_start))

        hour_stop = hour_stop + SamplingPeriod_Hours
        hour_start = hour_start + SamplingPeriod_Hours

        if params['timestamp'] == 'daily':
            break


    if not os.path.exists(MetDeclnFile):
        raise Exception("Cannot find Met Declaration file {}".format(MetDeclnFile))

    declstrings = []
    with open(MetDeclnFile, 'r') as ins:
        for l in ins:
            l = l.rstrip()
            l = re.sub('%MetDir%', metdir, l)
            l = re.sub('%TopogDir%', topodir, l)
            l = re.sub('%MetRestoreScript%', MetRestoreScript, l)
            declstrings.append(l)

    return header+inandout+coordstr+footer+"\n".join(hourstrings)+"\n\n"+"\n".join(declstrings)

