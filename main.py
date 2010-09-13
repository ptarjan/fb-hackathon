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

class BaseHandler(webapp.RequestHandler):
  def fetch(self, url, isJson=True):
    logging.error(url)
    try:
      result = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
      print '\n\n', e.geturl()
      raise e

    if isJson:
      return json.loads(result.read())
    else :
      return result.read()

  def getAppOAuthToken(self):
    response = self.fetch('https://graph.facebook.com/oauth/access_token?' + urllib.urlencode({
      'grant_type': 'client_credentials',
      'client_id': Facebook.appId,
      'client_secret': Facebook.secret}), isJson=False)
    for piece in response.split('&') :
      k,v = piece.split('=')
      if k == 'access_token':
        return v
  
  def getEvents(self):
    events = self.fetch('https://api.facebook.com/method/events.get?format=json&uid=114869201895800&oauth_token='+self.getAppOAuthToken())
    for event in events:
      event['count'] = self.getHackCount(event['eid'])
    return events
    
  def getEvent(self, eid):
    return self.fetch('https://graph.facebook.com/'+eid)

  def getHacks(self, eid):
    feed = self.fetch('https://graph.facebook.com/'+str(eid)+'/feed')
    return feed['data']

  def getHackCount(self, eid):
    return len(self.getHacks(eid))


class MainHandler(BaseHandler):
  def get(self):
    template_values = {
      'events' : self.getEvents()
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))


class EventHandler(BaseHandler):
  def get(self, eid):
    template_values = {
      'hacks' : self.getHacks(eid),
      'eid'   : eid,
      'event' : self.getEvent(eid),
    }
    path = os.path.join(os.path.dirname(__file__), 'event.html')
    self.response.out.write(template.render(path, template_values))


class EventRedirectHandler(webapp.RequestHandler):
  def get(self, eid):
     self.redirect('http://www.facebook.com/event.php?eid='+eid)

class EventSubmissionHandler(BaseHandler):
  def getFBGraph(self):
    user = facebook.get_user_from_cookie(self.request.cookies, Facebook.appId, Facebook.secret)
    if user:
      graph = facebook.GraphAPI(user["access_token"])
      return graph

  def getFriends(self):
    graph = self.getFBGraph()
    if graph:
      friends = graph.get_connections("me", "friends")['data']
      def getName(friend) :
        if friend.has_key('name'):
          return friend['name']
        return ''

      return sorted(friends, key=getName)
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
                                        ('/([0-9]*)/event', EventRedirectHandler),
                                        ('/([0-9]*)/submit', EventSubmissionHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
