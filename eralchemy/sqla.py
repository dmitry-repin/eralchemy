"""
This module allows transforming SQLAlchemy metadata to intermediary syntax.
"""
import sys

from sqlalchemy.exc import CompileError

from eralchemy.models import Relation, Column, Table


if sys.version_info[0] == 3:
    unicode = str


def relation_to_intermediary(fk):
    """
    Transforms an SQLAlchemy ForeignKey object to its intermediary
    representation.
    """
    parent = fk.parent
    referred = fk.column

    return Relation(
        left_col=format_name(parent.table.fullname),
        right_col=format_name(referred.table.fullname),
        left_cardinality='*' if parent.nullable else '+',
        right_cardinality='?' if referred.nullable else '1',
    )


def format_type(typ):
    """ Transforms the type into a nice string representation.
    """
    try:
        return unicode(typ)
    except CompileError:
        return 'Null'


def format_name(name):
    """ Transforms the name into a nice string representation.
    """
    return unicode(name)


def column_to_intermediary(col, type_formatter=format_type):
    """ Transforms an SQLAlchemy Column object to it's intermediary
    representation.
    """
    return Column(
        name=col.name,
        type=type_formatter(col.type),
        is_key=col.primary_key,
    )


def table_to_intermediary(table):
    """ Transforms an SQLAlchemy Table object to it's intermediary
    representation.
    """
    return Table(
        name=table.fullname,
        columns=[column_to_intermediary(col) for col in table.c._data.values()]
    )


def metadata_to_intermediary(metadata):
    """ Transforms SQLAlchemy metadata to the intermediary representation.
    """
    tables = [
        table_to_intermediary(table) for table in metadata.tables.values()
    ]
    relationships = [
        relation_to_intermediary(fk)
        for table in metadata.tables.values()
        for fk in table.foreign_keys
    ]
    return tables, relationships


def declarative_to_intermediary(base):
    """Transforms an SQLAlchemy Declarative Base to the intermediary
    representation.
    """
    return metadata_to_intermediary(base.metadata)


def name_for_scalar_relationship(base, local_cls, referred_cls, constraint):
    """ Overrides naming schemes.
    """
    name = referred_cls.__name__.lower() + "_ref"
    return name


def database_to_intermediary(database_uri, schema=None):
    """ Introspects from the database (given the database_uri) to create the
    intermediary representation.
    """
    from sqlalchemy.ext.automap import automap_base
    from sqlalchemy import create_engine

    Base = automap_base()
    engine = create_engine(database_uri)
    if schema is not None:
        Base.metadata.schema = schema

    # reflect the tables
    Base.prepare(
        engine,
        reflect=True,
        name_for_scalar_relationship=name_for_scalar_relationship
    )
    return declarative_to_intermediary(Base)
