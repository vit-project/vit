import os
from functools import reduce

import tasklib
from tasklib.task import Task
from tasklib.backends import TaskWarriorException

from vit import util
from vit.exception import VitException

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

    def parse_error(self, err):
        messages = filter(lambda l : l.startswith('Error:'), str(err).splitlines())
        return "\n".join(messages)

    def update_report(self, report, context_filters=[], extra_filters=[]):
        self.report = report
        active_report = self.active_report()
        report_filters = active_report['filter'] if 'filter' in active_report else []
        filters = self.build_task_filters(context_filters, report_filters, extra_filters)
        try:
            self.tasks = self.tw.tasks.filter(filters) if filters else self.tw.tasks.all()
            # NOTE: tasklib uses lazy loading and some operation is necessary
            # for self.tasks to actually be populated here.
            # See https://github.com/robgolding/tasklib/issues/81
            len(self.tasks)
        except TaskWarriorException as err:
            raise VitException(self.parse_error(err))

    def build_task_filters(self, *all_filters):
        def reducer(accum, filters):
            if filters:
                accum.append('( %s )' % ' '.join(filters))
            return accum
        filter_parts = reduce(reducer, all_filters, [])
        return ' '.join(filter_parts) if filter_parts else ''

    def get_task(self, uuid):
        try:
            return self.tw.tasks.get(uuid=uuid)
        except Task.DoesNotExist:
            return False

    def task_id(self, uuid):
        try:
            task = self.tw.tasks.get(uuid=uuid)
            return util.task_id_or_uuid_short(task)
        except Task.DoesNotExist:
            return False

    def task_description(self, uuid, description):
        task = self.get_task(uuid)
        if task:
            task['description'] = description
            task.save()
            return task
        return False

    def task_annotate(self, uuid, description):
        task = self.get_task(uuid)
        if task:
            task.add_annotation(description)
            return task
        return False

    def task_denotate(self, uuid, annotation):
        task = self.get_task(uuid)
        if task:
            task.remove_annotation(annotation)
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
            try:
                task.done()
                return True, task
            except (Task.CompletedTask, Task.DeletedTask) as e:
                return False, e
        return False, None

    def task_delete(self, uuid):
        task = self.get_task(uuid)
        if task:
            try:
                task.delete()
                return True, task
            except Task.DeletedTask as e:
                return False, e
        return False, None

    def task_start_stop(self, uuid):
        task = self.get_task(uuid)
        if task:
            try:
                task.stop() if task.active else task.start()
                return True, task
            except (Task.CompletedTask, Task.DeletedTask, Task.ActiveTask, Task.InactiveTask) as e:
                return False, e
        return False, None

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
