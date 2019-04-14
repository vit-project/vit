from formatter import String

class Project(String):
    def __init__(self, report, defaults, **kwargs):
        super().__init__(report, defaults)
        self.indent_subprojects = self.is_subproject_indentable()

    def format(self, project, task):
        return self.format_project(project, task) if project else ''

    def format_project(self, project, task):
        return self.format_subproject_indented(project, task) if self.indent_subprojects else project

    def format_subproject_indented(self, project, task):
        parts = project.split('.')
        return self.defaults.format_subproject_indented(parts)

    def is_subproject_indentable(self):
        return self.defaults.config.subproject_indentable and self.report['subproject_indentable']
