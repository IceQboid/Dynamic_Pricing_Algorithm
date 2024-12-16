import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import StandardScaler

class PricingPredictor:
    def __init__(self):
        # Temperature thresholds (F)
        self.COLD_TEMP = 45
        self.HOT_TEMP = 73
        
        # Precipitation thresholds (inches)
        self.RAIN_THRESHOLD = 0.04
        self.SNOW_THRESHOLD = 1.0
        
        # Busyness threshold (percentage)
        self.BUSY_THRESHOLD = 70
        
        # Price adjustment factors
        self.MAX_PRICE_INCREASE = 1.3  # 30% max increase
        self.MIN_PRICE_DECREASE = 0.9  # 10% max decrease
        
        # Initialize ML model
        self.model = DecisionTreeRegressor(max_depth=3)
        self.scaler = StandardScaler()
        
        # Train model on historical data
        self._train_model()

    def _generate_training_data(self):
        """Generate synthetic training data based on Hicksville patterns"""
        n_samples = 5000
        
        # Generating synthetic features
        temperatures = np.random.normal(loc=55, scale=15, size=n_samples)  # Mean temp with variation
        precipitation = np.random.exponential(scale=0.1, size=n_samples)   # Rain/snow amounts
        busyness = np.random.normal(loc=50, scale=20, size=n_samples)     # Restaurant busyness
        
        # Required conditions for price adjustments
        cold_weather = temperatures < self.COLD_TEMP
        wet_weather = precipitation > self.RAIN_THRESHOLD
        busy_times = busyness > self.BUSY_THRESHOLD
        
        
        price_adjustments = np.ones(n_samples)
        
       
        price_adjustments[cold_weather & wet_weather & busy_times] *= self.MAX_PRICE_INCREASE
        price_adjustments[~(cold_weather | wet_weather | busy_times)] *= self.MIN_PRICE_DECREASE
        
        #Feature matrix
        X = np.column_stack([temperatures, precipitation, busyness])
        y = price_adjustments
        
        return X, y

    def _train_model(self):
        
        X, y = self._generate_training_data()       
        
        X_scaled = self.scaler.fit_transform(X)        
        
        self.model.fit(X_scaled, y)

    def predict_price_adjustment(self, temperature, precipitation, busyness):       
        # Scale input features  
        X = np.array([[temperature, precipitation, busyness]])
        X_scaled = self.scaler.transform(X)
        
        # Get prediction
        adjustment = self.model.predict(X_scaled)[0]
        
        # Ensure adjustment stays within bounds
        adjustment = max(self.MIN_PRICE_DECREASE, min(self.MAX_PRICE_INCREASE, adjustment))
        
        return adjustment

    def get_final_price(self, base_price, temperature, precipitation, busyness):
        """Calculate final price based on conditions"""
        adjustment = self.predict_price_adjustment(temperature, precipitation, busyness)
        return round(base_price * adjustment, 2)