from mdxpy.mdx import (
    MdxBuilder,
    MdxAxis,
    MdxTuple,
    MdxHierarchySet,
    TuplesSet,
    Member,
    CurrentMember,
    Tm1SubsetToSetHierarchySet,
    Tm1DrillDownMemberSet,
    AllMembersHierarchySet,
    Tm1SubsetAllHierarchySet,
    Tm1FilterByPattern,
    ChildrenHierarchySet,
    Tm1FilterByLevelHierarchySet,
    ExceptHierarchySet,
    RangeHierarchySet,
    UnionHierarchySet,
    DefaultMemberHierarchySet,
    OrderByCellValueHierarchySet,
    DescendantsHierarchySet,
    ElementsHierarchySet,
    MdxPropertiesTuple,
)
from .mdxpy_plugin import (
    DrillUpMemberSet
)

import lark

parse_tuple_to_data = lambda x: {i[0]: i[1] for i in x if isinstance(i, tuple)}


class MDXTransformer(lark.Transformer):
    """
    This transformer is used to transform the parsed MDX query into an MdxBuilder object.
    
    #! This transformer is expecting to transform the simple MDX query, if the query is complex, it will not work as expected, or may error out. 
    #! It is not a complete implementation of the MDX query language, but it is enough to handle the simple queries.
    """

    def string(self, item):
        return item[1].value

    def child(self, item):
        return item[0]

    def consolidation(self, item):
        return None

    def name(self, item):
        return [i for i in item if isinstance(i, lark.Token) and i.type == 'IDENTIFIER'][0]

    def dimension(self, item):
        return ('dimension', item[0].value)

    def hierarchy(self, item):
        return ('hierarchy', item[0].value)

    def element(self, item):
        return ('element', item[0].value)

    def member(self, item):
        data = {i[0]: i[1] for i in item if isinstance(i, tuple)}
        if data.get('element'):
            return Member(dimension=data['dimension'], hierarchy=data.get('hierarchy', data['dimension']),
                          element=data['element'])
        return CurrentMember.build_unique_name(dimension=data['dimension'],
                                               hierarchy=data.get('hierarchy', data['dimension']))

    def mdx_tuple(self, item):
        return MdxTuple(members=[i for i in item if isinstance(i, Member)])

    def mdx_axis_row(self, item):
        mdx_axis = MdxAxis.empty()
        property_tuple = None
        for node in item:
            if isinstance(node, lark.Tree):
                if node.data == 'non_empty':
                    mdx_axis.non_empty = True
                    continue
                for i in node.children:
                    if isinstance(i, lark.Token):
                        continue
                    if isinstance(i, MdxTuple):
                        mdx_axis.add_set(TuplesSet([i]))
                    if isinstance(i, MdxHierarchySet):
                        mdx_axis.add_set(i)
            if isinstance(node, MdxTuple):
                mdx_axis.add_set(TuplesSet([node]))
            if isinstance(node, MdxHierarchySet):
                mdx_axis.add_set(node)
            if isinstance(node, MdxPropertiesTuple):
                property_tuple = node
        if property_tuple:
            return {'row': mdx_axis, 'row_properties': property_tuple}
        return {'row': mdx_axis}

    def where(self, item):
        return {'where': [i for i in item if isinstance(i, MdxTuple)][0]}

    def cube_source(self, item):
        return {'cube': item[0]}

    def mdx_axis_column(self, item):
        mdx_axis = MdxAxis.empty()
        property_tuple = None
        for node in item:
            if isinstance(node, lark.Tree):
                if node.data == 'non_empty':
                    mdx_axis.non_empty = True
                    continue
                for i in node.children:
                    if isinstance(i, lark.Token):
                        continue
                    if isinstance(i, MdxTuple):
                        mdx_axis.add_set(TuplesSet([i]))
                    if isinstance(i, MdxHierarchySet):
                        mdx_axis.add_set(i)
            if isinstance(node, MdxTuple):
                mdx_axis.add_tuple(node)
            if isinstance(node, MdxHierarchySet):
                mdx_axis.add_set(node)
            if isinstance(node, MdxPropertiesTuple):
                property_tuple = node
        if property_tuple:
            return {'column': mdx_axis, 'column_properties': property_tuple}
        return {'column': mdx_axis}
    
    def dimension_properties(self, item):
        return MdxPropertiesTuple(members=[i for i in item if isinstance(i, Member)])

    def mdx_builder(self, item):
        data = {}
        for i in item:
            if isinstance(i, dict):
                data.update(i)
        builder = MdxBuilder(cube=data['cube'],)
        axes = {}
        if row_data := data.get('row'):
            axes.update({1: row_data})
        if column_data := data.get('column'):
            axes.update({0: column_data})
        if row_properties := data.get('row_properties'):
            builder.axes_properties[0] = row_properties
        if column_properties := data.get('column_properties'):
            builder.axes_properties[1] = column_properties
        builder.axes = axes
        builder._where = where if (where := data.get('where')) else MdxTuple.empty()
        return builder

    def mdx_hierarchy_set(self, item):
        for i in item:
            if isinstance(i, lark.Tree):
                # Log the presence of a lark.Tree instance for debugging purposes
                print(f"Debug: Found lark.Tree instance in mdx_hierarchy_set with data: {i.data}")
        return [i for i in item if not isinstance(i, lark.Token)][0]

    def tm1_subset_to_set(self, item):
        data = parse_tuple_to_data(item)
        return Tm1SubsetToSetHierarchySet(
            dimension=data['dimension'], hierarchy=data.get('hierarchy', data['dimension']),
            subset=[i for i in item if isinstance(i, str) and not isinstance(i, lark.Token)][0])

    def drill_down_member(self, item):
        data = [i for i in item if not isinstance(i, lark.Token)]
        return Tm1DrillDownMemberSet(
            underlying_hierarchy_set=data[0],
            other_set=data[1],
        )

    def all_members_hierarchy_set(self, item):
        data = parse_tuple_to_data(item)
        dimension = data['dimension']
        hierarchy = data.get('hierarchy', dimension)
        return AllMembersHierarchySet(dimension=dimension, hierarchy=hierarchy)

    def tm1_subset_all_hierarchy_set(self, item):
        data = parse_tuple_to_data(item)
        dimension = data['dimension']
        hierarchy = data.get('hierarchy', dimension)
        return Tm1SubsetAllHierarchySet(dimension=dimension, hierarchy=hierarchy)

    def tm1_filter_by_pattern(self, item):
        assert isinstance(item[1],
                          MdxHierarchySet), 'the solution assumed the first element of the list is MdxHierarchySet'
        assert isinstance([i for i in item if isinstance(i, str)][0],
                          str), 'the solution assumed there is at least one string in the list'
        return Tm1FilterByPattern(item[1], wildcard=[i for i in item if isinstance(i, str)][0])

    def drill_up_member(self, item):
        data = [i for i in item if not isinstance(i, lark.Token)]
        return DrillUpMemberSet(
            underlying_hierarchy_set=data[0],
            other_set=data[1],
        )

    def children_hierarchy_set(self, item):
        assert isinstance(item[0], Member), 'the solution assumed the first elemetn of the list is Member'
        return ChildrenHierarchySet(item[0])

    def tm1_filter_by_level(self, item):
        assert isinstance(item[1],
                          MdxHierarchySet), 'the solution assumed the first element of the list is MDXHierarchySet'
        assert (numeric_list :=
                [i.value for i in [i for i in item if isinstance(i, lark.Token)] if i.type == 'NUMERIC'
                ]), 'the solution assumed there is at least one numeric token'
        return Tm1FilterByLevelHierarchySet(underlying_hierarchy_set=item[1], level=int(numeric_list[0]))

    def except_hierarchy_set(self, item):
        assert isinstance(
            item[1], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the second element of the list is MDXHierarchySst or TupleSet'
        assert isinstance(
            item[3], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the forth element of the list is MDX HierarchySet or TupleSet'
        return ExceptHierarchySet(item[1], item[3])

    def range_hierarchy_set(self, item):
        assert isinstance(item[1], (Member)), 'the solution assumed the second element of the list is Member'
        assert isinstance(item[3], (Member)), 'the solution assumed the fourth element of the list is Member'
        return RangeHierarchySet(item[1], item[3])

    def union_hierarchy_set(self, item):
        assert isinstance(
            item[1], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the second element of the list is MDXHierarchySet or TuplesSet'
        assert isinstance(
            item[3], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the forth element of the list is MDX HierarchySet or TuplesSet'
        return UnionHierarchySet(item[1], item[3], allow_duplicates=False)

    def tm1_drill_down_member(self, item):

        assert isinstance(
            item[1],
            (MdxHierarchySet, TuplesSet)), 'the solution assumed the second element of the list is MdxHierarchySet'
        assert item[3] == 'ALL' or isinstance(
            item[3], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the forth element of the list is MdxHierarchySet or "ALL"'
        other_set = None if item[3] == 'ALL' else item[3]
        recursive = [i for i in item if isinstance(i, lark.Token) and i.type == 'RECURSIVE']
        return Tm1DrillDownMemberSet(underlying_hierarchy_set=item[1], other_set=other_set, recursive=bool(recursive))

    def default_member_hierarchy_set(self, item):
        assert isinstance(item[0], Member), 'the solution assumed the first element of the list is Member'
        return DefaultMemberHierarchySet(item[0].dimension, item[0].hierarchy)

    def order_by_cell_value_hierarchy_set(self, item):
        data = parse_tuple_to_data(item)
        assert isinstance(
            item[1], (MdxHierarchySet,
                      TuplesSet)), 'the solution assumed the second element of the list is MdxHierarchySet or TuplesSet'
        assert isinstance(item[5], (MdxTuple)), 'the solution assumed the fifth element of the list is MdxTuple'
        assert isinstance(data.get('cube'), str), 'the solution assumed there is a cube in the data'
        return OrderByCellValueHierarchySet(underlying_hierarchy_set=item[1], cube=data['cube'], mdx_tuple=item[5])

    def descendants_hierarchy_set(self, item):
        assert isinstance(
            item[1],
            (TuplesSet,
             MdxHierarchySet)), 'the solution assumed the second element of the list is TuplesSet or MdxHierarchySet'
        if len(item) > 3:
            raise ValueError(
                "descendants hierarchy set does not support parameter, but it is needed. raise the issue to GitHub")
        return DescendantsHierarchySet(member=item[1],)

    def elements_hierarchy_set(self, item):
        hierarchy_set = ElementsHierarchySet(*[i for i in item if isinstance(i, Member)])
        if not hierarchy_set.members:
            raise ValueError("The members list in hierarchy_set is empty. Cannot access the first member.")
        hierarchy_set.dimension = hierarchy_set.members[0].dimension
        hierarchy_set.hierarchy = hierarchy_set.members[0].hierarchy
        return hierarchy_set
