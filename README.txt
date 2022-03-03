This App is to upload XLSX file in this case (Book12 in main directory). 
Then select the column to be multiplied by 2.
Then download the new table with the new column made by multiplying another by 2.

# Upload, select, manipulate, download

# Structure:
	-This app has 2 databases one to capture excel file upon upload
	- Once uploaded the excel file gets saved in Data (database sql alchemy) and in uploads excel_uploads
	-Then it redirects to a new page columnselect which lets you see the table un manipulated and upon submit performs calculation 
		- Then it submits the calculated df to uploads/manipulated_exce and to the manipulated (sql alchemy database)
		- redirects you and shows you data that has new column
	- Then upon download you can get file 