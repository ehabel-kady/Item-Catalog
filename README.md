#Item Catalog
This is a web app that is used to display a list of categories and each category contains a group of items. Each item has a discription and has the ability to be edited and deleted from the list of category items.
##How to build?
To build this web app you should run the following command in the terminal in case of using linux OS:
```
python project.py
```
then in the browser write the following URL:
```
localhost:8000/
```
##Program Design:
This app is designed using flask API and used to control templates and forms that are designed and found in the templates directory and their CSS file is in the static directory.
###Description
This url will redirect to the website and display the categories and you can login to this website using the login button in the header which will redirect to a page that contains google+ login oauth. After login in you will go back to the main page and you will be able to carry out the CRUD operations as a user. You will not be able to edit, add or delete without loging in to the website.