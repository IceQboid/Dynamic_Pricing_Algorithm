from django.shortcuts import render
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from django.http import JsonResponse
import populartimes
from .ml_predictor import PricingPredictor
from datetime import datetime

load_dotenv()

#helper function for better display of time in 12hr format
def format_time(time_str):    
    hour = int(time_str[:2])
    minute = time_str[2:]    
    suffix = "AM" if hour < 12 else "PM"
    hour = hour % 12
    if hour == 0:
        hour = 12

    return f"{hour}:{minute} {suffix}"

def extract_menu(restaurant_url):
    response = requests.get(restaurant_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        sections = soup.find_all("h2", class_="alternate")  
        menu = {}
        for section in sections:
            section_title = section.text.strip()
            menu_items = section.find_next("div", class_="u-space-b3").find_all("div", class_="menu-item")
            
            items = []
            for item in menu_items:
                h4_name = item.find("h4").text.strip() if item.find("h4") else "N/A"
                price = item.find("div", class_="menu-item-prices arrange_unit")
                price = price.text.strip() if price else "N/A"
                items.append({"item": h4_name, "price": price})
            
            menu[section_title] = items
        
        return menu
    else:
        print(f"Failed to fetch menu for {restaurant_url}")
        return None

def get_restaurant_menus(restaurants):
    all_menus = {}
    for restaurant in restaurants:
        menu = extract_menu(restaurant["url"])
        if menu:
            all_menus[restaurant["name"]] = menu
    return all_menus

#general analysis function
def get_competitor_prices():
      
    competitors = [
        {"name": "Village the Soul of India", "url": "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"},
        {"name": "Kunga Kitchen", "url": "https://www.yelp.com/menu/kunga-kitchen-hicksville"},
        {"name": "Taste of Mumbai", "url": "https://www.yelp.com/menu/taste-of-mumbai-hicksville-3"},
        {"name": "Kathis & Kababs", "url": "https://www.yelp.com/menu/kathis-and-kababs-hicksville"},
        {"name": "Kabul Grill", "url": "https://www.yelp.com/menu/kabul-grill-hicksville-2"},
        {"name": "Taste Of Chennai", "url": "https://www.yelp.com/menu/taste-of-chennai-hicksville"}
    ]
    
    competitor_prices = []
    
    for restaurant in competitors:
        try:            
            menu = extract_menu(restaurant["url"])            
            # Format menu prices
            formatted_menu = {}
            if menu:
                for section, items in menu.items():
                    for item in items:
                        
                        try:
                            price = float(item['price'].replace('$', '').strip())
                            formatted_menu[item['item']] = price
                        except (ValueError, AttributeError):
                            continue
            
            competitor_prices.append({
                'name': restaurant['name'],
                'menu': formatted_menu
            })
            
        except Exception as e:
            print(f"Error fetching menu for {restaurant['name']}: {str(e)}")
            continue
    
    return competitor_prices

#specialized analysis function
def compare_prices_and_show_cheapest(village_menu, nearby_menus):
    lowest_prices = {}

    for section, items in village_menu.items():
        for item in items:
            if isinstance(item, dict):
                item_name = item['item'].strip().lower()  
                village_price = item['price']
                try:
                    village_price_value = float(village_price.strip('$'))  # Get the price from Village
                except ValueError:
                    village_price_value = None  # If the price format is invalid

                
                item_info = {
                    'item': item_name,
                    'village_price': village_price_value,
                    'village_restaurant': "Village the Soul of India",
                    'matching_restaurants': []
                }

                #search for similar items (critical matching)
                for nearby_restaurant in nearby_menus:
                    nearby_menu = nearby_restaurant['menu']

                    if section in nearby_menu:
                        for nearby_item in nearby_menu[section]:
                            if isinstance(nearby_item, dict):
                                nearby_item_name = nearby_item['item'].strip().lower()  # Normalize the name
                                if item_name == nearby_item_name:  # Check if the names match
                                    nearby_price = nearby_item['price']
                                    try:
                                        nearby_price_value = float(nearby_price.strip('$'))  # Get nearby price
                                        item_info['matching_restaurants'].append({
                                            'restaurant': nearby_restaurant['name'],
                                            'price': nearby_price_value
                                        })
                                    except ValueError:
                                        print(f"Invalid price format for item '{item_name}' at {nearby_restaurant['name']}.")

                # After collecting all matching restaurants, check for the cheapest
                if item_info['matching_restaurants']:
                    item_info['matching_restaurants'].append({
                        'restaurant': "Village the Soul of India",
                        'price': village_price_value
                    })

                    # Find the cheapest price
                    cheapest = min(item_info['matching_restaurants'], key=lambda x: x['price'])

                    # Store the result for later use
                    lowest_prices[item_name] = {
                        'cheapest_restaurant': cheapest['restaurant'],
                        'lowest_price': f"${cheapest['price']:.2f}",
                        'matching_restaurants': item_info['matching_restaurants']
                    }

    return lowest_prices 

#only for village
def get_village_details(request):
    if request.method == "GET" and "show_details" in request.GET:
    # Yelp API Setup
        API_KEY = os.getenv("YELP_API_KEY")  # Replace with your actual Yelp API key
        HEADERS = {"Authorization": f"Bearer {API_KEY}"}
        SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

        # Step 1: Fetch the business ID for "Village: The Soul of India"
        search_params = {"term": "Village The Soul of India", "location": "Hicksville, NY"}
        response = requests.get(SEARCH_URL, headers=HEADERS, params=search_params)

        if response.status_code == 200:
            data = response.json()
            if data["businesses"]:
                restaurant = data["businesses"][0]
                business_id = restaurant["id"]

                # Step 2: Fetch detailed business information
                details_url = f"https://api.yelp.com/v3/businesses/{business_id}"
                details_response = requests.get(details_url, headers=HEADERS)

                if details_response.status_code == 200:
                    details = details_response.json()
                    # Extract restaurant details
                    name = details["name"]
                    address = ", ".join(details["location"]["display_address"])
                    phone = details["phone"]
                    rating = details["rating"]

                    # Extract hours of operation
                    hours = []
                    if "hours" in details:
                        for day_hours in details["hours"][0]["open"]:
                            DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                            day_name = DAYS[day_hours["day"]]
                            start_time = format_time(day_hours["start"])
                            end_time = format_time(day_hours["end"])
                            hours.append(f"{day_name}: {start_time} - {end_time}")
                    #Extract menu
                    village_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"  # Replace with actual URL of menu
                    menu = extract_menu(village_url)

                    # Pass data to the template
                    context = {
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "rating": rating,
                        "hours": hours,
                        "menu" : menu,
                    }
                    return render(request, "village_pricing/village_details.html", context)
                else:
                    return JsonResponse({"error": "Error fetching business details"}, status=details_response.status_code)
            else:
                return JsonResponse({"error": "No business found"}, status=404)
        else:
            return JsonResponse({"error": "Error fetching search results"}, status=response.status_code)
    else:
        return render(request, "village_pricing/village_details.html")
    
#similar restaurant
def get_top5_restaurants(request):
    context = {}
    
    if request.method == "GET" and "show_top5" in request.GET:
        # Yelp API Setup
        API_KEY = os.getenv("YELP_API_KEY")  # Replace with your actual Yelp API key
        HEADERS = {"Authorization": f"Bearer {API_KEY}"}
        SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

        params_for_top5 = {
            "term": "Indian",  # Modify this to match the cuisine type of interest
            "location": "Hicksville, NY",  # Change this to the location of your target restaurant
            "radius": 2000,  # 2 km radius
            "limit": 6,  # Get top 5 results
            "sort_by": "rating",  # Sort by rating (default is best match)
        }

        # Make the API request
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params_for_top5)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            top5_restaurants = []
            if data["businesses"]:
                for restaurant in data["businesses"]:
                    name = restaurant["name"]
                    if "Village" in name:
                        continue

                    address = ", ".join(restaurant["location"]["display_address"])
                    rating = restaurant["rating"]
                    phone = restaurant.get("phone", "N/A")
                    top5_restaurants.append({
                        "name": name,
                        "address": address,
                        "rating": rating,
                        "phone": phone,
                    })
            context["top5"] = top5_restaurants
        else:
            context["error_top5"] = "Error fetching top 5 restaurants."

    return render(request, "village_pricing/village_details.html", context)

    
def compare_prices(request):
    context = {}
    
    if request.method == "GET" and "compare_prices" in request.GET:
        # Define your list of restaurants
        restaurants_test = [
            {"name": "Village the Soul of India", "url": "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"},
            {"name": "Kunga Kitchen", "url": "https://www.yelp.com/menu/kunga-kitchen-hicksville"},
            {"name": "Taste of Mumbai", "url": "https://www.yelp.com/menu/taste-of-mumbai-hicksville-3"},
            {"name": "Kathis & Kababs", "url": "https://www.yelp.com/menu/kathis-and-kababs-hicksville"},
            {"name": "Kabul Grill", "url": "https://www.yelp.com/menu/kabul-grill-hicksville-2"},
            {"name": "Taste Of Chennai", "url": "https://www.yelp.com/menu/taste-of-chennai-hicksville"}
        ]

        # Get all the restaurant menus
        all_menus = get_restaurant_menus(restaurants_test)

        # Extract the Village menu
        village_menu = all_menus.get("Village the Soul of India", {})
        # Extract the menus of nearby restaurants
        nearby_menus = [
            {"name": "Kunga Kitchen", "menu": all_menus.get("Kunga Kitchen", {})},
            {"name": "Taste of Mumbai", "menu": all_menus.get("Taste of Mumbai", {})},
            {"name": "Kathis & Kababs", "menu": all_menus.get("Kathis & Kababs", {})},
            {"name": "Kabul Grill", "menu": all_menus.get("Kabul Grill", {})},
            {"name": "Taste Of Chennai", "menu": all_menus.get("Taste Of Chennai", {})}
        ]

        # Compare prices and find the cheapest options
        lowest_prices = compare_prices_and_show_cheapest(village_menu, nearby_menus)

        # Add the lowest prices to the context
        context["lowest_prices"] = lowest_prices

    return render(request, "village_pricing/village_details.html", context)


def get_busy_hours(request):
    
    POPULARITY_THRESHOLD = 50  # Example threshold for popularity
    WAIT_TIME_THRESHOLD = 30  # Example threshold for wait time
    
    context = {}
    
    if request.method == "GET" and "show_busy_hours" in request.GET:
        
        API_KEY = os.getenv("GOOGLE_API_KEY")
        place_id = "ChIJPYSDLXWBwokRHLcHIl02Kh8"  # Place ID for Village the Soul of India
        popularity_info = populartimes.get_id(API_KEY, place_id)

        # Process popularity data
        busy_times = []
        for i in range(len(popularity_info["populartimes"])):
            day_name = popularity_info["populartimes"][i]["name"]
            popular_times = popularity_info["populartimes"][i]["data"]
            wait_times = popularity_info["time_wait"][i]["data"]

            day_info = {
                "day": day_name,
                "times": []
            }

            for hour in range(24):  # Iterate over 24 hours of the day
                if popular_times[hour] > POPULARITY_THRESHOLD or wait_times[hour] > WAIT_TIME_THRESHOLD:
                    day_info["times"].append({
                        "hour": hour,
                        "popularity": popular_times[hour],
                        "wait_time": wait_times[hour]
                    })

            busy_times.append(day_info)

        # Add details to context
        context.update({
            "busy_times": busy_times,
        })
    
    return render(request, "village_pricing/weather_busy.html", context)
        

def get_weather(request):
    context = {}
    
    if request.method == "GET" and "show_weather" in request.GET:
        API_KEY = os.getenv("WEATHER_API_KEY")
        city = "Hicksville"
        #imperial units in url parameter returns Temperature in Farenheit 
        url_for_temperature = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=imperial"
        
        response = requests.get(url_for_temperature)
        data = response.json()

        if response.status_code == 200:
            weather = data['weather'][0]['description']
            temperature = data['main']['temp']
            rain = "It is currently raining" if 'rain' in data else "No rain at the moment"

            context.update({
                "weather": weather,
                "temperature": temperature,
                "rain": rain,
                "city": city,
            })
        else:
            context["error_weather"] = "Error fetching weather data."
    
    return render(request, "village_pricing/weather_busy.html", context)
        

#ML Implementation      
def get_adjusted_prices(request):
    context = {}
    
    if request.method == "GET" and "show_adjusted_prices" in request.GET:
        try:
            #weather data
            API_KEY = os.getenv("WEATHER_API_KEY")
            city = "Hicksville"
            url_for_temperature = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=imperial"
            
            weather_response = requests.get(url_for_temperature)
            weather_data = weather_response.json()
            
            if weather_response.status_code != 200:
                raise Exception("Failed to fetch weather data")
                
            temperature = weather_data['main']['temp']
            precipitation = weather_data.get('rain', {}).get('1h', 0)  # Rain in last hour
            
            # busy hour
            current_hour = datetime.now().hour
            current_day = datetime.now().strftime('%A')
            
            #Using popularity_info with google api
            g_api_key = os.getenv("GOOGLE_API_KEY")
            place_id = "ChIJPYSDLXWBwokRHLcHIl02Kh8"
            
            popularity_info = populartimes.get_id(g_api_key, place_id)
            day_data = next((day for day in popularity_info['populartimes'] if day['name'] == current_day), None)
            current_busyness = day_data['data'][current_hour] if day_data else 50
            
            # Initialize ML predictor and get menus
            predictor = PricingPredictor()
            village_url = "https://www.yelp.com/menu/village-the-soul-of-india-hicksville"
            
            village_menu = extract_menu(village_url)
            competitor_prices = get_competitor_prices()
            
            
            formatted_village_menu = {}
            for section, items in village_menu.items():
                for item in items:
                    try:
                        price = float(item['price'].replace('$', '').strip())
                        formatted_village_menu[item['item']] = price
                    except (ValueError, AttributeError):
                        continue
            
            # Calculate adjusted prices
            adjusted_prices = []
            for item, base_price in formatted_village_menu.items():
                try:
                    # Get competitor prices for this item
                    competitor_item_prices = [
                       {'price': comp['menu'][menu_item], 
                        'restaurant': comp['name']} 
                        for comp in competitor_prices 
                        for menu_item in comp['menu']
                        if menu_item.lower() == item.lower()
                    ]
                    
                    if competitor_item_prices:
                        lowest = min(competitor_item_prices, key=lambda x: x['price'])
                        lowest_competitor_price = lowest['price']
                        lowest_competitor = lowest['restaurant']
                        
                        # Get price adjustment
                        adjustment = predictor.predict_price_adjustment(
                            temperature=temperature,
                            precipitation=precipitation,
                            busyness=current_busyness
                        )
                        
                        # Calculate final price
                        final_price = predictor.get_final_price(
                            base_price=lowest_competitor_price,
                            temperature=temperature,
                            precipitation=precipitation,
                            busyness=current_busyness
                        )
                        
                        adjusted_prices.append({
                            'item': item,
                            'base_price': base_price,
                            'lowest_competitor_price': lowest_competitor_price,
                            'lowest_competitor': lowest_competitor,
                            'adjusted_price': final_price,
                            'adjustment_factor': adjustment
                        })
                
                except Exception as e:
                    print(f"Error processing item {item}: {str(e)}")
                    continue
            
            
            context.update({
                'adjusted_prices': adjusted_prices,
                'current_temperature': temperature,
                'current_precipitation': precipitation,
                'current_busyness': current_busyness,
                'weather_description': weather_data['weather'][0]['description']
            })
            
        except Exception as e:
            context['error'] = f"Error calculating adjusted prices: {str(e)}"
    
    return render(request, "village_pricing/adjusted_prices.html", context)