__author__ = "Ulises Francisco Ruiz Gomez"
__copyright__ = "Copyright 2022, GPS"
__credits__ = "GPS"

__version__ = "1.0.2"
__maintainer__ = "Francisco Ruiz"
__email__ = "uf.ruizgomez@ugto.mx"
__status__ = "Developer"


import os
import pandas as pd
import arcpy

#Parameters
tab_name = arcpy.GetParameterAsText(0)  #Table name
statis_path = arcpy.GetParameterAsText(1)

#Enviroment Arguments
arcpy.env.overwriteOutput = False
# arcpy.env.workspace = statis_path


#Arguments
complete_path = r"C:\Users\Francisco Ruiz\OneDrive - Universidad de Guanajuato\UG\SEM_6\SIG_AVANZADO_2022\SEMANA_08"
ks_records = pd.read_csv(complete_path + os.sep + "GPS_COEFICIENTES.csv", encoding='utf-8')
statis_path += os.sep + 'aux_Ks'

arcpy.AddMessage("Creating aux_ks folder")
#Create a new folder where will be saved whole created files
if not os.path.isdir(statis_path):
    os.mkdir(statis_path)
statis_file = statis_path + os.sep + 'statistics.csv'

arcpy.AddMessage("Creating summary")
#Proccesses
arcpy.Statistics_analysis(in_table=tab_name, out_table=statis_file, statistics_fields=[["US_EDAFO", "COUNT"]], case_field=["US_EDAFO"])


#Get ks
class Suelo:
    def __init__(self, type, permea):
        self.tipo = type
        self.permea = permea
    
    def iguala(self):
        if self.tipo == "Agricultura de riego (incluye riego eventual)" or self.tipo == "Agricultura de humedad":
            suelo_k = "Cultivos En Hilera"
        elif self.tipo == "Agricultura de temporal":
            suelo_k = "Cultivos Legumbres o rotación de pradera"
        elif self.tipo == "Área sin vegetación aparente":
            suelo_k = "Barbecho, áreas incultas y desnudas"
        elif self.tipo == "Asentamiento humano" or self.tipo == "Cuerpo de agua":
            suelo_k = "Zonas urbanas"
        elif self.tipo == "Bosque de encino":
            suelo_k = "Bosque Cubierto del 50 al 75%"
        elif self.tipo == "Bosque de pino" or self.tipo == "Bosque de pino-encino (incluye encino-pino)":
            suelo_k = "Bosque Cubierto más del 75%"
        elif self.tipo == "Chaparral":
            suelo_k = "Pastizal Más del 75% - Poco -"
        elif self.tipo == "Matorral crasicaule" or self.tipo == "Mezquital (incluye huizachal)" or self.tipo == "Pastizal natural (incluye pastizal - huizachal)":
            suelo_k = r"Pastizal Menos del 50% - Excesivo -"
        elif self.tipo == "Matorral subtropical" or self.tipo == "Pastizal inducido" or self.tipo == "Vegetación halófila y gipsófila":
            suelo_k = "Pastizal Del 50 al 75% - Regular -"
        
        return suelo_k


arcpy.AddMessage("Evaluating with basis on Criteria")
#Evaluate US_EDAFO field with criteria
gps_file = pd.DataFrame(columns=['ID', 'US_EDAFO', 'CRITERIA', 'K'])

records = pd.read_csv(statis_file)
records.pop('FID')
records.pop('FREQUENCY')
records.pop('COUNT_US_EDAFO')

records["ID"] = records.index

ks_records = pd.read_csv(complete_path + os.sep + "GPS_COEFICIENTES.csv", encoding = 'utf-8')


for i,rec in records.iterrows():
    #Aplicate criteria for ks
    land_type = rec["US_EDAFO"].split("/")[0].strip()
    land_permea = rec["US_EDAFO"].split("/")[1].strip()
    land = Suelo(land_type, land_permea)
    try:
        patt = land.iguala() + " / " + land.permea
    except:
        arcpy.AddError(("There is not matched criteria for this land use: {}").format(rec["US_EDAFO"]))
    else:
        for n,r in ks_records.iterrows():
            if r["Tipo"].strip() == patt.strip():
                gps_file.loc[i] = [i, rec["US_EDAFO"], patt, r['k']]
                break

merged_left = pd.merge(left=records, right=gps_file, how='left', left_on='ID', right_on='ID')
merged_left.pop('ID')
merged_left.pop('US_EDAFO_y')

merged_left.columns = merged_left.columns.str.replace('_x', '')


merged_left.to_csv(statis_path + os.sep + 'k_values.csv', encoding='utf-8',index=False)
arcpy.AddMessage("Evaluated")
arcpy.AddMessage("Work Done")