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
            #print(ycount - y,ycount,y,y+rowSize)
            #print(xcount,ycount)
            #print(xoff, y+yoff,xcount, rowSize)
            #dataraster = banddataraster.ReadAsArray(0, y, xcount,rowSize).astype(numpy.byte)
            #datamask = bandmask.ReadAsArray(x-xoff, y-yoff,lineSize, rowSize).astype(numpy.byte)

            dataraster = banddataraster.ReadAsArray(xoff, y+yoff,xcount, rowSize).astype(numpy.byte)
            datamask = bandmask.ReadAsArray(0, y, xcount,rowSize).astype(numpy.byte)
            
        else:
            #print('hu3')
            #dataraster = banddataraster.ReadAsArray(0, y, xcount,ycount - y).astype(numpy.byte)
            #datamask = bandmask.ReadAsArray(x-xoff, y-yoff,lineSize, ycount - (y-yoff)).astype(numpy.byte)

            dataraster = banddataraster.ReadAsArray(xoff, y+yoff,xcount, ycount - y).astype(numpy.byte)
            datamask = bandmask.ReadAsArray(0, y, xcount,ycount - y).astype(numpy.byte)

        zoneraster = dataraster[datamask==1]

        #print(zoneraster)

        #zoneraster = banddataraster.ReadAsArray(0, 0, xcount,ycount).astype(numpy.byte)
        #print(numpy.sum(zoneraster))
        totalSum = totalSum + numpy.sum(zoneraster);

        ##result.append(numpy.nanmean(zoneraster))
        #result.append(stats.mode(zoneraster, axis=None)[0][0])

        #print(stats.mode(zoneraster, axis=None)[0][0])

        #print(totalSum*((pixelWidth)*(pixelWidth))/10000.0)
        dataraster = datamask = zoneraster = None
            
        #print('Total time spend: ' + str(datetime.datetime.now()-beginAt))
    
        #banddataraster = bandmask = raster = shp = target_ds = None

        #uniques, counts = numpy.unique(dataraster, return_counts=True)

        #for i,u in enumerate(uniques):
        #    key = '0'+ str(u) if len(str(u)) == 1 else str(u)
        #    if key not in result:
        #        result[key] = 0
        #    result[key] = result[key] + counts[i]
        #resultStr = " "
        #
        #for key in range(1,4):
        #    if str(key) in result:
        #        resultStr = resultStr + str(result[str(key)]) + " "
        #    else:
        #        resultStr = resultStr + "0"
        ##totalSum = totalSum + numpy.sum(zoneraster);
        #


        #dataraster = datamask = None
        #resultStr = resultStr + "0 "

        #uniques, counts = numpy.unique(zoneraster, return_counts=True)

        #print(uniques,counts)

        #for i,u in enumerate(uniques):
        #
        #    if (len(str(u))) == 1:
        #        key = '0'+str(u)
        #    else:
        #        key = str(u)
        #    if key not in result:
        #        result[key] = 0
        #    result[key] = result[key] + counts[i]

        #keylist = list(result.keys())

        #keylist.sort()

        #for key in keylist:
        #    print("{0}: {1}".format(key, result[key]))
        
    print('Total time spend: ' + str(datetime.datetime.now()-beginAt))
    
    banddataraster = bandmask = raster = shp = target_ds = None

    #return result

    #return stats.mode(result, axis=None)[0][0]

    #return int(totalSum)
    return float(int(totalSum)*((pixelWidth)*(pixelHeight*-1))/10000.0)

def loop_zonal_stats(input_zone_polygon, input_value_raster,field_name):

    shp = ogr.Open(input_zone_polygon)
    lyr = shp.GetLayer()
    featList = range(lyr.GetFeatureCount())
    statDict = {}

    for FID in featList:
        #FID = 3
        feature = lyr.GetFeature(FID)
        name = feature.GetField(str(field_name))

        #print(name)

        #if name == 'Mata Atlântica':

        feat = lyr.GetFeature(FID)
        meanValue = zonal_stats(feat, input_zone_polygon, input_value_raster, FID)
           
        print('Biomas: ' + name,input_value_raster,meanValue)
        #print(input_value_raster,meanValue)
        
        #keylist = list(meanValue.keys())
        #keylist.sort()
        #
        #for key in keylist:
        #    print("{0}: {1},".format(key, meanValue[key]),end =" ")
    
        statDict[name] = meanValue
    return statDict

loop_zonal_stats(sys.argv[1], sys.argv[2],sys.argv[3])