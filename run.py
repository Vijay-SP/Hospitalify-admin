from flask import Flask, session, redirect, request, render_template, url_for, jsonify
import json
from check_login import check_login
from firebase_crud import *
from firebase_admin import auth, firestore



app = Flask(__name__)
app.secret_key = "admin_panel_website"

with open("config.json", "r") as c:
    params = json.load(c)['params']


@app.route("/", methods=["GET", "POST"])
def login():
    # if user is logged in
    if ('user' in session and session['user'] == params['admin_user']):
        return redirect("/properties")

    # If user requests to log in
    if request.method == "POST":
        # Redirect to Admin Panel
        username = request.form.get('uname')
        userpassword = request.form.get('pass')
        if (username == params['admin_user'] and userpassword == params['admin_password']):
            session['user'] = username
            return redirect("/properties")

    return render_template("register.html", params=params)


@app.route("/properties")
@check_login
def properties():
    coursedata = fetchCourse()
    return render_template("properties.html", params=params, course=coursedata, active="course")


@app.route('/register', methods=['GET', 'POST'])
def register_hospital():
    if request.method == 'POST':
        # Get the hospital name, email, and password from the form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        auth.create_user(email = email, password= password)
        # Add the hospital to the hospitals collection in Firestore
        hospitals_ref = db.collection('hospitals')
        hospital_doc = hospitals_ref.document()
        hospital_doc.set({
            'id': hospital_doc.id,
            'name': name,
            'email': email,
            'password': password
        })

        return render_template('login.html', params=params)
    else:
        return render_template('register.html', params=params)

# @app.route('/register', methods=["GET", "POST"])
# def register():
#     if ('user' in session and session['user'] == params['admin_user']):
#         return redirect("/properties")
#     # Get user data from the request
#     name = request.form['name']
#     email = request.form['email']
#     phone = request.form['phone']
#     image = request.files['image']
#     image_content = image.read()
#
#     # Use face_recognition library to extract face features
#     encoding = face_recognition.face_encodings(face_recognition.load_image_file(image_content))[0]
#
#     # Store user data in Firebase
#     user_ref = db.collection('users').document(email)
#     user_ref.set({
#         'name': name,
#         'email': email,
#         'phone': phone,
#         'encoding': encoding.tolist()
#     })
#
#     # Return success message
#     return render_template("register.html", params=params)

# Hospital login
@app.route('/login', methods=['GET', 'POST'])
def login_hospital():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Authenticate the hospital
            user = auth.get_user_by_email(email)
            print(user.uid)

            # Set a session cookie with Firebase credentials
            params["userId"] = user.uid
            return render_template('slots.html', params=params)

        except Exception as e:
            print(e)
            return "Error: Invalid email or password."

    else:
        return render_template('login.html', params=params)

# Add or update slots
@app.route('/set_slots', methods=['GET', 'POST'])
def add_slots():
        # Get the hospital ID, date, and slots from the form data
        hospital_id = request.form['hospital_id']
        date = request.form['date']
        slots = request.form.getlist('slots')

        if not hospital_id or not date or not slots:
            return jsonify({'error': 'Missing required fields'}), 400

        # Get a reference to the hospital document in the Firestore database
        hospital_ref = db.collection('hospitals').document(hospital_id)

        # Get the current slots for the specified date
        current_slots = hospital_ref.get().to_dict().get(date, [])

        # Merge the new slots with the current slots
        new_slots = list(set(current_slots) | set(slots))

        # Update the hospital document with the merged slots for the specified date
        try:
            hospital_ref.update({
                date: new_slots
            })
            return jsonify({'message': 'Slots added successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        return render_template('slots.html')

@app.route("/buyers")
@check_login
def buyers():
    usersData = fetchBuyers()
    return render_template("buyers.html", params=params, users=usersData,  active="buyers")

@app.route("/contacts")
@check_login
def contacts():
    contacts = fetchContacts()
    return render_template("contacts.html", params=params, contacts=contacts,  active="contacts")



@app.route("/logout")
def logout():
    session.pop('user')
    session.clear()
    return redirect("/")


@app.route("/addproperty", methods=["GET", "POST"])
@check_login
def addproperty():
    # when add button is pressed
    if request.method == "POST":
        # upload the images

        # upload the data to firebase
        uploadPropertyData(request)
        return redirect("/properties")

    return render_template("add_property.html", params=params, active="properties")


@app.route("/property/<id>", methods=["GET", "POST"])
@check_login
def property(id):
    coursedata = fetchCourse()

    if request.method == "POST":

        updateEditedProperty(request, id)
        # check for new floor plan images

        return redirect("/properties")

    return render_template("edit_property.html", params=params, course=coursedata, active="course")


@app.route("/delete/<id>", methods=["GET", "POST"])
@check_login
def deleteProperty(id):
    property = fetchProperty(id)
    # Delete the document from firebase
    deletePropertyFromFirebase(id)

    return redirect("/properties")

@app.route("/deletecontact/<id>", methods=["GET", "POST"])
@check_login
def deletecontact(id):
    # Delete the document from firebase
    deleteContactFromFirebase(id)
    return redirect("/contacts")


if __name__ == '__main__':
    app.run(debug=True)

# CONTACT US

