from .wps_wordcounter import WordCounter
from .wps_inout import InOut
from .wps_testplot import MakeMap
from .wps_nameparams import RunNAME
from .wps_name_standard import RunNAMEstandard

processes = [
    RunNAMEstandard(),
    RunNAME(),
]
