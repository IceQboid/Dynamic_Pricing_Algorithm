# Pricing Algorithm Project

## Overview
This project implements a dynamic pricing algorithm for restaurants, example used here is "Village the Soul of India," based on various factors such as local competition, weather conditions, and busyness. The project uses data from Yelp, Google Maps, and OpenWeather APIs to adjust menu prices dynamically.

## Features
1. **Fetch Restaurant Details**: Get name, address, open times, menu items, and prices for Village from Yelp API.
2. **Fetch Competitor Data**: Get top-rated 5 restaurants within 2 km with similar menu items.
3. **Display Menu Items & Prices**: Display menu items and prices for Village and each competitor restaurant.
4. **Adjust Prices Based on Conditions**:
   - Fetch busy times from Google Maps API.
   - Fetch current temperature and rain data from OpenWeather API.
   - Adjust prices based on weather and busyness conditions using ML algorithm.
5. **Display Adjusted Prices**: Show the final predicted prices for each menu item.


## Installation
1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/dynamic_pricing_algorithm.git
    cd pricing_algorithm
    ```

2. **Create a virtual environment**:
    ```bash
    conda create -n projectname python=3.9
    conda activate projectname  
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    For Populartimes Library, refer: https://github.com/m-wrzr/populartimes

4. **Set up environment variables**:
    Create a [.env] file in the root directory and add your API keys:
    ```env
    YELP_API_KEY=your_yelp_api_key
    GOOGLE_API_KEY=your_google_api_key
    WEATHER_API_KEY=your_openweather_api_key
    ```

5. **Run the Django server**:
    ```bash
    python manage.py runserver
    ```

## Usage
1. **Fetch and Display Village Details**:
    - Navigate to `pricing/village-details/` to see the details of "Village the Soul of India."
      
    -Details include
   
    1.1.Name,Address,Phone,Rating,Opening Hours and Menu.
   
    1.2.Fetching nearby restaurant serving similar menu.
   
    1.3.Comparing similar menu items.


3. **View Busy Times and Weather of Restaurant**:
    - Navigate to `pricing/get-busy-times/`,  to see the busy hours and the momentary popularity of the restaurant.
    - Navigate to `pricing/get-current-weather/`, to see current weather in the location of the restaurant.

4. **View Adjusted Prices**:
    - Navigate to `pricing/get_adjusted_prices/` to see the dynamically adjusted prices based on current weather and busyness conditions.

## API References
- **Yelp API**: Used to fetch restaurant details and competitor data.
- **Google Maps API**: Places API is used to fetch place based information.
- **OpenWeather API**: Used to fetch current weather data.

## Problem Tackled
- **Google Places API Popular Timing**: The Google Maps API did not provide popular timing data directly. To resolve this, the [populartimes] library was used to fetch and process the busy times data.
- **Yelp API Time Format**: The Yelp API provided time data in a 24-hour format. This was converted to a 12-hour format for better readability using a helper function.
- **Dataset Collection**: The data is synthesized with recent weather reports to ensure accurate and up-to-date pricing adjustments.

## Machine Learning Model
- **Model Used**: Decision Tree Regressor
  - A supervised learning algorithm used for predicting continuous output values (in this case, price adjustment factors).
  - The algorithm learns decision rules from the input data by splitting the data recursively based on feature values to minimize prediction errors.
- **Adjustment Rules**:
  - If the temperature is below 45°F, or if there is snow or heavy rain, and the restaurant is busier than usual, the price is increased by 15%.
  - If the restaurant is busier than usual, an additional 10% increase is applied.
  - Otherwise, the price is set to the lowest competitive price.
  - Room for more lenient adjustment even if one conditions satisfy.

