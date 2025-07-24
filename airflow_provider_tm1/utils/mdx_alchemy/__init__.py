from lark import Lark
import lark
from importlib import resources
from .transformer import MDXTransformer
from mdxpy.mdx import MdxBuilder

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

def mdx_to_mdx_builder(mdx: str) -> MdxBuilder:
    """
    Converts an MDX query string into an MdxBuilder object.

    :param mdx: The MDX query string to be converted.
    :return: An MdxBuilder object representing the MDX query.
    """
    parser = build_parser()
    mdx_tree = parser.parse(mdx)
    return MDXTransformer().transform(mdx_tree).children[0]
