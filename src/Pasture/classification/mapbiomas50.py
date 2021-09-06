from loguru import logger
from Pasture.help.Lapig import HelpLapig
from Pasture.help.Functions import login_gee
import ee
import sys

def main(settings):
    login_gee(ee)
    help_lapig = HelpLapig(ee)

    
    L8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
    L5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_TOA")
    L7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")

    LANDSAT_GRID = ee.FeatureCollection(settings.LANDSAT_GRID)

    TRAIN_DATA = ee.FeatureCollection(settings.COL5_TRAIN_DATA_PLANTED)
 

    def clipCollection(img):
        #wrsProps = ee.Number.parse(img.get('WRS_PATH')).format().cat('/').cat(ee.Number.parse(img.get('WRS_ROW')).format())
        gridSelect = LANDSAT_GRID.filter(ee.Filter.eq('SPRNOME', query_SPRNOME))
        return img.clip(gridSelect)

    for  nb_grd in settings.GRIDLIST:
        class_stack = ee.Image([0])

        landsatWRSPath = nb_grd[1:4]; #Landsat satellite WRS orbital path number (1 - 251) / Works only for Brazil;
        landsatWRSRow = nb_grd[4:7]; # Landsat satellite WRS row (1-248) / Works only for Brazil;
        

        #*******************************************************************/
        #*************** Classification Methods ****************************/
        #*******************************************************************/

        for year in range(settings.START_YEAR,settings.END_YEAR+1):

            samplingArea, neighborhoodArea = help_lapig.getNeibArea(landsatWRSPath,landsatWRSRow,LANDSAT_GRID)


            
            classFieldName = f'cons_{year}'; #Collum used as reference for classifier

            classificationArea = LANDSAT_GRID.filter(ee.Filter.eq('TILE_T',nb_grd))
            
            #Generates spectral indexes based on the satellite data
            def spectralFeatures(image):
                if year >2012:
                
                    qaImage = ee.Image(image.select(['BQA']));
                    image = image.mask(qaImage.eq(2720));
                    
                    ndvi = image.expression(settings.NDVI_L8).select([0],['NDVI']);
                    ndwi = image.expression(settings.NDWI_L8).select([0],['NDWI']);
                    cai = image.expression(settings.CAI_L8).select([0],['CAI']);
                    
                    image = image.addBands([ndvi,ndwi,cai]);
                    
                    return image;
                else:
                
                    qaImage = ee.Image(image.select(['BQA']));
                    image = image.mask(qaImage.eq(672));
                    
                    ndvi = image.expression(settings.NDVI_L5_7).select([0],['NDVI']);
                    ndwi = image.expression(settings.NDWI_L5_7).select([0],['NDWI']);
                    cai = image.expression(settings.CAI_L5_7).select([0],['CAI']);
                    
                    image = image.addBands([ndvi,ndwi,cai]);
                
                    return image;
                
            
            
            #Builds spectro-temporal features from spectral data and spectral indexes
            def temporalFeatures(image, landsatBandsWetAmp):
                            
                amp = image.reduce(ee.Reducer.max()).subtract(image.reduce(ee.Reducer.min())).rename(landsatBandsWetAmp)
            
                return ee.Image().select().addBands([
                    image.reduce(ee.Reducer.min()),
                    image.reduce(ee.Reducer.max()),
                    image.reduce(ee.Reducer.median()),
                    amp,
                    image.reduce(ee.Reducer.stdDev())
                ])
                
                
            
                
            def temporalPercs(image):
                percs = image.reduce(ee.Reducer.percentile([10,25,75,90]))
                return ee.Image().select().addBands([percs])

            SRTM = help_lapig.getSRTM()
            elevation = SRTM["elevation"]
            slope = SRTM["slope"]
            aspect = SRTM["aspect"]
                
            #*************************************/
            
            #Defines the date window that will be used to filter the satellite collection
            startDate = f'{year-1}-07-01';
            endDate = f'{year+1}-06-30';
            
            landsatCollection = ee.ImageCollection(ee.Algorithms.If(ee.Number(year).gt(2012), L8, ee.Algorithms.If(ee.List([2000,2001,2002,2012]).contains(year), L7, L5)))
            
            bands = ee.Algorithms.If(ee.Number(year).gt(2012),["B3","B4","B5","B6","B7","NDVI","NDWI","CAI"],["B2","B3","B4","B5","B7","NDVI","NDWI","CAI"])
            
           
            
            landsatBandsWet = ['green_wet','red_wet','nir_wet', 'swir1_wet','swir2_wet','ndvi_wet','ndwi_wet','cai_wet'];
            landsatBandsWetAmp = ['green_wet_amp','red_wet_amp','nir_wet_amp', 'swir1_wet_amp','swir2_wet_amp','ndvi_wet_amp','ndwi_wet_amp','cai_wet_amp'];

            neibData = []
            
            #Builds an mask based on the NDVI percentil 25%
            def onlyWetSeasonNei(image):
                seasonMask = image.select("ndvi_wet").gte(wetThresholdNei)
                return image.mask(seasonMask);
            
            
            #Generates spectro-temporal information/bands for sampling and classification
            for  i in neighborhoodArea:
                
                sceneInfo = i.split('/')
                
                query_SPRNOME = f'{int(sceneInfo[0])}/{int(sceneInfo[1])}' # Usado no clipCollection
                spectralDataNei = (landsatCollection
                                    .filterMetadata('WRS_PATH', 'equals', int(sceneInfo[0]))
                                    .filterMetadata('WRS_ROW', 'equals', int(sceneInfo[1]))
                                    .filterDate(startDate, endDate)
                                    .map(spectralFeatures)
                                    .map(clipCollection)
                                    .select(bands)
                )
                                    #.select(['B3','B4','B5','B6','B7','NDVI','NDWI','CAI'])
                
                wetThresholdNei = (spectralDataNei
                                        .select("NDVI")
                                        .reduce(ee.Reducer.percentile([25]))
                )
                                        
                wetSpectralDataNei = (spectralDataNei
                                        .select(bands, landsatBandsWet)
                                        .map(onlyWetSeasonNei)
                )
                
                temporalData = help_lapig.getLatLong(temporalPercs(wetSpectralDataNei)).addBands([
                    temporalFeatures(
                        wetSpectralDataNei,
                        landsatBandsWetAmp
                        ),
                elevation,slope])
                
                bandSize = ee.Number(temporalData.bandNames().size())
                
                neibData.append(temporalData.set({'BandNumber': bandSize}))
            
            
                
            neibCollection = ee.ImageCollection(neibData).filter(ee.Filter.gt('BandNumber',4)).mosaic().clip(samplingArea)
            mainScene = neibCollection.clip(classificationArea)
            
            #Map.addLayer()
                
            features = [mainScene, neibCollection]
            
            #Organizes the samples for the classifier training phase
            
            trainSamples = TRAIN_DATA.select(classFieldName).filterBounds(samplingArea)
            
            classifier = ee.Classifier.smileRandomForest(settings.RFNTREES, settings.RFVARPERSPLIT, 1, settings.RFBAGFRACTION, None, year);
            classifier = classifier.setOutputMode('PROBABILITY');
            
            trainSamplesFeeded = features[1].sampleRegions(**{
                'collection': trainSamples.filter(ee.Filter.neq(classFieldName,None)),
                'properties': [classFieldName],
                'scale': 30,
                'tileScale': 16
            });

            classifier = classifier.train(trainSamplesFeeded, classFieldName);
            
            classification = ee.Image(features[0]).classify(classifier).select(0);
            
            
            #*******************************************************************/
            #*************** Classification Approach ****************************/
            #*******************************************************************/
            
            class_stack = class_stack.addBands(ee.Image(classification).rename(f'Y{year}'))
        
        name = f"pasture_col5_{landsatWRSPath}_{landsatWRSRow}_{settings.START_YEAR}_{settings.END_YEAR}_stack_LAPIG"
        task = ee.batch.Export.image.toDrive(
            **{
                "image": class_stack.multiply(10000).int16(),
                "description": name,
                "fileNamePrefix": name,
                "folder": settings.FOLDER,
                "region": classificationArea.geometry().bounds(),
                "scale": 30,
                "maxPixels": 1.0e13,
            }
        )
        try:
            task.start()
            logger.info(f"A task named {name} has been created and will be saved in the {settings.FOLDER} folder in Google Drive")
        except Exception as e:
            logger.warning(f"Error: {e}")
