from __future__ import print_function

import os
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

    def __init__(self, config, default_filters=None):
        self.default_filters = default_filters or ('column', 'project', 'tag')
        self.config = config
        self.command = Command(self.config)
        for ac_type in self.default_filters:
            setattr(self, ac_type, [])

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
