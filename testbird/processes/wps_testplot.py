
from pywps import Process
from pywps import ComplexInput, ComplexOutput, Format
from pywps import LiteralInput, LiteralOutput
from pywps.app.Common import Metadata

from testbird.visualisation import plot_area, fig2plot
from matplotlib import pyplot as plt


import logging
LOGGER = logging.getLogger("PYWPS")


class MakeMap(Process):
    """
    Notes
    -----

    Takes longitude and latitude and plots a map of that location.
    """
    def __init__(self):
        inputs = [
            LiteralInput('longitude','Longitude', data_type='float',
                         abstract="Longitude to center on",
                         default=-75.0),
            LiteralInput('latitude', 'Latitude', data_type='float',
                         abstract="Latitude to center on",
                         default=43.0)
            ]
        outputs = [
            ComplexOutput('output_figure', 'map',
                          abstract="Centered Map",
                          as_reference=True,
                          supported_formats=[Format('image/png'),
                                             Format('application/pdf'),
                                             Format('image/svg+xml'),
                                             Format('application/postscript'), ],
                          ),
            ]

        super(MakeMap, self).__init__(
            self._handler,
            identifier='makemap',
            title='Make a map',
            abstract="Builds a map",
            version='1.0',
            metadata=[
                Metadata('User Guide', 'http://testbird.readthedocs.io/en/latest/'),
                Metadata('Free eBooks at Gutenberg', 'http://www.gutenberg.org/'),
                Metadata('Example: Alice in Wonderland', 'http://www.gutenberg.org/cache/epub/19033/pg19033.txt'),
            ],
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):

        longitude = request.inputs['longitude'][0].data
        LOGGER.error(longitude, type(longitude))
        latitude = request.inputs['latitude'][0].data

        try:
            fig = plot_area((longitude,latitude))
            output = fig2plot(fig, 'svg')

        except Exception as e:
            msg = "Failed to create figure: {}".format(e)
            LOGGER.error(msg)
            raise Exception(msg)

        finally:
            plt.close()

        response.outputs['output_figure'].file = output
        response.update_status("done", 100)
        return response
