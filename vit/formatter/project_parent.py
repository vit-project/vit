from vit import util
from vit.formatter.project import Project
from vit.util import unicode_len

class ProjectParent(Project):
    def format(self, project, task):
        parent = util.project_get_root(project)
        return (unicode_len(parent), self.markup_element(parent)) if parent else self.markup_none(self.colorizer.project_none())

