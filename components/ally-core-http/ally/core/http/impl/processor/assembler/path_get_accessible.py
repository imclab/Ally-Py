'''
Created on Feb 7, 2014

@package: ally core http
@copyright: 2014 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Mugur Rus

Finds all get invokers that can be directly accessed without the need of extra information, basically all paths that can be
directly related to a node.
'''

from collections import OrderedDict

from ally.api.operator.extract import inheritedTypesFrom
from ally.api.operator.type import TypeModel, TypeProperty
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.server import HTTP_GET


# --------------------------------------------------------------------
class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    nodes = requires(list)
    polymorphed = requires(dict)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Optional
    shadowing = optional(Context)
    filterName = optional(str)
    # ---------------------------------------------------------------- Required
    node = requires(Context)
    target = requires(TypeModel)
    isModel = requires(bool)
    isCollection = requires(bool)
    methodHTTP = requires(str)
    path = requires(list)
    
class Element(Context):
    '''
    The element context.
    '''
    # ---------------------------------------------------------------- Required
    name = requires(str)
    property = requires(TypeProperty)

class Node(Context):
    '''
    The node context.
    '''
    # ---------------------------------------------------------------- Required
    parent = requires(Context)
    invokers = requires(dict)
    nodesByProperty = requires(dict)
    child = requires(Context)
    childByName = requires(dict)
    properties = requires(set)
    # ---------------------------------------------------------------- Defined
    invokersAccessible = defines(dict, doc='''
    @rtype: dict{TypeModel:[tuple(string, Context)]}
    The dictionary of list of invokers tuples that are accessible for this node for the key model.
    The first entry in tuple is a generated invoker name.
    ''')

class Polymorph(Context):
    '''
    The polymorph context.
    '''
    # ---------------------------------------------------------------- Required
    target = requires(TypeModel)
    parents = requires(list)
    values = requires(dict)

# --------------------------------------------------------------------

class PathGetAccesibleHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the accessible invokers for a node.
    '''
    method = HTTP_GET
    # THe method to index the accessible paths for.
    
    def __init__(self):
        assert isinstance(self.method, str), 'Invalid method %s' % self.method
        super().__init__(Invoker=Invoker, Element=Element, Node=Node)

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provides the accessible invokers.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.nodes: return  # No nodes to process
        
        mandatories = {}
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.methodHTTP != self.method: continue
            if Invoker.filterName in invoker and invoker.filterName: continue
            
            if not invoker.isModel or not invoker.target: continue
            
            available = self.invokerAvailable(invoker)
            
            invoker.node.invokersAccessible = self.processAccessible(register.invokers, invoker.target, mandatories,
                            available, invoker.node.invokersAccessible, invoker.shadowing if Invoker.shadowing in invoker else None)
        
        # Handling the polymorph accessible paths.
        if not register.polymorphed: return
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            if invoker.methodHTTP != self.method: continue
            if Invoker.filterName in invoker and invoker.filterName: continue
            if not invoker.isModel or not invoker.target or not invoker.node.nodesByProperty: continue
            if invoker.target not in register.polymorphed: continue
            
            for polymorph in register.polymorphed[invoker.target]:
                assert isinstance(polymorph, Polymorph), 'Invalid polymorph %s' % polymorph
                assert isinstance(polymorph.target, TypeModel)
                
                if polymorph.target.propertyId is None: continue
                pnodes = invoker.node.nodesByProperty.get(polymorph.target.propertyId)
                if not pnodes: continue
                for pnode in pnodes:
                    assert isinstance(pnode, Node)
                    if self.method in pnode.invokers and pnode.invokersAccessible:
                        pinvoker = pnode.invokers[self.method]
                        if pinvoker.target == polymorph.target:
                            for accessible in pnode.invokersAccessible.values():
                                for ainvoker in accessible.values():
                                    invoker.node.invokersAccessible = self.merge(invoker.node.invokersAccessible,
                                                                                 polymorph.target, ainvoker)
                    else:
                        invoker.node.invokersAccessible = self.processAccessible(register.invokers, polymorph.target, mandatories,
                            available, invoker.node.invokersAccessible, None)
    
    # ----------------------------------------------------------------
    
    def invokerAvailable(self, invoker):
        assert isinstance(invoker, Invoker)
        
        available = set()
        for el in invoker.path:
            assert isinstance(el, Element), 'Invalid element %s' % el
            if el.property:
                assert isinstance(el.property, TypeProperty), 'Invalid element property %s' % el.property
                assert isinstance(el.property.parent, TypeModel), 'Invalid element property %s' % el.property.parent
                available.add(el.property)
                for model in inheritedTypesFrom(el.property.parent.clazz, TypeModel, inDepth=True):
                    assert isinstance(model, TypeModel)
                    if el.property.name in model.properties: available.add(model.properties[el.property.name])
        
        return available
    
    def processAccessible(self, invokers, target, mandatories, available, invokersAccessible, shadowing):
        '''
        Process the accessible paths.
        '''
        assert isinstance(target, TypeModel)
        package = mandatories.get(target)
        if package is None:
            mandatory, types = set(), set(inheritedTypesFrom(target.clazz, TypeModel, inDepth=True))
            for model in types:
                assert isinstance(model, TypeModel)
                mandatory.update(model.properties.values())
            mandatories[target] = (mandatory, types)
        else:
            mandatory, types = package
                
        for invoker in invokers:
            assert isinstance(invoker, Invoker)
            if invoker.methodHTTP != self.method: continue
            if Invoker.filterName in invoker and invoker.filterName: continue
            if not invoker.isCollection and invoker.target in types: continue
            if Invoker.shadowing in invoker and invoker.shadowing: continue
            if shadowing == invoker: continue
            
            hasMandatory = False
            for el in invoker.path:
                assert isinstance(el, Element), 'Invalid element %s' % el
                if not el.property: continue
                if el.property in mandatory: hasMandatory = True
                elif el.property not in available: break
            else:
                if hasMandatory:
                    invokersAccessible = self.merge(invokersAccessible, target, invoker)
                        
        return invokersAccessible
    
    def merge(self, invokersAccessible, target, invoker):
        '''
        Merge the invoker in the accessible dictionary.
        '''
        if invokersAccessible is None: invokersAccessible = {}
        accessible = invokersAccessible.get(target)
        if accessible is None: accessible = invokersAccessible[target] = OrderedDict()
        
        for el in reversed(invoker.path):
            if el.name:
                ainvoker = accessible.get(el.name)
                if ainvoker and self.priorityInvoker(ainvoker) > self.priorityInvoker(invoker): break
                accessible[el.name] = invoker
                break
        return invokersAccessible
    
    def priorityInvoker(self, invoker):
        ''' Provides the priority of an invoker.'''
        assert isinstance(invoker, Invoker)
        
        priority = 0
        for el in invoker.path:
            if el.property: priority += 1
        return priority
