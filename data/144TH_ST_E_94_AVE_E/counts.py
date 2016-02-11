
import csv
import datetime
import os

class CountPeriod:
    """Class with period objects for the purpose of building .csv files
    as output that contain each day in the range. This will also build
    a total for the period.
    """

    def __init__(self, year, month, day, period):
        self._year = year
        self._month = month
        self._day = day
        self._period = period
        self._dates = []
        self._EB = 0
        self._NB = 0
        self._SB = 0
        self._WB = 0
        self._count_days = []
        self.set_period_counts()
        self.export_period_counts()

    def get_EB(self):
        """Function to return self._EB.
        """
        return self._EB

    def get_NB(self):
        """Function to return self._NB.
        """
        return self._NB

    def get_SB(self):
        """Function to return self._SB.
        """
        return self._SB

    def get_WB(self):
        """Function to return self._WB.
        """
        return self._WB

    def add_EB(self, value):
        """Add a record's count to the file's EB count.
        """
        self._EB += value
        return True

    def add_NB(self, value):
        """Add a record's count to the file's NB count.
        """
        self._NB += value
        return True

    def add_SB(self, value):
        """Add a record's count to the file's SB count.
        """
        self._SB += value
        return True

    def add_WB(self, value):
        """Add a record's count to the file's WB count.
        """
        self._WB += value
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
        return year, month, day

    def set_range(self):
        """Build a range of dates for the length of the period.
        """
        start = datetime.datetime(int(self._year), int(self._month),
                                  int(self._day))
        self._dates = [start + datetime.timedelta(days=x) for x in range(0,
                                                        int(self._period))]
        return True

    def set_count_days(self):
        """Build CountDay objects for each day in the period.
        """
        self.set_range()
        for date in self._dates:
            year, month, day = self.configure_values(date.year,
                                                        date.month, date.day)
            count_day_obj = CountDay(year, month, day, date)
            self._count_days.append(count_day_obj)

    def set_period_counts(self):
        """Sum all CountDay object counts for each direction.
        """
        self.set_count_days()
        for obj in self._count_days:
            self.add_EB(obj.get_EB())
            self.add_NB(obj.get_NB())
            self.add_SB(obj.get_SB())
            self.add_WB(obj.get_WB())
        return True

    def export_period_counts(self):
        csvout = open(os.getcwd() + '\\' + self._year + self._month +
                      self._day + self._period + '.csv', 'w', newline='')
        writer = csv.writer(csvout, delimiter=',', quotechar='|')
        for date in self._count_days:
            writer.writerow([date._datetime_value.strftime('%A'),
                             (date._datetime_value.strftime('%B')+' '+date._day
                              +' '+date._datetime_value.strftime('%Y'))])
            writer.writerow(['Hour', 'EB', 'NB', 'SB', 'WB'])
            for hour in sorted(date._count_hours.keys()):
                writer.writerow([str(hour) + ':00',
                                 date._count_hours[hour].get_EB(),
                                 date._count_hours[hour].get_NB(),
                                 date._count_hours[hour].get_SB(),
                                 date._count_hours[hour].get_WB()])
            writer.writerow([])
        return True
            
class CountDay:

    def __init__(self, year, month, day, datetime_value):
        self._year = year
        self._month = month
        self._day = day
        self._datetime_value = datetime_value
        self._hours = {}
        self._EB = 0
        self._NB = 0
        self._SB = 0
        self._WB = 0
        self._count_hours = {}
        self.set_day_counts()

    def get_EB(self):
        """Function to return self._EB.
        """
        return self._EB

    def get_NB(self):
        """Function to return self._NB.
        """
        return self._NB

    def get_SB(self):
        """Function to return self._SB.
        """
        return self._SB

    def get_WB(self):
        """Function to return self._WB.
        """
        return self._WB

    def add_EB(self, value):
        """Add a record's count to the file's EB count.
        """
        self._EB += value
        return True

    def add_NB(self, value):
        """Add a record's count to the file's NB count.
        """
        self._NB += value
        return True

    def add_SB(self, value):
        """Add a record's count to the file's SB count.
        """
        self._SB += value
        return True

    def add_WB(self, value):
        """Add a record's count to the file's WB count.
        """
        self._WB += value
        return True

    def set_select_files(self):
        for filepath in os.listdir(os.getcwd()):
            if (filepath[0:4] == self._year and
                filepath[5:7] == self._month and
                filepath[8:10] == self._day):
                hour = filepath[11:13]
                if hour not in self._hours:
                    self._hours[hour] = []
                self._hours[hour] = self._hours.get(hour, 0) + [filepath]
        return True

    def set_count_hours(self):
        for hour in self._hours:
            self._count_hours[hour] = CountHour(self, hour, self._hours[hour])
        return True

    def set_day_counts(self):
        """Sum all CountHour object counts for each direction.
        """
        self.set_select_files()
        self.set_count_hours()
        for hour in self._count_hours:
            self.add_EB(self._count_hours[hour].get_EB())
            self.add_NB(self._count_hours[hour].get_NB())
            self.add_SB(self._count_hours[hour].get_SB())
            self.add_WB(self._count_hours[hour].get_WB())
        return True

class CountHour:

    def __init__(self, count_day, hour, filepaths):
        self._count_day = count_day
        self._hour = hour
        self._filepaths = filepaths
        self._EB = 0
        self._NB = 0
        self._SB = 0
        self._WB = 0
        self._count_files = []
        self.set_hour_counts()

    def get_EB(self):
        """Function to return self._EB.
        """
        return self._EB

    def get_NB(self):
        """Function to return self._NB.
        """
        return self._NB

    def get_SB(self):
        """Function to return self._SB.
        """
        return self._SB

    def get_WB(self):
        """Function to return self._WB.
        """
        return self._WB

    def add_EB(self, value):
        """Add a record's count to the file's EB count.
        """
        self._EB += value
        return True

    def add_NB(self, value):
        """Add a record's count to the file's NB count.
        """
        self._NB += value
        return True

    def add_SB(self, value):
        """Add a record's count to the file's SB count.
        """
        self._SB += value
        return True

    def add_WB(self, value):
        """Add a record's count to the file's WB count.
        """
        self._WB += value
        return True

    def set_count_files(self):
        
        for filepath in self._filepaths:
            count_file_obj = CountFile(self._count_day, self, filepath)
            self._count_files.append(count_file_obj)
        return True

    def set_hour_counts(self):
        """Sum all CountFile object counts for each direction.
        """
        self.set_count_files()
        for obj in self._count_files:
            self.add_EB(obj.get_EB())
            self.add_NB(obj.get_NB())
            self.add_SB(obj.get_SB())
            self.add_WB(obj.get_WB())
        return True

class CountFile:

    def __init__(self, count_day, count_hour, filepath):
        self._count_day = count_day
        self._count_hour = count_hour
        self._filepath = filepath
        self._EB = 0
        self._NB = 0
        self._SB = 0
        self._WB = 0
        self._count_records = []
        self.set_file_counts()

    def get_EB(self):
        """Function to return self._EB.
        """
        return self._EB

    def get_NB(self):
        """Function to return self._NB.
        """
        return self._NB

    def get_SB(self):
        """Function to return self._SB.
        """
        return self._SB

    def get_WB(self):
        """Function to return self._WB.
        """
        return self._WB

    def add_EB(self, value):
        """Add a record's count to the file's EB count.
        """
        self._EB += value
        return True

    def add_NB(self, value):
        """Add a record's count to the file's NB count.
        """
        self._NB += value
        return True

    def add_SB(self, value):
        """Add a record's count to the file's SB count.
        """
        self._SB += value
        return True

    def add_WB(self, value):
        """Add a record's count to the file's WB count.
        """
        self._WB += value
        return True

    def set_count_records(self):
        """Extract each record from the file and set its values using
        the CountRecords class (as an object).
        """
        reader = open(self._filepath, 'r')
        records = []
        for row in reader:
            records.append(row.split(','))
        for record in records[1:]:
            timestamp = record[0].split()
            count_record_obj = CountRecord(self, timestamp[0], timestamp[1],
                                           int(record[4]), int(record[34]),
                                           int(record[64]), int(record[94]))
            self._count_records.append(count_record_obj)
        return True

    def set_file_counts(self):
        """Sum all CountRecord object counts for each direction.
        """
        self.set_count_records()
        for obj in self._count_records:
            self.add_EB(obj.get_EB())
            self.add_NB(obj.get_NB())
            self.add_SB(obj.get_SB())
            self.add_WB(obj.get_WB())
        return True

class CountRecord:

    def __init__(self, count_file, day, time, EB, NB, SB, WB):
        self._count_file = count_file
        self._day = day
        self._time = time
        self._EB = EB
        self._NB = NB
        self._SB = SB
        self._WB = WB

    def get_EB(self):
        """Function to return self._EB.
        """
        return self._EB

    def get_NB(self):
        """Function to return self._NB.
        """
        return self._NB

    def get_SB(self):
        """Function to return self._SB.
        """
        return self._SB

    def get_WB(self):
        """Function to return self._WB.
        """
        return self._WB

"""
Minimal Interface-------------------------------------------------------
"""
# Retrieve user inputs
year = input('Enter year: ')
month = input('Enter month: ')
day = input('Enter day: ')
period = input('Enter number of days: ')

# Try creating the CountPeriod object
count_period_obj = CountPeriod(year, month, day, period)

# Print summarized counts as a test
print('East: ', count_period_obj.get_EB())
print('North: ', count_period_obj.get_NB())
print('South: ', count_period_obj.get_SB())
print('West: ', count_period_obj.get_WB())
        
