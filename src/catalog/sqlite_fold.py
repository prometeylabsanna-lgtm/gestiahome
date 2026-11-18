"""Згортання регістру для пошуку. SQLite сам не згортає українські літери."""


def fold_text(value):
    if value is None:
        return ""
    return str(value).casefold()


def register_sqlite_fold(sender, connection, **kwargs):
    del sender, kwargs
    if connection.vendor != "sqlite":
        return
    connection.connection.create_function("py_fold", 1, fold_text, deterministic=True)
