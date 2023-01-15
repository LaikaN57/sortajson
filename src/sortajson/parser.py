from collections import OrderedDict
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
lexer_logger = logging.getLogger("lexer")
parser_logger = logging.getLogger("parser")

import pprint

import ply.lex as lex
import ply.yacc as yacc


test_doc = """{
    TestA=TestB TestC,
    TestD{
        TestE=TestF
    },
    TestG[0]{
        TestH="TestI-TestJ",
        TestK=TestL:TestM
    }
}"""

tokens = (
    "DIGITS",
    "ARRAYIDX",
    "KORV",  # Key or Value
    "LBRACE",  # {
    "RBRACE",  # }
    "LBRACKET",  # [
    "RBRACKET",  # ]
    "COMMA",  # ,
    "EQUALS",  # =
)

t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_COMMA = r","
t_EQUALS = r"="


def t_DIGITS(t) -> int:
    r"\d+"
    t.value = int(t.value)
    return t


def t_ARRAYIDX(t) -> int:
    r"\[\d+\]"
    t.value = int(t.value[1:-1])
    return t


def t_KORV(t) -> str:
    r'[a-zA-Z0-9.: "-]+'  # todo
    t.value = str(t.value)
    return t


# just some fancy tracking of line numbers
def t_newline(t) -> None:
    r"\n+"
    t.lexer.lineno += len(t.value)


# skip any characters that we do not recognize
def t_error(t) -> None:
    lexer_logger.warning("Illegal character '%s'.", t.value[0])
    # t.lexer.skip(1)


lexer = lex.lex()


def p_generation(p):
    """
    generation : LBRACE siblings RBRACE
    """
    p[0] = p[2]


def p_siblings(p):
    """
    siblings : sibling
             | sibling COMMA siblings
    """
    if len(p) == 2:  # [siblings, sibling]
        p[0] = p[1]
    else:  # [siblings, sibling, COMMA, siblings]
        ret = {}
        ret.update(p[1])
        ret.update(p[3])
        p[0] = ret


def p_sibling(p):
    """
    sibling : kv
            | child
            | grandchildren
    """
    p[0] = p[1]


def p_child(p):
    """
    child : KORV generation
    """

    p[0] = {p[1]: p[2]}


def p_grandchildren(p):
    """
    grandchildren : KORV ARRAYIDX generation
    """
    p[0] = {p[1]: {p[2]: p[3]}}


def p_kv(p):
    """
    kv : KORV EQUALS KORV
    """
    p[0] = {p[1]: p[3]}


def p_error(p):
    parser_logger.warning("Syntax error at %s.", repr(p.value))
    parser_logger.warning("at %s.", lexer.lineno)


# Build the parser
parser = yacc.yacc()


def realmain():
    ast = parser.parse(test_doc)
    # logger.debug(pprint.pprint(ast))

    json_str = json.dumps(ast, indent=4)

    print(json.dumps(ast, indent=4))


if __name__ == "__main__":
    realmain()
