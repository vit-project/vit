def get(name, task_config):
    subtree = task_config.subtree(r'^uda\.%s\.' % name, walk_subtree=False)
    if 'uda' in subtree and name in subtree['uda']:
        return subtree['uda'][name]
    return None
