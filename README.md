# box-office
A simple ticket booking system built in Python using Flask

To run on your local machine follow these steps

1. Create a python virtual environment using `virtualenv venv`
2. Activate the virtual environment using `source venv/bin/activate` if
using a Unix OS or `venv\Scripts\activate` on Windows
3. Run `pip install -r requirements.txt`
4. Run `python manage.py runserver`

# Current Features

* Users - register, login, forgotten password, change email, order history
* Bookings - create bookings
* Cart - add tickets, timed release tickets, checkout
* Emails - booking confirmations, change password emails
* Events - display showings, number of available tickets
* Tickets - ticket types

# Planned Features

* Admin - add events, add showings, edit Bookings
* Cart - remove tickets, group by showings
* Events - change showing layout, add images
