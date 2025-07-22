from lark import Lark
import lark
from importlib import resources

_PACKAGE_NAME: str = __package__ if __package__ else ""
GRAMMAR_LARK = 'mdx.grammar.lark'


def build_parser():
    assert isinstance(_PACKAGE_NAME, str), "Package name must be a string"
    assert isinstance(GRAMMAR_LARK, str), "Grammar file name must be a string"
    # Use the modern importlib.resources.files API
    grammar_path = resources.files(_PACKAGE_NAME) / GRAMMAR_LARK
    with grammar_path.open('r', encoding='utf-8') as f:
        grammar = f.read()
    return Lark(grammar,)
