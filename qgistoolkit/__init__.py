# author: GUO ZIJIAN from PolyU

# how to install qgis in dockerfile
#RUN apt -y update
#RUN apt install -y gnupg software-properties-common
#RUN wget -qO - https://qgis.org/downloads/qgis-2020.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import
#RUN chmod a+r /etc/apt/trusted.gpg.d/qgis-archive.gpg
#RUN add-apt-repository -y "deb https://qgis.org/ubuntu $(lsb_release -c -s) main"
#RUN apt -y update
#RUN apt -y install qgis qgis-plugin-grass saga
#ENV PATH=$PATH:/usr/share/qgis/python/plugins:/usr/lib/qgis$PATH

# how to install qgis in linux
# apt -y update
# apt install -y gnupg software-properties-common
# wget -qO - https://qgis.org/downloads/qgis-2020.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import
# chmod a+r /etc/apt/trusted.gpg.d/qgis-archive.gpg
# add-apt-repository -y "deb https://qgis.org/ubuntu $(lsb_release -c -s) main"
# apt -y update
# apt -y install qgis qgis-plugin-grass saga
# EXPORT PATH=$PATH:/usr/share/qgis/python/plugins:/usr/lib/qgis$PATH

from shapely.wkt import loads
import numpy as np
import pandas as pd
import geopandas as gpd
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
# initialization
from qgis.core import *

# Supply path to qgis install location
QgsApplication.setPrefixPath('/usr', True)

# Create a reference to the QgsApplication.  Setting the
# second argument to False disables the GUI.
qgs = QgsApplication([], False)

# Load providers
qgs.initQgis()

# Write your code here to load some layers, use processing
# algorithms, etc.

import sys
sys.path.append('/usr/share/qgis/python/plugins')
sys.path.append('/usr/lib/qgis/')

import processing
from processing.core.Processing import Processing
from qgis.analysis import QgsNativeAlgorithms
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

class Qgistools(object):

    def __init__(self):
        pass

    # Close qgis
    def quit(self):
        qgs.exitQgis()

    # Check algorithm
    def algorithm(self):
        num=0
        for alg in QgsApplication.processingRegistry().algorithms():
            print(alg.id(), "->", alg.displayName())
            num+=1
        print(num)

    # load shapefile
    def read_file(self, path, layer_name="temp",encoding='utf-8', *args, **kwargs):
        v_layer = QgsVectorLayer(path, layer_name, "ogr", *args, **kwargs)
        v_layer.setProviderEncoding(encoding)
        return v_layer

    # Do Qgis processing
    def run(self, method, parameters,output=True):
        processing_result = processing.run(method,parameters)
        if output:
            return processing_result['OUTPUT']
        else:
            return processing_result
    def geopandas2layer(self,df,name='temp'):
        vlayer = QgsVectorLayer(df.to_json(), name,"ogr")
        return vlayer

    def layer2geopandas(self, vlayer):
        features = vlayer.getFeatures()
        prov = vlayer.dataProvider()
        field_names = [field.name() for field in prov.fields()]
        Index=[]
        row_list=[]
        crs_t = vlayer.crs().toProj()
        for feature in features:
            Index.append(feature.id())
            wkt = feature.geometry().asWkt()
            attrs = tuple(feature.attributes()+[wkt])
            row_list.append(attrs)
        data=np.asarray(row_list)
        field_names.append('geometry')
        data_framework=pd.DataFrame(data,index=Index,columns=field_names)
        data_framework['geometry'] = data_framework['geometry'].apply(loads)
        geo_df = gpd.GeoDataFrame(data_framework, crs=crs_t, geometry='geometry')        
        return geo_df
        
    def plot(self, vlayer):
        df=self.layer2geopandas(vlayer)
        df.plot()

    # check the layer
    def see_layer(self,vlayer):
        features = vlayer.getFeatures()
        for feature in features:
            # retrieve every feature with its geometry and attributes
            print("Feature ID: ", feature.id())
            # fetch geometry
            # show some information about the feature geometry
            geom = feature.geometry()
            geomSingleType = QgsWkbTypes.isSingleType(geom.wkbType())
            if geom.type() == QgsWkbTypes.PointGeometry:
                # the geometry type can be of single or multi type
                if geomSingleType:
                    x = geom.asPoint()
                    print("Point: ", x)
                else:
                    x = geom.asMultiPoint()
                    print("MultiPoint: ", x)
            elif geom.type() == QgsWkbTypes.LineGeometry:
                if geomSingleType:
                    x = geom.asPolyline()
                    print("Line: ", x, "length: ", geom.length())
                else:
                    x = geom.asMultiPolyline()
                    print("MultiLine: ", x, "length: ", geom.length())
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                if geomSingleType:
                    x = geom.asPolygon()
                    print("Polygon: ", x, "Area: ", geom.area())
                else:
                    x = geom.asMultiPolygon()
                    print("MultiPolygon: ", x, "Area: ", geom.area())
            else:
                print("Unknown or invalid geometry")
            # fetch attributes
            attrs = feature.attributes()
            # attrs is a list. It contains all the attribute values of this feature
            print(attrs)
            # for this test only print the first feature

    def save_layer(self,v_layer,path):
        parameters = {'INPUT':v_layer,
                        'OUTPUT':path}
        processing.run('qgis:savefeatures',parameters)

