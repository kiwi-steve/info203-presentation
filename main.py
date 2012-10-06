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
                        Sorry! We're not in your area.</div>")
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
        template = jinja_environment.get_template('entername.html')
        self.response.out.write(template.render(template_values))

    def post(self):
        customer = Customer()
        customer.fname = self.request.get('fname')
        customer.lname = self.request.get('lname')
        customer.address = self.request.get('address')
        customer.put()
        self.session['added'] = True
        self.redirect('/add_customer')


class ListCustomers(BaseHandler):
    def get(self):
        user = self.session.get('user')
        customers = []
        query = db.GqlQuery("SELECT * FROM Customer ORDER BY lname ASC")
        for customer in query:
            customers.append(customer)
        template_values = {
            'customers': customers,
            'user': user
            }
        template = jinja_environment.get_template('customerlist.html')
        self.response.out.write(template.render(template_values))


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


class Customer(db.Model):
    fname = db.StringProperty()
    lname = db.StringProperty()
    address = db.StringProperty(multiline=True)
    postcode = db.IntegerProperty()
    pooldetails = db.StringProperty(multiline=True)


class Stock(db.Model):
    itemname = db.StringProperty()
    stockcode = db.StringProperty()
    description = db.StringProperty(multiline=True)
    costprice = db.IntegerProperty()
    sellprice = db.IntegerProperty()
    stocklevel = db.IntegerProperty()
    supplier = db.StringProperty()


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
    ('/list_stock', ListStock)],
    debug=True,
    config=config)


def main():
    app.run()


if __name__ == '__main__':
    main()
