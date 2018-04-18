from .wps_wordcounter import WordCounter
from .wps_inout import InOut
from .wps_testplot import MakeMap

processes = [
    WordCounter(),
    InOut(),
    MakeMap(),
]
