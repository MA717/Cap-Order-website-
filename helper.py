

def mapCityToDistricts_DistrictToStreets(locations):
    cityToDistricts = {}
    DistrictToStreets = {}

    for location in locations:
        city = location[1]
        District = location[2]
        Street = location[3]
        if(city in cityToDistricts):
            if not( District in cityToDistricts[city] ): 
                cityToDistricts[city].append(District)
        else:
            cityToDistricts[city] = [District]
        
        if(District in DistrictToStreets):
            DistrictToStreets[District].append(Street)
        else:
            DistrictToStreets[District] = [Street]

    
    return cityToDistricts, DistrictToStreets

