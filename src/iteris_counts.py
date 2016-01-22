
import csv
import datetime
import os
import re
import sys
import time

class Count:

    def __init__(self):
        CountLocation.load_lanes()
        CountLocation.load_files()
        for week in Week.objects:
            CountPeriod(week[0], week[1], week[2], 7)

class CountPeriod:
    """Class with week objects for the purpose of building .csv files
    as output that contain each day in the range. This will also build
    a total for the week period. It is left for adaptation in case the
    user would like to modify the period to be a different number of
    days than 7.
    """

    objects = {}

    def __init__(self, year, month, day, period):
        self._year = str(year)
        self._month = str(month)
        self._day = str(day)
        self._period = str(period)
        self._date_range = []
        self._dates = {}
        CountPeriod.objects[(year, month, day, period)] = self
        self.set_range()
        self.set_direction_matrices()
        self.export_locations()

    def set_range(self):
        """Build a range of dates for the length of the period.
        """
        self._dates = {}
        start = datetime.datetime(int(self._year), int(self._month),
                                  int(self._day))
        self._date_range = [start + datetime.timedelta(days=x) for x in range(
                            0, int(self._period))]
        for date in self._date_range:
            self._dates[(self.configure_values(date.year, date.month,
                                               date.day))] = True
        return True

    def configure_values(self, year, month, day):
        """Convert values from datetime to strings.
        """
        year = str(year)
        month = str(month)
        day = str(day)
        if len(year) == 2:
            year = '20' + year
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        return year+'-'+month+'-'+day

    def set_direction_matrices(self):
        for location in CountLocation.objects:
            CountLocation.objects[location].set_direction_matrices(self._dates)
        return True

    def export_file(self, street, avenue, direction, lanes, matrix):
        csvout = open(os.getcwd() + '\\' + street + 'at' + avenue + '\\' +
                      self._year + '_' + self._month + '_' + self._day + '\\' +
                      self._year + '_'+ self._month + '_' + self._day + '_' +
                      self._period + 'days_' + str(street) + str(avenue) +
                      '_' + str(direction) + '.csv', 'w', newline='')
        writer = csv.writer(csvout, delimiter=',', quotechar='|')
        # Write name
        writer.writerow([str(street)+ ' and ' + str(avenue)])
        # Write days
        days = [""]
        for date in self._date_range:
            days.append(date.strftime('%A'))
            i = 0
            while i < (len(lanes) - 1):
                days.append("")
                i += 1
        writer.writerow(days)
        # Write dates
        dates = [""]
        for date in self._date_range:
            dates.append(date.strftime('%B %d %Y'))
            i = 0
            while i < (len(lanes) - 1):
                dates.append("")
                i += 1
        writer.writerow(dates)
        # Write header
        heading = ['TIME']
        i = 0
        while i < int(self._period):
            for lane in lanes:
                heading.append('LN ' + lane)
            i += 1
        writer.writerow(heading)
        # Write hours and matrix
        hours = [[str(x) + ':00' for x in range(0, 24)] + ['TOTAL']]
        matrix = hours + matrix
        matrix = zip(*matrix)
        for row in matrix:
            writer.writerow(row)
        return True

    def export_week(self, street, avenue, matrix):
        csvout = open(os.getcwd() + '\\' + street + 'at' + avenue + '\\' +
                      self._year + '_' + self._month + '_' + self._day + '\\' +
                      self._year + '_'+ self._month + '_' + self._day + '_' +
                      self._period + 'days_' + str(street) + str(avenue) +
                      '_' + 'Period.csv', 'w', newline='')
        writer = csv.writer(csvout, delimiter=',', quotechar='|')
        # Write name
        writer.writerow([str(street)+ ' and ' + str(avenue)])
        # Write days
        days = [""]
        for date in self._date_range:
            days.append(date.strftime('%A'))
        writer.writerow(days)
        # Write dates
        dates = [""]
        for date in self._date_range:
            dates.append(date.strftime('%B %d %Y'))
        writer.writerow(dates)
        # Write day counts by direction with total
        values = ['EAST LEG', 'NORTH LEG', 'SOUTH LEG', 'WEST LEG', 'TOTAL']
        matrix = [values] + matrix
        matrix = zip(*matrix)
        for row in matrix:
            writer.writerow(row)
        return True

    def export_locations(self):
        for location in CountLocation.objects:
            if not os.path.exists(CountLocation.objects[location]._street +
                                  'at' +
                                  CountLocation.objects[location]._avenue):
                os.makedirs(CountLocation.objects[location]._street + 'at' +
                                  CountLocation.objects[location]._avenue)
            if not os.path.exists(CountLocation.objects[location]._street +
                                  'at' +
                                  CountLocation.objects[location]._avenue +
                                  '\\' + self._year + '_' + self._month + '_' +
                                  self._day + '\\'):
                os.makedirs(CountLocation.objects[location]._street + 'at' +
                                  CountLocation.objects[location]._avenue +
                                  '\\' + self._year + '_' + self._month + '_' +
                                  self._day + '\\')
            self.export_file(CountLocation.objects[location]._street,
                             CountLocation.objects[location]._avenue,
                             'East', CountLocation.objects[location]._EB,
                             CountLocation.objects[location]._EB_matrix)
            self.export_file(CountLocation.objects[location]._street,
                             CountLocation.objects[location]._avenue,
                             'North', CountLocation.objects[location]._NB,
                             CountLocation.objects[location]._NB_matrix)
            self.export_file(CountLocation.objects[location]._street,
                             CountLocation.objects[location]._avenue,
                             'South', CountLocation.objects[location]._SB,
                             CountLocation.objects[location]._SB_matrix)
            self.export_file(CountLocation.objects[location]._street,
                             CountLocation.objects[location]._avenue,
                             'West', CountLocation.objects[location]._WB,
                             CountLocation.objects[location]._WB_matrix)
            self.export_week(CountLocation.objects[location]._street,
                             CountLocation.objects[location]._avenue,
                             CountLocation.objects[location]._period_matrix)
        return True

class CountLocation:

    lane_configurations = {}
    objects = {}

    def __init__(self, street, avenue, filepath):
        self._street = street
        self._avenue = avenue
        self._filepath = filepath
        self._count = 0
        self._EB = []
        self._NB = []
        self._SB = []
        self._WB = []
        self._EB_count = 0
        self._NB_count = 0
        self._SB_count = 0
        self._WB_count = 0
        self._EB_matrix = []
        self._NB_matrix = []
        self._SB_matrix = []
        self._WB_matrix = []
        self._period_matrix = []
        self._daily_counts = {}
        self._minimum_day = ''
        self._maximum_day = ''
        self._count_lanes = {}
        CountLocation.objects[(street, avenue)] = self

    def get_count(self):
        """Retrieve the object's count value.
        """
        return self._count

    def add_count(self, value):
        """Add a count value from a subsuming class to the current
        object's count.
        """
        self._count += value
        return True

    def add_east_count(self, value):
        """Add a count value from a subsuming class to the current
        object's EB count.
        """
        self._EB_count += value
        return True

    def add_north_count(self, value):
        """Add a count value from a subsuming class to the current
        object's NB count.
        """
        self._NB_count += value
        return True

    def add_south_count(self, value):
        """Add a count value from a subsuming class to the current
        object's SB count.
        """
        self._SB_count += value
        return True

    def add_west_count(self, value):
        """Add a count value from a subsuming class to the current
        object's WB count.
        """
        self._WB_count += value
        return True

    def load_lanes():
        csvin = open(os.getcwd() + '\\' + 'lane_config.csv', 'r')
        reader = csv.reader(csvin, delimiter=',', quotechar='|')
        loc = ('', '')
        for row in reader:
            if (row[0] != 'EB' and row[0] != 'NB' and
                row[0] != 'SB' and row[0] != 'WB' and row != []):
                loc = (row[0], row[1])
            elif row:
                if loc not in CountLocation.lane_configurations:
                    CountLocation.lane_configurations[loc] = {}
                CountLocation.lane_configurations[loc][row[0]] = [x for x in
                                                                  row[1:] if x]
        return True

    def load_files():
        for filepath in os.listdir(os.getcwd()):
            if not re.search('count', filepath):
                continue
            if filepath[-3:] == '.py' or filepath[-5:] == '.clso':
                continue
            first_re = re.compile('at')
            second_re = re.compile('[_|\.]')
            first = first_re.search(filepath)
            second = second_re.search(filepath)
            street = filepath[:first.span()[0]]
            avenue = filepath[first.span()[1]:second.span()[0]]
            count_location_object = CountLocation(street, avenue, filepath)
            count_location_object.set_lanes()
            count_location_object.process_file()
            count_location_object.count_subsumers()
        return True

    def set_lanes(self):
        if (self._street, self._avenue) in CountLocation.lane_configurations:
            self._EB = CountLocation.lane_configurations[(self._street,
                                                         self._avenue)]['EB']
            self._NB = CountLocation.lane_configurations[(self._street,
                                                         self._avenue)]['NB']
            self._SB = CountLocation.lane_configurations[(self._street,
                                                         self._avenue)]['SB']
            self._WB = CountLocation.lane_configurations[(self._street,
                                                         self._avenue)]['WB']
        else:
            print('Lane configurations not found')
        return True

    def load_records(self):
        return True
                
    def process_file(self):
        reader = open(os.getcwd() + '\\' + self._filepath, 'r')
        for line in reader:
            line = line.split(',')
            timestamp = line[1].split()
            self.pass_lane(line[0], timestamp[0], timestamp[1], int(line[2]))
                
    def pass_lane(self, lane, day, hour, count):
        """Pass data from a record to the correct count_lane object.
        """
        lane = str(int(lane))
        if lane not in self._count_lanes:
            CountLane(self._street, self._avenue, lane)
            self._count_lanes[lane] = True
        lane = CountLane.objects[(self._street, self._avenue, lane)]
        lane.pass_day(day, hour, count)
        return True

    def count_subsumers(self):
        """Add the count of all subsuming objects to the current
        object's count.
        """
        self._count = 0
        for lane in self._count_lanes:
            lane_obj = CountLane.objects[(self._street, self._avenue, lane)]
            lane_obj.count_subsumers()
            self.add_count(lane_obj.get_count())
            if lane in self._EB:
                self.add_east_count(lane_obj.get_count())
            if lane in self._NB:
                self.add_north_count(lane_obj.get_count())
            if lane in self._SB:
                self.add_south_count(lane_obj.get_count())
            if lane in self._WB:
                self.add_west_count(lane_obj.get_count())
        return True

    def set_daily_counts(self):
        self._daily_counts = {}
        for lane in self._count_lanes:
            lane_obj = CountLane.objects[(self._street, self._avenue, lane)]
            for day in lane_obj._count_days:
                day_obj = CountDay.objects[(self._street, self._avenue, lane,
                                            day)]
                if day not in self._daily_counts:
                    self._daily_counts[day]= {}
                hours = []
                for hour in sorted(day_obj._count_hours.keys()):
                    hour_obj = CountHour.objects[(self._street, self._avenue,
                                                  lane, day, hour)]
                    hours.append(hour_obj.get_count())
                self._daily_counts[day][lane] = hours
                if lane in self._EB:
                    self._daily_counts[day]['<EB>'] = self._daily_counts[day
                                        ].get('<EB>', 0) + day_obj.get_count()
                elif lane in self._NB:
                    self._daily_counts[day]['<NB>'] = self._daily_counts[day
                                        ].get('<NB>', 0) + day_obj.get_count()
                elif lane in self._SB:
                    self._daily_counts[day]['<SB>'] = self._daily_counts[day
                                        ].get('<SB>', 0) + day_obj.get_count()
                elif lane in self._WB:
                    self._daily_counts[day]['<WB>'] = self._daily_counts[day
                                        ].get('<WB>', 0) + day_obj.get_count()
        return True

    def set_direction_matrices(self, dates):
        self.set_daily_counts()
        self._EB_matrix = []
        self._NB_matrix = []
        self._SB_matrix = []
        self._WB_matrix = []
        self._period_matrix = []
        for day in sorted(self._daily_counts.keys()):
            if day in dates:
                for lane in sorted(self._daily_counts[day].keys()):
                    if not re.search('<[\w]*>', lane):
                        day_obj = CountDay.objects[(self._street, self._avenue,
                                                lane, day)]
                    if lane in self._EB:
                        self._EB_matrix.append(self._daily_counts[day][lane] +
                        [day_obj.get_count()])
                    elif lane in self._NB:
                        self._NB_matrix.append(self._daily_counts[day][lane] +
                        [day_obj.get_count()])
                    elif lane in self._SB:
                        self._SB_matrix.append(self._daily_counts[day][lane] +
                        [day_obj.get_count()])
                    elif lane in self._WB:
                        self._WB_matrix.append(self._daily_counts[day][lane] +
                        [day_obj.get_count()])
                self._period_matrix.append([self._daily_counts[day]['<EB>'],
                                            self._daily_counts[day]['<NB>'],
                                            self._daily_counts[day]['<SB>'],
                                            self._daily_counts[day]['<WB>'],
                                            (self._daily_counts[day]['<EB>'] +
                                             self._daily_counts[day]['<NB>'] +
                                             self._daily_counts[day]['<SB>'] +
                                             self._daily_counts[day]['<WB>'])])                 
        return True

class CountLane:

    objects = {}

    def __init__(self, street, avenue, lane):
        self._street = street
        self._avenue = avenue
        self._lane = lane
        self._count = 0
        self._count_days = {}
        CountLane.objects[(street, avenue, lane)] = self

    def get_count(self):
        """Retrieve the object's count value.
        """
        return self._count

    def add_count(self, value):
        """Add a count value from a subsuming class to the current
        object's count.
        """
        self._count += value
        return True

    def pass_day(self, day, hour, count):
        """Pass data from a record to the correct count_lane object.
        """
        if day not in self._count_days:
            CountDay(self._street, self._avenue, self._lane, day)
            self._count_days[day] = True
        day = CountDay.objects[(self._street, self._avenue, self._lane, day)]
        day.initialize_hour(hour, count)
        return True

    def count_subsumers(self):
        """Add the count of all subsuming objects to the current
        object's count.
        """
        self._count = 0
        for day in self._count_days:
            day_obj = CountDay.objects[(self._street, self._avenue, self._lane,
                                        day)]
            day_obj.count_subsumers()
            self.add_count(day_obj.get_count())
        return True
        
class CountDay:

    objects = {}

    def __init__(self, street, avenue, lane, day):
        self._street = street
        self._avenue = avenue
        self._lane = lane
        self._day = day
        self._datetime_value = datetime.datetime(int(day[0:4]), int(day[5:7]),
                                                 int(day[8:]))
        self._week = self._datetime_value.isocalendar()
        if (self._week[0], self._week[1]) not in Week.objects:
            Week(self._datetime_value)
        self._count = 0
        self._count_hours = {}
        CountDay.objects[(street, avenue, lane, day)] = self

    def get_count(self):
        """Retrieve the object's count value.
        """
        return self._count

    def add_count(self, value):
        """Add a count value from a subsuming class to the current
        object's count.
        """
        self._count += value
        return True

    def initialize_hour(self, hour, count):
        """Pass data from a record to the correct count_lane object.
        """
        CountHour(self._street, self._avenue, self._lane, self._day,
                  self._datetime_value, hour, count)
        self._count_hours[hour] = True
        return True

    def count_subsumers(self):
        """Add the count of all subsuming objects to the current
        object's count.
        """
        self._count = 0
        for hour in self._count_hours:
            hour_obj = CountHour.objects[(self._street, self._avenue,
                                          self._lane, self._day, hour)]
            self.add_count(hour_obj.get_count())
        return True

class CountHour:

    objects = {}

    def __init__(self, street, avenue, lane, day, datetime_value, hour, count):
        self._street = street
        self._avenue = avenue
        self._lane = lane
        self._day = day
        self._datetime_value = datetime_value
        self._hour = self._round_hour(datetime_value, hour)
        self._count = count
        CountHour.objects[(street, avenue, lane, day, hour)] = self

    def get_hour(self):
        """Retrieve the object's hour value.
        """
        return self._hour

    def get_count(self):
        """Retrieve the object's count value.
        """
        return self._count

    def _round_hour(self, datetime_value, hr):
        dt = datetime_value.replace(hour=int(hr[0:2]), minute=int(hr[3:5]),
                                    second=int(hr[6:]))
        self._datetime_value = dt
        seconds = (dt - dt.min).seconds
        rounding = (seconds+3600/2) // 3600 * 3600
        return dt + datetime.timedelta(0,rounding-seconds,-dt.microsecond)

class Week:

    objects = {}

    def __init__(self, date):
        self._year = date.isocalendar()[0]
        self._week = date.isocalendar()[1]
        if str(date.isocalendar()[2]) == '7':
            self._sunday = date
            self._saturday = date + datetime.timedelta(days=6)
        else:
            self._sunday = date - datetime.timedelta(
                                                days=(date.isocalendar()[2]))
            self._saturday = date + datetime.timedelta(
                                                days=(6-date.isocalendar()[2]))
        self._month = self._sunday.month
        self._day = self._sunday.day
        Week.objects[(self._year, self._month, self._day)] = self
        
"""
Minimal Interface-------------------------------------------------------
"""
start = time.clock()
Count()
print('Processing time: ' + str(time.clock() - start) + ' clocked seconds.')
