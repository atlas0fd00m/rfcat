
import vstruct
import vstruct.primitives as vs_prim

class fat_header(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self, bigend=True)
        self.magic = vs_prim.v_uint32()
        self.nfat_arch = vs_prim.v_uint32()

class fat_arch(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self, bigend=True)
        self.cputype    = vs_prim.v_uint32()  # cpu specifier (int) */
        self.cpusubtype = vs_prim.v_uint32()  # machine specifier (int) */
        self.offset     = vs_prim.v_uint32()  # file offset to this object file */
        self.size       = vs_prim.v_uint32()  # size of this object file */
        self.align      = vs_prim.v_uint32()  # alignment as a power of 2 */

