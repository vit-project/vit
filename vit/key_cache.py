from functools import reduce

class KeyCacheError(Exception):
    pass

class KeyCache(object):
    def __init__(self, keybindings):
        self.keybindings = keybindings
        self.cached_keys = ''
        self.build_multi_key_cache()

    def get(self, key=None):
        return '%s%s' % (self.cached_keys, key) if key else self.cached_keys

    def set(self, keys=''):
        self.cached_keys = keys

    def is_keybinding(self, keys):
        return keys in self.keybindings

    def sort_keybindings_by_len(self, keybindings, min_len=1):
        max_key_length = len(max(keybindings, key=len))
        def reducer(accum, key_length):
            accum.append([v for k, v in enumerate(keybindings) if len(keybindings[k]) == key_length])
            return accum
        sorted_keybindings = reduce(reducer, range(max_key_length, min_len, -1), [])
        return list(filter(None, sorted_keybindings))

    def get_non_modified_keybindings(self):
        return [k for k in self.keybindings if self.keybindings[k]['has_special_keys'] or not self.keybindings[k]['has_modifier']]

    def add_keybinding_to_key_cache(self, to_cache, keybinding, existing_keybindings, key_cache):
        if to_cache in existing_keybindings:
            raise KeyCacheError("Invalid key binding '%s', '%s' already used in another key binding" % (keybinding, to_cache))
        else:
            key_cache[to_cache] = True

    def build_multi_key_cache(self):
        keybindings = self.get_non_modified_keybindings()
        sorted_keybindings = self.sort_keybindings_by_len(keybindings)
        def sorted_keybindings_reducer(key_cache, keybinding_list):
            def keybinding_list_reducer(_, keybinding):
                keys = list(keybinding)
                keys.pop()
                def keybinding_reducer(processed_keys, key):
                    processed_keys.append(key)
                    to_cache = ''.join(processed_keys)
                    self.add_keybinding_to_key_cache(to_cache, keybinding, keybindings, key_cache)
                    return processed_keys
                reduce(keybinding_reducer, keys, [])
            reduce(keybinding_list_reducer, keybinding_list, [])
            return key_cache
        self.multi_key_cache = reduce(sorted_keybindings_reducer, sorted_keybindings, {})
