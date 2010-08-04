#!/usr/bin/env python

import logging
import simplejson as json
import os
import urllib, urllib2, urlparse

import wsgiref.handlers
import facebook

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Facebook:
  appId = '136348336398305'
  secret = '8b664e5066bd0071a52bb728371f2544'
  pageOAuthToken = '136348336398305|65ff6e8dc8fe6dcd6785297b-218471|114869201895800|uQShWWwlYsbIEtoRAriSb4Gxpj0.'
  paulOAuthToken = '136348336398305|65ff6e8dc8fe6dcd6785297b-218471|TnZAzOziZpwCdGqzBmQGztvkM_c.'

class BaseHandler(webapp.RequestHandler):
  def fetch(self, url):
    logging.error(url)
    result = urllib2.urlopen(url)
    data = json.loads(result.read())
    return data
    

class MainHandler(BaseHandler):
  def getEvents(self):
    events = self.fetch('https://api.facebook.com/method/events.get?format=json&uid=114869201895800&oauth_token='+Facebook.paulOAuthToken)
    for event in events:
      event['count'] = self.getHackCount(event['eid'])
    return events

  def getHackCount(self, eid):
    feed = self.fetch('https://graph.facebook.com/'+str(eid)+'/feed')
    return len(feed['data'])

  def get(self):
    template_values = {
      'events' : self.getEvents()
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
class EventHandler(webapp.RequestHandler):
  def get(self, eid):
     self.redirect('http://www.facebook.com/event.php?eid='+eid)

class EventSubmissionHandler(webapp.RequestHandler):
  def getFBGraph(self):
    user = facebook.get_user_from_cookie(self.request.cookies, Facebook.appId, Facebook.secret)
    if user:
      graph = facebook.GraphAPI(user["access_token"])
      return graph
    
  def getEvent(self, eid):
    result = urllib2.urlopen('https://graph.facebook.com/'+eid)
    data = json.loads(result.read())
    return data

  def getFriends(self):
    graph = self.getFBGraph()
    if graph:
      friends = graph.get_connections("me", "friends")['data']
      return sorted(friends, key=lambda friend: friend['name'])
    return []

  def getMe(self):
    graph = self.getFBGraph()
    if graph:
      return graph.get_object("me")
    return {}

  def post(self, eid):
    return self.get(eid)

  def get(self, eid):
    template_values = {
      'eid' : eid,
      'event' : self.getEvent(eid),
      'friends' : self.getFriends(),
      'me' : self.getMe(),
    }
    path = os.path.join(os.path.dirname(__file__), 'event_submit.html')
    self.response.out.write(template.render(path, template_values))


def main():
  application = webapp.WSGIApplication([('/', MainHandler),
                                        ('/([0-9]*)', EventHandler),
                                        ('/([0-9]*)/submit', EventSubmissionHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
