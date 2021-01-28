import warnings                                  # `do not disturbe` mode
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

#Import data
df = pd.read_csv('FAOSTAT_downloaded20210119.csv')
foods = pd.read_csv('foods.csv')

df = df[(df['Area'] == 'BDI') & (df['Area'] == 'RWA') & (df['Area'] == 'UGA')]

#Bind old (-2013) and new time series (2014-): Food Balances and Producer prices
df.Domain.replace('Food Balances (old methodology and population)', 'FoodBalances', inplace=True)
df.Domain.replace('New Food Balances', 'FoodBalances', inplace=True)
df.Domain.replace('Producer Prices', 'ProducerPrices', inplace=True)
df.Domain.replace('Producer Prices (old series)', 'ProducerPrices', inplace=True)
df.Domain.replace('Food Supply - Crops Primary Equivalent', 'FoodSupply', inplace=True)
df.Domain.replace('Crops', 'CropProduction', inplace=True)
df.Domain.replace('Value of Agricultural Production', 'ValueAgProduction', inplace=True)
df.Element.replace('Food supply quantity (kg/capita/yr)', 'FoodPerCapita', inplace=True)
df.Element.replace('Producer Price Index (2014-2016 = 100)', 'PriceIndex', inplace=True)
df.Element.replace('Gross Production Value (constant 2014-2016 million US$)','GrossProductionValue', inplace=True)
df.Element.replace('Area harvested','AreaHarvested', inplace=True)

#merge with dictionary including "Food groups". Category 2 based on HDDS.
#if you want to filter out non-food, processed foods and beverages, select 'Crop' and 'CropProducts'
df = df.merge(foods, how='left', on='Item')

#select only 'crop' and 'cropProducts'
df = df[((df.Category1 == 'Crop') | (df.Category1 == 'CropProducts'))]
df = df[['Domain', 'Area', 'Element', 'Year', 'Unit', 'Value', 'name']]
df.rename(columns={'name':'Item'}, inplace=True)

#Calculate for LVB
#whyprice index does not work?
LVB = df.groupby(['Domain', 'Year', 'Element', 'Item']).sum()
LVB['Area'] = 'LVB'
LVB.reset_index(inplace=True)
df = pd.concat([LVB, df])

#change unit
df.Unit[(df.Element== 'Production')] = '1000 tones'
df.Unit[(df.Element== 'Food')] = '1000 tones'
df.Unit[(df.Element== 'FoodPerCapita')] = 'kg/capita/year'
df.Unit[(df.Element== 'PriceIndex')] = 'PriceIndex'
df.Unit[(df.Element== 'GrossProductionValue')] = 'million US$'
df.Unit[(df.Element== 'AreaHarvested')] = '1000 ha'

df.Element[(df.Domain == 'CropProduction') & (df.Element == 'Production')] = 'CropProduction'

####################
# Food Balance
df1 = df[(df.Domain == 'FoodBalances') &
         (df.Year >= 2014) & (df.Year <= 2016)]
a = df1[(df1.Element == 'Production') ].groupby(['Item', 'Area']).mean().reset_index()
a = a.rename(columns={'Value':'Production'})
b = df1[ (df1.Element == 'Food')].groupby(['Item', 'Area']).mean().reset_index()
b = b.rename(columns={'Value':'Food'})
d = df1[(df1.Element == 'Import Quantity')].groupby(['Item', 'Area']).mean().reset_index()
d = d.rename(columns={'Value':'Import'})
e = df1[(df1.Element == 'Export Quantity')].groupby(['Item', 'Area']).mean().reset_index()
e = e.rename(columns={'Value':'Export'})
f = df1[(df1.Element == 'Domestic supply quantity')].groupby(['Item', 'Area']).mean().reset_index()
f = f.rename(columns={'Value':'DomesticSupply'})
g = df1[(df1.Element == 'FoodPerCapita')].groupby(['Item', 'Area']).mean().reset_index()
g = g.rename(columns={'Value':'FoodPerCapita'})

#Producer Price Index
df3 = df[(df.Domain == 'ProducerPrices') &
         (df.Year >= 2014) & (df.Year <= 2016)] 
h = df3[(df3.Element == 'PriceIndex') ].groupby(['Item', 'Area']).mean().reset_index()
h = h.rename(columns = {'Value':'PriceIndex'})

#ValueAgProduction
df4 = df[(df.Domain == 'ValueAgProduction') & 
         (df.Year >= 2014) & (df.Year <= 2016)] 
i = df4[(df4.Element == 'GrossProductionValue') ].groupby(['Item', 'Area']).mean().reset_index()
i = i.rename(columns = {'Value':'GrossProductionValue'})

#CropProduction 
df5 = df[(df.Domain == 'CropProduction') &
         (df.Year >= 2014) & (df.Year <= 2016)] 
j = df5[(df5.Element == 'AreaHarvested') ].groupby(['Item', 'Area']).mean().reset_index()
j = j.rename(columns = {'Value':'AreaHarvested'})

#drop year
porVar = [a, b, g, h, i, j]
for cadaUno in porVar:
    cadaUno.drop('Year', axis=1, inplace=True)

#merge
df2 = a.merge(b, how='outer', on=['Item', 'Area'])
for cadaUno in porVar[2:]:
    df2 = df2.merge(cadaUno, how='outer', on=['Item', 'Area'])
    
#round
df2['FoodSelfSufficiency'] = df2.Production / df2.Food  *100
df2['AreaHarvested'] = (df2['AreaHarvested'] / 1000)
porInd = ['Production', 'Food', 'FoodPerCapita', 'PriceIndex', 
          'GrossProductionValue', 'AreaHarvested', 'FoodSelfSufficiency']
for cadaUno in porInd:
    df2[cadaUno] = df2[cadaUno].round(1)

########################################
#Function one
def potentialCompetitor (variable, country, number):
    a = df2[df2['Area'] == country].sort_values(variable, ascending=False).head(number)
    a.reset_index(inplace=True)
    a.drop('index', axis=1, inplace=True)         
    a.index += 1
    a.rename(columns={'Item':'TopCrops'}, inplace=True)

    return a

#Funtion Two
def graphCompetitors (variable, country, number):
    datos = df.rename(columns={'Item' : 'TopCrops'})
    datos = datos.sort_values('Year', ascending=True)
        
    topCrops = potentialCompetitor(variable, country, number)
    datos = datos.merge(topCrops['TopCrops'], how='right', on='TopCrops')
    
    datitos = datos[(datos.Element == variable)]
    
    fig = px.line(datitos,
                  x='Year', 
                  y = 'Value',
                  color='TopCrops', 
                  facet_col='Area',
                  facet_col_wrap=2,
                  title=variable, 
                  labels = {'Value': datitos.Unit.iloc[1]})

    fig.show()

