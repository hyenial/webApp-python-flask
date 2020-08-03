# Item Catalog Project


An Udacity Full Stack Web Developer  Nanodegree project developed by Harun Yenial.

## About
- This application provides a list of items within a variety of categories as well as provide a user registration and authentication system. 
- Registered users will have the ability to create, edit, and delete their own items (CRUD functionality)
- for demo you can visit this address http://54.90.129.96.xip.io/

## Features

- Proper authentication and authorisation check.
- Full CRUD support using SQLAlchemy and Flask.
- JSON endpoints.
- Implements oAuth using Google Sign-in API.

## Skills used for this project
- Python Flask
- HTML, and CSS
- Bootstrap
- Jinja2
- SQLAchemy
- OAuth
- Google Login


## Some things you might need
- Python 3.6 or higher
- $ pip install Flask
- SQL Alchemy 1.3 or higher
- pip install SQLAlchemy https://pypi.org/project/SQLAlchemy/
- Jinga 2 
- pip install Jinja2

### OR

- instal Vagrant https://www.vagrantup.com/
- Install Virtual Machine (https://www.virtualbox.org/) 
- Go to Vagrant folder where you have installed in
- open in terminal then Vagrant UP (it may take more than 2 min, it will setup Ubuntu18.04 O.S virtually )
- then Vagrant ssh
- cd /vagrant


## Getting Started
- go to the folder

 ```sh
$ cd catalog_CRUD
$ python app.py
 ```
 - Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 - open your browser than http://localhost:5000/
 
## JSON Endpoints
you can reach JSON end points
- http://localhost:5000/bookstores/JSON
- http://localhost:5000/books/JSON
- http://localhost:5000/bookstores/1/JSON or any bookstore number 
http://localhost:5000/bookstores/1/books/1/JSON or change bookstore number and item bumber

## Troubleshooting
- if you havee flask login problem "ImportError: No module named flask_login
", use the this command  pip install flask-login

- if you cannot sign in with Google account please make sure your browser adress must be "http://localhost:5000/login" NOT 0.0.0.5000
- if you cannot logout please clear cookies in your browser


