from TM1py import TM1Service 
from mdxpy.mdx import MdxBuilder, ElementsHierarchySet, Member
import math.prod, math.ceil
from . import mdx_to_mdx_builder
import copy 


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

    __mdx_builder_stat = {}
    # row axis 
    for row_dim_set in mdx_builder.axes.get(1, []).dim_sets:
        element_names = tm1.elements.execute_set_mdx(mdx=row_dim_set.to_mdx())
        #todo: create better simple function to extract the dimension name and hierarchy name from set mdx
        __mdx_builder_stat.update({row_dim_set.dimension_name: len(element_names)})
        new_mdx_builder.add_hierarchy_set_to_row_axis(
            ElementsHierarchySet(
                *[Member(dimension=row_dim_set.dimension_name, hierarchy=row_dim_set.hierarchy_name, element=element_name) for element_name in element_names],
            )
        )
    
    # column axis 
    for col_dim_set in mdx_builder.axes.get(0, []).dim_sets:
        element_names = tm1.elements.execute_set_mdx(mdx=col_dim_set.to_mdx())
        #todo: create better simple function to extract the dimension name and hierarchy name from set mdx
        __mdx_builder_stat.update({col_dim_set.dimension_name: len(element_names)})
        new_mdx_builder.add_hierarchy_set_to_column_axis(
            ElementsHierarchySet(
                *[Member(dimension=col_dim_set.dimension_name, hierarchy=col_dim_set.hierarchy_name, element=element_name) for element_name in element_names],
            )
        )
    for title in mdx_builder._where.members:
        new_mdx_builder.add_member_to_where(title)
        
    if math.prod(__mdx_builder_stat.values()) <= chunk_size:
        return [new_mdx_builder]
    
    chunk_size = math.ceil(__mdx_builder_stat[max(__mdx_builder_stat, key=__mdx_builder_stat.get)] / (math.prod(__mdx_builder_stat.values()) / chunk_size))
    
    chunk_mdx_builder = MdxBuilder(mdx_builder.cube)
    for row_dim_set in new_mdx_builder.axes.get(1, []).dim_sets:
        if row_dim_set.dimension_name == max(__mdx_builder_stat, key=__mdx_builder_stat.get):
            continue 
        chunk_mdx_builder.add_hierarchy_set_to_row_axis(row_dim_set)
    
    for col_dim_set in new_mdx_builder.axes.get(0, []).dim_sets:
        if col_dim_set.dimension_name == max(__mdx_builder_stat, key=__mdx_builder_stat.get):
            continue 
        chunk_mdx_builder.add_hierarchy_set_to_column_axis(col_dim_set)
    
    for title in new_mdx_builder._where.members:
        chunk_mdx_builder.add_member_to_where(title)
    
    chunks = []
    for row_dim_set in new_mdx_builder.axes.get(1, []).dim_sets:
        if row_dim_set.dimension_name != max(__mdx_builder_stat, key=__mdx_builder_stat.get):
            continue 
        for i in range(0, __mdx_builder_stat[row_dim_set.dimension_name], chunk_size):
            tmp_chunk_mdx_builder = copy.deepcopy(chunk_mdx_builder)
            tmp_chunk_mdx_builder.add_hierarchy_set_to_row_axis(
                ElementsHierarchySet(*row_dim_set.members[i:i + chunk_size])
            )
            chunks.append(tmp_chunk_mdx_builder)
            
    for col_dim_set in new_mdx_builder.axes.get(0, []).dim_sets:
        if col_dim_set.dimension_name != max(__mdx_builder_stat, key=__mdx_builder_stat.get):
            continue 
        for i in range(0, __mdx_builder_stat[col_dim_set.dimension_name], chunk_size):
            tmp_chunk_mdx_builder = copy.deepcopy(chunk_mdx_builder)
            tmp_chunk_mdx_builder.add_hierarchy_set_to_column_axis(
                ElementsHierarchySet(*col_dim_set.members[i:i + chunk_size])
            )
            chunks.append(tmp_chunk_mdx_builder)

    return chunks
