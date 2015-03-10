#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sqlite3 as lite
import re, sys, datetime

class DBOperate(object):
	
	def CheckExistence (self, string):
		con = lite.connect('BBHelper.db')
		cur = con.cursor();
		currentime = datetime.date.today()
		print currentime
		result = cur.execute("SELECT flightcode, timestamp FROM BBHelper_flightinfo WHERE flightcode=? AND timestamp=?", (string, currentime))
		return result
	
	def InsertData (self, flugcode, ):
		cur = con.cursor();
		cur.execute("INSERT INTO")
