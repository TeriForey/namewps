from .wps_nameparams import RunNAME
from .wps_name_standard import RunNAMEstandard
from .wps_plot_allops import PlotAll

processes = [
    RunNAME(),
    RunNAMEstandard(),
    PlotAll(),
]
