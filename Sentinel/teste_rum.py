import ee
from dynaconf import settings
from Lapig.Lapig import HelpLapig
from Lapig.Functions import type_process
from requests import post
from pathlib import Path
from sys import exit
try:
    credentials = ee.ServiceAccountCredentials(
        'nxgame2009@gmail.com',#settings.GMAIL, 
        f"{str(Path.home())}/{settings.PRIVATEKEY}")
    ee.Initialize()
except FileNotFoundError as e:
    print(e)
    exit(1)



def generate_image(name):
    # Import the Landsat 8 TOA image collection.
    l8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA');

    ROI = ee.Geometry.Polygon(
        [[[-52.18234904583088, -14.82063229778676],
        [-52.18234904583088, -14.859461214385924],
        [-52.13668711956135, -14.859461214385924],
        [-52.13668711956135, -14.82063229778676]]]
    );

    image = ee.Image(
    l8.filterBounds(ROI)
        .filterDate(f'{name}-01-01', f'{name}-12-31')
        .sort('CLOUD_COVER')
        .median().select(['B5','B4'])
    );

    return ROI,image.clip(ROI)



def get_Exports(version,name):
    ROI,imgae = generate_image(name)
    task = ee.batch.Export.image.toDrive(
    **{
        'image':imgae ,
        'description': f'pastureMapping_S2_col6_2020_{name}' ,
        'folder':'pastureMapping_S2_col6_2020',
        'fileNamePrefix':f'{version}-pastureMapping_S2_col6_2020_{name}',
        'region': ROI,
        'scale': 30,
        'maxPixels': 1.0E13
    });
    task.start()
    rest = {
            'id_': f'{version}_{name}',
            'version':version,
            'name':name,
            'state':type_process(task.state),
            'task_id':task.id
    }

    return task.id,post(f'http://{settings.SERVER}:{settings.PORT}/update',json= rest)








