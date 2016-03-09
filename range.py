#/usr/bin/python

from __future__ import division

import bisect
import sys
from csv import DictReader
from datetime import datetime, timedelta, date
from enerdata.contracts.tariff import *
from enerdata.cups.cups import CUPS
from enerdata.datetime.timezone import TIMEZONE
from enerdata.profiles.profile import Profile
from termcolor import colored
from one_year_ago.one_year_ago import *



fitx = 'lectures.txt'
__NUMBER__ = None
__info__ = None

# Performance monitor
from timeit import default_timer as timer
__timer__ = None
timer_start = None
timer_end = None

un_dia = timedelta(days=1)


def performance_summary(regs_count=None):
    missatge = format_secundari("   Takes {0:.5f}s".format(timer_end -
                                                           timer_start))
    print missatge + format_secundari(" for {} registries".format(
        regs_count)) if regs_count else missatge


def performance_start():
    global timer_start
    timer_start = timer()


def performance_stop():
    global timer_end
    timer_end = timer()


def format_date(date_to_format):
    return date_to_format.strftime("%Y/%m/%d")


def format_negreta(entrada):
    return colored(entrada, attrs=['bold', 'reverse'])


def format_verd(entrada):
    return colored(entrada, "green")


def format_vermell(entrada):
    return colored(entrada, "red")


def format_sign(entrada):
    if entrada > 0:
        return format_verd(entrada)
    else:
        return format_vermell(entrada)


def format_secundari(entrada):
    return colored(entrada, 'grey')


def informam(entrada):
    if __info__:
        print(entrada)



class Reporting ():

    path = './reports/'
    file_name = 'prediction.html'

    def create_html(self):
        file = self.create_file("prediction.html")
        self.dump_html(file)
        file.close()

    def create_tsv(self, prediction):
        file = self.create_file("data.tsv")
        self.dump_tsv(file, prediction)
        self.dump_array(file, prediction)
        file.close()


    def create_file(self, file_name=None):
        if file_name:
            self.file_name = file_name
        try:
            file = open(self.path + self.file_name,'w')   # Trying to create a new file or open one
            return file

        except:
            print('HTML creation failed')
            exit(0)

    def dump_tsv (self,file, prediction):
        print >>file, "hour\tvalue"

        for day in prediction.days_to_predict:
            day2print = day
            day = day.toordinal()
            values = prediction.predictions_day_by_hour[day]

            for idx, pred in enumerate(values[1]):
                print >>file, '{}-{:0>2}:00\t{}'.format(format_date(day2print),
                    idx, prediction.get_final_amount(pred))

    def dump_array (self,file, prediction):
        valors = "valors = ["

        for day in prediction.days_to_predict:
            day2print = day
            day = day.toordinal()
            values = prediction.predictions_day_by_hour[day]

            for idx, pred in enumerate(values[1]):

                valors += '[{}, {}, {}, {}, {}], '.format(
                    day2print.year, day2print.month, day2print.day, idx, prediction.get_final_amount(pred))

        print valors+"],"

    def dump_html(self, file):

        html_content = """

<!DOCTYPE html>
<meta charset="utf-8">
<style>

body {
  font: 10px sans-serif;
}

.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}

.x.axis path {
  display: none;
}

.line {
  fill: none;
  stroke: steelblue;
  stroke-width: 1.5px;
}

</style>
<body>
<script src="http://d3js.org/d3.v3.min.js"></script>
<script>

var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var formatDate = d3.time.format("%d-%b-%y");

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var line = d3.svg.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.value); });

var svg = d3.select("body").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

d3.tsv("data.tsv", type, function(error, data) {
  if (error) throw error;

  x.domain(d3.extent(data, function(d) { return d.date; }));
  y.domain(d3.extent(data, function(d) { return d.value; }));

  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis)
    .append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 6)
      .attr("dy", ".71em")
      .style("text-anchor", "end")
      .text("Price ($)");

  svg.append("path")
      .datum(data)
      .attr("class", "line")
      .attr("d", line);
});

function type(d) {
  d.date = formatDate.parse(d.date);
  d.value = +d.value;
  return d;
}

</script>




        """

        print >>file, html_content



class Prediction():
    past_cups = []  # list of [cup, Past]
    future_cups = []  # list of [cup, Past]

    total_consumption = 0
    days_count = 0

    days_to_predict = []  #list of datetime for future days
    days_to_predict_past = [
    ]  #list of datetime for past days (same order than days_to_predict)

    predictions_day_by_hour = dict(
    )  # dict of list { day.toordinal(): [ #list day_consumption, array of hours[] }

    hourly_detail = False

    correction_apply = False
    correction_fixed = 0
    correction_fixed_global = 0

    def __init__(self):
        pass

    def importData(self):
        self.parseFile()

    def parseFile(self):

        if __timer__:
            performance_start()

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

            informam(' - {} {} {} {}kw'.format(row['cups'], format_date(
                data_anterior), format_date(data_lectura), row['consum']))

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
                    print colored("[!] ERROR", 'red'), " :: {} {}\n".format(
                        row, sys.exc_info())

                    raise
            else:
                print colored(
                    "[!] WARNING",
                    'yellow'), " :: No hi ha dades pel mes {}.\n".format(
                        mes_actual.month)

            bisect.insort(self.past_cups, [past_cup.cups, past_cup,
                                           past_cup.period])

        if __timer__:
            performance_stop()
            performance_summary(count - 1)

    def predictions_by_day_increase_hour_measure(self, day, hour, measure):
        #print "yyy", datetime.fromordinal(day), day, hour, measure
        #pythoprint self.predictions_day_by_hour
        self.predictions_day_by_hour[day][1][hour] += measure

    def predictions_by_day_increase_total(self, day, measure):
        self.predictions_day_by_hour[day][0] += measure

    def is_same_day(self, datea, dateb):
        return datea.date() == dateb.date()

    def extract_and_add_hours_to_prediction(self, partial):
        day_total = 0
        count = 0
        for day in self.days_to_predict:
            for hour in partial.profile.measures:
                if hour.measure > 0:
                    if not self.is_same_day(hour.date,
                                            self.days_to_predict_past[count]):
                        continue
                    #print "   ---> {} {} kw".format(hour.date, hour.measure)
                    self.predictions_by_day_increase_hour_measure(
                        day.toordinal(), hour.date.hour, hour.measure)
                    day_total += hour.measure

            self.predictions_by_day_increase_total(day.toordinal(), day_total)
            day_total = 0
            count += 1

    def initialize_prediction(self, start_date, end_date):
        delta = end_date - start_date

        self.start_date = dia_cont = start_date
        self.end_date = end_date

        self.days_count = 0
        while self.days_count < delta.days:

            self.days_to_predict_past.append(OneYearAgo(dia_cont).day_year_ago)
            self.days_to_predict.append(dia_cont)

            #bisect.insort(self.days_to_predict, dia_cont)
            #bisect.insort(self.days_to_predict_past, OneYearAgo(dia_cont).day_year_ago)

            #print "inserto", dia_cont
            #bisect.insort(self.predictions_day_by_hour, [, [0]*24])

            self.predictions_day_by_hour[(dia_cont).toordinal()] = [
                0, [0] * 24
            ]  #list day_consumption, array of hours

            dia_cont += un_dia
            self.days_count += 1

    def predict(self, start_date, end_date, cups_list=None):
        if __timer__:
            performance_start()

        # todo filter cups list - currently bypassed to analyze all CUPS
        if 0 and cups_list:
            for cups in cups_list:
                past = bisect.bisect(self.past_cups, cups)
                future = Future(past, datetime(2016, 10, 25),
                                datetime(2016, 10, 27))

                # Poor performance.. needed to change Past to dicts!
                #past_cups_2process = [ cups
                #          for cups in self.past_cups[0]
                #          if cups == ]

        else:
            message = (
                "\nStart prediction for all Past CUPS bewteen {} - {}".format(
                    format_date(start_date), format_date(end_date)))

            logger.info(message)
            print message

            self.initialize_prediction(start_date, end_date)

            for past in self.past_cups:
                future = Future(past[1], start_date, end_date)

                self.extract_and_add_hours_to_prediction(future)
                #self.future_cups = future
                bisect.insort(self.future_cups, future)
                self.total_consumption += future.profile.total_consumption
                #print "TOTAL", future.profile.total_consumption

        message = (
            "\nPredicted TOTAL consumption of {} kw between {} - {} based on the last year info".format(
                self.total_consumption, format_date(start_date),
                format_date(end_date)))

        logger.info(message)

        if __timer__:
            performance_stop()
            performance_summary(len(self.past_cups))

        print message + "\n"

    # for performance reasons just set the fixed amount on the object, and assume that
    # when the data will be consumed the fixed correction will be applied in real-time
    def apply_correction_increase(self, percentatge, is_global=None):
        # todo :: increase Prediction profiles instead just the total amount!
        self.correction_apply = True

        previous_amount = self.get_final_amount(self.total_consumption)
        if is_global:
            self.correction_fixed_global += float(percentatge) / 100
        else:
            self.correction_fixed += float(percentatge) / 100

        return "Total {} kw  (previous {} kw)".format(
            float(self.get_final_amount(self.total_consumption)),
            previous_amount)

    def apply_correction(self, factor_name, params=None):
        correction_type, correction_what = None, None
        if params:
            if len(params) > 0:
                correction_type = params[0]
                try:
                    correction_what = params[1]
                except:
                    correction_what = None

                try:
                    correction_global = params[2]
                    message_global = ", global"
                except:
                    correction_global = False
                    message_global = ""

        print " - '{}' ({}: {}{})".format(factor_name, correction_type,
                                          correction_what, message_global)

        # Do the job!
        type_of_correction = {
            'increase_percent':
            self.apply_correction_increase(correction_what, correction_global),
            'filter': None
        }.get(correction_type, None)

        print "    - Result: {}".format(type_of_correction)

    # apply static corrections to a value
    def get_final_amount(self, value):
        if self.correction_apply:
            value_corrected = float(1 + self.correction_fixed) * float(value)

            # increase the corrected value with the global fixed correction
            value_corrected_global = float(
                1 + self.correction_fixed_global) * float(value_corrected)
            return value_corrected_global
        return value

    def apply_correctional_factors(self):
        if __timer__:
            performance_start()

        print "Applying correctional factors"
        self.apply_correction("Set 15% contingency margin",
                              ["increase_percent", "15"])
        #self.apply_correction("Discount 15%", ["increase_percent", "-15"] )

        #self.apply_correction("Duplicate", ["increase_percent", "100", "global"] )

        self.apply_correction("The half (including margins)",
                              ["increase_percent", "-50", "global"])

        #self.apply_correction("Name", ["filter", "region"] )

        if __timer__:
            performance_stop()
            performance_summary()

        print "\n"

    def view_hourly_detail(self):
        self.hourly_detail = True

    def hide_hourly_detail(self):
        self.hourly_detail = False

    def summarize(self):
        print format_negreta("PREDICTION SUMMARY"), "\n"
        print "  ", format_verd("{} kw".format(self.get_final_amount(
            self.total_consumption))), "from {} to {} [{} days]\n".format(
                format_date(self.start_date), format_date(self.end_date),
                self.days_count)

        for day in self.days_to_predict:
            day = day.toordinal()
            values = self.predictions_day_by_hour[day]
            ##print day, sum(values[1]), values
            self.print_day_summary(day, values)
            print ""

        if self.correction_apply:
            print "   // Applied Margins of '{}%' and '{}%' global".format(
                format_sign(self.correction_fixed),
                format_sign(self.correction_fixed_global))

    def print_day_summary(self, day, values):
        print '   + {} kw {}'.format(
            self.get_final_amount(values[0]),
            format_date(date.fromordinal(day)))
        if self.hourly_detail:
            for idx, pred in enumerate(values[1]):
                print '      - {} kw    {:0>2}:00 - {:0>2}:00'.format(
                    self.get_final_amount(pred), idx, idx + 1)


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

    # todo wait for merge PR #53 @ enerdata to delete this method!
    def get_cof_per_tarif(self, tarifa):
        return {
            'x2.0DHS': 'D',
            'x2.1DHS': 'D',
            'x2.0A': 'A',
            'x2.0DHA': 'B',
            'x2.1A': 'A',
            'x2.1DHA': 'B',
            'x3.0A': 'C',
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

        #        t.cof = self.get_cof_per_tarif(t.code)

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

        self.profile = self.range_profile(data_anterior, data_lectura, tarifa,
                                          consum, periode)
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
                self.profile.total_consumption, self.cups.number,
                self.past.period, format_date(start_date),
                format_date(end_date)))

        logger.info(message)
        informam(message)

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

            dia_localized = TIMEZONE.localize(dia)

            bisect.insort(self.present_days_list, dia)

            # Set the past day
            past_day = self.get_past_day(dia_localized)

            past_day_localized = TIMEZONE.localize(past_day)

            bisect.insort(self.past_days_list, past_day)

            def index_passat(a, x):
                i = bisect.bisect_left(a, [x])
                if i != len(a) and a[i][0] == x:
                    return i
                return None

            dia_passat = index_passat(self.past.profile_per_day,
                                      past_day_localized)

            if not dia_passat:
                informam(" - Estimation not found for {} --> {}".format(
                    format_date(dia), format_date(past_day)))
                dia += un_dia
                continue

            # todo canviar data interna de la mesura (segueix sent la vella
            # encara)

            mesures_dia_passat = self.past.profile_per_day[dia_passat][1]

            #bisect.insort(self.profile.measures, mesures_dia_passat)

            self.profile.measures.extend(mesures_dia_passat.measures)

            missatge = (
                " - Adding day_measurements for day: {} [{} kw] -> {} ".format(
                    dia, mesures_dia_passat.total_consumption,
                    mesures_dia_passat.measures))

            informam(missatge)

            logger.info(missatge)

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


__NUMBER__ = 2
__info__ = False
__timer__ = True

#import logging
#logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)

prediction = Prediction()
prediction.parseFile()

cups_list = ["ES0031406178012015XD0F"]

cups_list = None

date_start = datetime(2016, 12, 29)
date_end = datetime(2016, 12, 31)

prediction.predict(date_start, date_end, cups_list)

prediction.apply_correctional_factors()

#prediction.view_hourly_detail()

prediction.summarize()

#print prediction.future_cups[0].total_consumption


report = Reporting()

report.create_html()

report.create_tsv(prediction)


