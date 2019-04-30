import datetime
from formatter import DateTime

class UdaDate(DateTime):
    def format(self, dt, task):
        if not dt:
            return self.markup_none(self.colorize())
        # TODO: This is wrong, tasklib should convert this, need a way to convert
        # '20190429T070000Z' to a datetime for now.
        #dt = dt if isinstance(dt, datetime.datetime) else datetime.datetime.now()
        #formatted_date = dt.strftime(self.custom_formatter or self.defaults.report)
        formatted_date = dt
        return (len(formatted_date), (self.colorize(dt), formatted_date))
    def colorize(self, dt=None):
        return self.colorizer.uda_date(self.column, dt)
