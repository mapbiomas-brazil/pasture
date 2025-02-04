import ee
import math
import sys

ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')

#Classification Params
#year = 2023 #Selected year
#IBGE_CHART = 'SE-22-X-A' #Check here the code of the desired IBGE Chart
my_folder = 'lapig_br_pasture_mapping_s2_v1' # Desired output folder

#Charts used as region/model delimitation
cartas = ee.FeatureCollection(
    "users/vieiramesquita/LAPIG-PASTURE/VECTORS/CARTAS_IBGE_BR_mod"
)

rfNTrees = 500; ##Number of random trees - lesser faster, but worst. 100-500 is the optimal;
rfBagFraction = 0.5; ##Fraction (10^-2%) of variables in the bag - 0.5/50% is the default;
rfVarPersplit = 13 ##Number of varibales per tree branch - estimated by the square root of the number of variables used in the feature space;

#Dictionary containing spectral indexes and their formulas
indexes = {
    'CAI': "(b('B12') / b('B11'))", #Cellulose absorption index
    'NDVI': "(b('B8') - b('B4')) / (b('B8') + b('B4'))", #Normalized Difference Vegetation Index
    'NDWI': "(b('B8') - b('B11')) / (b('B8') + b('B11'))", #Normalized Difference Water/Wetness Index
    'CRI1': "1/(b('B2')) - 1/(b('B3'))", #Carotenoid Reflectance Index 1
    'ARI_1': "(1/b('B3') - 1/b('B5'))*1000", #Anthocyanin Reflectance Index 1
    'RGR': "b('B4')/b('B3')", #Simple Ratio Red/Green Red-Green Ratio
    'PSRI': "(b('B4') - b('B2') )/(b('B6'))", #Plant Senescence Reflectance Index
    'SATVI': "((b('B11') - b('B4'))/(b('B11') + b('B4') + 0.5))*(1*0.5)-(b('B12')/2)*0.0001" #Soil-Adjusted Total Vegetation Index
}

#Function made to estimate spectral indexes for each image in the Image Collection
def spectralFeatures(image):

    ndvi = image.expression(indexes["NDVI"]).select([0], ['NDVI']) #Calculates the NDVI
    ndwi = image.expression(indexes["NDWI"]).select([0], ['NDWI']) #Calculates the NDWI
    cai = image.expression(indexes["CAI"]).select([0], ['CAI']) #Calculate thes CAI
    cri1 = image.expression(indexes["CRI1"]).select([0], ['CRI1']) #Calculates the CRI1
    ari1 = image.expression(indexes["ARI_1"]).select([0], ['ARI_1']) #Calculates the ARI_1
    rgr = image.expression(indexes["RGR"]).select([0], ['RGR']) #Calculates the RGR
    psri = image.expression(indexes["PSRI"]).select([0], ['PSRI']) #Calculates the PSRI
    satvi = image.expression(indexes["SATVI"]).select([0], ['SATVI']) #Calculates the SATVI

    image = image.addBands([ndvi, ndwi, cai, cri1, ari1, rgr, psri, satvi]) #Adds the spectral indexes to the image with the spectral bands

    return image

#Function made to reduce all images/band in the collection to their specific reductor, e.g. median.
def temporalFeatures(image):

    min = image.reduce(ee.Reducer.min()) #Reduces all bands to the minimum of their values per pixel
    max = image.reduce(ee.Reducer.max()) #Reduces all bands to the maximum of their values per pixel
    median = image.reduce(ee.Reducer.median()) #Reduces all bands to the median of their values per pixel
    stdv = image.reduce(ee.Reducer.stdDev()) #Reduces all bands to the standaard deviation of their values per pixel

    amp = (image.reduce(ee.Reducer.max()) #Reduces all bands to the amplitude (max - min) of their values per pixel
        .subtract(image.reduce(ee.Reducer.min()))
        .rename(BandsWetAmp))

    result = (ee.Image().select()
        .addBands([min, max, median, amp, stdv])) #Creates an empty image and add the reduced bands to it
    return result


#Function made to reduce all images/band in the collection to their percentiles, e.g. 10%, 25%, 75% and 90%.
def temporalPercs(image):

    percs = image.reduce(ee.Reducer.percentile([10, 25, 75, 90]))

    result = ee.Image().select().addBands([percs])

    return result

#Function made to generate the latitude and the longitude of each pixel
def getLatLong(img):
    ## Gets the projection
    proj = ee.Image(img).select(0).projection() #Gets the reference projection from one image
    latlon = ee.Image.pixelLonLat() #Estimates the latitude and longitude for each pixel
    return ee.Image(img).addBands(latlon.select('longitude', 'latitude')) #Adds the latitude and the longitude as a band

#Function made to mask cloud and shadows in the images, based on the quality band from Google Cloud Score (cs)
def maskClouds(img):
    # The threshold for masking; values between 0.50 and 0.65 generally work well.
    # Higher values will remove thin clouds, haze & cirrus shadows.
    CLEAR_THRESHOLD = 0.50;
    mask = img.select('cs').gte(CLEAR_THRESHOLD); #Masks the pixels with 50% of chance or more to be clouds.
    return img.updateMask(mask);

#Function made to convert deegre image to percent
def radians(img):
    return img.toFloat().multiply(math.pi).divide(180)

def res_bilinear(img):

    ##Resamples the 20 meters bands to 10m using bilinear resampling method
    bands = img.select('B5', 'B6', 'B7', 'B8A', 'B11', 'B12'); #Bands to be resampled from 20 to 10 meters

    return img.resample('bilinear').reproject(**{
        'crs': bands.projection().crs(), #Gets the projection
        'scale': img.select('B8').projection().nominalScale() #Gets the pixel size
    })

#Function made to mask some weird black edges which can appear in some Sentinel 2 images
def maskEdges(s2_img):
    return s2_img.updateMask(
        s2_img.select('B8A').mask().updateMask(s2_img.select('B9').mask())) #Defined

terrain = ee.Algorithms.Terrain(ee.Image("NASA/NASADEM_HGT/001")); #Terrain variables (i.e. elevation, slope, aspect) extraction from the NASADEM 
elevation = terrain.select('elevation'); #Selection of the elevation band
slope = (radians(terrain.select('slope'))).expression('b("slope")*100'); #Selection of the slope band and conversion from deegre to percentage

#List of names to rename the bands
BandsWet = ['blue_wet', 'green_wet', 'red_wet', 'rededge1_wet', 'rededge2_wet', 'rededge3_wet',
    'nir_wet', 'rededge4_wet', 'swir1_wet', 'swir2_wet', 'ndvi_wet', 'ndwi_wet', 'cai_wet',
    'cri1_wet', 'ari1_wet', 'rgr_wet', 'psri_wet', 'satvi_wet'
];

#List of names to rename amplitude bands
BandsWetAmp = ['blue_wet_amp', 'green_wet_amp', 'red_wet_amp', 'rededge1_wet_amp',
    'rededge2_wet_amp', 'rededge3_wet_amp', 'nir_wet_amp', 'rededge4_wet_amp', 'swir1_wet_amp', 'swir2_wet_amp',
    'ndvi_wet_amp', 'ndwi_wet_amp', 'cai_wet_amp', 'cri1_wet_amp', 'ari1_wet_amp', 'rgr_wet_amp',
    'psri_wet_amp', 'satvi_wet_amp'
];

#########################################

#Main function, responsible to execute the classification. Accept as parameters the chart name (e.g. 'SE-22-X-A') and the year (e.g. 2022)
def run_classficiation(carta, year):

    nm_carta = carta; #Changes the chart variable name

    cartas_area = cartas.filter(ee.Filter.eq('grid_name', nm_carta)); # Filters the main charts feature collection by the choosed chart
    cartas_buffer = cartas_area.geometry().buffer(100000); # Selects the charts around the choosed chart

    START_DATE = f"{year - 1}-07-01"; #Start date to filter the image collection (usually six months before the main year)
    END_DATE = f"{year + 1}-06-30"; #End date to filter the image collection (usually six months after the main year)

    s2 = (ee.ImageCollection("COPERNICUS/S2_HARMONIZED") #Selects the Sentinel 2 TOA Harmonized time series 
        .filterBounds(cartas_buffer) #Filters the images that intersects with the main and neighbor charts
        .filterDate(START_DATE, END_DATE) #Filters the images by the range of dates (start and end)
    )

    csPlus = (ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED') #Selects the Google Sentinel 2 AI Cloud Score +, the best cloud and shadow mask from Sentinel 2
        .filterBounds(cartas_buffer) #Filters the images that intersects with the main and neighbor charts
        .filterDate(START_DATE, END_DATE)); #Filters the images by the range of dates (start and end)

    csPlusBands = csPlus.first().bandNames(); #Get the band names of the Cloud Score+ bands

    s2CloudMasked = (s2.linkCollection(csPlus, csPlusBands) #Link the Sentinel collection with the CloudScore+
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 80)) #Filter the images with more than 80% of cloud
        .map(maskEdges) #Applies the filter to mask fault edges
        .map(maskClouds) #Applies the filter to mask cloud and shadows
        .map(res_bilinear)); #Applies the bilinear resampling on the lower resolution images (i.e. 20 meters)
    
    #Applies the spectral index calculations and selects the bands to be used
    spectralDataNei = (s2CloudMasked
        .map(spectralFeatures)
        .select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A',
            'B11', 'B12', 'NDVI', 'NDWI', 'CAI', 'CRI1', 'ARI_1', 'RGR',
            'PSRI', 'SATVI'
        ]));

    #Calculates the 25% NDVI percentile to use as a noise mask
    wetThresholdNei = (spectralDataNei
        .select("NDVI")
        .reduce(ee.Reducer.percentile([25])));
        
    #Function made to get the image NDVI and mask it according to the 25% NDVI percentile
    def onlyWetSeasonNei(image):
        seasonMask = image.select("ndvi_wet").gte(wetThresholdNei);
        return image.mask(seasonMask);
  
    #Applies the 25% NDVI percentile mask to each image in the collection
    wetSpectralDataNei = (spectralDataNei
        .select(spectralDataNei.first().bandNames(), BandsWet)
        .map(onlyWetSeasonNei));
    
    #Applies the functions to calculate percentiles, get latitude and longitude, calculate the temporal reducers and adds the elevation and slope data.
    temporalData = (getLatLong(temporalPercs(wetSpectralDataNei))
      .addBands([temporalFeatures(wetSpectralDataNei),elevation, slope]));

    featureSpace = ee.Image(temporalData)
        
    #Defines the name of the column to be used as training reference (e.g. cons_2022); NEEDS TO BE INTERGER DATA (i.e. 1 ,2 ,3 4)
    classFieldName = f'cons_{year}';
    
    #Function made to adjust the class field from the extra training samples 
    def make_classFieldName(feat):
        return feat.set(classFieldName, feat.get('is_pasture'));
  
    #Merges the main training samples with the extra training samples
    trainSamples_main = ee.FeatureCollection('users/vieiramesquita/LAPIG-PASTURE/VECTORS/mapa_pastagem_col8_50k_final_v2')

    if year < 2023:
      trainSamples_main = ee.FeatureCollection(trainSamples_main).select(classFieldName)
    else:
      classFieldName = 'cons_2022'
      trainSamples_main = ee.FeatureCollection(trainSamples_main).select('cons_2022')
    
    extra_samples = (ee.FeatureCollection('users/vieiramesquita/LAPIG-PASTURE/VECTORS/Pasture_Extra_Brasil_plus_Date_v1_3')
      .filter(ee.Filter.lte('YearPastur',year)))

    reclass_extra_samples = extra_samples.map(make_classFieldName).select(classFieldName)

    trainSamples = trainSamples_main.merge(reclass_extra_samples)
    
    #Creates and define the classifier parameters (NUmber of Trees, Variables per Split, Minimum Leaf Population, Bag Fraction, Max nodes and Seed)
    classifier = ee.Classifier.smileRandomForest(rfNTrees, rfVarPersplit, 1, rfBagFraction, None, year);

    #Sets the classifier to the Probability Mode - Default is CLASSIFICATION
    classifier = classifier.setOutputMode('PROBABILITY');
    
    #Crosses the training samples with the feature space variables to associate the information with the classes
    trainSamplesFeeded = (featureSpace.sampleRegions(**{
        'collection': trainSamples.filterBounds(cartas_buffer).filter(ee.Filter.neq(classFieldName, None)),
        'properties': [classFieldName],
        'scale': 10,
        'tileScale': 16
    }));
    
    #Trains the classifier using the training samples asociated with the feature space information
    classifier = classifier.train(trainSamplesFeeded, classFieldName);
   
    #Takes the trained classifier and use it to classify the entire feature space pixel by pixel
    classification = featureSpace.classify(classifier).select(0);
    
    fileName = f'br_pasture_s2_col2_v1_{carta}_{year}'; #Output file name
    
    #Generates the export task for the Google Drive
    task = (ee.batch.Export.image.toDrive(
       #Points to the classification image and convert it from Float (0 to 1) to Integer image (0 to 10000) and clips it based on the chart geometry
       image= classification.multiply(10000).int16().clip(cartas_area), 
       crs= "EPSG:4326", #Defines the output porjection
       region= cartas_area.geometry().bounds(), #Defines the output porjection
       description= fileName, #Gets the output file name
       folder= my_folder, #Gets the output folder name
       scale= 10, #Sets the output resolution, measured in meters
       maxPixels= 1e13, #Sets the maximum amount of pixels that can be exported, which is 10^13 or 1E13
    ));
    
    task.start()

# ##############CHECK#################

list_charts = ['SF-23-Z-C','SF-23-X-D','SF-23-X-C','SF-23-Z-A','SF-23-Y-B','SF-23-V-D','SF-23-X-A','SF-23-V-B','SE-23-Y-D','SE-23-Z-C',
			'SF-23-X-B','SE-23-Z-D','SE-23-Z-A','SE-23-Y-B','SE-23-X-C','SE-23-V-D','SE-23-V-B','SE-23-X-A','SE-23-X-D','SE-23-Z-B',
			'SE-23-X-B','SE-24-Y-C','SE-24-Y-A','SE-24-V-C','SE-24-Y-B','SE-24-V-D','SE-24-Y-D','SF-24-V-C','SB-25-V-C','SB-25-Y-A',
			'SB-25-Y-C','SC-25-V-A','SC-25-V-C','SC-24-X-D','SC-24-Z-B','SC-24-Z-D','SC-24-X-B','SC-24-X-A','SC-24-X-C','SC-24-V-B',
			'SC-24-V-D','SC-24-Z-A','SC-24-Y-B','SC-24-Z-C','SD-24-X-A','SC-24-Y-D','SD-24-V-B','SD-24-V-A','SD-24-V-C','SD-23-X-B',
			'SD-23-X-D','SD-24-Y-A','SD-23-Z-B','SD-24-Y-C','SE-24-V-A','SD-23-Z-D','SD-23-Z-A','SD-23-Z-C','SD-23-Y-D','SD-23-Y-B',
			'SD-23-X-C','SD-23-V-D','SD-23-V-B','SD-23-X-A','SC-23-Z-C','SC-23-Y-D','SC-23-Z-A','SC-23-Y-B','SC-23-X-C','SC-23-V-D',
			'SC-23-Z-B','SC-23-Z-D','SC-23-X-D','SC-24-Y-C','SC-24-Y-A','SC-24-V-C','SC-23-X-B','SC-24-V-A','SB-24-Y-C','SB-23-Z-D',
			'SB-23-Z-C','SC-23-X-A','SC-23-V-B','SB-23-Y-D','SB-23-Y-B','SB-23-Z-A','SB-23-Z-B','SB-23-X-D','SB-23-X-C','SB-23-V-D',
			'SB-23-X-A','SB-23-V-B','SA-23-Y-D','SA-23-Z-C','SB-23-X-B','SA-23-Z-D','SB-24-V-C','SB-24-V-A','SA-24-Y-C','SB-24-V-B',
			'SA-24-Y-D','SB-24-V-D','SB-24-Y-A','SB-24-Y-B','SB-24-Y-D','SB-24-Z-C','SB-24-Z-A','SB-24-Z-B','SB-24-Z-D','SB-24-X-D',
			'SB-24-X-B','SB-24-X-A','SA-24-Z-C','SB-24-X-C','SA-24-Y-B','SA-24-Y-A','SA-23-Z-B','SA-23-X-C','SA-23-Z-A','SA-23-Y-B',
			'NB-22-Y-D','NA-22-V-B','NA-22-X-A','NA-22-X-C','NA-22-Z-A','SA-23-V-A','NA-22-Z-C','SA-22-X-A','NA-22-Y-D','SA-22-V-B',
			'SA-22-V-A','NA-22-Y-C','NA-22-Y-B','NA-22-Y-A','NA-22-V-D','NA-22-V-C','NA-21-Z-B','NA-21-X-D','NA-21-Z-D','SA-21-X-B',
			'SA-21-X-A','NA-21-Z-C','NA-21-Z-A','NA-21-X-C','NA-21-Y-D','SA-21-V-B','SA-21-V-A','NA-21-Y-C','NA-21-Y-A','SA-20-X-B',
			'NA-20-Z-D','NA-20-Z-B','NA-20-X-D','NA-21-V-C','NA-21-V-A','NA-20-X-B','NB-20-Z-C','NA-20-V-D','NA-20-X-A','NA-20-X-C',
			'NA-20-Z-A','NA-20-Z-C','SA-20-X-A','SA-20-V-B','NA-20-Y-D','SA-20-V-A','NA-20-Y-C','NA-19-Z-D','SA-19-X-B','SA-19-X-A',
			'NA-19-Z-C','SA-19-V-B','NA-19-Y-D','NA-19-Y-B','SC-19-V-D','SC-19-X-C','SC-19-Z-B','SC-19-X-D','SC-19-X-B','SC-19-X-A',
			'SC-19-V-B','SB-19-Z-C','SB-19-Y-D','SB-19-Z-D','SB-19-Z-A','SB-19-Z-B','SB-19-X-C','SB-19-X-D','SB-19-X-A','SB-19-X-B',
			'SB-19-Y-B','SB-19-V-D','SB-19-V-B','SB-19-Y-C','SB-19-Y-A','SB-19-V-C','SB-19-V-A','SB-18-X-D','SB-18-X-B','SB-18-Z-D',
			'SC-19-V-A','SC-19-V-C','SC-18-X-D','SB-18-Z-C','SA-19-V-D','SA-19-Y-B','SA-19-Y-D','SA-19-Z-A','SA-19-Z-C','SA-19-Z-D',
			'SA-19-Z-B','SA-19-X-D','SA-19-X-C','SA-20-V-C','SA-20-Y-A','SA-20-Y-B','SA-20-V-D','SA-20-X-C','SA-20-X-D','SA-20-Z-A',
			'SA-20-Z-B','SA-20-Y-D','SA-20-Z-C','SA-20-Z-D','SB-20-X-A','SB-20-X-B','SB-20-V-B','SB-20-V-A','SA-20-Y-C','SB-20-V-C',
			'SB-20-V-D','SB-20-Y-A','SB-20-Y-B','SB-20-Y-D','SB-20-Y-C','SC-20-V-A','SC-20-V-C','SC-20-V-D','SC-20-V-B','SB-20-Z-A',
			'SB-20-Z-C','SC-20-X-A','SC-20-X-C','SC-20-X-D','SC-20-X-B','SB-20-Z-D','SB-20-Z-B','SB-20-X-C','SB-20-X-D','SB-21-V-C',
			'SB-21-V-A','SB-21-V-B','SB-21-V-D','SB-21-Y-A','SB-21-Y-B','SB-21-Y-C','SC-21-V-C','SC-21-V-A','SC-21-V-B','SC-21-V-D',
			'SB-21-Y-D','SB-21-Z-A','SB-21-Z-C','SC-21-X-A','SC-21-X-B','SB-21-Z-D','SB-21-Z-B','SB-21-X-C','SB-21-X-D','SB-21-X-A',
			'SB-21-X-B','SA-21-Z-C','SA-21-Z-D','SA-21-Z-B','SA-21-Z-A','SA-21-Y-D','SA-21-Y-B','SA-21-Y-C','SA-21-Y-A','SA-21-V-D',
			'SA-21-V-C','SA-21-X-C','SA-21-X-D','SA-22-V-C','SB-22-V-A','SA-22-Y-C','SA-22-Y-A','SA-22-V-D','SA-22-Y-B','SA-22-Y-D',
			'SB-22-V-B','SA-22-Z-A','SA-22-Z-C','SA-22-X-C','SA-22-X-D','SA-23-V-C','SA-23-Y-A','SA-23-Y-C','SA-22-Z-D','SA-22-Z-B',
			'SB-22-X-A','SB-22-X-B','SB-22-X-C','SB-22-X-D','SB-23-V-C','SB-23-V-A','SB-23-Y-A','SB-23-Y-C','SB-22-Z-D','SC-22-X-B',
			'SB-22-Z-B','SB-22-Z-A','SB-22-Z-C','SC-22-X-A','SB-22-Y-D','SC-22-V-B','SC-22-V-A','SB-22-Y-C','SB-22-Y-B','SB-22-Y-A',
			'SB-22-V-D','SB-22-V-C','SC-21-X-D','SC-22-V-C','SC-22-Y-A','SC-21-Z-B','SC-22-Y-C','SC-21-Z-D','SD-21-X-B','SD-21-X-D',
			'SD-22-V-A','SD-22-V-C','SC-22-Y-B','SC-22-Y-D','SD-22-V-B','SD-22-V-D','SC-22-Z-C','SD-22-X-A','SC-22-Z-A','SC-22-X-C',
			'SC-22-V-D','SC-22-X-D','SC-22-Z-B','SC-23-V-C','SC-23-Y-A','SC-23-V-A','SC-23-Y-C','SD-23-V-A','SD-22-X-B','SC-22-Z-D',
			'SD-22-X-C','SD-22-X-D','SD-22-Z-A','SD-22-Z-B','SD-22-Z-C','SD-22-Z-D','SD-23-Y-A','SD-23-V-C','SD-23-Y-C','SE-23-V-A',
			'SE-23-V-C','SE-22-X-B','SE-22-X-D','SE-22-X-A','SE-22-X-C','SE-22-V-D','SE-22-V-B','SE-22-Y-B','SE-22-Y-A','SE-22-V-C',
			'SE-22-V-A','SD-22-Y-D','SD-22-Y-C','SD-22-Y-B','SD-22-Y-A','SE-21-X-B','SD-21-Z-D','SD-21-Z-B','SE-21-X-D','SE-21-Z-B',
			'SE-21-Z-C','SE-21-Z-A','SE-21-X-C','SE-21-X-A','SE-21-Y-B','SE-21-V-D','SE-21-V-B','SE-21-Y-D','SE-21-V-A','SD-21-Y-C',
			'SD-21-Y-D','SD-20-Z-B','SD-21-Y-A','SD-21-Y-B','SD-21-V-D','SD-21-X-C','SD-21-Z-A','SD-21-Z-C','SD-21-X-A','SD-21-V-B',
			'SC-21-Y-D','SC-21-Z-C','SC-21-Z-A','SC-21-X-C','SC-21-Y-B','SC-21-Y-C','SC-21-Y-A','SC-20-Z-B','SC-20-Z-D','SD-20-X-B',
			'SD-20-X-D','SD-21-V-A','SD-21-V-C','SD-20-X-C','SD-20-V-B','SD-20-X-A','SC-20-Z-C','SC-20-Z-A','SC-20-Y-B','SC-20-Y-D',
			'SD-20-V-A','SC-20-Y-C','SC-20-Y-A','SH-21-X-A','SH-21-X-C','SH-21-X-D','SH-21-X-B','SG-21-Z-D','SG-21-X-D','SG-21-X-B',
			'SF-21-Z-A','SF-21-Z-B','SF-21-X-C','SF-21-X-D','SF-21-Y-B','SF-21-V-D','SF-21-V-B','SF-21-X-A','SF-21-X-B','SE-21-Z-D',
			'SE-22-Y-C','SF-22-V-A','SF-22-V-C','SF-22-Y-A','SF-22-Y-C','SF-22-V-D','SF-22-V-B','SF-22-Y-B','SF-22-Y-D','SF-22-X-C',
			'SF-22-Z-A','SF-22-Z-C','SF-22-X-A','SE-22-Z-C','SE-22-Z-A','SE-22-Y-D','SE-22-Z-B','SE-22-Z-D','SF-22-X-B','SE-23-Y-A',
			'SE-23-Y-C','SF-23-V-A','SF-23-V-C','SF-23-Y-A','SF-22-X-D','SF-22-Z-B','SF-22-Z-D','SG-22-X-A','SG-22-X-B','SG-22-X-C',
			'SG-22-X-D','SF-23-Y-C','SG-22-Z-B','SG-22-Z-D','SG-22-Z-A','SG-22-Z-C','SH-22-X-A','SG-22-Y-D','SG-22-Y-B','SH-22-V-B',
			'SH-22-V-A','SG-22-Y-C','SG-22-Y-A','SG-22-V-D','SG-22-V-B','SG-22-V-A','SG-22-V-C','SH-22-V-C','SH-21-Z-B','SH-22-Y-A',
			'SH-21-Z-D','SH-22-Y-C','SI-22-V-A','SI-22-V-C','SH-22-Y-B','SH-22-V-D','SH-22-X-B','SE-24-V-B','SD-24-Y-D','SD-24-Y-B',
			'SD-24-V-D','SF-24-V-A','SF-23-Z-B','SF-24-Y-A','SF-23-Y-D','SH-22-X-D','SH-21-V-D','SF-21-Z-C','SD-20-Z-D','SC-19-Z-C',
			'SC-19-Y-B','SC-18-X-B','SB-18-Z-B','NA-19-Z-A','NA-19-Z-B','NA-20-Y-A','NA-20-V-A','NB-21-Y-A','SA-22-X-B','SA-23-V-D',
			'SH-21-Z-C','SI-22-V-B','SH-22-Z-A','SG-23-V-C','NA-21-V-D']

#Executes the classification function
for tile in list_charts:
    #for year in range(2015,2024,1):
    run_classficiation(tile, int(sys.argv[1]));
