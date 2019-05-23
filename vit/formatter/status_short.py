from vit.formatter.status import Status

class StatusShort(Status):

    def status_format(self, status):
        return status[0].upper()
