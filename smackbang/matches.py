import numpy as np
import pandas as pd
import requests
import os
from dotenv import load_dotenv, find_dotenv
from requests.structures import CaseInsensitiveDict

env_path = find_dotenv()
load_dotenv(env_path)
TEQUILA_API_KEY = os.getenv('TEQUILA_API_KEY')

def get_matches(origin_one, origin_two, departure_date, continent, return_date, currency):
    '''
    Required arguments: origin_one, origin_two and contintent
    Optional argugments: return_date
    Returns df  index=['cityTo'],
    columns=[origin_one,origin_two,origin_one_price,origin_two_price,combined_price
    '''
    # assigning url to be in used in get request
    url = "https://tequila-api.kiwi.com/v2/search"

    # create airports_df from csv
    airports_df = pd.read_csv('../data/airport_codes.csv')

    # creating origins variable to used in get request
    origins = f'{origin_one},{origin_two}'

    # creating fly_to variable to be used in get request
    destinations_ser = airports_df[airports_df['continent']==continent]['iata_code'].dropna()
    destinations_list = []
    for code in destinations_ser:
        destinations_list.append(code)
    if origin_one in destinations_list:
        destinations_list.remove(origin_one)
    if origin_two in destinations_list:
        destinations_list.remove(origin_two)
    fly_to = ','.join(destinations_list)

    # creating headers
    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["apikey"] = TEQUILA_API_KEY

    # creating query string to be used in get request
    query_string = {'fly_from':origins, 'fly_to':fly_to,
                'date_from':departure_date, 'date_to':departure_date,'return_from':return_date,'return_to':return_date,
               'adults':1, 'children':0,'selected_cabins':'M','adult_hold_bag':1,'adult_hand_bag':1,
               "curr":currency, 'limit':1000}

    # creating response d in json format
    d = requests.get(url, headers=headers, params=query_string).json()

    # creating dictionary with desired keys
    df = {'cityFrom':[], 'cityTo':[],'cityCodeFrom':[],'cityCodeTo':[], 'price':[], 'duration':[],
          'total_stops':[],'distance':[],'local_departure':[],'local_arrival':[], "deep_link":[]
    }

    # importing response d into df
    for i in range(0,len(d['data'])):
        for k,v in d['data'][i].items():
            if k == 'duration':
                df[k].append(round(v['total']/3600,2))
            elif k == 'id':
                df['total_stops'].append(len(v.split('|'))-1)
            else:
                if k in df:
                    df[k].append(v)

    # creating dataframe df from dictionary df
    df = pd.DataFrame(df)

    # creating new df column "route"
    df['route'] = df.cityCodeFrom + "-" + df.cityCodeTo

    # outputting the cheapest flight for each route and sort values by the common destination
    df = df.groupby('route').min().sort_values('cityTo')

    # creating pivot table to compare flights from origin_one and orign_two to common destination
    df = df.pivot(index='cityTo', columns='cityFrom', values=['price','duration','total_stops','distance','local_departure','local_arrival','deep_link'])

    # creating new column for combined price
    df['combined_price'] = df['price'].iloc[:,0] + df['price'].iloc[:,1]

    # creating new column for combined duration
    df['combined_duration'] = df['duration'].iloc[:,0] + df['duration'].iloc[:,1]

    # sorting df by combined price for the top common destinations by price
    df = df.sort_values(by='combined_price')

    #creating empty lat,long columns type float64
    df['lat'] = np.nan
    df['lon'] = np.nan

    # grabbing lat,lon from airports df
    for city in list(df.index):
        if city in list(airports_df['city']):
            df.loc[city,'lat']=list(airports_df[airports_df['city']==city]['lat'])[0]
            df.loc[city,'lon']=list(airports_df[airports_df['city']==city]['lon'])[0]

    # return top 20 common destinations by price
    return df.head(10).dropna()

if __name__ == "__main__":
    ## user input
    # origin_one = 'NRT'
    # origin_two = 'SYD'
    # depature_date = '01/04/2022'
    # return_date = ""
    # continent = "AS"
    # currency = "USD"

    matches_df = get_matches(origin_one='LHR', origin_two='CDG', departure_date='01/12/2022', continent='EU', return_date='', currency='USD')
    print(matches_df)

    #print(df)
    # running tests
    # print(df)
    # print(type(df))
    # print(df.shape)
    # print(df.columns)
    # print(df.index)
