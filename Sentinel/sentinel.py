import ee
from dynaconf import settings
from Lapig.Lapig import HelpLapig
from Lapig.Functions import type_process
from requests import post
from pathlib import Path
from sys import exit

try:
    credentials = ee.ServiceAccountCredentials(
        "nxgame2009@gmail.com",  # settings.GMAIL,
        f"{str(Path.home())}/{settings.PRIVATEKEY}",
    )
    ee.Initialize()
except FileNotFoundError as e:
    print(e)
    exit(1)


cartas = ee.FeatureCollection(
    "users/vieiramesquita/LAPIG-PASTURE/VECTORS/CARTAS_IBGE_BR_mod"
)


Lapig = HelpLapig(ee)
sat = "SENTINEL"
lista_cartas = settings.LISTA_CARTAS

list_size = 1

cartas_list = cartas.toList(list_size)


def generate_image(num, name):
    cartas_area = ee.Feature(cartas_list.get(cartaNm))
    cartas_buffer = cartas.filterBounds(cartas_area.geometry().buffer(75000))

    TRAIN_DATA = ee.FeatureCollection(
        "users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_cultivado_QGIS_new_pampa_v2"
    )

    rfNTrees = 500
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

    s2 = ee.ImageCollection("COPERNICUS/S2_SR")
    s2Clouds = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")

    START_DATE = ee.Date("2018-07-01")
    END_DATE = ee.Date("2020-12-31")
    MAX_CLOUD_PROBABILITY = 20

    def maskClouds(img):

        cloudProb = img.select("MSK_CLDPRB")
        scl = img.select("SCL")

        shadow = scl.eq(3)
        # 3 = cloud shadow
        cirrus = scl.eq(10)
        # 10 = cirrus

        clouds = ee.Image(img.get("cloud_mask")).select("probability")
        isNotCloud = clouds.lt(MAX_CLOUD_PROBABILITY)

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

    # print(s2SrWithCloudMask,s2CloudMasked)

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

    classFieldName = "cons_2017"

    trainSamples = TRAIN_DATA.select(classFieldName).filterBounds(cartas_buffer)

    classifier = ee.Classifier.randomForest(
        rfNTrees, rfVarPersplit, 1, rfBagFraction, False, 2017
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


def get_Exports(version, num, name):
    ROI, imgae = generate_image(num, name)
    task = ee.batch.Export.image.toDrive(
        **{
            "image": imgae,
            "description": f"pastureMapping_S2_col6_2020_{name}",
            "folder": "pastureMapping_S2_col6_2020",
            "fileNamePrefix": f"{version}-pastureMapping_S2_col6_2020_{name}",
            "region": ROI,
            "scale": 10,
            "maxPixels": 1.0e13,
        }
    )
    task.start()
    rest = {
        "id_": f"{version}_{name}",
        "version": version,
        "name": name,
        "state": type_process(task.state),
        "task_id": task.id,
        "num": num,
    }

    return task.id, post(f"http://{settings.SERVER}:{settings.PORT}/update", json=rest)
