'''
Created on Jul 27, 2012

@package: ally core
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the invoker encoder.
'''

from ally.api.type import Type
from ally.container.ioc import injected
from ally.core.spec.transform.encdec import IEncoder
from ally.design.processor.assembly import Assembly
from ally.design.processor.attribute import requires, defines
from ally.design.processor.branch import Branch
from ally.design.processor.context import Context
from ally.design.processor.execution import Processing, Chain
from ally.design.processor.handler import HandlerBranching
from ally.support.api.util_service import isModelId
import logging

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    invokers = requires(list)
    exclude = requires(set)
    
class Invoker(Context):
    '''
    The invoker context.
    '''
    # ---------------------------------------------------------------- Defined
    encoder = defines(IEncoder, doc='''
    @rtype: IEncoder
    The encoder to be used for rendering the response object.
    ''')
    hideProperties = defines(bool, doc='''
    @rtype: boolean
    Indicates that the properties of model rendering should be hidden (not rendering).
    ''')
    # ---------------------------------------------------------------- Required
    id = requires(str)
    node = requires(Context)
    output = requires(Type)
    isCollection = requires(bool)
    invokerGet = requires(Context)
    location = requires(str)

class Create(Context):
    '''
    The create encoder context.
    '''
    # ---------------------------------------------------------------- Defined
    objType = defines(object, doc='''
    @rtype: object
    The object type.
    ''')
    # ---------------------------------------------------------------- Required
    encoder = requires(IEncoder)
    isCorrupted = requires(bool)
    
# --------------------------------------------------------------------

@injected
class EncodingHandler(HandlerBranching):
    '''
    Implementation for a handler that provides the creation of encoders for invokers.
    '''
    
    encodeAssembly = Assembly
    # The encode processors to be used for encoding properties.
    
    def __init__(self):
        assert isinstance(self.encodeAssembly, Assembly), 'Invalid encode assembly %s' % self.encodeAssembly
        super().__init__(Branch(self.encodeAssembly).using(create=Create).
                         included(('invoker', 'Invoker'), ('node', 'Node')).included(), Invoker=Invoker)

    def process(self, chain, processing, register:Register, **keyargs):
        '''
        @see: HandlerBranching.process
        
        Populate the encoder.
        '''
        assert isinstance(chain, Chain), 'Invalid chain %s' % chain
        assert isinstance(processing, Processing), 'Invalid processing %s' % processing
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.invokers: return  # No invokers to process.
        
        for invoker in register.invokers:
            assert isinstance(invoker, Invoker), 'Invalid invoker %s' % invoker
            
            if invoker.invokerGet:
                if invoker.isCollection:
                    # TODO: Gabriel: This is a temporary fix to get the same rendering as before until we refactor the plugins
                    # to return only ids.
                    invoker.hideProperties = True
                elif isModelId(invoker.output): invoker.hideProperties = True
            
            arg = processing.executeWithAll(create=processing.ctx.create(objType=invoker.output),
                                            node=invoker.node, invoker=invoker, **keyargs)
            assert isinstance(arg.create, Create), 'Invalid create %s' % arg.create
            if arg.create.isCorrupted:
                assert isinstance(register.exclude, set), 'Invalid exclude set %s' % register.exclude
                register.exclude.add(invoker.id)
                chain.cancel()
                log.error('Cannot create encoder for %s, at:%s', invoker.output, invoker.location)
            elif arg.create.encoder is not None: invoker.encoder = arg.create.encoder