'''
Created on Nov 24, 2011

@package: ally core
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the configurations for the processors used in handling the request.
'''

from .encode import assemblyEncode
from .parsing_rendering import renderingAssembly, assemblyParsing
from ally.container import ioc
from ally.core.impl.processor.arguments import ArgumentsPrepareHandler, \
    ArgumentsBuildHandler
from ally.core.impl.processor.content import ContentHandler
from ally.core.impl.processor.decoder import CreateDecoderHandler
from ally.core.impl.processor.encoding import EncodingHandler
from ally.core.impl.processor.invoking import InvokingHandler
from ally.core.impl.processor.parsing import ParsingHandler
from ally.core.impl.processor.rendering import RenderingHandler
from ally.core.impl.processor.text_conversion import ConversionSetHandler
from ally.core.spec.resources import Normalizer, Converter
from ally.design.processor.handler import Handler
from ally.core.impl.processor.render_encoder import RenderEncoderHandler

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.config
def default_language():
    '''The default language to use in case none is provided in the request'''
    return 'en'

@ioc.config
def default_characterset() -> str:
    '''The default character set to use if none is provided in the request'''
    return 'UTF-8'

@ioc.config
def explain_detailed_error():
    '''If True will provide as an error response a detailed response containing info about where the problem originated'''
    return True

# --------------------------------------------------------------------

@ioc.entity
def normalizer() -> Normalizer: return Normalizer()

@ioc.entity
def converter() -> Converter: return Converter()

# --------------------------------------------------------------------

@ioc.entity
def argumentsPrepare() -> Handler: return ArgumentsPrepareHandler()

@ioc.entity
def rendering() -> Handler:
    b = RenderingHandler()
    b.charSetDefault = default_characterset()
    b.renderingAssembly = renderingAssembly()
    return b

@ioc.entity
def conversion() -> Handler:
    b = ConversionSetHandler()
    b.normalizer = normalizer()
    b.converter = converter()
    return b

@ioc.entity
def encoding() -> Handler:
    b = EncodingHandler()
    b.encodeAssembly = assemblyEncode()
    return b

@ioc.entity
def createDecoder() -> Handler: return CreateDecoderHandler()

@ioc.entity
def parsing() -> Handler:
    b = ParsingHandler()
    b.charSetDefault = default_characterset()
    b.parsingAssembly = assemblyParsing()
    return b

@ioc.entity
def content() -> Handler: return ContentHandler()

@ioc.entity
def argumentsBuild() -> Handler: return ArgumentsBuildHandler()

@ioc.entity
def invoking() -> Handler: return InvokingHandler()

@ioc.entity
def renderEncoder() -> Handler: return RenderEncoderHandler()

