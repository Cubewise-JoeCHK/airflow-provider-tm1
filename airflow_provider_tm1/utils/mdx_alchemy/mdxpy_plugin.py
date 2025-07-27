from mdxpy.mdx import MdxHierarchySet 

class DrillUpMemberSet(MdxHierarchySet):
    """
    Represents a set of members to be used in a drill-up operation.
    This class extends MdxHierarchySet to provide functionality for
    handling drill-up operations in MDX queries.
    """
    
    def __init__(self, underlying_hierarchy_set: MdxHierarchySet, other_set: 'MdxHierarchySet'):
        super(DrillUpMemberSet, self).__init__(
            underlying_hierarchy_set.dimension,
            underlying_hierarchy_set.hierarchy)
        self.underlying_hierarchy_set = underlying_hierarchy_set
        self.other_set = other_set

    def to_mdx(self) -> str:
        return f"{{DRILLUPMEMBER({self.underlying_hierarchy_set.to_mdx()}, {self.other_set.to_mdx()})}}"
