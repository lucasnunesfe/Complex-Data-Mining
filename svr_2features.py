import pandas as pd

train_data = pd.read_csv('./train.csv')
test_data = pd.read_csv('./test.csv')
train_data.groupby(['City']).size()

print(train_data.shape)
print(test_data.shape)

"""## Missing Values"""

any(train_data.isna())

#function for identfying which columns have missing values
def identify_nan(dataframe):

    result = {}

    for i in dataframe.columns.to_list():

        result.update({i: dataframe[i].isnull().values.any()})

    return result

identify_columns_nan = identify_nan(train_data)
print(identify_columns_nan)

#which columns have at least one missing value
identify_output_nan = {}

for key, value in identify_columns_nan.items():
    
    if (value == True):

        identify_output_nan[key] = value

print(identify_output_nan)

is_NaN = train_data.isnull()
row_has_NaN = is_NaN.any(axis=1)
rows_with_NaN = train_data[row_has_NaN]
print(rows_with_NaN.shape) #how many rows with at least 1 NaN value

"""##Data Types"""

print(train_data.dtypes)

"""# Feature Engineering"""

import haversine

df = pd.DataFrame()
dataset = train_data

df['City'] = dataset['City']
df['Latitude'] = dataset['Latitude']
df['Longitude'] = dataset['Longitude']
df['Weekend'] = dataset.apply(lambda x: 1-x['Weekend'], axis=1) #negative correlation
df.head()

df_test = pd.DataFrame()
dataset_test = test_data
df_test['City'] = dataset_test['City']
df_test['Latitude'] = dataset_test['Latitude']
df_test['Longitude'] = dataset_test['Longitude']
df_test['Weekend'] = dataset_test.apply(lambda x: 1-x['Weekend'], axis=1) #negative correlation
df_test.head()

"""##Rush Hour"""

def rush_hour(X):
    hour = X['Hour']
    if (hour >= 8 and hour < 10) or (hour >= 18 and hour < 20):
        return 1
    else:
        return -1

df['RushHour'] = dataset.apply(rush_hour, axis=1)
df_test['RushHour'] = dataset_test.apply(rush_hour, axis=1)

"""##Hour of the Day"""

def group_hour(X):
  hour = X['Hour']
  if hour > 4 and hour <= 8:
    return 'early morning'
  elif hour < 10:
    return 'morning rush'
  elif hour < 12:
    return 'late morning'
  elif hour < 18:
    return 'afternoon'
  elif hour < 20:
    return 'night rush'
  elif hour < 23:
    return 'night'
  else:
    return 'late night'

from sklearn.preprocessing import OneHotEncoder
hourGrouped = dataset.apply(group_hour, axis=1)
hourOHE = OneHotEncoder().fit_transform(hourGrouped.values.reshape(-1, 1))

df = pd.concat([df, pd.DataFrame(hourOHE.toarray()
                                , index=df.index
                                , columns=['HourOHE1', 'HourOHE2', 'HourOHE3', 'HourOHE4', 'HourOHE5', 'HourOHE6', 'HourOHE7'])], axis=1)
del(hourGrouped)
del(hourOHE)

df.head()

hourGrouped = dataset_test.apply(group_hour, axis=1)
hourOHE = OneHotEncoder().fit_transform(hourGrouped.values.reshape(-1, 1))
df_test = pd.concat([df_test, pd.DataFrame(hourOHE.toarray()
                                , index=df_test.index
                                , columns=['HourOHE1', 'HourOHE2', 'HourOHE3', 'HourOHE4', 'HourOHE5', 'HourOHE6', 'HourOHE7'])], axis=1)
del(hourGrouped)
del(hourOHE)

def normalize_coordinate(coord): # truncamos a coordenada para evitar overfitting
    return int(coord*1000)  

def heading_vector(heading):
    (V, H) = (0, 0)
    if 'N' in heading:
        V = 1
    if 'S' in heading:
        V = -1
    if 'W' in heading:
        H = -1
    if 'E' in heading:
        H = 1
    return (V, H)

def heading_direction(X):
    lt, lg, heading = normalize_coordinate(X['Latitude']), normalize_coordinate(X['Longitude']), X['ExitHeading']
    ltv, lgv = heading_vector(heading)
    return (ltv, lgv)

df['HeadingX'] = dataset.apply(lambda x: heading_direction(x)[0], axis=1)
df['HeadingY'] = dataset.apply(lambda x: heading_direction(x)[1], axis=1)
df.head()

df_test['HeadingX'] = dataset_test.apply(lambda x: heading_direction(x)[0], axis=1)
df_test['HeadingY'] = dataset_test.apply(lambda x: heading_direction(x)[1], axis=1)
df_test.head()

def curve_abs(X):
  entry, exit = X['EntryHeading'], X['ExitHeading']
  (x_in, y_in) = heading_vector(entry)
  (x_out, y_out) = heading_vector(exit)

  return abs(x_out - x_in) + abs(y_out-y_in)

import numpy as np
df['Curvature'] =  np.asarray(train_data.apply(curve_abs, axis=1)).astype('int')

df_test['Curvature'] =  np.asarray(test_data.apply(curve_abs, axis=1)).astype('int')

from haversine import haversine

cityCenterLocation ={'Atlanta':[33.753746, -84.386330], 
                      'Boston':[42.361145, -71.057083], 
                      'Chicago':[41.881832, -87.623177], 
                      'Philadelphia':[39.952583, -75.165222]}
def getDistancePoint(X):
  city, latPoint, lonPoint = X['City'], X['Latitude'], X['Longitude']
  latCity, lonCity = cityCenterLocation[city]

  return haversine((latCity, lonCity), (latPoint, lonPoint))

df['Dist_Downtown'] = dataset.apply(getDistancePoint, axis=1)

df_test['Dist_Downtown'] = dataset_test.apply(getDistancePoint, axis=1)

def to_downtown(X): # 0, 1 ou 2, dependendo se se aproxima do centro em 0, 1 ou 2 direcoes
  city, latPoint, lonPoint = X['City'], X['Latitude'], X['Longitude']
  cityCenterLocation ={'Atlanta':[33.753746, -84.386330], 
                      'Boston':[42.361145, -71.057083], 
                      'Chicago':[41.881832, -87.623177], 
                      'Philadelphia':[39.952583, -75.165222]}

  latCity, lonCity = cityCenterLocation[city]
  epsilon = 0.0001
  dx, dy = np.array(heading_vector(X['ExitHeading'])) * epsilon

  score = 0

  if abs(latPoint+dx - latCity) < abs(latPoint - latCity):
      score += 1 # aproxima latitude

  if abs(lonPoint+dy - lonCity) < abs(lonPoint - lonCity):
      score += 1 # aproxima longitude

  return score

df['ToDowntown']=dataset.apply(to_downtown, axis=1)

df_test['ToDowntown']=dataset_test.apply(to_downtown, axis=1)

city_month = dataset["City"].astype(str) + dataset["Month"].astype(str)
city_month = dataset_test["City"].astype(str) + dataset_test["Month"].astype(str)

monthly_temp = {'Atlanta1': 43, 'Atlanta5': 69, 'Atlanta6': 76, 'Atlanta7': 79, 'Atlanta8': 78, 
                'Atlanta9': 73, 'Atlanta10': 62, 'Atlanta11': 53, 'Atlanta12': 45, 'Boston1': 30, 
                'Boston5': 59, 'Boston6': 68, 'Boston7': 74, 'Boston8': 73, 'Boston9': 66, 
                'Boston10': 55,'Boston11': 45, 'Boston12': 35, 'Chicago1': 27, 'Chicago5': 60, 
                'Chicago6': 70, 'Chicago7': 76, 'Chicago8': 76, 'Chicago9': 68, 
                'Chicago10': 56,  'Chicago11': 45, 'Chicago12': 32, 'Philadelphia1': 35, 
                'Philadelphia5': 66, 'Philadelphia6': 76, 'Philadelphia7': 81, 
                'Philadelphia8': 79, 'Philadelphia9': 72, 'Philadelphia10': 60, 
                'Philadelphia11': 49, 'Philadelphia12': 40}

df['TempAvg'] = city_month.map(monthly_temp)
df_test['TempAvg'] = city_month.map(monthly_temp)

monthly_rainfall = {'Atlanta1': 5.02, 'Atlanta5': 3.95, 'Atlanta6': 3.63, 'Atlanta7': 5.12, 
                    'Atlanta8': 3.67, 'Atlanta9': 4.09, 'Atlanta10': 3.11, 'Atlanta11': 4.10, 
                    'Atlanta12': 3.82, 'Boston1': 3.92, 'Boston5': 3.24, 'Boston6': 3.22, 
                    'Boston7': 3.06, 'Boston8': 3.37, 'Boston9': 3.47, 'Boston10': 3.79, 
                    'Boston11': 3.98, 'Boston12': 3.73, 'Chicago1': 1.75, 'Chicago5': 3.38, 
                    'Chicago6': 3.63, 'Chicago7': 3.51, 'Chicago8': 4.62, 'Chicago9': 3.27, 
                    'Chicago10': 2.71,  'Chicago11': 3.01, 'Chicago12': 2.43, 
                    'Philadelphia1': 3.52, 'Philadelphia5': 3.88, 'Philadelphia6': 3.29,
                    'Philadelphia7': 4.39, 'Philadelphia8': 3.82, 'Philadelphia9':3.88 , 
                    'Philadelphia10': 2.75, 'Philadelphia11': 3.16, 'Philadelphia12': 3.31}

df['RainAvg'] = city_month.map(monthly_rainfall)
df_test['RainAvg'] = city_month.map(monthly_rainfall)

"""##Data Preparation and Treating Data"""

def register_result(city, target, rmse, tag):
  
  (rmse_res, tag_res) = best_values.get((city, target), (99999, 'default'))
  if(rmse_res > rmse):
    best_values[(city, target)] = (rmse, tag)

def make_city_dict(df):
  train_data_dict = {
      "Atlanta": df[df["City"] == "Atlanta"],
      "Boston": df[df["City"] == "Boston"],
      "Chicago": df[df["City"] == "Chicago"],
      "Philadelphia": df[df["City"] == "Philadelphia"]
  }
  return train_data_dict

targets = ['TotalTimeStopped_p20',
           'TotalTimeStopped_p50',
           'TotalTimeStopped_p80',           
           'DistanceToFirstStop_p20',
           'DistanceToFirstStop_p50',
           'DistanceToFirstStop_p80']

pseudo_targets = ['TimeFromFirstStop_p20',
                  'TotalTimeStopped_p40',
                  'TotalTimeStopped_p60',
                  'DistanceToFirstStop_p40',
                  'DistanceToFirstStop_p60',
                  'TimeFromFirstStop_p40',
                  'TimeFromFirstStop_p50',
                  'TimeFromFirstStop_p60',
                  'TimeFromFirstStop_p80']

non_targets = ['City', 'Latitude', 'Longitude']

best_values = {}

for target in targets:
    df[target] = dataset[target]

def generate_features():    
  featuresSet = set(df.columns) - set(targets) 
  featuresSet = featuresSet - set(non_targets)
  featuresSet = featuresSet - set(pseudo_targets)

  features = list(featuresSet)
  return features

features = generate_features()

import matplotlib.pyplot as plt
import seaborn as sns 
targets_plot = targets

dfInteresse = pd.concat([df[features], df[targets_plot]], axis=1)

fig = plt.subplots(figsize=(20,20))
sns.heatmap(dfInteresse.corr(), vmax=1, square=True, annot=True, cmap='Blues')

from sklearn.preprocessing import LabelEncoder

encoder = LabelEncoder()

train_data['PathOHE'] = encoder.fit_transform(train_data['Path'])
train_data['ExitHeadingOHE']     = encoder.fit_transform(train_data['ExitHeading'])
train_data['EntryHeadingOHE']    = encoder.fit_transform(train_data['EntryHeading'])
train_data['CityOHE']            = encoder.fit_transform(train_data['City'])

test_data['PathOHE'] = encoder.fit_transform(test_data['Path'])
test_data['ExitHeadingOHE']     = encoder.fit_transform(test_data['ExitHeading'])
test_data['EntryHeadingOHE']    = encoder.fit_transform(test_data['EntryHeading'])
test_data['CityOHE']            = encoder.fit_transform(test_data['City'])

correlation = train_data.corr()

"""# Baseline"""

import matplotlib.pyplot as plt
import seaborn as sns 

fig = plt.subplots(figsize=(10,10))
sns.heatmap(correlation, vmax=1, square=True, annot=True, cmap='Blues')
features = ['Latitude', 'Longitude', 'EntryHeadingOHE', 'ExitHeadingOHE', 'CityOHE', 'Hour', 'Weekend', 'Month']
x = train_data[features]
y_time = train_data['TotalTimeStopped_p80']
y_dist = train_data['DistanceToFirstStop_p80']

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

(x_train, x_val, y_train, y_val) = train_test_split(x, y_time, test_size = .25)

regressor = LinearRegression()
regressor.fit(x_train, y_train)
predict = regressor.predict(x_val)
accuracy = regressor.score(x_val, y_val)

print('\n')
print('Baseline - Resultado Tempo')
print("MSE:\t\t", mean_squared_error(y_val, predict))
print("MAE:\t\t", mean_absolute_error(y_val, predict))
print("R2 score:\t",accuracy)

(x_train, x_val, y_train, y_val) = train_test_split(x, y_dist, test_size = .25)

regressor = LinearRegression()
regressor.fit(x_train, y_train)
predict = regressor.predict(x_val)
accuracy = regressor.score(x_val, y_val)

print('\n')
print('Baseline - Resultado Distancia')
print("MSE:\t\t", mean_squared_error(y_val, predict))
print("MAE:\t\t", mean_absolute_error(y_val, predict))
print("R2 score:\t",accuracy)

"""# Modelos

## SVR
"""

import numpy as np

print(dfInteresse.columns)

"""###Reduce Complexity

####Features Selection
"""

dfAtlanta = df[df['City'] == 'Atlanta'].drop('City', axis = 1)
dfBoston = df[df['City'] == 'Boston'].drop('City', axis = 1)
dfChicago = df[df['City'] == 'Chicago'].drop('City', axis = 1)
dfPhiladelphia = df[df['City'] == 'Philadelphia'].drop('City', axis = 1)

cities_list = [[dfAtlanta, 'Atlanta'],
               [dfBoston, 'Boston'],
               [dfChicago, 'Chicago'],
               [dfPhiladelphia ,'Philadelphia']
              ]

from sklearn.feature_selection import SelectKBest, chi2, f_regression

"""###Hyperparameteres Selection"""

import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR

kernel_types = ['rbf']#,'linear', 'sigmoid']

C_range = np.logspace(-2, 10, 2, base=2)
gamma_range = np.logspace(-9, 3, 2, base=2)
epsilon_range = np.logspace(-2, 10, 2, base=2)

k_features = 2 #number of features

dfParametersToPredict = pd.DataFrame(columns=['City','Target','Feature1', 'Feature2','GS_BestParameters', 'x_fit_dataset', 'y_fit_dataset', 'model_fit'])

dictMapeamento = {}

count = 0

for t in targets:

  print(t,'\n')

  for city,ref in cities_list:

    exclude_list = list(set(city[targets].columns.to_list()) - set([t])) 

    dfAlvo = city.drop(exclude_list, axis=1)

    # Create and fit selector
    selector = SelectKBest(score_func=f_regression, k=k_features)
    selector.fit(dfAlvo.drop([t], axis = 1), dfAlvo[[t]])
    # Get columns to keep and create new dataframe with those only
    cols = selector.get_support(indices=True)

    features_df_new = dfAlvo.iloc[:,cols]
    featuresSvr = list(features_df_new.columns)
    dfFinalissimoSeriao=pd.concat([features_df_new, dfAlvo[[t]]], axis=1)

    train_summarized = dfFinalissimoSeriao.groupby(featuresSvr, as_index=False)\
                                            .agg({t:[np.mean]})

    print('\t',ref,'\n\t','#Entries:',len(train_summarized),'\n\t','Best',k_features,'Features:',featuresSvr,'\n')

    param_dist = dict(C = C_range, epsilon = epsilon_range, gamma = gamma_range)

    for kernel in kernel_types:
        grid = GridSearchCV(estimator = SVR(kernel = kernel),
                                    param_grid = param_dist,
                                    cv = 3,
                                    n_jobs = -1,
                                    scoring = 'neg_mean_absolute_error')

        grid.fit(train_summarized[featuresSvr], train_summarized[[t]].values.ravel())

        print('\n\t Kernel {} | Parametros: {} | Score: {}'.format(kernel, grid.best_params_, grid.best_score_))

        sv = grid.best_estimator_
        model_fit_variable = sv.fit(train_summarized[featuresSvr], train_summarized[[t]].values.ravel())
        
    dictMapeamento[(ref,t)] = count

    count += 1

    listParameters = [ref, 
                      t, 
                      featuresSvr[0], 
                      featuresSvr[1], 
                      grid.best_params_, 
                      train_summarized[featuresSvr], 
                      train_summarized[[t]].values.ravel(),
                      model_fit_variable]

    dfParametersToPredict.loc[len(dfParametersToPredict)] = listParameters

    print('\n\n')

print('\n')
print(dictMapeamento)
print('\n')

"""##Prediction"""

print(dfParametersToPredict)

firstId = 0

import csv

with open('output.csv', 'w', newline = '') as file:

    writer = csv.writer(file)

    writer.writerow(['TargetId','Target'])

    for index, row in df_test[:1920335].iterrows():

        secondId = 0

        for i in targets:

          city = row['City']

          first_parameter = dfParametersToPredict.loc[(dfParametersToPredict['City'] == city) &
                                                         (dfParametersToPredict['Target'] == i), 'Feature1']

          second_parameter = dfParametersToPredict.loc[(dfParametersToPredict['City'] == city) &
                                                        (dfParametersToPredict['Target'] == i), 'Feature2']

          feature1, feature2 = (row[first_parameter].values, row[second_parameter].values)

          iteration_bestEstimator = dfParametersToPredict.loc[(dfParametersToPredict['City'] == city) &
                                                              (dfParametersToPredict['Target'] == i), :]['GS_BestParameters']

          sv = SVR(iteration_bestEstimator)

          model_fit = dfParametersToPredict.loc[(dfParametersToPredict['City'] == city) &
                                                         (dfParametersToPredict['Target'] == i), :]['model_fit'][dictMapeamento[(city,i)]]

          y_pred = model_fit.predict(pd.concat([row[first_parameter].to_frame().T,row[second_parameter].to_frame().T], axis = 1))
          #print(y_pred)

          writer.writerow(['{}_{}'.format(firstId,secondId),'{}'.format(float(y_pred))])

          print('{}_{},{}'.format(firstId,secondId,float(y_pred)))

          secondId = secondId + 1

        firstId = firstId + 1