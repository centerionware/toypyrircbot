# -*- coding: utf-8 -*-
#
# A simple irc bot in python created from some example found online heavily modified
# Copyright (C) 2009 Matthew Adams and some guy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
						
import sys
import socket
import string
import os #not necassary but later on I am going to use a few features from this 
import pickle
import random
import time
import urllib
import urllib2
import re

def sorter(a, b):
	return cmp(len(b[0]), len(a[0]))

class Bot:
	def __init__(self):
		self.HOST='irc.ubuntu.com' #The server we want to connect to
		self.PORT=8001 #The connection port which is usually 6667
		self.NICK='Bots-Nick' #The bot's nickname
		self.PASS='Bots-Pass' # If the nick is registered with nickserv
		self.IDENT='pybot'
		self.REALNAME='s1ash'
		self.OWNER='OxDeadC0de' #The bot owner's nick
		self.channel='OxDeadC0de' #The default self.channel for the bot to speak on.. changes every time it's spoken to.
		self.readbuffer='' #Here we store all the messages from server
		self.jobs = []
		self.ops = [] # List of room ops, detect +o and -o
		self.lastJoin = ''
		self.banned = []
		self.learned = [] # Learned objects, addarray([key, value])
		self.loadBanned()
		self.loadLearned()

	def getSubmitter(self, text):
		return text[text.find(":")+1:text.find("!n")]
	
	def getRest(self, text, marker):
		return (text[text.find(marker)+len(marker):]).strip()

	def do_learned(self, text):
		self.learned.sort(sorter)
		self.learnCommand(text)
		self.unlearn(text)
		self.alllearned(text)
		for l in self.learned:

			if( text.find(l[0]) != -1):
				rest = self.getRest(text, l[0])
				rest.strip()
				if(rest is not ""):
					rest = rest + ": "
				self.sendm(rest + l[1])
				return 1

		return 0

	def alllearned(self, text):
		if((text.lower()).find(":!commands") != -1 or (text.lower()).find(":!allcommands") != -1):
			self.channel = self.getSubmitter(text)
			out = ""
			if( not len(self.learned) ):
				out = "There are no commands available!"
			xc = 0
			for l in self.learned:
				out = out + (l[0])[1:] + " "

				xc = xc + 1
				if(xc is 10):
					xc = 0
					self.sendm(out)
					out = ""
			self.sendm(out)

	def unlearn(self, text):
		if(text.find(":!unlearn ") != -1):
			if(self.isOp(self.getSubmitter(text))):
				rest = ":!"+self.getRest(text, ":!unlearn")
				if(not self.is_learned(rest)):
					self.sendm(rest + " is not a known command!")
					return
				de = None
				for l in self.learned:
					if(l[0] == rest):
						de = l
				if(de is not None):
					self.learned.remove(de)
					self.sendm(rest + " was removed")
					self.writeLearned()

	def is_learned(self, command):
		for l in self.learned:
			if(l[0] == command): return 1
		return 0

	def real_learn_command(self, text):
		rest = self.getRest(text, ":!learn");
		first_space = rest.find(" ")
		if(first_space == -1):
			self.sendm("Usage: !learn command response")
			return
		command = ":!" + rest[:first_space]
		rest = rest[first_space+1:]
		self.learned.append([command, rest])
		self.writeLearned()
		self.sendm("Yummy Yummy in my Tummy!")

	def learnCommand(self, text):
		if(text.find(":!learn ") != -1):
			submitter = self.getSubmitter(text)
			if(self.isOp(submitter)):
				self.real_learn_command(text)

	def isOp(self, name):
		#print "is Op " + name + " "+self.channel
		if(name == self.OWNER):
			return 1
		for op in self.ops:
			if(op[0] == name and self.channel == op[1]):
				return 1
		return 0

	def isBanned(self, name):
		for b in self.banned:
			if(b.lower() == name.lower()):
				if(self.isOp(name)):
					#print "Warning, " + name + " is banned, but is an op, continueing anyway!"
					return 0
				return 1
		return 0

	def ban_user(self, name):
		if(not self.isOp(name)):
			self.banned.append(name) 
			#print "Banned " + name
			self.writeBanned()

	def unban_user(self, name):
		banned = None
		for b in self.banned:
			if(b == name):
				banned = b
		if(banned is not None):
			self.banned.remove(banned)
			#print "Unbanned " + name
			self.writeBanned()

	def joinChannel(self, channel):
		# Get list of ops:
		output = "names " + channel
		self.sock.send(output)
		self.lastJoin = channel

	def loadJobs(self):
		try:
			jobfile = open('jobs.pkl', 'r')
			self.jobs = pickle.load(jobfile)
			jobfile.close()
		except IOError:
			print "No job file, continue"
	
	def writeJobs(self, ojobs):
		jobfile = open('jobs.pkl', 'w')
		pickle.dump(ojobs, jobfile)
		jobfile.close()

	def loadBanned(self):
		try:
			jobfile = open('banned.pkl', 'r')
			self.banned = pickle.load(jobfile)
			jobfile.close()
		except IOError:
			print "No ban file, continue"
	
	def writeBanned(self):
		jobfile = open('banned.pkl', 'w')
		pickle.dump(self.banned, jobfile)
		jobfile.close()

	def loadLearned(self):
		try:
			j = open("learned.pkl", 'r')
			self.learned = pickle.load(j)
			j.close()
		except IOError:
			print "No learned file! I don't know anything"

	def writeLearned(self):
		j = open("learned.pkl", 'w')
		pickle.dump(self.learned, j)
		j.close()

	def sendm(self, msg): 
		self.sock.send('PRIVMSG '+ self.channel + ' :' + str(msg) + '\r\n')
		#print "Sending: " + 'PRIVMSG '+ self.channel + ' :' + str(msg) 

	def removeone(self, one):
		self.jobs.remove(one)
		length = len(self.jobs)
		for x in range(length):
			self.jobs[x][0] = "%s" % x

	def extractChan(self, string):
		privmsg = string.find("PRIVMSG ")
		chan =  string[privmsg+8:string.find(" :", privmsg)]
		if self.NICK == chan:
			chan = string[string.find(":")+1:string.find("!n")]
		return chan
#/** @brief bield room op list from user nick's.op's are designated by @
# *
# * @name nicklist
# *
# */
	def nicklist(self, text):
		if(text.find(self.NICK + " = " + self.lastJoin + " : ") != -1):
			#print "Name list found"
			rest = text[text.find(self.NICK + " = " + self.lastJoin + " :"):]
			nickList = rest.split(" ")
			for nick in nickList:
				#print "Nick : " + nick
				if(nick.find("@") == 0):
					#print "Op found " + nick + " " + self.lastJoin
					nick = nick[1:]
					self.ops.append([nick, self.lastJoin])

	def addOp(self, text):
		if re.match(':ChanServ!ChanServ@services\. MODE (.*) \+o', text): 
			print "adding op!"
			name = text[text.find("+o")+3:]
			name = name.strip();
			if(not self.isOp(name)):
				self.ops.append([name, self.channel])
				#print "Adding op " + name + " " + self.channel

	def remOp(self, text):
		if re.match(':ChanServ!ChanServ@services\. MODE (.*) \-o', text):#text.find(':ChanServ!ChanServ@services. MODE #php-freelance -o') == 0 or text.find(':ChanServ!ChanServ@services. MODE #php-freelance -o')== 1:
			remOp = None
			name = text[text.find("-o")+3:]
			name = name.strip();
			#print "Trying to remove op: " + name + " " + self.channel
			for op in self.ops:
				if op[0] == name and op[1] == self.channel:
					remOp = op
			if remOp is not None:
				self.ops.remove(remOp)
				#print "Removing op " + name

	def google(self, text):
		if(text.find("google ") != -1):
			rest = text[text.find("google ")+7:]
			rest = rest.strip()
			temp = { 'q':rest }
			if(len(rest) > 0): 
				self.sendm("http://www.google.com/search?" + urllib.urlencode(temp))

	def amiop(self, text):
		if(text.find(":!amiop") != -1):
			submitter = text[text.find(":")+1:text.find("!n")]
			if self.isOp(submitter):
				self.sendm("Yes, "+ submitter +" you are an op!")
			else:
				self.sendm("No, " + submitter +" you are not an op!")

	def join(self, text):
		if(text.find(":!join ") != -1):
			rest = text[text.find(":!join ")+6:]
			rest = rest.strip()
			submitter = text[text.find(":")+1:text.find("!n")]
			if self.isOp(submitter):
				#print 'Joining channel: %s' % rest
				self.sock.send('JOIN %s\r\n' % rest) 
				self.joinChannel(rest)
	def ping(self, text):
		if text.find('PING') == 0: 
			self.sock.send('PONG ' + text.split() [1] + '\r\n')

	def quit(self, text):
		if text.find(':!quit') != -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			if(self.isOp(submitter)):
				self.sock.send('QUIT :python bot\r\n')

	def bot(self, text):
		if text.find(':bot') != -1 or text.find("!bot") != -1:
			self.sendm('I are no bot . no , you are bot')

	def job(self, text):
		val = text.find(":job ")
		if (val != -1):
			ttext = text[val+5:]
			ttext = ttext.strip()
			leng = len(ttext)
			if(leng > 140): leng = 140
			ttext = ttext[0:leng]
			submitter = text[text.find(":")+1:text.find("!n")]
			self.jobs.append(["%s" % len(self.jobs), ttext, submitter])
			self.writeJobs(self.jobs)
			self.sendm("Job %s added!" % self.jobs[len(self.jobs)-1][0])

	def login(self, text):
		if text.find('NOTICE %s :This nickname is registered' % self.NICK) != -1:
			self.sock.send('PRIVMSG nickserv :identify %s\r\n' % self.PASS )

	def date(self, text):
		if text.find(':!date') != -1:
			self.sendm(''+ time.strftime("%A, %B %d, %Y", time.localtime()))

	def usage(self, text):
		if text.find(':!usage') != -1 or text.find(":!help") != -1:
			self.sendm('I am a very simple bot with simple usage. !job # to display job #, if # is omitted I will display a random job; Add a new one with: ":job your very important job" without quotes; !jobs to see the total amount of jobs; Remove your jobs with !rjob # and view your jobs with !myjobs. !job all for a full job listing! Ops can have me !ignore user and !unignore user. Type !ignored for all ignored users.')

	def time(self, text):
		if text.find(':!time') != -1:
			self.sendm(''+ time.strftime("%H:%M:%S", time.localtime()))

	def load(self, text):
		if text.find(':!load') != -1:
			self.loadJobs()
			self.sendm('job file loaded!')
	def removeJob(self, text):
		val = text.find(':!rjob ')
		if val == -1:
			val = text.find('::rjob ')
		if val != -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			rnum = text[val+6:]
			rnum = rnum.strip()
			rjob = None
			if(rnum >= 0):
				for job in self.jobs:
					if(job[0] == rnum):
						rjob = job
				if rjob is not None:
					if(submitter == rjob[2] or self.isOp(submitter)):
						self.sendm( "Job %s removed" % (rjob[0]))
						self.removeone(rjob)
						self.writeJobs(self.jobs)	

	def listJobs(self, text):
		#print "list"
		if text.find(':!list') != -1 or text.find(':!jobs') != -1:
			#print "Found list again"
			self.sendm("Total Jobs: %s " % len(self.jobs))

	def myjobs(self, text):
		if text.find(':!myjobs') != -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			self.channel = submitter
			myjobs = ""
			for job in self.jobs:
				if(job[2] == submitter):
					myjobs = job[0] + " " + myjobs
			if(myjobs == ""):
				self.sendm("You haven't submitted any jobs!")
			else:
				self.sendm("Your jobs are: %s" % myjobs)

	def ignored(self, text):
		if text.find(':!ignored') != -1:
			#submitter = text[text.find(":")+1:text.find("!n")]
			# self.channel = submitter
			ignoredusers = ""
			for ignored in self.banned:
				ignoredusers = ignoredusers + " " + ignored
			self.sendm("Ignored users: " + ignoredusers)
	def ignore(self, text):
		if text.find(':!ignore ') != -1 and text.find(":!ignored") == -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			rest = text[text.find('!ignore')+8:]
			rest = rest.strip()
			if(self.isOp(submitter)):
				self.ban_user(rest)

	def unignore(self, text):
		if text.find(':!unignore ') != -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			rest = text[text.find('!unignore')+10:]
			rest = rest.strip()
			if(self.isOp(submitter)):
				self.unban_user(rest)

	def mainJob(self, text):
		if text.find(':!job\r\n') != -1 or text.find(":!job ") != -1:
			submitter = text[text.find(":")+1:text.find("!n")]
			rest = text[text.find('!job')+5:]
			rest = rest.strip()
			if(rest.find('all ') != -1):
				#    if(text.find('#php-freelance') == -1):
					chantemp = self.channel
					self.channel = submitter;
					top = len(self.jobs)
					count = 0
					while(count != top): 
						self.sendm('Job: %s Submitted By: %s Description: %s' % (self.jobs[count][0], self.jobs[count][2], self.jobs[count][1]))
						count = count +1
					self.channel = chantemp
					
			rnum = 0
			doit = 1
			try:
				i = float(rest)
				# numeric
				rnum = int(rest)
				if rnum >= len(self.jobs) or rnum < 0:
					self.sendm('Error, invalid job number %s' % rnum)
					doit = 0

			except ValueError:
				range = len(self.jobs)
				if range > 0:
					rnum = random.randrange(0,len(self.jobs))
				else:
					rnum = 0
					doit = 0
				# not numeric
			if (len(self.jobs) == 0) or (len(self.jobs) == -1):
				self.sendm('There are no jobs, sorry!\r\n')
			else:    
				if doit == 1:
					self.sendm('Job: %s Submitted By: %s Description: %s' % (self.jobs[rnum][0], self.jobs[rnum][2], self.jobs[rnum][1]))

	def runQuery(self, text):
		print '[GET]', text
		self.nicklist( text )
		self.addOp( text )
		self.remOp( text )
		self.google( text )
		self.amiop( text )
		self.join( text )
		self.ping( text )
		self.quit( text )
		self.bot( text )
		self.job( text )
		self.login( text )
		self.date( text )
		self.usage( text )
		self.time( text )
		self.load( text )
		self.removeJob( text )
		self.listJobs( text )
		self.myjobs( text )
		self.ignored( text )
		self.ignore( text )
		self.unignore( text )
		self.mainJob( text )

	
	def main(self ):	
		
		self.loadJobs()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		self.sock.connect((self.HOST, self.PORT)) 
		
		self.sock.send('USER python host servname : Python Bot\r\n') 
		self.sock.send('NICK %s\r\n' % self.NICK) 

		
		while 1:
			text=self.sock.recv(2040)

			if not text:
				break
					
			if(text.find("PRIVMSG ") != -1):
				self.channel = self.extractChan(text)
			submitter = text[text.find(":")+1:text.find("!n")]
			if(self.isBanned(submitter)): continue
			self.do_learned(text)
			
			self.runQuery(text)

mybot = Bot()
mybot.main()
