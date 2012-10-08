#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
import jinja2
import os
import logging
import random
from google.appengine.ext import db
from google.appengine.api import mail
from webapp2_extras import sessions


jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


class MainPage(BaseHandler):
    def get(self):
        user = self.session.get('user')
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('main.html')
        self.response.out.write(template.render(template_values))


class Services(BaseHandler):
    def get(self):
        user = self.session.get('user')
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('services.html')
        self.response.out.write(template.render(template_values))


class ContactUs(BaseHandler):
    def get(self):
        user = self.session.get('user')
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('contact.html')
        self.response.out.write(template.render(template_values))


class InStreet(BaseHandler):
    def get(self):
        user = self.session.get('user')
        yes = self.session.get('yes')
        if yes:
            if yes == "1":
                self.response.out.write("<div class=\"flash\"> \
                        Yes! We work in your neighbourhood.</div>")
            else:
                self.response.out.write("<div class=\"flash\"> \
                        Sorry! We're not in your area yet.</div>")
            del self.session['yes']
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('instreet.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        streets = ["Ilam Rd", "Creyke Rd", "Clyde Rd", "Kirkwood Ave",
                    "Forestry Rd", "Arts Rd", "Fine Arts Ln", "Science Rd",
                    "Engineering Rd", "University Dr", "Montana Ave"]
        postcodes = ['8041']
        address = self.request.get('address')
        postcode = self.request.get('postcode')
        email = self.request.get('email')
        logging.info("Address is in range: {0}".format(address in streets))
        logging.info("Postcode is in range: {0}".format(postcode in postcodes))
        if address in streets or postcode in postcodes:
            self.session['yes'] = "1"
        else:
            self.session['yes'] = "0"
        if len(email) > 0:
            self.sendmail(email, address, postcode)
            logging.info("Contact request email sent to admins")
        self.redirect('/instreet')

    def sendmail(self, email, address, postcode):
        mail.send_mail_to_admins(
                sender="The Website<info203.presentation@gmail.com>",
                subject="A request for pool maintenance",
                body="""email: %s
                    address: %s
                    postcode: %s""" % (email, address, postcode))


class AddCustomer(BaseHandler):
    def get(self):
        user = self.session.get('user')
        if self.session.get('added'):
            self.response.out.write(
                    "<div class=\"flash\">New Customer Added!</div>")
            del self.session['added']
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('addcustomer.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        customer = Customer()
        customer.fname = self.request.get('fname')
        customer.lname = self.request.get('lname')
        customer.address = self.request.get('address')
        customer.email = self.request.get('email')
        customer.phone = self.request.get('phone')
        customer.put()
        self.session['added'] = True
        self.redirect('/add_customer')


class ListCustomers(BaseHandler):
    def get(self):
        user = self.session.get('user')
        query = db.GqlQuery("SELECT * FROM Customer ORDER BY lname ASC")
        if self.session.get('updated'):
            self.response.out.write(
                    "<div class=\"flash\">Customer Updated!</div>")
            del self.session['updated']
        if self.session.get('deleted'):
            self.response.out.write(
                    "<div class=\"flash\">Customer Deleted!</div>")
            del self.session['deleted']
        template_values = {
            'customers': query,
            'user': user
            }
        template = jinja_environment.get_template('customerlist.html')
        self.response.out.write(template.render(template_values))


class UpdateCustomer(BaseHandler):
	def get(self):
		user = self.session.get('user')
		query = db.GqlQuery("SELECT * FROM Customer")
		template_values = {
            'customer': query[0], #take top, we are prototyping
            'user': user
            }
		template = jinja_environment.get_template('updatecustomer.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		self.redirect('/')
		

class EditCustomer(BaseHandler):
    def get(self):
        user = self.session.get('user')
        # Grab the id that was passed in with the URL
        customer = int(self.request.get('id'))
        query = db.GqlQuery("SELECT * FROM Customer \
                WHERE __key__ = KEY('Customer', :1) LIMIT 1", customer)
        template_values = {
            'customer': query[0],
            'user': user
            }
        template = jinja_environment.get_template('editcustomer.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        logging.info(self.request.get('delete'))
        customer_id = int(self.request.get('id'))
        query = db.GqlQuery("SELECT * FROM Customer \
                WHERE __key__ = KEY('Customer', :1) LIMIT 1", customer_id)
        customer = query[0]
        if len(self.request.get('delete')) > 0:
            customer.delete()
            self.session['deleted'] = True
        else:
            customer.fname = self.request.get('fname')
            customer.lname = self.request.get('lname')
            customer.address = self.request.get('address')
            customer.email = self.request.get('email')
            customer.phone = self.request.get('phone')
            customer.notes = self.request.get('notes')
            customer.put()
            self.session['updated'] = True
        self.redirect('/list_customers')


class AddStock(BaseHandler):
    def get(self):
        user = self.session.get('user')
        if self.session.get('added'):
            self.response.out.write(
                    "<div class=\"flash\">New Stock Item Added!</div>")
            del self.session['added']
        template_values = {
            'user': user
            }
        template = jinja_environment.get_template('addstock.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        stock = Stock()
        stock.itemname = self.request.get('itemname')
        stock.stockcode = self.request.get('stockcode')
        stock.description = self.request.get('description')
        costprice = self.request.get('costprice')
        sellprice = self.request.get('sellprice')
        stocklevel = self.request.get('stocklevel')
        stock.supplier = self.request.get('supplier')
        # Remove $ and . from prices (assuming they will be $45.26 or similar)
        cost = costprice.replace("$", "")
        # Allow for value in dollars only (45 becomes 4500)
        if not '.' in cost:
            cost += "00"
        cost = cost.replace(".", "")
        sell = sellprice.replace("$", "")
        if not '.' in sell:
            sell += "00"
        sell = sell.replace(".", "")
        # Now convert to a cents value for integer storage
        stock.costprice = int(cost)
        stock.sellprice = int(sell)
        # And convert the stock level to an int
        stock.stocklevel = int(stocklevel)
        stock.put()
        self.session['added'] = True
        self.redirect('/add_stock')


class ListStock(BaseHandler):
    def get(self):
        user = self.session.get('user')
        items = []
        costprices = []
        sellprices = []
        query = db.GqlQuery("SELECT * FROM Stock ORDER BY stockcode ASC")
        for item in query:
            cost = str(item.costprice)
            sell = str(item.sellprice)
            cost = '$' + cost[:-2] + '.' + cost[-2:]
            sell = '$' + sell[:-2] + '.' + sell[-2:]
            items.append(item)
            costprices.append(cost)
            sellprices.append(sell)
        template_values = {
            'items': items,
            'user': user,
            'cost': costprices,
            'sell': sellprices
            }
        template = jinja_environment.get_template('stocklist.html')
        self.response.out.write(template.render(template_values))


class Jobs(BaseHandler):
	def get(self):
		user = self.session.get('user')
		template_values = {
			'user': user
		}
		template = jinja_environment.get_template('jobs.html')
		self.response.out.write(template.render(template_values))
		
		
		
class EditStock(BaseHandler):
    def get(self):
        user = self.session.get('user')
        # Grab the id that was passed in with the URL
        stock = int(self.request.get('id'))
        query = db.GqlQuery("SELECT * FROM Stock \
                WHERE __key__ = KEY('Stock', :1) LIMIT 1", stock)
        template_values = {
            'stock': query[0],
            'user': user
            }
        template = jinja_environment.get_template('editstock.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        logging.info("Delete? -- %s --" % self.request.get('delete'))
        stock_id = int(self.request.get('id'))
        query = db.GqlQuery("SELECT * FROM Stock \
                WHERE __key__ = KEY('Stock', :1) LIMIT 1", stock_id)
        stock = query[0]
        if len(self.request.get('delete')) > 0:
            stock.delete()
            self.session['deleted'] = True
        else:
            stock.itemname = self.request.get('itemname')
            stock.stockcode = self.request.get('stockcode')
            stock.description = self.request.get('description')
            costprice = self.request.get('costprice')
            sellprice = self.request.get('sellprice')
            stocklevel = self.request.get('stocklevel')
            stock.supplier = self.request.get('supplier')
            # Remove $ / . from prices (assume they will be $45.26 or similar)
            cost = costprice.replace("$", "")
            # Allow for value in dollars only (45 becomes 4500)
            if not '.' in cost:
                cost += "00"
            if cost[-2] == ".":
                cost += "0"
            cost = cost.replace(".", "")
            sell = sellprice.replace("$", "")
            if not '.' in sell:
                sell += "00"
            if sell[-2] == ".":
                sell += "0"
            sell = sell.replace(".", "")
            # Now convert to a cents value for integer storage
            stock.costprice = int(cost)
            stock.sellprice = int(sell)
            # And convert the stock level to an int
            stock.stocklevel = int(stocklevel)
            stock.put()
            self.session['updated'] = True
        self.redirect('/list_stock')


class LogIn(BaseHandler):
    def get(self):
        if self.session.get('user'):
            del self.session['user']
        if not self.session.get('referrer'):
            self.session['referrer'] = \
                self.request.environ['HTTP_REFERER'] \
                if 'HTTP_REFERER' in self.request.environ \
                else '/'
        template_values = {
            }
        template = jinja_environment.get_template('login.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        user = self.request.get('user')
        self.session['user'] = user
        logging.info("%s just logged in" % user)
        self.redirect('/')


class LogOut(BaseHandler):
    def get(self):
        if self.session.get('user'):
            logging.info("%s just logged out" % self.session.get('user'))
            del self.session['user']
        self.redirect('/')


class CreateJob(BaseHandler):
    def get(self):
		user = self.session.get('user')
		query = db.GqlQuery("SELECT * FROM Customer")
		template_values = {
            'customer': query[0], #take top, we are prototyping
            'user': user
            }
		template = jinja_environment.get_template('createjob.html')
		self.response.out.write(template.render(template_values))


class Billing(BaseHandler):
	def get(self):
		user = self.session.get('user')
		items = []
		costprices = []
		sellprices = []
		query = db.GqlQuery("SELECT * FROM Stock ORDER BY stockcode ASC")
		for item in query:
			sell = str(item.sellprice)
			sell = '$' + sell[:-2] + '.' + sell[-2:]
			items.append(item)
			sellprices.append(sell)
			
		query = db.GqlQuery("SELECT * FROM Customer")
		template_values = {
            'customer': query[0], #take top, we are prototyping
            'user': user,
            'items': items,
            'sell': sellprices
            }
		template = jinja_environment.get_template('invoice.html')
		self.response.out.write(template.render(template_values))
	def post(self):
		self.redirect('/')

class Customer(db.Model):
    fname = db.StringProperty()
    lname = db.StringProperty()
    address = db.StringProperty(multiline=True)
    email = db.StringProperty()
    phone = db.StringProperty()
    postcode = db.IntegerProperty()
    pooldetails = db.StringProperty(multiline=True)
    notes = db.StringProperty(multiline=True)

class Stock(db.Model):
    itemname = db.StringProperty()
    stockcode = db.StringProperty()
    description = db.StringProperty(multiline=True)
    costprice = db.IntegerProperty()
    sellprice = db.IntegerProperty()
    stocklevel = db.IntegerProperty()
    supplier = db.StringProperty()
	
class Job(db.Model):
    customerId = db.StringProperty()
    stockId = db.StringProperty()
    
	
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'info203',
}


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', LogIn),
    ('/logout', LogOut),
    ('/add_customer', AddCustomer),
    ('/list_customers', ListCustomers),
    ('/services', Services),
    ('/contact', ContactUs),
    ('/instreet', InStreet),
    ('/add_stock', AddStock),
    ('/list_stock', ListStock),
    ('/edit_customer', EditCustomer),
    ('/update_customer', UpdateCustomer),
    ('/jobs', Jobs),
    ('/billing', Billing),
    ('/create_job', CreateJob),
    ('/edit_stock', EditStock)],
    debug=True,
    config=config)


def main():
    app.run()


if __name__ == '__main__':
    main()
