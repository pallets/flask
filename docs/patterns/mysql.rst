Using MySQL with Flask
======================

.. currentmodule:: flask_mysqldb

Flask and MySQL have a nice partnership. With an easy setup, Flask can connect to your MySQL database. Inserting,
updating, deleting, and selecting data from MySQL can all be done in one simple setup.


Installation
------------

Install and update using `pip <https://pip.pypa.io/en/stable/quickstart/>`_::

    $ pip install mysqlclient
    $ pip install flask-mysql

A Minimal Application
---------------------

In order to have MySQL integrated with Flask, the flask module needs to be imported with Flask and flask_mysqldb needs
to be imported with MySQL. For the purpose of this document rendor_template, request, redirect, url_for will also be
used from the module flask. Below is a snippet that can be used for this implementation::

    from flask import Flask, rendor_template, request, redirect, url_for
    from flask_mysqldb import MySQL

To get things up and running, the flask app needs to be setup. Also, the MySQL configuration needs to have the MySQL
credentials. The following is the basic setup that is needed to connect MySQL to Flask. This can be placed at the top
of the routes file that will handle MySQL data and below the modules that are imported.
Be sure to fill in the proper credentials for host, port, user, and password, database name::

    app = Flask(__name__)
    app.config['MYSQL_HOST'] = 'HOST'
    app.config['MYSQL_PORT'] = 'PORT'
    app.config['MYSQL_USER'] = 'USER'
    app.config['MYSQL_PASSWORD'] = 'PASSWORD'
    app.config['MYSQL_DB'] = 'DATABASE NAME'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    mysql = MySQL(app)

It is recommended that you set app.config['MYSQL_CURSORCLASS'] = 'DictCursor' to easily parse form data passed to Flask.
This makes all incoming form data passed as a dictionary style object. It is very similar to a dictionary but not a true
dictionary. Each field in the form is a key and the input is the value assigned to the key. Also, the information from
database can be passed to HTML templates and easily used in the Jinja syntax. This tutorial assumes DictCursor has been
setup.

Selecting Database Information and Displaying it
------------------------------------------------

To grab data from the database, a cursor needs to be opened and saved to variable name of your choice using
mysql.connection.cursor(). To perform a select statement, place it within .execute(). To pull everything after a
statement execution, the command .fetchall() can be used and saved to a dictionary style variable with name of your
choosing. After the data is saved to a variable, be sure to close the cursor with .close() so the connection is
properly closed. The information pulled from MySQL can be placed within the render_template function in the return
statement. This will send the data to the desired HTML template to be displayed to users. The following snippet shows an
example of MySQL table named Customers and the data being rendered to a page called customers.html. It is also placed
in a function named customers() with the Flask route decoration to page /customers/::

    @app.route('/customers/', methods=['POST','GET'])
    def customers():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM customers")
        customers = cur.fetchall()
        cur.close()

        return render_template('customers.html', customers=customers)

The MySQL data has now been passed to the customers.html file. In order to display the data, the Jinja syntax is used.
The Jinja syntax is used to parse data from the customers object passed in rendor_tmplate. Below is an example of
how Jinja syntax can be used to display the MySQL data in an html data format::

    <table class="table table-hover table-dark" data-toggle="table" data-sort-name="Customer ID">
        <thead>
            <tr>
                <th scope="col" data-sortable="true" data-field="Customer ID">Customer ID</th>
                <th scope="col" data-sortable="true">First Name</th>
                <th scope="col" data-sortable="true">Last Name</th>
                <th scope="col" data-sortable="true">Phone Number</th>
            </tr>
        </thead>
        <tbody>
        {% for customer in customers %}
            <tr>
                <td>{{ customer.customer_id }}</td>
                <td>{{ customer.first_name }}</td>
                <td>{{ customer.last_name }}</td>
                <td>{{ customer.phone_number }}</td>
            </tr>
        </tbody>
    </table>

If only certain fields or specific entries need to be pulled, the fields can be placed instead of the * and using the where
clause can filter out unneeded entries. Below is an example of pulling only first_name and last_name where customer_id
is some input saved in cid::

    cur.execute("SELECT first_name, last_name FROM customers WHERE customer_id = %s", (cid))

Creating and Inserting Data into a Database Table
-------------------------------------------------

Flask can gather data from an HTML form, pass it a to Flask route, and then use MySQL to insert data into a table.
This is where the url_for is used to pass html form data to Flask. Below is an example of a simple form for capturing
data and passing it to a Flask route. The form is using Bootstrap for styling::

    <form action="{{ url_for('add_customer') }}" method="POST">
        <div class="modal-body" style="color:black">
            <div class="form-group">
                <label>First Name</label>
                <input type="text" pattern="[a-zA-Z\s]+" class="form-control" id=fname name="fname" required="1" maxlength="35" value="{{customer.first_name}}">
            </div>
            <div class="form-group">
                <label>Last Name</label>
                <input type="text" pattern="[a-zA-Z\s]+" class="form-control" id=lname name="lname" required="1" maxlength="35" value="{{customer.last_name}}">
            </div>
            <div class="form-group">
                <label>Phone Number</label>
                <input type="text" class="form-control" id="phone" name="phone" pattern="[0-9]+" required="1" minlength="10" maxlength="10" value="{{customer.phone_number}}">
            </div>
        </div>
    </form>

Within the form action, the Jinja syntax {{ url_for('update_customer') }} will pass what is captured in the form to
the route update_customer. Each id in the input will be the key in the dictionary style object that will be used to
insert data into the table. Below is the route and associated function that the information in the form is sent to::

    @app.route('/add_customer/', methods=['POST', 'GET'])
    def add_customer():

        if request.method == 'POST':

            fname = request.form['fname']
            lname = request.form['lname']
            phone = request.form['phone']

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO customers (first_name, last_name, phone_number) VALUES (%s, %s, $s)", (fname, lname, phone))
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('customers'))

The above snippet is the route, add_customer, that was used in the action= of the form. As mentioned before, it is
passed in a dictionary type object. Within the add_customer function, the request module is used. The POST method needs
to be checked to make sure the POST was used in the form. Each field is pulled by the id used in the form. In the
snippet, fname = request.form['fname'] will pull the valude form key 'fname' and assign it to a Python variable called
fname. As with the select, a cursor needs to be opened. Once the cursor is opened, the Python variables can be placed
into the execute command. Using **"INSERT INTO customers (first_name, last_name, phone_number) VALUES (%s, %s, $s)",
(fname, lname, phone)** is the same as running **INSERT INTO customers (first_name, last_name, phone_number) VALUES
('John', 'Smith', '8005882300')**. In Python syntax, the variables fname, lname, and phone will be placed in %s. The app need needs
to commit the changes and close the cursor. In the return statement, redirect and url_for will jump back to the customers
function and then the data will be pulled and displayed on the page customers.html page.

Deleting an Entry from a MySQL Table
------------------------------------

Deleting an entry is very simple. A user can select a database entry by the primary key and use Python SQL syntax to
delete the object. Building on the select statement section, a delete option can be implemented for each row. Below,
is an updated version of the HTML table that includes the field for delete::

    <table class="table table-hover table-dark" data-toggle="table" data-sort-name="Customer ID">
        <thead>
            <tr>
                <th scope="col" data-sortable="true" data-field="Customer ID">Customer ID</th>
                <th scope="col" data-sortable="true">First Name</th>
                <th scope="col" data-sortable="true">Last Name</th>
                <th scope="col" data-sortable="true">Phone Number</th>
                <th scope="col">Delete</th>
            </tr>
        </thead>
        <tbody>
        {% for customer in customers %}
            <tr>
                <td>{{ customer.customer_id }}</td>
                <td>{{ customer.first_name }}</td>
                <td>{{ customer.last_name }}</td>
                <td>{{ customer.phone_number }}</td>
                <td><a href="/delete_customers/{{customer.customer_id}}" class="btn btn-danger btn-sm" data-toggle="modal" data-target="#deletecustomermodal{{customer.customer_id}}" >Delete Customer</a></td>
            </tr>
        </tbody>
    </table>

    <div class="modal fade" id="deletecustomermodal{{customer.customer_id}}" tabindex="-1" role="dialog" aria-labelledby="deleteModalLabel" aria-hidden="true">
        <form action="{{ url_for('delete_customer') }}" method="POST">
            <div class="modal-body" style="color:black">
                <div class="form-group">
                    <input type="hidden" id="cid" name="cid" value="{{customer.customer_id}}">
                </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="submit" name="editcustomerdata" class="btn btn-danger">DELETE CUSTOMER</button>
            </div>
        </form>
    </div>

The snippet is using Bootstrap, but don't worry about it too much about. Another column has been added for Delete.
The Delete column includes a button that will lead to a form to delete the customer. It is a pop up box that will
route to delete_customer in the Flask routes and shown in action="{{ url_for('delete_customer') }}. The form will pass
the customer ID (primary key) based on the entry (row) that was selected. Deletion works best when using the primary key
instead of searching by other fields. Now that the customer id (cid) has been routed to delete_customer, the following
snippet gives an example of a customer being deleting using the customer id::

    @app.route('/delete_customer/',methods=['POST','GET'])
    def delete_customer():

        cid = request.form['cid']
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM customers WHERE customer_id=%s", [cid],)

        mysql.connection.commit()
        cur.close()
        return redirect(url_for('customers'))

As with adding a customer, the data was sent as dictionary type object. Use the request module to pull the value in key
'cid'. Open up a cursor to establish the connection for the operation. When using the delete operation with single key,
use %s after the customer_id and pass cid within brackets. The extra comma after cid ensures that a single object is
passed. As before, the execution is not saved unless commit is used. Close the connection (cursor) and redirect to the
desired function, in this case the customers function to display data on customers.html.

Updating Entries from a MySQL Table
-----------------------------------

Entries can be updated using Flask and MySQL. It is important that the primary key is used when updating objects, otherwise
issues can occur. Below builds on the current HTML table by adding an update button next to each entry. It has been included
with the delete button::

    <table class="table table-hover table-dark" data-toggle="table" data-sort-name="Customer ID">
        <thead>
            <tr>
                <th scope="col" data-sortable="true" data-field="Customer ID">Customer ID</th>
                <th scope="col" data-sortable="true">First Name</th>
                <th scope="col" data-sortable="true">Last Name</th>
                <th scope="col" data-sortable="true">Phone Number</th>
                <th scope="col">Edit / Delete</th>
            </tr>
        </thead>
        <tbody>
        {% for customer in customers %}
            <tr>
                <td>{{ customer.customer_id }}</td>
                <td>{{ customer.first_name }}</td>
                <td>{{ customer.last_name }}</td>
                <td>{{ customer.phone_number }}</td>
                <td>
                    <a href="/update_customers/{{customer.customer_id}}" class="btn btn-warning btn-sm" data-toggle="modal" data-target="#editcustomermodal{{customer.customer_id}}" >Edit Customer</a>
                    <a href="/delete_customers/{{customer.customer_id}}" class="btn btn-danger btn-sm" data-toggle="modal" data-target="#deletecustomermodal{{customer.customer_id}}" >Delete Customer</a>
                </td>
            </tr>
        </tbody>
    </table>

    <div class="modal fade" id="editcustomermodal{{customer.customer_id}}" tabindex="-1" role="dialog" aria-labelledby="editModalLabel" aria-hidden="true">
        <form action="{{ url_for('update_customer') }}" method="POST">
            <div class="form-group">
                <input type="hidden" id="cid" name="cid" value="{{customer.customer_id}}">
            </div>
            <div class="form-group">
                <label>First Name</label>
                <input type="text" pattern="[a-zA-Z\s]+" class="form-control" id=fname name="fname" required="1" maxlength="35" value="{{customer.first_name}}">
            </div>
            <div class="form-group">
                <label>Last Name</label>
                <input type="text" pattern="[a-zA-Z\s]+" class="form-control" id=lname name="lname" required="1" maxlength="35" value="{{customer.last_name}}">
            </div>
            <div class="form-group">
                <label>Phone Number</label>
                <input type="text" class="form-control" id="phone" name="phone" pattern="[0-9]+" required="1" minlength="10" maxlength="10" value="{{customer.phone_number}}">
            </div>
        </form>
    <div>

Again, the example above uses Bootstrap style objects, but do not worry about it. An edit button has been added to the
table that will pull up a form. The form is passed the primary key of the entry that the user clicked on. The form allows
the fields associated to the customer id (primary id) to update the entry in MySQL. It is passed to the route
update_customer. The snippet below is for the route update_customer::

    @app.route('/update_customer/',methods=['POST','GET'])
    def update_customer():

        if request.method == 'POST':

            cid = request.form['cid']
            fname = request.form['fname']
            lname = request.form['lname']
            phone = request.form['phone']

            cur = mysql.connection.cursor()
            cur.execute(""" UPDATE customers SET first_name=%s, last_name=%s, phone_number=%s WHERE customer_id=%s """, (fname, lname, phone, cid)
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('customers'))

This route is the same as the customers route with the select statement. The only difference is the execute statement,
everything else is the same. The execute contains the SQL syntax for update. The variables fname, lname, phone, and
cid are passed into the %s place holders. The function then returns to customers() to show the updated data in the
table. At this point, the document has gone over selecting, inserting, deleting, and updating data.

Creating a Table in MySQL
-------------------------

This section will give a quick example of creating a MySQL database in Flask. Most of the time, a table would not be
created in a Flask app, but in the backend when creating or updating the layout of the database. Below, is a
snippet that shows an example creating the customer table in Flask::

    @app.route("/")
    def create_customer_table():

        cur = mysql.connection.cursor()
        cur.execute("CREATE TABLE customers (customer_id INT NOT NULL PRIMARY KEY, first_name VARCHAR(35) NOT NULL, last_name VARCHAR(35) NOT NULL, phone_number CHAR(10) NOT NULL)")
        mysql.connection.commit()
        cur.close()

        return

A cursor is opened to establish a connection. The CREATE TABLE SQL syntax is exactly same as running in SQL command
line. It needs to be placed in the execute. Commit the changes and the table will be created in the database.
