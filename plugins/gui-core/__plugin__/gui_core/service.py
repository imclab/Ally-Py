'''
Created on Jan 9, 2012

@package: gui core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services for the gui core.
'''

from __setup__.ally.notifier import registersListeners
from ally.container import ioc, support
from ally.design.processor.assembly import Assembly
from ally.design.processor.handler import Handler
from ally.xml.digester import Node, RuleRoot
from gui.core.config.impl.processor.configuration_notifier import \
    ConfigurationListeners
from gui.core.config.impl.processor.xml.parser import ParserHandler
from gui.core.config.impl.rules import AccessRule, MethodRule, URLRule, \
    ActionRule, DescriptionRule, GroupRule

# --------------------------------------------------------------------
# The synchronization processors
synchronizeAction = synchronizeGroups = synchronizeGroupActions = support.notCreated  # Just to avoid errors
support.createEntitySetup('gui.core.config.impl.processor.synchronize.**.*')

# --------------------------------------------------------------------

@ioc.config
def access_group():
    '''
    Contains the names of the access groups that are expected in the configuration file. Expected properties are name and
    optionally a flag indicating if actions are allowed.
    '''
    return {
            'Anonymous': dict(hasActions=True, isAnonymous=True),
            'Captcha': dict(hasActions=False),
            'Right': dict(hasActions=True)
            }

@ioc.config
def gui_configuration():
    ''' The URI pattern (can have * for dynamic path elements) where the XML configurations can be found.'''
    return 'file:///home/mihaigociu/Work/*/config_test.xml'

# --------------------------------------------------------------------

@ioc.entity
def assemblyConfiguration() -> Assembly:
    return Assembly('GUI Configurations')

@ioc.entity
def nodeRootXML() -> Node: return RuleRoot()

@ioc.entity
def parserXML() -> Handler:
    b = ParserHandler()
    b.rootNode = nodeRootXML()
    return b

@ioc.entity
def configurationListeners() -> Handler:
    b = ConfigurationListeners()
    b.assemblyConfiguration = assemblyConfiguration()
    b.patterns = [gui_configuration()]
    return b

# --------------------------------------------------------------------

@ioc.before(synchronizeGroupActions)
def updateAccessGroup():
    synchronizeGroupActions().anonymousGroups = set(name for name, spec in access_group().items()
                                                    if spec.get('isAnonymous', False))

@ioc.before(synchronizeGroups)
def updateGroup():
    synchronizeGroups().anonymousGroups = set(name for name, spec in access_group().items()
                                                    if spec.get('isAnonymous', False))

@ioc.before(nodeRootXML)
def updateRootNodeXMLForGroups():
    for name, spec in access_group().items():
        assert isinstance(name, str), 'Invalid name %s' % name
        assert isinstance(spec, dict), 'Invalid specifications %s' % spec
        node = nodeRootXML().addRule(GroupRule(), 'Config/%s' % name)
        addNodeAccess(node)
        addNodeDescription(node)
        if spec.get('hasActions', False): addNodeAction(node)

@ioc.before(assemblyConfiguration)
def updateAssemblyConfiguration():
    assemblyConfiguration().add(parserXML(), synchronizeAction(), synchronizeGroups(), synchronizeGroupActions())

@ioc.before(registersListeners)
def updateRegistersListenersForConfiguration():
    registersListeners().append(configurationListeners())


# @app.deploy
# def cleanup():
#     ''' Start the cleanup process for authentications/sessions'''
#     
#     class TestSolicit(Context):
#         '''
#         The solicit context.
#         '''
#         # ---------------------------------------------------------------- Defined
#         file = defines(str, doc='''
#         @rtype: string
#         The file to be parsed.
#         ''')
#         # ---------------------------------------------------------------- Required
#         repository = requires(Context)
#         
#     proc = assemblyConfiguration().create(solicit=TestSolicit)
#     assert isinstance(proc, Processing)
#     solicit = proc.ctx.solicit(file='acl_right_2.xml')
     
#     schedule = scheduler(time.time, time.sleep)
#     def executeCleanup():
#         arg = proc.execute(FILL_ALL, solicit=solicit)
#         assert isinstance(arg.solicit, TestSolicit)
#         
#         if arg.solicit.repository.children:
#             for repository in arg.solicit.repository.children:
#                 if repository.groupName:
#                     print('Group: %s' % repository.groupName)
#                     if repository.description: print('Description: %s' % repository.description)
#                 
#                 print('Actions: ')
#                 if repository.actions:
#                     for action in repository.actions:
#                         print('Action at line %s: ' % action.lineNumber, action.path, action.label, action.script, action.navBar)
#                      
#                 print("Accesses: ")
#                 if repository.accesses:
#                     for access in repository.accesses:
#                         print('Access at line %s: ' % access.lineNumber, access.filters, access.methods, access.urls)        
#                 print()
#     
#         schedule.enter(3, 1, executeCleanup, ())
# 
#     schedule.enter(3, 1, executeCleanup, ())
#     scheduleRunner = Thread(name='Configuration scanner', target=schedule.run)
#     scheduleRunner.daemon = True
#     scheduleRunner.start()
    
# --------------------------------------------------------------------

def addNodeDescription(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    node.addRule(DescriptionRule(), 'Description')

def addNodeAccess(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    
    access = node.addRule(AccessRule(), 'Allows')
    access.addRule(MethodRule(fromAttributes=True))
    access.addRule(URLRule(), 'URL')
    access.addRule(MethodRule(), 'Method')

def addNodeAction(node):
    assert isinstance(node, Node), 'Invalid node %s' % node
    
    action = Node('Action')
    action.addRule(ActionRule())
    action.childrens['Action'] = action
    
    actions = Node('Actions')
    actions.childrens['Action'] = action
    
    node.childrens['Actions'] = actions
    node.childrens['Action'] = action
