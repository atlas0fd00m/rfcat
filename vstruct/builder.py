'''

VStruct builder!  Used to serialize structure definitions etc...

'''

import types
import inspect
import vstruct
import vstruct.primitives as vs_prim

prim_types = [ None, 
               vs_prim.v_uint8,
               vs_prim.v_uint16,
               None,
               vs_prim.v_uint32,
               None, None, None,
               vs_prim.v_uint64
             ]

# VStruct Field Flags
VSFF_ARRAY   = 1
VSFF_POINTER = 2

class VStructConstructor:
    def __init__(self, builder, vsname):
        self.builder = builder
        self.vsname = vsname

    def __call__(self, *args, **kwargs):
        return self.builder.buildVStruct(self.vsname)

class VStructBuilder:

    def __init__(self, defs=(), enums=()):
        self._vs_defs = {}
        self._vs_enums = {}
        self._vs_namespaces = {}
        for vsdef in defs:
            self.addVStructDef(vsdef)
        for enum in enums:
            self.addVStructEnumeration(enum)

    def __getattr__(self, name):
        ns = self._vs_namespaces.get(name)
        if ns != None:
            return ns

        vsdef = self._vs_defs.get(name)
        if vsdef != None:
            return VStructConstructor(self, name)

        raise AttributeError, name

    def addVStructEnumeration(self, enum):
        self._vs_enums[enum[0]] = enum

    def addVStructNamespace(self, name, builder):
        self._vs_namespaces[name] = builder

    def getVStructNamespaces(self):
        return self._vs_namespaces.items()

    def getVStructNamespaceNames(self):
        return self._vs_namespaces.keys()

    def hasVStructNamespace(self, namespace):
        return self._vs_namespaces.get(namespace, None) != None

    def getVStructNames(self, namespace=None):
        if namespace == None:
            return self._vs_defs.keys()
        nsmod = self._vs_namespaces.get(namespace)
        ret = []
        for name in dir(nsmod):
            nobj = getattr(nsmod, name)
            if not inspect.isclass(nobj):
                continue
            if issubclass(nobj, vstruct.VStruct):
                ret.append(name)
        return ret

    def addVStructDef(self, vsdef):
        vsname = vsdef[0]
        self._vs_defs[vsname] = vsdef

    def buildVStruct(self, vsname):
        # Check for a namespace
        parts = vsname.split('.', 1)
        if len(parts) == 2:
            ns = self._vs_namespaces.get(parts[0])
            if ns == None:
                raise Exception('Namespace %s is not present! (need symbols?)' % parts[0])

            # If a module gets added as a namespace, assume it has a class def...
            if isinstance(ns, types.ModuleType):
                cls = getattr(ns, parts[1])
                if cls == None:
                    raise Exception('Unknown VStruct Definition: %s' % vsname)
                return cls()

            return ns.buildVStruct(parts[1])

        vsdef = self._vs_defs.get(vsname)
        if vsdef == None:
            raise Exception('Unknown VStruct Definition: %s' % vsname)

        vsname, vssize, vskids = vsdef

        vs = vstruct.VStruct()
        vs._vs_name = vsname

        for fname, foffset, fsize, ftypename, fflags in vskids:

            if fflags & VSFF_POINTER:
                # FIXME support pointers with types!
                if fsize == 4:
                    fieldval = vs_prim.v_ptr32()

                elif fsize == 8:
                    fieldval = vs_prim.v_ptr64()

                else:
                    raise Exception('Invalid Pointer Width: %d' % fsize)

            elif fflags & VSFF_ARRAY:
                if ftypename != None:
                    fieldval = vstruct.VArray()
                    while len(fieldval) < fsize:
                        fieldval.vsAddElement( self.buildVStruct(ftypename) )
                else:
                # FIXME actually handle arrays!
                    fieldval = vs_prim.v_bytes(size=fsize)

            elif ftypename == None:

                if fsize not in [1,2,4,8]:
                    #print 'Primitive Field Size: %d' % fsize
                    fieldval = v_bytes(size=fsize)

                else:
                    fieldval = prim_types[fsize]()

            else:
                fieldval = self.buildVStruct(ftypename)

            cursize = len(vs)
            if foffset < cursize:
                #print 'FIXME handle unions, overlaps, etc...'
                continue

            if foffset > cursize:
                setattr(vs, '_pad%.4x' % foffset, vs_prim.v_bytes(size=(foffset-cursize)))

            setattr(vs, fname, fieldval)

        return vs

    def genVStructPyCode(self):
        ret = 'import vstruct\n'
        ret += 'from vstruct.primitives import *'
        ret += '\n\n'

        for ename, esize, ekids in self._vs_enums.values():
            ret += '%s = v_enum()\n' % ename
            for kname, kval in ekids:
                ret += '%s.%s = %d\n' % (ename,kname,kval)
            ret += '\n\n'


        for vsname, vsize, vskids in self._vs_defs.values():
            ret += 'class %s(vstruct.VStruct):\n' % vsname
            ret += '    def __init__(self):\n'
            ret += '        vstruct.VStruct.__init__(self)\n'
            offset = 0
            for fname, foffset, fsize, ftypename, fflags in vskids:

                if foffset < offset:
                    continue

                if foffset > offset:
                    ret += '        self._pad%.4x = v_bytes(size=%d)\n' % (foffset, foffset-offset)
                    offset += (foffset - offset)

                if fflags & VSFF_POINTER:
                    if fsize == 4:
                        fconst = 'v_ptr32()'
                    elif fsize == 8:
                        fconst = 'v_ptr64()'
                    else:
                        fconst = 'v_bytes(size=%d) # FIXME should be pointer!' % fsize

                elif fflags & VSFF_ARRAY:
                    if ftypename != None:
                        '[ %s() for i in xrange( %d / len(%s())) ]' % (ftypename, fsize, ftypename)
                    else:
                        fconst = 'v_bytes(size=%d) # FIXME Unknown Array Type' % fsize

                elif ftypename == None:
                    if fsize == 1:
                        fconst = 'v_uint8()'
                    elif fsize == 2:
                        fconst = 'v_uint16()'
                    elif fsize == 4:
                        fconst = 'v_uint32()'
                    elif fsize == 8:
                        fconst = 'v_uint64()'
                    else:
                        fconst = 'v_bytes(size=%d)' % fsize
                else:
                    fconst = '%s()' % ftypename


                ret += '        self.%s = %s\n' % (fname, fconst)
                offset += fsize
            ret += '\n\n'

        return ret

if __name__ == '__main__':
    # Parse windows structures from dll symbols...
    import os
    import sys
    import platform

    from pprint import pprint

    import PE
    import vtrace.platforms.win32 as vt_win32

    p = PE.PE(file(sys.argv[1], 'rb'))
    baseaddr = p.IMAGE_NT_HEADERS.OptionalHeader.ImageBase
    osmajor = p.IMAGE_NT_HEADERS.OptionalHeader.MajorOperatingSystemVersion
    osminor = p.IMAGE_NT_HEADERS.OptionalHeader.MinorOperatingSystemVersion
    machine = p.IMAGE_NT_HEADERS.FileHeader.Machine

    archname = PE.machine_names.get(machine)

    parser = vt_win32.Win32SymbolParser(0xffffffff, sys.argv[1], baseaddr)
    parser.parse()

    t = parser._sym_types.values()
    e = parser._sym_enums.values()
    builder = VStructBuilder(defs=t, enums=e)

    print '# Version: %d.%d' % (osmajor, osminor)
    print '# Architecture: %s' % archname
    print builder.genVStructPyCode()

