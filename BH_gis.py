__author__ = "Ulises Francisco Ruiz Gomez"
__copyright__ = "Copyright 2022, GPS"
__credits__ = "GPS"

__version__ = "1.0.1"
__maintainer__ = "Francisco Ruiz"
__email__ = "franciscoruiz078@gmail.com"
__status__ = "Developer"

#+++++++++++++++++++++++++  LIBRARIES   +++++++++++++++++++++++++++++
import os
import pandas as pd
import shapefile as shp
import arcpy


#+++++++++++++++++++++++++  FUNCTIONS   +++++++++++++++++++++++++++++
def escorrentia(k, p, rd = False):
    """
    
    Calculo de la cantidad de agua, en mm, que genera una corriente
    superficial de acuerdo con la NOM-011-2015 de CONAGUA.
    
    <k>
    Valor de k ponderado promedio.
    
    <p>
    Precipiacion ponderada por área (mm).
    
    <rd>
    Decimales a redondear.
    
    """
    
    if k <= 0.15: ce = k*(p-250)/2000
    else: ce = k*(p-250)/2000 + (k-0.15)/1.5
    
    if rd != False: ce = round(ce, rd)
    
    return ce

def et_turc(p, t, rd = False, percentage = False):
    """
    
    Ecuación para el calculo de la evapotranspiracion real en milimetros,
    tomando en cuenta la precipitacion y la temperatura de
    la zona de estudio.
    
    <precip>
    Altura de la lámina de precipitación anual en milimetros.
    
    <t>
    Temperatura de la zona de estudio en grados celcius.
    
    <rd>
    Decimales a redondear.
    
    <percentage>
    Evapotranspiracion arrojada en porcentaje.
    """
    #Calculo del valor de L
    l = 300 + 25*t + 0.05*pow(t, 3)
    
    #Calculo de la ET
    etr = p/pow(0.9 + pow(p/l, 2), 1/2)
    
    if rd != False: etr = round(etr, rd)
    
    if percentage:
        etr_per = round((p/etr)*100, 2)
        return ("ET: {}, Porcentaje: {}%").format(etr, etr_per)
    else: return etr

def infil(p, et, esc):
    """
    
    Calculo de la escorrentia
    
    <p>
    Precipitación en mm
    
    <et>
    Evapotranspiración en mm
    
    <esc>
    Escurrimiento en mm
    
    """
    
    inf = p - (et + esc)
    
    return inf


#+++++++++++++++++++++++++  PARAMETERS   +++++++++++++++++++++++++++++
stations_file = arcpy.GetParameterAsText(0)
output_path = arcpy.GetParameterAsText(1)
experimental_k = arcpy.GetParameterAsText(2)
experimental_tmp = arcpy.GetParameterAsText(3)


#+++++++++++++++++++++++++  ARGUMENTS   +++++++++++++++++++++++++++++
arcpy.env.overwriteOutput = False
arcpy.env.workspace = output_path

bh_file = output_path + os.sep + 'BH.csv'

stations_shp = shp.Reader(stations_file)
outcome_tab = pd.DataFrame()


#+++++++++++++++++++++++++  PROCEDUREMENT  +++++++++++++++++++++++++++++
atts = stations_shp.fields[1:]  #Fetch oficial fields only.
colnames = []
for r in atts:
    colnames.append(r[0])   #Fetch attribute name only. Datatype, length, etc., are ignored.

ptemp_tab = pd.DataFrame(data = stations_shp.records(), columns = colnames)


arcpy.AddMessage('Calculated...')
#------------------------    OUTCOME FILLING    --------------------------
#-------------------------------------------------------------------------
outcome_tab['ID_STATION'] = ptemp_tab['ID_ESTACIO']
outcome_tab['POND_PRECIP'] = ptemp_tab['PRECIP'] * ptemp_tab['POLY_AREA']

if experimental_tmp == '':
    outcome_tab['TMP'] = ptemp_tab['TEMP']
else:
    outcome_tab['TMP'] = float(experimental_tmp)

outcome_tab['POND_TMP'] = outcome_tab['TMP'] * ptemp_tab['POLY_AREA']

if experimental_k == '':
    outcome_tab['K'] = ptemp_tab['K']
else:
    outcome_tab['K'] = float(experimental_k)


#----------------    EFFECTIVE PRECIPITATION, ET & INFILTRATION    ---------------
esc_values = []
et_values = []
infil_values = []
i = 0
while i < len(ptemp_tab.index):
    esc = escorrentia(outcome_tab['K'].iloc[i], outcome_tab['POND_PRECIP'].iloc[i], 2)
    et = et_turc(outcome_tab['POND_PRECIP'].iloc[i], outcome_tab['POND_TMP'].iloc[i], 2)
    infil_value = infil(outcome_tab['POND_PRECIP'].iloc[i], et, esc)*1e-9
    esc_values.append(esc)
    et_values.append(et)
    infil_values.append(infil_value)
    i += 1

arcpy.AddMessage('Adding Fields...')
outcome_tab['ESC'] = esc_values
outcome_tab['ET'] = et_values
outcome_tab['INF'] = infil_values
outcome_tab['INF_TOTAL'] = sum(outcome_tab['INF'])

arcpy.AddMessage('Exporting...')
#-----------------------    EXPORT OUTCOME DF    -------------------------
#-------------------------------------------------------------------------
outcome_tab.to_csv(bh_file, encoding = 'utf-8')

arcpy.AddMessage('Work Done!')