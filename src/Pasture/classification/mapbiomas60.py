from Pasture.help.Lapig import HelpLapig
from Pasture.help.Functions import login_gee
import ee
import sys
from loguru import logger

def main(settings):
    login_gee(ee)
    help_lapig = HelpLapig(ee)

    L8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
    L5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_TOA")
    L7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")
    LANDSAT_GRID = ee.FeatureCollection(settings.LANDSAT_GRID)
    COL5_TRAIN_DATA_PLANTED = ee.FeatureCollection(settings.COL5_TRAIN_DATA_PLANTED)
    COL5_TRAIN_DATA_NATURAL = ee.FeatureCollection(
        "users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_natural_QGIS"
    )

    COL6_TRAIN_DATA = ee.FeatureCollection(
        settings.COL6_TRAIN_DATA
    )


    # *******************************************************************/
    # *************** Classification Parameters *************************/
    # *******************************************************************/
    # year = 2017 # Year choosed;

    def clipCollection(img):
        
        gridSelect = LANDSAT_GRID.filter(ee.Filter.eq("SPRNOME", query_SPRNOME))
        return img.clip(gridSelect)

    for nb_grd in settings.GRIDLIST:

        class_stack = ee.Image([0])

        landsatWRSPath = nb_grd[1:4]
        # Landsat satellite WRS orbital path number (1 - 251) / Works only for Brazil;
        landsatWRSRow = nb_grd[4:7]
        #  Landsat satellite WRS row (1-248) / Works only for Brazil;
        
        
        
        # *******************************************************************/
        # *************** Classification Methods ****************************/
        # *******************************************************************/

        for year in range(settings.START_YEAR, settings.END_YEAR + 1):

            samplingArea, neighborhoodArea = help_lapig.getNeibArea(
                landsatWRSPath, landsatWRSRow, LANDSAT_GRID
            )
            
            

            classificationArea = LANDSAT_GRID.filter(ee.Filter.eq("TILE_T", nb_grd))

            # Builds spectro-temporal features from spectral data and spectral indexes
            def temporalFeatures(image, landsatBandsWetAmp):

                _min = image.reduce(ee.Reducer.min())
                _max = image.reduce(ee.Reducer.max())
                median = image.reduce(ee.Reducer.median())
                stdv = image.reduce(ee.Reducer.stdDev())
                amp = (
                    image.reduce(ee.Reducer.max())
                    .subtract(image.reduce(ee.Reducer.min()))
                    .rename(landsatBandsWetAmp)
                )

                result = ee.Image().select().addBands([_min, _max, median, amp, stdv])

                return result

            def temporalPercs(image):
                percs = image.reduce(ee.Reducer.percentile([10, 25, 75, 90]))
                result = ee.Image().select().addBands([percs])
                return result

            SRTM = help_lapig.getSRTM()
            elevation = SRTM["elevation"]
            slope = SRTM["slope"]
            aspect = SRTM["aspect"]
            trainSamplesFeeded = ee.FeatureCollection([])
            listYearsApp = {
                2018: [2015, 2016, 2017, 2018, 2019],
                2019: [2016, 2017, 2018, 2019, 2020],
                2020: [2016, 2017, 2018, 2019, 2020],
            }

            for year_images in listYearsApp[year]:

                # Generates spectral indexes based on the satellite data
                def spectralFeatures(image):

                    if year_images > 2012:

                        qaImage = ee.Image(image.select(["BQA"]))
                        image = image.mask(qaImage.eq(2720))

                        b3 = image.expression(settings.B3).select([0], ["B3"])
                        b4 = image.expression(settings.B4).select([0], ["B4"])
                        b5 = image.expression(settings.B5).select([0], ["B5"])
                        b6 = image.expression(settings.B6_L8).select([0], ["B6"])
                        b7 = image.expression(settings.B7).select([0], ["B7"])

                        ndvi = image.expression(settings.NDVI_L8).select([0], ["NDVI"])
                        ndwi = image.expression(settings.NDWI_L8).select([0], ["NDWI"])
                        cai = image.expression(settings.CAI_L8).select([0], ["CAI"])

                        image = (
                            ee.Image()
                            .addBands([b3, b4, b5, b6, b7, ndvi, ndwi, cai])
                            .copyProperties(image)
                        )

                        return image
                    else:

                        qaImage = ee.Image(image.select(["BQA"]))
                        image = image.mask(qaImage.eq(672))

                        b2 = image.expression(settings.B2).select([0], ["B2"])
                        b3 = image.expression(settings.B3).select([0], ["B3"])
                        b4 = image.expression(settings.B4).select([0], ["B4"])
                        b5 = image.expression(settings.B5).select([0], ["B5"])
                        b7 = image.expression(settings.B7).select([0], ["B7"])

                        ndvi = image.expression(settings.NDVI_L5_7).select(
                            [0], ["NDVI"]
                        )
                        ndwi = image.expression(settings.NDWI_L5_7).select(
                            [0], ["NDWI"]
                        )
                        cai = image.expression(settings.CAI_L5_7).select([0], ["CAI"])

                        image = (
                            ee.Image()
                            .addBands([b2, b3, b4, b5, b7, ndvi, ndwi, cai])
                            .copyProperties(image)
                        )

                        return image

                # Defines the date window that will be used to filter the satellite collection
                startDate = f"{year_images - 1}-07-01"
                endDate = f"{year_images + 1}-06-30"

                landsatCollection = ee.ImageCollection(
                    ee.Algorithms.If(
                        ee.Number(year_images).gt(2012),
                        L8,
                        ee.Algorithms.If(
                            ee.List([2000, 2001, 2002, 2012]).contains(year_images),
                            L7,
                            L5,
                        ),
                    )
                )

                bands = ee.Algorithms.If(
                    ee.Number(year_images).gt(2012),
                    ["B3", "B4", "B5", "B6", "B7", "NDVI", "NDWI", "CAI"],
                    ["B2", "B3", "B4", "B5", "B7", "NDVI", "NDWI", "CAI"],
                )

                landsatBandsWet = [
                    "green_wet",
                    "red_wet",
                    "nir_wet",
                    "swir1_wet",
                    "swir2_wet",
                    "ndvi_wet",
                    "ndwi_wet",
                    "cai_wet",
                ]
                landsatBandsWetAmp = [
                    "green_wet_amp",
                    "red_wet_amp",
                    "nir_wet_amp",
                    "swir1_wet_amp",
                    "swir2_wet_amp",
                    "ndvi_wet_amp",
                    "ndwi_wet_amp",
                    "cai_wet_amp",
                ]

                neibData = []

                # Builds an mask based on the NDVI percentil 25%
                def onlyWetSeasonNei(image):
                    seasonMask = image.select("ndvi_wet").gte(wetThresholdNei)
                    return image.mask(seasonMask)

                # Generates spectro-temporal information/bands for sampling and classification
                for i in neighborhoodArea:

                    sceneInfo = i.split("/")
                    query_SPRNOME = f'{int(sceneInfo[0])}/{int(sceneInfo[1])}'
                    spectralDataNei = (
                        landsatCollection.filterMetadata(
                            "WRS_PATH", "equals", int(sceneInfo[0])
                        )
                        .filterMetadata("WRS_ROW", "equals", int(sceneInfo[1]))
                        .filterDate(startDate, endDate)
                        .map(spectralFeatures)
                        .map(clipCollection)
                        .select(bands)
                    )
                    
                    
                    # .select(['B3','B4','B5','B6','B7','NDVI','NDWI','CAI'])

                    wetThresholdNei = spectralDataNei.select("NDVI").reduce(
                        ee.Reducer.percentile([25])
                    )

                    wetSpectralDataNei = spectralDataNei.select(
                        bands, landsatBandsWet
                    ).map(onlyWetSeasonNei)

                    temporalData = help_lapig.getLatLong(
                        temporalPercs(wetSpectralDataNei)
                    ).addBands(
                        [
                            temporalFeatures(wetSpectralDataNei, landsatBandsWetAmp),
                            elevation,
                            slope,
                        ]
                    )

                    bandSize = ee.Number(temporalData.bandNames().size())

                    neibData.append(temporalData.set({"BandNumber": bandSize}))

                neibCollection = (
                    ee.ImageCollection(neibData)
                    .filter(ee.Filter.gt("BandNumber", 4))
                    .mosaic()
                    .clip(samplingArea)
                )

                classFieldName = f"cons_{year_images}"
                # Collum used as reference for classifier
                
                if year_images > 2017:
                    trainSamples = COL6_TRAIN_DATA.select(
                        [classFieldName], ["classValues"]
                    ).filterBounds(samplingArea)
                else:
                    trainSamples = COL5_TRAIN_DATA_PLANTED.select(
                        [classFieldName], ["classValues"]
                    ).filterBounds(samplingArea)


                
                trainSamplesFeeded_year = neibCollection.sampleRegions(
                    **{
                        "collection": trainSamples.filter(
                            ee.Filter.neq("classValues", None)
                        ),
                        "properties": ["classValues"],
                        "scale": 30,
                        "tileScale": 16,
                    }
                )
                
                trainSamplesFeeded = trainSamplesFeeded.merge(trainSamplesFeeded_year)

                if year == year_images:
                    mainScene = ee.Image(neibCollection.clip(classificationArea)).set(
                        {"year": year_images}
                    )

            # Map.addLayer(mainScene)

            features = mainScene

            # Organizes the samples for the classifier training phase

            classifier = ee.Classifier.smileRandomForest(
                settings.RFNTREES, settings.RFVARPERSPLIT, 1, settings.RFBAGFRACTION, None, year
            )
            classifier = classifier.setOutputMode("PROBABILITY")

            classifier = classifier.train(
                trainSamplesFeeded, "classValues", mainScene.bandNames()
            )

            classification = ee.Image(features).classify(classifier).select(0)

            # *******************************************************************/
            # *************** Classification Approach ****************************/
            # *******************************************************************/

            class_stack = class_stack.addBands(
                ee.Image(classification).rename(f"Y{year}")
            )
        # settings.START_YEAR, settings.END_YEAR
        name = f"pasture_col6_planted_{landsatWRSPath}_{landsatWRSRow}_{settings.START_YEAR}_{settings.END_YEAR}_stack_LAPIG"
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


