from __future__ import print_function

import os
import re
import tasklib
import util

from process import Command

class TaskListModel(object):
    def __init__(self, task_config, reports, report=None, data_location=None):

        if not data_location:
            data_location = task_config.subtree('data.location')
        self.data_location = os.path.expanduser(data_location)
        self.tw = tasklib.TaskWarrior(self.data_location)
        self.reports = reports
        self.report = report
        self.tasks = []
        if report:
            self.update_report(report)

    def add(self, contact):
        pass

    def active_report(self):
        return self.reports[self.report]

    def update_report(self, report, extra_filters=[]):
        self.report = report
        active_report = self.active_report()
        filters = active_report['filter'] if 'filter' in active_report else []
        all_filters = filters + extra_filters
        self.tasks = self.tw.tasks.filter(*all_filters) if len(all_filters) > 0 else self.tw.tasks.all()

    def get_task(self, uuid):
        try:
            return self.tw.tasks.get(uuid=uuid)
        except tasklib.task.DoesNotExist:
            return False

    def task_id(self, uuid):
        try:
            task = self.tw.tasks.get(uuid=uuid)
            return task['id'] or util.uuid_short(task['uuid'])
        except tasklib.task.DoesNotExist:
            return False

    def task_description(self, uuid, description):
        task = self.get_task(uuid)
        if task:
            task['description'] = description
            task.save()
            return task
        return False

    def task_priority(self, uuid, priority):
        task = self.get_task(uuid)
        if task:
            task['priority'] = priority
            task.save()
            return task
        return False

    def task_project(self, uuid, project):
        task = self.get_task(uuid)
        if task:
            task['project'] = project
            task.save()
            return task
        return False

    def task_done(self, uuid):
        task = self.get_task(uuid)
        if task:
            task.done()
            return task
        return False

    def task_start_stop(self, uuid):
        task = self.get_task(uuid)
        if task:
            task.stop() if task.active else task.start()
            return task
        return False

    def task_tags(self, uuid, tags):
        task = self.get_task(uuid)
        if task:
            for tag in tags:
                marker = tag[0]
                if marker in ('+', '-'):
                    tag = tag[1:]
                    if marker == '+':
                        task['tags'].add(tag)
                    elif tag in task['tags']:
                        task['tags'].remove(tag)
                else:
                    task['tags'].add(tag)
            task.save()
            return task
        return False

#    def get_summary(self, report=None):
#        report = report or self.report
#        self.update_report(report)
#        summary = []
#        for task in self.tasks:
#            summary.append(self.build_task_row(task))
#        return summary
#
#    def _reload_list(self, new_value=None):
#        self._list_view.options = self._model.get_summary()
#        self._list_view.value = new_value

class TaskAutoComplete(object):

    def __init__(self, config, default_filters=None, extra_filters=None):
        self.default_filters = default_filters or ('column', 'project', 'tag')
        self.extra_filters = extra_filters or {}
        self.default_prefixes = {
            'column': {
                'suffixes': [':'],
            },
            'project': {
                'prefixes': ['project:'],
            },
            'tag': {
                'prefixes': ['+', '-'],
            },
        }
        self.config = config
        self.command = Command(self.config)
        for ac_type in self.default_filters:
            setattr(self, ac_type, [])
        for ac_type, items in list(self.extra_filters.items()):
            setattr(self, ac_type, items)
        self.reset()

    def refresh(self, filters=None):
        filters = filters or self.default_filters
        for ac_type in filters:
            setattr(self, ac_type, self.refresh_type(ac_type))

    def refresh_type(self, ac_type):
        command = 'task _%ss' % ac_type
        returncode, stdout, stderr = self.command.run(command, capture_output=True)
        if returncode == 0:
            return list(filter(lambda x: True if x else False, stdout.split("\n")))
        else:
            raise "Error running command '%s': %s" % (command, stderr)

    def make_entries(self, filters, prefixes):
        entries = []
        for ac_type in filters:
            items = getattr(self, ac_type)
            include_unprefixed = prefixes[ac_type]['include_unprefixed'] if ac_type in prefixes and 'include_unprefixed' in prefixes[ac_type] else False
            type_prefixes = prefixes[ac_type]['prefixes'] if ac_type in prefixes and 'prefixes' in prefixes[ac_type] else []
            type_suffixes = prefixes[ac_type]['suffixes'] if ac_type in prefixes and 'suffixes' in prefixes[ac_type] else []
            if include_unprefixed:
                for item in items:
                    entries.append((ac_type, item))
            for prefix in type_prefixes:
                for item in items:
                    entries.append((ac_type, '%s%s' % (prefix, item)))
            for suffix in type_suffixes:
                for item in items:
                    entries.append((ac_type, '%s%s' % (item, suffix)))
        entries.sort()
        return entries

    def setup(self, text_callback, filters=None, prefixes=None):
        if self.is_setup:
            self.reset()
        self.text_callback = text_callback
        if not filters:
            filters = self.default_filters
        if not prefixes:
            prefixes = self.default_prefixes
        self.refresh()
        self.entries = self.make_entries(filters, prefixes)
        self.root_only_filters = list(filter(lambda f: True if f in prefixes and 'root_only' in prefixes[f] else False, filters))
        self.is_setup = True

    def teardown(self):
        self.is_setup = False
        self.entries = []
        self.root_only_filters = []
        self.callback = None
        self.deactivate()

    def reset(self):
        self.teardown()

    def activate(self, text, edit_pos):
        if self.activated:
            self.send_tabbed_text(text, edit_pos)
            return
        if self.can_tab(text, edit_pos):
            self.activated = True
            self.generate_tab_options(text, edit_pos)
            self.send_tabbed_text(text, edit_pos)

    def deactivate(self):
        self.activated = False
        self.idx = 0
        self.tab_options = []
        self.root_search = False
        self.search_fragment = None
        self.prefix = None
        self.suffix = None

    def send_tabbed_text(self, text, edit_pos):
        tabbed_text, final_edit_pos = self.next_tab_item(text, edit_pos)
        self.text_callback(tabbed_text, final_edit_pos)

    def generate_tab_options(self, text, edit_pos):
        if self.root_search:
            if len(self.root_only_filters) > 0:
                self.tab_options = list(map(lambda e: e[1], filter(lambda e: True if e[0] in self.root_only_filters else False, self.entries)))
            else:
                self.tab_options = list(map(lambda e: e[1], self.entries))
        else:
            self.parse_text(text, edit_pos)
            exp = re.compile(self.search_fragment)
            if len(self.root_only_filters) > 0:
                self.tab_options = list(map(lambda e: e[1], filter(lambda e: True if e[0] not in self.root_only_filters and exp.match(e[1]) else False, self.entries)))
            else:
                self.tab_options = list(map(lambda e: e[1], filter(lambda e: True if exp.match(e[1]) else False, self.entries)))

    def parse_text(self, text, edit_pos):
        full_prefix = text[:edit_pos]
        prefix_parts = util.string_to_args(full_prefix)
        self.search_fragment = prefix_parts.pop()
        self.prefix = ' '.join(prefix_parts)
        self.suffix = text[(edit_pos + 1):]

    def can_tab(self, text, edit_pos):
        if edit_pos == 0:
            if text == '':
                self.root_search = True
                return True
            return False
        previous_pos = edit_pos - 1
        next_pos = edit_pos + 1
        return text[edit_pos:next_pos] in (' ', '') and text[previous_pos:edit_pos] not in (' ', '')

    def assemble(self, tab_option):
        parts = [self.prefix, tab_option, self.suffix]
        tabbed_text = ' '.join(filter(lambda p: True if p else False, parts))
        parts.pop()
        edit_pos_parts = ' '.join(filter(lambda p: True if p else False, parts))
        edit_pos_final = len(edit_pos_parts)
        return tabbed_text, edit_pos_final

    def increment_index(self):
        self.idx = self.idx + 1 if self.idx < len(self.tab_options) - 1 else 0

    def next_tab_item(self, text, edit_pos):
        tabbed_text = ''
        final_edit_pos = None
        if self.root_search:
            tabbed_text = self.tab_options[self.idx]
            self.increment_index()
        else:
            if len(self.tab_options) == 0:
                tabbed_text = text
            else:
                tabbed_text, final_edit_pos = self.assemble(self.tab_options[self.idx])
                self.increment_index()
        return tabbed_text, final_edit_pos

