import datetime
import types
from unittest import mock

import pytest

from tests import errors


@pytest.mark.parametrize(
    "kwargs",
    (
            dict(),
            dict(name="John"),
            dict(age=42),
            dict(name="John", age=42),
            dict(name="John", age=42, ts=53452345.3465),
            dict(name="John", age="Karl", ts=datetime.datetime.now()),
    ),
)
def test_templating(kwargs):
    with pytest.raises(ValueError):
        errors.ComplexTemplateOnlyError(**kwargs)


@mock.patch("izulu.root.Error._hook")
@mock.patch("izulu.root.Error._Error__process_template")
@mock.patch("izulu.root.Error._Error__populate_attrs")
@mock.patch("izulu.root.Error._Error__process_features")
def test_init(fake_proc_ftrs, fake_set_attrs, fake_proc_tpl, fake_hook):
    fake_proc_tpl.return_value = errors.RootError.__template__
    overriden_message = "overriden message"
    fake_hook.return_value = overriden_message
    store = getattr(errors.RootError, "_Error__cls_store")
    manager = mock.Mock()
    manager.attach_mock(fake_proc_ftrs, "fake_proc_ftrs")
    manager.attach_mock(fake_set_attrs, "fake_set_attrs")
    manager.attach_mock(fake_proc_tpl, "fake_proc_tpl")
    manager.attach_mock(fake_hook, "fake_hook")
    expected_calls = [mock.call.fake_proc_ftrs(),
                      mock.call.fake_set_attrs(),
                      mock.call.fake_proc_tpl({}),
                      mock.call.fake_hook(store,
                                          {},
                                          errors.RootError.__template__)]

    e = errors.RootError()

    assert manager.mock_calls == expected_calls
    assert str(e) == overriden_message


@pytest.mark.parametrize(
    ("kls", "fields", "hints", "registered", "defaults"),
    (
            (
                    errors.RootError,
                    frozenset(),
                    types.MappingProxyType({}),
                    frozenset(),
                    frozenset(),
            ),
            (
                    errors.TemplateOnlyError,
                    frozenset(("name", "age")),
                    types.MappingProxyType({}),
                    frozenset(("name", "age")),
                    frozenset(),
            ),
            (
                    errors.AttributesOnlyError,
                    frozenset(),
                    types.MappingProxyType(dict(name=str, age=int)),
                    frozenset(("name", "age")),
                    frozenset(),
            ),
            (
                    errors.AttributesWithStaticDefaultsError,
                    frozenset(),
                    types.MappingProxyType(dict(name=str, age=int)),
                    frozenset(("name", "age")),
                    frozenset(("age",)),
            ),
            (
                    errors.AttributesWithDynamicDefaultsError,
                    frozenset(),
                    types.MappingProxyType(dict(name=str, age=int)),
                    frozenset(("name", "age")),
                    frozenset(("age",)),
            ),
            (
                    errors.ClassVarsError,
                    frozenset(),
                    types.MappingProxyType({}),
                    frozenset(),
                    frozenset(),
            ),
            (
                    errors.MixedError,
                    frozenset(("name", "age", "note")),
                    types.MappingProxyType(dict(name=str,
                                                age=int,
                                                timestamp=datetime.datetime,
                                                my_type=str)),
                    frozenset(("name", "age", "note", "timestamp", "my_type")),
                    frozenset(("age", "timestamp", "my_type")),
            ),
            (
                    errors.DerivedError,
                    frozenset(("name", "surname", "age", "note")),
                    types.MappingProxyType(dict(name=str,
                                                age=int,
                                                timestamp=datetime.datetime,
                                                my_type=str,
                                                surname=str,
                                                location=tuple[float, float],
                                                updated_at=datetime.datetime,
                                                full_name=str,
                                                box=dict)),
                    frozenset(("name",
                               "age",
                               "note",
                               "timestamp",
                               "my_type",
                               "surname",
                               "location",
                               "updated_at",
                               "full_name",
                               "box")),
                    frozenset(("age",
                               "timestamp",
                               "my_type",
                               "location",
                               "updated_at",
                               "full_name")),
            ),
    )
)
def test_class_stores(kls, fields, hints, registered, defaults):
    """validates root.Error.__init_subclass__"""

    store = getattr(kls, "_Error__cls_store")

    assert type(store.fields) is type(fields)
    assert store.fields == fields
    assert type(store.hints) is type(hints)
    assert store.hints == hints
    assert type(store.registered) is type(registered)
    assert store.registered == registered
    assert type(store.defaults) is type(defaults)
    assert store.defaults == defaults
