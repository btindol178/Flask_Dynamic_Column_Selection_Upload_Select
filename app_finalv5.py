from flask import Flask ,url_for, redirect, render_template,send_file, abort,send_from_directory,request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from wtforms import SelectField, SubmitField

SECRET_KEY = os.urandom(32)
app = Flask(__name__)
app.config['SECRET_KEY'] = '5f4d94e1da3bd8871282c8e4b2586a87'
app.config["UPLOAD_FOLDER"]="uploads/excel_uploads"
app.config["RETRIVE_FOLDER"]= "uploads"
app.config["MANIPULATED_FOLDER"]="uploads/manipulated_excel"

app.config["BASE_PATH_UPLOAD"] = os.path.dirname(app.instance_path)  +"/"+ app.config["UPLOAD_FOLDER"]
app.config["BASE_PATH_DOWNLOAD"] = os.path.dirname(app.instance_path)  +"/"+ app.config["MANIPULATED_FOLDER"]

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.before_first_request
def create_tables():
    db.create_all() 
    
#Creating model table for our CRUD database
class Data(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    filename = db.Column(db.String(200))
    filepath = db.Column(db.String(200))
    
class DataManipulated(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    filename_fin = db.Column(db.String(200))
    filepath_fin = db.Column(db.String(200))
    timestamp_prev = db.Column(db.String(200))

class UploadForm(FlaskForm):
    file = FileField()

class selectionform(FlaskForm):
    selection = SelectField('First Selection')
    submit = SubmitField('Execute Query')

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    
    if form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)             # get the date and file name from upload

        # Read in the file name to pandas excel file 
        df = pd.read_excel(filename)           
        print("Form File Data Unmanipulated is",df)

        # Rename file with date time for sending unique file name for later grabbing
        dt = datetime.now()                 # get date
        ts = dt.strftime("%Y%m%d_%H%M%S")   # format date
        tempfilename = f'{ts}{filename}'    # concatenate date and file name 
        print("Paste file name with date time unmanipulated",tempfilename)

        # Format unmanipulated dataframe url link
        url = f'{app.config["BASE_PATH_UPLOAD"]}/{tempfilename}' # get path to upload file and file name with date
        print("The url you are sending unmanipulated dataframe to is ",url)
        
        # Send data frame to url
        df.to_excel(url)
        
        # Send the url and the file name to database for later grabbing
        req = Data(filepath = url,filename=tempfilename)

        db.session.add(req)
        db.session.commit()

        return redirect(url_for('columnselect')) 

    return render_template('upload.html', form=form)


# NOW FROM HERE SHOW THE TABLE 
@app.route('/columnselect',methods=['GET','POST'])
def columnselect():

    # If pick column and submit then 
    if request.method == 'POST':
        # Grab the column 
        selectedcol = request.form['columns']
        
        # Get path to latest table again unmanipulated 
        tables =Data.query.order_by(Data.timestamp.desc()).all()
        print("tables",tables[0].filepath) # 0 will give you the latest record 
        path_to_df = tables[0].filepath 
        
        file_name = tables[0].filename
        print("filename",file_name)
        print("path t0 df",path_to_df)

        df = pd.read_excel(path_to_df)
        df = pd.DataFrame(df)
        print("dataframe is",df)
        print("selectedcol is",selectedcol)

        # Create new column by selecting the column we selected and multiplyingit by 2
        df["x3"] = df[selectedcol] * 2 

        # Get time stamp for when unmanipulated table was uploaded
        pre_manipulated_upload_timestamp = tables[0].timestamp

        # Get time for the manipulated dataframe
        dt = datetime.now()
        ts = dt.strftime("%Y%m%d_%H%M%S")
        tempfilename = f'{ts}{file_name}'
        print("tempfilename is",tempfilename)
        
        # Path for where the manipulated dataframe will be
        download_url_path = f'{app.config["BASE_PATH_DOWNLOAD"]}/{tempfilename}'
        print("download_url_path",download_url_path)

        # Send dataframe to excel file
        df.to_excel(download_url_path)

        # Submit manipulated data information to database
        final_manipulated = DataManipulated(filename_fin = tempfilename,filepath_fin=download_url_path,timestamp_prev=pre_manipulated_upload_timestamp)
        db.session.add(final_manipulated)
        db.session.commit()

        tables = df.to_html(classes='table table-striped', header="true", index=False)
        print(type(selectedcol))

        return  redirect(url_for('downloadfinal'))

    # DEFAULT VIEW OF SELECT COLUMNS SHOWS UN-MANIPULATED DATAFRAME AND DROPDOWN OF COLUMNS
    #Get uploaded record
    tables =Data.query.order_by(Data.timestamp.desc()).all()

    # 0 will give you the latest record of filepath to unmanipulated table
    print("tables",tables[0].filepath) 
    path_to_df = tables[0].filepath
    print("Path_to_df",path_to_df)

    # Read the url to get the table
    df = pd.read_excel(path_to_df)
    #make it dataframe
    df = pd.DataFrame(df)
    print(df)
    # Get columns for the dropdown values
    cols = list(df.columns)
    # Get the table from the sql alchemy query 
    tables = df.to_html(classes='table table-striped', header="true", index=False)
    
    return render_template("tableselection2.html",cols=cols,tables=tables)


# Make download page where it redirects 
# NOW FROM HERE SHOW FILE AND IF POST SEND FILE!!! 
@app.route('/downloadfinal',methods=['GET','POST'])
def downloadfinal():

    # If click download
    if request.method == 'POST':

        # Get the dataframe manipulated
        tables =DataManipulated.query.order_by(DataManipulated.timestamp.desc()).all()

        # get url path to manipulated dataframe
        print("tables",tables[0].filepath_fin) 
        path_to_df = tables[0].filepath_fin
        print("Path_to_df",path_to_df)
        path_to_file = tables[0].filename_fin
        print("Filename_fin:",path_to_file)

        # Send the manipulated dataframe to browser
        return send_file(path_to_df ,as_attachment=True, mimetype='application/vnd.ms-excel',attachment_filename="test.xlsx")

    # Default view to see the manipulated dataframe with extra column!!!!!!!!!!!!!
    # grab new manipulated dataframe
    tables =DataManipulated.query.order_by(DataManipulated.timestamp.desc()).all()

    # Get file path of manipulated dataframe
    print("tables",tables[0].filepath_fin) 
    path_to_df = tables[0].filepath_fin
    print("Path_to_df",path_to_df)
    df = pd.read_excel(path_to_df)
    df = pd.DataFrame(df)
    print(df)

    # Get columns for just display purposes
    cols = list(df.columns)
    # Get the table from the sql alchemy query 
    tables = df.to_html(classes='table table-striped', header="true", index=False)
    
    return render_template("download.html",cols=cols,tables=tables)


if __name__ =="__main__":
    app.run(debug=True)