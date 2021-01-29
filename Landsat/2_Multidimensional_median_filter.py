import sys, os
import datetime
import gdal, ogr, osr
import numpy as np
import time
from scipy.ndimage import median_filter

def getInputFiles(basedir, files):

  inputFiles = []

  for file in files:

    inputFilepath = basedir+'/'+file

    if os.path.exists(inputFilepath):
      inputFiles.append(inputFilepath)
      
    else:
      print(inputFilepath + ' not exists !')

  return inputFiles

def createOutputFiles(inputFiles, outputFiles):

  for i in range(0, len(inputFiles)):
    inputFile = inputFiles[i]
    outputFile = outputFiles[i]
    os.remove(outputFile)
    if (not os.path.exists(outputFile)):
      createImageAsReference(inputFile, outputFile)
    else:
      print(outputFile + " file exists")

def createOutputImage(referenceFile, outputFile, startRow, xSize, data, imageFormat = 'GTiff'):
  
  driver = gdal.GetDriverByName(imageFormat)
  referenceDs = gdal.Open(referenceFile)
  referenceBand = referenceDs.GetRasterBand(1)
  ySize = referenceDs.RasterYSize

  originX, pixelWidth, _, originY, _, pixelHeight  = referenceDs.GetGeoTransform()
  
  newOriginX = startRow*pixelWidth + originX

  outRasterSRS = osr.SpatialReference()
  outRasterSRS.ImportFromWkt(referenceDs.GetProjectionRef())

  #print("Creating " + outputFile + " ("+str(xSize)+"x"+str(ySize)+")")
  outRaster = driver.Create(outputFile, xSize, ySize, 1, referenceBand.DataType, [ 'COMPRESS=LZW' ])
  outRaster.SetGeoTransform((newOriginX, pixelWidth, 0, originY, 0, pixelHeight))
  outRaster.SetProjection(outRasterSRS.ExportToWkt())
  rasterBand = outRaster.GetRasterBand(1)
  rasterBand.WriteArray(data)
  rasterBand.FlushCache()

  return outRaster

def getInputWindow(inputFile, startRow, endRow):
  ds = gdal.Open(inputFile)
  Xsize = ds.RasterXSize
  Ysize = ds.RasterYSize

  xoff = startRow - 1
  winXsize = (endRow - startRow) + 2

  #print(xoff,winXsize, Xsize,xoff+winXsize)

  if (xoff < 0):
    xoff = 0
  if (xoff+winXsize > Xsize):
    winXsize = Xsize - xoff

  #print(winXsize)

  return xoff, 0, winXsize, Ysize

def getOutputWindow(inputFile, startRow, endRow):
  ds = gdal.Open(inputFile)
  Xsize = ds.RasterXSize
  Ysize = ds.RasterYSize

  outStartRow = 1
  outEndRow = (endRow - startRow)+1

  if startRow == 0:
    outStartRow = 0
    outEndRow = outEndRow-1

  return startRow, 0, outStartRow, outEndRow

def readData(inputFiles, startRow, endRow):
  
  result = []

  xoff, yoff, winXsize, Ysize = getInputWindow(inputFiles[0], startRow, endRow)

  #print(xoff, yoff, winXsize, Ysize)

  for inputFile in inputFiles:
    ds = gdal.Open(inputFile)
    rasterBand = ds.GetRasterBand(1)
    dataraster = rasterBand.ReadAsArray(xoff, yoff, winXsize, Ysize)
    result.append(dataraster)

  return np.stack(result)

def writeData(outputBaseDir, inputFiles, startRow, endRow, outputData):
    
  referenceFile = inputFiles[0]
  xoff, yoff, outStartRow, outEndRow = getOutputWindow(referenceFile, startRow, endRow)

  for i in range(0, len(inputFiles)):
    inputFile = os.path.basename(inputFiles[i])
    outputDir = outputBaseDir + '/' + inputFile.replace('.tif', '')

    if not os.path.exists(outputDir):
      try:
        os.makedirs(outputDir)
      except:
        pass

    outputfile = outputDir + '/' + inputFile.replace('.tif', '_tsmedian-' + str(startRow) + '-' + str(endRow) + '.tif')
    print(outputfile)
    
    xSize = (endRow - startRow)
    ySize = 1

    data = outputData[i,:,outStartRow:outEndRow]
    outRaster = createOutputImage(referenceFile, outputfile, startRow, xSize, data)

def applyFilter(data):
  return median_filter(data, size=(5,3,3),mode = 'mirror')

def log(*arg):
  
  dateStr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  msgList = list(arg)
  msgList = [var for var in msgList if var]
  msg = " ".join(msgList)

  identifier=str(startRow)+'-'+str(endRow)
  print("{dateStr} [{identifier}] {msg}".format(dateStr=dateStr, identifier=identifier, msg=msg))

def formatTime(timeValue):
  return str(round( (timeValue),2))

inputDir = '/data/PASTAGEM/mapbiomas_col5_pasture/INPUT'
outputDir = '/data/PASTAGEM/mapbiomas_col5_pasture/OUTPUT'
files = ['Y1985_planted.tif','Y1986_planted.tif','Y1987_planted.tif','Y1988_planted.tif','Y1989_planted.tif','Y1990_planted.tif','Y1991_planted.tif','Y1992_planted.tif','Y1993_planted.tif','Y1994_planted.tif','Y1995_planted.tif','Y1996_planted.tif','Y1997_planted.tif','Y1998_planted.tif','Y1999_planted.tif','Y2000_planted.tif','Y2001_planted.tif','Y2002_planted.tif','Y2003_planted.tif','Y2004_planted.tif','Y2005_planted.tif','Y2006_planted.tif','Y2007_planted.tif','Y2008_planted.tif','Y2009_planted.tif','Y2010_planted.tif','Y2011_planted.tif','Y2012_planted.tif','Y2013_planted.tif','Y2014_planted.tif','Y2015_planted.tif','Y2016_planted.tif','Y2017_planted.tif','Y2018_planted.tif','Y2019_planted.tif']

startRow = int(sys.argv[1])
endRow = startRow + int(sys.argv[2])

log("Starting")

inputFiles = getInputFiles(inputDir, files)

gdal.SetCacheMax(2**30)

readingTime = time.time()
data = readData(inputFiles, startRow, endRow)
readingTime = (time.time() - readingTime)

log(' Data read time: ', formatTime(readingTime), 'segs')

if np.sum(data) != 0:
  
  #print('Input data:' + str(data.shape))

  filterTime = time.time()
  dataFiltered = applyFilter(data)
  filterTime = (time.time() - filterTime)

  log(' Filter application time: ', formatTime(filterTime), 'segs')
  #print('Output data:' + str(dataFiltered.shape))

  writingTime = time.time()
  writeData(outputDir, inputFiles, startRow, endRow, dataFiltered)
  writingTime = (time.time() - writingTime)

  log(' Data write time: ', formatTime(writingTime), 'segs')
  log(' CPU/IO relation: ', str(filterTime / (readingTime+writingTime)) )
  log(' Total time:', str(filterTime+readingTime+writingTime))
  
else:
  log(" Only zero values")

log("Finished")
