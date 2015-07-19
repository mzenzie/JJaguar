import base64
from bson.objectid import ObjectId
import os
import urllib
import tornado.auth
import tornado.escape
import tornado.gen
import tornado.httpserver
import logging
import bson.json_util
from decorator import protected
import json
import urlparse
import time
import threading
from tornado.ioloop import IOLoop
from tornado.web import asynchronous, RequestHandler, Application
from tornado.httpclient import AsyncHTTPClient
import pymongo
from recommend import give_recommendations
import sys
sys.path.append('../')
import descriptions


class BaseHandler(RequestHandler):
    def get_login_url(self):
        return u"/auth/login/"

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if user_json:
            return tornado.escape.json_decode(user_json)
        else:
            return None
        
# Purpose: Login page checks for permission                
class AuthLoginHandler(BaseHandler):
    def get(self):
        self.render ("login.html")

    def post(self):  
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        user = self.application.db['auth_users'].find_one({username: password})

        if user:
            self.set_current_user(username)
            self.redirect('/home/')
        else:
            self.redirect(u'/register/')
        

    def set_current_user(self, user):
        if user:
            self.set_secure_cookie("user", tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")
 
# Logout page clears cookie        
class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))

class RegisterHandler(AuthLoginHandler):
    def get(self):
        self.render("register.html")
    
    def post(self):
        username = self.get_argument("username", "")
        names = list(self.application.db['auth_users'].find())
        for each in names:
            try:
                if each[username]:
                    error_msg = u"?error=" + tornado.escape.url_escape("Login name already taken")
                    self.redirect(u"/login" + error_msg)   
            except KeyError: 
                pass
        password = self.get_argument('password', '')
        user = {}
        user[username] = password
        self.application.db['auth_users'].insert_one(user)
        self.set_current_user(username)
        self.redirect('/home/')

class MainPageHandler(BaseHandler):
    @protected
    def get(self):  
	self.redirect('/home/')
	
class HomePageHandler(BaseHandler):
    @protected
    def get(self):  
	recs = []	
	conn = pymongo.MongoClient()
	db = conn['jjaguar_database']
	coll = db['account_info']
	print list(coll.find())
	
	doc = coll.find_one({'name': self.get_current_user()})
	
	print doc 
	
	if doc:
	    d = doc.get('old_rec')
	
	    for w in sorted(d, key=d.get, reverse=True):
		recs.append([w, d[w]])
	else:
	    d = {}
		
		
	self.render('home.html', user= self.get_current_user(), doc = doc, d= recs)


class AccountPageHandler(BaseHandler):
    def get(self):
	conn = pymongo.MongoClient()
	db = conn['jjaguar_database']
	coll = db['account_info']
	user = self.get_current_user()
	old_recs = {}
	exceptions = []
	skills = []
	new = True
	
        languages = []
	skills = {}
        for each in descriptions.evaluated_languages:
	    skills[each] = 0
	    languages.append(each)
	    
	user_doc = coll.find_one({'name': user})
	if user_doc:
	    old_recs = user_doc.get('old_rec')
	    exceptions = user_doc.get('exceptions')
	    skills = user_doc.get('skills')
	    new = False
	    
	else:
	    user_doc = {
	        'name': user,
	        'exceptions': [],
	        'old_rec': {},
	        'skills': skills
	    }
	    old_recs = {}
	    exceptions = []
	    coll.insert(user_doc)
	    new = True

	new_langs = []
	for each in skills:
	    new_langs.append([each, skills[each]])
	                     
	recs = []
	count = 0
	print '!!!!!!!!!!!!!!!', old_recs
	for w in sorted(old_recs, key=old_recs.get, reverse=True):
	    recs.append([w, old_recs[w]])
	
	self.render('account.html', languages = new_langs, exceptions = exceptions, old_recs = recs, user = user, new = new)
	
    def post(self):
	conn = pymongo.MongoClient()
	db = conn['jjaguar_database']
	coll = db['account_info']
	user = self.get_current_user()	
	
	languages = []
	
	skills = {}
	for each in descriptions.evaluated_languages:
	    skills[each] = 1
	    languages.append(each)
	    
	new_langs = []
	for each in skills:
	    new_langs.append([each, skills[each]])    

	user_doc = coll.find_one({'name': user})
	exceptions = user_doc['exceptions']
	word = self.get_argument('hiding').split()
	for each in word:
	    if each in exceptions:
		exceptions.remove(each)
	
	skills = user_doc.get('skills')
	rates = self.get_argument('rates')
	if rates != '':
	    rates = rates.replace(',', ' ')
	    rates = rates.split()
	    print 'rates', rates
	    for i in range(0, len(languages)):
		if str(rates[i]) != str(0):
		    r = str(rates[i]).split('-')
		    print r[0], r[1], 'hi'
		    skills[r[1]] = r[0]
		    print skills
		    
	    
	print 'SKILLS', skills
	recs = []	
	old_recs =  user_doc['old_rec']
	print old_recs
	
	count = 0
	for w in sorted(old_recs, key=old_recs.get, reverse=True):
	    recs.append([w, old_recs[w]])	

	input0 = self.get_argument('bad_lang0')
	if input0 not in exceptions and input0 != '':
	    exceptions.append(input0)	
	try:
	    input1 = self.get_argument('bad_lang1')
	    if input1 and input1 not in exceptions and input1 != '':
		exceptions.append(input1)	    
	    try:
		input2 = self.get_argument('bad_lang2')
		if input2 and input2 not in exceptions and input2 != '':
		    exceptions.append(input2)
	    except:
		print 'nope'
	except:
	    print 'nope'
	
	coll.update({'name': user}, {'$set': {'exceptions': exceptions, 'skills': skills}})

	self.redirect('/account/')

	

class LearnPageHandler(BaseHandler):
    @protected
    def get(self):
	self.render('learn.html', user = self.get_current_user())

    def post(self):
	#self.redirect('/result/')
	constraints = {}
	id_type = self.get_argument('type')
	process = self.get_argument('process')
	functional = self.get_argument('Functional')
	VM = self.get_argument("VM")
	Usage1 = self.get_argument("Usage_1")
	Usage2 = self.get_argument("Usage_2")
	Usage3 = self.get_argument("Usage_3")
	typing = self.get_argument('typing')
	
	# self.write('You chose {}, {}, {}, {}'.format(id_type, process, functional, typing))
	if id_type == 'Imperative':
	    constraints['imperative'] = 'y'
	elif id_type == "Declarative":
	    
	    constraints['imperative'] = 'n'
	    
	if process == 'Compiled':
	    constraints['compiled'] = 'y'
	elif process == "Interpreted":
	    
	    constraints['compiled'] = 'n'
	    
	if functional == 'Functional':
	    constraints['functional'] = 'y'
	
	    
	if typing == "Dynamic":
	    constraints['typing'] = 'd'
	elif typing == "Static":
	    constraints['typing'] = 's'
	    
	if VM == "JVM":
	    constraints['vm'] = 'jvm'
	elif VM == "SQVM":
	    constraints['vm'] = "squeakvm"
	
	if Usage2 == 'MobileApp':
	    constraints['phone'] = 'y'
	if Usage1 == "Game":
	    constraints['game'] = 'y'
	if Usage3 == 'UtilityScripts':
	    constraints['utility'] = 'y'
	
	conn = pymongo.MongoClient()
	db = conn['jjaguar_database']
	coll = db['account_info']
	profile = coll.find_one({'name': self.get_current_user()})

	result = give_recommendations(profile, constraints)
	final = []
	for w in sorted(result, key=result.get, reverse=True):
	    final.append([w, result[w]])
	coll.update({'name': self.get_current_user()}, {'$set': {'old_rec': result}})
	self.render('result.html', user = self.get_current_user(), result = final)
	
class ResultPageHandler(BaseHandler):
    @protected
    def get(self):
	self.render('result.html',self.get_current_user())
    def post(self):
	constraints = {}

	
class DefPageHandler(BaseHandler):
    @protected
    def get(self):
	doc = {"name": "azheng", "skill": {"python": 7, "c": 3}, "old_recs":{"c": 90, "python": 10}}
	d = doc['old_recs']	
	self.render('definition.html', user = self.get_current_user(),  d = d)