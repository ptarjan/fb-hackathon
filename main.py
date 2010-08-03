#!/usr/bin/env python

import json
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

class MainHandler(webapp.RequestHandler):

  def getFBGraph(self):
    user = facebook.get_user_from_cookie(self.request.cookies, Facebook.appId, Facebook.secret)
    if user:
      graph = facebook.GraphAPI(user["access_token"])
      return graph
    
  def getEventName(self, eid):
    return 'Placeholder until push'
    result = urllib2.urlopen('https://graph.facebook.com/'+eid)
    data = json.loads(result.read())
    return data['name']

  def getFriends(self):
    graph = self.getFBGraph()
    friends = graph.get_connections("me", "friends")['data']
    return sorted(friends, key=lambda friend: friend['name'])

  def post(self):
    return self.get()

  def get(self):
    template_values = {
      'eid' : self.request.get('eid'),
      'event_name' : self.getEventName(self.request.get('eid')),
      'friends' : self.getFriends(),
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))


def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
