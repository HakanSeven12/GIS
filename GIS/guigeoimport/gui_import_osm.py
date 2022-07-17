# -------------------------------------------------
# -- osm map importer gui
# --
# -- microelly 2016 v 0.4
# -- Bernd Hahnebach <bernd@bimstatik.org> 2020
# --
# -- GNU Lesser General Public License (LGPL)
# -------------------------------------------------
"""gui for import data from openstreetmap"""

import FreeCAD, FreeCADGui
from PySide2 import QtWidgets
import re
import WebGui

from GIS_libs import ui_path
from ..geoimport.import_osm import import_osm2


class ImportOSM:
    """
    Execution layer of the Gui
    """

    def __init__(self):
        """
        Constructor
        """
        # Get *.ui file(s)
        self.form = FreeCADGui.PySideUic.loadUi(ui_path + "/import_osm.ui")

        # UI connections
        self.form.lineEdit_mapLink.textChanged.connect(self.get_separator)
        self.form.pushButton_help.clicked.connect(self.show_help)
        self.form.pushButton_getCoordinates.clicked.connect(self.get_coordinate)
        self.form.pushButton_swap.clicked.connect(self.swap)
        self.form.horizontalSlider_length.valueChanged.connect(self.update_length)
        self.form.pushButton_downloadData.clicked.connect(self.download_data)
        self.form.pushButton_showWeb.clicked.connect(self.show_web)

    def import_osm(self, lat, lon, bk, progressbar, status, elevation):
        """
        import the osm data by the use of import_osm module
        """
        has_finished = import_osm2(
            lat,
            lon,
            bk,
            progressbar,
            status,
            elevation
        )
        return has_finished

    def run(self, lat, lon):
        """
        run(self,lat,lon) imports area
        with center coordinates latitude lat, longitude lon
        """
        s = self.root.ids["s"].value()
        key = "%0.7f" % (lat) + "," + "%0.7f" % (lon)
        self.root.ids["bl"].setText(key)
        self.import_osm(
            lat,
            lon,
            float(s)/10,
            self.root.ids["progb"],
            self.root.ids["status"],
            False
        )

    def show_help(self):

        msg = QtWidgets.QMessageBox()
        msg.setText("<b>Help</b>")
        msg.setInformativeText(
            "Import_osm map dialogue box can also accept links "
            "from following sites in addition to "
            "(latitude, longitude)<ul><li>OpenStreetMap</li><br>"
            "e.g. https://www.openstreetmap.org/#map=15/30.8611/75.8610<br><li>Google Maps</li><br>"
            "e.g. https://www.google.co.in/maps/@30.8611,75.8610,5z<br><li>Bing Map</li><br>"
            "e.g. https://www.bing.com/maps?osid=339f4dc6-92ea-4f25-b25c-f98d8ef9bc45&cp=30.8611~75.8610&lvl=17&v=2&sV=2&form=S00027<br><li>Here Map</li><br>"
            "e.g. https://wego.here.com/?map=30.8611,75.8610,15,normal<br><li>(latitude,longitude)</li><br>"
            "e.g. 30.8611,75.8610</ul><br>"
            "If in any case, the latitude & longitudes are estimated incorrectly, "
            "you can use different separators in separator box "
            "or can put latitude & longitude directly into their respective boxes."
        )
        msg.exec_()

    def get_separator(self):
        map_link = self.form.lineEdit_mapLink.text()
        seperator = self.form.lineEdit_seperator
        if map_link.find("openstreetmap.org") != -1:
            seperator.setText("/")
        elif map_link.find("google.com") != -1:
            seperator.setText("@|,")
        elif map_link.find("bing.com") != -1:
            seperator.setText("=|~|&")
        elif map_link.find("wego.here.com") != -1:
            seperator.setText("=|,")
        elif map_link.find(",") != -1:
            seperator.setText(",")
        elif map_link.find(":") != -1:
            seperator.setText(":")
        elif map_link.find("/") != -1:
            seperator.setText("/")

    def get_coordinate(self):
        map_link = self.form.lineEdit_mapLink.text()
        seperator = self.form.lineEdit_seperator.text()

        split = re.split(seperator, map_link)
        flag = init_flag = 0

        for text in split:
            try:
                float(text)
                if text.find(".") != -1:
                    if flag == 0:
                        self.form.lineEdit_latitude.setText(text)
                    elif flag == 1:
                        self.form.lineEdit_longitude.setText(text)
                    flag += 1
            except Exception:
                flag = init_flag

    def swap(self):
        latitude = self.form.lineEdit_latitude.text()
        longitude = self.form.lineEdit_longitude.text()
        self.form.lineEdit_latitude.setText(longitude)
        self.form.lineEdit_longitude.setText(latitude)

    def download_data(self):
        """download data from osm"""

        latitude = self.form.lineEdit_latitude.text()
        longitude = self.form.lineEdit_longitude.text()
        lat = float(latitude)
        lon = float(longitude)

        length = self.form.horizontalSlider_length.value()
        elevation = self.form.checkBox_elevation.isChecked()

        rc=self.import_osm(float(lat),float(lon),float(length)/10,
            self.form.progressBar,self.form.label_status,elevation)

    def show_web(self):
        """
        open a webbrowser window and display
        the openstreetmap presentation of the area
        """

        latitude = self.form.lineEdit_latitude.text()
        longitude = self.form.lineEdit_longitude.text()
        lat = float(latitude)
        lon = float(longitude)

        WebGui.openBrowser("http://www.openstreetmap.org/#map=16/{}/{}".format(lat, lon))

    def update_length(self):
        length = self.form.horizontalSlider_length.value()
        self.form.label_length.setText("Length is {} km".format(float(length)/10))
