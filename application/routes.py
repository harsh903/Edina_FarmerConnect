from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from application.database import app, db, User, Farmer, Expert, Post, PostCommentLikes, Chat, ChatReply, Appointment
from flask_login import current_user, login_required
import openai

# Set your OpenAI API key
openai.api_key = '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'

app.secret_key = 'jfglkafjdf4556erty'


# Home route
@app.route('/')
def home():
    return render_template('home.html')

#____________________________________________________________Register and Login____________________________________________________________________

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(name=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.user_id
            session['username'] = user.name
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your username and password', 'error')
            return "404", 404
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')
        hashed_password = generate_password_hash(password)

        new_user = User(
            name=username,
            email=email,
            password=hashed_password,
            role=role,
            location=request.form.get('location'),
            primary_language=request.form.get('primary_language')
        )
        db.session.add(new_user)
        db.session.commit()

        if role == 'farmer':
            new_farmer = Farmer(
                user_id=new_user.user_id,
                land_size=request.form.get('land_size'),
                farmer_bio=request.form.get('farmer_bio'),
                major_crops=request.form.get('major_crops')
            )
            db.session.add(new_farmer)
        elif role == 'expert':
            new_expert = Expert(
                user_id=new_user.user_id,
                expert_bio=request.form.get('expert_bio'),
                experience=request.form.get('experience'),
                domain=request.form.get('domain')
            )
            db.session.add(new_expert)

        db.session.commit()

        session['user_id'] = new_user.user_id
        session['username'] = new_user.name
        session['role'] = new_user.role
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

#____________________________________________________________Profile Dashboard____________________________________________________________________

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    user = User.query.get(user_id)
    if not user:
        flash('User not found!')
        return redirect(url_for('logout'))

    if role == 'farmer':
        farmer = Farmer.query.filter_by(user_id=user_id).first()
        if not farmer:
            flash('Farmer profile not found!')
            return redirect(url_for('logout'))

        # Dummy requests and replies for farmers (e.g., Harsh and Aakash)
        requests_from_experts = [
            {"expert_name": "Aarti Sharma", "message": "Please provide more details about your farm’s financial situation."},
            {"expert_name": "Rajesh Kumar", "message": "Can you share the recent crop yield data for better financial advice?"}
        ]
        replies_to_experts = [
            {"expert_name": "Aarti Sharma", "message": "Thank you for the advice. I'll provide the financial data soon."},
            {"expert_name": "Rajesh Kumar", "message": "I've uploaded the yield data. Please review it."}
        ]

        return render_template(
            'profile.html',
            user=user,
            role=role,
            farmer=farmer,
            requests_from_experts=requests_from_experts,
            replies_to_experts=replies_to_experts
        )

    elif role == 'expert':
        expert = Expert.query.filter_by(user_id=user_id).first()
        if not expert:
            flash('Expert profile not found!')
            return redirect(url_for('logout'))

        # Dummy requests and replies for experts (e.g., Aarti Sharma and Rajesh Kumar)
        requests_from_farmers = [
            {"farmer_name": "Harsh", "message": "I need advice on securing a loan for my next crop cycle."},
            {"farmer_name": "Aakash", "message": "Can you help with financial planning for the upcoming season?"}
        ]
        replies_to_farmers = [
            {"farmer_name": "Harsh", "message": "I suggest you apply for the Kisan Credit Card scheme for easier loan access."},
            {"farmer_name": "Aakash", "message": "Please consider using crop insurance to mitigate financial risks."}
        ]

        return render_template(
            'profile.html',
            user=user,
            role=role,
            expert=expert,
            requests_from_farmers=requests_from_farmers,
            replies_to_farmers=replies_to_farmers
        )

    flash('Invalid user role!')
    return redirect(url_for('logout'))

@app.route('/search_experts')
def search_experts():
    return render_template('search_expert.html')

# Route for Price Calculator page
@app.route('/price_cal')
def price_cal():
    return render_template('price_cal.html')




# Update profile route
@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        user.name = request.form.get('username')
        user.email = request.form.get('email')
        user.location = request.form.get('location')
        user.primary_language = request.form.get('primary_language')
        
        new_password = request.form.get('password')
        if new_password:
            user.password = generate_password_hash(new_password, method='sha256')

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', user=user)


def get_farming_recommendation(location, land_area, income, season):
    messages = [
        {"role": "system", "content": "You are an expert in agriculture and agro-value chain financing."},
        {"role": "user", "content": f"Location: {location}"},
        {"role": "user", "content": f"Farming Land Area: {land_area} acres"},
        {"role": "user", "content": f"Income: {income} INR"},
        {"role": "user", "content": f"Season: {season}"},
        {"role": "user", "content": "Recommend 5 crops to grow for maximum profit. For each crop, provide the following details:\n"
                                    "- Best planting times\n"
                                    "- Optimal irrigation techniques\n"
                                    "- Pest management strategies\n"
                                    "- Where to sell the crops (local markets, cooperatives, digital marketplaces)\n"
                                    "- Financing schemes that can support the crop (government schemes, subsidies, etc.)\n"
                                    "- Seeding bank facilities and how to access them\n"
                                    "- Support from cooperative banks for financing\n"
                                    "- Cost-cutting strategies to maximize profit\n"
                                    "- Best practices for maximizing crop yield using Agriculture 4.0 technologies (IoT, AI, drones, precision farming)."}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=4000,
        temperature=0.7,
    )
    
    recommendation = response['choices'][0]['message']['content'].strip()
    return recommendation


@app.route('/crop_recommender', methods=['GET', 'POST'])
def crop_recommender():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            location = data.get('location')
            land_area = data.get('land_area')
            income = data.get('income')
            season = data.get('season')

            if not all([location, land_area, income, season]):
                return jsonify({"error": "Missing required parameters"}), 400

            recommendation = get_farming_recommendation(location, land_area, income, season)
            return jsonify({"recommendation": recommendation})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # For GET requests or initial page load
    return render_template('Crop_Recommender.html')



# Function to check if user is logged in
def is_logged_in():
    return 'user_id' in session

# Route to display community posts and create a new post
@app.route('/community_posts', methods=['GET', 'POST'])
def community_posts():
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']
        new_post = Post(title=title, content=content, user_id=user_id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('community_posts'))

    posts = Post.query.all()
    return render_template('community_posts.html', posts=posts)

# Route to add a comment on a post
@app.route('/comment', methods=['POST'])
def comment():
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in

    post_id = request.form['post_id']
    comment = request.form['comment']
    user_id = session['user_id']
    new_comment = PostCommentLikes(post_id=post_id, commenter_id=user_id, creator_id=None, comment=comment)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('community_posts'))

# Route to like a post
@app.route('/like/<int:post_id>', methods=['POST'])
def like(post_id):
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in

    post = Post.query.get(post_id)
    if post:
        comment = PostCommentLikes.query.filter_by(post_id=post_id, commenter_id=session['user_id']).first()
        if comment:
            comment.total_likes += 1
        else:
            new_like = PostCommentLikes(post_id=post_id, commenter_id=session['user_id'], creator_id=None, comment='', total_likes=1)
            db.session.add(new_like)
        db.session.commit()
    return jsonify({'success': True})

# Route to dislike a post
@app.route('/dislike/<int:post_id>', methods=['POST'])
def dislike(post_id):
    if not is_logged_in():
        return redirect(url_for('login'))  # Redirect to login if not logged in

    post = Post.query.get(post_id)
    if post:
        comment = PostCommentLikes.query.filter_by(post_id=post_id, commenter_id=session['user_id']).first()
        if comment:
            comment.total_dislikes += 1
        else:
            new_dislike = PostCommentLikes(post_id=post_id, commenter_id=session['user_id'], creator_id=None, comment='', total_dislikes=1)
            db.session.add(new_dislike)
        db.session.commit()
    return jsonify({'success': True})





@app.route('/send_query/<int:expert_id>', methods=['POST'])
def send_query(expert_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    if role != 'farmer':
        flash('Only farmers can send queries.', 'danger')
        return redirect(url_for('dashboard'))

    query_text = request.form.get('query_text')
    new_query = Chat(user_id=user_id, expert_id=expert_id, query_text=query_text)
    db.session.add(new_query)
    db.session.commit()
    flash('Your query has been sent.', 'success')

    return redirect(url_for('dashboard'))

@app.route('/send_appointment/<int:expert_id>', methods=['POST'])
def send_appointment(expert_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    if role != 'farmer':
        flash('Only farmers can request appointments.', 'danger')
        return redirect(url_for('dashboard'))

    new_appointment_request = Appointment(user_id=user_id, expert_id=expert_id, appointment_requested=True)
    db.session.add(new_appointment_request)
    db.session.commit()
    flash('Appointment request has been sent.', 'success')

    return redirect(url_for('dashboard'))

@app.route('/reply_query/<int:query_id>', methods=['POST'])
def reply_query(query_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    if role != 'expert':
        flash('Only experts can reply to queries.', 'danger')
        return redirect(url_for('dashboard'))

    query = Chat.query.get_or_404(query_id)
    reply_text = request.form.get('reply_text')
    new_reply = ChatReply(chat_id=query_id, expert_id=user_id, reply_text=reply_text)
    db.session.add(new_reply)
    db.session.commit()
    flash('Your reply has been submitted.', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/confirm_appointment/<int:appointment_id>', methods=['POST'])
def confirm_appointment(appointment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    appointment = Appointment.query.get_or_404(appointment_id)

    if role != 'expert' or user_id != appointment.expert_id:
        flash('Only the assigned expert can confirm this appointment.', 'danger')
        return redirect(url_for('dashboard'))

    appointment_time = datetime.strptime(request.form.get('appointment_time'), '%Y-%m-%dT%H:%M')
    contact_details = request.form.get('contact_details')

    appointment.appointment_time = appointment_time
    appointment.contact_details = contact_details
    appointment.appointment_confirmed = True
    db.session.commit()

    flash('Appointment has been confirmed and details sent to the farmer.', 'success')
    return redirect(url_for('dashboard'))







# Mock data for latest updates
latest_update = [
  {
    "Scheme Title": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
    "Center/State Scheme": "Center",
    "Short Description": "Income support scheme for farmers to help their financial needs in procuring various inputs to ensure proper crop health and appropriate yields.",
    "Link": "https://www.pmkisan.gov.in/"
  },
  {
    "Scheme Title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
    "Center/State Scheme": "Center",
    "Short Description": "A comprehensive insurance scheme aimed at reducing the premium burden on farmers and ensuring early settlement of crop assurance claims for the full insured sum.",
    "Link": "https://pmfby.gov.in/"
  },
  {
    "Scheme Title": "Pradhan Mantri Krishi Sinchayee Yojana (PMKSY)",
    "Center/State Scheme": "Center",
    "Short Description": "An initiative to improve farm productivity and ensure better utilization of water resources in the country.",
    "Link": "http://pmksy.gov.in/"
  },
  {
    "Scheme Title": "Kisan Credit Card (KCC) Scheme",
    "Center/State Scheme": "Center",
    "Short Description": "Provides adequate and timely credit support from the banking system under a single window to the farmers for their cultivation and other needs.",
    "Link": "https://www.nabard.org/content1.aspx?id=602&catid=23&mid=530"
  },
  {
    "Scheme Title": "Soil Health Card Scheme",
    "Center/State Scheme": "Center",
    "Short Description": "Promotes soil testing in the country and issues Soil Health Cards to farmers, providing nutrient recommendations for their crops aimed at improving productivity.",
    "Link": "https://soilhealth.dac.gov.in/"
  },
  {
    "Scheme Title": "National Mission For Sustainable Agriculture (NMSA)",
    "Center/State Scheme": "Center",
    "Short Description": "Aims at promoting sustainable agriculture practices among farmers by targeting resource conservation, resilient farming methods, and soil health.",
    "Link": "https://nmsa.dac.gov.in/"
  },
  {
    "Scheme Title": "Atmanirbhar Bharat Abhiyan (Self-reliant India Campaign)",
    "Center/State Scheme": "Center",
    "Short Description": "A holistic package aimed at reducing farmers' dependency on imported goods, encouraging domestic production, and fostering self-reliance.",
    "Link": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1625309"
  },
  {
    "Scheme Title": "Rashtriya Krishi Vikas Yojana (RKVY)",
    "Center/State Scheme": "Center",
    "Short Description": "Provides flexibility and autonomy to states in planning and executing schemes for holistic development of agriculture and allied sectors.",
    "Link": "https://rkvy.nic.in/"
  },
  {
    "Scheme Title": "Paramparagat Krishi Vikas Yojana (PKVY)",
    "Center/State Scheme": "Center",
    "Short Description": "Aims at promoting organic farming practices among farmers and ensuring the availability of organic produce in the market.",
    "Link": "https://pib.gov.in/PressReleasePage.aspx?PRID=1543238"
  },
  {
    "Scheme Title": "Gramin Bhandaran Yojna",
    "Center/State Scheme": "Center",
    "Short Description": "Supports the creation of scientific storage capacity and helps reduce post-harvest losses by offering financial assistance to farmers.",
    "Link": "https://www.nabard.org/content1.aspx?id=603&catid=23&mid=531"
  },
  {
    "Scheme Title": "National Agricultural Market (eNAM)",
    "Center/State Scheme": "Center",
    "Short Description": "An online trading platform which helps farmers get better prices for their commodities by providing real-time market prices and transparent trade processes.",
    "Link": "https://www.enam.gov.in/"
  },
  {
    "Scheme Title": "Micro Irrigation Fund (MIF)",
    "Center/State Scheme": "Center",
    "Short Description": "Provides loans to state governments to support micro-irrigation projects, enabling efficient water usage and increased farm productivity.",
    "Link": "https://www.nabard.org/content1.aspx?id=758&catid=23&mid=538"
  },
  {
    "Scheme Title": "National Mission on Edible Oils – Oil Palm (NMEO-OP)",
    "Center/State Scheme": "Center",
    "Short Description": "Supports the cultivation of oil palm to reduce the country's dependence on imported edible oils and promote domestic production.",
    "Link": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1745743"
  },
  {
    "Scheme Title": "Dairy Entrepreneurship Development Scheme (DEDS)",
    "Center/State Scheme": "Center",
    "Short Description": "Promotes entrepreneurship in dairy farming by providing financial support for setting up dairy units and other related activities.",
    "Link": "https://dahd.nic.in/"
  },
  {
    "Scheme Title": "Fisheries and Aquaculture Infrastructure Development Fund (FIDF)",
    "Center/State Scheme": "Center",
    "Short Description": "Aims at boosting the fishery sector by providing concessional finance for creating infrastructure facilities for the fisheries sector.",
    "Link": "https://www.nfdb.gov.in/"
  },
  {
    "Scheme Title": "Mukhya Mantri Krishi Ashirwad Yojana",
    "Center/State Scheme": "State",
    "State_Name": "Jharkhand",
    "Short Description": "Provides financial assistance to farmers of Jharkhand on a yearly basis to support their farming activities.",
    "Link": "https://cmka.jharkhand.gov.in/"
  },
  {
    "Scheme Title": "Pasudhan Bima Yojana",
    "Center/State Scheme": "State",
    "State_Name": "Haryana",
    "Short Description": "Offers insurance coverage for cattle to protect farmers against losses due to death of livestock, providing economic stability.",
    "Link": "http://pashudhanharyana.gov.in/en/pashudhan-bima-yojana"
  },
  {
    "Scheme Title": "Karnataka Raitha Suraksha Pradhan Mantri Fasal Bima Yojna",
    "Center/State Scheme": "State",
    "State_Name": "Karnataka",
    "Short Description": "A customized crop insurance scheme tailored for farmers in Karnataka, helping them secure crop loss due to unforeseen disasters.",
    "Link": "https://raitamitra.karnataka.gov.in/English"
  },
  {
    "Scheme Title": "Rythu Bandhu Scheme",
    "Center/State Scheme": "State",
    "State_Name": "Telangana",
    "Short Description": "Provides financial assistance to farmers for the two crop seasons every year to support input purchasing and farming activities.",
    "Link": "https://rythubandhu.telangana.gov.in/"
  },
  {
    "Scheme Title": "YSR Rythu Bharosa",
    "Center/State Scheme": "State",
    "State_Name": "Andhra Pradesh",
    "Short Description": "Provides financial support to eligible farmers in Andhra Pradesh to ensure timely investment in their agriculture and maximize yield.",
    "Link": "https://ysrrythubharosa.ap.gov.in/"
  },
  {
    "Scheme Title": "Krishi Rin Samadhan Yojana",
    "Center/State Scheme": "State",
    "State_Name": "Uttar Pradesh",
    "Short Description": "A loan waiver scheme aimed at small and marginal farmers to alleviate their debt burden and secure their economic future.",
    "Link": "http://upagripardarshi.gov.in/"
  },
  {
    "Scheme Title": "Bihar Rajya Fasal Sahayata Yojana",
    "Center/State Scheme": "State",
    "State_Name": "Bihar",
    "Short Description": "Provides financial support to farmers in case of crop loss due to natural calamities, securing their investment and livelihood.",
    "Link": "https://pacsonline.bih.nic.in/"
  },
  {
    "Scheme Title": "Pradhan Mantri Kisan Maan-Dhan Yojana (PM-KMY)",
    "Center/State Scheme": "Center",
    "Short Description": "A pension scheme for small and marginal farmers to ensure financial security in their old age by providing a monthly pension.",
    "Link": "https://pmkmy.gov.in/"
  },
  {
    "Scheme Title": "Sampada Yojana",
    "Center/State Scheme": "Center",
    "Short Description": "A scheme aiming at agro-marine processing and development of agro-processing clusters, boosting farmer income through value addition.",
    "Link": "https://mofpi.nic.in/Schemes/pmksy"
  },
  {
    "Scheme Title": "Deen Dayal Upadhyaya Grameen Kaushalya Yojana (DDU-GKY)",
    "Center/State Scheme": "Center",
    "Short Description": "Training youth from rural areas in various skill sets to secure employment, promoting rural prosperity and economic well-being.",
    "Link": "https://ddugky.gov.in/"
  },
  {
    "Scheme Title": "Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)",
    "Center/State Scheme": "Center",
    "Short Description": "Provides a legal guarantee for at least 100 days of wage employment in a financial year to every rural household whose adult members volunteer to do unskilled manual work.",
    "Link": "https://www.nrega.nic.in/"
  }
]


@app.route('/latest_updates', methods=['GET'])
def latest_updates():
    scheme_name = request.args.get('scheme_name', '')
    center_state = request.args.get('center_state', '')

    # Your logic to filter updates based on scheme_name and center_state
    # Example:
    filtered_updates = [update for update in latest_update if 
                        (scheme_name.lower() in update["Scheme Title"].lower()) and 
                        (not center_state or center_state == update["Center/State Scheme"])]

    return render_template('latest_updates.html', updates=filtered_updates)
