#/usr/bin/python

import sys
from datetime import datetime, timedelta, date
from enerdata.profiles.profile import Profile
from enerdata.datetime.timezone import TIMEZONE
from enerdata.contracts.tariff import *

from enerdata.cups.cups import CUPS

from csv import DictReader

from time import sleep

from termcolor import colored


import bisect


from one_year_ago.one_year_ago import *
from datetime import datetime, timedelta, date

fitx = 'lectures.txt'
__NUMBER__ = None
un_dia = timedelta(days=1)


class Prediction():
    past_cups = []  # list of [cup, Past]
    future_cups = []  # list of [cup, Past]

    total_consumption = 0
    days_count = 0

    days_to_predict = [] #list of datetime

    predictions_day_by_hour = dict() # dict of list { day.toordinal(): [ #list day_consumption, array of hours[] }

    hourly_detail=False

    def importData(self):
        self.parseFile()

    def parseFile(self):
        f = open(fitx, 'rb')
        a = DictReader(f, delimiter=';')
        count = 0
        mes_actual = datetime.today()

        message = "\nStart parsing incoming file {}".format(fitx)
        print message
        logger.info(message)


        for row in a:
            past_cup = Past()
            count += 1

            if __NUMBER__ and count > __NUMBER__:
                break
            # print row
            data_anterior = datetime.strptime(row['data_anterior'], '%Y-%m-%d')
            data_lectura = datetime.strptime(row['data_mesura'], '%Y-%m-%d')

            print ' - {} {} {} {}kw'.format(
                row['cups'], data_anterior.strftime("%d/%m/%Y"),
                data_lectura.strftime("%d/%m/%Y"), row['consum'])

            # todo ISSUE enerdata tema mes actual
            # El mes actual encara no esta disponible
            # http://www.ree.es/sites/default/files/simel/perff/PERFF_201602.gz

            if (mes_actual - data_lectura).total_seconds() > 0:
                try:
                    past_cup.range_process(row)
                    past_cup.period = row['periode']

                    # print colored("[!] OK", 'green'), " :: {}
                    # {}".format(row,sys.exc_info())
                except:

                    print colored("[!] ERROR", 'red'), " :: {} {}\n".format(row,sys.exc_info())

                    raise
            else:
                print colored(
                    "[!] WARNING",
                    'yellow'), " :: No hi ha dades pel mes {}.\n".format(
                        mes_actual.month)

            bisect.insort(self.past_cups, [past_cup.cups, past_cup, past_cup.period])

    def predictions_by_day_increase_hour_measure(self, day, hour, measure):
        self.predictions_day_by_hour[day][1][hour] += measure


    def predictions_by_day_increase_total(self, day, measure):
        self.predictions_day_by_hour[day][0] += measure



    def extract_and_add_hours_to_prediction(self, partial):
        day_total=0;
        for day in self.days_to_predict:
            for hour in partial.profile.measures:
                if hour.measure > 0:
                    #print "   ---> {} {} kw".format(hour.date, hour.measure)
                    self.predictions_by_day_increase_hour_measure(day.toordinal(), hour.date.hour, hour.measure)
                    day_total += hour.measure

            self.predictions_by_day_increase_total(day.toordinal(), day_total)
            day_total=0




    def initialize_prediction (self, start_date, end_date):
            delta = end_date - start_date

            self.start_date=start_date
            self.end_date = end_date

            self.days_count=0
            while self.days_count < delta.days:
                bisect.insort(self.days_to_predict, start_date + un_dia)
                #bisect.insort(self.predictions_day_by_hour, [, [0]*24])
                self.predictions_day_by_hour[(start_date + un_dia).toordinal()] = [0, [0]*24] #list day_consumption, array of hours

                self.days_count+=1

    def predict(self, start_date, end_date, cups_list=None):
        # todo filter cups list - currently bypassed to analyze all CUPS
        if 0 and cups_list:
            for cups in cups_list:
                past = bisect.bisect(self.past_cups, cups)
                future = Future(past, datetime(2016, 10, 25),
                                datetime(2016, 10, 27))
        else:
            message = (
                "\nStart prediction for all Past CUPS bewteen {} - {}".format(
                    start_date, end_date))

            logger.info(message)
            print message

            self.initialize_prediction(start_date, end_date)



            for past in self.past_cups:
                future = Future(past[1], start_date, end_date)

                self.extract_and_add_hours_to_prediction (future)
                #self.future_cups = future
                bisect.insort(self.future_cups, future)
                self.total_consumption += future.profile.total_consumption

        message = (
            "\nPredicted TOTAL consumption of {} kw between {} - {} based on the last year info".format(
                self.total_consumption, start_date, end_date))

        logger.info(message)
        print message+"\n"

    def view_hourly_detail(self):
        self.hourly_detail=True

    def hide_hourly_detail(self):
        self.hourly_detail=False

    def summarize(self):
        print "PREDICTION SUMMARY"
        print " - {} kw from {} to {} [{} days]".format(self.total_consumption, self.start_date.strftime("%Y/%m/%d"), self.end_date.strftime("%Y/%m/%d"), self.days_count)

        for day, values in self.predictions_day_by_hour.items():
            self.print_day_summary(day, values)

    def print_day_summary(self,day, values):
        print '  - {} kw {}'.format(values[0], date.fromordinal(day).strftime("%Y/%m/%d"))

        if self.hourly_detail:
            for idx, pred in enumerate(values[1]):
                print '   - {:0>2}:00 - {:0>2}:00 :: {} kw'.format(idx, idx+1, pred)

class Past():
    cups = None
    date_ini = None
    date_fi = None

    # default period
    period = 'P1'

    # generic profile with gap fixing for null days
    # created with the info of estimated
    profile = None

    # a profile for each day
    profile_per_day = None

    dates_past_included, dates_future_done = None, None

    past = None  # The parsed past data!

    # statistics
    usage_sum = 0
    count = 0

    def get_cof_per_tarif(self, tarifa):
        return {
            '2.0DHS': 'D',
            '2.1DHS': 'D',
            '2.0A': 'A',
            '2.0DHA': 'B',
            '2.1A': 'A',
            '2.1DHA': 'B',
            '3.0A': 'C',
            '3.1A': 'C',
            '3.1A LB': 'C',

        }.get(tarifa, 'A')



    def get_tariff_per_tarif(self, tarifa):
        return {
            '2.0DHS': 'T20DHS',
            '2.1DHS': 'T21DHS',
            '2.0A': 'T20A',
            '2.0DHA': 'T20DHA',
            '2.1A': 'T21A',
            '2.1DHA': 'T21DHA',
            '3.0A': 'T30A',
            '3.1A': 'T31A',
            '3.1A LB': 'T31A',

        }.get(tarifa, None)

    # Receives the day to process!
    def include_day(self, day, data):
        bisect.insort(self.dates_past_included, day)
        bisect.insort(self.past, [day, data])

    def range_profile(self, data_ini, data_fi, tarifa, consum, periode):
        """
        Create a profile for a range and estimate it with the correct usage,
        tarifa and coef

        :param data_ini:
        :param data_fi:
        :param consum:
        :param periode:
        :return:
        """

        data_ini = TIMEZONE.localize(data_ini)
        data_fi = TIMEZONE.localize(data_fi + timedelta(days=1))

        p = Profile(data_ini, data_fi, [])

        t = get_tariff_by_code(tarifa)()

        t.cof = self.get_cof_per_tarif(t.code)

        #periode="P1"

        estimacio = p.estimate(t, {str(periode): int(consum)})

        # print '{} {}-{}'.format(estimacio.total_consumption, estimacio.start_date.strftime('%d/%m/%Y'), estimacio.end_date.strftime('%d/%m/%Y'))
        # print '{} mesures\n'.format(len(estimacio.measures))

        # print estimacio.measures

        return estimacio

    # Candidate to be merged on Enerdata
    # Return a list of day Profiles
    # todo prev insort -> review if date exist and sum the new one (for next
    # day 0h estimation)
    def profile_cut_by_date(self, perfil_gran):
        perfils_dia_llista = []

        dia = perfil_gran.start_date
        dia_fi = perfil_gran.end_date

        logger.debug("GRAN: {}".format(perfil_gran))

        while dia < dia_fi:
            perfil_dia = Profile(dia, dia + un_dia, [])

            perfil_dia.measures = [mesura
                                   for mesura in perfil_gran.measures
                                   if mesura.date.month == dia.month and
                                   mesura.date.day == dia.day]

            logger.debug("  - {}".format(perfil_dia))

            logger.info("  - {} {}".format(perfil_dia.start_date,
                                           perfil_dia.total_consumption))

            bisect.insort(perfils_dia_llista, [dia, perfil_dia])
            dia += un_dia

        return perfils_dia_llista

    def range_process(self, entrada):
        self.cups = CUPS(entrada['cups'])

        data_anterior = datetime.strptime(entrada['data_anterior'], '%Y-%m-%d')
        data_lectura = datetime.strptime(entrada['data_mesura'], '%Y-%m-%d')

        consum = entrada['consum']
        periode = entrada['periode']
        tarifa = entrada['tarifa']

        self.profile = self.range_profile(data_anterior, data_lectura, tarifa, consum,
                                          periode)
        self.date_ini = data_anterior
        self.date_fi = data_lectura
        self.usage_sum = consum

        logger.info(self.estimation_summary())

        # create a profile for each day
        self.profile_per_day = self.profile_cut_by_date(self.profile)

    def estimation_summary(self):
        return "{} {}kw [#{}] {} - {}".format(
            self.cups.number, self.usage_sum, self.count,
            self.date_ini.strftime("%d/%m/%Y"),
            self.date_fi.strftime("%d/%m/%Y"))


class Future(Past):
    def __init__(self, past, start_date, end_date):
        self.past = past

        self.date_ini = start_date
        self.date_fi = end_date

        self.cups = past.cups

        self.present_days_list = []
        self.present_days_list_done = []

        self.past_days_list = []

        self.by_ours = []

        logger.info("Present days: {}".format(self.present_days_list))
        logger.info("Past days: {}".format(self.past_days_list))



        self.project_past_to_future()

        message = (
            " - Predicted consumption of {} kw for CUPS {} and {} between {} - {} based on the last year info".format(
                self.profile.total_consumption, self.cups.number, self.past.period, start_date,
                end_date))

        logger.info(message)
        print message

    # todo -> add correctional factors
    def project_past_to_future(self):
        un_dia = timedelta(days=1)

        self.days_list = []

        dia = self.date_ini

        logger.info("Setting days list for {} - {}".format(dia, self.date_fi))

        #        ("GRAN: {}".format(perfil_gran))

        self.profile = Profile(
            TIMEZONE.localize(dia), TIMEZONE.localize(self.date_fi), [])

        logger.info("Creating projected profile: {} ".format(self.profile))

        while dia < self.date_fi:
            # Set the present day

            dia = (dia)

            dia_localized = TIMEZONE.localize(dia)

            bisect.insort(self.present_days_list, dia)

            # Set the past day
            past_day = self.get_past_day(dia_localized)

            past_day_localized = TIMEZONE.localize(past_day)

            bisect.insort(self.past_days_list, past_day)


            def index_passat(a,x):
                i=bisect.bisect_left(a, [ x ])
                if i != len(a) and a[i][0] == x:
                    return i
                return None


            dia_passat = index_passat(self.past.profile_per_day, past_day_localized)

            if not dia_passat:
                print " - Estimation not found for {} --> {}".format(dia, past_day)
                dia += un_dia
                continue

            # todo canviar data interna de la mesura (segueix sent la vella
            # encara)


            mesures_dia_passat = self.past.profile_per_day[dia_passat][1]

            #bisect.insort(self.profile.measures, mesures_dia_passat)


            self.profile.measures.extend(mesures_dia_passat.measures)

            logger.info(
                " - Adding day_measurements for day: {} [{} kw] -> {} ".format(
                    dia, mesures_dia_passat.total_consumption,
                    mesures_dia_passat.measures))

            # Set the day to future

            self.usage_sum += mesures_dia_passat.total_consumption
            self.count += 1

            dia += un_dia

    def get_past_day(self, day):
        """
        Interact with one_year_ago to reach the related past day

        :param day:
        :return: past_day
        """
        return OneYearAgo(day).day_year_ago





__NUMBER__ = 3

#import logging
#logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

prediction = Prediction()
prediction.parseFile()

cups_list = ["ES0031406178012015XD0F"]

cups_list = None

prediction.predict(datetime(2016, 10, 25), datetime(2016, 10, 26), cups_list)

#prediction.view_hourly_detail()

prediction.summarize()

#print prediction.future_cups[0].total_consumption