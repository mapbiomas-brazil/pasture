#!/usr/#!/usr/bin/python
import sys
import math
import time
import json
import ee
import logging
import traceback
import os
from os.path import expanduser

ee.Initialize()


home = expanduser("~")
tiles = open(home+'/tiles.in','r').read()
tiles = tiles.replace('T','').split('\n')


global pasture_type
global folder_dir
global Tile2Process

#pasture_type = None
pasture_type = 1 # 

BR_Tiles = ['001057','001058','001059','001060','001061','001062','001063','001064','001065','001066','001067','002057','002059','002060','002061','002062','002063','002064','002065','002066','002067','002068','003058','003059','003060','003061','003062','003063','003064','003065','003066','003067','003068','004059','004060','004061','004062','004063','004064','004065','004066','004067','005059','005060','005063','005064','005065','005066','005067','006063','006064','006065','006066','214064','214065','214066','214067','215063','215064','215065','215066','215067','215068','215069','215070','215071','215072','215073','215074','216063','216064','216065','216066','216067','216068','216069','216070','216071','216072','216073','216074','216075','216076','217062','217063','217064','217065','217066','217067','217068','217069','217070','217071','217072','217073','217074','217075','217076','218062','218063','218064','218065','218066','218067','218068','218069','218070','218071','218072','218073','218074','218075','218076','218077','219062','219063','219064','219065','219066','219067','219068','219069','219070','219071','219072','219073','219074','219075','219076','219077','220062','220063','220064','220065','220066','220067','220068','220069','220070','220071','220072','220073','220074','220075','220076','220077','220078','220079','220080','220081','221061','221062','221063','221064','221065','221066','221067','221068','221069','221070','221071','221072','221073','221074','221075','221076','221077','221078','221079','221080','221081','221082','221083','222061','222062','222063','222064','222065','222066','222067','222068','222069','222070','222071','222072','222073','222074','222075','222076','222077','222078','222079','222080','222081','222082','222083','223060','223061','223062','223063','223064','223065','223066','223067','223068','223069','223070','223071','223072','223073','223074','223075','223076','223077','223078','223079','223080','223081','223082','224060','224061','224062','224063','224064','224065','224066','224067','224068','224069','224070','224071','224072','224073','224074','224075','224076','224077','224078','224079','224080','224081','224082','225058','225059','225060','225061','225062','225063','225064','225065','225066','225067','225068','225069','225070','225071','225072','225073','225074','225075','225076','225077','225080','225081','226057','226058','226059','226060','226061','226062','226063','226064','226065','226066','226067','226068','226069','226070','226071','226072','226073','226074','226075','227058','227059','227060','227061','227062','227063','227064','227065','227066','227067','227068','227069','227070','227071','227072','227073','227074','227075','228058','228059','228060','228061','228062','228063','228064','228065','228066','228067','228068','228069','228070','228071','228072','229058','229059','229060','229061','229062','229063','229064','229065','229066','229067','229068','229069','229070','229071','230059','230060','230061','230062','230063','230064','230065','230066','230067','230068','230069','231057','231058','231059','231060','231061','231062','231063','231064','231065','231066','231067','231068','231069','232056','232057','232058','232059','232060','232061','232062','232063','232064','232065','232066','232067','232068','232069','233057','233058','233059','233060','233061','233062','233063','233064','233065','233066','233067','233068','220082']

if pasture_type == 0:
	folder_dir = "mapbiomas_col5_pasture_natural_v2"
	Tile2Process = tiles
	Col2Process = ee.FeatureCollection("users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_natural_QGIS") #natural
elif pasture_type == 1:
	folder_dir = "mapbiomas_col5_pasture_planted_v2"
	Tile2Process = tiles
	Col2Process = ee.FeatureCollection("users/vieiramesquita/mapbiomas_col3_1_all_stages_12_03_2018_past_cultivado_QGIS_new_pampa_v2") #planted
else:
	folder_dir = "mapbiomas_col5_pasture_v2"
	Tile2Process = BR_Tiles
	Col2Process = ee.FeatureCollection("users/vieiramesquita/LAPIG-PASTURE/VECTORS/mapbiomas_col3_1_ALL_STAGES_bin_12_03_2018_QGIS")

ExpCalc = {
	'CAI_L8': "((b('B7')<0)*0 + (b('B7') > 1)*1 + (b('B7') >= 0 & b('B7') <= 1)*b('B7'))/((b('B6')<0)*0 + (b('B6') > 1)*1 + (b('B6') >= 0 & b('B6') <= 1)*b('B6'))",
	'CAI_L5_7': "((b('B7')<0)*0 + (b('B7') > 1)*1 + (b('B7') >= 0 & b('B7') <= 1)*b('B7'))/((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5'))",
	'B1': "((b('B1')<0)*0 + (b('B1') > 1)*1 + (b('B1') >= 0 & b('B1') <= 1)*b('B1'))",
	'B2': "((b('B2')<0)*0 + (b('B2') > 1)*1 + (b('B2') >= 0 & b('B2') <= 1)*b('B2'))",
	'B3': "((b('B3')<0)*0 + (b('B3') > 1)*1 + (b('B3') >= 0 & b('B3') <= 1)*b('B3'))",
	'B4': "((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4'))",
	'B5': "((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5'))",
	'B6_L5': "b('B6')",
	'B6_L7': "b('B6_VCID_1')",
	'B6_L8': "((b('B6')<0)*0 + (b('B6') > 1)*1 + (b('B6') >= 0 & b('B6') <= 1)*b('B6'))",
	'B7': "((b('B7')<0)*0 + (b('B7') > 1)*1 + (b('B7') >= 0 & b('B7') <= 1)*b('B7'))",
	#'B10': "b('B10')",
	'NDVI_L8': "(((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')) - ((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')))/(((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')) + ((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')))", 
	'NDWI_L8': "(((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')) - ((b('B6')<0)*0 + (b('B6') > 1)*1 + (b('B6') >= 0 & b('B6') <= 1)*b('B6')))/(((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')) + ((b('B6')<0)*0 + (b('B6') > 1)*1 + (b('B6') >= 0 & b('B6') <= 1)*b('B6')))",
	'NDVI_L5_7': "(((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')) - ((b('B3')<0)*0 + (b('B3') > 1)*1 + (b('B3') >= 0 & b('B3') <= 1)*b('B3')))/(((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')) + ((b('B3')<0)*0 + (b('B3') > 1)*1 + (b('B3') >= 0 & b('B3') <= 1)*b('B3')))", 
	'NDWI_L5_7': "(((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')) - ((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')))/(((b('B4')<0)*0 + (b('B4') > 1)*1 + (b('B4') >= 0 & b('B4') <= 1)*b('B4')) + ((b('B5')<0)*0 + (b('B5') > 1)*1 + (b('B5') >= 0 & b('B5') <= 1)*b('B5')))",

}




config = {
	"grid": {
			"allTiles": BR_Tiles
		,	"tilesToProcess": Tile2Process
		,	"ftCollection":"users/vieiramesquita/LAPIG-PASTURE/VECTORS/LANDSAT_GRID_V2_PASTURE"
	} 

	, "metrics": {
			"series": [
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2015"
						,	"dtStart": '2014-07-01'
						,	"dtEnd": '2016-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					}, #2015
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2019"
						,	"dtStart": '2018-07-01'
						,	"dtEnd": '2020-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					},#2019
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2018"
						,	"dtStart": '2017-07-01'
						,	"dtEnd": '2019-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					},#2018
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2017"
						,	"dtStart": '2016-07-01'
						,	"dtEnd": '2018-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					}, #2017
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2016"
						,	"dtStart": '2015-07-01'
						,	"dtEnd": '2017-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					}, #2016
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2014"
						,	"dtStart": '2013-07-01'
						,	"dtEnd": '2015-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					}, #2014
					{
							"imgCollection": 'LANDSAT/LC08/C01/T1_TOA'
						,	"prefix": "L8P2013"
						,	"dtStart": '2012-07-01'
						,	"dtEnd": '2014-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B3']}
							,	{ "name": 'red', "expression": ExpCalc['B4']}
							,	{ "name": 'nir', "expression": ExpCalc['B5']}
							,	{ "name": 'swir1', "expression": ExpCalc['B6_L8']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L8']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L8']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L8']}
						]
					}, #2013
					{
							"imgCollection": 'LANDSAT/LE07/C01/T1_TOA'
						,	"prefix": "L7P2012"
						,	"dtStart": '2011-07-01'
						,	"dtEnd": '2013-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2012
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2011"
						,	"dtStart": '2010-07-01'
						,	"dtEnd": '2012-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2011
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2010"
						,	"dtStart": '2009-07-01'
						,	"dtEnd": '2011-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2010
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2009"
						,	"dtStart": '2008-07-01'
						,	"dtEnd": '2010-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2009
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2008"
						,	"dtStart": '2007-07-01'
						,	"dtEnd": '2009-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2008
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2007"
						,	"dtStart": '2006-07-01'
						,	"dtEnd": '2008-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2007
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2006"
						,	"dtStart": '2005-07-01'
						,	"dtEnd": '2007-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2006
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2005"
						,	"dtStart": '2004-07-01'
						,	"dtEnd": '2006-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2005
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2004"
						,	"dtStart": '2003-07-01'
						,	"dtEnd": '2005-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2004
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P2003"
						,	"dtStart": '2002-07-01'
						,	"dtEnd": '2004-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2003
					{
							"imgCollection": 'LANDSAT/LE07/C01/T1_TOA'
						,	"prefix": "L7P2002"
						,	"dtStart": '2001-07-01'
						,	"dtEnd": '2003-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2002
					{
							"imgCollection": 'LANDSAT/LE07/C01/T1_TOA'
						,	"prefix": "L7P2001"
						,	"dtStart": '2000-07-01'
						,	"dtEnd": '2002-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2001
					{
							"imgCollection": 'LANDSAT/LE07/C01/T1_TOA'
						,	"prefix": "L7P2000"
						,	"dtStart": '1999-07-01'
						,	"dtEnd": '2001-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #2000
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1999"
						,	"dtStart": '1998-07-01'
						,	"dtEnd": '2000-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1999
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1998"
						,	"dtStart": '1997-07-01'
						,	"dtEnd": '1999-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1998
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1997"
						,	"dtStart": '1996-07-01'
						,	"dtEnd": '1998-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1997
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1996"
						,	"dtStart": '1995-07-01'
						,	"dtEnd": '1997-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1996
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1995"
						,	"dtStart": '1994-07-01'
						,	"dtEnd": '1996-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1995
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1994"
						,	"dtStart": '1993-07-01'
						,	"dtEnd": '1995-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1994
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1993"
						,	"dtStart": '1992-07-01'
						,	"dtEnd": '1994-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1993
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1992"
						,	"dtStart": '1991-07-01'
						,	"dtEnd": '1993-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1992
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1991"
						,	"dtStart": '1990-07-01'
						,	"dtEnd": '1992-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1991
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1990"
						,	"dtStart": '1989-07-01'
						,	"dtEnd": '1991-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1990
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1989"
						,	"dtStart": '1988-07-01'
						,	"dtEnd": '1990-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1989
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1988"
						,	"dtStart": '1987-07-01'
						,	"dtEnd": '1989-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1988
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1987"
						,	"dtStart": '1986-07-01'
						,	"dtEnd": '1988-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1987
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1986"
						,	"dtStart": '1985-07-01'
						,	"dtEnd": '1987-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					}, #1986
					{
							"imgCollection": 'LANDSAT/LT05/C01/T1_TOA'
						,	"prefix": "L5P1985"
						,	"dtStart": '1984-07-01'
						,	"dtEnd": '1986-07-01'
						,	"primary": [
								{ "name": 'green', "expression": ExpCalc['B2'] }
							,	{ "name": 'red', "expression": ExpCalc['B3']}
							,	{ "name": 'nir', "expression": ExpCalc['B4']}
							,	{ "name": 'swir1', "expression": ExpCalc['B5']}
							,	{ "name": 'swir2', "expression":ExpCalc['B7']}
							,	{ "name": 'ndvi', "expression": ExpCalc['NDVI_L5_7']}
							,	{ "name": 'ndwi', "expression": ExpCalc['NDWI_L5_7']}
							,	{ "name": 'cai', "expression": ExpCalc['CAI_L5_7']}
						]
					} #1985
				]
			,	"startIndexSerie": 0
			,	"secondary": [
					{ 
						"name": "gte_p25_ndvi"
						, "band": "ndvi"
						, "percentile": 25
						, "reducers": [
									{ "type": "reducer", "suffix": 'mean', "obj": ee.Reducer.mean() }
								,	{ "type": "reducer", "suffix": 'min', "obj": ee.Reducer.min() }
								,	{ "type": "reducer", "suffix": 'max', "obj": ee.Reducer.max() }
								,	{ "type": "reducer", "suffix": 'stdDev', "obj": ee.Reducer.stdDev() }
								,	{ "type": "reducer", "suffix": 'p10', "obj": ee.Reducer.percentile([10]) }
								,	{ "type": "reducer", "suffix": 'p25', "obj": ee.Reducer.percentile([25]) }
								,	{ "type": "reducer", "suffix": 'p75', "obj": ee.Reducer.percentile([75]) }
								,	{ "type": "reducer", "suffix": 'p90', "obj": ee.Reducer.percentile([90]) }
								,	{ "type": "amplitude" }
							] 
					}
			]
			, "tertiary": [
			]
			, "notNullBands": [  ]
	}
	, "cloud": {
			"cloudCoverThreshold": 80
		, "gapfillValue": -1
	}
	, "trainning": {
			"scale": 30
		, "nPoints": 2700
		, "gridCellSize": 3
		, "classValues": [1,0]
		, "strategy": '50/50'
		, "classBandName": 'class'
		, 'outlierThreshold': 0.02
		, 'outlierBandname': 'ndvi-0809'
		, "referenceMask": ee.Image('users/lealparente/pasture_mask_v8').expression("(b('b1') == 1) ? 1 : 0")
	}
	, "classification": {
			"nTrees": 500
		, "variablesPerSplit": 6
		, "bagFraction": 0.5
		, "minLeafPopulation": 1
	}
	, "filter": {
			"spatial": {
				"enable": False,
				"maxSize": 20,
				"possibleMaxSize": 100,
				"threshold": 0.5
			}
	}
	, "download": {
			"createTask": True
			, "poolSize": 6
			, "poolCheckTime": 60
			,	"attempts": 20
			#, "taskConfig": { "scale": 30, "maxPixels": 1.0E13, "driveFolder": folder_dir}
			, "taskConfig": { "scale": 30, "maxPixels": 1.0E13, "bucket": 'mapbiomas-pastagem'}
	}
}

extra = { 'current_tile': None}
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(current_tile)s # %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger = logging.LoggerAdapter(logger, extra)


def getMetrics(serie, gridCell,gridNumber):

	result = None;
	
	primaryMetrics = serie['primary'];
	secondaryMetrics = config['metrics']['secondary'];
	tertiaryMetrics = config['metrics']['tertiary'];
	imgCollection = ee.ImageCollection(serie['imgCollection'])
	cloudCoverThreshold = config['cloud']['cloudCoverThreshold']

	global gridWRS

	gridname = str(int(gridNumber[:3])) + '/' + str(int(gridNumber[3:]))

	gridWRS =  ee.FeatureCollection("users/vieiramesquita/LAPIG-PASTURE/VECTORS/LANDSAT_GRID_V2_PASTURE").filter(ee.Filter.eq('SPRNOME',gridname))

	def clipCollection(img):
		wrsProps = ee.Number(img.get('WRS_PATH')).format().cat('/').cat(ee.Number(img.get('WRS_ROW')).format())
		gridSelect = gridWRS.filter(ee.Filter.eq('SPRNOME',wrsProps))
		return img.clip(gridSelect)

	def getLatLong(img):

		# Get the projection
		proj = ee.Image(img).projection()
		# get coordinates image
		latlon = ee.Image.pixelLonLat()
		
		return ee.Image(img).addBands(latlon.select('longitude','latitude'))

	def radians(img):
		return img.toFloat().multiply(math.pi).divide(180)
	
	def calcPrimaryMetrics(img):

		BQAValue = None
		SeriesVersion = str((serie['prefix'])[:2])

		if SeriesVersion == 'L8':
			BQAValue = 2720
		else:
			BQAValue = 672

		fmask = img.select(['BQA']).eq(BQAValue);
		img = img.mask(fmask);

		innerResult = None;
		
		for primaryMetric in primaryMetrics:

			metricImg = img.expression(primaryMetric['expression']).select([0],[primaryMetric['name']]);

			if primaryMetric['name'] in ['green','red','nir','swir1','swir2']:
				metricImg = metricImg.mask(metricImg.gte(0.0));
				metricImg = metricImg.mask(metricImg.lte(1.0));
			if primaryMetric['name'] in ['cai']:
				metricImg = metricImg.mask(metricImg.gte(0.0));
			if primaryMetric['name'] in ['temp']:
				metricImg = metricImg.mask(metricImg.gte(273.0));
			if primaryMetric['name'] in ['ndvi', 'ndwi']:
				metricImg = metricImg.mask(metricImg.gte(-1.0));
				metricImg = metricImg.mask(metricImg.lte(1.0));

			if innerResult is None:
				innerResult = metricImg;
			else:
				innerResult = innerResult.addBands(metricImg);

		return innerResult.copyProperties(img);

	#metrics = imgCollection.filterBounds(gridCell.geometry().centroid()) \
	#	.filterMetadata('CLOUD_COVER', 'less_than', cloudCoverThreshold) \
	#	.filterDate(serie['dtStart'],serie['dtEnd']) \
	#	.map(calcPrimaryMetrics);

	WRS_PATH= int(gridNumber[:3])
	WRS_ROW = int(gridNumber[3:])

	metrics = imgCollection \
		.filterMetadata('WRS_PATH', 'equals', WRS_PATH) \
		.filterMetadata('WRS_ROW', 'equals', WRS_ROW) \
		.filterMetadata('CLOUD_COVER', 'less_than', cloudCoverThreshold) \
		.filterDate(serie['dtStart'],serie['dtEnd']) \
		.map(calcPrimaryMetrics);

	permanentBands = []

	for secondaryMetric in secondaryMetrics:
		metricFilter = metrics.select([secondaryMetric['band']]).reduce(ee.Reducer.percentile([secondaryMetric['percentile']]));
		
		def calcSecondaryMetrics(img):
			metricMask = img.select([secondaryMetric['band']]).gte(metricFilter);
			return img.mask(metricMask);

		metricImgCollection = metrics.map(calcSecondaryMetrics).map(clipCollection);

		#print(metricImgCollection.size().getInfo())
		
		for reducer in secondaryMetric['reducers']:
			metricImg = None;
			
			if reducer['type'] == 'reducer':
				metricImg = metricImgCollection.reduce(reducer['obj']);
				#print(metricImg.bandNames().getInfo())
			elif reducer['type'] == 'quality':
				metricImg = metrics.qualityMosaic(secondaryMetric['band']);
			elif reducer['type'] == 'amplitude':
				metricImg = metricImgCollection.reduce(ee.Reducer.minMax());
			
			for primaryMetric in primaryMetrics:
				bandName = None;
				newBandName = None;
				if reducer['type'] == 'reducer':
					bandName = primaryMetric['name'] + "_" + reducer['suffix'];
					newBandName = reducer['suffix'] + "_" + primaryMetric['name'] + "_" + secondaryMetric['name'];
				elif reducer['type'] == 'quality':
					bandName = primaryMetric['name'];
					newBandName = primaryMetric['name'] + "_" + reducer['name'];
				elif reducer['type'] == 'amplitude':
					minBand = primaryMetric['name']+"_min";
					maxBand = primaryMetric['name']+"_max";
					bandName = "amp_" + primaryMetric['name'] + "_" + secondaryMetric['name'];
					newBandName = bandName;

					metricImg = metricImg.addBands(metricImg.expression("b('"+maxBand+"') - b('"+minBand+"')").select([0],[bandName]));

				auxMetricImg = metricImg.select( [bandName], [newBandName] );

				if not ('temp' in reducer and reducer['temp'] == True):
					permanentBands.append(newBandName);
				
				if result is None:
					result = auxMetricImg;
				else:
					result = result.addBands(auxMetricImg);

	for tertiaryMetric in tertiaryMetrics:
		tertiaryMetricImg = result.expression(tertiaryMetric['expresion']).select([0],[tertiaryMetric['name']]);
		result = result.addBands(tertiaryMetricImg);
		permanentBands.append(tertiaryMetric['name']);

	terrain = ee.Algorithms.Terrain(ee.Image('USGS/SRTMGL1_003').clip(gridWRS));
	elevation = (terrain.select('elevation'))
	slope = (radians(terrain.select('slope'))).expression('b("slope")*100')

	result = result#.select(permanentBands)

	bandSize = ee.Number(result.bandNames().size())

	#return result.set({'BandNumber': bandSize})

	return ee.Image(getLatLong(result)).addBands([elevation,slope]).set({'BandNumber': bandSize})

def keyToSeed(key):
	return abs(hash(key)) % (10 ** 8)

def getClassifiers(tile, gridCell, neighborsGridCell, serie, neiYears):
	
	series = config['metrics']['series']
	nPoints = config['trainning']['nPoints']
	nTrees = config['classification']['nTrees'];
	classBand = config['trainning']['classBandName']
	gridCellSize = config['trainning']['gridCellSize']
	bagFraction = config['classification']['bagFraction'];
	variablesPerSplit = config['classification']['variablesPerSplit'];
	minLeafPopulation = config['classification']['minLeafPopulation'];
	
	result = []
	year = int((serie['prefix'])[3:])
	ColClass = str("cons_"+str(year))
	DataScale = 30	
	neiTrainningDataset = None
	trainningDataset = None
	CompletedDataset = None
	
	key = serie['prefix'] + str(tile) + '_';
	seed = keyToSeed(key);

	if year > 2017:

		Y2013 = {"imgCollection": 'LANDSAT/LC08/C01/T1_TOA','prefix':'L8P2013','dtStart': '2012-07-01','dtEnd': '2014-07-01','primary':serie['primary']}
		Y2014 = {"imgCollection": 'LANDSAT/LC08/C01/T1_TOA','prefix':'L8P2014','dtStart': '2013-07-01','dtEnd': '2015-07-01','primary':serie['primary']}
		Y2015 = {"imgCollection": 'LANDSAT/LC08/C01/T1_TOA','prefix':'L8P2015','dtStart': '2014-07-01','dtEnd': '2016-07-01','primary':serie['primary']}
		Y2016 = {"imgCollection": 'LANDSAT/LC08/C01/T1_TOA','prefix':'L8P2016','dtStart': '2015-07-01','dtEnd': '2017-07-01','primary':serie['primary']} 
		Y2017 = {"imgCollection": 'LANDSAT/LC08/C01/T1_TOA','prefix':'L8P2017','dtStart': '2016-07-01','dtEnd': '2018-07-01','primary':serie['primary']}
	
		seriesY = [Y2013,Y2014,Y2015,Y2016,Y2017]
	
		yearlist = ['cons_2013','cons_2014','cons_2015','cons_2016','cons_2017']
	
	
		for l in range(0,len(seriesY)):
	
			neibData = []
	
			for i in range(0,len(neighborsGridCell)):
		
				neiGridCellId = neighborsGridCell[i]['id']
				neiGridCellFeat = neighborsGridCell[i]['feature']
	
				gridId = str(neiGridCellId)
				
				try:
					neiMetrics = getMetrics(seriesY[l], neiGridCellFeat,gridId)
					neiMetrics = ee.Image(neiMetrics)
					errorTest = neiMetrics.select(0).getInfo()
				except:
					print('Error - Image - GRID ' + neiGridCellId + ' - Year ' + str(yearlist[l][3:]))
					continue
	
				neibData.append(neiMetrics)
	
			neibData = ee.Image(ee.ImageCollection(neibData).filter(ee.Filter.gt('BandNumber',0)).mosaic())
		
			sPoints = Col2Process.filter(ee.Filter.neq(yearlist[l], None)).select([yearlist[l]],['classValues'])
			
			def getFeatures(n): return n['feature']
	
			getNeibArea = ee.FeatureCollection(list(map(getFeatures,neighborsGridCell)))
	
			neiTrainningDataset = neibData.sampleRegions(collection = sPoints.filterBounds(getNeibArea.geometry()), properties= ['classValues'], scale=DataScale,tileScale=16)
	
			if neiTrainningDataset is not None:
				if trainningDataset is None:
					trainningDataset = neiTrainningDataset
				else:
					trainningDataset = trainningDataset.merge(neiTrainningDataset)
				
			else:
				logger.warning('Classifier %s can\'t be generate. There weren\'t enough samples', key)

	else:

		neibData = []

		for i in range(0,len(neighborsGridCell)):
	
			neiGridCellId = neighborsGridCell[i]['id']
			neiGridCellFeat = neighborsGridCell[i]['feature']

			gridId = str(neiGridCellId)
			
			try:
				neiMetrics = getMetrics(serie, neiGridCellFeat, gridId)
				neiMetrics = ee.Image(neiMetrics)
				errorTest = neiMetrics.select(0).getInfo()
			except:
				print('Error - Image - GRID ' + neiGridCellId + ' - Year ' + str(year))
				continue

			neibData.append(neiMetrics)

		neibData = ee.Image(ee.ImageCollection(neibData).filter(ee.Filter.gt('BandNumber',0)).mosaic())
	
		sPoints = Col2Process.filter(ee.Filter.neq(ColClass, None)).select([ColClass],['classValues'])
		
		def getFeatures(n): return n['feature']

		getNeibArea = ee.FeatureCollection(list(map(getFeatures,neighborsGridCell)))

		neiTrainningDataset = neibData.sampleRegions(collection = sPoints.filterBounds(getNeibArea.geometry()), properties= ['classValues'], scale=DataScale,tileScale=16)

		if neiTrainningDataset is not None:
			if trainningDataset is None:
				trainningDataset = neiTrainningDataset
			else:
				trainningDataset = trainningDataset.merge(neiTrainningDataset)
			
		else:
			logger.warning('Classifier %s can\'t be generate. There weren\'t enough samples', key)



	try:
		key = tile + '_' + str(gridCellSize) + 'x' + str(gridCellSize);
		seed = keyToSeed(key);

		if neiTrainningDataset is not None:
			trainningDataset = trainningDataset.set('band_order', neiTrainningDataset.get('band_order'))

		#.classifier = ee.Classifier.randomForest(nTrees, variablesPerSplit, minLeafPopulation, bagFraction, False, seed);
		classifier = ee.Classifier.smileRandomForest(nTrees, variablesPerSplit, minLeafPopulation, bagFraction, None, seed)
		classifier = classifier.train(trainningDataset, ee.String('classValues'));
		classifier = classifier.setOutputMode('PROBABILITY');
			
				
		logger.warning('Classifier %s was generate', key)
		result.append({ 'id': key, 'classifier': classifier });
	except:
		traceback.print_exc()


	return result

def doClassification(metrics, gridCell, classifiers):
	
	classificationArray = []
	
	clipedMetrics = metrics.clip(gridCell.geometry())

	for c in classifiers:
		logger.debug('Executing classifier %s', c['id'] )
		classificationArray.append(clipedMetrics.classify(c['classifier']))
	
	finalClassification = None;
	if len(classificationArray) > 1:
		finalClassification = ee.ImageCollection.fromImages(classificationArray).mean()
	else:
		finalClassification = classificationArray[0]

	finalClassification = finalClassification.multiply(10000).toInt16()
	finalClassification = finalClassification.set('system:footprint', metrics.get('system:footprint'))

	return finalClassification

def spatialFilter(classification):

	maxSize = config['filter']['spatial']['maxSize']
	threshold = config['filter']['spatial']['threshold']
	possibleMaxSize = config['filter']['spatial']['possibleMaxSize']

	classMask = classification.gte(threshold)
	labeled = classMask.mask(classMask).connectedPixelCount(possibleMaxSize, True)
	
	region = labeled.lt(maxSize)
	kernel = ee.Kernel.square(1)

	neighs = classification.neighborhoodToBands(kernel).mask(region)
	majority = neighs.reduce(ee.Reducer.mode())
	filtered = classification.where(region, majority)

	return filtered

def run(tile, gridCell, neighborsGridCell):
	
	series  = config['metrics']['series'];
	startIndexSerie = config['metrics']['startIndexSerie'];
	
	result = {};
	
	mainSerie = series[0]
	logger.debug('Main serie prefix: %s', mainSerie['prefix'])

	neiYears = [None]

	for i in range(startIndexSerie, len(series)):
		serie = series[i];
		metrics = getMetrics(serie, gridCell,str(tile));

		try:
			neiYears = [series[i-1]]
		except:
			pass
		try:
			neiYears = [series[i+1]]
		except:
			pass
		try:
			neiYears = [series[i-1],series[i+1]]
		except:
			pass

		classifiers = getClassifiers(tile, gridCell, neighborsGridCell, serie,neiYears)
		logger.info('Run classification for tile %s', serie['prefix'])
		serieResult = doClassification(metrics, gridCell, classifiers)
		result[serie['prefix'] + tile] = serieResult;
		
	return result

def checkPoolState(config, taskPool):
	
	logger.info('The download\'s pool is full... waiting %s secs', config['download']['poolCheckTime'])
	time.sleep(config['download']['poolCheckTime'])

	for task in list(taskPool):
		status = task.status()
		
		taskStatus = status['state']
		taskId = task.config['description']

		if taskStatus in (ee.batch.Task.State.FAILED, ee.batch.Task.State.COMPLETED, ee.batch.Task.State.CANCELLED):
			taskPool.remove(task)
			if('error_message' in status):
				logger.error('Exportation %s %s', taskId, status['error_message'])
			if('error_message' in status and (\
					status['error_message'] == 'User memory limit exceeded.' or \
					('Earth Engine memory capacity exceeded.' in status['error_message']) or \
					('Computation timed out' in status['error_message'])  	 or \
					('internal error' in status['error_message'])			 or \
					('Unable to write to bucket' in status['error_message']) ) ):
				reRunCount = mapResult[taskId]['reRunCount'];
				if(reRunCount < config['download']['attempts']):
					logger.info('Try export classification %s.tif again', taskId)

					reRuntask = ee.batch.Export.image.toCloudStorage(mapResult[taskId]['result'], description = taskId,bucket = mapResult[taskId]['bucket'], \
															  fileNamePrefix =mapResult[taskId]['fileNamePrefix'], region = mapResult[taskId]['region'], \
															   scale = mapResult[taskId]['scale'],maxPixels = mapResult[taskId]['maxPixels'])
					mapResult[taskId]['reRunCount'] = reRunCount + 1;
					reRuntask.start()
					taskPool.append(reRuntask)
		else:
			logger.info('Exportation %s %s', taskId, taskStatus)

def getGridCell(tile):

	gridCellSize = config['trainning']['gridCellSize']
	incNumber = (gridCellSize - 1) / 2

	#print(tile)

	path = int(tile[:3])
	row = int(tile[3:])

	result = []

	tAuxArray = []
	for pInc in range(int(path-incNumber), int((path+incNumber) + 1)):
		for rInc in range(int(row-incNumber), int((row+incNumber) + 1)):
		
			pAux = pInc
			rAux = rInc

			if path == 1 and pAux == 0:
				pAux = 233
			elif path == 233 and pAux == 234:
				pAux = 1
		
			tAux = str(pAux).zfill(3) + str(rAux).zfill(3)
		
			if tAux in tileDict:
				tAuxArray.append(tAux)
				gridCell = ee.FeatureCollection(config['grid']['ftCollection']) \
					.filter(ee.Filter.eq('TILE_T', 'T'+tAux)) \
					.first();
				
				result.append({ "id": tAux, "feature": gridCell })

	logger.debug('Neighbors tiles: %s', tAuxArray)

	return result

center = None
taskPool = []
mapResult = {}
tileDict = {}

for tile in config['grid']['allTiles']:
	tileDict[tile] = True

for tile in config['grid']['tilesToProcess']:
	
	extra['current_tile'] = 'T'+str(tile)

	logger.info('Processing tile %s', tile)

	neighborsGridCell = getGridCell(tile);
 
	execFlag = True
	gridCell = ee.FeatureCollection(config['grid']['ftCollection']) \
		.filter(ee.Filter.eq('TILE_T', 'T'+tile)) \
		.first();

	while execFlag:
		try:
			gridGeometry = gridCell.geometry().bounds();
			coordList = gridGeometry.coordinates().getInfo()
			seriesResult = run(tile, gridCell, neighborsGridCell)
	
			while len(taskPool) >= config['download']['poolSize']:
				checkPoolState(config,taskPool)
	
			for taskId,serieResult in seriesResult.items():
				taskConfig = config['download']['taskConfig']
				taskConfig['region'] = [coordList[0][0], coordList[0][1], coordList[0][2], coordList[0][3]]
	
				logger.info('Export classification %s.tif %s', taskId, str(taskConfig['region']))
				
				IDPrefix = None

				if pasture_type == 0:
					IDPrefix = taskId[3:7]+taskId[0:3]+taskId[7:]+"_natural"
				elif pasture_type ==1:
					IDPrefix = taskId[3:7]+taskId[0:3]+taskId[7:]+"_planted"
				else:
					IDPrefix = taskId[3:7]+taskId[0:3]+taskId[7:]

				taskId = IDPrefix

				task = ee.batch.Export.image.toCloudStorage(image = serieResult, description = taskId,bucket = taskConfig['bucket'], \
															  fileNamePrefix =('COL5_105B/'+ taskId), region = taskConfig['region'], \
															   scale = taskConfig['scale'],maxPixels = taskConfig['maxPixels'])

				mapResult[taskId] = { 'result': serieResult, 'config': taskConfig.copy(), 'reRunCount': 0, 'fileNamePrefix': 'COL5_105B/'+ taskId };
				task.start()
	
				taskPool.append(task)
				execFlag = False  
		except:
			traceback.print_exc()
			execFlag = True

while len(taskPool) > 0:
	checkPoolState(config,taskPool)
