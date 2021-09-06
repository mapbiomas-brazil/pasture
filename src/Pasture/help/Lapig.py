import math


class HelpLapig:
    def __init__(self, __ee):
        self.ee = __ee

    def getLatLong(self, img):
        proj = self.ee.Image(img).select(0).projection()
        latlon = self.ee.Image.pixelLonLat()
        return self.ee.Image(img).addBands(latlon.select("longitude", "latitude"))

    def getSRTM(self):
        def radians(img):
            return img.toFloat().multiply(math.pi).divide(180)

        terrain = self.ee.Algorithms.Terrain(self.ee.Image("USGS/SRTMGL1_003"))
        return {
            "elevation": terrain.select("elevation"),
            "slope": radians(terrain.select("slope")).expression('b("slope")*100'),
            "aspect": radians(terrain.select("aspect")),
        }

    def temporalFeatures(self, image, new_bands):
        min = image.reduce(self.ee.Reducer.min())
        max = image.reduce(self.ee.Reducer.max())
        median = image.reduce(self.ee.Reducer.median())
        stdv = image.reduce(self.ee.Reducer.stdDev())
        amp = (
            image.reduce(self.ee.Reducer.max())
            .subtract(image.reduce(self.ee.Reducer.min()))
            .rename(new_bands)
        )
        return self.ee.Image().select().addBands([min, max, median, amp, stdv])

    def temporalPercs(self, image, percentile):
        percs = image.reduce(self.ee.Reducer.percentile(percentile))
        result = self.ee.Image().select().addBands([percs])

        return result

    def getNeibArea(self, path, row, LANDSAT_GRID):

        neitiles = []
        neitilesT = []

        xW = [1, 1]  # Window Path
        yW = [1, 1]  # Window Row

        for pInc in range(int(path) - xW[0], int(path) + xW[1] + 1):
            for rInc in range(int(row) - yW[0], int(row) + yW[1] + 1):
                pAux = pInc
                rAux = rInc
                if int(path) == 1 and pAux == 0:
                    pAux = 233
                elif int(path) == 233 and pAux == 234:
                    pAux = 1
                Aux = f"{pAux}/{rAux}"
                neitiles.append(Aux)
                tAux = f"T{pAux:03}{rAux:03}"
                neitilesT.append(tAux)
        return [
            LANDSAT_GRID.filter(self.ee.Filter.inList("TILE_T", neitilesT)),
            neitiles
        ]
