from vit.formatter import String

class Project(String):
    def __init__(self, column, report, defaults, blocking_task_uuids, **kwargs):
        super().__init__(column, report, defaults, blocking_task_uuids)
        self.indent_subprojects = self.is_subproject_indentable()

    def format(self, project, task):
        return self.format_project(project, task) if project else self.markup_none(self.colorizer.project_none())

    def format_project(self, project, task):
        return self.format_subproject_indented(project, task) if self.indent_subprojects else (len(project), self.markup_element(project))

    def format_subproject_indented(self, project, task):
        parts = project.split('.')
        (width, spaces, marker, subproject) = self.formatter.format_subproject_indented(parts)
        return (width, [spaces, marker, (self.colorize(project), subproject)])

    def is_subproject_indentable(self):
        return self.formatter.config.subproject_indentable and self.report['subproject_indentable']

    def colorize(self, project):
        return self.colorizer.project(project)
