from vit.formatter.project import Project

class ProjectIndented(Project):
    def format(self, obj, task):
        return 'N/A, use indent_subprojects setting'

