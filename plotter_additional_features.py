import rasterio.plot
import rasterio.mask
import numpy as np
import matplotlib.pyplot as plt
from cartopy import crs
import json
import geopandas as gpd


class Plotter:
    def __init__(self, background, user_location, destination, path, png, folder):
        self.background = background
        self.user_location = user_location
        self.destination = destination
        self.path = path
        self.png = png
        self.folder = folder

    def plot_graph(self):
        # Plot the background map of the surrounding area, 20km x 20km.
        background = rasterio.open(self.background)
        back_array = background.read(1)
        palette = np.array([value for key, value in background.colormap(1).items()])
        background_image = palette[back_array]
        bounds = background.bounds
        extent = [bounds.left, bounds.right, bounds.bottom,  bounds.top]
        display_extent = [self.user_location.x - 10000, self.user_location.x + 10000,
                          self.user_location.y - 10000, self.user_location.y + 10000]

        fig = plt.figure(figsize=(9, 5), dpi=300)
        ax = fig.add_subplot(1, 1, 1, projection=crs.OSGB())
        ax.imshow(background_image, extent=extent, zorder=0)

        # Overlay a transparent elevation raster.
        scope_buffer = gpd.GeoDataFrame({'geometry': self.user_location.buffer(5000)}, index=[0], crs='EPSG:27700')
        clip_range = [json.loads(scope_buffer.to_json())['features'][0]['geometry']]
        elevation = rasterio.open(self.folder + '/elevation/SZ.asc')
        out_image, out_transform = rasterio.mask.mask(elevation, clip_range, crop=True, nodata=-30)
        elev_mask = np.ma.masked_where(out_image == -30, out_image)
        rasterio.plot.show(elev_mask, transform=out_transform, cmap='terrain', ax=ax, alpha=0.4, zorder=1)

        # Plot the user location.
        plt.scatter(getattr(self.user_location, 'x'),
                    getattr(self.user_location, 'y'),
                    color='r', label='You are here', s=0.8, zorder=3)

        # Plot the destination.
        plt.scatter(getattr(self.destination, 'x'),
                    getattr(self.destination, 'y'),
                    color='k', label='Destination', s=0.8, zorder=3)

        # Plot the shortest path.
        self.path.plot(ax=ax, edgecolor='blue', linewidth=0.4, zorder=2, label='Fastest Route')

        # Plot colour bar showing the elevation range.
        elevation = rasterio.open(self.folder + '/elevation/out.tif')
        elevation_array = elevation.read(1)
        elevation_image = ax.imshow(elevation_array, cmap='terrain')
        plt.colorbar(elevation_image, ax=ax, orientation='vertical', anchor=(0.0, 0.5), shrink=0.9)
        plt.text(1.1, 1.0, 'Elevation', transform=ax.transAxes, fontsize=8)

        # Add copyright text.
        plt.text(0, -0.025,
                 '1:50 000 Scale Colour Raster [TIFF geospatial data], Scale 1:50000, Tiles: sz28_clipped,sz46_clipped,'
                 'sz48_clipped,sz68_clipped, Updated: 12 June 2018, Ordnance Survey (GB),\n '
                 'Using: EDINA Digimap Ordnance Survey Service, <https://digimap.edina.ac.uk>, '
                 'Downloaded: 2018-12-09 10:51:09.83',
                 horizontalalignment='left',
                 verticalalignment='baseline', transform=ax.transAxes, fontsize='2')

        plt.text(0, -0.065,
                 'OS Terrain 5 [ASC geospatial data], Scale 1:10000, Tiles: sz28ne,sz28se,sz38ne,sz38nw,sz38se,sz38sw,'
                 'sz39se,sz39sw,sz47ne,sz47nw,sz48ne,sz48nw,sz48se,sz48sw,sz49ne,sz49nw,sz49se,sz49sw,sz57ne,sz57nw,\n'
                 'sz58ne,sz58nw,sz58se,sz58sw,sz59ne,sz59nw,sz59se,sz59sw,sz68ne,sz68nw,sz68sw,sz69nw,sz69se,sz69sw, '
                 'Updated: 3 July 2018, Ordnance Survey (GB), Using: EDINA Digimap Ordnance Survey Service,\n '
                 'https://digimap.edina.ac.uk>, Downloaded: 2018-11-27 13:56:28.547',
                 horizontalalignment='left',
                 verticalalignment='baseline', transform=ax.transAxes, fontsize='2')

        plt.text(0, -0.095,
                 'OS MasterMap® Integrated Transport Network Layer [GML2 geospatial data], Scale 1:1250, Tiles: GB, '
                 'Updated: 11 July 2018, Ordnance Survey (GB), Using: EDINA Digimap Ordnance Survey Service,\n'
                 '<https://digimap.edina.ac.uk>, Downloaded: 2018-11-16 18:04:10.025',
                 horizontalalignment='left',
                 verticalalignment='baseline', transform=ax.transAxes, fontsize='2')

        plt.text(0, -0.125,
                 'OS MasterMap® Integrated Transport Network Layer [GML2 geospatial data], Scale 1:1250, Tiles: GB, '
                 'Updated: 11 July 2018, Ordnance Survey (GB), Using: EDINA Digimap Ordnance Survey Service,\n '
                 '<https://digimap.edina.ac.uk>, Downloaded: 2018-11-16 18:04:10.025',
                 horizontalalignment='left',
                 verticalalignment='baseline', transform=ax.transAxes, fontsize='2')

        # Add the map elements.
        plt.title('Evacuation Route', size=14)
        plt.legend(loc='lower right', fontsize='4', bbox_to_anchor=(-0.04, 0), borderaxespad=0, title='Legend')
        x, y, arrow_length = -0.04, 1, 0.05
        ax.annotate('N', xy=(x, y), xytext=(x, y - arrow_length), ha='center', va='center', fontsize='4',
                    xycoords=ax.transAxes, arrowprops=dict(facecolor='black', width=1, headwidth=4, headlength=2))

        ax.set_extent(display_extent, crs=crs.OSGB())
        plt.savefig(self.folder + '/history/' + self.png)
