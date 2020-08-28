import os
import sys
import gdal, ogr, osr, numpy
import datetime
from scipy import stats

def zonal_stats(feat, input_zone_polygon, input_value_raster, nb):

    # Open data
    raster = gdal.Open(input_value_raster)
    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()
    
    #Select feature layer
    feature = lyr.GetFeature(nb)
    name = feature.GetField(str(sys.argv[3]))
    #Get feature geometry
    geometry = feature.GetGeometryRef()

    #Create an virtual Layer
    driver = ogr.GetDriverByName("Memory")

    data_source = driver.CreateDataSource("tempDS")
    srs = lyr.GetSpatialRef()

    layer = data_source.CreateLayer("tempLayer", srs, geometry.GetGeometryType())
        
    Nfeature = ogr.Feature(layer.GetLayerDefn());
    Nfeature.SetGeometry(geometry);
    layer.CreateFeature(Nfeature);

    # Get raster georeference info
    transform = raster.GetGeoTransform()
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = transform[5]

    #print(transform)

    # Get extent of feat
    geom = feat.GetGeometryRef()
    if (geom.GetGeometryName() == 'MULTIPOLYGON'):
        count = 0
        pointsX = []; pointsY = []
        for polygon in geom:
            geomInner = geom.GetGeometryRef(count)
            ring = geomInner.GetGeometryRef(0)
            numpoints = ring.GetPointCount()
            for p in range(numpoints):
                    lon, lat, z = ring.GetPoint(p)
                    pointsX.append(lon)
                    pointsY.append(lat)
            count += 1
    elif (geom.GetGeometryName() == 'POLYGON'):
        ring = geom.GetGeometryRef(0)
        numpoints = ring.GetPointCount()
        pointsX = []; pointsY = []
        for p in range(numpoints):
                lon, lat, z = ring.GetPoint(p)
                pointsX.append(lon)
                pointsY.append(lat)

    else:
        sys.exit("ERROR: Geometry needs to be either Polygon or Multipolygon")

    xmin = min(pointsX)
    xmax = max(pointsX)
    ymin = min(pointsY)
    ymax = max(pointsY)

    # Specify offset and rows and columns to read
    xoff = float((xmin - xOrigin)/pixelWidth)
    yoff = float((yOrigin - ymax)/pixelWidth)
    xcount = int((xmax - xmin)/pixelWidth)+1
    ycount = int((ymax - ymin)/pixelWidth)+1

    #print(xoff,yoff,xcount,ycount)

    # Create memory target raster
    target_ds = gdal.GetDriverByName('MEM').Create('', xcount, ycount, gdal.GDT_Byte)
    
    dirtemp = '/data/PASTAGEM/Mapeamento/MapBiomas/Versions/v5.0/TEMP/'

    file = dirtemp +str(name)+'_temp.tif'

    #print(xmin, pixelWidth, 0,ymax, 0, pixelHeight)

    if os.path.exists(file):
        target_ds = gdal.Open(file)
    else:
        target_ds = gdal.GetDriverByName('GTiff').Create(dirtemp+str(name)+'_temp.tif', xcount, ycount, 1, gdal.GDT_Byte,[ 'COMPRESS=LZW' ])
        target_ds.SetGeoTransform((xmin, pixelWidth, 0,ymax, 0, pixelHeight))
        # Create for target raster the same projection as for the value raster
        raster_srs = osr.SpatialReference()
        raster_srs.ImportFromWkt(raster.GetProjectionRef())
        target_ds.SetProjection(raster_srs.ExportToWkt())
        gdal.RasterizeLayer(target_ds, [1], layer, burn_values=[1], options = []) #, options = ["ALL_TOUCHED=TRUE", "BURN_VALUE_FROM"]);

    # Rasterize zone polygon to raster
    
    # Read raster as arrays
    print('Feature mask generated! Proceding to Z0N4L 5T4T1ST1C5')

    banddataraster = raster.GetRasterBand(1)
    bandmask = target_ds.GetRasterBand(1)

    rowSize = 256

    totalSum = 0

    beginAt = datetime.datetime.now()
    
    #print(ycount)

    result = {}

    #ycount = raster.RasterYSize
    #xcount = raster.RasterXSize

    for y in range(0,ycount,rowSize):

        if (y+rowSize) <= (ycount):
            dataraster = banddataraster.ReadAsArray(xoff, y+yoff,xcount, rowSize).astype(numpy.byte)
            datamask = bandmask.ReadAsArray(0, y, xcount,rowSize).astype(numpy.byte)
            
        else:
            dataraster = banddataraster.ReadAsArray(xoff, y+yoff,xcount, ycount - y).astype(numpy.byte)
            datamask = bandmask.ReadAsArray(0, y, xcount,ycount - y).astype(numpy.byte)

        zoneraster = dataraster[datamask==1]

        totalSum = totalSum + numpy.sum(zoneraster);

        dataraster = datamask = zoneraster = None
   
    print('Total time spend: ' + str(datetime.datetime.now()-beginAt))
    
    banddataraster = bandmask = raster = shp = target_ds = None

    return float(int(totalSum)*((pixelWidth)*(pixelHeight*-1))/10000.0)

def loop_zonal_stats(input_zone_polygon, input_value_raster,field_name):

    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()
    featList = range(lyr.GetFeatureCount())
    statDict = {}

    for FID in featList:

        feature = lyr.GetFeature(FID)
        name = feature.GetField(str(field_name))

        feat = lyr.GetFeature(FID)
        meanValue = zonal_stats(feat, input_zone_polygon, input_value_raster, FID)
           
        print('Biomas: ' + name,input_value_raster,meanValue)
    
        statDict[name] = meanValue
    return statDict

loop_zonal_stats(sys.argv[1], sys.argv[2],sys.argv[3])
