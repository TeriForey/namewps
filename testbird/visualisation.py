# encoding: utf8
import os
from os.path import join
from tempfile import mkstemp
import logging
from matplotlib import use
use('Agg')   # use this if no xserver is available

from matplotlib import pyplot as plt
import cartopy.crs as ccrs

LOGGER = logging.getLogger("PYWPS")


def plot_area(coords=(-75.0,43.0)):
    """
    return a map plot centered on a particular spot
    :param coords: tuple (lon,lat) of central location
    :return: matplotlib object
    """
    central_lon = coords[0]
    central_lat = coords[1]


    fig = plt.figure(figsize=(20, 10))
    projection = ccrs.Orthographic(central_longitude=central_lon,
                               central_latitude=central_lat,
                               globe=None)  # Robinson()
    ax = plt.axes(projection=projection)
    ax.coastlines()
    ax.gridlines()
    ax.stock_img()

    plt.plot(central_lon, central_lat, marker='x', color='red')

    return fig

def fig2plot(fig, file_extension='png', output_dir='.', bbox_inches='tight', dpi=300, facecolor='w', edgecolor='k', figsize=(20, 10)):
    '''saving a matplotlib figure to a graphic - copied directly from flyingpigeon
    :param fig: matplotlib figure object
    :param output_dir: directory of output plot
    :param file_extension: file file_extension (default='png')
    :return str: path to graphic
    '''

    _, graphic = mkstemp(dir=output_dir, suffix='.%s' % file_extension)
    fig.savefig(graphic, bbox_inches=bbox_inches, dpi=dpi, facecolor=facecolor, edgecolor=edgecolor, figsize=figsize)

    return graphic
