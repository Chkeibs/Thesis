import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
import statsmodels.api as sm
import statsmodels.formula.api as smf


# Premiere partie de la lecture : 2018 -------------------------------------------------------------------
# Lecture donnÃ©es DVF 2018 75

don2018_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2018/75/dvf201875_prepare.csv'
dvf752018 = pd.read_csv(don2018_path)

#don2018_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026//DVFGEO/DVFGEO2018/75/dvf201875_prepare.sas7bdat'
#dvf752018 = pd.read_sas(don2018_path)

dvf752018['id_mutation'] = dvf752018['id_mutation'].astype("string")   # 18/01/26
dvf752018['num_ordre'] = dvf752018['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752018['Quatier'] = dvf752018['section'].str[8:] # Modification 16/01/2026
dvf752018['Annnee'] = 2018

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752018Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',', header=0)

# Keep only specified columns
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]   # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752018Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',', header=0)

# Keep only specified columns
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]    # 18/01/2026

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752018Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',', header=0)

# Keep only specified columns
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]

# Rename distances to dist_m
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752018Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',', header=0)

# Keep only specified columns
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
# This replicates the SAS logic of removing duplicates based on id_mutation and num_ordre
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})

# Lecture donnÃ©es Centre de Paris
proj_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752018Centre.csv'
centre_Paris = pd.read_csv(proj_path, delimiter=',', dtype=str)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})

# Lecture des donnÃ©es sur le Crime
crimegps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752018Crime.csv'
crime = pd.read_csv(crimegps_path, delimiter=',', dtype=str)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26


crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())


# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752018Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026


# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752018Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2018


print (dvf752018.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # dist_centre : Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge dataframes on ['id_mutation', 'num_ordre']
joint2018 = dvf752018.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')                      

print(joint2018.dtypes)

# The commented SAS code for log transformations can be done as follows if needed:
# import numpy as np
# joint2018['Lsurface'] = np.log(joint2018['surface_reelle_bati'])
# joint2018['Lval'] = np.log(joint2018['valeur_fonciere'])
# joint2018['prix'] = joint2018['valeur_fonciere'] * joint2018['surface_reelle_bati'] / joint2018['surface_totale']
# joint2018['Lprix'] = np.log(joint2018['prix'])
# joint2018['LSurfaceTotale'] = np.log(joint2018['surface_totale'])


# Fin lecture 2018 ------------------------------------------------------------------------------------------------------------





# Lecture donnÃ©es DVF 2019 75 -------------------------------------------------------------------------------------------------

don2019_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2019/75/dvf201975_prepare.csv'
dvf752019 = pd.read_csv(don2019_path)

#don2019_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2019/75/dvf201975_prepare.sas7bdat'
#dvf752019 = pd.read_sas(don2019_path)

dvf752019['id_mutation'] = dvf752019['id_mutation'].astype("string")   # 18/01/26
dvf752019['num_ordre'] = dvf752019['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752019['Quatier'] = dvf752019['section'].str[8:] # Modification 16/01/2026
dvf752019['Annnee'] = 2019

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752019Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]   # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752019Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752019Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752019Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752019Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752019Crime.csv', delimiter=',', low_memory=False)


crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26


crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752019Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752019Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2019

print (dvf752019.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) #  dist_centre : Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2019 = dvf752019.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')     

print (joint2019.dtypes)

# Uncomment and adapt the following lines if needed for log transformations:
# joint2019['Lsurface'] = np.log(joint2019['surface_reelle_bati'])
# joint2019['Lval'] = np.log(joint2019['valeur_fonciere'])
# joint2019['prix'] = joint2019['valeur_fonciere'] * joint2019['surface_reelle_bati'] / joint2019['surface_totale']
# joint2019['Lprix'] = np.log(joint2019['prix'])
# joint2019['LSurfaceTotale'] = np.log(joint2019['surface_totale'])


# Fin traitement pour 2019 -------------------------------------------------------------------------------------------------









# Lecture donnÃ©es DVF 2020 75 -------------------------------------------------------------------------------------------------

don2020_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2020/75/dvf202075_prepare.csv'
dvf752020 = pd.read_csv(don2020_path)

#don2020_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2020/75/dvf202075_prepare.sas7bdat'
#dvf752020 = pd.read_sas(don2020_path)

dvf752020['id_mutation'] = dvf752020['id_mutation'].astype("string")   # 18/01/26
dvf752020['num_ordre'] = dvf752020['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752020['Quatier'] = dvf752020['section'].str[8:] # Modification 16/01/2026
dvf752020['Annnee'] = 2020

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752020Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]  # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752020Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]    # 18/01/26

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752020Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752020Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752020Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752020Crime.csv', delimiter=',', low_memory=False)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26

crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752020Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752020Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2020# Assuming dvf752020, gares, bruit, lycees, meilleurs are pandas DataFrames already loaded in the environment

print (dvf752020.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2020 = dvf752020.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')                          

# Uncomment and adapt the following lines if needed for log transformations:
# joint2020['Lsurface'] = np.log(joint2020['surface_reelle_bati'])
# joint2020['Lval'] = np.log(joint2020['valeur_fonciere'])
# joint2020['prix'] = joint2020['valeur_fonciere'] * joint2019['surface_reelle_bati'] / joint2019['surface_totale']
# joint2020['Lprix'] = np.log(joint2020['prix'])
# joint2020['LSurfaceTotale'] = np.log(joint2020['surface_totale'])


print (joint2020.dtypes)

# Fin traitement pour 2020 -------------------------------------------------------------------------------------------------





# Lecture donnÃ©es DVF 2021 75 -------------------------------------------------------------------------------------------------

don2021_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2021/75/dvf202175_prepare.csv'
dvf752021 = pd.read_csv(don2021_path)

#don2021_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2021/75/dvf202175_prepare.sas7bdat'
#dvf752021 = pd.read_sas(don2021_path)

dvf752021['id_mutation'] = dvf752021['id_mutation'].astype("string")   # 18/01/26
dvf752021['num_ordre'] = dvf752021['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752021['Quatier'] = dvf752021['section'].str[8:] # Modification 16/01/2026
dvf752021['Annnee'] = 2021

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752021Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]        # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752021Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]       # 18/01/26

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752021Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752021Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752021Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752021Crime.csv', delimiter=',', low_memory=False)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26


crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752021Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752021Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2021# Assuming dvf752021, gares, bruit, lycees, meilleurs are pandas DataFrames already loaded in the environment

print (dvf752021.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2021 = dvf752021.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')     

print (joint2021.dtypes)

# Uncomment and adapt the following lines if needed for log transformations:
# joint2021['Lsurface'] = np.log(joint2021['surface_reelle_bati'])
# joint2021['Lval'] = np.log(joint2021['valeur_fonciere'])
# joint2021['prix'] = joint2021['valeur_fonciere'] * joint2019['surface_reelle_bati'] / joint2019['surface_totale']
# joint2021['Lprix'] = np.log(joint2021['prix'])
# joint2021['LSurfaceTotale'] = np.log(joint2019['surface_totale'])


# Fin traitement pour 2021 -------------------------------------------------------------------------------------------------



# Lecture donnÃ©es DVF 2022 75 -------------------------------------------------------------------------------------------------

don2022_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2022/75/dvf202275_prepare.csv'
dvf752022 = pd.read_csv(don2022_path)

#don2022_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2022/75/dvf202275_prepare.sas7bdat'
#dvf752022 = pd.read_sas(don2022_path)

dvf752022['id_mutation'] = dvf752022['id_mutation'].astype("string")   # 18/01/26
dvf752022['num_ordre'] = dvf752022['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752022['Quatier'] = dvf752022['section'].str[8:] # Modification 16/01/2026
dvf752022['Annnee'] = 2022

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752022Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]                 # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752022Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]     # 18/01/26

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752022Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752022Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752022Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752022Crime.csv', delimiter=',', low_memory=False)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26

crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752022Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752022Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2022

print (dvf752022.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2022 = dvf752022.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')     

print (joint2022.dtypes)

# Uncomment and adapt the following lines if needed for log transformations:
# joint2022['Lsurface'] = np.log(joint2022['surface_reelle_bati'])
# joint2022['Lval'] = np.log(joint2022['valeur_fonciere'])
# joint2022['prix'] = joint2022['valeur_fonciere'] * joint2019['surface_reelle_bati'] / joint2019['surface_totale']
# joint2022['Lprix'] = np.log(joint2022['prix'])
# joint2022['LSurfaceTotale'] = np.log(joint2019['surface_totale'])


# Fin traitement pour 2022 -------------------------------------------------------------------------------------------------



# Lecture donnÃ©es DVF 2023 75 -------------------------------------------------------------------------------------------------

don2023_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2023/75/dvf202375_prepare.csv'
dvf752023 = pd.read_csv(don2023_path)

#don2023_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2023/75/dvf202375_prepare.sas7bdat'
#dvf752023 = pd.read_sas(don2023_path)

dvf752023['id_mutation'] = dvf752023['id_mutation'].astype("string")   # 18/01/26
dvf752023['num_ordre'] = dvf752023['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752023['Quatier'] = dvf752023['section'].str[8:] # Modification 16/01/2026
dvf752023['Annnee'] = 2023

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752023Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]                   # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752023Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]     # 18/01/26

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752023Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752023Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752023Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752023Crime.csv', delimiter=',', low_memory=False)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26


crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752023Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752023Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2023

print (dvf752023.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2023 = dvf752023.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')     
                     
print (joint2023.dtypes)

# Uncomment and adapt the following lines if needed for log transformations:
# joint2023['Lsurface'] = np.log(joint2023['surface_reelle_bati'])
# joint2023['Lval'] = np.log(joint2023['valeur_fonciere'])
# joint2023['prix'] = joint2023['valeur_fonciere'] * joint2023['surface_reelle_bati'] / joint2019['surface_totale']
# joint2023['Lprix'] = np.log(joint2023['prix'])
# joint2023['LSurfaceTotale'] = np.log(joint2023['surface_totale'])


# Fin traitement pour 2023 -------------------------------------------------------------------------------------------------



# Lecture donnÃ©es DVF 2024 75 -------------------------------------------------------------------------------------------------

don2024_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2024/75/dvf202475_prepare.csv'
dvf752024 = pd.read_csv(don2024_path)

#don2024_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DVFGEO/DVFGEO2024/75/dvf202475_prepare.sas7bdat'
#dvf752024 = pd.read_sas(don2024_path)

dvf752024['id_mutation'] = dvf752024['id_mutation'].astype("string")   # 18/01/26
dvf752024['num_ordre'] = dvf752024['num_ordre'].astype(int)   # 18/01/26

# Recuperation du quartier
dvf752024['Quatier'] = dvf752024['section'].str[8:] # Modification 16/01/2026
dvf752024['Annnee'] = 2024

# Lecture donnÃ©es Bruit
bruitgps_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Bruit/dvf752024Bruit.csv'
bruit = pd.read_csv(bruitgps_path, delimiter=',')
bruit = bruit[['id_mutation', 'num_ordre', 'gridcode', 'Classe']]                 # 18/01/26

# Lecture donnÃ©es Gares
proj4_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Gares/dvf752024Gares.csv'
gares = pd.read_csv(proj4_path, delimiter=',')
gares = gares[['id_mutation', 'num_ordre', 'distances', 'Trafic', 'nb_correspondances']]          # 18/01/26

# Rename distances to dist_gare
gares = gares.rename(columns={'distances': 'dist_gare'})

# Lecture donnÃ©es Meilleurs Lycees
proj2_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Meilleurs/dvf752024Meilleurs.csv'
meilleurs = pd.read_csv(proj2_path, delimiter=',')
meilleurs = meilleurs[['id_mutation', 'num_ordre', 'distances']]
meilleurs = meilleurs.rename(columns={'distances': 'dist_m'})

# Lecture donnÃ©es Lycees
proj3_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Lycees/dvf752024Lycees.csv'
lycees = pd.read_csv(proj3_path, delimiter=',')
lycees = lycees[['id_mutation', 'num_ordre', 'distances']]

# Remove duplicates where transactions have multiple lycees at same distances
lycees = lycees.drop_duplicates(subset=['id_mutation', 'num_ordre'])

# Rename distances to dist_lycee
lycees = lycees.rename(columns={'distances': 'dist_lycee'})


# Lecture donnÃ©es Centre de Paris
centre_Paris = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Centre/dvf752024Centre.csv', delimiter=',', low_memory=False)

centre_Paris['num_ordre'] = pd.to_numeric(centre_Paris['num_ordre'],errors = 'coerce') # 18/01/26

# Keep only specific columns
centre_Paris = centre_Paris[['id_mutation', 'num_ordre', 'distances']]

# Rename column distances to dist_centre
centre_Paris = centre_Paris.rename(columns={'distances': 'dist_centre'})


# Lecture des donnÃ©es sur le Crime
crime = pd.read_csv(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Crime/dvf752024Crime.csv', delimiter=',', low_memory=False)

crime['num_ordre'] = pd.to_numeric(crime['num_ordre'],errors = 'coerce') # 18/01/26


crime['C135_158'] = crime['classe'] == "de 13,5 à 15,8"
crime['C158_186'] = crime['classe'] == "de 15,8 à 18,6"
crime['C186_226'] = crime['classe'] == "de 18,6 à 22,6"
crime['C116_135'] = crime['classe'] == "de 11,6 à 13,5"
crime['C100_116'] = crime['classe'] == "de 10,0 à 11,6"
crime['C84_100'] = crime['classe'] == "de 8,4 à 10,0"
crime['C68_84'] = crime['classe'] == "de 6,8 à 8,4"
crime['C51_68'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'].isna())
crime['C51_84'] = (crime['classe'] == "de 5,1 à 6,8") | (crime['classe'] == "de 6,8 à 8,4") | (crime['classe'].isna())

#crime['C135_158n'] = crime['classe'].str.slice(3, 7)

# Keep only required columns
crime = crime[['id_mutation', 'num_ordre', 'C135_158', 'C158_186', 'C186_226', 'C116_135', 'C100_116', 'C84_100', 'C68_84', 'C51_68', 'C51_84']]

# Lecture donnÃ©es Quartiers # Modification 16/01/2026
quartier_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Quartiers/dvf752024Quartier.csv' # Modification 16/01/2026
quartier = pd.read_csv(quartier_path, delimiter=',') # Modification 16/01/2026
quartier = quartier[['id_mutation', 'num_ordre', 'C_QU']] # Modification 16/01/2026
quartier = quartier.rename(columns={'C_QU': 'c_qu'}) # Modification 16/01/2026

# Lecture donnÃ©es Kebabs 27/02/26
kebabs_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Kebabs/dvf752024Kebabs.csv'
kebabs = pd.read_csv(kebabs_path, delimiter=',', header=0)

# Keep only specified columns
kebabs = kebabs[['id_mutation', 'num_ordre', 'distances']]  

# Rename distances to dist_kebabs
kebabs = kebabs.rename(columns={'distances': 'dist_kebabs'})


# Appariement des donnÃ©es pour le dÃ©partement 75 et l'annÃ©e 2024

print (dvf752024.dtypes)
print (gares.dtypes)
print (bruit.dtypes)
print (lycees.dtypes)
print (meilleurs.dtypes)
print (centre_Paris.dtypes) # Object
print (crime.dtypes)
print (quartier.dtypes)
print (kebabs.dtypes)

# Merge all datasets on ['id_mutation', 'num_ordre']
joint2024 = dvf752024.merge(gares, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(bruit, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(lycees, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(meilleurs, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(centre_Paris, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(crime, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(quartier, on=['id_mutation', 'num_ordre'], how='outer') \
                     .merge(kebabs, on=['id_mutation', 'num_ordre'], how='outer')     
                     
pd.set_option('display.max_rows',100)
print (joint2024.dtypes)

# Uncomment and adapt the following lines if needed for log transformations:
# joint2024['Lsurface'] = np.log(joint2024['surface_reelle_bati'])
# joint2024['Lval'] = np.log(joint2024['valeur_fonciere'])
# joint2024['prix'] = joint2024['valeur_fonciere'] * joint2024['surface_reelle_bati'] / joint2019['surface_totale']
# joint2024['Lprix'] = np.log(joint2024['prix'])
# joint2024['LSurfaceTotale'] = np.log(joint2024['surface_totale'])


# Fin traitement pour 2024 -------------------------------------------------------------------------------------------------





 
# Assuming joint2018, joint2019, ..., joint2024 are pandas DataFrames already loaded
 
# Combine datasets
joint2 = pd.concat([joint2018, joint2019, joint2020, joint2021, joint2022, joint2023, joint2024], ignore_index=True)
 
pd.set_option('display.max_rows',100)
print (joint2.dtypes)


# Create new columns based on conditions
joint2['g1'] = (joint2['gridcode'] == 1).astype(int)
joint2['g2'] = (joint2['gridcode'] == 2).astype(int)
joint2['g3'] = (joint2['gridcode'] == 3).astype(int)
joint2['g4'] = (joint2['gridcode'] == 4).astype(int)
joint2['g5'] = (joint2['gridcode'] == 5).astype(int)
joint2['g6'] = (joint2['gridcode'] == 6).astype(int)
joint2['g7'] = (joint2['gridcode'] == 7).astype(int)
joint2['g8'] = (joint2['gridcode'] == 8).astype(int)
joint2['g9'] = (joint2['gridcode'] == 9).astype(int)
joint2['g10'] = (joint2['gridcode'] == 10).astype(int)
joint2['g8p'] = (joint2['gridcode'] >= 8).astype(int)
joint2['g9p'] = (joint2['gridcode'] >= 9).astype(int)
 
joint2['nbp2'] = (joint2['nombre_pieces_principales'] == 2).astype(int)
joint2['nbp3'] = (joint2['nombre_pieces_principales'] == 3).astype(int)
joint2['nbp4'] = (joint2['nombre_pieces_principales'] == 4).astype(int)
joint2['nbp5'] = (joint2['nombre_pieces_principales'] >= 5).astype(int)
 
joint2['t0'] = (joint2['Trafic'] != -1).astype(int)                                      # 19/01/26
joint2['t1'] = joint2['Trafic'] * (joint2['Trafic'] != -1) / 1_000_000                   # 19/01/26
 
joint2['tnb_coresp1'] = ((joint2['nb_correspondances'] == 1) & (joint2['nb_correspondances'] != -1)).astype(int)
joint2['tnb_coresp2'] = ((joint2['nb_correspondances'] == 2) & (joint2['nb_correspondances'] != -1)).astype(int)
joint2['tnb_coresp3'] = ((joint2['nb_correspondances'] == 3) & (joint2['nb_correspondances'] != -1)).astype(int)
joint2['tnb_coresp4p'] = ((joint2['nb_correspondances'] >= 4) & (joint2['nb_correspondances'] != -1)).astype(int)
joint2['tnb_coresp4'] = ((joint2['nb_correspondances'] == 4) & (joint2['nb_correspondances'] != -1)).astype(int)
joint2['tnb_coresp5'] = ((joint2['nb_correspondances'] == 5) & (joint2['nb_correspondances'] != -1)).astype(int)
 
joint2["dist_centre"] = joint2.dist_centre.astype(float)       # 19/01/26


joint2['dist_lycee'] = joint2['dist_lycee'] / 10000
joint2['dist_centre'] = joint2['dist_centre'] / 10000
joint2['dist_m'] = joint2['dist_m'] / 10000
joint2['dist_gare'] = joint2['dist_gare'] / 10000
 
# Moyenne de surface par quartier (c_qu) et par année (Annnee) pour chaque transaction.         # Ajout 30/01/26
# Calculée sur toutes les ventes disponibles dans le même quartier et la même année
joint2['mean_surface_quartier'] = joint2.groupby(['Annnee', 'c_qu'])['surface_reelle_bati'].transform('mean')
 
# Moyenne de surface par quartier (c_qu) et par année (Annnee) pour chaque transaction.         # Ajout 12/02/26
# Calculée sur toutes les ventes disponibles dans le même quartier et la même année
joint2['mean_pieces_quartier'] = joint2.groupby(['Annnee', 'c_qu'])['nombre_pieces_principales'].transform('mean')
 
 
# stat des sur la surface pour chaque quatier 
stat_des_surface = joint2.groupby(['Annnee', 'code_postal', 'c_qu'])['surface_reelle_bati'].mean().reset_index() 


# stat des sur la prix pour chaque quatier 
stat_des_prix = joint2.groupby(['Annnee', 'code_postal', 'c_qu'])['prix'].mean().reset_index()  


# Frequency table for code_postal
code_postal_freq = joint2['code_postal'].value_counts()
print(code_postal_freq) 


# Filter for year 2018
fileaux = joint2[joint2['Annnee'] == 2018].copy()                         # 19/01/26
fileaux['prixm2'] = fileaux['prix'] / fileaux['surface_reelle_bati']
fileaux['dcenter'] = fileaux['dist_centre'] * 10000
fileaux['dlycee'] = fileaux['dist_lycee'] * 10000
fileaux['dmeilleur'] = fileaux['dist_m'] * 10000
fileaux['dgare'] = fileaux['dist_gare'] * 10000
fileaux['t1_ori'] = fileaux['t1'] * 1_000_000

 
# Summary statistics for prix and prixm2
prix_stats = fileaux[['prix', 'prixm2']].describe()
print(prix_stats) 

# Sort by code_postal
fileaux_sorted = fileaux.sort_values('code_postal')
 
# Summary statistics for prixm2 by code_postal
prixm2_by_code_postal = fileaux_sorted.groupby('code_postal')['prixm2'].describe()
print(prixm2_by_code_postal)
 
# Frequency table for nombre_pieces_principales
nb_pieces_freq = fileaux['nombre_pieces_principales'].value_counts()
print(nb_pieces_freq) 

# Summary statistics for distances
dist_stats = fileaux[['dcenter', 'dlycee', 'dmeilleur', 'dgare']].describe()
print(dist_stats) 

# Frequency table for t0
t0_freq = fileaux['t0'].value_counts()
print(t0_freq) 


# Summary statistics for t1_ori and tnb_coresp* where t0 == 1
fileaux_t0_1 = fileaux[fileaux['t0'] == 1]
t_stats = fileaux_t0_1[['t1_ori', 'tnb_coresp1', 'tnb_coresp2', 'tnb_coresp3', 'tnb_coresp4p']].describe()
print(t_stats) 

# Summary statistics for dcenter by code_postal
dcenter_by_code_postal = fileaux.groupby('code_postal')['dcenter'].describe()
print(dcenter_by_code_postal)
 
# Frequency tables for bruit and gares datasets (assuming they are pandas DataFrames)
bruit_gridcode_freq = bruit['gridcode'].value_counts()
print(bruit_gridcode_freq)
gares_nb_corresp_freq = gares['nb_correspondances'].value_counts()             # 19/01/26
print(gares_nb_corresp_freq)




 



# Frequency table for code_postal
freq_code_postal = joint2['code_postal'].value_counts()
print(freq_code_postal)


# Transform type for some variables to be saved in a Stata data file
 
joint2['nature_mutation'] = joint2['nature_mutation'].astype("string")   # 19/01/26
joint2['adresse_suffixe'] = joint2['adresse_suffixe'].astype("string")   # 19/01/26
joint2['adresse_nom_voie'] = joint2['adresse_nom_voie'].astype("string")   # 19/01/26
joint2['adresse_code_voie'] = joint2['adresse_code_voie'].astype("string")   # 19/01/26
joint2['nom_commune'] = joint2['nom_commune'].astype("string")   # 19/01/26
joint2['id_parcelle'] = joint2['id_parcelle'].astype("string")   # 19/01/26
joint2['lot1_numero'] = joint2['lot1_numero'].astype("string")   # 19/01/26
joint2['lot2_numero'] = joint2['lot2_numero'].astype("string")   # 19/01/26
joint2['lot3_numero'] = joint2['lot1_numero'].astype("string")   # 19/01/26
joint2['type_local'] = joint2['type_local'].astype("string")   # 19/01/26
joint2['code_nature_culture'] = joint2['code_nature_culture'].astype("string")   # 19/01/26
joint2['nature_culture'] = joint2['nature_culture'].astype("string")   # 19/01/26
joint2['section'] = joint2['section'].astype("string")   # 19/01/26
joint2['Quatier'] = joint2['Quatier'].astype("string")   # 19/01/26

joint2["nature_culture_speciale"] = joint2.nature_culture_speciale.astype(float)       # 19/01/26
joint2["code_nature_culture_speciale"] = joint2.code_nature_culture_speciale.astype(float)       # 19/01/26
joint2["ancien_code_commune"] = joint2.ancien_code_commune.astype(float)       # 19/01/26
joint2["ancien_nom_commune"] = joint2.ancien_nom_commune.astype(float)       # 19/01/26
joint2["ancien_id_parcelle"] = joint2.ancien_id_parcelle.astype(float)       # 19/01/26

#print (joint2.dtypes)


joint2["C51_68"] = joint2["C51_68"].astype(int)        # 20/01/26
joint2["C68_84"] = joint2["C68_84"].astype(int)
joint2["C84_100"] = joint2["C84_100"].astype(int)                       
joint2["C100_116"] = joint2["C100_116"].astype(int)    
joint2["C116_135"] = joint2["C116_135"].astype(int)  
joint2["C135_158"] = joint2["C135_158"].astype(int)  
joint2["C158_186"] = joint2["C158_186"].astype(int)  
joint2["C186_226"] = joint2["C186_226"].astype(int) 


# Export to Stata .dta file
joint2.to_stata(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/base_270226.dta', write_index=False)
 
# Create sortie_ascii DataFrame with selected columns
   
cols_to_keep = ['Lprix', 'nbp2', 'nbp3', 'nbp4', 'nbp5', 'surface_reelle_bati', 'Lsurface', 'dist_gare',
                'presence_dependance', 't0', 't1', 'tnb_coresp2', 'tnb_coresp3', 'tnb_coresp4p',
                'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9', 'g10', 'dist_lycee', 'dist_m',
                'dist_centre', 'gridcode', 'C51_68', 'C68_84', 'C84_100', 'C100_116', 'C116_135',
                'C135_158', 'C158_186', 'C186_226', 'Annnee', 'code_postal', 'c_qu',    #  ] # Modification 16/01/2026 # 19/01/26
                'mean_surface_quartier','mean_pieces_quartier','dist_kebabs'] # Ajout moyenne de surface par quartier. 30/01/26 et moyenne nombre de pièces le 12/02/26
              

 
sortie_ascii = joint2[cols_to_keep]
 
# Write sortie_ascii to a text file with space-separated values
output_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Simulations_Mars2026/don27022026.txt'
sortie_ascii.to_csv(output_path, sep=' ', index=False, header=False)


# Part adding variable related to DPE and filtering for observed DPE


dpe2018_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752018Dpe.csv'    # 20/01/26
dpe2018 = pd.read_csv(dpe2018_path)

dpe2019_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752019Dpe.csv'
dpe2019 = pd.read_csv(dpe2019_path)

dpe2020_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752020Dpe.csv'
dpe2020 = pd.read_csv(dpe2020_path)

dpe2021_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752021Dpe.csv'
dpe2021 = pd.read_csv(dpe2021_path)

dpe2022_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752022Dpe.csv'
dpe2022 = pd.read_csv(dpe2022_path)

dpe2023_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752023Dpe.csv'
dpe2023 = pd.read_csv(dpe2023_path)

dpe2024_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/DPEPourMatch/dvf752024Dpe.csv'
dpe2024 = pd.read_csv(dpe2024_path)

# Assuming ...
 
 
# Concatenate all years into one DataFrame
dpe = pd.concat([dpe2018, dpe2019, dpe2020, dpe2021, dpe2022, dpe2023, dpe2024], ignore_index=True)
 
# Sort dpe by id_mutation and num_ordre
dpe = dpe.sort_values(by=['id_mutation', 'num_ordre'])
 
# Assuming joint2 is already loaded as a DataFrame
# Merge joint2 and dpe on id_mutation and num_ordre
joint3 = pd.merge(joint2, dpe, on=['id_mutation', 'num_ordre'], how='outer')
 
# Create IDSel1 and IDSel2 as sums of specified columns
dpe_cols = ['DPE1','DPE2','DPE3','DPE4','DPE5','DPE6','DPE7']
dpe_old_cols = ['DPE1old','DPE2old','DPE3old','DPE4old','DPE5old','DPE6old','DPE7old']
 
joint3['IDSel1'] = joint3[dpe_cols].sum(axis=1)
joint3['IDSel2'] = joint3[dpe_old_cols].sum(axis=1)
 
# Frequency tables for DPE columns (similar to proc freq)
freqs = {}
for col in dpe_cols + dpe_old_cols:
    freqs[col] = joint3[col].value_counts(dropna=False)
 
# Filter rows where IDSel1 or IDSel2 is 1 or more (equivalent to SAS condition)
joint3 = joint3[(joint3['IDSel1'] >= 1) | (joint3['IDSel2'] >= 1)].copy()
 
# Drop IDSel1 and IDSel2 columns
joint3.drop(columns=['IDSel1', 'IDSel2'], inplace=True)
 
# Export joint3 to Stata .dta file
joint3.to_stata(r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/base2_270226.dta', write_index=False)
 

# Select columns for sortie_ascii
cols_to_keep = [
    'Lprix', 'nbp2', 'nbp3', 'nbp4', 'nbp5', 'surface_reelle_bati', 'Lsurface', 'dist_gare', 'presence_dependance',
    't0', 't1', 'tnb_coresp2', 'tnb_coresp3', 'tnb_coresp4p',
    'g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8', 'g9', 'g10',
    'dist_lycee', 'dist_m', 'dist_centre', 'gridcode',
    'C51_68', 'C68_84', 'C84_100', 'C100_116', 'C116_135', 'C135_158', 'C158_186', 'C186_226',
    'Annnee', 'code_postal', 'c_qu', # Modification 16/01/2026  20/01/26
    'DPE1', 'DPE2', 'DPE3', 'DPE4', 'DPE5', 'DPE6', 'DPE7',
    'DPE1old', 'DPE2old', 'DPE3old', 'DPE4old', 'DPE5old', 'DPE6old', 'DPE7old','mean_surface_quartier','mean_pieces_quartier','dist_kebabs'
]
 
sortie_ascii = joint3[cols_to_keep].copy()
 
# Write sortie_ascii to a text file with space-separated values
fileout_path = r'/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Simulations_DPE_Mars2026/don27022026DPE.txt'
sortie_ascii.to_csv(fileout_path, sep=' ', index=False, header=False)