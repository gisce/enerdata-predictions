#/usr/bin/python

import sys
from datetime import datetime, timedelta, date
from enerdata.profiles.profile import Profile
from enerdata.datetime.timezone import TIMEZONE
from enerdata.contracts.tariff import T20A

from enerdata.cups.cups import CUPS

from csv import DictReader

from time import sleep

from termcolor import colored




import logging
#logging.basicConfig(level=logging.DEBUG)


import bisect

fitx='lectures.txt'

from one_year_ago.one_year_ago import *
from datetime import datetime, timedelta, date

class Past():

    cups = None
    date_ini = None
    date_fi = None

    #generic profile with gap fixing for null days
    #created with the info of estimated
    profile = None

    #a profile for each day
    profile_per_day = None


    dates_past_included, dates_future_done = None, None

    past = None # The parsed past data!

    #statistics
    usage_sum = 0
    count=0


    #Receives the day to process!
    def include_day(self, day, data):
        bisect.insort(self.dates_past_included, day)
        bisect.insort(self.past, [day, data])


    # Create a profile for a range and estimate it with the correct usage, tarifa and coef
    def range_profile (self,data_ini, data_fi, consum, periode):

    #    print '{} {} {}'.format(data_ini, data_fi, consum)

        #data_ini = datetime(2015,11,26)
        #data_fi = datetime(2015,11,27)

        data_ini = TIMEZONE.localize(data_ini)
        data_fi = TIMEZONE.localize( data_fi + timedelta(days=1) )

        p = Profile(data_ini, data_fi, [])

        t = T20A()

        t.cof='A'

        estimacio = p.estimate(t, {str(periode): int(consum)})

        #print '{} {}-{}'.format(estimacio.total_consumption, estimacio.start_date.strftime('%d/%m/%Y'), estimacio.end_date.strftime('%d/%m/%Y'))
        #print '{} mesures\n'.format(len(estimacio.measures))

        #print estimacio.measures

        return estimacio



    ## Candidate to be merged on Enerdata
    # Return a list of day Profiles
    ## todo prev insort -> review if date exist and sum the new one (for next day 0h estimation)
    def profile_cut_by_date(self, perfil_gran ):
        un_dia = timedelta(days=1)

        perfils_dia_llista = []

        dia = perfil_gran.start_date
        dia_fi = perfil_gran.end_date

        logger.debug("GRAN: {}".format(perfil_gran))

        while dia <= dia_fi:

            perfil_dia = Profile(dia,dia+un_dia,[])

            perfil_dia.measures = [mesura for mesura in perfil_gran.measures
                            if mesura.date.month == dia.month and mesura.date.day == dia.day]

            logger.debug("  - {}".format(perfil_dia))

            logger.info( "  - {} {}".format(perfil_dia.start_date, perfil_dia.total_consumption))
            dia += un_dia
            bisect.insort(perfils_dia_llista, perfil_dia)

        return perfils_dia_llista



    def range_process (self,entrada):

        self.cups = CUPS(entrada['cups'])

        data_anterior = datetime.strptime(entrada['data_anterior'], '%Y-%m-%d')
        data_lectura = datetime.strptime(entrada['data_mesura'], '%Y-%m-%d')

        consum = entrada['consum']
        periode = entrada['periode']

        self.profile = self.range_profile (data_anterior, data_lectura, consum, periode)
        self.date_ini = data_anterior
        self.date_fi = data_lectura
        self.usage_sum=consum

        #print self.estimation_summary()
        logger.info(self.estimation_summary())

        self.profile_cut_by_date(self.profile)



    def estimation_summary(self):
        return "{} {}kw [#{}] {} - {}".format(self.cups.number, self.usage_sum, self.count, self.date_ini.strftime("%d/%m/%Y"), self.date_fi.strftime("%d/%m/%Y"))



    def parseFile(self):
        f=open(fitx, 'rb')
        a = DictReader(f,delimiter=';')
        count=0

        for row in a:
            count+=1
            if count>2:
                break
            #print row
            data_anterior = datetime.strptime(row['data_anterior'], '%Y-%m-%d')
            data_lectura = datetime.strptime(row['data_mesura'], '%Y-%m-%d')

            print '{} {}kw {} {}'.format(row['cups'], data_anterior.strftime("%d/%m/%Y"), data_lectura.strftime("%d/%m/%Y"), row['consum'])


            ## todo ISSUE enerdata tema mes actual
            ## El mes actual encara no esta disponible
            ## http://www.ree.es/sites/default/files/simel/perff/PERFF_201602.gz
            if 1 or (mes_actual - data_lectura).total_seconds() > 0:
                try:
                    self.range_process(row)

                    #print colored("[!] OK", 'green'), " :: {}  {}".format(row,sys.exc_info())
                except:
                    raise
                    #print colored("[!] ERROR", 'red'), " :: {}  {}\n".format(row,sys.exc_info())
            else:
                print colored("[!] WARNING", 'yellow'), " :: No hi ha dades pel mes {}.\n".format(mes_actual.month)






    def testme(self):
        #logging.basicConfig(level=logging.DEBUG)


        dia=datetime(2016,1 ,1) # !is_working, is_holiday
        dia=datetime(2016,5,1) # !is_working, is_holiday
        dia=datetime(2016,2,29) # is_working, !is_holiday
        dia=datetime(2016,3,25) # is_working, !is_holiday


        #if ree_cal.is_holiday(dia):
         #   print dia

        fa_un_any = OneYearAgo(dia)

        #fa_un_any.get_one_year_ago()

        #fa_un_any.get_year_ago(yearsago=2)






logging.basicConfig(level=logging.INFO)

past = Past()

past.parseFile()
