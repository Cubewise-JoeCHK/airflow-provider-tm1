from TM1py import TM1Service 
from mdxpy.mdx import MdxBuilder 
from . import mdx_to_mdx_builder

def chunk_query(tm1: TM1Service, mdx: str|MdxBuilder, chunk_size: int = 1000) -> list[MdxBuilder]:
    """
    #! This function is experimental and not fully implemented yet.
    #! It is intended to split the MDX query into smaller chunks based on the specified chunk size.
    #! Please make sure the MDX query is simple enough to be handled by this function.
    #! If the MDX query is complex, it may not work as expected or may raise an error.

    Splits the MDX query into smaller chunks based on the specified chunk size.

    :param tm1: The TM1Service instance to use for executing the MDX queries.
    :param mdx: The Mdx Statement or MdxBuilder object representing the MDX query.
    :param chunk_size: The maximum number of rows to include in each chunk.
    
    :return: A list of MdxBuilder objects, each representing a chunk of the original MDX query.
    """
    if isinstance(mdx, str):
        mdx_builder = mdx_to_mdx_builder(mdx)
    else: 
        assert isinstance(mdx, MdxBuilder), "mdx must be a string or an MdxBuilder object"
        mdx_builder = mdx
        
    new_mdx_builder = MdxBuilder(mdx_builder.cube)

    # row axis 
    for row_dim_set in mdx_builder.axes.get(1, []).dim_sets:
        ...
    
    # column axis 
    for col_dim_set in mdx_builder.axes.get(0, []).dim_sets:
        ...
    
    return [new_mdx_builder]  # Placeholder for the actual implementation
