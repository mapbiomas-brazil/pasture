![Vinícius Mesquita](Logo_v2.png)

# Pasture Mapping Codes

This repository organizes the pasture mapping codes developed by [Laboratório de Processamento de Imagens e Geoprocessamento (LAPIG/UFG)](https://www.lapig.iesa.ufg.br/). The methology used by LAPIG team is avaliable in the paper of [PARENTE et al. (2017)](https://www.sciencedirect.com/science/article/pii/S0034425719303207) 

**Requisites**:

  * Python 3.7 or above
  
  * Gdal python package and Gdal Binaries
  
  * Scipy python package
  
  * Earth Engine python library
  
  * An folder synchronization with Google Drive ([For Windows](https://www.google.com/drive/download/) | [For Unix](https://github.com/odeke-em/drive))
  
  **Recommendations for Windows**: 
   * Install [Miniconda - Python 3.7](https://docs.conda.io/en/latest/miniconda.html) or above and the [Gdal package](https://anaconda.org/conda-forge/gdal). For Windows users, we need to add some system variables like:
      
      * PATH =  C:\ProgramData\Miniconda3; C:\ProgramData\Miniconda3\Library\bin; C:\ProgramData\Miniconda3\Scripts;
      * GDAL_DATA = C:\ProgramData\Miniconda3\Library\share\gdal
   
   * Install and configure the Earth Engine python library. [Click here to see how to install and configure with Miniconda.](https://developers.google.com/earth-engine/guides/python_install )
  
  **Recommendations for Unix**:
  
   * Install Python-Gdal and Gdal Binaries (sudo apt-get install -y python-gdal; sudo apt-get install -y gdal)
    
   * Install Earth Engine python library. [Click here to see how to install and configure with Python PIP.](https://developers.google.com/earth-engine/guides/python_install )   

# How to use

## 1. Run classification in Google Earth Engine (GEE)

You have 2 options for make your classification:

### Using Python with GEE

Before executing the first Python code, change the parameters below as desired:
```python

 # Build an file with Landsat WRS scenes you wanna use or you can uncomment the tiles used
 # to classify cultivated pasture (default) or natural pasture 
 * line 13 - tiles = open('tiles.in','r').read() #Cultivated Pasture tiles
 * line 14 - #tiles = open('tiles_natural.in','r').read() #Native Pasture tiles
 
 #Choose the classification mode between 0 (natural), cultivated (1) or any (None). P.S.: "Any" considers all the pasture samples as one. 
 * line 22 - pasture_type = 1
 
 #Choose the folder in Google Drive where the data will be saved
 * line 24 - folder = 'mapbiomas_col5_pasture'
```
Open the console terminal (Prompt on Windows) and run the these line: **python3 1_Pasture_classification_mapbiomas_COL_5.py**

### Using JavaScript in GEE
* [Access this link](https://code.earthengine.google.com/0c97565dcb06e343589451d08c3a4816) and, if desired, change the parameters of ***year***, ***landsatWRSPath***, ***landsatWRSRow***, ***my_folder***. After that you can click in **Run** and export your result in **Task**.

Also, you can change the training dataset (cultivated and natural) by changing the variable ***TRAIN_DATA*** (line 9).

## 2. Prepare the data for Multidimensional Median Filter

Merge the classifications files by year using the binaries **gdalbuildvrt** and **gdal_translate*. E.g.:

 * gdalbuildvrt lapig_pasture_map_<year xxxx>.vrt *_<year xxxx>_*.tif
 * gdal_translate lapig_pasture_map_<year xxxx>.vrt lapig_pasture_map_<year xxxx>.tif -co COMPRESS=LZW -co BIGTIFF=YES

In addition, if you want to view a file in a GIS like QGIS, just add a pyramid to your data using:

 * gdaladdo -ro lapig_pasture_map_<year xxxx>.tif 2 4 8 --config COMPRESS_OVERVIEW LZW --config USE_RRD YES
 
## 3. Applying the multidimensional median filter (3 x 3 x 5)

Before start this processs, be sure of the amount of memory available on your machine and define these variables on the script **2_Multidimensional_median_filter**:

```python
 * line 149 - inputDir = '/data/PASTAGEM/mapbiomas_col5_pasture/INPUT'
 * line 150 - outputDir = '/data/PASTAGEM/mapbiomas_col5_pasture/OUTPUT'
 * line 141 - files =  ['Y1985_planted.tif','Y1986_planted.tif','Y1987_planted.tif','Y1988_planted.tif','Y1989_planted.tif','Y1990_planted.tif','Y1991_planted.tif','Y1992_planted.tif','Y1993_planted.t if','Y1994_planted.tif','Y1995_planted.tif','Y1996_planted.tif','Y1997_planted.tif','Y1998_planted.tif','Y1999_planted.tif','Y2000_planted.tif','Y2001_planted.tif','Y2002_plante d.tif','Y2003_planted.tif','Y2004_planted.tif','Y2005_planted.tif','Y2006_planted.tif','Y2007_planted.tif','Y2008_planted.tif','Y2009_planted.tif','Y2010_planted.tif','Y2011_pla nted.tif','Y2012_planted.tif','Y2013_planted.tif','Y2014_planted.tif','Y2015_planted.tif','Y2016_planted.tif','Y2017_planted.tif','Y2018_planted.tif','Y2019_planted.tif']
```

This code need 2 arguments to run, the **start row** and the **window size** (e.g. python3 2_Multidimensional_median_filter 0 2048).

Because of the high memory consumption, this code works in blocks, so you probably will create an bash file (or batch - Windows) to make the process more autonomous. See the code examples below showing how to apply the filter by blocks.

### For Unix (Shell):
```shell
for X in {0..145446..2048} do python3 2_Multidimensional_median_filter.py $X 2048
```

### For Windows (DOS - batch):
``` dos
FOR /l %%X in (0,2048,145446) DO python3 2_Multidimensional_median_filter.py %%X 2048
```

P.S.: It's possible to obtain the image size using the binary *gdalinfo*.

## 4. Merging the files... again.

Like in the section 2, we will use the *gdalbuildvrt* and *gdal_translate* to merge the result files by year.


<details>
<summary> <b>Changelog</b> </summary>
<p>

* Version 1.0 released (Github version)

</p>
</details>
