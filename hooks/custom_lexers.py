"""
MkDocs hook: register custom Pygments lexers for Ingres ESQL and OpenROAD 4GL.

Usage in markdown:
    ```ingres-sql
    exec sql begin declare section;
    ...
    exec sql end declare section;
    ```

    ```openroad-4gl
    on event clicked =
    begin
        ...
    end;
    ```
"""

import pygments.lexers
from pygments.lexer import RegexLexer, words, bygroups, include
from pygments.token import (
    Text, Comment, Operator, Keyword, Name, String,
    Number, Punctuation, Whitespace
)


# ---------------------------------------------------------------------------
# Ingres Embedded SQL Lexer
# Handles Pascal host language with embedded exec sql directives
# ---------------------------------------------------------------------------
class IngresEsqlLexer(RegexLexer):
    name = 'Ingres ESQL'
    aliases = ['ingres-sql', 'ingres_sql', 'esql', 'ingres']
    filenames = ['*.esql', '*.equel', '*.qc']

    _EXEC_SQL_KW = (
        'select', 'insert', 'update', 'delete', 'from', 'where', 'into',
        'values', 'set', 'join', 'inner', 'outer', 'left', 'right',
        'order', 'group', 'by', 'having', 'union', 'all', 'distinct',
        'create', 'drop', 'alter', 'table', 'view', 'index',
        'grant', 'revoke', 'commit', 'rollback', 'connect', 'disconnect',
        'declare', 'cursor', 'fetch', 'open', 'close', 'execute',
        'immediate', 'prepare', 'describe', 'whenever', 'not', 'found',
        'sqlerror', 'continue', 'transaction', 'null', 'as', 'with',
    )

    _PASCAL_KW = (
        'program', 'procedure', 'function', 'uses', 'unit', 'interface',
        'implementation', 'begin', 'end', 'if', 'then', 'else', 'for', 'to',
        'downto', 'while', 'do', 'repeat', 'until', 'case', 'of', 'with',
        'record', 'file', 'goto', 'label', 'const', 'type', 'var',
        'forward', 'in', 'and', 'or', 'not', 'div', 'mod', 'packed',
        'array', 'string', 'varying',
    )

    _TYPES = (
        'integer', 'longint', 'shortint', 'byte', 'word', 'cardinal',
        'int64', 'qword', 'real', 'single', 'double', 'extended', 'comp',
        'boolean', 'char', 'character',
        # Ingres-specific types
        'i1', 'i2', 'i4', 'i8', 'f4', 'f8', 'float4', 'float8',
        'varchar', 'nvarchar', 'c', 'text', 'long', 'varbyte', 'longbyte',
        'decimal', 'date', 'money', 'smallint', 'bigint', 'ansidate',
        'time', 'timestamp', 'interval', 'alpha',
    )

    tokens = {
        'root': [
            # exec sql ... section directives (highest priority)
            (
                r'(?i)(exec)(\s+)(sql)(\s+)(begin|end)(\s+)(declare)(\s+)(section)',
                bygroups(
                    Keyword.Reserved, Whitespace, Keyword.Reserved,
                    Whitespace, Keyword.Reserved, Whitespace,
                    Keyword.Reserved, Whitespace, Keyword.Reserved,
                ),
            ),
            # exec sql <anything else>
            (r'(?i)(exec)(\s+)(sql)\b',
             bygroups(Keyword.Reserved, Whitespace, Keyword.Reserved)),

            # Pascal/Delphi-style curly comments  { comment }
            (r'\{[^}]*\}', Comment),
            # (* ... *) comments
            (r'\(\*.*?\*\)', Comment.Multiline),
            # -- line comments
            (r'--[^\n]*\n?', Comment.Single),
            # /* */ block comments
            (r'/\*', Comment.Multiline, 'block_comment'),

            # Strings
            (r"'(?:[^']|'')*'", String.Single),
            (r'"(?:[^"]|"")*"', String.Double),

            # Numbers
            (r'\b\d+\.\d*([Ee][+-]?\d+)?\b', Number.Float),
            (r'\b\d+\b', Number.Integer),

            # Types (check before general keywords)
            (words(_TYPES, suffix=r'\b', prefix=r'(?i)\b'), Keyword.Type),

            # Pascal keywords
            (words(_PASCAL_KW, suffix=r'\b', prefix=r'(?i)\b'), Keyword),

            # SQL keywords (after exec sql, inside ESQL blocks)
            (words(_EXEC_SQL_KW, suffix=r'\b', prefix=r'(?i)\b'), Keyword),

            # Range operator  1..6
            (r'\.\.', Operator),

            # Operators and comparison
            (r':=', Operator),
            (r'[<>=!+\-*/^@]', Operator),
            (r':', Punctuation),

            # Punctuation
            (r'[;,.()\[\]]', Punctuation),

            # Identifiers
            (r'\b[A-Za-z_][A-Za-z0-9_]*\b', Name),

            # Whitespace
            (r'\s+', Whitespace),

            # Anything else
            (r'.', Text),
        ],
        'block_comment': [
            (r'[^*]+', Comment.Multiline),
            (r'\*/', Comment.Multiline, '#pop'),
            (r'\*', Comment.Multiline),
        ],
    }


# ---------------------------------------------------------------------------
# OpenROAD 4GL Lexer
# ---------------------------------------------------------------------------
class OpenRoad4GLLexer(RegexLexer):
    name = 'OpenROAD 4GL'
    aliases = ['openroad-4gl', 'openroad', '4gl', 'or4gl']
    filenames = ['*.4gl', '*.or4', '*.w4gl']

    _KEYWORDS = (
        # Event/frame structure
        'on', 'event', 'initialize', 'finalize', 'activate', 'field',
        'menuitem', 'key', 'column', 'entry', 'exit', 'timeout',
        'declare', 'enddeclare', 'begin', 'end',
        # Control flow
        'if', 'then', 'else', 'elseif', 'endif',
        'while', 'endwhile', 'for', 'endfor', 'foreach', 'endforeach',
        'return', 'next', 'resume', 'sleep', 'exit',
        # Call/frame
        'call', 'callproc', 'callframe', 'calls', 'openframe', 'gotoframe',
        # DML
        'select', 'insert', 'update', 'delete', 'from', 'where',
        'into', 'values', 'set', 'order', 'by', 'group', 'having',
        'join', 'inner', 'outer', 'left', 'right', 'union', 'all',
        'distinct', 'as', 'commit', 'rollback', 'connect', 'disconnect',
        # Forms
        'getform', 'putform', 'getrow', 'putrow', 'deleterow', 'insertrow',
        'unloadtable', 'loadtable', 'clear', 'scroll', 'forminit',
        'inittable', 'formdata',
        # Query / misc
        'inquire_sql', 'inquire_forms', 'inquire_4gl',
        'message', 'prompt', 'byref',
        # Logical / SQL operators
        'not', 'and', 'or', 'is', 'null', 'like', 'in', 'any',
        'with', 'default', 'nodefault', 'mandatory', 'nomandatory',
        # Scope
        'global', 'local', 'procedure', 'frame', 'database', 'constant',
    )

    _TYPES = (
        'integer', 'smallint', 'bigint', 'float', 'float4', 'float8',
        'i1', 'i2', 'i4', 'i8', 'f4', 'f8',
        'varchar', 'nvarchar', 'char', 'c', 'text', 'long varchar',
        'date', 'ansidate', 'time', 'timestamp', 'interval', 'money',
        'decimal', 'byte', 'varbyte', 'boolean',
        'stringobject', 'object_source',
    )

    _BUILTINS = (
        'ifnull', 'isnull', 'coalesce', 'case', 'when', 'then', 'end',
        'upper', 'lower', 'trim', 'ltrim', 'rtrim', 'length', 'pad',
        'left', 'right', 'locate', 'substr', 'substring', 'concat',
        'abs', 'mod', 'int1', 'int2', 'int4', 'int8', 'float4', 'float8',
        'date', 'time', 'interval', 'now', 'today', 'iidate', 'iitime',
        'hex', 'unhex', 'soundex', 'charextract',
    )

    tokens = {
        'root': [
            # /* */ block comments
            (r'/\*', Comment.Multiline, 'block_comment'),
            # -- and // line comments
            (r'--[^\n]*\n?', Comment.Single),
            (r'//[^\n]*\n?', Comment.Single),
            # { } used as comments in some 4GL dialects
            (r'\{[^}]*\}', Comment),

            # Strings
            (r"'(?:[^']|'')*'", String.Single),
            (r'"(?:[^"]|"")*"', String.Double),

            # Numbers
            (r'\b\d+\.\d*([Ee][+-]?\d+)?\b', Number.Float),
            (r'\b\d+\b', Number.Integer),

            # Types
            (words(_TYPES, suffix=r'\b', prefix=r'(?i)\b'), Keyword.Type),

            # Built-in functions
            (words(_BUILTINS, suffix=r'\b', prefix=r'(?i)\b'), Name.Builtin),

            # Keywords
            (words(_KEYWORDS, suffix=r'\b', prefix=r'(?i)\b'), Keyword),

            # :: global variable prefix  ::globalvar
            (r'::[A-Za-z_][A-Za-z0-9_]*', Name.Variable.Global),
            # : host variable  :hostvar
            (r':[A-Za-z_][A-Za-z0-9_]*', Name.Variable),

            # Attribute access  object.attribute
            (r'([A-Za-z_][A-Za-z0-9_]*)(\s*\.\s*)([A-Za-z_][A-Za-z0-9_]*)',
             bygroups(Name, Punctuation, Name.Attribute)),

            # Operators
            (r':=', Operator),
            (r'[<>=!+\-*/^@]', Operator),

            # Punctuation
            (r'[;,.()\[\]]', Punctuation),

            # Identifiers
            (r'\b[A-Za-z_][A-Za-z0-9_]*\b', Name),

            # Whitespace
            (r'\s+', Whitespace),

            (r'.', Text),
        ],
        'block_comment': [
            (r'[^*]+', Comment.Multiline),
            (r'\*/', Comment.Multiline, '#pop'),
            (r'\*', Comment.Multiline),
        ],
    }


# ---------------------------------------------------------------------------
# Registration: patch Pygments AND pymdownx at MkDocs config time
# ---------------------------------------------------------------------------
_CUSTOM_LEXERS = {
    alias: lexer_class
    for lexer_class in (IngresEsqlLexer, OpenRoad4GLLexer)
    for alias in lexer_class.aliases
}

_original_get_lexer_by_name = pygments.lexers.get_lexer_by_name


def _patched_get_lexer_by_name(alias, **options):
    lexer_class = _CUSTOM_LEXERS.get(alias.lower())
    if lexer_class:
        return lexer_class(**options)
    return _original_get_lexer_by_name(alias, **options)


def on_config(config):
    """Register custom lexers with Pygments AND pymdownx before the build starts."""
    # 1. Patch pygments module attribute (for direct callers)
    pygments.lexers.get_lexer_by_name = _patched_get_lexer_by_name

    # 2. Patch pymdownx.highlight's locally-imported reference
    #    (it does: from pygments.lexers import get_lexer_by_name  inside a try block)
    try:
        import pymdownx.highlight as md_hl
        if hasattr(md_hl, 'get_lexer_by_name'):
            md_hl.get_lexer_by_name = _patched_get_lexer_by_name
    except ImportError:
        pass

    # 3. Patch pymdownx.superfences if it also caches the function
    try:
        import pymdownx.superfences as md_sf
        if hasattr(md_sf, 'get_lexer_by_name'):
            md_sf.get_lexer_by_name = _patched_get_lexer_by_name
    except ImportError:
        pass

    return config
