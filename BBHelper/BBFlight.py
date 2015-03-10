#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import re, mechanize, sys, cv2, numpy, time

class FindFlight(object):

    def correctdate (self, olddate):
        newdate = olddate[6:]+'-'+olddate[:2]+'-'+olddate[3:5]
        return newdate

    def LoadFlights(self, flightschedule, date):          ##früher SearchFlights
        options = [item.name for item in flightschedule.items]
        flights = []
        deptimes = []
        ##print ('Looking for flights..')
        for item in options:
            m = re.match("\d{1}~[A-Z]{1}~~[A-Z]{1}~\d{1,4}~~\d{1}~[A-Z]{1}[|]\d{1}[A-Z]{1}~..\d{2}~\s~~[A-Z]{3}~\d{2}.\d{2}.\d{4}\s\d{2}.\d{2}~[A-Z]{3}~\d{2}.\d{2}.\d{4}\s\d{2}.\d{2}~", str(item))
##21.07.2013            m = re.match("\d{1}~[A-Z]~[A-Z]{1,5}~\d{4}~~None~X.4U~..\d{2}~\s~~[A-Z]{3}~"+date+"\s\d{2}:\d{2}~[A-Z]{3}~\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}", str(item))
            if m:
                m = re.search("\d{2}:\d{2}.", item)
                if m.group(0) in deptimes:
                    continue
                else:
                    deptimes.append(m.group(0))        
                flights.append(item)
        return flights

    def searchSeats(self, page, n):     ## n is 1(Hinflug) or 2(Rueckflug)
        string = '<input type="hidden" id="SeatSelection_Flight_' + str(n)
        startpos = page.find(string)
        row = ['F','E','D','C','B','A']
        seatingmap = []
        for key in row: 
            i = 1       
            while True:  ##26=Anzahl der Sitzreihen
                try:                    
                    start = page.find('<img id="Seat_' + str(i) + key + '_Flight_' +str(n), startpos)
                    if ((start == -1) and (i == 13)) or ((start == -1) and (i == 17)):  ## falls die Sitzreihe 13 bzw. 17 nicht existiert, gehe zur nächsten Sitzreihe!
                        i += 1
                        continue
                    startseat = page.find('"',start)
                    endseat = page.find('"',startseat+1)
                    seatstatus = page[startseat+1:endseat]
                    if (seatstatus == 'Seat_'+str(i)+key+'_Flight_'+str(n)+'_Occupied') or (seatstatus == 'Seat_'+str(i)+key+'_Flight_'+str(n)+'_Missing'):
##21.07.2013                    if seatstatus == 'Seat_'+str(i)+key+'_Flight_'+str(n)+'_Occupied': ##ursprünglich: (len(seatstatus) == 25) or (len(seatstatus) == 26):
                        seatingmap.append(1)      ## Occupied
                    elif seatstatus == 'Seat_'+str(i)+key+'_Flight_'+str(n):            ## ursprünglich: (len(seatstatus) == 16) or (len(seatstatus) == 17):
                        seatingmap.append(0)      ## available
                    else:
                        break                   ##seatingmap.append('E')      ## Error!    
                    startpos = endseat+1
                    i += 1          ## print (seatstatus)
                except Exception, e:
                    print 'Error:', e
        return seatingmap

    def LoadBB_Cluster(self, page, departures, response):
        global clusterdict
        global clusternames
        clusterdict = {}
        clusternames = {}
        for key in departures:    ##dh momentan 3 Mal, für CGN, HAJ, STR
            page = response
            clusternr = []
            while True:         ## Schleife läuft bis ans Ende der Webseite und speichert jedes Mal die Clusternr des BB-Programms in die Liste clusternr ab, welche dann an das Dict clusterDict übergeben wird!
                startpos = page.find('<div class="cluster cds_'+str(key)+'" id="cluster')
                startclusternr= page.find('cluster_',startpos)
                if startclusternr == -1:
                    break

                ## AUSLESEN DER CLUSTERNUMMERN
                endclusternr = page.find('"',startclusternr+8)
                cluster = page[startclusternr+8:endclusternr]
                clusternr.append(cluster)

                ## AUSLESEN DER BB-PROGRAMM-NAMEN
                startname = page.find('<label class="name">',endclusternr)
                endname = page.find('</label>',startname+20)
                name = page[startname+20:endname]
                clusternames[cluster] = str(name)
                page = page[endname:]    
            clusterdict[key] = clusternr
        return clusterdict, clusternames

    def LoadDeselects(self, response):
        global cluster_deselect
        cluster_deselect = {}
        for key in clusternames:
            page = response
            airports_deselect = []
            while True:
                ## AUSLESEN DER AUSSCHLUSSZIELE INNERHALB DES PROGRAMMS
                startpos = page.find('class="deselectoption" id="deselect_'+str(key))
                if startpos == -1:
                    break
                startdeselect = page.find('value="',startpos)
                enddeselect = page.find('"',startdeselect+7)
                deselect = page[startdeselect+7:enddeselect]
                airports_deselect.append(deselect)
                page = page[enddeselect:]
            cluster_deselect[key] = airports_deselect
        return cluster_deselect
            
    def LoadDestinations(self, response):
        page = response
        iatacodes = {}
        while True:
            ## AUSLESEN DER FLUGHAFENKÜRZEL UND -NAMEN, ZUERST IATA-CODES DANN DIE NAMEN
            startposiata = page.find('name="deselection" value=')
            if startposiata == -1:
                break
            startiata = page.find('"',startposiata+20)
            endiata = page.find('"',startiata+1)
            iata = page[startiata+1:endiata]

            startairport_name = page.find('>',endiata)
            endairport_name = page.find('</label>',startairport_name+1)
            airportname = page[startairport_name+1:endairport_name]
            iatacodes[iata] = str(airportname)
            page = page[endairport_name:]
        return iatacodes

    def Match (self, bb_flight, re_flight, rows_bb):
        bb_totalseats = len(bb_flight)
        bb_row = bb_totalseats/rows_bb
        resp = []
        for key, value in re_flight.items():
            re_totalseats = len(re_flight[key])   
            if re_totalseats == bb_totalseats:
                print ('Aktueller Key: '+key)
                i = -1
                for j in value:     ## j ist ein Element in i (i=value, also ein String!)
                    i += 1
                    print i, j, bb_flight[i]
                    if (j == 1) and (bb_flight[i] == 0) and (rows_bb == 4): ##In diese if-Condition reingehen, wenn der Flieger 4 Sitzreihen hat!
                        if (i in range(0, 4)) or (i in range(bb_row, bb_row+4)) or (i in range(2*bb_row, 2*bb_row+4)) or (i in range(3*bb_row, 3*bb_row+4)):
                            ##print "In der "+str(i)+". Sitzreihe! ..."
                            continue
                        else:
                            break
                    if (j == 1) and (bb_flight[i] == 0) and (rows_bb == 6): ##In diese if-Condition reingehen, wenn der Flieger 6 Sitzreihen hat!
                        if (i in range(0, 3)) or (i in range(bb_row, bb_row+3)) or (i in range(2*bb_row, 2*bb_row+3)) or (i in range(3*bb_row, 3*bb_row+3)) or (i in range(4*bb_row, 4*bb_row+3)) or (i in range(5*bb_row, 5*bb_row+3)):
                            ##print "6 lines...In der "+str(i)+". Sitzreihe! ..."
                            continue
                        else:
                            break
                    if i == len(bb_flight)-1:
                        print key          ##('Der Flug passt!')
                        resp.append(key)     ## wenn es der richtige Flug ist, gebe den Flightcode an resp weiter
            else:
                pass
        return resp

    def FillFormAndGo (self, url, dep_airport, item, outgoing_flight, return_flight, fromdate, todate):
        browse = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True)) 
        browse.addheaders = [("Content-type", "text/html, charset=utf-8")]
        browse.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11')]
        browse.set_proxies ({"http": "5.9.117.186:3128"})
        browse.set_handle_robots(False)
        response = browse.open(url,timeout=5)
        sitecontent = response.read()
        response1 = browse.response()
        ##print response1.read()
        '''
        for form in browse.forms():
        	print "Form name:", form.name
        	print form
        '''
        ##print '1'    
        try:
            browse.form = list(browse.forms())[0]
        except mechanize._mechanize.BrowserStateError:
            print 'Ladefehler, neuer Versuch in 5 Sekunden!'
            time.sleep(5)
            browse = mechanize.Browser(factory=mechanize.DefaultFactory(i_want_broken_xhtml_support=True)) 
            browse.addheaders = [("Content-type", "text/html, charset=utf-8")]
            browse.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.2; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.47 Safari/536.11')]
            browse.set_proxies ({"http": "5.9.117.186:3128"})
            browse.set_handle_robots(False)
            response = browse.open(url,timeout=5)
            sitecontent = response.read()
            response1 = browse.response()
            browse.form = list(browse.forms())[0]
        ##print '2'
        ##print '3'
        control3 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListFareTypes')
        control3.readonly = False
        control3.value = 'R'
        control4 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketDateRange1')
        control4.readonly = False
        control4.value = '6|6'
        control5 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketDateRange2')
        control5.readonly = False
        control5.value = '6|6'
        control6 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketDay1')
        control6.readonly = False
        control6.value = fromdate[-2:],	##JJJJ/MM/TT
        control7 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketDay2')
        control7.readonly = False
        control7.value = todate[-2:],
        control8 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketMonth1')
        control8.readonly = False
        control8.value = fromdate.replace("/","-")[:7],
        control9 = browse.form.find_control('AvailabilitySearchInputSelectView$DropDownListMarketMonth2')
        control9.readonly = False
        control9.value = todate.replace("/","-")[:7],
        '''
        AvailabilitySearchInputSelectView$DropDownListPassengerType_ADT=
        AvailabilitySearchInputSelectView$DropDownListPassengerType_CHD=
        AvailabilitySearchInputSelectView$DropDownListPassengerType_INFANT=

        '''
        control10 = browse.form.find_control('AvailabilitySearchInputSelectView$RadioButtonMarketStructure')
        control10.readonly = False
        control10.value = 'RoundTrip',
        control11 = browse.form.find_control('AvailabilitySearchInputSelectView$TextBoxMarketDestination1')
        control11.readonly = False
        control11.value = item
        control12 = browse.form.find_control('AvailabilitySearchInputSelectView$TextBoxMarketOrigin1')
        control12.readonly = False
        control12.value = dep_airport
        control13 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$HiddenFieldSearchNextFlightsOutwardDays')
        control13.readonly = False
        control13.value = '1'
        control14 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$HiddenFieldSearchNextFlightsReturnDays')
        control14.readonly = False
        control14.value = '1'
        control15 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$HiddenFieldSearchPreviousFlightsOutwardDays')
        control15.readonly = False
        control15.value = '1'
        control16 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$HiddenFieldSearchPreviousFlightsReturnDays')
        control16.readonly = False
        control16.value = '1'
        control17 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$journey_0')
        control17.readonly = False
        control17.value = outgoing_flight
        control18 = browse.form.find_control('SelectViewControlGroupFlightSelection$SelectViewFlightSelectionControl$journey_1')
        control18.readonly = False
        control18.value = return_flight
        '''
        __EVENTARGUMENT=
        '''
        control19 = browse.form.find_control('__EVENTTARGET')
        control19.readonly = False
        control19.value = 'SelectViewControlGroupFlightSelection$ButtonSubmit'
        controlview = browse.form.find_control('__VIEWSTATE')
        viewstate_wert = controlview.value
        controlview.readonly = False
        controlview.value = viewstate_wert
        control21 = browse.form.find_control('passengersADT')
        control21.readonly = False
        control21.value = '1',
        control22 = browse.form.find_control('passengersCHD')
        control22.readonly = False
        control22.value = '0',
        control23 = browse.form.find_control('passengersINFANT')
        control23.readonly = False
        control23.value = '0',
        ##print browse.form
        ##print ('Submitting form!')
        response2 = browse.submit()
        ##print ('Getting response')
        page = response2.read()
        
        outgoings = self.searchSeats (page, 1)
        returns = self.searchSeats (page, 2)
        return outgoings, returns
        
    def ImgRec (self, dateiname):
        def check_rows_and_cols (list1, list2):
            rows1 = []
            cols1 = []
            rows2 = []
            cols2 = []
            for x,y in list1:
                rows1.append(y)
                cols1.append(x)
            for x,y in list2:
                rows2.append(y)
                cols2.append(x)
            rows = rows1 + rows2
            rows = list(set(rows))
            cols = cols1 + cols2
            cols = list(set(cols))
            return sorted(rows), sorted(cols), len(cols), len(rows)

        def test(liste):
            if (liste[-1][0] == liste[-2][0]) and (liste[-1][1] == liste[-2][1]+24):
                liste.pop()
                liste.pop()
        
        img = cv2.imread(dateiname) ##Beispiel-Datei heißt neu.png
        template = cv2.imread('seat_avail.jpg')
        template2 = cv2.imread('seat_occupied.jpg')
        th, tw = template.shape[:2]
        t2h, t2w = template.shape[:2]

        available = []
        occupied = []
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        result2 = cv2.matchTemplate(img, template2, cv2.TM_CCOEFF_NORMED)
        threshold = 0.995
        loc = numpy.where(result >= threshold)
        loc2 = numpy.where(result2 >= threshold)

        for pt in zip(*loc[::-1]):
            ##print pt
            available.append(pt)
            cv2.rectangle(img, pt, (pt[0] + tw, pt[1] + th), 0, 2)
        for pt2 in zip(*loc2[::-1]):
            ##print pt2
            occupied.append(pt2)
            cv2.rectangle(img, pt2, (pt2[0] + t2w, pt2[1] + t2h), 10, 1)
        cv2.imwrite('erg_'+dateiname, img)
        
        print "available: ", available
        print "occupied: ", occupied
        
        test(available)
        test(occupied)
        rows, cols, x, y = check_rows_and_cols(available, occupied)

        BB_seats = []
        for ia in rows:
            for na in cols:
                ##print (na, ia)
                if (na, ia) in occupied:
                    ##print 'Ist in Occupied'
                    BB_seats.append(1)
                    continue
                if (na, ia) in available:
                    ##print 'Ist in Available'
                    BB_seats.append(0)
                    continue

        print BB_seats
        print "Anzahl Sitzreihen: ", len(rows)
        return BB_seats, len(rows)