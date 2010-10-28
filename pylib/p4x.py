#!/usr/bin/env python3

"""python 4 XML (P4X) - a scripty way to manipulate XML

P4X provides javascript like loose syntax for creating or manipulating 
an XML document.

根据 http://ponderer.org/cvs/index.pl/python/p4x/ 改写，原文件为 Python2 版
"""

# TODO: * operator to get all child nodes
# TODO: 注释

# the use of minidom is pretty arbitrary, any xml parser with DOM should work
import io
from xml.dom import minidom
from xml.sax import saxutils

class PBase:
  def __str__(self):
    """Serialize into xml."""
    buffer = io.StringIO()
    handler = saxutils.XMLGenerator(buffer)
    self.__dict__['@publish'](handler)
    return buffer.getvalue()
  
class PList(PBase):
  """A list of PNode objects with the same parent node."""
  
  def __init__(self, nodes=[]):
    self.__dict__['@nodes'] = nodes
    self.__dict__['@publish'] = self.__publish
  
  def __getitem__(self, idx):
    """Pass operation onto list."""
    nodes = self.__dict__['@nodes']
    if idx in range(len(nodes)):
      return nodes[idx]
    return None

  def __setitem__(self, idx, value):
    """Change an existing item or create a new item."""
    pnodes = self.__dict__['@nodes']
    if idx < len(pnodes):
      for l in pnodes:
        dom = l.__dict__['@dom']
        _SetNodeValue(dom, value)
    else:
      if not len(pnodes):
        # should never be here
        raise Exception("Can't create sibling in an empty list.")
      
      # We're past list bounds so we append a new entry (this is what E4X
      # does). TODO: should we give a warning if we're more than 1 past
      # array bounds?
      
      # All the nodes in a Plist are currently of the same type.  This will
      # change once * is implemented.
      oldNode = pnodes[0].__dict__['@dom']
      newNode = oldNode.ownerDocument.createElement(oldNode.nodeName)
      _SetNodeValue(newNode, value)
      oldNode.parentNode.childNodes.append(newNode)

  def __iter__(self):
    """Pass operation onto list."""
    return self.__dict__['@nodes'].__iter__()

  def __len__(self):
    """Length of the list."""
    return self.__dict__['@nodes'].__len__()
  
  def __call__(self, **kwargs):
    """Handle attribute filters.  For example, to get all nodes that have the
    attribute foo=42, you would call with params foo=42 (or _foo=42)."""
    nodes = []

    for pnode in self.__dict__['@nodes']:
      attrs = pnode.__dict__['@dom'].attributes
      
      match = True
      # check to see if the node matches the filters
      for key, value in kwargs:
        # filters may start with an underscore
        if key.startswith('_'):
          key = key[1:]
        
        # make sure it has the attribute
        if key not in attrs:
          match = False
          break
        elif value != None:
          # if a value is provided, make sure the value matches
          if attrs[key].value != str(value):
            match = False
            break
      if match:
        nodes.append(pnode)
    
    if len(nodes):
      return PList(nodes)
        
    return None

  def __bool__(self):
    return bool(len(self.__dict__['@nodes']))

  def __getattr__(self, key):
    # check self
    if key in self.__dict__:
      return self.__dict__[key]

    if key.startswith('_'):
      # attribute
      values = []
      for pnode in self.__dict__['@nodes']:
        value = getattr(pnode, key)
        if value:
          values.append(value)
      
      if len(values):
        return values
    else:
      # check to see if it's in the DOM node
      nodes = []
      for pnode in self.__dict__['@nodes']:
        plist = getattr(pnode, key)
        if plist:
          nodes.extend(plist.__dict__['@nodes'])
      if len(nodes):
        return PList(nodes)

    return None

  def __setattr__(self, key, value):
    """Set an attribute in the node."""
    if key.startswith('_'):
      key = key[1:]
      
      # attribute update
      for pnode in self.__dict__['@nodes']:
        node = pnode.__dict__['@dom']
        node.attributes[key] = value
    else:
      # node creation, only works if there is exactly one node
      pnodes = self.__dict__['@nodes']
      if not len(pnodes):
        # should never be here
        raise Exception("Can't create sibling in an empty list.")
      elif len(pnodes) > 1:
        raise AttributeError("Can't set property in xml list.")

      # there should be exactly 1 node
      setattr(pnodes[0], key, value)

  def __delattr__(self, key):
    """Remove attrs and elements from the DOM."""
    if key.startswith('_'):
      key = key[1:]
      for pnode in self.__dict__['@nodes']:
        node = pnode.__dict__['@dom']
        del node.attributes[key]
    else:
      for pnode in self.__dict__['@nodes']:
        node = pnode.__dict__['@dom']
        deleting = [n for n in node.childNodes if n.nodeName == key]
        for n in deleting:
          node.removeChild(n)

  def __repr__(self):
    return 'PList(%s)' % repr(self.__dict__['@nodes'])

  def __publish(self, handler):
    """Write the xml output."""
    for pnode in self.__dict__['@nodes']:
      pnode.__dict__['@publish'](handler)
      handler.ignorableWhitespace('\n')


class PNode(PBase):
  """This is a wrapper for element nodes."""
  def __init__(self, node):
    self.__dict__['@dom'] = node
    self.__dict__['@publish'] = self.__publish

  def __publish(self, handler):
    handler.startElement(self.__dict__['@dom'].nodeName,
                         dict(self.__dict__['@dom'].attributes.items()))
    for child in self.__dict__['@dom'].childNodes:
      if minidom.Node.ELEMENT_NODE == child.nodeType:
        PNode(child).__dict__['@publish'](handler)
      elif minidom.Node.TEXT_NODE == child.nodeType:
        PText(child).__dict__['@publish'](handler)
      # TODO: other node types?
    handler.endElement(self.__dict__['@dom'].nodeName)

  def __getattr__(self, key):
    # check the local object first
    if key in self.__dict__:
      return self.__dict__[key]

    if key.startswith('_'):
      # attribute
      attr = key[1:]
      if attr in self.__dict__['@dom'].attributes:
        return self.__dict__['@dom'].attributes[attr].value
    else:
      # check to see if it's in the DOM node
      nodes = []
      for node in self.__dict__['@dom'].childNodes:
        if node.nodeName == key:
          nodes.append(PNode(node))
      if len(nodes):
        return PList(nodes)

    return None
  
  def __setattr__(self, key, value):
    """Set an attribute in the node."""
    if key.startswith('_'):
      # set attribute
      key = key[1:]
      node = self.__dict__['@dom']
      node.attributes[key] = value
    else:
      # set node
      # get the first node that matches or create a new one
      node = self.__dict__['@dom']
      newChildNodes = []
      updateNode = None
      for child in node.childNodes:
        if child.nodeName == key:
          if not updateNode:
            updateNode = child
            newChildNodes.append(child)
        else:
          newChildNodes.append(child)
      if not updateNode:
        # create a new node
        updateNode = node.ownerDocument.createElement(key)
        node.appendChild(updateNode)
        newChildNodes.append(updateNode)
      
      # add in the value node
      _SetNodeValue(updateNode, value)
      
      # update the node
      node.childNodes = newChildNodes
  
  def __delattr__(self, key):
    if key.startswith('_'):
      # delete an attribute
      key = key[1:]
      node = self.__dict__['@dom']
      del node.attributes[key]
    else:
      node = self.__dict__['@dom']
      deleting = [n for n in node.childNodes if n.nodeName == key]
      for n in deleting:
        node.removeChild(n)

  def __repr__(self):
    return 'PNode(%s)' % repr(str(self.__dict__['@dom']))
  
class PText(PBase):
  def __init__(self, node):
    self.__dict__['@dom'] = node
    self.__dict__['@publish'] = self.__publish
  
  def __publish(self, handler):
    handler.characters(self.__dict__['@dom'].nodeValue)

  def __repr__(self):
    return 'PText(%s)' % repr(str(self.__dict__['@dom']))

class P4X(PNode):
  """This is a wrapper for the DOM document root."""

  def __init__(self, literal='<xml/>'):
    doc = minidom.parseString(literal)
    # find the root element
    root = doc.documentElement
    PNode.__init__(self, root)
    self.__dict__['@doc'] = doc
    self.__dict__['@publish'] = self.__publish
  
  def __publish(self, handler):
    PNode(self.__dict__['@dom']).__dict__['@publish'](handler)
  
  def __repr__(self):
    return 'P4X(%s)' % repr(str(self))

def _SetNodeValue(domnode, value):
  """Set the contents of a dom node.
  domnode: the node to set the contents of
    value: the value to apply to the node. This can be None, a string, a dom
           node, a list of dom nodes, a PNode or a PList."""
  if value is None:
    # no children
    domnode.childNodes = []
  elif isinstance(value, str):
    doc = domnode.ownerDocument
    inner = doc.createTextNode(value)
    domnode.childNodes = [inner]
  else:
    # Handle DOM nodes, list of DOM nodes, PNode, PList, PText, P4X
    raise NotImplementedError

def getDOM(pobj):
  """This is a helper function to get the DOM element out of a PNode or P4X
  object."""
  return pobj.__dict__['@dom']

def toSimpleString(pobj):
  """This is a helper function to get an XML string.  If it's a node with a
  single text node as child, it returns the text.  Otherwise, it returns the
  XML including the node itself.  This is more like how E4X returns values
  in Gecko."""

  nodelist = pobj.__dict__.get('@nodes', None)
  if nodelist:
    if len(nodelist) == 1:
      node = nodelist[0]
    else:
      return pobj.__str__()
  else:
    node = pobj
  children = node.__dict__['@dom'].childNodes
  if len(children) == 0:
    return ''
  texts = [x.nodeValue for x in children if x.nodeType == minidom.Node.TEXT_NODE]
  if len(texts) == len(children):
    return ''.join(texts)
  return str(node)
