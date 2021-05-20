import ee
from loguru import logger
from dynaconf import settings
from Lapig.Lapig import HelpLapig
from Lapig.Functions import type_process, login_gee
from requests import post
from sys import exit

login_gee(ee)

# Imports GEE
cartas = ee.FeatureCollection(
    "users/vieiramesquita/LAPIG-PASTURE/VECTORS/CARTAS_IBGE_BR_mod"
)
#mapbiomas_train = (ee.FeatureCollection("users/vieiramesquita/TrainingSamples/mapbiomas_85k_plus_rare_noEdge_and_stable_10years")
#  .remap(['Afloramento Rochoso', 'Apicum', 'Cultura Anual', "Lavoura Temporária", 'Cultura Perene', "Lavoura Perene", 'Cultura Semi-Perene', 'Floresta Plantada', 'Formação Campestre', 'Formação Florestal', 'Formação Savânica', 'Infraestrutura Urbana', 'Mangue', 'Mineração', 'Outra Formação Natural Não Florestal', "Outra Formação Não Florestal", 'Outra Área Não Vegetada', 'Outra Área não Vegetada', 'Pastagem Cultivada', 'Praia e Duna', 'Rio, Lago e Oceano', "Área Úmida Natural não Florestal", "Campo Alagado e Área Pantanosa", 'Aquicultura' ],
#    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
#    'CLASS_2016')
#  .remap(['Afloramento Rochoso', 'Apicum', 'Cultura Anual', "Lavoura Temporária", 'Cultura Perene', "Lavoura Perene", 'Cultura Semi-Perene', 'Floresta Plantada', 'Formação Campestre', 'Formação Florestal', 'Formação Savânica', 'Infraestrutura Urbana', 'Mangue', 'Mineração', 'Outra Formação Natural Não Florestal', "Outra Formação Não Florestal", 'Outra Área Não Vegetada', 'Outra Área não Vegetada', 'Pastagem Cultivada', 'Praia e Duna', 'Rio, Lago e Oceano', "Área Úmida Natural não Florestal", "Campo Alagado e Área Pantanosa", 'Aquicultura' ],
#    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
#    'CLASS_2017')
#  .remap(['Afloramento Rochoso', 'Apicum', 'Cultura Anual', "Lavoura Temporária", 'Cultura Perene', "Lavoura Perene", 'Cultura Semi-Perene', 'Floresta Plantada', 'Formação Campestre', 'Formação Florestal', 'Formação Savânica', 'Infraestrutura Urbana', 'Mangue', 'Mineração', 'Outra Formação Natural Não Florestal', "Outra Formação Não Florestal", 'Outra Área Não Vegetada', 'Outra Área não Vegetada', 'Pastagem Cultivada', 'Praia e Duna', 'Rio, Lago e Oceano', "Área Úmida Natural não Florestal", "Campo Alagado e Área Pantanosa", 'Aquicultura' ],
#    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
#    'CLASS_2018'))

# End Imports GEE

Lapig = HelpLapig(ee)
sat = "SENTINEL"
lista_cartas = settings.LIST_OF_TASKS
TRAIN_DATA = ee.FeatureCollection(
    'users/vieiramesquita/LAPIG-PASTURE/VECTORS/mapbiomas_col6_stable5y_training_samples_corrected_v5_w_field'
)




def generate_image(name, class_year, classFieldName, isTOA = False): 

    cartas_area = cartas.filter(ee.Filter.eq('grid_name',name))

    cartas_buffer = cartas.filterBounds(cartas_area.geometry().buffer(75000))
    
    
    rfNTrees = 200
    # Number of random trees;
    rfBagFraction = 0.5
    # Fraction (10^-2%) of variables in the bag;
    rfVarPersplit = 6  # Number of varibales per tree branch;

    def spectralFeatures(image):
        ndvi = Lapig.expression_select(image, sat, "NDVI")
        ndwi = Lapig.expression_select(image, sat, "NDWI")
        cai = Lapig.expression_select(image, sat, "CAI")
        cri1 = Lapig.expression_select(image, sat, "CRI1")
        ari1 = Lapig.expression_select(image, sat, "ARI_1")
        rgr = Lapig.expression_select(image, sat, "RGR")
        psri = Lapig.expression_select(image, sat, "PSRI")
        satvi = Lapig.expression_select(image, sat, "SATVI")

        return image.addBands([ndvi, ndwi, cai, cri1, ari1, rgr, psri, satvi])

    def onlyWetSeasonNei(image):
        seasonMask = image.select("ndvi_wet").gte(wetThresholdNei)
        return image.mask(seasonMask)

    SRTM = Lapig.getSRTM()
    elevation = SRTM["elevation"]
    slope = SRTM["slope"]
    #######################################

    
    #
    s2Clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")

    if(isTOA == True):
        logger.warning(f'Voce no modo Toa')
        s2 = ee.ImageCollection("COPERNICUS/S2")
        START_DATE = ee.Date(f"{int(class_year)-1}-07-01")
        END_DATE = ee.Date(f"{int(class_year)+1}-06-30") 
    else:
        logger.warning(f'Voce no modo superfice')
        s2 = ee.ImageCollection("COPERNICUS/S2_SR")
        START_DATE = ee.Date(f"{int(class_year)-1}-01-01")
        END_DATE = ee.Date(f"{int(class_year)}-12-31")

    
    

    MAX_CLOUD_PROBABILITY = 20

    def maskClouds(img):

        if(isTOA == True):
            #logger.warning(f'Voce ta usado mascara Toa')
            clouds = ee.Image(img.get("cloud_mask")).select("probability")
            isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY)
            mask = isNotCloud

        else:
            #logger.warning(f'Voce nao esta usado mascara Toa')
            clouds = ee.Image(img.get("cloud_mask")).select("probability")
            cloudProb = img.select("MSK_CLDPRB")
            isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY)
            scl = img.select("SCL")

            shadow = scl.eq(3)
            # 3 = cloud shadow
            cirrus = scl.eq(10)
            # 10 = cirrus
            mask = cloudProb.lt(5).And((cirrus).neq(1)).And((shadow).neq(1)).And(isNotCloud)

        # thanks Eric Waller for the correction

        return img.updateMask(mask)

    def maskEdges(s2_img):
        return s2_img.updateMask(
            s2_img.select("B8A").mask().updateMask(s2_img.select("B9").mask())
        )

    s2 = s2.filterBounds(cartas_buffer).filterDate(START_DATE, END_DATE).map(maskEdges)
    s2Clouds = s2Clouds.filterBounds(cartas_buffer).filterDate(START_DATE, END_DATE)
    
    # Join S2 SR with cloud probability dataset to add cloud mask.
    s2SrWithCloudMask = ee.Join.saveFirst("cloud_mask").apply(
        **{
            "primary": s2,
            "secondary": s2Clouds,
            "condition": ee.Filter.equals(
                **{"leftField": "system:index", "rightField": "system:index"}
            ),
        }
    )

    s2CloudMasked = ee.ImageCollection(s2SrWithCloudMask).map(maskClouds)

    
    spectralDataNei = s2CloudMasked.map(spectralFeatures).select(Lapig.getBands(sat))
    

    wetThresholdNei = spectralDataNei.select("NDVI").reduce(ee.Reducer.percentile([25]))

    wetSpectralDataNei = spectralDataNei.select(
        spectralDataNei.first().bandNames(), Lapig.getExpression(sat, "BandsWet")
    ).map(onlyWetSeasonNei)

    temporalData = (
        Lapig.getLatLong(
            Lapig.temporalPercs(wetSpectralDataNei, [1, 10, 25, 75, 90, 99])
        )
        .addBands(
            [
                Lapig.temporalFeatures(
                    wetSpectralDataNei, Lapig.getExpression(sat, "BandsWetAmp")
                ),
                elevation,
                slope,
            ]
        )
        .clip(cartas_buffer)
    )

    featureSpace = temporalData

    #######################################/


    trainSamples = TRAIN_DATA.select(classFieldName).filterBounds(cartas_buffer)

    classifier = ee.Classifier.smileRandomForest(
        rfNTrees,
        rfVarPersplit, 
        1,
        rfBagFraction,
        None,
        2017
        )
    classifier = classifier.setOutputMode("PROBABILITY")

    trainSamplesFeeded = featureSpace.sampleRegions(
        **{
            "collection": trainSamples.filter(ee.Filter.neq(classFieldName, None)),
            "properties": [classFieldName],
            "scale": 10,
            "tileScale": 16,
        }
    )

    classifier = classifier.train(trainSamplesFeeded, classFieldName)

    classification = featureSpace.clip(cartas_area).classify(classifier).select(0)

    return (
        cartas_area.geometry().bounds(),
        ee.Image(classification).multiply(10000).int16(),
    )


def get_Exports(version, num, full_name):
    class_year, name, coll_name  = full_name.split(';')

    ROI, imgae = generate_image(name,class_year, coll_name)
    task = ee.batch.Export.image.toCloudStorage(
        **{
            "image": imgae,
            "description": f"pastureMapping_S2_col6_{class_year}_LAPIG_{name}_{coll_name}",
            "bucket": "mapbiomas-public-temp",
            "fileNamePrefix": f"COLECAO/SENTINEL/PASTURE/pastureMapping_S2_col6_{class_year}_LAPIG_{name}_{coll_name}",
            "region": ROI,
            "scale": 10,
            "maxPixels": 1.0e13,
        }
    )
    try:
        task.start()
        rest = {
            "id_": f"{version}_{full_name}",
            "version": version,
            "name": full_name,
            "state": type_process(task.state),
            "task_id": task.id,
            "num": num,
        }
        return task.id, post(f"http://{settings.SERVER}:{settings.PORT}/task/update", json=rest)
    except Exception as e:
        rest = {
            "id_": f"{version}_{full_name}",
            "version": version,
            "name": full_name,
            "state": 'None',
            "task_id": task.id,
            "shardSize":32,
            "num": num,
        }
        logger.warning(f'Error ao exporta, dados recebidp{rest} error:{e}')
        return 'None', post(f"http://{settings.SERVER}:{settings.PORT}/task/update", json=rest)

