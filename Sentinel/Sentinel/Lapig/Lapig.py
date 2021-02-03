import math

class HelpLapig():

    def __init__(self, __ee):
        self.ee = __ee
    

    def getExpression(self,satellite,equation):
        index = {
        'L8':{
            'CAI':    "(b('B7') / b('B6'))",
            'NDVI':   "(b('B5') - b('B4')) / (b('B5') + b('B4'))",
            'NDWI':   "(b('B5') - b('B6')) / (b('B5') + b('B6'))",
            'eq':2720,
            'bands': ["B3","B4","B5","B6","B7","NDVI","NDWI","CAI"]
        },
        'L5_7':{
            'CAI':  "(b('B12') / b('B5'))",
            'NDVI': "(b('B4') - b('B3')) / (b('B4') + b('B3'))",
            'NDWI': "(b('B4') - b('B5')) / (b('B4') + b('B5'))",
            'bands':["B2","B3","B4","B5","B7","NDVI","NDWI","CAI"],
            'eq':672
        },
        'SENTINEL':{
            'CAI':    "(b('B12') / b('B11'))",
            'NDVI':   "(b('B8') - b('B4')) / (b('B8') + b('B4'))",
            'NDWI':   "(b('B8A') - b('B11')) / (b('B8A') + b('B11'))",
            'CRI1': "1/(b('B2')) - 1/(b('B3'))",
            'ARI_1': "(1/b('B3') - 1/b('B6'))*1000",
            'RGR': "b('B4')/b('B3')",
            'PSRI': "(b('B4') - b('B3') )/(b('B6'))",
            'SATVI': "((b('B11') - b('B4'))/(b('B11') + b('B4') + 0.5))*(1*0.5)-(b('B12')/2)*0.0001",
            'bands':[
                'B2','B3','B4','B5','B6','B7','B8','B8A',
                'B11','B12','NDVI','NDWI','CAI','CRI1', 'ARI_1', 'RGR',
                'PSRI', 'SATVI'],
            'BandsWet':['blue_wet','green_wet','re d_wet','rededge1_wet','rededge2_wet','rededge3_wet',
                        'nir_wet','rededge4_wet' ,'swir1_wet','swir2_wet','ndvi_wet','ndwi_wet','cai_wet',
                        'cri1_wet', 'ari1_wet', 'rgr_wet', 'psri_wet', 'satvi_wet'],
            'BandsWetAmp':['blue_wet_amp','green_wet_amp','red_wet_amp','rededge1_wet_amp',
            'rededge2_wet_amp','rededge3_wet_amp','nir_wet_amp','rededge4_wet_amp','swir1_wet_amp','swir2_wet_amp',
            'ndvi_wet_amp','ndwi_wet_amp','cai_wet_amp','cri1_wet_amp', 'ari1_wet_amp', 'rgr_wet_amp',
            'psri_wet_amp', 'satvi_wet_amp']
        
        }
    };
        return index[satellite][equation]

    def expression_select(self, image, satellite, band):
        return image.expression(self.getExpression(satellite,band)).select([0],[band]);


    def getLatLong(self, img):
        proj = self.ee.Image(img).select(0).projection()
        latlon = self.ee.Image.pixelLonLat()
        return self.ee.Image(img).addBands(latlon.select('longitude','latitude'));


    def getSRTM(self):
        def radians(img):
            return img.toFloat().multiply(math.pi).divide(180);

        terrain = self.ee.Algorithms.Terrain(self.ee.Image('USGS/SRTMGL1_003'));
        return {
            'elevation': terrain.select('elevation'),
            'slope': radians(terrain.select('slope')).expression('b("slope")*100'),
            'aspect': radians(terrain.select('aspect'))
        
        }

    def temporalFeatures(self, image,new_bands):
        min = image.reduce(self.ee.Reducer.min())
        max = image.reduce(self.ee.Reducer.max())
        median = image.reduce(self.ee.Reducer.median());
        stdv = image.reduce(self.ee.Reducer.stdDev());
        amp = (image.reduce(self.ee.Reducer.max())
                   .subtract(image.reduce(
                       self.ee.Reducer.min()))
                   .rename(new_bands))
        return self.ee.Image().select().addBands([min,max,median,amp,stdv]);


    def temporalPercs(self,image,percentile):
        percs = image.reduce(self.ee.Reducer.percentile(percentile))
        result = self.ee.Image().select().addBands([percs])

        return result;

    def getBands(self, satellite):
        bands = {
            'SENTINEL':[
                'B2','B3','B4','B5','B6','B7','B8','B8A',
                'B11','B12','NDVI','NDWI','CAI','CRI1', 'ARI_1', 'RGR',
                'PSRI', 'SATVI'],
            'L5_7':["B2","B3","B4","B5","B7","NDVI","NDWI","CAI"],
            'L8': ["B3","B4","B5","B6","B7","NDVI","NDWI","CAI"]
            
        }
        return bands[satellite]

