from formatter import String

class Project(String):
    def __init__(self, report, defaults, **kwargs):
        super().__init__(report, defaults)
        self.indent_subprojects = self.is_subproject_indentable()

    def format(self, project, task):
        return self.format_project(project, task) if project else (0, '')

    def format_project(self, project, task):
        return self.format_subproject_indented(project, task) if self.indent_subprojects else (len(project), self.markup_element(project))

    def format_subproject_indented(self, project, task):
        parts = project.split('.')
        (width, spaces, marker, subproject) = self.defaults.format_subproject_indented(parts)
        return (width, [spaces, marker, (self.color(project), subproject)])

    def is_subproject_indentable(self):
        return self.defaults.config.subproject_indentable and self.report['subproject_indentable']

    def color(self, project):
        display_attr = 'color.project.%s' % project
        return display_attr if self.has_display_attr(display_attr) else None
