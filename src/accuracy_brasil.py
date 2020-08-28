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

def AccuracyAssessment(GDALDataSet, layer, classs, outdir, year, precision):

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

		#try:
		#	yearClass = year
		#	if year > 2017:
		#		yearClass = 2017
		#	numVotes = int(feature.GetFieldAsString(getclasssIndex('nb_'+str(yearClass) + '_1', layer)))
		#except:
		#	numVotes = 0

		#if numVotes >= 3:

		#print(gt)
		#print(mx, my)

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

	print(sum(totalAccuracy[0]) + sum(totalAccuracy[1]))

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

	#mapArea = {
	#'2017_NEW' : {'Pasture': 177355574.156, 'Total':850038838.195},
	#'2018_NEW' : {'Pasture': 0.0, 'Total':850038838.195},
	#'2017_OLD' : {'Pasture': 171280442.157, 'Total':850038838.195}
	#}

	#mapArea = {
	#'2016' : {'Pasture': 169568217.479, 'Total':850038838.195},
	#'2017' : {'Pasture': 169796320.796, 'Total':850038838.195},
	#'2018' : {'Pasture': 169860979.623, 'Total':850038838.195}
	#}

	#mapArea = {
	#'2017_OLD' : {'Pasture': 171280442.15682864, 'Total':850038838.195},
	#'2017_COL3_1' : {'Pasture': 177355607.75328773, 'Total':850038838.195},
	#'2017_COL_4' : {'Pasture': 174131592.25627664, 'Total':850038838.195}
	#}

	#mapArea = {
	#'223_071_1985_NORM': {'Pasture': 1169754.18,'Total': 2673193.37},
	#'223_071_2000_NORM': {'Pasture': 1634527.10,'Total': 2673193.37},
	#'223_071_2010_NORM': {'Pasture': 1621163.24,'Total': 2673193.37},
	#'223_071_2015_NORM': {'Pasture': 1629227.26,'Total': 2673193.37},
	#'223_071_1985_OLD': {'Pasture': 1040652.30,'Total': 2673193.37},
	#'223_071_2000_OLD': {'Pasture': 1569037.15,'Total': 2673193.37},
	#'223_071_2010_OLD': {'Pasture': 1632185.87,'Total': 2673193.37},
	#'223_071_2015_OLD': {'Pasture': 1630858.87,'Total': 2673193.37}
	#}

	mapArea ={
		'1985': {'Pasture': 121384802.1, 'Total':850038946.4674064},
		'1986': {'Pasture': 121333604.5, 'Total':850038946.4674064},
		'1987': {'Pasture': 124765112.2, 'Total':850038946.4674064},
		'1988': {'Pasture': 130572431.2, 'Total':850038946.4674064},
		'1989': {'Pasture': 134626111, 'Total':850038946.4674064},
		'1990': {'Pasture': 137914291.4, 'Total':850038946.4674064},
		'1991': {'Pasture': 140789685.8, 'Total':850038946.4674064},
		'1992': {'Pasture': 143578524.2, 'Total':850038946.4674064},
		'1993': {'Pasture': 146190033.9, 'Total':850038946.4674064},
		'1994': {'Pasture': 149029085.8, 'Total':850038946.4674064},
		'1995': {'Pasture': 151741270.2, 'Total':850038946.4674064},
		'1996': {'Pasture': 153997778.6, 'Total':850038946.4674064},
		'1997': {'Pasture': 156176026.7, 'Total':850038946.4674064},
		'1998': {'Pasture': 158612165.9, 'Total':850038946.4674064},
		'1999': {'Pasture': 161188428.9, 'Total':850038946.4674064},
		'2000': {'Pasture': 164490686.3, 'Total':850038946.4674064},
		'2001': {'Pasture': 165542968.6, 'Total':850038946.4674064},
		'2002': {'Pasture': 167317623.4, 'Total':850038946.4674064},
		'2003': {'Pasture': 168669971.7, 'Total':850038946.4674064},
		'2004': {'Pasture': 170128592.4, 'Total':850038946.4674064},
		'2005': {'Pasture': 171414163.9, 'Total':850038946.4674064},
		'2006': {'Pasture': 173178793.5, 'Total':850038946.4674064},
		'2007': {'Pasture': 173579253.1, 'Total':850038946.4674064},
		'2008': {'Pasture': 173566223.3, 'Total':850038946.4674064},
		'2009': {'Pasture': 172178252, 'Total':850038946.4674064},
		'2010': {'Pasture': 171618596.3, 'Total':850038946.4674064},
		'2011': {'Pasture': 170231662.8, 'Total':850038946.4674064},
		'2012': {'Pasture': 169127308.4, 'Total':850038946.4674064},
		'2013': {'Pasture': 168214942.8, 'Total':850038946.4674064},
		'2014': {'Pasture': 168789448.4, 'Total':850038946.4674064},
		'2015': {'Pasture': 168704482.8, 'Total':850038946.4674064},
		'2016': {'Pasture': 169328441.9, 'Total':850038946.4674064},
		'2017': {'Pasture': 170122582.4, 'Total':850038946.4674064},
		'2018': {'Pasture': 170686078, 'Total':850038946.4674064},
		'2019': {'Pasture': 170903212.3, 'Total':850038946.4674064}
	}

	#mapArea = {
	#'2016' : {'Pasture': 155418238.772, 'Total':850038838.195},
	#'2017' : {'Pasture': 155923836.369, 'Total':850038838.195},
	#'2018' : {'Pasture': 155855484.423, 'Total':850038838.195}
	#}

	areaPasture = mapArea[str(year)]['Pasture']

	totalArea = mapArea[str(year)]['Total']
	
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

	RefNptPt = sum(totalAccuracy[1][1:]) - float(RefPtPt) - float(nonObsOne) - float(nonValuesOne) - float(nonConsOne)
	RefNptNpt = sum(totalAccuracy[2][1:]) - float(RefPtNpt) - float(nonObsTwo) - float(nonValuesTwo) - float(nonConsTwo)

	RefPtSum = float(RefPtPt) + float(RefPtNpt)
	RefNptSum = float(RefNptNpt) +  float(RefNptPt)
	
	PtSum = float(RefPtPt) + float(RefNptPt)
	NptSum = float(RefPtNpt) + float(RefNptNpt)

	totSamples = float(RefNptPt) + float(RefNptNpt) + float(RefPtPt) + float(RefPtNpt)

	corrRefPtPt = (float(RefPtPt)/float(PtSum))*(areaPasture/totalArea)
	corrRefNptPt = (float(RefNptPt)/float(PtSum))*(areaPasture/totalArea)

	corrRefPtNpt = (float(RefPtNpt)/float(NptSum))*((totalArea-areaPasture)/totalArea)
	corrRefNptNpt = (float(RefNptNpt)/float(NptSum))*((totalArea-areaPasture)/totalArea)

	producerAccRefPt = corrRefPtPt/(corrRefPtPt+corrRefPtNpt)
	producerAccRefNpt = corrRefNptNpt/(corrRefNptNpt+corrRefNptPt)

	userAccPt = corrRefPtPt/(corrRefPtPt+corrRefNptPt)
	userAccNpt =  corrRefNptNpt/(corrRefNptNpt+corrRefPtNpt)

	totCorrSamples = corrRefPtPt + corrRefNptPt + corrRefPtNpt + corrRefNptNpt

	globalAcc = (corrRefPtPt + corrRefNptNpt)/totCorrSamples

	PI = float(areaPasture/totalArea)
	PC = PI*userAccPt + PI*(1-userAccNpt)
	ME = 1.96*math.sqrt((1/float(totSamples))*(((corrRefPtPt+corrRefPtNpt)/totCorrSamples)*userAccPt*(1-userAccPt)+((corrRefPtPt+corrRefPtNpt)/totCorrSamples)*(1-userAccNpt)*userAccNpt))

	AC = PC * float(totalArea)
	LI = totalArea*(PC - ME)
	LS = totalArea*(PC + ME)

	#print(totalAccuracy,producerAccRefPt,userAccPt,globalAcc,PI,PC,ME,AC,LI,LS)

	return(totalAccuracy,producerAccRefPt,userAccPt,globalAcc,PI,PC,ME,AC,LI,LS,areaPasture,(totalArea-areaPasture),totalArea)
	
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
		spamwriter.writerow(('Total Area' , float(AAs[12])))

		return True;

def main(classsification, reference, classs, outdir, year, precision=5000):

	GDALDataSet = gdal.Open(classsification);
	shape = ogr.Open(reference);
	print(shape)
	layer = shape.GetLayer();
	AAs =  AccuracyAssessment(GDALDataSet, layer, classs, outdir, year, precision);
	WriteFile(AAs, outdir);

def parseArguments():
		    
    parser = argparse.ArgumentParser()
    parser.add_argument("classification", help="Raster file", type=str);
    parser.add_argument("reference", help="Shape file", type=str);
    parser.add_argument("classs", help="column value", type=str);
    parser.add_argument("outdir", help="Output directory", type=str);
    parser.add_argument("year", help="year selected",type=str);
    parser.add_argument("precision", help="precision to be analyzed", default=5000, nargs='?');
    
    args = parser.parse_args();

    return args

if __name__ == "__main__":

	args = parseArguments()

	main(args.classification, args.reference, args.classs, args.outdir, args.year, args.precision);
