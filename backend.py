from flask import Flask, render_template
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__,template_folder='templates')

# Initialize Firebase Admin SDK
cred = credentials.Certificate('account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Route to fetch data from Firestore and render template
@app.route('/')
def index():
    images_ref = db.collection('images')
    images = [doc.to_dict() for doc in images_ref.stream()]
    return render_template('index.html', images=images)

if __name__ == '__main__':
    app.run(debug=True)
