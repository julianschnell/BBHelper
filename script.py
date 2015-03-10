#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import mechanize, urllib, urllib2, string, time, re, random, lxml.html, sys
from BBHelper.BBFlight import FindFlight
from BBHelper.DBops import DBOperate
import cv2, numpy ##für Imagerecognition!


## Lade Browser-Instanz, öffne Website und speicher Antwort in Variable page
url = 'https://www.germanwings.com/skysales/BlindBooking.aspx'
br = mechanize.Browser()

br.addheaders = [("Content-type", "text/html, charset=utf-8")]
br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11')]
br.set_handle_robots(False)
br.open(url, timeout=5)
##br._factory.is_html = True
response = br.response().read()
page = response

def findOptions(controlname):   ## findet items innerhalb eines Control-Panels und gibt diese aus!
    opt1 = []
    for item in br.form.find_control(controlname).items:
        opt1.append(item.name)
    return opt1

def checkdate (date):   ## überprüft, ob das gegebene Datum date ein gültiges Datum ist!
    year = int(date[:4])
    month = int(date[5:7])
    day = int(date[8:])
    if (len(date) == 10) and (date[4] == '/') and (date[7] == '/') and (year in range(2014, 2015)) and (month in range(1, 13)) and ((day in range(1,32) and month in range(1,8,2)) or (day in range(1,32) and month in range(8,13,2)) or (day in range(1,31) and month in range(4,7,2)) or (day in range(1,31) and month in range(9,12,2)) or (month == 2 and day in range(1,29))):
        return True
    else:
        return False

def correctdate (olddate):  ## wandelt das gegebene Datum olddate um, und gibt das neue, umgestellte Datum zurück
    newdate = olddate[:4]+'-'+olddate[5:7]+'-'+olddate[8:]
    return newdate

## LESE ALLE FORMS AUF DER SEITE AUS

##for form in br.forms():
##    form.set_all_readonly(False)
##    print form

print br.response().geturl()
print br.response().info()

br.select_form(nr=1)
br.form.set_all_readonly(False)

## LESE ALLE BB-ABFLUGHÄFEN AUS UND SPEICHER SIE ALS LISTE IN departures!
departures = findOptions('departure-station-radio-slider')
clusters = findOptions('clusteridtoggle')

LoadBB = FindFlight()
clusterdict, clusternames = LoadBB.LoadBB_Cluster(page, departures, response)
LoadDes = FindFlight()
cluster_deselect = LoadDes.LoadDeselects(response)
LoadGoal = FindFlight()
iatacodes = LoadGoal.LoadDestinations(response)
iatacodes['CGN'] = 'Köln/Bonn'
iatacodes['HAJ'] = 'Hannover'
iatacodes['DUS'] = 'Düsseldorf'

##print iatacodes, len(iatacodes), len(clusterdict)
print
print ('mögliche Abflughäfen:')
print ('---------------------')
print
for key in clusterdict:
    iata = key
    print key,
    for k in iatacodes:
        if k == iata:
            print iatacodes[key]
        else:
            continue
print    
s = raw_input('Abflughafen auswählen (für Köln/Bonn z.B. CGN): ')

while True:
    s = string.upper(s)
    if s in clusterdict:
        break
    else:
        s = raw_input('Falsche Eingabe, bitte wiederholen: ')

clusters = {}
i = 1
dep_airport = s   ##aenderung!
for value in clusterdict[s]:
    clusters[i] = value
    i += 1
    
print
print
print 'BlindBooking-Programme ab '+iatacodes[s]+' ('+s+'):'
print
for key, value in clusters.items():
    print
    print str(key) + ' ' + clusternames[value]
    list = cluster_deselect[value]
    print ('-------------------')
    for item in list:
        print iatacodes[item]
    print

print
print    

zahl = raw_input('Bitte BlindBooking-Programm wählen (z.B. 1 für '+clusternames[clusters[1]]+'): ')


while True:
    zahl = int(zahl)
    if zahl in clusters:
        break
    else:
        zahl = raw_input('Falsche Eingabe, bitte wiederholen (z.B. 1 für '+clusternames[clusters[1]]+'): ')

print
print 'Im Programm '+clusternames[clusters[zahl]]+' werden folgende Ziele angeflogen:'
list = cluster_deselect[clusters[zahl]]
for i in list:
    print iatacodes[i]+' ('+i+')'

s = raw_input ('Wieviele Ziele sollen ausgeschlossen werden? (0 für keine, max. '+str(len(list)-3)+'): ')

deselection = []
while True:
    s = int(s)
    if s == 0:
        break
    elif s <= len(list)-3: ##es müssen 3 Ziele mindestens übrigbleiben!
        for i in range(1,int(s)+1):
            deselect = raw_input(str(i)+'. Ziel, das ausgeschlossen werden soll (z.B. '+list[0]+' für '+iatacodes[list[0]]+'): ')
            while True:
                deselect = string.upper(deselect)
                if deselect in list:
                    deselection.append(list.pop(list.index(deselect)))
                    break
                else:
                   deselect = raw_input('Eingabe war nicht korrekt, bitte wiederholen (z.B. '+list[0]+' für '+iatacodes[list[0]]+'): ')
        break
    else:
        s = raw_input ('Falsche Eingabe, bitte wiederholen (0 für keine!): ')

print
print
fromdate = raw_input('Abflugdatum (JJJJ/MM/TT): ')

while True:
    if checkdate(fromdate) == True:
        break
    else:
        fromdate = raw_input('Abflugdatum (JJJJ/MM/TT): ')

print
todate = raw_input('Rückflugdatum (JJJJ/MM/TT): ')

while True:
    if checkdate(todate) == True:
        break
    else:
        todate = raw_input('Rückflugdatum (JJJJ/MM/TT): ')
        
clusterid = clusters[zahl]      ## z.B. '24' für Cluster Nr. 24

'''
forms = [f for f in br.forms()]
print forms

br.form.set_all_readonly(False)
for control in br.form.controls:
       if not control.name:
           print " - (type) =", (control.type)
           continue  
       print " - (name, type, value) =", (control.name, control.type, br[control.name])
'''

## AB HIER SETZEN WIR DATEN EIN!
br['fromdate'] = fromdate
br['todate'] = todate
br['clusterid'] = clusterid
while True:
    if len(deselection) >= 1:
        br['deselection'] = deselection
        break
    else:
        break


response = br.submit()
BB = response.read()
##print page


## DIE FOLGENDEN ZEILEN WERDEN HIER AUSKOMMENTIERT, DA ICH DEN BB-SITZPLAN ÜBER SCREENSHOTS EINLESEN WILL UND NICHT ÜBER DAS AUSLESEN DER WEBSEITE
'''
Sitzplan_Hin = FindFlight()
hinflug = Sitzplan_Hin.searchSeats(BB, 1)
hinflug = [int(i) for i in hinflug]
Sitzplan_Zurueck = FindFlight()
rueckflug = Sitzplan_Zurueck.searchSeats(BB, 2)
rueckflug = [int(i) for i in rueckflug]
if len(hinflug) == 0 or len(rueckflug) == 0:        ## checkt, ob Sitzpläne geladen werden konnten
    print 'Fehler! Es konnte kein Flug geladen werden. Dies kann verschiedene Gründe haben:'
    print '- Zu diesen Daten gibt es leider keinen BlindBooking-Flug'
    print '- Es wurden zu viele Flugziele ausgeschlossen'
    sys.exit()
print "Sitzplan Hinflug", hinflug
print "Sitzplan Rückflug", rueckflug
'''



## ---------------------------------------------------------------------------
## ---------------------------------------------------------------------------
## ---------------------------------------------------------------------------
## ---------------------------------------------------------------------------

browse = mechanize.Browser() 
browse.addheaders = [("Content-type", "text/html, charset=utf-8")]
browse.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11')]
browse.set_handle_robots(False)

hin_dict = {}
rueck_dict = {}
NoFlightlist = []
o = {}
r = {}
for item in list:
    print
    print 'Suche Flüge von '+dep_airport+' nach '+item
    url = "https://www.germanwings.com/skysales/Deeplink.aspx?o="+dep_airport+"&d="+item+"&t=r&adt=1&chd=0&inf=0&lng=de-DE&od="+correctdate(fromdate)+"&rd="+correctdate(todate)
    print ('Loading website now...')
    print url
    while True:
        browse.open(url,timeout=5)
        ##browse._factory.is_html = True
        print ('Opening website!')
        response1 = browse.response()
        sitecontent = response1.read()
        if (dep_airport in sitecontent) and (item in sitecontent):
            print "in der if-clause! -> Alles OKAY! :-)"
            break
        else:
            print sitecontent
            time.sleep(10)
        time.sleep(3)
    print "Content ist da! Jetzt wird geparsed!"
    html = lxml.html.fromstring(sitecontent)
    print "Und los geht die Sucherei..."
    
    i = 1
    ##HINFLUG
    NoFlight = False
    while True:
        out_flightlist = []
        ret_flightlist = []
        flugda = html.xpath('//*[@id="FlightSelectionNew"]/div[3]/div[1]/div[1]/table/tbody')
        anz_hinflug = len(flugda[0])
        print "Anzahl der Hinflüge: ", anz_hinflug-1

        try:  ##NoFlights-Condition!
            if ("NoFlights" in flugda[0][2].attrib['class']) or ("NoFlights" in flugda[0][4].attrib['class']):
                print "Kein Flug vorhanden!"
                NoFlight = True
                break
            else:
                pass
        except IndexError:
            print "Flüge verfügbar! -> Weitermachen!"
            pass
        except KeyError:
            print "Flüge verfügbar! -> Weitermachen!"
            pass
        
        for i in range(1, anz_hinflug):
            try:  ##via-Condition!
                if "viaLink" in flugda[0][i][0][0][2][0][1].attrib['id']:
                    print "StopOver-Flug..."
                    continue
                else:
                    pass
            except KeyError:
                print "Hier liegt ein KeyError vor wo eigentlich kein KeyError sein sollte...Nachschauen!"
                pass
            except IndexError:
                pass
        
            ##NoFares-Condition!
            if "NoFares" in flugda[0][i][1][0].attrib['class']:  ##BASIC-Fare ausverkauft!
                if "NoFares" in flugda[0][i][2][0].attrib['class']:  ##SMART-Fare ausverkauft!
                    continue ##Weiter zum nächsten Flug!
                elif "Amount" in flugda[0][i][2][0].attrib['class']: ##SMART-Fare verfügbar!
                    preis_dep = flugda[0][i][2][0].text
                    if flugda[0][i][2][3].text == None: ##FALLS DER TARIF SMART-FLEX ist, befinden sich die Daten woanders!
                        tarif_dep = flugda[0][i][2][7].text
                        flugcode_dep = flugda[0][i][2][5].text
                    else:
                        tarif_dep = flugda[0][i][2][5].text
                        flugcode_dep = flugda[0][i][2][3].text
                else:
                    print "FEHLER in der NoFares-Condition! 1"
            elif "Amount" in flugda[0][i][1][0].attrib['class']: ##BASIC-Fare verfügbar!
                preis_dep = flugda[0][i][1][0].text
                tarif_dep = flugda[0][i][1][5].text
                flugcode_dep = flugda[0][i][1][3].text
            else:
                print "FEHLER in der NoFares-Condition! 2"
            
            ##Daten auslesen!
            flugzeit_dep = flugda[0][i][0][0][0].text
            flugzeug_dep = flugda[0][i][0][0][2].text
            print "Flugzeit: ", flugzeit_dep
            print "Flugzeug: ", flugzeug_dep
            print "Preis: ", preis_dep
            print "Tarif: ", tarif_dep
            print "Flightcode: ", flugcode_dep
            print
            hin_dict[flugcode_dep] = dep_airport, item, flugzeit_dep, preis_dep, flugzeug_dep, tarif_dep
            out_flightlist.append(flugcode_dep)
        print out_flightlist
        break
    if NoFlight == True:  ##Diese if-Clause bewirkt, dass wenn kein Hinflug verfügbar ist, direkt das nächste Ziel geladen wird, anstatt die Rückflüge noch auszulesen!
        NoFlightlist.append(item)
        continue
    ##############
    
    ##RUECKFLUG
    i = 1
    flugda = html.xpath('//*[@id="FlightSelectionNew"]/div[3]/div[1]/div[2]/table/tbody')
    anz_rueckflug = len(flugda[0])
    while True:
        print
        print "Anzahl der Rückflüge: ", anz_rueckflug-1
        NoFlight = False
        
        try:  ##NoFlights-Condition!
            if ("NoFlights" in flugda[0][2].attrib['class']) or ("NoFlights" in flugda[0][4].attrib['class']):
                print "Kein Flug vorhanden!"
                NoFlight = True
                break
            else:
                pass
        except IndexError:
            print "Flüge verfügbar! -> Weitermachen!"
            pass
        except KeyError:
            print "Flüge verfügbar! -> Weitermachen!"
            pass
        
        for i in range(1, anz_rueckflug):
            try:  ##via-Condition!
                if "viaLink" in flugda[0][i][0][0][2][0][1].attrib['id']:
                    print "StopOver-Flug..."
                    continue
            except KeyError:
                print "Hier liegt ein KeyError vor wo eigentlich kein KeyError sein sollte...Nachschauen!"
                pass
            except IndexError:
                pass
        
            ##NoFares-Condition!
            if "NoFares" in flugda[0][i][1][0].attrib['class']:  ##BASIC-Fare ausverkauft!
                if "NoFares" in flugda[0][i][2][0].attrib['class']:  ##SMART-Fare ausverkauft!
                    continue ##Weiter zum nächsten Flug!
                elif "Amount" in flugda[0][i][2][0].attrib['class']: ##SMART-Fare verfügbar!
                    preis_ret = flugda[0][i][2][0].text
                    tarif_ret = flugda[0][i][2][5].text
                    flugcode_ret = flugda[0][i][2][3].text
                else:
                    print "FEHLER in der NoFares-Condition! 1"
            elif "Amount" in flugda[0][i][1][0].attrib['class']: ##BASIC-Fare verfügbar!
                preis_ret = flugda[0][i][1][0].text
                tarif_ret = flugda[0][i][1][5].text
                flugcode_ret = flugda[0][i][1][3].text
            else:
                print "FEHLER in der NoFares-Condition! 2"
            
            ##Daten auslesen!
            flugzeit_ret = flugda[0][i][0][0][0].text
            flugzeug_ret = flugda[0][i][0][0][2].text
            print "Flugzeit: ", flugzeit_ret
            print "Flugzeug: ", flugzeug_ret
            print "Preis: ", preis_ret
            print "Tarif: ", tarif_ret
            print "Flightcode: ", flugcode_ret
            print
            rueck_dict[flugcode_ret] = flugzeit_ret, preis_ret, flugzeug_ret, tarif_ret
            ret_flightlist.append(flugcode_ret)
        print ret_flightlist
        print
        break
    if NoFlight == True:
        NoFlightlist.append(item)
        continue
    
    if min(len(out_flightlist),len(ret_flightlist)) == 0: ##checken, ob aufgrund der via-Condition kein Hin- und/oder Rückflug verfügbar ist, wenn ja, zur nächsten Destination!
        NoFlightlist.append(item)
        continue
            
    Sitzplatz = FindFlight()

    i = -1
    while True:
        i += 1
        if i < min(len(out_flightlist),len(ret_flightlist)):
            outgoing_flight = out_flightlist[i]
            return_flight = ret_flightlist[i]
        if i >= min(len(out_flightlist),len(ret_flightlist)):
            if i == max(len(out_flightlist),len(ret_flightlist)):
                break
            if len(out_flightlist) > len(ret_flightlist):
                outgoing_flight = out_flightlist[i]
                return_flight = ret_flightlist[len(ret_flightlist)-1]
            if len(out_flightlist) < len(ret_flightlist):
                outgoing_flight = out_flightlist[len(out_flightlist)-1]
                return_flight = ret_flightlist[i]
            if (len(out_flightlist) == len(ret_flightlist) and (i == len(out_flightlist))) or (len(out_flightlist) == len(ret_flightlist) and (i == len(ret_flightlist))):
                break
        elif i == max(len(out_flightlist),len(ret_flightlist)):
            break
            print ('Selecting flight')
            ## HIER MUSS JETZT DER NEUE CODE REIN!!!
        
        print('-------------')
        print outgoing_flight
        print ('---')
        print return_flight
        print ('------------')
        try:
            result1, result2 = FindFlight().FillFormAndGo (url, dep_airport, item, outgoing_flight, return_flight, fromdate, todate)
        except mechanize._mechanize.BrowserStateError, e:
            print 'Browser hängt, versuche es in 5 Sekunden erneut! Fehlermeldung: ', e
            time.sleep(5)
            result1, result2 = FindFlight().FillFormAndGo (url, dep_airport, item, outgoing_flight, return_flight, fromdate, todate)
        except mechanize._form.ControlNotFoundError, e:
        	print 'Control-Element nicht gefunden, versuche es in 5 Sekunden erneut! Fehlermeldung: ', e
        	time.sleep(5)
        	result1, result2 = FindFlight().FillFormAndGo (url, dep_airport, item, outgoing_flight, return_flight, fromdate, todate)
        print
        print
        print i,". Durchgang vom Sitzplan auslesen!"
        print '-----------'
        print 'Sitzplan von Flug ', outgoing_flight
        print result1
        o[outgoing_flight] = result1            ## hier wird der Hinflug-Sitzplan mit dem Flightcode in dem dict o gespeichert!
        print
        print 'Sitzplan von Flug ', return_flight
        print result2
        r[return_flight] = result2              ## hier wird der Rückflug-Sitzplan mit dem Flightcode in dem dict r gespeichert!

print
if len(NoFlightlist)>0:
    print "Folgende Destinationen müssen nicht ausgeschlossen werden, da an den gewählten Daten mind. eine Strecke nicht bedient wird:"
    for flughafen in NoFlightlist:
        print flughafen
print

while True:
    print 'DIE SITZPLÄNE SIND GELADEN! JETZT ÜBER DIE WEBSEITE DAS BB-ANGEBOT ANWÄHLEN UND SCREENSHOTS DER SITZPLÄNE MACHEN!'
    datei_hin = raw_input('SITZPLAN HINFLUG - Bitte Dateinamen eingeben: ')
    LeseDatei = FindFlight()
    hinflug, rows_hin = LeseDatei.ImgRec(datei_hin)
    print 'Sitzplan für den Hinflug eingelesen!'
    print "Eingelesener Hinflug-Sitzplan: ", hinflug
    print
    datei_rueck = raw_input('SITZPLAN RÜCKFLUG - Bitte Dateinamen eingeben: ')
    rueckflug, rows_rueck = LeseDatei.ImgRec(datei_rueck)
    print 'Sitzplan für den Rückflug eingelesen!'
    print "Eingelesener Rückflug-Sitzplan: ", rueckflug
    print
    Compare = FindFlight()
    print 'Vergleiche Hinflüge...'
    PassenderHinflug = Compare.Match(hinflug,o, rows_hin)
    print 'Mögliche Hinflüge...'
    for k in PassenderHinflug:
        print k
    print
    print 'Vergleiche Rückflüge...'
    PassenderRueckflug = Compare.Match(rueckflug,r, rows_rueck)
    print 'Mögliche Rückflüge...'
    for l in PassenderRueckflug:
        print l
    print
    print '--------------'
    retry = raw_input('Weitere Sitzpläne einlesen (j/n)? ')
    if retry == 'n':
        break
    else:
        continue
    

'''
count = 0
while True:
    if count == 10:
        break
    else:
        count += 1
        
        url = 'https://www.germanwings.com/skysales/BlindBooking.aspx'
        br = mechanize.Browser()

        br.addheaders = [("Content-type", "text/html, charset=utf-8")]
        br.addheaders = [('User-agent', 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)')]
        br.set_proxies ({"http": "5.9.117.186:3128"})
        br.set_handle_robots(False)
        br.open(url)
        response = br.response().read()
        page = response
        ##print br.response().geturl()
        ##print br.response().info()
        time.sleep(1)
        ##response1 = browse.back()
        ##response1.get_data()

        br.select_form(nr=1)
        forms = [f for f in br.forms()]
        br.form.set_all_readonly(False)
        ##br.select_form(nr=1)
        ##br.form.set_all_readonly(False)

        br['fromdate'] = fromdate
        br['todate'] = todate
        br['clusterid'] = clusterid
        while True:
            if len(deselection) >= 1:
                br['deselection'] = deselection
                break
            else:
                break
        response = br.submit()
        BB = response.read()
        ##print page
        Sitzplan_Hin = FindFlight()
        hinflug = Sitzplan_Hin.searchSeats(BB, 1)
        hinflug = [int(i) for i in hinflug]
        Sitzplan_Zurueck = FindFlight()
        rueckflug = Sitzplan_Zurueck.searchSeats(BB, 2)
        rueckflug = [int(i) for i in rueckflug]
        if len(hinflug) == 0 or len(rueckflug) == 0:        ## checkt, ob Sitzpläne geladen werden konnten
            print 'Fehler! Es konnte kein Flug geladen werden. Dies kann verschiedene Gründe haben:'
            print '- Zu diesen Daten gibt es leider keinen BlindBooking-Flug'
            print '- Es wurden zu viele Flugziele ausgeschlossen'
        
        print
        print str(count)+'. Check'
        print "----"
##        print "Sitzplan Hinflug", hinflug
##        print "Sitzplan Rückflug", rueckflug
        print 'Vergleiche Hinflüge...'
        Compare = FindFlight()
        PassenderHinflug = Compare.Match(hinflug,o)
        print
        print 'Vergleiche Rückflüge...'
        PassenderRueckflug = Compare.Match(rueckflug,r)
'''