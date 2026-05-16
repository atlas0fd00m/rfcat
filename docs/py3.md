## Summary of Changes Made for Python 3.14 Compatibility

### 1. `rfcat/rflib/chipcon_nic.py` (lines 80-83)
**Before:**
```rfcat/rflib/chipcon_nic.py#L80-83
def savePkts(pkts, filename):
    pickle.dump(pkts, file(filename, 'a'))
def loadPkts(filename):
    return pickle.load( file(filename, 'r'))
```
**After:**
```rfcat/rflib/chipcon_nic.py#L80-83
def savePkts(pkts, filename):
    pickle.dump(pkts, open(filename, "ab"))
def loadPkts(filename):
    return pickle.load(open(filename, "rb"))
```
**Issue:** `file()` doesn't exist in Python 3. Changed to `open()` with appropriate binary modes (`'ab'` and `'rb'`).

---

### 2. `rfcat/rflib/vstruct/builder.py` (line 222)
**Before:**
```rfcat/rflib/vstruct/builder.py#L222
p = PE.PE(file(sys.argv[1], 'rb'))
```
**After:**
```rfcat/rflib/vstruct/builder.py#L222
p = PE.PE(open(sys.argv[1], 'rb'))
```
**Issue:** `file()` doesn't exist in Python 3.

---

### 3. `rfcat/rflib/vstruct/builder.py` (lines 194-197)
**Before:**
```rfcat/rflib/vstruct/builder.py#L194-197
'[ %s() for i in xrange( %d / len(%s())) ]' % (ftypename, fsize, ftypename)
```
**After:**
```rfcat/rflib/vstruct/builder.py#L194-197
'[ %s() for i in range( %d // len(%s())) ]' % (ftypename, fsize, ftypename)
```
**Issues:** 
- `xrange` doesn't exist in Python 3, changed to `range`
- Changed `/` to `//` for integer division (proper for code generation)

---

### 4. `rfcat/rflib/ccspecan.py` (line 507)
**Before:**
```rfcat/rflib/ccspecan.py#L507
if type(data) == str:
```
**After:**
```rfcat/rflib/ccspecan.py#L507
if isinstance(data, str):
```
**Issue:** Direct type comparison is discouraged in Python 3. Use `isinstance()` instead.

---

### 5. `rfcat/rflib/fakedongle_nic.py` (lines 177-180)
**Before:**
```rfcat/rflib/fakedongle_nic.py#L177-180
if type(data) == int and data < 0x100:
    data = b'%c' % data
```
**After:**
```rfcat/rflib/fakedongle_nic.py#L177-180
if isinstance(data, int) and data < 0x100:
    data = bytes([data])
```
**Issues:**
- Direct type comparison changed to `isinstance()`
- `b'%c' % data` doesn't work in Python 3 when `data` is an integer. Changed to `bytes([data])` to create a single-byte bytes object

---

### Test Results
All 6 tests passed:
- `tests.test_api.TestApis.test_api_nic` ✅
- `tests.test_basics.RfCatBasicTests.test_importing` ✅
- `tests.test_bits.BitsTest.test_bits` ✅

The functionality remains the same as before after these Python 3.14 compatibility changes.
