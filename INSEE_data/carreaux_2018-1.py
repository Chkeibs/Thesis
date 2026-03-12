
import os
import geopandas as gpd
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARREAUX_DIR = os.path.join(BASE_DIR, 'Carreaux')
RESULTATS_DIR = os.path.join(CARREAUX_DIR, 'resultats')

dvf_path = os.path.join(BASE_DIR, 'dvf752018.csv')
if not os.path.exists(dvf_path):
    dvf_path = os.path.join(BASE_DIR, 'New_DPE', 'dvf752018.csv')

# Import data transaction 75 2018 -> Dataframe dvf
dvf = pd.read_table(dvf_path, delimiter=',')
print(dvf)
print(dvf.shape)

# Dataframe -> GeoDataframe (EPSG:4326 = WGS84)
geodvf = gpd.GeoDataFrame(
    dvf, geometry=gpd.points_from_xy(dvf.longitude, dvf.latitude), crs="EPSG:4326"
)

print(geodvf.loc[[1]])

# Carreaux 200m Paris (polygones)
geocarreaux = gpd.read_file(os.path.join(RESULTATS_DIR, 'carreaux_paris.shp'))
print(geocarreaux.head())
print(geocarreaux.shape)

# Check original projection
geocarreaux.crs

# Reproject to Lambert93
geocarreaux93 = geocarreaux.to_crs("EPSG:2154")

# Reproject DVF to Lambert93
geodvf93 = geodvf.to_crs("EPSG:2154")

# Spatial Joint entre le fichier DVF 2018 et Carreaux Paris
join_left_dvf = geodvf93.sjoin(geocarreaux93, how="left")

# Donne la ligne 6000 du fichier joint_left_dvf (jointure)
print(join_left_dvf.loc[[6000]])

# Donne la ligne 1000 du fichier joint_left_dvf (jointure)
print(join_left_dvf.loc[[1000]])

print(join_left_dvf.info())

# Export to csv
join_left_dvf.to_csv(os.path.join(RESULTATS_DIR, 'dvf752018Carreaux.csv'))
