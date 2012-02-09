
# FIXME this is named wrong!

import vstruct
from vstruct.primitives import *

class CLIENT_ID(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.UniqueProcess = v_ptr()
        self.UniqueThread = v_ptr()

class EXCEPTION_RECORD(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.ExceptionCode = v_uint32()
        self.ExceptionFlags = v_uint32()
        self.ExceptionRecord = v_ptr()
        self.ExceptionAddress = v_ptr()
        self.NumberParameters = v_uint32()

class EXCEPTION_REGISTRATION(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.prev = v_ptr()
        self.handler = v_ptr()

class HEAP(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.Entry = HEAP_ENTRY()
        self.Signature = v_uint32()
        self.Flags = v_uint32()
        self.ForceFlags = v_uint32()
        self.VirtualMemoryThreshold = v_uint32()
        self.SegmentReserve = v_uint32()
        self.SegmentCommit = v_uint32()
        self.DeCommitFreeBlockThreshold = v_uint32()
        self.DeCommitTotalFreeThreshold = v_uint32()
        self.TotalFreeSize = v_uint32()
        self.MaximumAllocationSize = v_uint32()
        self.ProcessHeapsListIndex = v_uint16()
        self.HeaderValidateLength = v_uint16()
        self.HeaderValidateCopy = v_ptr()
        self.NextAvailableTagIndex = v_uint16()
        self.MaximumTagIndex = v_uint16()
        self.TagEntries = v_ptr()
        self.UCRSegments = v_ptr()
        self.UnusedUnCommittedRanges = v_ptr()
        self.AlignRound = v_uint32()
        self.AlignMask = v_uint32()
        self.VirtualAllocBlocks = ListEntry()
        self.Segments = vstruct.VArray([v_uint32() for i in range(64)])
        self.u = vstruct.VArray([v_uint8() for i in range(16)])
        self.u2 = vstruct.VArray([v_uint8() for i in range(2)])
        self.AllocatorBackTraceIndex = v_uint16()
        self.NonDedicatedListLength = v_uint32()
        self.LargeBlocksIndex = v_ptr()
        self.PseudoTagEntries = v_ptr()
        self.FreeLists = vstruct.VArray([ListEntry() for i in range(128)])
        self.LockVariable = v_uint32()
        self.CommitRoutine = v_ptr()
        self.FrontEndHeap = v_ptr()
        self.FrontEndHeapLockCount = v_uint16()
        self.FrontEndHeapType = v_uint8()
        self.LastSegmentIndex = v_uint8()

class HEAP_SEGMENT(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.Entry = HEAP_ENTRY()
        self.SegmentSignature = v_uint32()
        self.SegmentFlags = v_uint32()
        self.Heap = v_ptr()
        self.LargestUncommitedRange = v_uint32()
        self.BaseAddress = v_ptr()
        self.NumberOfPages = v_uint32()
        self.FirstEntry = v_ptr()
        self.LastValidEntry = v_ptr()
        self.NumberOfUnCommittedPages = v_uint32()
        self.NumberOfUnCommittedRanges = v_uint32()
        self.UncommittedRanges = v_ptr()
        self.SegmentAllocatorBackTraceIndex = v_uint16()
        self.Reserved = v_uint16()
        self.LastEntryInSegment = v_ptr()

class HEAP_ENTRY(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.Size = v_uint16()
        self.PrevSize = v_uint16()
        self.SegmentIndex = v_uint8()
        self.Flags = v_uint8()
        self.Unused = v_uint8()
        self.TagIndex = v_uint8()

class ListEntry(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.Flink = v_ptr()
        self.Blink = v_ptr()

class NT_TIB(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.ExceptionList = v_ptr()
        self.StackBase = v_ptr()
        self.StackLimit = v_ptr()
        self.SubSystemTib = v_ptr()
        self.FiberData = v_ptr()
        #x.Version = v_ptr() # This is a union field
        self.ArbitraryUserPtr = v_ptr()
        self.Self = v_ptr()

class PEB(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.InheritedAddressSpace = v_uint8()
        self.ReadImageFileExecOptions = v_uint8()
        self.BeingDebugged = v_uint8()
        self.SpareBool = v_uint8()
        self.Mutant = v_ptr()
        self.ImageBaseAddress = v_ptr()
        self.Ldr = v_ptr()
        self.ProcessParameters = v_ptr()
        self.SubSystemData = v_ptr()
        self.ProcessHeap = v_ptr()
        self.FastPebLock = v_ptr()
        self.FastPebLockRoutine = v_ptr()
        self.FastPebUnlockRoutine = v_ptr()
        self.EnvironmentUpdateCount = v_uint32()
        self.KernelCallbackTable = v_ptr()
        self.SystemReserved = v_uint32()
        self.AtlThunkSListPtr32 = v_ptr()
        self.FreeList = v_ptr()
        self.TlsExpansionCounter = v_uint32()
        self.TlsBitmap = v_ptr()
        self.TlsBitmapBits = vstruct.VArray([v_uint32() for i in range(2)])
        self.ReadOnlySharedMemoryBase = v_ptr()
        self.ReadOnlySharedMemoryHeap = v_ptr()
        self.ReadOnlyStaticServerData = v_ptr()
        self.AnsiCodePageData = v_ptr()
        self.OemCodePageData = v_ptr()
        self.UnicodeCaseTableData = v_ptr()
        self.NumberOfProcessors = v_uint32()
        self.NtGlobalFlag = v_uint64()
        self.CriticalSectionTimeout = v_uint64()
        self.HeapSegmentReserve = v_uint32()
        self.HeapSegmentCommit = v_uint32()
        self.HeapDeCommitTotalFreeThreshold = v_uint32()
        self.HeapDeCommitFreeBlockThreshold = v_uint32()
        self.NumberOfHeaps = v_uint32()
        self.MaximumNumberOfHeaps = v_uint32()
        self.ProcessHeaps = v_ptr()
        self.GdiSharedHandleTable = v_ptr()
        self.ProcessStarterHelper = v_ptr()
        self.GdiDCAttributeList = v_uint32()
        self.LoaderLock = v_ptr()
        self.OSMajorVersion = v_uint32()
        self.OSMinorVersion = v_uint32()
        self.OSBuildNumber = v_uint16()
        self.OSCSDVersion = v_uint16()
        self.OSPlatformId = v_uint32()
        self.ImageSubsystem = v_uint32()
        self.ImageSubsystemMajorVersion = v_uint32()
        self.ImageSubsystemMinorVersion = v_uint32()
        self.ImageProcessAffinityMask = v_uint32()
        self.GdiHandleBuffer = vstruct.VArray([v_ptr() for i in range(34)])
        self.PostProcessInitRoutine = v_ptr()
        self.TlsExpansionBitmap = v_ptr()
        self.TlsExpansionBitmapBits = vstruct.VArray([v_uint32() for i in range(32)])
        self.SessionId = v_uint32()
        self.AppCompatFlags = v_uint64()
        self.AppCompatFlagsUser = v_uint64()
        self.pShimData = v_ptr()
        self.AppCompatInfo = v_ptr()
        self.CSDVersion = v_ptr()
        self.UNKNOWN = v_uint32()
        self.ActivationContextData = v_ptr()
        self.ProcessAssemblyStorageMap = v_ptr()
        self.SystemDefaultActivationContextData = v_ptr()
        self.SystemAssemblyStorageMap = v_ptr()
        self.MinimumStackCommit = v_uint32()

class SEH3_SCOPETABLE(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.EnclosingLevel = v_int32()
        self.FilterFunction = v_ptr()
        self.HandlerFunction = v_ptr()

class SEH4_SCOPETABLE(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.GSCookieOffset = v_int32()
        self.GSCookieXOROffset = v_int32()
        self.EHCookieOffset = v_int32()
        self.EHCookieXOROffset = v_int32()
        self.EnclosingLevel = v_int32()
        self.FilterFunction = v_ptr()
        self.HandlerFunction = v_ptr()

class TEB(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.TIB = NT_TIB()
        self.EnvironmentPointer = v_ptr()
        self.ClientId = CLIENT_ID()
        self.ActiveRpcHandle = v_ptr()
        self.ThreadLocalStorage = v_ptr()
        self.ProcessEnvironmentBlock = v_ptr()
        self.LastErrorValue = v_uint32()
        self.CountOfOwnedCriticalSections = v_uint32()
        self.CsrClientThread = v_ptr()
        self.Win32ThreadInfo = v_ptr()
        self.User32Reserved = vstruct.VArray([v_uint32() for i in range(26)])
        self.UserReserved = vstruct.VArray([v_uint32() for i in range(5)])
        self.WOW32Reserved = v_ptr()
        self.CurrentLocale = v_uint32()
        self.FpSoftwareStatusRegister = v_uint32()

class CLSID(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.uuid = GUID()

class IID(vstruct.VStruct):
    def __init__(self):
        vstruct.VStruct.__init__(self)
        self.uuid = GUID()

