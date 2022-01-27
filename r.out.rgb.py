#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      r.out.rgb
# AUTHOR(S):   Anika Weinmann
#
# PURPOSE:     Exports a RGB raster as GeoTiff and returns a SLD for the RGB
#              composite
#
# COPYRIGHT:    (C) 2019-2022 by mundialis GmbH & Co. KG and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################
# %Module
# % description: Exports a RGB raster scene as multilayer GeoTiff and returns a SLD for the RGB composite.
# % keyword: export
# % keyword: raster
# % keyword: SLD
# %End

# %option G_OPT_R_INPUT
# % key: red
# % label: Raster map
# %end

# %option G_OPT_R_INPUT
# % key: green
# % label: Raster map
# %end

# %option G_OPT_R_INPUT
# % key: blue
# % label: Raster map
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % label: RGB output GeoTiff file
# %end

import atexit
import os
import uuid
from grass.script import core as grass

# initialize global vars
rm_groups = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmgroup in rm_groups:
        if grass.find_file(name=rmgroup, element="group")["file"]:
            grass.run_command("g.remove", type="group", name=rmgroup, **kwargs)


def main():

    global rm_groups

    red = options["red"]
    green = options["green"]
    blue = options["blue"]

    if options["output"].lower().endswith(".tif") or options["output"].lower().endswith(
        ".tiff"
    ):
        output = options["output"]
    else:
        grass.fatal(_("The parameter output have to end with .tif or .tiff"))

    uuid_str = str(uuid.uuid4())

    grass.message(_("Export RGB GeoTiff..."))
    tmp_group = "rgb_group_%s" % uuid_str
    rm_groups.append(tmp_group)
    grass.run_command("i.group", input=[red, green, blue], group=tmp_group, quiet=True)
    compress_overview = None
    if "COMPRESS_OVERVIEW" in os.environ:
        compress_overview = os.environ["COMPRESS_OVERVIEW"]
    os.environ["COMPRESS_OVERVIEW"] = "LZW"
    grass.run_command(
        "r.out.gdal",
        input=tmp_group,
        output=output,
        createopt="COMPRESS=LZW,TILED=YES",
        overviews=5,
        quiet=True,
    )
    if not compress_overview:
        del os.environ["COMPRESS_OVERVIEW"]
    else:
        os.environ["COMPRESS_OVERVIEW"] = compress_overview

    grass.message(_("SLD for RGB GeoTiff..."))
    rgb_sld = """
<?xml version="1.0" encoding="UTF-8"?><sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" version="1.0.0">
  <sld:NamedLayer>
    <sld:Name>Default Styler</sld:Name>
    <sld:UserStyle>
      <sld:Name>Default Styler</sld:Name>
      <sld:Title>vhr_raster : ""</sld:Title>
      <sld:FeatureTypeStyle>
        <sld:Name>name</sld:Name>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:RedChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
                <sld:ContrastEnhancement>
                  <sld:GammaValue>1.0</sld:GammaValue>
                </sld:ContrastEnhancement>
              </sld:RedChannel>
              <sld:GreenChannel>
                <sld:SourceChannelName>2</sld:SourceChannelName>
                <sld:ContrastEnhancement>
                  <sld:GammaValue>1.0</sld:GammaValue>
                </sld:ContrastEnhancement>
              </sld:GreenChannel>
              <sld:BlueChannel>
                <sld:SourceChannelName>3</sld:SourceChannelName>
                <sld:ContrastEnhancement>
                  <sld:GammaValue>1.0</sld:GammaValue>
                </sld:ContrastEnhancement>
              </sld:BlueChannel>
            </sld:ChannelSelection>
            <sld:ContrastEnhancement/>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </sld:NamedLayer>
</sld:StyledLayerDescriptor>
"""
    print(rgb_sld)
    grass.message(_("Created GeoTiff <%s>" % output))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
