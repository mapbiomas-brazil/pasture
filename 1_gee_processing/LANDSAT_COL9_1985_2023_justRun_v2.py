import ee
from Lapig import HelpLapig
from sys import exit

ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

# Imports GEE
grids = ee.FeatureCollection(
    "users/vieiramesquita/LAPIG-PASTURE/VECTORS/LANDSAT_GRID_V3_PASTURE"
)

# End Imports GEE
Lapig = HelpLapig(ee)

def getNeibArea(path,row):
    path = int(path)
    row = int(row)

    neitiles = []
    neitilesT = []

    for pInc in range(path-1, path+2):
        for rInc in range(row-1,row+2):
            if path == 1 and pInc == 0:
                pInc = 233
            elif path == 233 and pInc == 234:
                pInc = 1

            neitiles.append(f"{pInc}/{rInc}")
            neitilesT.append(f"T{pInc:03}{rInc:03}")

    return neitilesT,neitiles

def clipCollection(img):

    path =  ee.Number(img.get('WRS_PATH')).int().format()
    row = ee.Number(img.get('WRS_ROW')).int().format()

    path = ee.Algorithms.If(path.length().eq(1), ee.String('00').cat(path), path)

    wrsProps =ee.String(path).cat('/').cat(row)
    gridSelect = grids.filter(ee.Filter.eq('SPRNOME',wrsProps))

    return img.clip(gridSelect)

def generate_image(name, class_year,sample_type):

    landsatWRSPath = name[1:4]
    landsatWRSRow = name[4:7]

    rfNTrees = 500
    rfBagFraction = 0.5
    rfVarPersplit = 9
    neitilesT, neitiles = getNeibArea(landsatWRSPath,landsatWRSRow)

    neibRegion = [grids.filter(ee.Filter.inList('TILE_T',neitilesT)),neitiles] 
    classFieldName = f'cons_{class_year}'

    if class_year >= 2024:
            classFieldName = 'cons_2023'
    if class_year < 1985:
            classFieldName = 'cons_1985'

    def make_classFieldName(feat):
        return feat.set(classFieldName,feat.get('is_pasture'))

    trainSamples_main = ee.FeatureCollection('users/vieiramesquita/LAPIG-PASTURE/VECTORS/mapa_pastagem_col8_50k_final_v3_1')

    if class_year != 2023:
        trainSamples_main = ee.FeatureCollection(trainSamples_main).select(classFieldName)

    else:
        trainSamples_main = ee.FeatureCollection(trainSamples_main).select('cons_2023')

    extra_samples = (ee.FeatureCollection('users/vieiramesquita/LAPIG-PASTURE/VECTORS/Pasture_Extra_Brasil_plus_Date_v1_3')
        .filter(ee.Filter.lte('YearPastur',class_year)))

    reclass_extra_samples = extra_samples.map(make_classFieldName).select(classFieldName)

    trainSamples = trainSamples_main.merge(reclass_extra_samples)

    samplingArea = neibRegion[0]
    neighborhoodArea = neibRegion[1]
    classificationArea = grids.filter(ee.Filter.eq('TILE_T',name))

    Collections = {
         'L8':"LANDSAT/LC08/C02/T1_TOA",
         'L5':"LANDSAT/LT05/C02/T1_TOA",
         'L7':"LANDSAT/LE07/C02/T1_TOA"
    }

    startDate = f"{class_year - 1}-07-01"
    endDate = f"{class_year + 1}-06-30"

    landsatBandsWet = ['green_wet','red_wet','nir_wet', 'swir1_wet','swir2_wet','ndvi_wet','ndwi_wet','cai_wet']
    landsatBandsWetAmp = ['green_wet_amp','red_wet_amp','nir_wet_amp', 'swir1_wet_amp','swir2_wet_amp','ndvi_wet_amp','ndwi_wet_amp','cai_wet_amp']

    if int(class_year) > 2012:
        sat = 'L8'
        collection = Collections['L8']
        mask_exp = "(b('QA_PIXEL') == 21824 || b('QA_PIXEL') == 21952)"

    elif int(class_year) in (2000,2001,2002,2012):
        sat = 'L5_7'
        collection = Collections['L7']
        mask_exp = "(b('QA_PIXEL') == 5440 || b('QA_PIXEL') == 5504)"
    else:
        sat = 'L5_7'
        collection = Collections['L5']
        mask_exp = "(b('QA_PIXEL') == 5440 || b('QA_PIXEL') == 5504)"

    def spectralFeatures(image):
        ndvi = Lapig.expression_select(image, sat, "NDVI")
        ndwi = Lapig.expression_select(image, sat, "NDWI")
        cai = Lapig.expression_select(image, sat, "CAI")

        return image.addBands([ndvi, ndwi, cai])

    def onlyWetSeasonNei(image):
        seasonMask = image.select("ndvi_wet").gte(wetThresholdNei)
        return image.updateMask(seasonMask)

    def maskClouds(img):

        qaImage = img.expression(mask_exp).add(img.lte(0))
        noisy_data = img.expression("(b('B5') >= 0)")

        return img.updateMask(qaImage.multiply(noisy_data))

    SRTM = Lapig.getSRTM()
    elevation = SRTM["elevation"]
    slope = SRTM["slope"]
    #######################################

    neibData = []

    for i in neighborhoodArea:

        sceneInfo = i.split("/")
        query_SPRNOME = f'{int(sceneInfo[0])}/{int(sceneInfo[1])}'
        spectralDataNei = (
            ee.ImageCollection(collection).filterMetadata(
                "WRS_PATH", "equals", int(sceneInfo[0])
            )
            .filterMetadata("WRS_ROW", "equals", int(sceneInfo[1]))
            .filterDate(startDate, endDate)
            .map(maskClouds)
            .map(spectralFeatures)
            .map(clipCollection)
            .select(Lapig.getExpression(sat,'bands'))
        )

        wetThresholdNei = spectralDataNei.select("NDVI").reduce(
            ee.Reducer.percentile([25])
        )

        wetSpectralDataNei = spectralDataNei.select(
            Lapig.getBands(sat), landsatBandsWet
        ).map(onlyWetSeasonNei)

        temporalData = Lapig.getLatLong(Lapig.temporalFeatures(wetSpectralDataNei, landsatBandsWetAmp)).addBands(
            [
                Lapig.temporalPercs(wetSpectralDataNei,[10, 25, 75, 90]),
                elevation,
                slope
            ]
        )

        bandSize = ee.Number(temporalData.bandNames().size())

        neibData.append(temporalData.set({"BandNumber": bandSize}))


    neibCollection = (
        ee.ImageCollection(neibData)
        .filter(ee.Filter.gt("BandNumber", 4))
        .mosaic()
    )

    classifier = ee.Classifier.smileRandomForest(
        rfNTrees,
        rfVarPersplit, 
        1,
        rfBagFraction,
        None,
        int(class_year)
        )
    classifier = classifier.setOutputMode("PROBABILITY")

    trainSamplesFeeded = neibCollection.sampleRegions(**{
        'collection': trainSamples.filterBounds(samplingArea).filter(ee.Filter.neq(classFieldName,None)),
        'properties': [classFieldName],
        'scale': 30,
        'tileScale': 16
    })

    classifier = classifier.train(trainSamplesFeeded, classFieldName,neibCollection.bandNames())

    classification = neibCollection.classify(classifier).select(0).clip(classificationArea)

    fileName = f"br_pasture_lapig_mapbiomas_col9_{name}_{class_year}"
    folder_drive = f'Pasture_Mapping_Landsat_Col9'

    task = (ee.batch.Export.image.toDrive(
       image = classification.multiply(10000).int16(),
       crs = "EPSG:4326",
       region = classificationArea.geometry().bounds(),
       description = fileName,
       folder = folder_drive,
       scale = 30,
       maxPixels = 1e13,
    ))
    
    task.start()


lista_tiles = ['T001057','T001058','T001059','T001060','T001061','T001062','T001063','T001064','T001065','T001066',
'T001067','T002057','T002059','T002060','T002061','T002062','T002063','T002064','T002065','T002066','T002067',
'T002068','T003058','T003059','T003060','T003061','T003062','T003063','T003064','T003065','T003066','T003067',
'T003068','T004059','T004060','T004061','T004062','T004063','T004064','T004065','T004066','T004067','T005059',
'T005060','T005063','T005064','T005065','T005066','T005067','T006063','T006064','T006065','T006066','T214064',
'T214065','T214066','T214067','T215063','T215064','T215065','T215066','T215067','T215068','T215069','T215070',
'T215071','T215072','T215073','T215074','T216063','T216064','T216065','T216066','T216067','T216068','T216069',
'T216070','T216071','T216072','T216073','T216074','T216075','T216076','T217062','T217063','T217064','T217065',
'T217066','T217067','T217068','T217069','T217070','T217071','T217072','T217073','T217074','T217075','T217076',
'T218062','T218063','T218064','T218065','T218066','T218067','T218068','T218069','T218070','T218071','T218072',
'T218073','T218074','T218075','T218076','T218077','T219062','T219063','T219064','T219065','T219066','T219067',
'T219068','T219069','T219070','T219071','T219072','T219073','T219074','T219075','T219076','T219077','T220062',
'T220063','T220064','T220065','T220066','T220067','T220068','T220069','T220070','T220071','T220072','T220073',
'T220074','T220075','T220076','T220077','T220078','T220079','T220080','T220081','T220082','T221061','T221062',
'T221063','T221064','T221065','T221066','T221067','T221068','T221069','T221070','T221071','T221072','T221073',
'T221074','T221075','T221076','T221077','T221078','T221079','T221080','T221081','T221082','T221083','T222061',
'T222062','T222063','T222064','T222065','T222066','T222067','T222068','T222069','T222070','T222071','T222072',
'T222073','T222074','T222075','T222076','T222077','T222078','T222079','T222080','T222081','T222082','T222083',
'T223060','T223061','T223062','T223063','T223064','T223065','T223066','T223067','T223068','T223069','T223070',
'T223071','T223072','T223073','T223074','T223075','T223076','T223077','T223078','T223079','T223080','T223081',
'T223082','T224060','T224061','T224062','T224063','T224064','T224065','T224066','T224067','T224068','T224069',
'T224070','T224071','T224072','T224073','T224074','T224075','T224076','T224077','T224078','T224079','T224080',
'T224081','T224082','T225058','T225059','T225060','T225061','T225062','T225063','T225064','T225065','T225066',
'T225067','T225068','T225069','T225070','T225071','T225072','T225073','T225074','T225075','T225076','T225077',
'T225080','T225081','T226057','T226058','T226059','T226060','T226061','T226062','T226063','T226064','T226065',
'T226066','T226067','T226068','T226069','T226070','T226071','T226072','T226073','T226074','T226075','T227058',
'T227059','T227060','T227061','T227062','T227063','T227064','T227065','T227066','T227067','T227068','T227069',
'T227070','T227071','T227072','T227073','T227074','T227075','T228058','T228059','T228060','T228061','T228062',
'T228063','T228064','T228065','T228066','T228067','T228068','T228069','T228070','T228071','T228072','T229058',
'T229059','T229060','T229061','T229062','T229063','T229064','T229065','T229066','T229067','T229068','T229069',
'T229070','T229071','T230059','T230060','T230061','T230062','T230063','T230064','T230065','T230066','T230067',
'T230068','T230069','T231057','T231058','T231059','T231060','T231061','T231062','T231063','T231064','T231065',
'T231066','T231067','T231068','T231069','T232056','T232057','T232058','T232059','T232060','T232061','T232062',
'T232063','T232064','T232065','T232066','T232067','T232068','T232069','T233057','T233058','T233059','T233060',
'T233061','T233062','T233063','T233064','T233065','T233066','T233067','T233068']

for tile in lista_tiles:
    for year in range(1984,2024,1):
        generate_image(tile,year)