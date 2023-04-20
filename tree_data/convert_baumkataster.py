"""
Convert a CSV file with the Baumkataster data for the city of Münster 
into a GeoJSON file to be used by main.py
"""

import re
import json
import csv
from datetime import datetime
import logging
from decimal import Decimal
from pyproj import Proj, transform

inProj = Proj('epsg:25832')
outProj = Proj('epsg:4326')


# Basic logger configuration
logging.basicConfig(level=logging.DEBUG,
                    format='<%(asctime)s %(levelname)s> %(message)s')

LOGGER = logging.getLogger(__name__)
TODAY = datetime.now()

LOGGER.info("=====> START %s <=====", TODAY)

geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Input data columns:
# ===================
#
# x  | column name
# ----------------------------
# 0  | ID;
# 1  | Standort-Nr;
# 2  | Baumhoehe_akt_m;
# 3  | Stammanzahl_akt_anz;
# 4  | Stammdurchmesser_akt_cm;
# 5  | Stammumfang_akt_cm;
# 6  | Kronendurchmesser_akt_cm;
# 7  | Pflanzjahr;
# 8  | Standalter_geschaetzt_jahr;
# 9  | ref_Baumart;
# 10 | ref_Baumart_botanisch;
# 11 | gis_komplex_UTM;
# 12 | ref_Objekt_Name;
# 13 | ref_Objekt_stat_Bezirk;
# 14 | ref_Objekt_Number;
# 15 | ref_Objekt_Name_Number

FILENAME = "tree_data/data_files/baumkataster_muenster"
with open(FILENAME + '.csv',  encoding='latin-1') as csvinput:
    line = 0
    treereader = csv.reader(csvinput, delimiter=';', quotechar='"')
    for row in treereader:
        if line < 1:
            logging.debug("Spalten %s", row)
        else:
            t_geo = row[11]
            t_geo1 = t_geo2 = False
            t_georesult = re.match(
                r"POINT\s*\(\s*(\d+\.\d+)\s+(\d+\.\d+)\s*\)", t_geo)
            if t_georesult:
                t_geo1 = t_georesult.group(1)
                t_geo2 = t_georesult.group(2)
            else:
                t_georesult = re.match(
                    r"POINT\s*\(\s*(\d+\,\d+)\)\s+\((\d+\,\d+)\s*\)", t_geo)
                if t_georesult:
                    t_geo1 = t_georesult.group(1).replace(',', '.')
                    t_geo2 = t_georesult.group(2).replace(',', '.')
            if not (t_geo1 and t_geo2):
                logging.error("DID not find point in '%s'", t_geo)
                continue

#          logging.debug("Geo %s ---> %s, %s", t_geo, Decimal(t_geo1), Decimal(t_geo2))
            x2, y2 = transform(
                inProj, outProj, Decimal(t_geo1), Decimal(t_geo2))
            logging.debug("latlong %s,%s", x2, y2)

            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [y2, x2]},
                "properties": {
                    "gml_id": "muenster/" + row[0] + "/" + row[1],
                    "baumid": row[0],
                    "standortnr": row[1],
                    "kennzeich": row[14] or None,
                    "namenr": row[15] or None,
                    "art_dtsch": row[9] or None,
                    "art_bot": row[10] or None,
                    "strname": row[12] or None,
                    "hausnr": None,
                    "pflanzjahr": row[7] or None,
                    "standalter": row[8] or None,
                    "stammumfg": row[5] or None,
                    "baumhoehe": row[2] or None,
                    "bezirk": row[13] or None,
                    "eigentuemer": None,
                    "zusatz": None,
                    "kronedurch": row[6] or None
                }
            }
            geojson["features"].append(feature)

        line = line + 1


OUTFILE = FILENAME + '.geojson'
LOGGER.info("Writing Geojson file '%s' ", OUTFILE)
with open(OUTFILE, mode='w') as json_file:
    json.dump(geojson, json_file, indent=2)
