from formatter import Marker

class Markers(Marker):
    def format(self, _, task):
        if task['tags']:
            return '(T)'
        else:
            return ''

    def display_attr(self, column, task):
        if column == 'tags' and task['tags']:
            return 'color.tagged'
        return None
