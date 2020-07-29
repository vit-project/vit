import datetime
from vit.formatter import DateTime

# TODO: Remove this once tasklib bug is fixed.
from tasklib.serializing import SerializingObject
serializer = SerializingObject({})

class UdaDate(DateTime):
    def format(self, dt, task):
        if not dt:
            return self.markup_none(self.colorize())
        # TODO: Remove this once tasklib bug is fixed.
        # https://github.com/robgolding/tasklib/issues/30
        dt = dt if isinstance(dt, datetime.datetime) else serializer.timestamp_deserializer(dt)
        formatted_date = dt.strftime(self.custom_formatter or self.formatter.report)
        return (len(formatted_date), (self.colorize(dt), formatted_date))
    def colorize(self, dt=None):
        return self.colorizer.uda_date(self.column, dt)
