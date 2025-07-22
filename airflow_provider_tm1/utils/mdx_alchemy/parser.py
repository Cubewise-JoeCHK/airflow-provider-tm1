from airflow_provider_tm1.utils.mdx_alchemy import build_parser
import lark 

def parse(mdx: str):
    """
    Parses the given MDX string and returns a Lark Tree.

    :param mdx: The MDX string to parse.
    :return: A Lark Tree representing the parsed MDX.
    """
    assert isinstance(mdx, str), "MDX must be a string"

    parser = build_parser()
    try:
        return parser.parse(mdx)
    except lark.exceptions.UnexpectedToken as e:
        error_message = (
            "Unexpected token in MDX parsing, please check the syntax, or copy the following context to raise an issue at GitHub if mdx is valid.\n"
            f"Unexpected token '{e.token}' at line {e.line}, column {e.column}.\n"
            f"Input: {mdx}\n")
        raise Exception(f'{error_message}')
    except Exception as e:
        error_message = (
            "Unknown error occurred while parsing the MDX string, please check the syntax, or copy the following context to raise an issue at GitHub if mdx is valid.\n"
            f"Error: {str(e)}\n"
            f"Input: {mdx}\n")
        raise Exception(f'{error_message}') from e
