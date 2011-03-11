#!/usr/bin/env python

import collections
import logging
import os, sys
import urllib, urllib2, urlparse
try:
  import simplejson as json
except:
  import json
from datetime import datetime

try:
  from secret import Facebook
except:
  print """You need to setup the application secret.

  cp secret.py.sample secret.py

Then put in your application id and secret."""
  sys.exit()

import wsgiref.handlers
import facebook

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class UserHandler(webapp.RequestHandler):
  def getFBGraph(self):
    user = facebook.get_user_from_cookie(self.request.cookies, Facebook.appId, Facebook.secret)
    if user:
      graph = facebook.GraphAPI(user["access_token"])
      try :
        me = graph.get_object("me")
      except Exception, e:
        return None
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

  def getID(self):
    return self.getMe()['id']

  def isAttending(self, eid):
    graph = self.getFBGraph()
    if graph:
      attending = graph.get_connections(eid, 'attending')['data']
      my_id = self.getID()
      for person in attending:
        if person['id'] == my_id:
          return True
    return False



class AppHandler(webapp.RequestHandler):
  def fetch(self, url, isJson=True, cached=60): # 1 minute
    logging.info('fetching: '+url)
    if cached:
      if memcache.get(url):
        return memcache.get(url)

    logging.info('cache miss: '+url)
    try:
      result = urllib2.urlopen(url)
    except urllib2.HTTPError, e:
      print '\n\n', e.geturl()
      raise e

    if isJson:
      ret = json.loads(result.read())
    else :
      ret = result.read()

    if cached:
      memcache.add(url, ret, cached)
    return ret

  def getAppOAuthToken(self):
    response = self.fetch('https://graph.facebook.com/oauth/access_token?' + urllib.urlencode({
      'grant_type': 'client_credentials',
      'client_id': Facebook.appId,
      'client_secret': Facebook.secret}), isJson=False)
    for piece in response.split('&') :
      k,v = piece.split('=')
      if k == 'access_token':
        return v
  
  def getEvents(self, page_id):
    events = self.fetch('https://graph.facebook.com/'+page_id+'/events?access_token='+self.getAppOAuthToken())['data']
    for event in events:
      # too slow...
      # event['count'] = self.getHackCount(event['id'])
      event['start_time'] = datetime.strptime(event['start_time'], "%Y-%m-%dT%H:%M:%S+0000")
      event['end_time'] = datetime.strptime(event['end_time'], "%Y-%m-%dT%H:%M:%S+0000")
    return events
    
  def getEvent(self, eid):
    return self.fetch('https://graph.facebook.com/'+eid)

  def getRawHacks(self, eid):
    data = []
    url = 'https://graph.facebook.com/'+str(eid)+'/feed'
    while 1:
      feed = self.fetch(url)
      data += feed['data']
      if feed.has_key('paging'):
        if url == feed['paging']['next']:
          # bug in facebook
          break
        url = feed['paging']['next']
      else:
        break

    return data
  
  def getHacks(self, eid):
    hacks = []
    for hack in self.getRawHacks(eid):
      if hack.has_key('application'):
        if hack['application']['id'] == Facebook.appId:
          hacks.append(hack)

    ret = []
    for hack in hacks:
      if not hack.has_key('picture') or not hack.has_key('to') or not hack['to'].has_key('data') or not hack.has_key('message') or not hack.has_key('id'):
         continue

      people = filter(lambda x: x and x.has_key('id') and x['id'] != eid, hack['to']['data'])
      msg = hack.get('message')
      banana = msg.split('Built by', 2)
      title = banana[0].replace('Hackathon Submission: ', '').strip()
      other_eid, fbid = hack['id'].split('_')
      # print '\n\n', hack

      ret.append({
        'description' : hack.get('description'),
        'link' : 'http://www.facebook.com/event.php?eid='+eid+'&story_fbid='+fbid,
        'likes' : hack.get('likes', {'count' : 0}).get('count'),
        'people' : people,
        'screenshot' : hack.get('picture'),
        'screenshot_raw' : hack.get('link'),
        'title' : title,
      })

    return ret

  def getHackCount(self, eid):
    return len(self.getHacks(eid))


class IndexHandler(AppHandler):
  def get(self):
    template_values = {
      'events' : self.getEvents('114869201895800')
    }
    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
  
  def post(self):
    return self.get()


class EventHandler(AppHandler):
  def get(self, eid):

    template_values = {
      'hacks' : self.getHacks(eid),
      'eid'   : eid,
      'event' : self.getEvent(eid),
    }
    path = os.path.join(os.path.dirname(__file__), 'event.html')
    self.response.out.write(template.render(path, template_values))

  def post(self, eid):
    return self.get(eid)


class EventRedirectHandler(webapp.RequestHandler):
  def get(self, eid):
     self.redirect('http://www.facebook.com/event.php?eid='+eid)

  def post(self, eid):
    return self.get(eid)


class EventSubmissionHandler(AppHandler, UserHandler):

  def post(self, eid):
    return self.get(eid)

  def get(self, eid):
    template_values = {
      'eid' : eid,
      'event' : self.getEvent(eid),
      'friends' : self.getFriends(),
      'me' : self.getMe(),
      'isAttending' : self.isAttending(eid),
    }
    path = os.path.join(os.path.dirname(__file__), 'event_submit.html')
    self.response.out.write(template.render(path, template_values))


def main():
  application = webapp.WSGIApplication([('/+', IndexHandler),
                                        ('/+([0-9]*)/*', EventHandler),
                                        ('/+([0-9]*)/+event', EventRedirectHandler),
                                        ('/+([0-9]*)/+submit', EventSubmissionHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
