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
            bisect.insort(perfils_dia_llista, [dia, perfil_dia])

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

        #create a profile for each day
        self.profile_per_day = self.profile_cut_by_date(self.profile)



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



class Future (Past):



    def __init__(self, past, start_date=None, end_date=None):
        self.past=past

        self.date_ini=start_date
        self.date_fi=end_date

        self.present_days_list=[]
        self.present_days_list_done=[]

        self.past_days_list=[]

        logger.info( "Present days: {}".format(self.present_days_list))
        logger.info("Past days: {}".format(self.past_days_list))

        self.project_past_to_future()

        logger.info("Predicted consumption of {} kw between {} - {} based on the last year info".format(self.profile.total_consumption, start_date, end_date))


    # todo -> add correctional factors
    def project_past_to_future(self):
        un_dia = timedelta(days=1)

        self.days_list = []

        dia = self.date_ini

        logger.info ("Setting days list for {} - {}".format(dia, self.date_fi))

#        ("GRAN: {}".format(perfil_gran))


        self.profile = Profile(TIMEZONE.localize(dia),TIMEZONE.localize(self.date_fi),[])

        logger.info ("Creating projected profile: {} ".format(self.profile))


        while dia <= self.date_fi:
            #Set the present day

            dia = (dia)

            dia_localized=TIMEZONE.localize(dia)

            bisect.insort(self.present_days_list, dia)

            #Set the past day
            past_day=self.get_past_day(dia_localized)
            past_day_localized = TIMEZONE.localize(past_day)

            bisect.insort(self.past_days_list, past_day)

            dia_passat =  bisect.bisect( self.past.profile_per_day, [past_day_localized] )  + 1


            ## todo canviar data interna de la mesura (segueix sent la vella encara)

            mesures_dia_passat = past.profile_per_day[dia_passat][1]

            #bisect.insort(self.profile.measures, mesures_dia_passat)

            self.profile.measures.extend(mesures_dia_passat.measures)

            logger.info(" - Adding day_measurements {} for day: {}".format(mesures_dia_passat.measures, dia))


            #Set the day to future

            self.usage_sum +=mesures_dia_passat.total_consumption
            self.count += 1

            dia += un_dia




    def get_past_day(self, day):
        """
        Interact with one_year_ago to reach the related past day

        :param day:
        :return: past_day
        """
        return OneYearAgo(day).day_year_ago


past = Past()

logging.basicConfig(level=logging.INFO)

past.parseFile()

p=Profile(TIMEZONE.localize(datetime(2018,10,2)),TIMEZONE.localize(datetime(2018,10,26)), [])

future = Future(past, datetime(2016,10,25), datetime(2016,10,27))