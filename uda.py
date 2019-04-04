def get(name, task_config):
    subtree = task_config.subtree('^uda\.%s\.' % name)
    if 'uda' in subtree and name in subtree['uda']:
        return subtree['uda'][name]
    return None
