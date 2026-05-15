# vstruct Module

## Overview

`vstruct` (value structure) is a lightweight binary structure definition and parsing library. It allows you to define C-like structures using Python classes, then easily marshal them to/from byte streams. It is used extensively in RfCat to represent the radio configuration (`RadioConfig`) and other binary layouts.

Key features:
- Define structures with field names and types (`v_uint8`, `v_uint16`, `v_bytes`, etc.)
- Automatic `struct` format string generation and endianness control.
- Nested structures and arrays.
- Parsing from bytes (`vsParse`) and emitting to bytes (`vsEmit`).
- Field alignment for Visual Studio style packing.

## Core Concepts

- **Primitive types**: Subclasses of `v_prim` representing basic data types (`v_uint8`, `v_uint16`, `v_ptr`, etc.).
- **`VStruct`**: Base class for composite structures. You add fields via attributes or `vsAddField`.
- **`VArray`**: A subclass of `VStruct` that behaves as an array of elements.

## Class: `VStruct`

The main class for defining structures.

### Initialization

```python
class VStruct(vs_prims.v_base):
    def __init__(self, bigend=False):
```

- `bigend`: If True, use big-endian format; otherwise little-endian (default).

### Adding Fields

You can define fields in two ways:

1. **Attribute assignment** (at class level or instance level):
    ```python
    class MyStruct(VStruct):
        def __init__(self):
            VStruct.__init__(self)
            self.field1 = v_uint8()
            self.field2 = v_uint16()
    ```

2. **`vsAddField(name, value)`** dynamically:
    ```python
    self.vsAddField('field1', v_uint8())
    ```

Fields must be `vstruct` primitive types or nested `VStruct` instances.

### Format Calculation

- `vsGetFormat()`: Returns the `struct` format string for the entire structure, including any nested structures. The format is built from the primitive fields in field order. Prefixed with `_vs_fmtbase` which is either `'<'` or `'>'` depending on endianness.

### Parsing

- `vsParse(bytes, offset=0)`: Unpacks the binary data into the structure's fields. It:
  - Computes `size = struct.calcsize(fmt)`.
  - Unpacks the slice `bytes[offset:offset+size]`.
  - Assigns each value to the corresponding primitive via `vsSetParsedValue`.

### Emitting

- `vsEmit()`: Packs the current field values into a bytes object. It builds a list of formatted values (using each primitive's `vsGetFmtValue`) and then `struct.pack`s using the format.

### Field Access

- `__getattr__(self, name)`: If `name` is a field name, returns the primitive's value (`vsGetValue()`). Raises `AttributeError` if not found.
- `__setattr__(self, name, value)`: If the field exists, assigns via `vsSetField`. If `value` is a `vstruct` type, adds a new field (dynamic). Otherwise falls back to normal object attribute.

- `vsGetField(name)`: Returns the primitive object (not just value). Equivalent to `self._vs_values[name]`.
- `vsHasField(name)`: Boolean.
- `vsSetField(name, value)`: Sets field value (or if value is a VStruct, replaces the field).

### Iteration and Inspection

- `__iter__`: Yields `(name, field_object)` tuples for each field in order.
- `vsGetFields()`: Returns list of `(name, field_obj)`.
- `vsGetPrintInfo(offset=0, indent=0, top=True)`: Returns list of `(offset, indent, name, field)` for pretty-printing the structure tree.
- `tree(va=0, reprmax=None)`: Returns a multi-line string representation similar to `objdump` or `hexdump -S`. Shows offsets, sizes, and values. Example:
  ```
  0x0000 ( 2)  field1: 0x1234 (4660)
  0x0002 ( 1)  field2: 0xff (255)
  ```

### Length

- `__len__`: Total size in bytes of the structure (`struct.calcsize(fmt)`).

### Substructures and Alignment

- `vsAddField` can accept a nested `VStruct`. The size of nested structs is accounted for automatically.
- Alignment: If `_vs_field_align` is True, padding is added to align fields to the size of the first element of the nested structure (for Visual Studio compatibility). Padding fields are added with names like `_pad0`.

### XOR Operation

- `__ixor__(self, other)`: In-place XOR of two structures field-by-field. Used for bitwise operations on structure instances.

### Utility Methods

- `vsGetClassPath()`: Returns `'module.ClassName'`.
- `vsGetPrims()`: Returns a flat list of all primitive objects in the structure (recursively).
- `vsGetTypeName()`: Returns `_vs_name` (class name).

## Class: `VArray`

An array-like structure where elements are added sequentially.

- `__init__(self, elems=())`: Creates a new VArray and adds each element via `vsAddElement`.
- `vsAddElement(elem)`: Adds a field with numeric name (the index). The element must be a `vstruct` type (typically a primitive or substructure).
- `__getitem__(self, index)`: Returns the field at that index (converted to string key internally).

`VArray` inherits from `VStruct`, so it can be nested.

## Module Functions

### `isVstructType(x)`

Returns True if `x` is an instance of a `v_prim` (i.e., a vstruct primitive or VStruct).

### `resolve(impmod, nameparts)`

Recursively resolves a dotted name (list of parts) within a module. Used by `getStructure` to find definitions in `vstruct.defs`.

### `getStructure(sname)`

Retrieves a structure definition by name. The name can be:
- A short name like `"TEB"` if it's defined in `vstruct.defs` (searches `vstruct.defs` module).
- A full Python path like `"vstruct.defs.windows.TEB"`.

Returns an *instance* of the structure (not the class). If not found, raises an exception or returns `None`? The code attempts to resolve; if `x != None` it returns `x()`, else returns `None`.

### `getModuleNames()`

Returns a list of module names within `vstruct.defs` (e.g., `["windows", "linux", ...]`).

### `getStructNames(modname)`

For a given module name under `vstruct.defs`, returns a list of structure class names defined in that module.

## Primitive Types (`primitives.py`)

The primitive types are the building blocks. Important ones:

- `v_uint8`, `v_uint16`, `v_uint32`, `v_uint64`: Unsigned integers of specified width.
- `v_int8`, `v_int16`, `v_int32`, `v_int64`: Signed integers.
- `v_ptr`: Pointer-sized integer (size depends on architecture; typically 32-bit).
- `v_bytes`: Arbitrary byte sequence. Can be fixed-length or variable? Actually there is `v_bytes` which takes a length in constructor? Let's check. I think `v_bytes` might be a primitive that holds a fixed-size byte array. The implementation likely uses `v_bytes(size)`. It's used in `chipcondefs.py` for padding fields `z0, z1, z2, z3, z4, z5, z6, z7` that are reserved bytes.

Each primitive class provides:
- `vsGetFmtValue()`: Returns the value packed as appropriate for `struct` (usually the integer itself, or a bytes object).
- `vsSetValue(val)`: Sets the internal value.
- `vsGetValue()`: Returns the value.
- `vsSetParsedValue(val)`: Called during parsing to set from unpacked data.

Primitives also define `vsGetFormat()` returning a struct format character (e.g., `'B'` for `v_uint8`, `'H'` for `v_uint16`).

## Usage Example

From `chipcondefs.py`:

```python
class RadioConfig(VStruct):
    def __init__(self):
        VStruct.__init__(self)
        self.sync1 = v_uint8()   # df00
        self.sync0 = v_uint8()   # df01
        self.pktlen = v_uint8()  # df02
        # ... many more fields
```

This defines a 60-byte structure matching the CC1111 radio registers.

To use:

```python
rc = RadioConfig()
rc.sync1 = 0xab
rc.sync0 = 0xcd
data = rc.vsEmit()   # bytes
rc2 = RadioConfig()
rc2.vsParse(data)
print(hex(rc2.sync1), hex(rc2.sync0))
```

In RfCat, `USBDongle.getRadioConfig()` creates a `RadioConfig` instance and calls `peek` for each register to fill it, or `setRadioConfig()` uses `vsEmit()` to get a binary blob and writes it via multiple `poke` calls (one per register). Actually `setRadioConfig` writes each register individually, not the entire blob, because the hardware expects individual register writes. But `vsEmit()` could be used to pack for bulk transfer if needed.

## Design Notes

- The library is intentionally simple; no built-in support for variable-length arrays beyond fixed-size.
- The `VStruct` class stores fields in `_vs_values` dictionary and order in `_vs_fields` list.
- Formatting for `struct` is built lazily by `vsGetFormat()`.
- The code tries to support both Python 2 and 3 (see `StringIO` import handling).

## Limitations

- No automatic handling of bitfields; those are represented as integer primitives.
- Enum types not built-in; you would need to add validation separately.
- The `VArray` doesn't currently support slice assignment (as noted in a FIXME).

## See Also

- `chipcondefs.py` for the most comprehensive use of `vstruct` in RfCat.
