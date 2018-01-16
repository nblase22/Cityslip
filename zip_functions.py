# Dependencies
import requests as req
import json
import zipcodes
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import http.client
from datetime import datetime
import time as time
import csv

# Use the google API to get a list of points of interest
def barfinder(lat, lng):
    # Google API Key
    gkey = ""

    # types of points of interest we care about
    target_types = ["liquor_store", "gym", "park", "shopping_mall", "grocery_or_supermarket", "movie_theater"]
    
    #create a blank dictionary to store results
    results = {}
    
    # loop through each target type and gather the number of each nearby
    for target in target_types:
        
        # set default values
        count = 0
        x = True
        
        # while loop that uses google radar to gather our numbers
        while x == True:
            
            # take in latitude and longitude, set the search radius to 5 miles (8k meters)
            target_area = {"lat": lat, "lng": lng}
            target_radius = 8000

            # create the target urls and use requests to gather the necessary data
            target_url = "https://maps.googleapis.com/maps/api/place/radarsearch/json" \
                "?types=%s&location=%s,%s&radius=%s&key=%s" % (
                    target, target_area["lat"], target_area["lng"], target_radius,
                    gkey)

            places_data = req.get(target_url).json()

            # use the len function to find the count of results
            numbers = len(places_data["results"])

            # use a series of if statments to check if we returned results. Run a second time if no results showed up as a check
            if numbers > 0:
                results[target.replace("_", " ").title()] = numbers
                x = False
            elif count == 1:
                x = False
            else:
                count += 1
    
    # return the results
    return results

#---------------------------------------------------------------#
# pie plot of all of the points of interest as percentage of points of interest
def pie_plot(rst, target_zip):
    # create a dataframe
    pie_df = pd.DataFrame.from_dict(rst, orient = 'index')

    # get the sum of points of interest
    tot_results = pie_df.sum()

    # turn the data frame into percentages
    pie_df = (pie_df/tot_results)*100

    # make the graph labels
    labels = pie_df.index

    fig = plt.figure(figsize = [10,10])
    plt.pie(pie_df, shadow=True, startangle=140, labels = labels, labeldistance=1.028, autopct="%1.1f%%", pctdistance = .65, textprops = {"fontsize": 12})

    plt.axis("equal")
    plt.title("Pct of Points of Interest w/in 5 Miles of %s" % target_zip)
    plt.savefig("Points_of_Interest_PieChart.png", bbox_inches='tight')
    plt.show()


#---------------------------------------------------------------#

# Function requires a latitude and longitude value
# Call this function to generate census population data for 2010 - 2016
def cen_block_query(lat,lng):
    # Queries Census for county/State associated to Lat/Long
    # API Info (No Key Required):  https://www.fcc.gov/general/census-block-conversions-api
    cen_block_url = ('http://data.fcc.gov/api/block/find?format=json&latitude=%s&longitude=%s&showall=true' % (lat, lng))
    lat_lon_county = req.get(cen_block_url).json()
    county_name = lat_lon_county['County']['name']
    state_name = lat_lon_county['State']['name']
    county_census_pop = pd.read_csv('Resources/co-est2016-alldata.csv',\
                                encoding="ISO-8859-1").apply(lambda x: x.astype(str).str.lower())
    # Match County and State name to retrieve population information from 2010 through 2016
    for index, row in county_census_pop.iterrows():
        if str.lower(county_name) in row['CTYNAME'] and row['STNAME'] == str.lower(state_name):
            years = ['2010','2011','2012','2013','2014','2015','2016']
            pops = []
            pops.append(int(row['POPESTIMATE2010']))
            pops.append(int(row['POPESTIMATE2011']))
            pops.append(int(row['POPESTIMATE2012']))
            pops.append(int(row['POPESTIMATE2013']))
            pops.append(int(row['POPESTIMATE2014']))
            pops.append(int(row['POPESTIMATE2015']))
            pops.append(int(row['POPESTIMATE2016']))           
            pop_dict = {'Years': years, 'Population': pops}
            # Return a dataframe with population value for each year
            pop_est = pd.DataFrame(pop_dict)
        else:
            next    
    return pop_est, county_name, state_name

#---------------------------------------------------------------#
# call this function to present a line graph of population change
def census_plot(pop_est,county_name,state_name):
    pop_len = len(pop_est['Population'])
    _2010 = pop_est['Population'][1]
    _2016 = pop_est['Population'][pop_len -1]
    pop_growth = 0
    if _2010 < _2016:
        #
        diff_ = (round(((_2016 - _2010)/ _2016) * 100))
        pop_growth = ((_2016 - _2010)/ _2016)
        diff_str = "Note:\nIncrease of population by\n" + str(diff_) + "% from 2010 to 2016"
    elif _2010 > _2016:
        diff_ = (round(((_2010 - _2016)/ _2010) * 100))
        diff_str = "Note:\nDecrease of population by\n" + str(diff_) + "% from 2010 to 2016"
    else:
        diff_str = "Note:\nPopulation estimated as\nthe same from 2010 to 2016"
    ax = pop_est.plot(figsize = (8,6),color='blue', legend=False, marker = '*',markersize=15)
    ax.set_xticklabels(pop_est['Years'], fontsize=13, rotation=45)
    plt.grid()
    plt.figtext(0.91,0.45,diff_str,fontsize=12)
    plt.title("Census Population Estimates (%s County, %s)"%(county_name,state_name), fontsize = 14)
    plt.ylabel("Population", fontsize=14)
    plt.savefig("Population_Change_LineGraph.png", bbox_inches='tight')
    plt.show()
    return pop_growth

#---------------------------------------------------------------#
# Call this function to capture a DF that includes yearly changes in population
def population_df_generator(pop_est):
    pop_len = len(pop_est['Population'])
    pop_diff = [0]
    pop_diff_prcnt = [0]
    for x in range(pop_len-1):
        diff = (pop_est['Population'][x+1] - pop_est['Population'][x])
        pop_diff.append(diff)
        diff_prcnt = round(((diff/ pop_est['Population'][x]) * 100),2)
        pop_diff_prcnt.append(diff_prcnt)
    census_pop_master_df = pop_est
    census_pop_master_df['Difference'] = pop_diff
    census_pop_master_df['Percent Change'] = pop_diff_prcnt
    return census_pop_master_df

#---------------------------------------------------------------#

#get the min and max real estate info to use for comparison purposes later
#for now just return the median home value and median rental price
def get_real_estate_extremes():
    all_homes = pd.read_csv("Resources/Zip_Zhvi_AllHomes.csv")
    all_rental_homes = pd.read_csv("Resources/Zip_Zri_AllHomes.csv")
    
    #get min and max home values
    min_home_value = all_homes['2017-09'].min()
    max_home_value = all_homes['2017-09'].max()
    median_home_value = all_homes['2017-09'].median()
    min_rental_price = all_rental_homes['2017-09'].min()
    max_rental_price = all_rental_homes['2017-09'].max()
    median_rental_price = all_rental_homes['2017-09'].median()
    
    return median_home_value, median_rental_price
#get_real_estate_extremes()

#---------------------------------------------------------------#
# Find the nearest zipcode to a zipcode missing data
def find_near_zips(zipc, city, state):
    x = zipcodes.similar_to(zipc[0], 
                    zips=zipcodes.filter_by(zipcodes.list_all(), active=True, city= city, state = state))
    zipps = []
    for zips in x:
        zipps.append(zips['zip_code'])
    return zipps

#---------------------------------------------------------------#

# Function to store Zillow home values and monthly rental prices for 2013-2017 quarters
# Function requires a zip code string; returns data frame
# If there is no Zillow data for the zip code, find nearby zips and average their data

def get_home_data(zipc, city, state):
    zip_code = int(zipc)
    
    #create lists for the Zillow data 
    home_values=[]
    monthly_rentals=[]
    periods = []
    years=["2014","2015","2016","2017"]
    months=["03","06","09","12"]
    
    #read all home values and monthly rents
    all_homes = pd.read_csv("Resources/Zip_Zhvi_AllHomes.csv")
    all_rental_homes = pd.read_csv("Resources/Zip_Zri_AllHomes.csv")
    
    ## Zillow Home Value Index (ZHVI) is a time series tracking the monthly median home value
    # get the data just for the input zip code
    try:
        #get home values for input zip
        zc_all_homes = all_homes[all_homes["RegionName"] == zip_code].iloc[0]

        ## Zillow Rental Index (ZRI) is a time series tracking the monthly median rental
        zc_all_rental_homes = all_rental_homes[all_rental_homes["RegionName"] == zip_code].iloc[0]

        #get the home value and monthly rental data for the years/months specified above
        for y in years:
            for m in months:
                col_name = "%s-%s" % (y,m)

                try:
                    #get the data for this column name
                    home_value = zc_all_homes[col_name]
                    rent = zc_all_rental_homes[col_name]
                    home_values.append(home_value)
                    monthly_rentals.append(rent)
                    periods.append(col_name)
                    #print(col_name, home_value, rent)
                except:
                    #print("no value for: %s" % col_name)
                    continue
        found = 3
    except:    
        #find nearby zip codes because there are no rows for the input zip
        z = find_near_zips(zipc, city, state)
        #print(z)
        found = 3
        
        p = {}
        for q in z:
            q = int(q)
            try:
                zc_all_homes = all_homes[all_homes["RegionName"] == q].iloc[0]
                zc_all_rental_homes = all_rental_homes[all_rental_homes["RegionName"] == q].iloc[0]
                
                #get the home value and monthly rental data for the years/months specified above
                for y in years:
                    for m in months:
                        col_name = "%s-%s" % (y,m)
                        try:
                            #get the data for this column name
                            home_value = zc_all_homes[col_name]
                            rent = zc_all_rental_homes[col_name]
                            home_values.append(home_value)
                            monthly_rentals.append(rent)
                            periods.append(col_name)
                            #print(col_name, home_value, rent)
                        except:
                            continue
                            #print("no value for: %s" % col_name)
               
            except IndexError:
                next
        #if no data was found, store 0s
        if len(home_values) == 0 & len(monthly_rentals) == 0:
            periods.append(0)
            home_values.append(0)
            monthly_rentals.append(0)
            print("No Home Data Found")
            found = 0
        elif len(monthly_rentals) == 0:
            #monthly_rentals.append(0)
            print("No Rent Data Found")
            found = 1
            for i in range(0, len(home_values)):
            	monthly_rentals.append(0)
        elif len(home_values) == 0:     
            #home_values.append(0)
            print("No Home Value Data Found")
            found = 2
            for j in range(0, len(monthly_rentals)):
            	home_values.append(0)
                                            
    #store rent and house prices into a DF

    zillow_df=pd.DataFrame({"period": periods, 
                        "home_value": home_values,
                        "monthly_rent": monthly_rentals}) 
    
    
    df = zillow_df.groupby("period").mean()
   
    
    #store the most recent home value and rent for use in score
    home_value = df.iloc[-1]['home_value']
    rent = df.iloc[-1]['monthly_rent']
    
    return df, periods, home_value, rent, found

#---------------------------------------------------------------#

# Function to plot Zillow home values and monthly rental prices for 2014-2017 quarters
# Function requires a DF with the Zillow info and the zip code (string)
def plot_homes(df, zipc, periods, found):
    #only plot if there is data
    if (found == 1) | (found == 3):
        #plot the home values 
        x_ticks = periods
        x_axis = np.arange(1,16,1)
        y_axis = df['home_value']
        plt.xticks(x_axis, x_ticks, rotation='vertical')
        plt.legend
        plt.plot(x_axis, y_axis)
        plt.ylabel("Home Prices ($)")
        plt.title("%s Home Sales 2014-2017" % zipc)
        #save the plot
        plt.savefig("Home_Prices_LineGraph.png", bbox_inches='tight')
        plt.show()
    
    if found > 1:
        #plot the monthly rentals
        x_ticks = periods
        x_axis = np.arange(1,16,1)
        y_axis = df['monthly_rent']
        plt.xticks(x_axis, x_ticks, rotation='vertical')
        plt.legend
        plt.plot(x_axis, y_axis)
        plt.ylabel("Montly Rents ($)")
        plt.title("%s Monthly Rents 2014-2017" % zipc)
        plt.savefig("Rent_Prices_LineGraph.png", bbox_inches='tight')
        plt.show()


#---------------------------------------------------------------#
#Query Community API and return the results as JSON object 'resp'

#API URL: https://developer.onboard-apis.com/docs
#---------------------------------------------------------------#


def get_community_data(target_zip):

   #Onboard API Key
    onboard_api_key = ""

    conn = http.client.HTTPSConnection("search.onboard-apis.com")
    headers = {
        'accept': "application/json",
        # Reenter Onboard API Key
        'apikey': "",
        } 

    community_url = "/communityapi/v2.0.0/Area/Full/?"
    queries="AreaId=ZI"+target_zip
    query_url = community_url + queries
    conn.request("GET", query_url, headers=headers) 
    res = conn.getresponse()
    resp = json.loads(res.read())
    return resp
#---------------------------------------------------------------#
# Extract age demographics from the 'resp' JSON object
# Provides a pie chart
#---------------------------------------------------------------#

def age_demographics_zip(resp, target_zip):
    resp_keys = list(resp['response'].keys())
    if 'result' not in resp_keys: #check if there is data in 'resp' 
        result = 2       
        print('No results to graph. This zip code may not be valid.')

    else: # If there are results in the 'resp' 
        age_columns = ['age00_04','age05_09','age10_14','age15_19','age20_24','age25_29','age30_34','age35_39','age40_44',
                    'age45_49','age50_54','age55_59','age60_64','age65_69','age70_74','age75_79','age80_84','agegt85']
        labels = []
        age_groups = []
        age_group_values = []
        county_name = resp['response']['result']['package']['item'][0]['countyname']
        for x in age_columns:
            group_name = x
            age_groups.append(x)
            route = resp['response']['result']['package']['item'][0][x]
            age_group_values.append(int(route))
            label = x.replace('age','').replace('_','-').replace('gt85',' >=85') #format labels
            labels.append(label)

        # Create DF with summarized age groups
        age_by_zip = {"Groups": age_groups, "Count": age_group_values}
        age_by_zip_df = pd.DataFrame(age_by_zip)
        _0_09 = age_by_zip_df[0:2]['Count'].sum()
        _10_19 = age_by_zip_df[2:4]['Count'].sum()
        _20_29 = age_by_zip_df[4:6]['Count'].sum()
        _30_39 = age_by_zip_df[6:8]['Count'].sum()
        _40_49 = age_by_zip_df[8:10]['Count'].sum()
        _50_59 = age_by_zip_df[10:12]['Count'].sum()
        _60_69 = age_by_zip_df[12:14]['Count'].sum()
        _70_plus = age_by_zip_df[14:18]['Count'].sum()
        grp_sum_lables = ['1-9','10-19','20-29','30-39','40-49','50-59','60-69','>= 70']
        grp_sums = [_0_09,_10_19,_20_29,_30_39,_40_49,_50_59,_60_69,_70_plus]
        grp_dict = {'Groups':grp_sum_lables,'Count':grp_sums}
        grouped_age_df = pd.DataFrame(grp_dict)
        # Determine max value amongst age groups and set this to explode in pie chart
        max_age = grouped_age_df['Count'].idxmax(axis=0, skipna=True)
        explode_params = [0,0,0,0,0,0,0,0,]
        explode_params[max_age] = 0.2
        # Plot pie chart 
        fig = plt.figure(figsize = [10,10])
        plt.pie(grouped_age_df['Count'], shadow=True, startangle=140,explode = explode_params,
                textprops={"fontsize": 12},labels = grouped_age_df['Groups'],autopct="%1.1f%%", pctdistance = .65)
        plt.title("Age Groups for zip code %s\nin %s" %(target_zip,county_name))
        plt.savefig("Age_Demographics_PieChart.png", bbox_inches='tight')
        plt.show()

        return county_name
#---------------------------------------------------------------#

#get_details(target_zip)  
def get_details(target_zip):
    
    resp = get_community_data(target_zip)
        
    #store the individual fields in a dictionary
    
    crime = resp['response']['result']['package']['item'][0]['crmcytotc']
    sales_tax= resp['response']['result']['package']['item'][0]['salestaxrate']
    avg_jan = resp['response']['result']['package']['item'][0]['tmpavejan']
    avg_jul = resp['response']['result']['package']['item'][0]['tmpavejul']

    print("Average Winter Temperature (F): %s" % avg_jan)
    print("Average Summer Temperature (F): %s" % avg_jul)
            
    return crime, sales_tax, avg_jan, avg_jul

#---------------------------------------------------------------#

# Function to store various information about a location, such as walkability score, market health index, schools
# Function requires a zip code string, latitude and longitude and the dictionary; returns the dictionary
def get_zip_factors (zipc, lat, lng, zip_factors_dict):
     
    
    #1) Market Health Index: 
    # This index indicates the current health of a given region’s housing market relative to other markets nationwide. 
    # It is calculated on a scale of 0 to 10, with 0 = the least healthy markets and 10 = the healthiest markets.
    market_health_index = pd.read_csv("Resources/MarketHealthIndex_Zip.csv",encoding="ISO-8859-1")
    
    try:
        zip_market_health = market_health_index[market_health_index["RegionName"] == int(zipc)].iloc[0]           
        zip_factors_dict["market_health"] = zip_market_health['MarketHealthIndex']  
    except:
        #no market health data for input zip code; store 0 as a N/A value
        zip_factors_dict["market_health"] = 0
    print("Market Health: %s" % zip_factors_dict['market_health'])
    
    #2) ##get walkability, transit and bike scores from Walk Score.
    # Input walkscore API Key
    walk_api_key = ""
    walk_url = "http://api.walkscore.com/score?format=json&"
    # Build query URL
    query_url = walk_url  + "&lat=" + str(lat) + "&lon=" + str(lng) + "&transit=1&bike=1" + "&wsapikey=" + walk_api_key
    walk_response = req.get(query_url).json()

    # Get the neighborhood data from the response
    walk_score = walk_response['walkscore']
    walk_description=walk_response['description']
    
    zip_factors_dict["walk_score"] = walk_score
    zip_factors_dict["walk_description"] = walk_description
    
    try:    
        bike_score = walk_response['bike']['score']
        bike_description = walk_response['bike']['description']
        zip_factors_dict["bike_score"] = bike_score
        zip_factors_dict["bike_description"] = bike_description
    except:
        print("no bike score")
        bike_score = 0
        bike_description = ""
    print("Walkability and Bikability Scores: %s: %s, %s: %s" % (walk_score, walk_description, bike_score, bike_description))

    #3) get community data and store in dictionary
    crime, salestax, avgtempJan, avgtempJul = get_details(zipc)
    zip_factors_dict["crime_risk"] = crime
    zip_factors_dict["sales_tax_rate"] = salestax
    zip_factors_dict["avg_temp_jan"] = avgtempJan
    zip_factors_dict["avg_temp_jul"] = avgtempJul
    
    #4) store the median RE data in the dictionary
    zip_factors_dict["median_home_value"], zip_factors_dict["median_rent"] = get_real_estate_extremes()
    
    #print("crime risk: %s" % crime)
    #print("sales tax rate: %s" % salestax)
    #print("avgJan %s" % avgtempJan)
    #print("avgJul %s" % avgtempJul)
    
    return zip_factors_dict

#---------------------------------------------------------------#

#Get school data from OnBoard
# Function requires latitude and longitude, radius in miles; returns counts
def get_school_data(lat, lng, radius):
    
    private = 0
    public = 0
    cath = 0
    other = 0
    
    page_size = 50

    #Onboard API Key
    onboard_api_key = ""

    conn = http.client.HTTPSConnection("search.onboard-apis.com") 
    school_url = "/propertyapi/v1.0.0/school/snapshot?"
    headers = { 
        'accept': "application/json", 
        # Reenter Onboard API Key
        'apikey': "", 
        } 

    point = "latitude=" + str(lat) + "&longitude=" + str(lng) + "&radius=" + str(radius)
    query_url = school_url + point + "&pageSize=" + str(page_size)
 
    #print(query_url)
    
    #request the first page of school data
    conn.request("GET", query_url, headers=headers) 

    res = conn.getresponse()
    resp = json.loads(res.read())
    resp
    
    #counts for types of schools
    private = 0
    public = 0
    cath = 0
    other = 0


    #loop through and count up private and public schools
    total_schools = resp['status']['total']   
    more_schools = True
    schools_to_get = total_schools
    page = 1

    #print("total schools: % s" % total_schools)
    while more_schools:
    
        #determine how many results to process
        if schools_to_get - page_size >= 0:
            max_s = page_size
            schools_to_get = schools_to_get - page_size
        else:
            max_s = schools_to_get 
        
        for i in range(0, max_s):        

            #track number of types of schools
            sch_type = resp['school'][i]['School']['Filetypetext']

            #print("Type: %s, Name: %s" % (sch_type, resp['school'][i]['School']['InstitutionName']))

            if sch_type == "PRIVATE":
                private = private + 1
            elif sch_type == "PUBLIC":
                public = public + 1
            elif sch_type == "CATHOLIC":
                cath = cath + 1
            else:
                other = other + 1
                
        if total_schools - (private+public+cath+other) > 0:
            #get the next page of data
            page = page + 1
            
            query_url = school_url + point + "&pageSize=" + str(page_size) + "&page="+ str(page)
            #print(query_url)
            conn.request("GET", query_url, headers=headers) 

            res = conn.getresponse()
            resp = json.loads(res.read())
            resp
        
        else:
            more_schools = False
    print("\nNumber of Schools")
    print("private: %s, public: %s, catholic: %s, other: %s" % (private, public, cath, other))
    return total_schools, private, public, cath

#---------------------------------------------------------------#

def plot_schools(priv, pub, cath, rad, target_zip):
    #make a bar graph of the schools 
    colors1=['red','blue','green']
    sch_x = ["Private", "Public", "Catholic"]
    sch_y = [priv, pub, cath]        
    x_axis = np.arange(len(sch_x))
    plt.bar(x_axis, sch_y, color=colors1,align="edge")
    tick_locations = [value+0.4 for value in x_axis]
    plt.xticks(tick_locations, sch_x)
    plt.xlim(-0.25, len(x_axis))
    plt.ylim(0, max(sch_y)+0.5)
    plt.title("Schools within %s Miles of %s" % (rad, target_zip))
    plt.xlabel("Type of School")
    plt.ylabel("Quantity")
    plt.savefig("Schools_BarGraph.png", bbox_inches='tight')
    plt.show()
        
#---------------------------------------------------------------#

#function to calculate the city score/zip slip!  Calculate 0-100 score
# inputs are in the zip_factors_dictionary:
#   most recent home values and monthly rent for zip code
#   most recent median home values and median monthly rent
#   comparison of most recent home value and monthly rent with medians for U.S.
#   RE market health (0-10)
#   population growth
#   age demographics
#   number of grocery stores
#   number of movie theaters
#   number of liquor stores
#   number of gyms
#   number of parks
#   number of shopping malls
#   walkability (0-100)
#   schools - use private to public ratio 
#   sales tax percent
#   crime risk (100 is median)
#   average temp in Jan
#   average temp in July
def compute_score(zip_factors):


    # compute ratios; closest to 1 is best
    # home and rent each have a max of 0.05
    
    

    #if no home value or rent data, set the scores to a median value but notify user
    if zip_factors['home_value'] == 0:
        RE_home = 0.025
        print("There is no Home Value Data.")
    else:
        home_value_ratio = zip_factors['home_value'] / zip_factors['median_home_value']
            
        #RE_value (home: 0.05; rent: 0.05)
        if home_value_ratio < 1.3:
            RE_home = 0.05
        elif home_value_ratio <= 1.8:
            RE_home = 0.03
        else:
            RE_home = 0.01
            
    if zip_factors['rent'] == 0:
        RE_rent = 0.025
        print("There is no Monthly Rental Data.")
    else:    
        rent_ratio = zip_factors['rent'] / zip_factors['median_rent']
        if rent_ratio < 1.3:
            RE_rent= 0.05
        elif rent_ratio <= 1.8:
            RE_rent = 0.03
        else:
            RE_rent = 0.01 
        
    #market health is 0.05
    MH = (zip_factors['market_health']/10) * .05


    # walkability is a percent -- worth 0.05
    WK = (zip_factors['walk_score']/100) * 0.05

    tax_rate = float(zip_factors['sales_tax_rate'])
    #tax - worth 0.05
    if tax_rate == 0:
        TX = 0.05
    elif tax_rate <= 3:
        TX = 0.04
    elif tax_rate <= 5:
        TX = 0.03
    elif tax_rate <= 6:  
        TX = 0.02
    elif tax_rate <= 7:
        TX = 0.01
    else:
        TX = 0

    #crime risk (100 is median); worth 0.15
    crime = float(zip_factors['crime_risk'])
    if crime < 100:
        CM = .15
    elif crime <= 150:
        CM = .1
    elif crime <= 200:
        CM = 0.05
    else:
        CM = 0

    #weather; worth .1 total
    avg_jan = float(zip_factors['avg_temp_jan'])
    if avg_jan < 20:
        WW = 0
    elif avg_jan < 30:
        WW = 0.01
    elif avg_jan < 40:
        WW = 0.03
    elif avg_jan < 50:
        WW = 0.04
    else:
        WW = 0.05
        
    avg_jul = float(zip_factors['avg_temp_jul'])
    if avg_jul > 100:
        WS = 0
    elif avg_jul > 90:
        WS = 0.01
    elif avg_jul >80:
        WS = 0.03
    elif avg_jul >70:
        WS = 0.05
    else:
        WS = 0.04


    #population growth: 0.10 total
    pop_growth = float(zip_factors['pop_growth'])
    if pop_growth < 0:
        PG = 0
    elif pop_growth >= 0.07:
        PG = 0.05
    else:
        PG = 0.1

    #POIs: total worth: .3 broken down as follows:
    points_of_interest = float(zip_factors['poi'])
    if points_of_interest < 400:
    	POI = .1
    elif points_of_interest < 800:
    	POI = .2
    else:
    	POI = .3

    #use ratio of private to public schools; 0.1 total
    if zip_factors['public_schools'] == 0:
        SCH = 0
    else:    
        SCH = ((zip_factors['private_schools'] + zip_factors['cath_schools']) / zip_factors['public_schools']) * 0.1
        #if ratio of private to public is over 1, then cap the SCH score
        if SCH > 0.1:
            SCH = 0.1
    
    
    #add up all the values to get the score:
    score = RE_home + RE_rent + MH + WK + TX + CM + WW + WS + PG + POI + SCH
    date = datetime.now().strftime("%m/%d/%y")
    city = zip_factors['city']
    zip_code = zip_factors['zip_code']
    state = zip_factors['state']
    county = zip_factors['county']

    # print the breakdown of total score
    print("Breakdown of Total Score for %s" % zip_code)
    print()
    print("Average Home Value: %s/5 | Average Rent: %s/5 | Real Estate Market Health: %s/5" % (round(RE_home*100, 2), round(RE_rent*100,2), round(MH*100,2)))
    print("Average Winter Temp (F): %s/5 | Average Summer Temp (F): %s/5" % (round(WW*100,2), round(WS*100,2)))
    print("Total Schools: %s/10 | Total Points of Interest: %s/30" % (round(SCH*100,2), round(POI*100,2)))
    print("Population Growth: %s/10" % round(PG*100, 2))
    print("Sales Tax Rate: %s/5" % round(TX*100,2))
    print("Walkability: %s/5" % round(WK*100,2))
    print("Crime Risk: %s/15" % round(CM*100,2))
    print()
    print("CitySlip Score (0-100): %s" % round(score * 100,2))

    # write the outputs of the score to a csv file
    f =  open('Output.csv', 'a', newline='')
    outwriter = csv.writer(f)
    outwriter.writerow([zip_code, city, county, state, date, round(RE_home*100, 2), round(RE_rent*100, 2), round(MH*100, 2), round(WW*100, 2), round(WS*100, 2), round(SCH*100, 2), round(POI*100, 2), round(PG*100, 2), round(TX*100, 2),round(WK*100, 2), round(CM*100, 2), round(score*100, 2)])
    f.close()
    return score