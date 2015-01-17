# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.lexnparse
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    All the unittests regarding lexing, parsing and syntax.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from jinja2.testsuite import JinjaTestCase

from jinja2 import Environment, Template, TemplateSyntaxError, \
     UndefinedError, nodes
from jinja2._compat import next, iteritems, text_type, PY2
from jinja2.lexer import Token, TokenStream, TOKEN_EOF, \
     TOKEN_BLOCK_BEGIN, TOKEN_BLOCK_END

env = Environment()


# how does a string look like in jinja syntax?
if PY2:
    def jinja_string_repr(string):
        return repr(string)[1:]
else:
    jinja_string_repr = repr


class TokenStreamTestCase(JinjaTestCase):
    test_tokens = [Token(1, TOKEN_BLOCK_BEGIN, ''),
                   Token(2, TOKEN_BLOCK_END, ''),
                  ]

    def test_simple(self):
        ts = TokenStream(self.test_tokens, "foo", "bar")
        assert ts.current.type is TOKEN_BLOCK_BEGIN
        assert bool(ts)
        assert not bool(ts.eos)
        next(ts)
        assert ts.current.type is TOKEN_BLOCK_END
        assert bool(ts)
        assert not bool(ts.eos)
        next(ts)
        assert ts.current.type is TOKEN_EOF
        assert not bool(ts)
        assert bool(ts.eos)

    def test_iter(self):
        token_types = [t.type for t in TokenStream(self.test_tokens, "foo", "bar")]
        assert token_types == ['block_begin', 'block_end', ]


class LexerTestCase(JinjaTestCase):

    def test_raw1(self):
        tmpl = env.from_string('{% raw %}foo{% endraw %}|'
                               '{%raw%}{{ bar }}|{% baz %}{%       endraw    %}')
        assert tmpl.render() == 'foo|{{ bar }}|{% baz %}'

    def test_raw2(self):
        tmpl = env.from_string('1  {%- raw -%}   2   {%- endraw -%}   3')
        assert tmpl.render() == '123'

    def test_balancing(self):
        env = Environment('{%', '%}', '${', '}')
        tmpl = env.from_string('''{% for item in seq
            %}${{'foo': item}|upper}{% endfor %}''')
        assert tmpl.render(seq=list(range(3))) == "{'FOO': 0}{'FOO': 1}{'FOO': 2}"

    def test_comments(self):
        env = Environment('<!--', '-->', '{', '}')
        tmpl = env.from_string('''\
<ul>
<!--- for item in seq -->
  <li>{item}</li>
<!--- endfor -->
</ul>''')
        assert tmpl.render(seq=list(range(3))) == ("<ul>\n  <li>0</li>\n  "
                                             "<li>1</li>\n  <li>2</li>\n</ul>")

    def test_string_escapes(self):
        for char in u'\0', u'\u2668', u'\xe4', u'\t', u'\r', u'\n':
            tmpl = env.from_string('{{ %s }}' % jinja_string_repr(char))
            assert tmpl.render() == char
        assert env.from_string('{{ "\N{HOT SPRINGS}" }}').render() == u'\u2668'

    def test_bytefallback(self):
        from pprint import pformat
        tmpl = env.from_string(u'''{{ 'foo'|pprint }}|{{ 'bär'|pprint }}''')
        assert tmpl.render() == pformat('foo') + '|' + pformat(u'bär')

    def test_operators(self):
        from jinja2.lexer import operators
        for test, expect in iteritems(operators):
            if test in '([{}])':
                continue
            stream = env.lexer.tokenize('{{ %s }}' % test)
            next(stream)
            assert stream.current.type == expect

    def test_normalizing(self):
        for seq in '\r', '\r\n', '\n':
            env = Environment(newline_sequence=seq)
            tmpl = env.from_string('1\n2\r\n3\n4\n')
            result = tmpl.render()
            assert result.replace(seq, 'X') == '1X2X3X4'

    def test_trailing_newline(self):
        for keep in [True, False]:
            env = Environment(keep_trailing_newline=keep)
            for template,expected in [
                    ('', {}),
                    ('no\nnewline', {}),
                    ('with\nnewline\n', {False: 'with\nnewline'}),
                    ('with\nseveral\n\n\n', {False: 'with\nseveral\n\n'}),
                    ]:
                tmpl = env.from_string(template)
                expect = expected.get(keep, template)
                result = tmpl.render()
                assert result == expect, (keep, template, result, expect)

class ParserTestCase(JinjaTestCase):

    def test_php_syntax(self):
        env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->')
        tmpl = env.from_string('''\
<!-- I'm a comment, I'm not interesting -->\
<? for item in seq -?>
    <?= item ?>
<?- endfor ?>''')
        assert tmpl.render(seq=list(range(5))) == '01234'

    def test_erb_syntax(self):
        env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>')
        tmpl = env.from_string('''\
<%# I'm a comment, I'm not interesting %>\
<% for item in seq -%>
    <%= item %>
<%- endfor %>''')
        assert tmpl.render(seq=list(range(5))) == '01234'

    def test_comment_syntax(self):
        env = Environment('<!--', '-->', '${', '}', '<!--#', '-->')
        tmpl = env.from_string('''\
<!--# I'm a comment, I'm not interesting -->\
<!-- for item in seq --->
    ${item}
<!--- endfor -->''')
        assert tmpl.render(seq=list(range(5))) == '01234'

    def test_balancing(self):
        tmpl = env.from_string('''{{{'foo':'bar'}.foo}}''')
        assert tmpl.render() == 'bar'

    def test_start_comment(self):
        tmpl = env.from_string('''{# foo comment
and bar comment #}
{% macro blub() %}foo{% endmacro %}
{{ blub() }}''')
        assert tmpl.render().strip() == 'foo'

    def test_line_syntax(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%')
        tmpl = env.from_string('''\
<%# regular comment %>
% for item in seq:
    ${item}
% endfor''')
        assert [int(x.strip()) for x in tmpl.render(seq=list(range(5))).split()] == \
               list(range(5))

        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##')
        tmpl = env.from_string('''\
<%# regular comment %>
% for item in seq:
    ${item} ## the rest of the stuff
% endfor''')
        assert [int(x.strip()) for x in tmpl.render(seq=list(range(5))).split()] == \
                list(range(5))

    def test_line_syntax_priority(self):
        # XXX: why is the whitespace there in front of the newline?
        env = Environment('{%', '%}', '${', '}', '/*', '*/', '##', '#')
        tmpl = env.from_string('''\
/* ignore me.
   I'm a multiline comment */
## for item in seq:
* ${item}          # this is just extra stuff
## endfor''')
        assert tmpl.render(seq=[1, 2]).strip() == '* 1\n* 2'
        env = Environment('{%', '%}', '${', '}', '/*', '*/', '#', '##')
        tmpl = env.from_string('''\
/* ignore me.
   I'm a multiline comment */
# for item in seq:
* ${item}          ## this is just extra stuff
    ## extra stuff i just want to ignore
# endfor''')
        assert tmpl.render(seq=[1, 2]).strip() == '* 1\n\n* 2'

    def test_error_messages(self):
        def assert_error(code, expected):
            try:
                Template(code)
            except TemplateSyntaxError as e:
                assert str(e) == expected, 'unexpected error message'
            else:
                assert False, 'that was supposed to be an error'

        assert_error('{% for item in seq %}...{% endif %}',
                     "Encountered unknown tag 'endif'. Jinja was looking "
                     "for the following tags: 'endfor' or 'else'. The "
                     "innermost block that needs to be closed is 'for'.")
        assert_error('{% if foo %}{% for item in seq %}...{% endfor %}{% endfor %}',
                     "Encountered unknown tag 'endfor'. Jinja was looking for "
                     "the following tags: 'elif' or 'else' or 'endif'. The "
                     "innermost block that needs to be closed is 'if'.")
        assert_error('{% if foo %}',
                     "Unexpected end of template. Jinja was looking for the "
                     "following tags: 'elif' or 'else' or 'endif'. The "
                     "innermost block that needs to be closed is 'if'.")
        assert_error('{% for item in seq %}',
                     "Unexpected end of template. Jinja was looking for the "
                     "following tags: 'endfor' or 'else'. The innermost block "
                     "that needs to be closed is 'for'.")
        assert_error('{% block foo-bar-baz %}',
                     "Block names in Jinja have to be valid Python identifiers "
                     "and may not contain hyphens, use an underscore instead.")
        assert_error('{% unknown_tag %}',
                     "Encountered unknown tag 'unknown_tag'.")


class SyntaxTestCase(JinjaTestCase):

    def test_call(self):
        env = Environment()
        env.globals['foo'] = lambda a, b, c, e, g: a + b + c + e + g
        tmpl = env.from_string("{{ foo('a', c='d', e='f', *['b'], **{'g': 'h'}) }}")
        assert tmpl.render() == 'abdfh'

    def test_slicing(self):
        tmpl = env.from_string('{{ [1, 2, 3][:] }}|{{ [1, 2, 3][::-1] }}')
        assert tmpl.render() == '[1, 2, 3]|[3, 2, 1]'

    def test_attr(self):
        tmpl = env.from_string("{{ foo.bar }}|{{ foo['bar'] }}")
        assert tmpl.render(foo={'bar': 42}) == '42|42'

    def test_subscript(self):
        tmpl = env.from_string("{{ foo[0] }}|{{ foo[-1] }}")
        assert tmpl.render(foo=[0, 1, 2]) == '0|2'

    def test_tuple(self):
        tmpl = env.from_string('{{ () }}|{{ (1,) }}|{{ (1, 2) }}')
        assert tmpl.render() == '()|(1,)|(1, 2)'

    def test_math(self):
        tmpl = env.from_string('{{ (1 + 1 * 2) - 3 / 2 }}|{{ 2**3 }}')
        assert tmpl.render() == '1.5|8'

    def test_div(self):
        tmpl = env.from_string('{{ 3 // 2 }}|{{ 3 / 2 }}|{{ 3 % 2 }}')
        assert tmpl.render() == '1|1.5|1'

    def test_unary(self):
        tmpl = env.from_string('{{ +3 }}|{{ -3 }}')
        assert tmpl.render() == '3|-3'

    def test_concat(self):
        tmpl = env.from_string("{{ [1, 2] ~ 'foo' }}")
        assert tmpl.render() == '[1, 2]foo'

    def test_compare(self):
        tmpl = env.from_string('{{ 1 > 0 }}|{{ 1 >= 1 }}|{{ 2 < 3 }}|'
                               '{{ 2 == 2 }}|{{ 1 <= 1 }}')
        assert tmpl.render() == 'True|True|True|True|True'

    def test_inop(self):
        tmpl = env.from_string('{{ 1 in [1, 2, 3] }}|{{ 1 not in [1, 2, 3] }}')
        assert tmpl.render() == 'True|False'

    def test_literals(self):
        tmpl = env.from_string('{{ [] }}|{{ {} }}|{{ () }}')
        assert tmpl.render().lower() == '[]|{}|()'

    def test_bool(self):
        tmpl = env.from_string('{{ true and false }}|{{ false '
                               'or true }}|{{ not false }}')
        assert tmpl.render() == 'False|True|True'

    def test_grouping(self):
        tmpl = env.from_string('{{ (true and false) or (false and true) and not false }}')
        assert tmpl.render() == 'False'

    def test_django_attr(self):
        tmpl = env.from_string('{{ [1, 2, 3].0 }}|{{ [[1]].0.0 }}')
        assert tmpl.render() == '1|1'

    def test_conditional_expression(self):
        tmpl = env.from_string('''{{ 0 if true else 1 }}''')
        assert tmpl.render() == '0'

    def test_short_conditional_expression(self):
        tmpl = env.from_string('<{{ 1 if false }}>')
        assert tmpl.render() == '<>'

        tmpl = env.from_string('<{{ (1 if false).bar }}>')
        self.assert_raises(UndefinedError, tmpl.render)

    def test_filter_priority(self):
        tmpl = env.from_string('{{ "foo"|upper + "bar"|upper }}')
        assert tmpl.render() == 'FOOBAR'

    def test_function_calls(self):
        tests = [
            (True, '*foo, bar'),
            (True, '*foo, *bar'),
            (True, '*foo, bar=42'),
            (True, '**foo, *bar'),
            (True, '**foo, bar'),
            (False, 'foo, bar'),
            (False, 'foo, bar=42'),
            (False, 'foo, bar=23, *args'),
            (False, 'a, b=c, *d, **e'),
            (False, '*foo, **bar')
        ]
        for should_fail, sig in tests:
            if should_fail:
                self.assert_raises(TemplateSyntaxError,
                    env.from_string, '{{ foo(%s) }}' % sig)
            else:
                env.from_string('foo(%s)' % sig)

    def test_tuple_expr(self):
        for tmpl in [
            '{{ () }}',
            '{{ (1, 2) }}',
            '{{ (1, 2,) }}',
            '{{ 1, }}',
            '{{ 1, 2 }}',
            '{% for foo, bar in seq %}...{% endfor %}',
            '{% for x in foo, bar %}...{% endfor %}',
            '{% for x in foo, %}...{% endfor %}'
        ]:
            assert env.from_string(tmpl)

    def test_trailing_comma(self):
        tmpl = env.from_string('{{ (1, 2,) }}|{{ [1, 2,] }}|{{ {1: 2,} }}')
        assert tmpl.render().lower() == '(1, 2)|[1, 2]|{1: 2}'

    def test_block_end_name(self):
        env.from_string('{% block foo %}...{% endblock foo %}')
        self.assert_raises(TemplateSyntaxError, env.from_string,
                           '{% block x %}{% endblock y %}')

    def test_constant_casing(self):
        for const in True, False, None:
            tmpl = env.from_string('{{ %s }}|{{ %s }}|{{ %s }}' % (
                str(const), str(const).lower(), str(const).upper()
            ))
            assert tmpl.render() == '%s|%s|' % (const, const)

    def test_test_chaining(self):
        self.assert_raises(TemplateSyntaxError, env.from_string,
                           '{{ foo is string is sequence }}')
        assert env.from_string('{{ 42 is string or 42 is number }}'
            ).render() == 'True'

    def test_string_concatenation(self):
        tmpl = env.from_string('{{ "foo" "bar" "baz" }}')
        assert tmpl.render() == 'foobarbaz'

    def test_notin(self):
        bar = range(100)
        tmpl = env.from_string('''{{ not 42 in bar }}''')
        assert tmpl.render(bar=bar) == text_type(not 42 in bar)

    def test_implicit_subscribed_tuple(self):
        class Foo(object):
            def __getitem__(self, x):
                return x
        t = env.from_string('{{ foo[1, 2] }}')
        assert t.render(foo=Foo()) == u'(1, 2)'

    def test_raw2(self):
        tmpl = env.from_string('{% raw %}{{ FOO }} and {% BAR %}{% endraw %}')
        assert tmpl.render() == '{{ FOO }} and {% BAR %}'

    def test_const(self):
        tmpl = env.from_string('{{ true }}|{{ false }}|{{ none }}|'
                               '{{ none is defined }}|{{ missing is defined }}')
        assert tmpl.render() == 'True|False|None|True|False'

    def test_neg_filter_priority(self):
        node = env.parse('{{ -1|foo }}')
        assert isinstance(node.body[0].nodes[0], nodes.Filter)
        assert isinstance(node.body[0].nodes[0].node, nodes.Neg)

    def test_const_assign(self):
        constass1 = '''{% set true = 42 %}'''
        constass2 = '''{% for none in seq %}{% endfor %}'''
        for tmpl in constass1, constass2:
            self.assert_raises(TemplateSyntaxError, env.from_string, tmpl)

    def test_localset(self):
        tmpl = env.from_string('''{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1 %}{% endfor %}\
{{ foo }}''')
        assert tmpl.render() == '0'

    def test_parse_unary(self):
        tmpl = env.from_string('{{ -foo["bar"] }}')
        assert tmpl.render(foo={'bar': 42}) == '-42'
        tmpl = env.from_string('{{ -foo["bar"]|abs }}')
        assert tmpl.render(foo={'bar': 42}) == '42'


class LstripBlocksTestCase(JinjaTestCase):

    def test_lstrip(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {% if True %}\n    {% endif %}''')
        assert tmpl.render() == "\n"

    def test_lstrip_trim(self):
        env = Environment(lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''    {% if True %}\n    {% endif %}''')
        assert tmpl.render() == ""

    def test_no_lstrip(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {%+ if True %}\n    {%+ endif %}''')
        assert tmpl.render() == "    \n    "

    def test_lstrip_endline(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    hello{% if True %}\n    goodbye{% endif %}''')
        assert tmpl.render() == "    hello\n    goodbye"

    def test_lstrip_inline(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {% if True %}hello    {% endif %}''')
        assert tmpl.render() == 'hello    '

    def test_lstrip_nested(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {% if True %}a {% if True %}b {% endif %}c {% endif %}''')
        assert tmpl.render() == 'a b c '

    def test_lstrip_left_chars(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    abc {% if True %}
        hello{% endif %}''')
        assert tmpl.render() == '    abc \n        hello'

    def test_lstrip_embeded_strings(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {% set x = " {% str %} " %}{{ x }}''')
        assert tmpl.render() == ' {% str %} '

    def test_lstrip_preserve_leading_newlines(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''\n\n\n{% set hello = 1 %}''')
        assert tmpl.render() == '\n\n\n'
        
    def test_lstrip_comment(self):
        env = Environment(lstrip_blocks=True, trim_blocks=False)
        tmpl = env.from_string('''    {# if True #}
hello
    {#endif#}''')
        assert tmpl.render() == '\nhello\n'

    def test_lstrip_angle_bracket_simple(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''    <% if True %>hello    <% endif %>''')
        assert tmpl.render() == 'hello    '

    def test_lstrip_angle_bracket_comment(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''    <%# if True %>hello    <%# endif %>''')
        assert tmpl.render() == 'hello    '

    def test_lstrip_angle_bracket(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
    <%# regular comment %>
    <% for item in seq %>
${item} ## the rest of the stuff
   <% endfor %>''')
        assert tmpl.render(seq=range(5)) == \
                ''.join('%s\n' % x for x in range(5))
        
    def test_lstrip_angle_bracket_compact(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
    <%#regular comment%>
    <%for item in seq%>
${item} ## the rest of the stuff
   <%endfor%>''')
        assert tmpl.render(seq=range(5)) == \
                ''.join('%s\n' % x for x in range(5))
        
    def test_php_syntax_with_manual(self):
        env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
    <!-- I'm a comment, I'm not interesting -->
    <? for item in seq -?>
        <?= item ?>
    <?- endfor ?>''')
        assert tmpl.render(seq=range(5)) == '01234'

    def test_php_syntax(self):
        env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
    <!-- I'm a comment, I'm not interesting -->
    <? for item in seq ?>
        <?= item ?>
    <? endfor ?>''')
        assert tmpl.render(seq=range(5)) == ''.join('        %s\n' % x for x in range(5))

    def test_php_syntax_compact(self):
        env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
    <!-- I'm a comment, I'm not interesting -->
    <?for item in seq?>
        <?=item?>
    <?endfor?>''')
        assert tmpl.render(seq=range(5)) == ''.join('        %s\n' % x for x in range(5))

    def test_erb_syntax(self):
        env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>',
            lstrip_blocks=True, trim_blocks=True)
        #env.from_string('')
        #for n,r in env.lexer.rules.iteritems():
        #    print n
        #print env.lexer.rules['root'][0][0].pattern
        #print "'%s'" % tmpl.render(seq=range(5))
        tmpl = env.from_string('''\
<%# I'm a comment, I'm not interesting %>
    <% for item in seq %>
    <%= item %>
    <% endfor %>
''')
        assert tmpl.render(seq=range(5)) == ''.join('    %s\n' % x for x in range(5))

    def test_erb_syntax_with_manual(self):
        env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
<%# I'm a comment, I'm not interesting %>
    <% for item in seq -%>
        <%= item %>
    <%- endfor %>''')
        assert tmpl.render(seq=range(5)) == '01234'

    def test_erb_syntax_no_lstrip(self):
        env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
<%# I'm a comment, I'm not interesting %>
    <%+ for item in seq -%>
        <%= item %>
    <%- endfor %>''')
        assert tmpl.render(seq=range(5)) == '    01234'

    def test_comment_syntax(self):
        env = Environment('<!--', '-->', '${', '}', '<!--#', '-->',
            lstrip_blocks=True, trim_blocks=True)
        tmpl = env.from_string('''\
<!--# I'm a comment, I'm not interesting -->\
<!-- for item in seq --->
    ${item}
<!--- endfor -->''')
        assert tmpl.render(seq=range(5)) == '01234'

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TokenStreamTestCase))
    suite.addTest(unittest.makeSuite(LexerTestCase))
    suite.addTest(unittest.makeSuite(ParserTestCase))
    suite.addTest(unittest.makeSuite(SyntaxTestCase))
    suite.addTest(unittest.makeSuite(LstripBlocksTestCase))
    return suite
