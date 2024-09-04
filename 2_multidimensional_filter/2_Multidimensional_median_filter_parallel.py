import os, sys
import glob
import datetime
from osgeo import gdal, osr
import numpy as np
import time
from scipy.ndimage import median_filter
from joblib import Parallel, delayed

def getInputFiles(files):

  inputFiles = []

  for file in files:

    inputFilepath = file

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

  outRaster = driver.Create(outputFile, xSize, ySize, 1, gdal.GDT_Byte, [ 'COMPRESS=LZW','TILED=YES','BIGTIFF=YES' ])
  outRaster.SetGeoTransform((newOriginX, pixelWidth, 0, originY, 0, pixelHeight))
  outRaster.SetProjection(outRasterSRS.ExportToWkt())
  rasterBand = outRaster.GetRasterBand(1)
  rasterBand.WriteArray(np.where(data >= 5100, 1, 0).astype(np.byte))
  rasterBand.FlushCache()

  return outRaster

def getInputWindow(inputFile, startRow, endRow):
  ds = gdal.Open(inputFile)
  Xsize = ds.RasterXSize
  Ysize = ds.RasterYSize

  xoff = startRow - 1
  winXsize = (endRow - startRow) + 2

  if (xoff < 0):
    xoff = 0
  if (xoff+winXsize > Xsize):
    winXsize = Xsize - xoff

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
    
    xSize = (endRow - startRow)
    ySize = 1

    data = outputData[i,:,outStartRow:outEndRow]
    outRaster = createOutputImage(referenceFile, outputfile, startRow, xSize, data)

def applyFilter(data):
  return median_filter(data, size=(5,3,3),mode = 'reflect')

def formatTime(timeValue):
  return str(round( (timeValue),2))

def run_process(startRow,endRow,input_dir,output_dir):

  def log(*arg):
  
    dateStr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msgList = list(arg)
    msgList = [var for var in msgList if var]
    msg = " ".join(msgList)

    identifier=str(startRow)+'-'+str(endRow)
    print("{dateStr} [{identifier}] {msg}".format(dateStr=dateStr, identifier=identifier, msg=msg))

  inputDir = input_dir
  outputDir = output_dir
  files = glob.glob(os.path.join(input_dir,'*.tif'))
  
  log("Starting")
  
  inputFiles = getInputFiles(files)
  
  gdal.SetCacheMax(2**30)
  
  readingTime = time.time()
  data = readData(inputFiles, startRow, endRow)
  readingTime = (time.time() - readingTime)
  
  log(' Data read time: ', formatTime(readingTime), 'segs')
  
  if np.sum(data) != 0:
    
    filterTime = time.time()
    dataFiltered = applyFilter(data)
    filterTime = (time.time() - filterTime)
  
    log(' Filter application time: ', formatTime(filterTime), 'segs')

    writingTime = time.time()
    writeData(outputDir, inputFiles, startRow, endRow, dataFiltered)
    writingTime = (time.time() - writingTime)
  
    log(' Data write time: ', formatTime(writingTime), 'segs')
    log(' CPU/IO relation: ', str(filterTime / (readingTime+writingTime)) )
    log(' Total time:', str(filterTime+readingTime+writingTime))
    
  else:
    log(" Only zero values")
  
  log("Finished")

if __name__ == '__main__':

  input_dir = sys.argv[1]
  output_dir = sys.argv[2]

  start_step = 0
  buffer_size = 256
  rowSize = gdal.Open(glob.glob(os.path.join(input_dir,'*.tif'))[0]).RasterXSize

  loopList = list(range(start_step,rowSize,buffer_size))

  if (loopList[-1]+buffer_size) > rowSize:
    loopList.append(rowSize)

  worker_args = [
    (startRow,startRow+buffer_size,input_dir,output_dir) \
    for startRow in loopList[:-2]
  ]

  worker_args.append((loopList[-2],rowSize,input_dir,output_dir))

  Parallel(n_jobs=6, backend='multiprocessing')(delayed(run_process)(*args) for args in worker_args)
