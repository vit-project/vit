from vit import util
from vit.formatter.project import Project

class ProjectParent(Project):
    def format(self, project, task):
        parent = util.project_get_root(project)
        return (len(parent), self.markup_element(parent)) if parent else self.markup_none(self.colorizer.project_none())

