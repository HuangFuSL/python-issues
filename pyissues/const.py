_HOME_URL = "https://bugs.python.org/"
_ISSUE_URL = "https://bugs.python.org/issue%d"
_ISSUE_LIST = "https://bugs.python.org/issue?@action=export_csv&@columns=id,status&@sort=id"

_STATUS = {
    1: 'open',
    2: 'closed',
    3: 'pending',
    4: 'languishing',
}

_METAFIELD = ['created', 'created_by', 'last_changed', 'last_changed_by']

_ISSUE_FIELD = {
    'title', 'type', 'stage', 'components', 'versions', 'status', 'resolution',
    'dependencies', 'superseder', 'assigned_to', 'nosy_list', 'priority',
    'keywords', 'files', 'pull_requests', 'messages', '_id'
} | set(_METAFIELD)


_ISSUE_ATTRIBUTES = {
    'title', 'type', 'stage', 'status', 'resolution',
    'dependencies', 'superseder', 'assigned_to', 'priority', '_id'
} | set(_METAFIELD)

_ISSUE_MULTIPLE_ATTRIBUTES = {
    'keywords', 'nosy_list', 'versions', 'components'
}

_ISSUE_NODES = {
    'files', 'pull_requests'
}

_ISSUE_COMPLEX = {
    'messages'
}

_COMMENT_FIELD = {
    'url', 'author', 'content', 'date'
}

_SPLIT_NEEDED = {
    'files': ('uploaded', 'date'),
    'pull_requests': ('linked', 'date')
}
