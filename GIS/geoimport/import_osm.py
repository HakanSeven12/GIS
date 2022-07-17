# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2016 microelly <>                                       *
# *   Copyright (c) 2020 Bernd Hahnebach <bernd@bimstatik.org>              *
# *   Copyright (c) 2022 Hakan Seven <hakanseven12@gmail.com>               *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

"""
Import data from OpenStreetMap
"""

import FreeCAD, FreeCADGui
import Part

import urllib.request
import os

from . import my_xmlparser
from . import transversmercator

from .get_elevation_srtm4 import get_height_single
from .get_elevation_srtm4 import get_height_list

from .say import say
from .say import sayErr

def import_osm(latitude, longitude, length, progressbar=None, status=None, elevation=False):

    if progressbar:
        progressbar.setValue(0)
    if status:
        status.setText("Get data from openstreetmap.org and parse it for later usage ...")

    # Get and parse osm data
    tree = get_osmdata(latitude, longitude, length/2)

    if tree is None:
        FreeCAD.Console.PrintError("Something went wrong on retrieving OSM data.")
        return False

    # Get map nodes data
    if status:
        status.setText("Transform data ...")

    nodes = tree.getiterator("node")
    objects = tree.getiterator("way")
    bounds = tree.getiterator("bounds")[0]

    tm, size, corner_min, points, nodesbyid = map_data(nodes, bounds)

    # Get active document or create new one
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("OSM")
        FreeCAD.Console.PrintMessage("New FreeCAD document created.\n")

    # Create base area and get base height
    if status:
        status.setText("create visualizations...")

    area = doc.addObject("Part::Plane", "area")
    area.Length = size[0] * 2
    area.Width = size[1] * 2
    area.Placement = FreeCAD.Placement(
        FreeCAD.Vector(-size[0], -size[1], 0.00),
        FreeCAD.Rotation(0.00, 0.00, 0.00, 1.00))

    if elevation:
        baseheight = get_height_single(latitude, longitude)
        elearea = doc.addObject("Part::Feature","Elevation_Area")
        elearea.Shape = get_elebase_sh(corner_min, size, baseheight, tm)
        elearea.ViewObject.Transparency = 75
        area.ViewObject.hide()
        FreeCAD.Console.PrintMessage("Area with Height done\n")

    else:
        baseheight = 0.0

    FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCAD.Console.PrintMessage("Base area created.\n")

    # Create object groups
    paths = doc.addObject("App::DocumentObjectGroup","Paths")
    roads = doc.addObject("App::DocumentObjectGroup","Roads")
    landuse = doc.addObject("App::DocumentObjectGroup","Landuse")
    buildings = doc.addObject("App::DocumentObjectGroup","Buildings")

    # Import objects
    for obj in objects:
        # Get object properties
        name, object_type, nr, building_height = get_way_information(obj)

        # Get object polygon points
        if not elevation:
            polygon_points = []
            for n in obj.getiterator("nd"):
                wpt = points[str(n.params["ref"])]
                polygon_points.append(wpt)
        else:
            # Get heights for object polygon points
            polygon_points = get_ppts_with_heights(obj, object_type, points, nodesbyid, baseheight)

        # a wire for each way polygon
        polygon_obj = doc.addObject("Part::Feature", "OsmPolygon")
        polygon_obj.Label = obj.params["id"]
        polygon_obj.Shape = Part.makePolygon(polygon_points)

        osm_object = doc.addObject("Part::Extrusion", "OsmObject")
        osm_object.Base = polygon_obj
        osm_object.Label = name
        osm_object.Dir = (0, 0, 1)

        if object_type == "building":
            buildings.addObject(osm_object)
            osm_object.ViewObject.ShapeColor = (1.0, 1.0, 1.0)
            osm_object.Solid = True
            if building_height == 0:
                building_height = 3000
            osm_object.Dir = (0, 0, building_height)

        elif object_type == "highway":
            roads.addObject(osm_object)
            osm_object.ViewObject.LineColor = (0.0, 0.0, 1.0)
            osm_object.ViewObject.LineWidth = 10

        elif object_type == "landuse":
            landuse.addObject(osm_object)
            osm_object.Solid = True
            if nr == "residential":
                osm_object.ViewObject.ShapeColor = (1.0, 0.6, 0.6)
            elif nr == "meadow":
                osm_object.ViewObject.ShapeColor = (0.0, 1.0, 0.0)
            elif nr == "farmland":
                osm_object.ViewObject.ShapeColor = (0.8, 0.8, 0.0)
            elif nr == "forest":
                osm_object.ViewObject.ShapeColor = (1.0, 0.4, 0.4)

        else:
            paths.addObject(osm_object)
            osm_object.ViewObject.ShapeColor = (1.0, 1.0, 0.0)
            osm_object.Solid = True

        if progressbar:
            progressbar.setValue(int(100 * objects.index(obj)+1 / len(objects)))

    if status:
        status.setText("import finished.")

    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.activeDocument().ActiveView.viewAxonometric()

def map_data(nodes, bounds):
    # Center of the scene
    minlat = float(bounds.params["minlat"])
    minlon = float(bounds.params["minlon"])
    maxlat = float(bounds.params["maxlat"])
    maxlon = float(bounds.params["maxlon"])

    # Note: Setting values changes the result, see transversmerctor module
    tm = transversmercator.TransverseMercator()
    tm.lat = 0.5 * (minlat + maxlat)
    tm.lon = 0.5 * (minlon + maxlon)

    center = tm.fromGeographic(tm.lat, tm.lon)
    coord_corner_min = tm.fromGeographic(minlat, minlon)
    coord_corner_max = tm.fromGeographic(maxlat, maxlon)

    corner_min = FreeCAD.Vector(coord_corner_min[0], coord_corner_min[1], 0)
    corner_max = FreeCAD.Vector(coord_corner_max[0], coord_corner_max[1], 0)
    size = [center[0] - corner_min[0], center[1] - corner_min[1]]

    # Map all points to xy-plane
    points = {}
    nodesbyid = {}
    for n in nodes:
        nodesbyid[n.params["id"]] = n
        ll = tm.fromGeographic(float(n.params["lat"]), float(n.params["lon"]))
        points[str(n.params["id"])] = FreeCAD.Vector(ll[0] - center[0], ll[1] - center[1], 0)

    return (tm, size, corner_min, points, nodesbyid)

def get_osmdata(b, l, bk):

    dn = os.path.join(FreeCAD.ConfigGet("UserAppData"), "geodat_osm")
    if not os.path.isdir(dn):
        os.makedirs(dn)
    fn = os.path.join(dn, "{}-{}-{}".format(b, l, bk))
    say("Local osm data file:")
    say("{}".format(fn))

    # TODO: do much less in try/except
    # use os for file existence etc.
    tree = None
    try:
        say("Try to read data from a former existing osm data file ... ")
        f = open(fn, "r")
        content = f.read()  # try to read it
        False if content else True  # get pylint and LGTM silent
        # really read fn before skipping new internet upload
        # because fn might be empty or does have wrong encoding
        tree = my_xmlparser.getData(fn)
    except Exception:
        say(
            "No former existing osm data file, "
            "connecting to openstreetmap.org ..."
        )
        lk = bk
        b1 = b - bk / 1113 * 10
        l1 = l - lk / 713 * 10
        b2 = b + bk / 1113 * 10
        l2 = l + lk / 713 * 10
        koord_str = "{},{},{},{}".format(l1, b1, l2, b2)
        source = "http://api.openstreetmap.org/api/0.6/map?bbox=" + koord_str
        say(source)

        response = urllib.request.urlopen(source)

        # the file we write into needs uft8 encoding
        f = open(fn, "w", encoding="utf-8")
        # decode makes a string out of the bytesstring
        f.write(response.read().decode("utf8"))
        f.close()

        # writing the file is only for later usage
        # thus may be first parse the data and afterwards write it ... ?
        tree = my_xmlparser.getData(fn)

    if tree is not None:
        return tree
    else:
        return None

def get_way_information(w):
    st = ""
    st2 = ""
    nr = ""
    building_height = 0
    # ci is never used
    # ci = ""
    way_type = ""

    for t in w.getiterator("tag"):
        try:
            if str(t.params["k"]) == "building":
                way_type = "building"
                if st == "":
                    st = "building"

            if str(t.params["k"]) == "landuse":
                way_type = "landuse"
                st = t.params["k"]
                nr = t.params["v"]

            if str(t.params["k"]) == "highway":
                way_type = "highway"
                st = t.params["k"]

            if str(t.params["k"]) == "addr:city":
                pass
                # ci is never used
                # ci = t.params["v"]

            if str(t.params["k"]) == "name":
                nr = t.params["v"]

            if str(t.params["k"]) == "ref":
                nr = t.params["v"]+" /"

            if str(t.params["k"]) == "addr:street":
                st2 = " "+t.params["v"]

            if str(t.params["k"]) == "addr:housenumber":
                nr = str(t.params["v"])

            if str(t.params["k"]) == "building:levels":
                if building_height == 0:
                    building_height = int(str(t.params["v"]))*1000*3

            if str(t.params["k"]) == "building:height":
                building_height = int(str(t.params["v"]))*1000

        except Exception:
            sayErr("unexpected error {}".format(50*"#"))

    name = "{}{} {}".format(st, st2, nr)
    if name == " ":
        name = "landuse xyz"

    return (name, way_type, nr, building_height)


def get_elebase_sh(corner_min, size, baseheight, tm):

    from FreeCAD import Vector as vec
    from MeshPart import meshFromShape
    from Part import makeLine

    # scaled place on origin
    place_for_mesh = FreeCAD.Vector(
        -corner_min.x - size[0],
        -corner_min.y - size[1],
        0.00)

    # SRTM data resolution is 30 m = 30'000 mm in the usa
    # rest of the world is 90 m = 90'000 mm
    # it makes no sense to use values smaller than 90'000 mm
    pt_distance = 100000

    say(corner_min)
    # y is huge!, but this is ok!
    say(size)

    # base area surface mesh with heights
    # Version new
    pn1 = vec(
        0,
        0,
        0
    )
    pn2 = vec(
        pn1.x + size[0] * 2,
        pn1.y,
        0
    )
    pn3 = vec(
        pn1.x + size[0] * 2,
        pn1.y + size[1] * 2,
        0
    )
    pn4 = vec(
        pn1.x,
        pn1.y + size[1] * 2,
        0
    )
    ln1 = makeLine(pn1, pn2)
    ln2 = makeLine(pn2, pn3)
    ln3 = makeLine(pn3, pn4)
    ln4 = makeLine(pn4, pn1)
    wi = Part.Wire([ln1, ln2, ln3, ln4])
    fa = Part.makeFace([wi], "Part::FaceMakerSimple")
    msh = meshFromShape(fa, LocalLength=pt_distance)
    # move to corner_min to retrieve the heights
    msh.translate(
        corner_min.x,
        corner_min.y,
        0,
    )
    # move mesh points z-koord
    for pt_msh in msh.Points:
        # say(pt_msh.Index)
        # say(pt_msh.Vector)
        pt_tm = tm.toGeographic(pt_msh.Vector.x, pt_msh.Vector.y)
        height = get_height_single(pt_tm[0], pt_tm[1])  # mm
        # say(height)
        pt_msh.move(FreeCAD.Vector(0, 0, height))
    # move mesh back centered on origin
    msh.translate(
        -corner_min.x - size[0],
        -corner_min.y - size[1],
        -baseheight,
    )

    # create Shape from Mesh
    sh = Part.Shape()
    sh.makeShapeFromMesh(msh.Topology, 0.1)

    return sh


def get_ppts_with_heights(way, way_type, points, nodesbyid, baseheight):

    plg_pts_latlon = []
    for n in way.getiterator("nd"):
        # say(n.params)
        m = nodesbyid[n.params["ref"]]
        plg_pts_latlon.append([
            n.params["ref"],
            m.params["lat"],
            m.params["lon"]
        ])
    say("    baseheight: {}".format(baseheight))
    say("    get heights for " + str(len(plg_pts_latlon)))
    heights = get_height_list(plg_pts_latlon)
    # say(heights)

    # set the scaled height for each way polygon point
    height = None
    polygon_points = []
    for n in way.getiterator("nd"):
        wpt = points[str(n.params["ref"])]
        # say(wpt)
        m = nodesbyid[n.params["ref"]]
        # say(m.params)
        hkey = "{:.7f} {:.7f}".format(
            float(m.params["lat"]),
            float(m.params["lon"])
        )
        # say(hkey)
        if way_type == "building":
            # for buildings use the height of the first point for all
            # thus code a bit different from the others
            # TODO use 10 cm below the lowest not the first
            # Why do we get all heights if only use one
            # but we need them all to get the lowest
            if height is None:
                say("    Building")
                if hkey in heights:
                    say("    height abs: {}".format(heights[hkey]))
                    height = heights[hkey]
                    say(heights[hkey])
                    say("    height rel: {}".format(height))
                else:
                    sayErr("   ---no height in heights for " + hkey)
                    height = baseheight
        elif way_type == "highway":
            # use the height for all points
            if height is None:
                say("    Highway")
            if hkey in heights:
                height = heights[hkey]
            else:
                sayErr("   ---no height in heights for " + hkey)
                height = baseheight
        elif way_type == "landuse":
            # use 1 mm above base height
            if height is None:
                sayErr("    ---no height used for landuse ATM")
                height = baseheight + 1
        else:
            # use the height for all points
            if height is None:
                say("    Other")
            if hkey in heights:
                height = heights[hkey]
            else:
                sayErr("   ---no height in heights for " + hkey)
                height = baseheight
        if height is None:
            height = baseheight
        wpt.z = height - baseheight
        # say("    with base: {}".format(wpt.z))
        polygon_points.append(wpt)

    return polygon_points
