from importlib import import_module
from datetime import datetime, timedelta
from tzlocal import get_localzone
from pytz import timezone

from vit import util
from vit import uda

INDICATORS = [
    'active',
    'dependency',
    'recurrence',
    'tag',
]
UDA_DEFAULT_INDICATOR = 'U'

DEFAULT_DESCRIPTION_TRUNCATE_LEN=20

class FormatterBase(object):
    def __init__(self, loader, config, task_config, markers, task_colorizer):
        self.loader = loader
        self.config = config
        self.task_config = task_config
        self.markers = markers
        self.task_colorizer = task_colorizer
        self.date_default = self.task_config.translate_date_markers(self.task_config.subtree('dateformat')["default"])
        self.report = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.report')) or self.date_default
        self.annotation = self.task_config.translate_date_markers(self.task_config.subtree('dateformat.annotation')) or self.date_default
        self.description_truncate_len = DEFAULT_DESCRIPTION_TRUNCATE_LEN
        self.zone = get_localzone()
        self.epoch_datetime = datetime(1970, 1, 1, tzinfo=timezone('UTC'))
        self.due_days = int(self.task_config.subtree('due'))
        self.none_label = config.get('color', 'none_label')
        self.build_indicators()

    def build_indicators(self):
        for indicator in INDICATORS:
            label = self.task_config.subtree('%s.indicator' % indicator)
            setattr(self, 'indicator_%s' % indicator, label)
        self.indicator_uda = {}
        for uda_name in uda.get_configured(self.task_config).keys():
            label = self.task_config.subtree('uda.%s.indicator' % uda_name) or UDA_DEFAULT_INDICATOR
            self.indicator_uda[uda_name] = label

    def get_module_class_from_parts(self, parts):
        formatter_module_name = '_'.join(parts)
        formatter_class_name = util.file_to_class_name(formatter_module_name)
        return formatter_module_name, formatter_class_name

    def get_user_formatter_class(self, parts):
        formatter_module_name, formatter_class_name = self.get_module_class_from_parts(parts)
        return self.loader.load_user_class('formatter', formatter_module_name, formatter_class_name)

    def get_formatter_class(self, parts):
        formatter_module_name, formatter_class_name = self.get_module_class_from_parts(parts)
        try:
            formatter_module = import_module('vit.formatter.%s' % formatter_module_name)
            formatter_class = getattr(formatter_module, formatter_class_name)
            return formatter_class
        except ImportError:
            return None

    def get(self, column_formatter):
        parts = column_formatter.split('.')
        name = parts[0]

        formatter_class = self.get_user_formatter_class(parts)
        if formatter_class:
            return name, formatter_class

        formatter_class = self.get_formatter_class(parts)
        if formatter_class:
            return name, formatter_class

        uda_metadata = uda.get(name, self.task_config)
        if uda_metadata:
            is_indicator = parts[-1] == 'indicator'
            if is_indicator:
                formatter_class = self.get_formatter_class(['uda', 'indicator'])
                return name, formatter_class
            else:
                uda_type = uda_metadata['type'] if 'type' in uda_metadata else 'string'
                formatter_class = self.get_formatter_class(['uda', uda_type])
                if formatter_class:
                    return name, formatter_class
        return name, Formatter

    def format_subproject_indented(self, project_parts):
        if len(project_parts) == 1:
            subproject = project_parts[0]
            return (len(subproject), '', '', subproject)
        else:
            subproject = project_parts.pop()
            space_padding = (len(project_parts) * 2) - 1
            indicator = u'\u21aa '
            width = space_padding + len(indicator) + len(subproject)
            return (width, ' ' * space_padding , indicator, subproject)

    def recalculate_due_datetimes(self):
        self.now = datetime.now(self.zone)
        # NOTE: For some reason using self.zone for the tzinfo below results
        # in the tzinfo object having a zone of 'LMT', which is wrong. Using
        # the tzinfo associated with self.now returns the correct value, no
        # idea why this glitch happens.
        self.end_of_day = datetime(self.now.year, self.now.month, self.now.day, 23, 59, 59, tzinfo=self.now.tzinfo)
        self.due_soon = self.end_of_day + timedelta(days=self.due_days)

    def get_due_state(self, due, task):
        if util.task_pending(task):
            if due < self.now:
                return 'overdue'
            elif due <= self.end_of_day:
                return 'due.today'
            elif due < self.due_soon:
                return 'due'
        return None

    def get_active_state(self, start, task):
        end = task['end']
        return util.task_pending(task) and start and start <= self.now and (not end or end > self.now)

    def get_scheduled_state(self, scheduled, task):
        return scheduled and not util.task_completed(task)

    def get_until_state(self, until, task):
        return until and not util.task_completed(task)


