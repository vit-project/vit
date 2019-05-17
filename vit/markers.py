from vit import uda

MARKABLE_COLUMNS = [
    'depends',
    'description',
    'due',
    'project',
    'recur',
    'scheduled',
    'start',
    'status',
    'tags',
    'until',
]
LABEL_DEFAULTS = {
    'active.label': '(A)',
    'blocked.label': '(BD)',
    'blocking.label': '(BG)',
    'completed.label': '(C)',
    'deleted.label': '(X)',
    'due.label': '(D)',
    'due.today.label': '(DT)',
    'keyword.label': '(K)',
    'overdue.label': '(OD)',
    'project.label': '(P)',
    'project.none.label': '',
    'recurring.label': '(R)',
    'scheduled.label': '(S)',
    'tag.label': '(T)',
    'tag.none.label': '',
    'uda.label': '',
    'uda.priority.label': '(PR)',
    'until.label': '(U)',
}

class Markers(object):
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
        self.enabled = self.config.get('marker', 'enabled')
        if self.enabled:
            self.udas = uda.get_configured(self.task_config)
            self.markable_columns = MARKABLE_COLUMNS + list(self.udas.keys())
            self.configured_columns = self.config.get('marker', 'columns')
            self.set_columns()
            self.header_label = self.config.get('marker', 'header_label')
            self.require_color = self.config.get('marker', 'require_color')
            self.include_subprojects = self.config.get('marker', 'include_subprojects')
            self.compose_labels()
            self.set_none_label_attributes()

    def set_columns(self):
        self.columns = self.markable_columns if self.configured_columns == 'all' else self.configured_columns.split(',')

    def compose_labels(self):
        self.labels = LABEL_DEFAULTS.copy()
        for uda in list(self.udas.keys()):
            self.labels['uda.%s.none.label' % uda] = ''
        for key, value in self.config.items('marker'):
            if key not in self.config.defaults['marker']:
                self.labels[key] = value
        if self.include_subprojects:
            self.add_project_children()

    def set_none_label_attributes(self):
        for label_type in ['project', 'tag', 'uda.priority']:
            label = '%s.none.label' % label_type
            attr = '%s_has_none_marker' % label_type.replace('.', '_')
            has_marker = self.labels[label] != ''
            setattr(self, attr, has_marker)

    def add_project_children(self):
        project_prefix = 'project.'
        label_suffix = '.label'
        for label, marker in self.get_project_labels():
            for entry in self.task_config.projects:
                new_label = '%s%s' % (project_prefix, entry)
                if not self.has_label(new_label) and new_label.startswith(label[:-len(label_suffix)]):
                    self.labels['%s%s' % (new_label, label_suffix)] = marker

    def get_project_labels(self):
        return sorted([(label, marker) for label, marker in self.labels.items() if self.is_project_label(label)], reverse=True)

    def is_project_label(self, label):
        return label.startswith('project.') and label not in ['project.label', 'project.none.label']

    def has_label(self, label):
        return label in self.labels
