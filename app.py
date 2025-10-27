from flask import Flask, render_template, request, jsonify, redirect, session
from flask_cors import CORS
import mysql.connector
import pickle
import numpy as np
import os 

app = Flask(__name__)
app.secret_key = 'App_login_data'  
CORS(app, supports_credentials=True, origins=['http://localhost:5000'])  
# Add these lines:
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False 
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mehulmysql@90',
    'database': 'project_smart' 
} 

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG) 

discount_model = None
discount_scaler = None
discount_features = None
platform_model = None
platform_scaler = None 
platform_features = None
label_encoders = None
model_metadata = None
models_loaded = False

try:
    # Load discount prediction model
    if os.path.exists('discount_model.pkl'):
        with open('discount_model.pkl', 'rb') as f:
            discount_model = pickle.load(f)
    
    if os.path.exists('discount_scaler.pkl'):
        with open('discount_scaler.pkl', 'rb') as f:
            discount_scaler = pickle.load(f)
    
    if os.path.exists('discount_features.pkl'):
        with open('discount_features.pkl', 'rb') as f:
            discount_features = pickle.load(f)
    
    # Load platform prediction model
    if os.path.exists('platform_model.pkl'):
        with open('platform_model.pkl', 'rb') as f:
            platform_model = pickle.load(f)    
    if os.path.exists('platform_scaler.pkl'):
        with open('platform_scaler.pkl', 'rb') as f:
            platform_scaler = pickle.load(f)
    
    if os.path.exists('platform_features.pkl'):
        with open('platform_features.pkl', 'rb') as f:
            platform_features = pickle.load(f)
    
    # Load label encoders
    if os.path.exists('label_encoders.pkl'):
        with open('label_encoders.pkl', 'rb') as f:
            label_encoders = pickle.load(f)
    
    # Load metadata
    if os.path.exists('model_metadata.pkl'):
        with open('model_metadata.pkl', 'rb') as f:
            model_metadata = pickle.load(f)
    
    if all([discount_model, discount_scaler, discount_features, 
            platform_model, platform_scaler, platform_features, label_encoders]):
        models_loaded = True
        print("All files loaded ! ") 
    else:
        print("⚠️ Some model files are missing!")
        
except Exception as e:
    print(f"❌ Error loading models: {e}")
    import traceback
    traceback.print_exc()
    
# Add this new route
@app.route('/signup')
def signup_page():
    return render_template('signup.html')

# CHANGE 1: Redirect home to login
@app.route('/')
def home():
    # Check if user is logged in
    if 'user_email' in session:
        return render_template('index.html')
    else:
        return redirect('/login')

# CHANGE 2: Login page route
@app.route('/login')
def login_page():
    return render_template('login.html')

# CHANGE 3: Add logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# CHANGE 4: Add home page route (for after login)
@app.route('/home')
def home_page():
    if 'user_email' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/predict')
def predict_page():
    # Check if user is logged in
    if 'user_email' not in session:
        return redirect('/login')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT platform FROM products ORDER BY platform")
        platforms = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return render_template('predict.html', categories=categories, platforms=platforms)
    except Exception as e:
        print(f"Error loading categories/platforms: {e}")
        return render_template('predict.html', categories=[], platforms=[])
    
@app.route('/contact')
def contact_page():
    # Contact page doesn't require login, but you can add it if needed
    return render_template('contact.html')


@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Validate inputs
        if not name or not email or not message:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # TODO: Save to database or send email
        # For now, just log it
        print(f"\n📧 NEW CONTACT MESSAGE")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Message: {message}")
        print("=" * 50)
        
        return jsonify({
            'success': True,
            'message': 'Thank you for contacting us! We will get back to you soon.'
        })
        
    except Exception as e:
        print(f"❌ Error in contact form: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Check database for user
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user['password'] == password:  # In production, use hashed passwords!
            session.permanent = True  # Add this line
            session['user_email'] = email
            session['logged_in'] = True
            
            token = "demo_token_" + email
            return jsonify({
                'success': True,
                'token': token,
                'user': {'email': email}
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not name or not email or not password:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email already registered'
            }), 400
        
        # Insert new user (Note: In production, hash the password!)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Auto-login after signup
        session.permanent = True  # THIS IS THE NEW LINE
        session['user_email'] = email
        session['logged_in'] = True
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully'
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/predict', methods=['POST'])
def predict():
    # Check if user is logged in
    if 'user_email' not in session:
        return jsonify({
            'success': False,
            'error': 'User not authenticated'
        }), 401
    
    print("\n" + "="*50)
    print("📮 NEW PREDICTION REQUEST")
    print("="*50)
    
    if not models_loaded:
        error_msg = 'Models not loaded. Please run model_training.py first.'
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
    
    try:
        data = request.json
        print(f"📥 Received data: {data}")
        
        # Extract user inputs
        category = data.get('category', 'Electronics')
        budget = float(data.get('budget', 5000))
        preferred_platform = data.get('platform', None)
        
        # Validate category
        if not category:
            raise ValueError("Category is required")
        
        # Encode category
        category_encoded = label_encoders['category'].transform([category])[0]
        
        # Calculate price range
        if budget < 1000:
            price_range = 0
        elif budget < 5000:
            price_range = 1
        elif budget < 15000:
            price_range = 2
        elif budget < 30000:
            price_range = 3
        else:
            price_range = 4
        
        # Default values
        rating_preference = 4.0
        stock_estimate = 200
        stock_status = 2
        
        # Rating category
        if rating_preference <= 3.5:
            rating_category = 0
        elif rating_preference <= 4.0:
            rating_category = 1
        elif rating_preference <= 4.5:
            rating_category = 2
        else:
            rating_category = 3
        
        # Predict best platform if not specified
        if preferred_platform:
            platform_encoded = label_encoders['platform'].transform([preferred_platform])[0]
            best_platform = preferred_platform
            platform_confidence = 100.0
        else:
            discount_estimate = 15
            discount_effectiveness = 0.15
            
            platform_features_vector = np.array([[
                category_encoded,
                budget,
                discount_estimate,
                rating_preference,
                stock_estimate,
                price_range,
                discount_effectiveness
            ]])
            
            platform_features_scaled = platform_scaler.transform(platform_features_vector)
            platform_encoded = platform_model.predict(platform_features_scaled)[0]
            platform_proba = platform_model.predict_proba(platform_features_scaled)[0]
            
            best_platform = label_encoders['platform'].inverse_transform([platform_encoded])[0]
            platform_confidence = float(platform_proba.max() * 100)
            
            print(f"🎯 Predicted Platform: {best_platform} ({platform_confidence:.1f}% confidence)")
        
        # Predict discount percentage
        stock_estimate = 200
        
        discount_features_vector = np.array([[
            platform_encoded,
            category_encoded,
            budget,
            rating_preference,
            stock_estimate,
            price_range,
            rating_category,
            stock_status
        ]])
        
        discount_features_scaled = discount_scaler.transform(discount_features_vector)
        predicted_discount = float(discount_model.predict(discount_features_scaled)[0])
        
        predicted_discount = max(0, min(50, predicted_discount))
        
        print(f"💰 Predicted Discount: {predicted_discount:.1f}%")
        
        # Calculate discounted price
        discounted_price = budget * (1 - predicted_discount / 100)
        savings = budget - discounted_price
        
        # Generate recommendations
        recommendations = generate_recommendations(
            predicted_discount, best_platform, category, budget
        )
        
        response = {
            'success': True,
            'predicted_discount': round(predicted_discount, 1),
            'best_platform': best_platform,
            'platform_confidence': round(platform_confidence, 1),
            'estimated_price': round(budget, 2),
            'discounted_price': round(discounted_price, 2),
            'savings': round(savings, 2),
            'category': category,
            'recommendations': recommendations,
            'model_used': model_metadata['discount_model_name'] if model_metadata else 'ML Model'
        }
        
        print(f"📤 Response: {response}")
        print("="*50 + "\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        print("="*50 + "\n")
        return jsonify({'success': False, 'error': str(e)}), 400

def generate_recommendations(discount, platform, category, budget):
    """Generate shopping recommendations based on predictions"""
    recommendations = []
    
    if discount > 30:
        recommendations.append(f"🎉 Excellent! {platform} offers great discounts on {category}")
        recommendations.append(f"💡 You can save up to {discount:.0f}% - perfect time to buy!")
    elif discount > 20:
        recommendations.append(f"✅ Good deal! {platform} has decent discounts on {category}")
        recommendations.append(f"💰 Expected savings around {discount:.0f}%")
    else:
        recommendations.append(f"⚠️ Moderate discounts on {platform} for {category}")
        recommendations.append(f"💡 Consider waiting for sales or checking other platforms")
    
    if budget > 10000:
        recommendations.append("💳 High-value purchase - look for bank offers and EMI options")
    
    recommendations.append(f"📊 Compare prices across platforms before purchasing")
    recommendations.append(f"⭐ Check product ratings and reviews")
    
    return recommendations

@app.route('/api/categories')
def get_categories():
    """Get all available categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/platforms')
def get_platforms():
    """Get all available platforms"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT platform FROM products ORDER BY platform")
        platforms = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'platforms': platforms})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)