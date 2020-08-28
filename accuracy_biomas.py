#!/usr/bin/python
# -*- coding: utf-8 -*-

import gdal, ogr, csv, os;
import sys
import argparse
import math
from sys import argv;

def getclasssIndex(classs, layer):
	feature0 = layer.GetFeature(0);
	for i in range(0, feature0.GetFieldCount()):
		if feature0.GetFieldDefnRef(i).GetNameRef() == classs:
			return i;
	
	return -1;

def AccuracyAssessment(GDALDataSet, layer, classs, outdir, biome, year, precision):

	precision = precision.split(',')
	precision = map(int,precision)

	if (os.path.isfile(outdir+'accuracy_'+ str(args.year)+'.shp')==True) & (os.path.isfile(outdir+'accuracy_'+ str(args.year)+'.shx')==True) & (os.path.isfile(outdir+'accuracy_'+ str(args.year)+'.dbf')==True):
		os.remove(outdir+'accuracy_'+ str(args.year)+'.shp');
		os.remove(outdir+'accuracy_'+ str(args.year)+'.shx');
		os.remove(outdir+'accuracy_'+ str(args.year)+'.dbf');


	driver = ogr.GetDriverByName('ESRI Shapefile')
	output_file = driver.CreateDataSource(outdir);

	output_layer = output_file.CreateLayer('accuracy'+ str(args.year), None, ogr.wkbPoint );
	classsReference = ogr.FieldDefn(layer.GetFeature(0).GetFieldDefnRef(getclasssIndex(classs, layer)).GetNameRef(), ogr.OFTString)
	classsclasssification = ogr.FieldDefn('classsClas', ogr.OFTString);

	output_layer.CreateField(classsReference);
	output_layer.CreateField(classsclasssification);

	
	FieldNames = {}
	FieldNamesLista = [];
	line = 0;
	colum = 2;
	pastagem = 0;
	notPastagem = 1;


	gt = GDALDataSet.GetGeoTransform()
	rasterBand = GDALDataSet.GetRasterBand(1);
	
	for feature in layer:
		fieldValue = feature.GetFieldAsString(getclasssIndex(classs, layer));
		if(fieldValue not in FieldNames):
				FieldNamesLista.append(fieldValue);
				FieldNames[fieldValue] = line;
				line += 1

	totalAccuracy = [[0 for x in range(line)] for y in range(colum)]
	layer.ResetReading();

	for feature in layer:
		geom = feature.GetGeometryRef();
		mx, my = geom.GetX(), geom.GetY();

		try:
			px = int((mx - gt[0]) / gt[1]) #x pixel
			py = int((my - gt[3]) / gt[5]) #y pixel
			intval = rasterBand.ReadAsArray(px,py,1,1)
			pixelValue = intval[0][0];

			fieldValue = feature.GetFieldAsString(getclasssIndex(classs, layer));
			accurancyclasssIndex = FieldNames[fieldValue];
			classseReferenciaValue = '';

			if pixelValue in precision:
				totalAccuracy[pastagem][accurancyclasssIndex] += 1;
				classseReferenciaValue = 'Pastagem';
			else:
				totalAccuracy[notPastagem][accurancyclasssIndex] += 1;
				classseReferenciaValue = 'Nao Pastagem';

			feat = ogr.Feature(output_layer.GetLayerDefn())
			feat.SetGeometry(geom);
			feat.SetField(layer.GetFeature(0).GetFieldDefnRef(getclasssIndex(classs, layer)).GetNameRef(), fieldValue);
			feat.SetField('classsClas', classseReferenciaValue);

			output_layer.CreateFeature(feat)

		except Exception:
			pass

	count = 0;   
	for line in totalAccuracy:
		if count == 0:
			line.insert(0, 'Pastagem');
			count += 1;
		else:
			line.insert(0, 'NotPastagem')

	keys = []

	for key in FieldNamesLista:
		keys.append(key);

	keys.insert(0,'#####')
	totalAccuracy.insert(0,keys)

	areaBiomas = {'AMAZONIA': 425429893.3851285, 'CAATINGA': 83859398.94177887, 'CERRADO': 206390735.70466304,'MATA_ATLANTICA': 112869092.27114443, 'PAMPA': 16690165.517929632, 'PANTANAL': 15282761.098346883}

	biomes = []

	with open('/data/PASTAGEM/Mapeamento/MapBiomas/Versions/v5.0/Accuracy/biomas_col5.txt','rt') as in_file:
		for data in in_file:
			biomes.append(data.replace('\n',''))
	
	biomeData = biomes[biomes.index('BIOMA\t'+ biome)+1:biomes.index('BIOMA\t'+ biome)+36]

	yearPos = [i.split('\t')[0] for i in biomeData].index(year)
	
	biomePasture = float([i.split('\t')[1] for i in biomeData][yearPos])
	biomeArea = float(areaBiomas[biome])
	
	try:
		pasturePos = totalAccuracy[0].index('Pastagem Cultivada')
	except:
		pasturePos = None
	try:
		nonObsPos = totalAccuracy[0].index('N\xc3\xa3o observado')
	except:
		nonObsPos = None
	try:
		npasturePos =  totalAccuracy[0].index('Pastagem Natural')
	except:
		npasturePos =  None
	try:
		nonConsPos =  totalAccuracy[0].index('N\xc3\xa3o consolidado')
	except:
		nonConsPos = None
	
	try:
		nonValue = totalAccuracy[0].index('')
	except:
		nonValue = None

	if pasturePos != None: pastureOne,pastureTwo = totalAccuracy[1][pasturePos],totalAccuracy[2][pasturePos]
	else: pastureOne,pastureTwo = 0,0

	if npasturePos != None:	RefPtPt,RefPtNpt = pastureOne + totalAccuracy[1][npasturePos] , pastureTwo + totalAccuracy[2][npasturePos]
	else: RefPtPt,RefPtNpt = pastureOne , pastureTwo

	if nonValue != None: nonValuesOne,nonValuesTwo = totalAccuracy[1][nonValue],totalAccuracy[2][nonValue] 
	else: nonValuesOne,nonValuesTwo = 0,0
	if nonConsPos != None: nonConsOne,nonConsTwo = totalAccuracy[1][nonConsPos],totalAccuracy[2][nonConsPos]
	else: nonConsOne,nonConsTwo = 0,0

	if nonObsPos != None: nonObsOne,nonObsTwo = totalAccuracy[1][nonObsPos],totalAccuracy[2][nonObsPos]
	else: nonObsOne,nonObsTwo = 0,0

	RefNptPt = sum(totalAccuracy[1][1:]) - RefPtPt - nonObsOne - nonValuesOne - nonConsOne
	RefNptNpt = sum(totalAccuracy[2][1:]) - RefPtNpt - nonObsTwo - nonValuesTwo - nonConsTwo

	RefPtSum = RefPtPt + RefPtNpt
	RefNptSum = RefNptNpt +  RefNptPt
	
	PtSum = RefPtPt + RefNptPt
	NptSum = RefPtNpt + RefNptNpt

	totSamples = RefNptPt + RefNptNpt + RefPtPt + RefPtNpt

	corrRefPtPt = (float(RefPtPt)/float(PtSum))*(biomePasture/biomeArea)
	corrRefNptPt = (float(RefNptPt)/float(PtSum))*(biomePasture/biomeArea)

	corrRefPtNpt = (float(RefPtNpt)/float(NptSum))*((biomeArea-biomePasture)/biomeArea)
	corrRefNptNpt = (float(RefNptNpt)/float(NptSum))*((biomeArea-biomePasture)/biomeArea)

	producerAccRefPt = corrRefPtPt/(corrRefPtPt+corrRefPtNpt)
	producerAccRefNpt = corrRefNptNpt/(corrRefNptNpt+corrRefNptPt)

	userAccPt = corrRefPtPt/(corrRefPtPt+corrRefNptPt)
	userAccNpt =  corrRefNptNpt/(corrRefNptNpt+corrRefPtNpt)

	totCorrSamples = corrRefPtPt + corrRefNptPt + corrRefPtNpt + corrRefNptNpt

	globalAcc = (corrRefPtPt + corrRefNptNpt)/totCorrSamples

	PI = float(biomePasture/biomeArea)
	PC = PI*userAccPt + PI*(1-userAccNpt)
	ME = 1.96*math.sqrt((1/float(totSamples))*(((corrRefPtPt+corrRefPtNpt)/totCorrSamples)*userAccPt*(1-userAccPt)+((corrRefPtPt+corrRefPtNpt)/totCorrSamples)*(1-userAccNpt)*userAccNpt))

	AC = PC * float(biomeArea)
	LI = biomeArea*(PC - ME)
	LS = biomeArea*(PC + ME)

	#print(totalAccuracy,producerAccRefPt,userAccPt,globalAcc,PI,PC,ME,AC,LI,LS)

	return(totalAccuracy,producerAccRefPt,userAccPt,globalAcc,PI,PC,ME,AC,LI,LS,biomePasture,(biomeArea-biomePasture),biomeArea)
	
def WriteFile(AAs, outdir):
	with open(outdir+'accuracy_' + str(args.year) + '.csv', 'wb') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter=',');
		for line in AAs[0]:
			spamwriter.writerow(line);
		spamwriter.writerow('\n')
		spamwriter.writerow(('Producer Accuracy' , str(AAs[1])))
		spamwriter.writerow(('User Accuracy' , str(AAs[2])))
		spamwriter.writerow(('Global Accuracy' , str(AAs[3])))
		spamwriter.writerow(('PI' , str(AAs[4])))
		spamwriter.writerow(('PC' , str(AAs[5])))
		spamwriter.writerow(('ME' , str(AAs[6])))
		spamwriter.writerow(('AC' , str(AAs[7])))
		spamwriter.writerow(('LI' , str(AAs[8])))
		spamwriter.writerow(('LS' , str(AAs[9])))
		spamwriter.writerow('\n')
		spamwriter.writerow(('Pasture Area' , float(AAs[10])))
		spamwriter.writerow(('Non pasture Area' , float(AAs[11])))
		spamwriter.writerow(('Biome Area' , float(AAs[12])))

		return True;

def main(classsification, reference, classs, outdir, biome,year, precision=5000):

	GDALDataSet = gdal.Open(classsification);
	shape = ogr.Open(reference);
	print(shape)
	layer = shape.GetLayer();
	AAs =  AccuracyAssessment(GDALDataSet, layer, classs, outdir, biome, year, precision);
	WriteFile(AAs, outdir);

def parseArguments():
		    
    parser = argparse.ArgumentParser()
    parser.add_argument("classification", help="Raster file", type=str);
    parser.add_argument("reference", help="Shape file", type=str);
    parser.add_argument("classs", help="column value", type=str);
    parser.add_argument("outdir", help="Output directory", type=str);
    parser.add_argument("biome", help="Biome selected",type=str);
    parser.add_argument("year", help="Year selected",type=str);
    parser.add_argument("precision", help="precision to be analyzed", default=5000, nargs='?');
    
    args = parser.parse_args();

    return args

if __name__ == "__main__":

	args = parseArguments()

	main(args.classification, args.reference, args.classs, args.outdir, args.biome, args.year, args.precision);