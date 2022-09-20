"""

    Python implementation of cc_schema_graph.cpp from lx sdk samples.

    Comments will be taken from there mostly as well.

"""

import lx
import lxu
import lxu.meta

NAME = "py.schema.graph"

"""

    There's no need to subclass the CLxSchematicConnection class because we're
    only going to use default behavior.

        - Links are managed using a graph.
        - Connection points are added only to one item type.
        - Items of all types can be connected.

    Any or all of these can be overridden by methods on a custom
    CLxSchematicConnection class, but it's not required.

    Likewise we're going to use the default CLxPackage class because we don't
    need any custom item behaviors on our test item.
    
"""

# lxu meta classes accept the name of the "server" and a class
schematic_meta = lxu.meta.Meta_SchematicConnection(NAME, lxu.meta.SchematicConnection)
package_meta = lxu.meta.Meta_Package(NAME, lxu.meta.Package)

# The C++ example creates a MetaRoot subclass and sets these in the pre_init,
# but I think this works just as well in Python.
schematic_meta.set_graph(NAME)
schematic_meta.set_itemtype(NAME)

package_meta.set_supertype(lx.symbol.sITYPE_LOCATOR)
package_meta.add_tag(lx.symbol.sPKG_GRAPHS, NAME)

lxu.meta.MetaRoot(schematic_meta, package_meta)
