from TM1py import TM1Service 
from mdxpy.mdx import MdxBuilder, ElementsHierarchySet, Member, MdxAxis
from math import prod, ceil
from . import mdx_to_mdx_builder
import copy 
from TM1py.Objects import AnonymousSubset, ViewTitleSelection

def build_mdx_statement(
    title_set: dict[str, AnonymousSubset],
    row_set: dict[str, AnonymousSubset],
    col_set: dict[str, AnonymousSubset],
    cube_name: str,
) -> str:
    """
    Builds an MDX statement from the provided title, row, and column sets.

    :param title_set: A dictionary of titles with dimension names as keys and AnonymousSubset as values.
    :param row_set: A dictionary of row sets with dimension names as keys and AnonymousSubset as values.
    :param col_set: A dictionary of column sets with dimension names as keys and AnonymousSubset as values.
    :param cube_name: The name of the cube to query.
    
    :return: An MdxBuilder object representing the MDX statement.
    """
    mdx_builder = MdxBuilder(cube_name)
    
    for title in title_set.values():
        mdx_builder.add_member_to_where(Member(title.dimension_name, title.hierarchy_name, title.elements[0])) 

    for row_subset in row_set.values():
        mdx_builder.add_hierarchy_set_to_row_axis(
            ElementsHierarchySet(*[Member(row_subset.dimension_name, row_subset.hierarchy_name, e) for e in row_subset.elements])
        )
        
    for col_subset in col_set.values():
        mdx_builder.add_hierarchy_set_to_column_axis(
            ElementsHierarchySet(*[Member(col_subset.dimension_name, col_subset.hierarchy_name, e) for e in col_subset.elements])
        )

    return mdx_builder.to_mdx()

def chunk_query(tm1: TM1Service, mdx: str|MdxBuilder, chunk_size: int = 1000) -> list[str]:
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

    __mdx_builder_stat = {}
    # row axis 
    row_set = {}
    for row_dim_set in mdx_builder.axes.get(1, MdxAxis.empty()).dim_sets:
        # Using to_mdx() for consistency with the column axis implementation.
        elements = tm1.elements.execute_set_mdx_element_names(row_dim_set.to_mdx())
        subset = AnonymousSubset(
            row_dim_set.dimension, 
            row_dim_set.hierarchy,
            elements=elements
        )
        __mdx_builder_stat.update({row_dim_set.dimension: len(elements)})
        row_set.update({row_dim_set.dimension: subset})

    # column axis 
    col_set = {}
    for col_dim_set in mdx_builder.axes.get(0, MdxAxis.empty()).dim_sets:
        element_names = tm1.elements.execute_set_mdx_element_names(col_dim_set.to_mdx())
        subset = AnonymousSubset(
            col_dim_set.dimension, 
            col_dim_set.hierarchy,
            elements=element_names
        )
        __mdx_builder_stat.update({col_dim_set.dimension: len(element_names)})

        col_set.update({col_dim_set.dimension: subset})

    title_set = {}
    for title in mdx_builder._where.members:
        subset = AnonymousSubset(
            title.dimension, 
            title.hierarchy, 
            elements=[title.element]
        )
        title_set.update({title.dimension: subset})
        
    if prod(__mdx_builder_stat.values()) <= chunk_size:
        return [build_mdx_statement(title_set, row_set, col_set, mdx_builder.cube)]
    
    largest_dim = max(__mdx_builder_stat, key=__mdx_builder_stat.get) #type: ignore
    
    batch = ceil(__mdx_builder_stat[largest_dim] / (prod(__mdx_builder_stat.values()) / chunk_size))
    
    unchanged_row_set = {}
    unchanged_col_set = {}
    chunk_row_set = []
    chunk_col_set = []
    for dim_name, subset in row_set.items():
        if dim_name != largest_dim:
            unchanged_row_set.update({dim_name: subset})
            continue 

        for i in range(0, len(subset.elements), batch):
            chunk_row_set.append(AnonymousSubset(
                dim_name,
                subset.hierarchy_name,
                elements=subset.elements[i:i + batch]
            ))
        
    for dim_name, subset in col_set.items():
        if dim_name != largest_dim:
            unchanged_col_set.update({dim_name: subset})
            continue
        
        for i in range(0, len(subset.elements), chunk_size):
            chunk_col_set.append(AnonymousSubset(
                dim_name,
                subset.hierarchy_name,
                elements=subset.elements[i:i + chunk_size]
            ))

    chunks = []
    for chunk in chunk_row_set:
        chunks.append(
            build_mdx_statement(
                title_set=title_set,
                row_set={**unchanged_row_set, chunk.dimension_name: chunk},
                col_set=unchanged_col_set,
                cube_name=mdx_builder.cube
            )
        )
    for chunk in chunk_col_set:
        chunks.append(
            build_mdx_statement(
                title_set=title_set,
                row_set=unchanged_row_set,
                col_set={**unchanged_col_set, chunk.dimension_name: chunk},
                cube_name=mdx_builder.cube
            )
        )

    return chunks
