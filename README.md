![Vinícius Mesquita](Logo_v2.png)

# Pasture Mapping Codes

This repository organizes the pasture mapping codes developed by [Laboratório de Processamento de Imagens e Geoprocessamento (LAPIG/UFG)](https://www.lapig.iesa.ufg.br/). The methology used by LAPIG team is avaliable in the paper of [PARENTE et al. (2017)](https://www.sciencedirect.com/science/article/pii/S0034425719303207) 

**Requisites**:

* Python 3.9 or above
  
* Gdal python package and Gdal Binaries
  
* scipy python package

* joblib python package
  
* Earth Engine python library
  
* An folder synchronization with Google Drive ([For Windows](https://www.google.com/drive/download/) | [For Unix](https://github.com/odeke-em/drive))
  
**Recommendations for Windows**: 
* Install [Miniconda - Python > 3.9]([https://python-poetry.org/docs/#windows-powershell-install-instructions](https://docs.anaconda.com/miniconda/) or above and the [Gdal package](https://anaconda.org/conda-forge/gdal). For Windows users, we need to add some system variables like:
      
* PATH =  C:\ProgramData\Miniconda3\Library\bin;
* GDAL_DATA = C:\ProgramData\Miniconda3\Library\share\gdal
  
**Recommendations for Unix**:

* Install Python-Gdal and Gdal Binaries (sudo apt-get install -y python-gdal; sudo apt-get install -y gdal)

* Install Earth Engine python library. [Click here to see how to install and configure with Python PIP.](https://developers.google.com/earth-engine/guides/python_install )

# How to use

## 1. Run classification in Google Earth Engine (GEE)

You have 2 options for make your classification:

### Using Python with GEE

First download/clone the in this Github repository, then acess the **1_gee_processing** folder through the system terminal/prompt and execute the command bellow:

```shell
python LANDSAT_COL9_1985_2023_justRun_v2.py
```

### Using JavaScript in GEE

* [Access this link](https://code.earthengine.google.com/0ce5f1d6cd5d1c9d1c3991740fb11606) and, if desired, change the parameters of ***year***, ***IBGE_Chart***, ***my_folder***. After that you can click in **Run** and export your result in **Task**.

Also, you can change the training dataset (cultivated and natural) by changing the variable ***TRAIN_DATA*** (line 9).

## 2. Prepare the data for Multidimensional Median Filter

Merge the classifications files by year using the binaries **gdalbuildvrt** and **gdal_translate*. E.g.:

* gdalbuildvrt lapig_pasture_map_|year xxxx|.vrt *_|year xxxx|_*.tif
* gdal_translate lapig_pasture_map_|year xxxx|.vrt lapig_pasture_map_|year xxxx|.tif -co COMPRESS=LZW -co BIGTIFF=YES

In addition, if you want to view a file in a GIS like QGIS, just add a pyramid to your data using:

* gdaladdo -ro lapig_pasture_map_<year xxxx>.tif 2 4 8 --config COMPRESS_OVERVIEW LZW --config USE_RRD YES

## 3. Applying the multidimensional median filter (3 x 3 x 5)

This code need 2 arguments to run, the **<input directory>** and the **<output directory>** (e.g. python 2_Multidimensional_median_filter prob_rasters_dir filtered_rasters_dir).

```shell

python 2_Multidimensional_median_filter_parallel.py <input_dir_name> <output_dir_name>

```

## 4. Merging the files... again.

Like in the section 2, we will use the *gdalbuildvrt* and *gdal_translate* to merge the result files by year.

<details>
<summary> <b>Changelog</b> </summary>
<p>* Version 3.0 released (Github version)</p>
</details>
