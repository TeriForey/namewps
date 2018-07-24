from datetime import datetime, timedelta
import os
import ConfigParser


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


def getjasminconfigs():
    """
    This will use ConfigParser to retrieve the JASMIN specific configurations
    :return: configparser obj
    """
    cfile = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jasmin.cfg')
    cparser = ConfigParser.SafeConfigParser()
    cparser.read([cfile])
    return cparser


def get_Mk_global(date):
    """
    Based on the script BackRuns_OneSite_ByDay.ksh, calculating the globalMetMk value
    :param date: datetime object
    :return: integer representing the globalMetMk value
    """

    seconds = int(datetime.strftime(date, "%s"))

    if seconds < 1136073600:
        return 0
    elif seconds < 1230768000:
        return 3
    elif seconds < 1257811200:
        return 4
    elif seconds < 1268092800:
        return 5
    elif seconds < 1367280000:
        return 6
    elif seconds < 1405382400:
        return 7
    elif seconds < 1440460800:
        return 8
    elif seconds < 1499731200:
        return 9
    else:
        return 10


def get_Met_vals(Mk):
    """
    Based on the script BackRuns_OneSite_ByDay.ksh, retrieves various file properties based on the global Mk value
    :param Mk: integer globalMetMk
    :return: dictionary of variables
    """

    d = dict()

    if Mk == 3:
        d['MetType'] = 'GLOUM6'
        d['MetDefnFileName'] = 'MetDefnUM6G.txt'
        d['MetDeclFileName'] = 'Use_UM6G.txt'
        d['MetSuffix'] = 'GLOUM6'
        d['ArchiveMetDir'] = 'Global/GLOUM6'
        d['MetPrefix'] = 'HP'
    elif Mk == 4:
        d['MetType'] = 'GLOUM6pp'
        d['MetDefnFileName'] = 'MetDefnUM6Gpp.txt'
        d['MetDeclFileName'] = 'Use_UM6Gpp.txt'
        d['MetSuffix'] = 'GLOUM6.pp'
        d['ArchiveMetDir'] = 'Global/GLOUM6pp'
        d['MetPrefix'] = 'HP'
    elif Mk == 5:
        d['MetType'] = 'UMG_Mk5'
        d['MetDefnFileName'] = 'MetDefnUMG_Mk5_L52pp.txt'
        d['MetDeclFileName'] = 'Use_UMG_Mk5_L52pp.txt'
        d['MetSuffix'] = 'UMG_Mk5_L52.pp'
        d['ArchiveMetDir'] = 'Global/UMG_Mk5'
        d['MetPrefix'] = 'MO'
    elif Mk == 6:
        d['MetType'] = 'UMG_Mk6PT'
        d['MetDefnFileName'] = 'MetDefnUMG_Mk6_L59PTpp.txt'
        d['MetDeclFileName'] = 'Use_UMG_Mk6_L59PTpp.txt'
        d['MetSuffix'] = 'UMG_Mk6_L59PT*.pp'
        d['ArchiveMetDir'] = 'Global/UMG_Mk6PT'
        d['MetPrefix'] = 'MO'
    else:
        d['MetType'] = 'UMG_Mk'+str(Mk)+'PT'
        d['MetDefnFileName'] = 'MetDefnUMG_Mk'+str(Mk)+'_L59PTpp.txt'
        d['MetDeclFileName'] = 'Use_UMG_Mk'+str(Mk)+'_L59PTpp.txt'
        d['MetSuffix'] = 'UMG_Mk'+str(Mk)+'_[IM]_L59PT*.pp'
        d['ArchiveMetDir'] = 'Global/UMG_Mk'+str(Mk)+'PT'
        d['MetPrefix'] = 'MO'

    return d


def estimatereq(time):
    if time < 5:
        return 'short-serial', '01:00', 8000
    elif time < 10:
        return 'short-serial', '02:00', 16000
    elif time < 15:
        return 'short-serial', '03:00', 32000
    elif time <= 20:
        return 'short-serial', '04:00', 32000
    else:
        return 'high-mem', '08:00', 90000


def get_num_dates(start, end, sum, type='3-hourly'):
    if sum == 'all':
        return 1
    elif sum == 'NA':
        if type == '3-hourly':
            return get_num_dates(start, end, 'day')*8
        else:
            return get_num_dates(start, end, 'day')
    elif sum == 'day':
        diff = (end+timedelta(days=1))-start
        return diff.days
    elif sum == 'month':
        return len(range(start.month, (end.year - start.year) * 12 + end.month + 1))
    elif sum == 'week':
        return len(range(start.isocalendar()[1], (end.year - start.year) * 52 + end.isocalendar()[1] + 1))
