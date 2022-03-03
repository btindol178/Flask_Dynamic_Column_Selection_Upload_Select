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
        filename = secure_filename(form.file.data.filename)
        form.file.data.save('uploads/excel_uploads' + "/" + filename)

        path_var = os.path.dirname(app.instance_path)  +"/"+ app.config["UPLOAD_FOLDER"] +"/" + filename
        print("pathvar is",path_var)
        dt = datetime.now()
        ts = dt.strftime("%Y%m%d_%H%M%S")
        tempfilename = f'{ts}{filename}'
        print("tempfilename is",tempfilename)
        urlzz = f'{app.config["BASE_PATH_UPLOAD"]}/{tempfilename}' #make the path that we will save the file to.
        print("URL IS ",urlzz)
        df = pd.read_excel(path_var)
        print(df)
        df.to_excel(urlzz)
        tables = df.to_html(classes='table table-striped', header="true", index=False)
        df2 = pd.DataFrame(df)
        #cols = list(df2.columns)
        path_var_fin = os.path.dirname(app.instance_path)  +"/"+ app.config["UPLOAD_FOLDER"] +"/" + tempfilename

        req = Data(filepath = path_var_fin,filename=tempfilename)

        db.session.add(req)
        db.session.commit()

        return redirect(url_for('columnselect')) #render_template("tableselection2.html",cols=cols,tables=tables)

    return render_template('upload.html', form=form)



@app.route('/uploads/manipulated_excel/<path>')
def redownloaded_file(path):
    print (path)
    return send_from_directory(app.config["MANIPULATED_FOLDER"], path)

# NOW FROM HERE SHOW THE TABLE 
@app.route('/columnselect',methods=['GET','POST'])
def columnselect():
    #form = selectionform()


    if request.method == 'POST':# form.validate_on_submit():
        #selection1 = form.selection.data
        selectedcol = request.form['columns']
        
        # Get path to latest table again
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

        df["x3"] = df[selectedcol] * 2 

        pre_manipulated_upload_timestamp = tables[0].timestamp
        dt = datetime.now()
        ts = dt.strftime("%Y%m%d_%H%M%S")
        tempfilename = f'{ts}{file_name}'
        print("tempfilename is",tempfilename)
        download_url_path = f'{app.config["BASE_PATH_DOWNLOAD"]}/{tempfilename}' #make the path that we will save the file to.
        print("download_url_path",download_url_path)
        # Send dataframe to excel file
        df.to_excel(download_url_path)

        # Submit manipulated data information to database
        final_manipulated = DataManipulated(filename_fin = tempfilename,filepath_fin=download_url_path,timestamp_prev=pre_manipulated_upload_timestamp)
        db.session.add(final_manipulated)
        db.session.commit()

        tables = df.to_html(classes='table table-striped', header="true", index=False)
        print(type(selectedcol))

        return  redirect(url_for('downloadfinal'))#render_template("download.html",tables=tables,selectedcol=selectedcol,file_name = file_name) #"<h1> Fart {selectedcol} </h1>"

    # Show the date from previous redirect upload
    tables =Data.query.order_by(Data.timestamp.desc()).all()
    print("tables",tables[0].filepath) # 0 will give you the latest record 
    path_to_df = tables[0].filepath
    print("Path_to_df",path_to_df)
    df = pd.read_excel(path_to_df)
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

    if request.method == 'POST':
        tables =DataManipulated.query.order_by(DataManipulated.timestamp.desc()).all()
        print("tables",tables[0].filepath_fin) # 0 will give you the latest record 
        path_to_df = tables[0].filepath_fin
        print("Path_to_df",path_to_df)
        path_to_file = tables[0].filename_fin
        print("Filename_fin:",path_to_file)
        return send_file(path_to_df ,as_attachment=True, mimetype='application/vnd.ms-excel',attachment_filename="test.xlsx")

    tables =DataManipulated.query.order_by(DataManipulated.timestamp.desc()).all()
    print("tables",tables[0].filepath_fin) # 0 will give you the latest record 
    path_to_df = tables[0].filepath_fin
    print("Path_to_df",path_to_df)
    df = pd.read_excel(path_to_df)
    df = pd.DataFrame(df)
    print(df)
    # Get columns for the dropdown values
    cols = list(df.columns)
    # Get the table from the sql alchemy query 
    tables = df.to_html(classes='table table-striped', header="true", index=False)
    
    return render_template("download.html",cols=cols,tables=tables)


if __name__ =="__main__":
    app.run(debug=True)