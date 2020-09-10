var L8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA")
var L5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_TOA")
var L7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_TOA")
var LANDSAT_GRID = ee.FeatureCollection("users/vieiramesquita/LAPIG-PASTURE/VECTORS/LANDSAT_GRID_V2_PASTURE")

var TRAIN_DATA_PLANTED = ee.FeatureCollection("users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_cultivado_QGIS_new_pampa_v2")
var TRAIN_DATA_NATURAL = ee.FeatureCollection("users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_natural_QGIS")

var TRAIN_DATA = TRAIN_DATA_PLANTED

/********************************************************************/
/**************** Classification Parameters *************************/
/********************************************************************/
var year = 2017 //Year choosed;
var landsatWRSPath = '221'; //Landsat satellite WRS orbital path number (1 - 251) / Works only for Brazil;
var landsatWRSRow = '071'; // Landsat satellite WRS row (1-248) / Works only for Brazil;
var pastureMapThreshold = 0.51 // PROBABILITY ABOVE 51% (10^-2%);

var rfNTrees = 500; //Number of random trees;
var rfBagFraction = 0.5; //Fraction (10^-2%) of variables in the bag;
var rfVarPersplit = 6 //Number of varibales per tree branch;

/********************************************************************/
/**************** Classification Methods ****************************/
/********************************************************************/

//Select of the feature that corresponds to the chosen Landsat Tile (WRS Path / WRS Row);
var getClassificationArea = function() {
  var wrsFieldName = 'TILE_T'
  var wrsFieldValue = 'T'+landsatWRSPath+landsatWRSRow

  var classificationArea = LANDSAT_GRID
                              .filter(ee.Filter.eq(wrsFieldName, wrsFieldValue))
  return classificationArea
}

function zeroPad(num, places) {
  var zero = places - num.toString().length + 1;
  return Array(+(zero > 0 && zero)).join("0") + num;
}

//Select the second order neighborhood features from the chosen Landsat Tile
var getNeibArea = function() {
  
  var neitiles = []
  
  var xW = [1,1] //Window Path
  var yW = [1,1] //Window Row
  
  
  var wrs_path = ee.List.sequence(parseInt(landsatWRSPath)-xW[0], parseInt(landsatWRSPath) + xW[1])
  var wrs_row = ee.List.sequence(parseInt(landsatWRSRow)-xW[0], parseInt(landsatWRSRow) + xW[1])

  for (var pInc = (parseInt(landsatWRSPath)-xW[0]) ; pInc < (parseInt(landsatWRSPath) + xW[1] + 1); pInc++){
    for (var rInc = (parseInt(landsatWRSRow)-yW[0]) ; rInc < (parseInt(landsatWRSRow) + yW[1] + 1); rInc++){
      
      var pAux = pInc
      var rAux = rInc;
      
      if (landsatWRSPath === 1 & pAux === 0){
        pAux = 233
      }	else if (landsatWRSPath === 233 & pAux === 234){
        pAux = 1
      }	
      
      var tAux = pAux + '/' + rAux
      
      neitiles.push(tAux)
      
    }
  }
  return neitiles
}

//Delimits the sample area based on the chosen Landsat Tile and the neighbors.
var getSamplingArea = function() {
  var classificationArea = getClassificationArea()
  var samplingArea = LANDSAT_GRID.
                        filterBounds(classificationArea.geometry().buffer(75000))
                        
  return samplingArea
}

//Creates the feature space for the phases of sampling and classifying
var getFeatureSpace = function() {
  
  var clipCollection = function(img){
		
		var wrsProps = ee.Number.parse(img.get('WRS_PATH')).format().cat('/').cat(ee.Number.parse(img.get('WRS_ROW')).format())
		
		var gridSelect = LANDSAT_GRID.filter(ee.Filter.eq('SPRNOME',wrsProps))
		
		return img.clip(gridSelect)
  }

  //Generates spectral indexes based on the satellite data
  var spectralFeatures = function(image) {
    
    var qaImage, ndvi, ndwi, cai;

    if (year >2012){
      
      qaImage = ee.Image(image.select(['BQA']));
      image = image.mask(qaImage.eq(2720));
      
      ndvi = image.expression(indexes["NDVI_L8"]).select([0],['NDVI']);
      ndwi = image.expression(indexes["NDWI_L8"]).select([0],['NDWI']);
      cai = image.expression(indexes["CAI_L8"]).select([0],['CAI']);
      
      image = image.addBands([ndvi,ndwi,cai]);
      
      return image;
    } else {
      
      qaImage = ee.Image(image.select(['BQA']));
      image = image.mask(qaImage.eq(672));
      
      ndvi = image.expression(indexes["NDVI_L5_7"]).select([0],['NDVI']);
      ndwi = image.expression(indexes["NDWI_L5_7"]).select([0],['NDWI']);
      cai = image.expression(indexes["CAI_L5_7"]).select([0],['CAI']);
      
      image = image.addBands([ndvi,ndwi,cai]);
      
      return image;
    }
  };

  //Builds spectro-temporal features from spectral data and spectral indexes
  var temporalFeatures = function(image) {

    var min = image.reduce(ee.Reducer.min())
    var max = image.reduce(ee.Reducer.max())
    var median = image.reduce(ee.Reducer.median());
    var stdv = image.reduce(ee.Reducer.stdDev());

    var amp = image.reduce(ee.Reducer.max())
                   .subtract(image.reduce(ee.Reducer.min()))
                   .rename(landsatBandsWetAmp)

    var result = ee.Image().select()
                      .addBands([min,max,median,amp,stdv])
                      //.clip(samplingArea);
    
    return result;
  };
  
  var temporalPercs = function(image) {
  
    var percs = image.reduce(ee.Reducer.percentile([10,25,75,90]))

    var result = ee.Image().select().addBands([percs])

    return result;
  };
  
  var getLatLong = (function(img) {

    // Get the projection
    var proj = ee.Image(img).select(['ndvi_wet_p10']).projection()
    // get coordinates image
    var latlon = ee.Image.pixelLonLat()//.reproject(proj)
    
    return ee.Image(img).addBands(latlon.select('longitude','latitude'));
  });

  function radians(img) {
    return img.toFloat().multiply(Math.PI).divide(180);
  }
  
  /*****************SRTM*****************/
  
  function radians(img) {
    return img.toFloat().multiply(Math.PI).divide(180);
  }
  
  var terrain = ee.Algorithms.Terrain(ee.Image('USGS/SRTMGL1_003'));
  
  var elevation = terrain.select('elevation');
  var slope = (radians(terrain.select('slope'))).expression('b("slope")*100');
  var aspect = radians(terrain.select('aspect'));
  
  /**************************************/

  //var bands; 
  //var landsatCollection = ee.ImageCollection(L5p)

  //Defines the date window that will be used to filter the satellite collection
  var startDate = (year-1)+'-07-01';
  var endDate = (year+1)+'-06-30';
  
  var landsatCollection = ee.ImageCollection(ee.Algorithms.If(ee.Number(year).gt(2012), L8, ee.Algorithms.If(ee.List([2000,2001,2002,2012]).contains(year), L7, L5)))
  
  var bands = ee.Algorithms.If(ee.Number(year).gt(2012),["B3","B4","B5","B6","B7","NDVI","NDWI","CAI"],["B2","B3","B4","B5","B7","NDVI","NDWI","CAI"])

  var indexes = {
    'CAI_L8':    "(b('B7') / b('B6'))",
    'CAI_L5_7':  "(b('B7') / b('B5'))",
    'NDVI_L8':   "(b('B5') - b('B4')) / (b('B5') + b('B4'))",
    'NDWI_L8':   "(b('B5') - b('B6')) / (b('B5') + b('B6'))",
    'NDVI_L5_7': "(b('B4') - b('B3')) / (b('B4') + b('B3'))",
    'NDWI_L5_7': "(b('B4') - b('B5')) / (b('B4') + b('B5'))",
  }

  var landsatBandsWet = ['green_wet','red_wet','nir_wet', 'swir1_wet','swir2_wet','ndvi_wet','ndwi_wet','cai_wet'];
  var landsatBandsWetAmp = ['green_wet_amp','red_wet_amp','nir_wet_amp', 'swir1_wet_amp','swir2_wet_amp','ndvi_wet_amp','ndwi_wet_amp','cai_wet_amp'];

  samplingArea.evaluate(function(samplingArea) {
    samplingArea.features.forEach(function(scene) {
    })
  })

  var neibData = []
  
  //Builds an mask based on the NDVI percentil 25%
  var onlyWetSeasonNei = function(image) {
    var seasonMask = image.select("ndvi_wet").gte(wetThresholdNei)
    return image.mask(seasonMask);
  }
  
  //Generates spectro-temporal information/bands for sampling and classification
  for (var i=0; i < neighborhoodArea.length ;i++){
    
    var sceneInfo = neighborhoodArea[i].split('/')
    
    
    var spectralDataNei = landsatCollection
                        .filterMetadata('WRS_PATH', 'equals', parseInt(sceneInfo[0]))
                        .filterMetadata('WRS_ROW', 'equals', parseInt(sceneInfo[1]))
                        .filterDate(startDate, endDate)
                        .map(spectralFeatures)
                        .map(clipCollection)
                        .select(['B3','B4','B5','B6','B7','NDVI','NDWI','CAI'])
    
    var wetThresholdNei = spectralDataNei
                              .select("NDVI")
                              .reduce(ee.Reducer.percentile([25]));
                              
    var wetSpectralDataNei = spectralDataNei
                              .select(bands, landsatBandsWet)
                              .map(onlyWetSeasonNei)
    
    var temporalData = getLatLong(temporalPercs(wetSpectralDataNei)).addBands([temporalFeatures(wetSpectralDataNei),
    elevation,slope])
    
    var bandSize = ee.Number(temporalData.bandNames().size())
    
    neibData.push(temporalData.set({BandNumber: bandSize}))

  }
  
    var neibCollection = ee.ImageCollection(neibData).filter(ee.Filter.gt('BandNumber',0)).mosaic().clip(getSamplingArea())
    var wetSpectralTemporalData = neibCollection.clip(LANDSAT_GRID.filter(ee.Filter.eq('TILE_T','T' +landsatWRSPath+landsatWRSRow)))
    
    print(neibCollection)

  return [wetSpectralTemporalData, neibCollection]
}

//Organizes the samples for the classifier training phase
var getTrainSamples = function() {
  
  var trainSamples = TRAIN_DATA
                      .select(classFieldName)
                      .filterBounds(samplingArea)

  return trainSamples
}

//Classifier training phase
var getTrainedClassifier = function() {
  var classifier = ee.Classifier.randomForest(rfNTrees, rfVarPersplit, 1, rfBagFraction, false, year);
  classifier = classifier.setOutputMode('PROBABILITY');

  var trainSamplesFeeded = featureSpace[1].clip(samplingArea).sampleRegions({
    collection: trainSamples.filter(ee.Filter.neq(classFieldName,null)),
    properties: [classFieldName],
    scale: 30,
    tileScale: 16
  });
  
  return classifier.train(trainSamplesFeeded, classFieldName);
}

//Runs trained classifier
var classify = function() {
  featureSpace = ee.Image(featureSpace[0])
  
  return featureSpace.classify(classifier).select(0);
}

//Adds visualization layers
var addLayers = function() {

  var pastureSamples = trainSamples.select(classFieldName).filter(ee.Filter.eq(classFieldName,1))
  var notPastureSamples = trainSamples.select(classFieldName).filter(ee.Filter.eq(classFieldName,0))

  var pastureContinuousStyle = { min:0, max:1, palette:['#37990a','#fff9b2','#d82727'], opacity: 1 }
  var pastureStyle = { palette:'#a37106',opacity: 1 }

  Map.addLayer(samplingArea,{},'Sampling Area')
  Map.addLayer(classificationArea, {},'Classification Area', false)
  Map.addLayer(notPastureSamples, { color: '#ff0000' },'Train Samples - Non-Pasture')
  Map.addLayer(pastureSamples, { color: '#f4f142' },'Train Samples - Pasture')
  
  /*THE LAYERS BELOW HAS BEEN COMMENTED BECAUSE THE EARTH ENGINE PLATFORM CANNOT LOAD THE RESULTS OF
  CLASSIFICATION, THUS CAUSING A COMPUTATION TIMED OUT ERROR***************************************/
  
  Map.addLayer(pastureContinuousResult, pastureContinuousStyle, "Pasture Continuous Result",false);
  Map.addLayer(pastureResult, pastureStyle, "Pasture Result");
}

//Export the results of the classification
var exportResults = function() {
  var pastureContinuousFilename =  "Pasture_Continuous_" + landsatWRSPath +'_'+ landsatWRSRow + '_' + year;
  var pastureFilename =  "Pasture_" + landsatWRSPath +'_'+ landsatWRSRow + '_' + year;

  Export.image.toDrive({
      image: pastureResult.byte(),
      description: pastureFilename,
      fileNamePrefix: pastureFilename,
      region: classificationArea,
      scale: 30,
      maxPixels: 1.0E13
  });

  Export.image.toDrive({
      image: pastureContinuousResult.multiply(10000).int16(),
      description: pastureContinuousFilename,
      fileNamePrefix: pastureContinuousFilename,
      region: classificationArea,
      scale: 30,
      maxPixels: 1.0E13
  });
}

/********************************************************************/
/**************** Classification Approach ****************************/
/********************************************************************/
var classFieldName = 'cons_' + year; //Collum used as reference for classifier

var samplingArea = getSamplingArea()

var neighborhoodArea = getNeibArea()

print(neighborhoodArea)

var classificationArea = getClassificationArea();

var featureSpace = getFeatureSpace();

var trainSamples = getTrainSamples();

var classifier = getTrainedClassifier();

var pastureContinuousResult = classify();

var pastureResult = pastureContinuousResult.gte(pastureMapThreshold);
pastureResult = pastureResult.mask(pastureResult);

addLayers()
exportResults()
