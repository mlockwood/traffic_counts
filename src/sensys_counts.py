#!/usr/bin/env python3.4
# -*- coding: utf-8 -*-

"""
__authors__ = MichaelLockwood
__projectclass__ = traffic_counts
__projectsubclass__ = puck_counts
__projectnumber__ = 2
__projectname__ = sensys_counts.py
__date__ = February2016
__credits__ = None
__collaborators__ = RonIgnacio

This extracts raw puck count data and aggregates the records by user
preference.
"""

# Import packages
import configparser
import csv
import datetime
import os
import re
import sys
import xlsxwriter

import multiprocessing as mp

"""
Closed Classes----------------------------------------------------------
"""
class PathSetter:

    def set_pythonpath(directory='', subdirectory=''):
        if directory:
            directory = PathSetter.find_path(directory)
            if subdirectory:
                if directory[-1] != '/' and subdirectory[0] != '/':
                    directory += '/'
                directory += subdirectory
        else:
            directory = os.getcwd()
        sys.path.append(directory)
        return True

    def find_path(directory):
        match = re.search(str(directory), os.getcwd())
        if not match:
            raise IOError(str(directory) + ' is not in current working ' +
                          'directory of ' + str(os.getcwd()))
        return os.getcwd()[:match.span()[0]] + '/' + directory

"""
Traffic Count Imports---------------------------------------------------
"""
PathSetter.set_pythonpath()
import report as rp

"""
Main Classes------------------------------------------------------------
"""
class System:
    
    @staticmethod
    def load_config():
        config = configparser.ConfigParser()
        config.read('system.ini')
        for var in config['DEFAULT']:
            try:
                exec('System.' + var + ' = ' + eval('\'' +
                    eval('config[\'DEFAULT\'][\'' + var + '\']') + '\''))
                if isinstance('System.' + var, complex):
                    exec('System.' + var + ' = \'' + eval(
                        'config[\'DEFAULT\'][\'' + var + '\']') + '\'')
            except:
                exec('System.' + var + ' = \'' + eval(
                    'config[\'DEFAULT\'][\'' + var + '\']') + '\'')
        return True

System.load_config()

class Sheet:

    objects = {}
    ID_generator = 1

    def __init__(self, file):
        self._file = file
        self._location = os.path.split(os.path.split(file)[0])[-1]
        self._records = {}
        self.set_id()

    def set_id(self):
        self._ID = hex(Sheet.ID_generator)
        Sheet.ID_generator += 1
        Sheet.objects[self._ID] = self
        return True

    @staticmethod
    def process():
        #Sheet.load_config()
        for dirpath, dirnames, filenames in os.walk(System.path +
                                                    '/data'):
            for filename in [f for f in filenames if re.search(
                '\d{4}-\d{2}-\d{2}', f)]:
                obj = Sheet(str(dirpath) + '/' + str(filename))
                obj.read_sheet()
        #Sheet.write_sheets()
        return True

    def read_sheet(self):
        """Extract each record from the sheet and create a Record class
        object.
        """
        reader = open(self._file, 'r')
        records = []
        for row in reader:
            records.append(row.split(','))
        for record in records[1:]:
            dt = record[0].split()
            """
            IMPORTANT----------------------------------------------------------
            Remember to update the indices if the columns change.
            """
            indices = [('EB', 4), ('NB', 34), ('SB', 64), ('WB', 94)]
            for I in indices:
                self._records[Record(self, self._location, dt[0], dt[1], I[0],
                                     int(record[I[1]]))] = True
        return True

class Record:

    objects = {}
    ID_generator = 1

    def __init__(self, count_file, location, datestr, time, direction, count):
        # Default values
        self._count_file = count_file
        self._location = location
        self._datestr = datestr
        self._time = time
        self._direction = direction
        self._count = count
        # Processing functions
        self.set_date()
        self.set_time()
        self.set_id()
        # Add record to the date it pertains
        Day.add_count(location, self._date, self._dow, self._week, count,
                      direction)

    def set_date(self):
        date = re.split('-', self._datestr)
        self._year = int(date[0])
        self._month = int(date[1])
        self._day = int(date[2])
        self._date = datetime.date(self._year, self._month, self._day)
        self._week = (str(self._date.isocalendar()[0]) + '_' +
                      str(self._date.isocalendar()[1]))
        self._dow = str(self._date.isocalendar()[2])
        return True

    def set_time(self):
        time = re.split(':', self._time)
        self._hour = int(time[0])
        self._minute = int(time[1])
        self._second = int(time[2])

    def set_id(self):
        self._ID = hex(Record.ID_generator)
        Record.ID_generator += 1
        Record.objects[self._ID] = self
        return True

class Location:

    objects = {}

    def __init__(self, location):
        self._location = location
        self._days = {}
        self._weeks = {}
        self._months = {}
        Location.objects[location] = self

class Day:

    objects = {}

    def __init__(self, location, year, month, day, date, week, dow):
        # Default values
        self._location = location
        self._year = year
        self._month = month
        self._day = day
        self._date = date
        self._week = week
        self._dow = dow
        self._EB = 0
        self._NB = 0
        self._SB = 0
        self._WB = 0
        self._total = 0
        self._average = 0
        # Processing functions
        if location not in Location.objects:
            Location(location)
        self.set_week()
        self.set_month()
        # Set object
        Day.objects[(location, year, month, day)] = self
        Location.objects[location]._days[date] = self

    @staticmethod
    def add_count(location, date, dow, week, count, direction):
        if (location, date.year, date.month, date.day) not in Day.objects:
            Day(location, date.year, date.month, date.day, date, week, dow)
        exec('Day.objects[(location, date.year, date.month, date.day)]._' +
             direction + ' += count')
        return True

    @staticmethod
    def set_summations():
        for day in Day.objects:
            obj = Day.objects[day]
            obj._total = obj._EB + obj._NB + obj._SB + obj._WB
        return True

    def set_week(self):
        if (self._location, self._week) not in Week.objects:
            Week(self._location, self._week)
        Week.objects[(self._location, self._week)]._days[self._dow] = self
        return True

    def set_month(self):
        month_key = str(self._year) + '_' + Month.convert_m[int(self._month)]
        if (self._location, month_key) not in Month.objects:
            Month(self._location, month_key)
        Month.objects[(self._location, month_key)]._days[self._date] = self

class Week:

    objects = {}
    convert_d = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3,
               'Thursday': 4, 'Friday': 5, 'Saturday': 6}
    convert_a = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wedesday',
                 4: 'Thursday', 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}

    def __init__(self, location, week):
        # Default values
        self._week = week
        self._days = {}
        # Set object
        Week.objects[(location, week)] = self
        Location.objects[location]._weeks[week] = self

    @staticmethod
    def publish():
        # For each location...
        for location in Location.objects:
            if not os.path.exists(System.path + '/reports/' + location +
                                  '/weekly/'):
                os.makedirs(System.path + '/reports/' + location + '/weekly/')
            # For each week at the location...
            for week in sorted(Location.objects[location]._weeks.keys()):
                # Create Publish object
                file = (System.path + '/reports/' + location + '/weekly/' +
                        str(week) + '.xlsx')
                obj = Location.objects[location]._weeks[week]
                obj.set_averages()
                temp = sorted(obj._days.keys())
                period = (
                    obj._days[temp[0]]._date.strftime('%d %b %Y').upper() +
                    ' -- ' +
                    obj._days[temp[-1]]._date.strftime('%d %b %Y').upper())
                Publish(file, obj, location, period, 'Weekly')
        return True

    def set_averages(self):
        N = {}
        for week in sorted(Week.objects.keys()):
            if week == self._week:
                break
            for dow in Week.objects[week]._days:
                try:
                    self._days[dow]._average += Week.objects[
                        week]._days[dow]._total
                    N[dow] = N.get(dow, 0) + 1
                except KeyError:
                    pass
        for dow in sorted(self._days.keys()):
            try:
                self._days[dow]._average = self._days[dow]._average / float(
                    N[dow])
            except:
                pass
        return True

class Month:

    objects = {}
    convert_m = {1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR', 5: 'MAY', 6: 'JUN',
                 7: 'JUL', 8: 'AUG', 9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC'}

    def __init__(self, location, month):
        # Default values
        self._month = month
        self._days = {}
        # Set object
        Month.objects[(location, month)] = self
        Location.objects[location]._months[month] = self

    @staticmethod
    def publish():
        # For each location...
        for location in Location.objects:
            if not os.path.exists(System.path + '/reports/' + location +
                                  '/monthly/'):
                os.makedirs(System.path + '/reports/' + location + '/monthly/')
            # For each week at the location...
            for month in sorted(Location.objects[location]._months.keys()):
                # Create Publish object
                file = (System.path + '/reports/' + location + '/monthly/' +
                        str(month) +'.xlsx')
                obj = Location.objects[location]._months[month]
                Publish(file, obj, location, month, 'Monthly')
        return True

class Publish():

    def __init__(self, file, obj, location, period, period_type):
        self._file = file
        self._obj = obj
        self._location = location
        self._period = period
        self._period_type = period_type
        self._prepare()

    def _prepare(self):
        # Open workbook and worksheet
        workbook = xlsxwriter.Workbook(self._file)
        worksheet = workbook.add_worksheet('Counts')
        chart = workbook.add_chart({'type': 'line'})
        
        # Set column widths
        alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
        i = 0
        while i < 7:
            worksheet.set_column(eval('\'' + alphabet[i] + ':' +
                                 alphabet[i] + '\''), 12)
            i += 1
        
        # Format declarations
        merge_format = workbook.add_format({'bold': True,
                                            'align': 'center',
                                            'font_size': 16,
                                            })
        
        sub_merge_format = workbook.add_format({'align': 'center',
                                                'font_size': 13,
                                            })
        sub_merge_format.set_bottom(2)

        header_format = workbook.add_format({'align': 'center',
                                             'valign': 'vcenter',
                                             })
        header_format.set_bottom(1)
        
        bold_format = workbook.add_format({'bold': True,
                                           'align': 'center',
                                           })
        
        center_format = workbook.add_format({'align': 'center',
                                             'valign': 'vcenter',
                                             })
        
        # Write headers
        worksheet.merge_range(eval('\'A1:' + alphabet[6] +
            '1\''), re.sub('_', ' & ', self._location), merge_format)
        worksheet.merge_range(eval('\'A2:' + alphabet[6] +
            '2\''), re.sub('_', ' ', self._period), sub_merge_format)
        worksheet.merge_range(eval('\'A3:' + alphabet[6] +
            '3\''), None)
        worksheet.set_row(2, 5)
        worksheet.write_row('A4', ['Weekday', 'Date', 'North Leg',
            'South Leg', 'East Leg', 'West Leg', 'Total'],
            header_format)
        
        # Write data
        i = 5
        row = 5
        for dow in sorted(self._obj._days.keys()):
            worksheet.write_row('A' + str(row),
                [self._obj._days[dow]._date.strftime('%A'),
                 self._obj._days[dow]._date.strftime('%d %b %Y').upper(),
                 self._obj._days[dow]._NB,
                 self._obj._days[dow]._SB,
                 self._obj._days[dow]._EB,
                 self._obj._days[dow]._WB,
                 self._obj._days[dow]._total,
                 #round(self._obj._days[dow]._average),
                 ], center_format)
            worksheet.write('G' + str(row), self._obj._days[dow]._total,
                            bold_format)
            row += 1

        # Set chart series
        series = [('North', 'C', i, row, '#909090'),
                  ('South', 'D', i, row, '#FFCC00'),
                  ('East', 'E', i, row, '#009933'),
                  ('West', 'F', i, row, '#0000CC'),
                  ]
        for s in series:
            exec(eval('self._set_chart_series' + str(s)))
        
        # Set chart ancillary information
        chart.set_title({'name': self._period_type + ' Counts'})
        chart.set_x_axis({'name': 'Date'})
        chart.set_y_axis({'name': 'Vehicles'})
        chart.set_plotarea({'layout': {'x': 0.13,
                                       'y': 0.26,
                                       'width': 0.73,
                                       'height': 0.57,
                                       }})
        
        # Insert chart into the worksheet
        worksheet.insert_chart('A' + str(row + 2), chart,
                               {'x_offset': 10,
                                'y_offset': 10})

        workbook.close()
        return True

    def _set_chart_series(self, name, col, i , row, color):
        return ('chart.add_series({' +
            # Name
            '\'name\': \'' + name + '\', ' +
            # Categories
            '\'categories\': (\'=Counts!$B$' + str(i) + ':$B$' + str(row - 1) +
                '\'), ' +
            # Values
            '\'values\': \'=Counts!$' + col + '$5:$' + col + '$' +
                str(row - 1) + '\', ' +
            # Line
            '\'line\': {\'color\': \'' + color + '\'}, ' +
            # Marker
            '\'marker\': {\'type\': \'diamond\', ' +
                         '\'fill\': {\'color\':\'' + color + '\'}, ' +
                         '\'border\': {\'color\':\'' + color + '\'}}, ' +
            # Closing syntax
            '})')

def publish():
    # Records
    #Record.publish_matrix()
    # Create total for each day
    Day.set_summations()
    # Weekly
    Week.publish()
    # Monthly
    Month.publish()
    return True

"""
User Interface----------------------------------------------------------
"""
Sheet.process()
print('Finished sheet processing')

publish()
print('Finished designed reports')

# Start date of 1 JAN 2012 and End date of 31 DEC 2020
start = datetime.date(2012, 1, 1)
end = datetime.date(2020, 12, 31)

# Set Report paths
rp.Report.path = System.path + '/reports/'
rp.Report.name = 'Traffic_Count_'

# Generate reports
rp_obj = rp.Report(rp.convert_objects(Record.objects))
rp_obj.generate(['location', 'year', 'month', 'day', 'hour', 'direction'],
                start=start, end=end)
rp_obj.generate(['location', 'week', 'dow', 'direction'])      
print('Finished generated reports')
