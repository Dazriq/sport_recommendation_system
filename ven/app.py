# from flask import Flask

# app=Flask(__name__)

# @app.route('/')
# def home(): 
#     return "Hello World"

from flask import Flask, redirect, render_template, request, jsonify, url_for
import pandas as pd
import numpy as np
from math import sqrt
from IPython.display import display
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import coo_matrix
from flask_mysqldb import MySQL
from flask import flash
from flask import session
from sqlalchemy import create_engine, text

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Set a secret key for flash messages

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'recommendation_system'

mysql = MySQL(app)



# Set the initial value for the name_id_counter
name_id_counter = 165

@app.route('/home')
def home():
    # Check if the user is logged in
    if 'email' in session:
        # User is logged in, proceed to Home.html
        return render_template('index.html')
        # return render_template('Home.html')

    else:
        # User is not logged in, redirect to the login page
        return render_template('index-login.html')
    
@app.route('/profile/<user_id>', methods=['GET', 'POST'])
def profile(user_id):
    # Create a cursor to interact with the database
    cursor = mysql.connection.cursor()

    # Prepare the SQL query to check if the user exists in the database
    sql = "SELECT * FROM userprofile WHERE user_id =" + user_id

    # Execute the query
    cursor.execute(sql)

    # Fetch the result
    user = cursor.fetchone()
    

    # Close the cursor
    cursor.close()
    return render_template('profile.html', results=user)
    # User is logged in, proceed to Home.html
    # return render_template('profile.html', results=5)
    # return render_template('profile.html')
    # return render_template('Home.html')


@app.route('/')
def login():
    # return render_template('login.html')
    return render_template('index-login.html')


@app.route('/loginForm', methods=['POST'])
def loginForm():
    email = request.form['email']
    password = request.form['password']

    # Create a cursor to interact with the database
    cursor = mysql.connection.cursor()

    # Prepare the SQL query to check if the user exists in the database
    sql = "SELECT * FROM userprofile WHERE Email = %s AND Password = %s"
    values = (email, password)

    # Execute the query
    cursor.execute(sql, values)

    # Fetch the result
    user = cursor.fetchone()

    # Close the cursor
    cursor.close()

    if user:
        # User exists in the database, set session and redirect to Home.html
        session['email'] = email
        session['user_id'] = user[0]
        return render_template('index.html')
        
        # return render_template('Home.html')

    else:
        # User does not exist or incorrect login details, display an error message
        # flash('Invalid email or password', 'error')
        return redirect(url_for('login', error='true'))
        # return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()

    # Redirect the user to the login page
    return render_template('index-login.html')
    # return render_template('login.html')


@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact')
def contact():
    return render_template('Contact.html')

@app.route('/registration')
def registration():
    return render_template('Registration.html')

# Define the route to handle the form submission
@app.route('/registerform', methods=['POST'])
def registerform():
    # global name_id_counter  # Access the global name_id_counter variable
    # name_id_counter += 1  # Increment the name_id_counter for each new registration

    # Retrieve form data
    email = request.form['email']
    name = request.form['name']
    password = request.form['password']
    age = request.form['age']
    gender = request.form['gender']
    state = request.form['state']
    sports = request.form['sports']
    athlete = request.form['athlete']
    time = request.form['time']
    rating = request.form['rating']

    # return email + name + password + age + gender + state + athlete + time + rating


    # Create a cursor to interact with the database
    cursor = mysql.connection.cursor()

    # Prepare the SQL query
    sql = "INSERT INTO userprofile (name, gender, age, state, athlete, sports, time, name_id, rating, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values = (name, gender, age, state, athlete, sports, time, name_id_counter, rating, email, password)

    # Execute the query
    cursor.execute(sql, values)

    # Commit the changes to the database
    mysql.connection.commit()

    # Close the cursor
    cursor.close()

    # Flash a success message
    flash('Registration successful!', 'success')
    
    session['email'] = email
    #todo: add user_id session
    # session['user_id'] = user[0]

    # Redirect the user to a success page or back to the registration form
    return redirect(url_for('home', register='true'))

    return render_template('index.html')


@app.route('/recommendation/<email>', methods=['GET', 'POST'])
def recommendation(email):
    # Connect to the database
    engine = create_engine('mysql://root:@localhost:3306/recommendation_system')
    connection = engine.connect()

    # Retrieve the name_id based on the email
    query = text("SELECT user_id FROM userprofile WHERE email = :email")
    result = connection.execute(query, {"email": email})
    row = result.fetchone()

    if row:
        # my_name_id = row[0]
        my_name_id = 266

        # Load data from the database into a DataFrame
        df = pd.read_sql_table('userprofile', engine)

        # df["name_id"] = df["name_id"].astype(str)
        # df["user_index"] = df["name_id"].astype("category").cat.codes
        # df["sports_index"] = df["Sports"].astype("category").cat.codes

        #create imp column
        for i in range(0, df.shape[0]):
          df["imp"]=df["state"] + ' ' + df["sports"]+' '+ df["rating"].map(str)

        df["ids"]=[i for i in range(0,df.shape[0])]

        from sklearn.feature_extraction.text import TfidfVectorizer
        vec=TfidfVectorizer()
        vecs=vec.fit_transform(df["imp"].apply(lambda x: np.str_(x)))

        from sklearn.metrics.pairwise import cosine_similarity
        sim=cosine_similarity(vecs) 

        #recommend
        scores=list(enumerate(sim[my_name_id]))
        sorted_scores=sorted(scores,key=lambda x:x[1],reverse=True)
        sorted_scores=sorted_scores[1:]
        name_list=[df[name_list[0]==df["ids"]]["ids"].values[0] for name_list in sorted_scores]
        # return name_list
        
        #recommend10
        first_ten=[]
        count=0
        for id in name_list:
            if count > 9:
                break
            count+=1
            first_ten.append(id)
        
        top_recs = df[df["ids"].isin(first_ten)].copy()
        # sports_recs = similar_users.groupby(["Name", "Gender", "Age", "Sports", "rating", "State", "Athlete", "Time"]).rating.agg(['count', 'mean']).reset_index()
        # similar_users = similar_users[similar_users["name_id"] != my_name_id]
        
        
        # ratings_mat_coo = coo_matrix((df["rating"], (df["user_index"], df["sports_index"])))

        # ratings_mat = ratings_mat_coo.tocsr()

        # # Rest of your code for performing the recommendation algorithm goes here
        # my_index = df[df["name_id"] == my_name_id]["user_index"].iloc[0]

        # similarity = cosine_similarity(ratings_mat[my_index, :], ratings_mat).flatten()
        # indices = np.argpartition(similarity, -11)[-11:]

        # similar_users = df[df["user_index"].isin(indices)].copy()
        # similar_users = similar_users[similar_users["name_id"] != my_name_id]

        # sports_recs = similar_users.groupby(["Name", "Gender", "Age", "Sports", "rating", "State", "Athlete", "Time"]).rating.agg(['count', 'mean']).reset_index()

        # sports_recs["score"] = sports_recs["mean"]


        # my_sports = df.loc[df["user_index"] == my_index, "Sports"].unique()

        # top_recs = sports_recs[sports_recs["Sports"].isin(my_sports)].sort_values("score", ascending=False)

        return render_template('recommendation.html', results=top_recs.to_dict('records'))
    else:
        # Handle the case when the user is not found
        return "User not found"




if __name__ == '__main__':
    app.run(debug=True)




