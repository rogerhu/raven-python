# -*- coding: utf-8 -*-
import pytest
import uuid

from raven.utils import six
from raven.utils.testutils import TestCase
from raven.utils.serializer import transform


class TransformTest(TestCase):
    @pytest.mark.skipif('six.PY3')
    def test_incorrect_unicode(self):
        x = six.b('רונית מגן')
        result = transform(x)

        assert result == six.b("'רונית מגן'")

    @pytest.mark.skipif('six.PY3')
    def test_truncating_unicode(self):
        # 'רונית מגן'
        x = six.u('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df')

        result = transform(x, string_max_length=5)
        assert result == six.u("u'\u05e8\u05d5\u05e0\u05d9\u05ea'")

    @pytest.mark.skipif('not six.PY3')
    def test_unicode_in_python3(self):
        # 'רונית מגן'
        x = six.u('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df')

        result = transform(x)
        assert result == six.u("'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'")

    @pytest.mark.skipif('six.PY3')
    def test_unicode_in_python2(self):
        # 'רונית מגן'
        x = six.u('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df')

        result = transform(x)
        assert result == six.u("u'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'")

    @pytest.mark.skipif('not six.PY3')
    def test_string_in_python3(self):
        # 'רונית מגן'
        x = six.b('hello world')

        result = transform(x)
        assert result == "b'hello world'"

    @pytest.mark.skipif('six.PY3')
    def test_string_in_python2(self):
        # 'רונית מגן'
        x = six.b('hello world')

        result = transform(x)
        assert result == "'hello world'"

    @pytest.mark.skipif('six.PY3')
    def test_bad_string(self):
        x = six.b('The following character causes problems: \xd4')

        result = transform(x)
        assert result == six.binary_type(six.binary_type)

    def test_float(self):
        result = transform(13.0)
        self.assertEqual(type(result), float)
        self.assertEqual(result, 13.0)

    def test_bool(self):
        result = transform(True)
        self.assertEqual(type(result), bool)
        self.assertEqual(result, True)

    def test_int_subclass(self):
        class X(int):
            pass

        result = transform(X())
        self.assertEqual(type(result), int)
        self.assertEqual(result, 0)

    # def test_bad_string(self):
    #     x = 'The following character causes problems: \xd4'

    #     result = transform(x)
    #     self.assertEqual(result, '(Error decoding value)')

    def test_dict_keys(self):
        x = {'foo': 'bar'}

        result = transform(x)
        self.assertEqual(type(result), dict)
        keys = list(result.keys())
        self.assertEqual(len(keys), 1)
        self.assertTrue(type(keys[0]), str)
        self.assertEqual(keys[0], "'foo'")

    @pytest.mark.skipif('six.PY3')
    def test_dict_keys_utf8_as_str(self):
        x = {'רונית מגן': 'bar'}

        result = transform(x)
        self.assertEqual(type(result), dict)
        keys = list(result.keys())
        self.assertEqual(len(keys), 1)
        assert keys[0] == "'רונית מגן'"

    def test_dict_keys_utf8_as_unicode(self):
        x = {
            six.text_type('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'): 'bar'
        }

        result = transform(x)
        assert type(result) is dict
        keys = list(result.keys())
        assert len(keys) == 1
        if six.PY3:
            expected = "'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'"
        else:
            expected = "u'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'"
        assert keys[0] == expected

    def test_uuid(self):
        x = uuid.uuid4()
        result = transform(x)
        assert result == repr(x)

    def test_recursive(self):
        x = []
        x.append(x)

        result = transform(x)
        self.assertEqual(result, ('<...>',))

    def test_custom_repr(self):
        class Foo(object):
            def __sentry__(self):
                return six.u('example')

        x = Foo()

        result = transform(x)
        if six.PY3:
            expected = "'example'"
        else:
            expected = "u'example'"
        self.assertEqual(result, expected)

    def test_broken_repr(self):
        class Foo(object):
            def __repr__(self):
                raise ValueError

        x = Foo()

        result = transform(x)
        self.assertEqual(result, "<class 'tests.utils.encoding.tests.Foo'>")

    def test_recursion_max_depth(self):
        x = [[[[1]]]]
        result = transform(x, max_depth=3)
        if six.PY3:
            expected = ((("'[1]'",),),)
        else:
            expected = ((("u'[1]'",),),)
        self.assertEqual(result, expected)

    def test_list_max_length(self):
        x = list(range(10))
        result = transform(x, list_max_length=3)
        self.assertEqual(result, (0, 1, 2))

    def test_dict_max_length(self):
        x = dict((x, x) for x in range(10))
        result = transform(x, list_max_length=3)
        self.assertEqual(type(x), dict)
        self.assertEqual(len(result), 3)

    def test_string_max_length(self):
        x = six.u('1234')
        result = transform(x, string_max_length=3)
        expected = "'123'" if six.PY3 else "u'123'"
        self.assertEqual(result, expected)
