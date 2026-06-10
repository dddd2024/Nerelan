# cpp_6af7c7f1 Static Analysis Notes

## Sample

- case_id: `cpp_6af7c7f1`
- sample path: `local_reverse_samples/cpp_6af7c7f1/sample.exe`
- sha256: `6af7c7f131eb4991b04f1dc04fd2341113da1aaa318018c14b9e9b81a37186c3`
- size_bytes: `196690`
- format: PE32 console-style executable

## Classification

- primary classification: `string_compare`
- secondary pattern: affine lowercase alphabet transform
- static evidence:
  - ASCII prompt string: `please input a string:`
  - success string: `Ok, you know it. Just hang on.`
  - failure string: `Sorry! Hang on!`
  - target string: `qvldxt`
  - input format string: `%s`

## Recovered Logic

The main routine reads a string into a stack buffer, rejects any character
outside `a` through `z`, then transforms each input byte:

```text
x = ord(input_char) - ord('a')
y = (x * 5 + 7) mod 26
output_char = chr(y + ord('a'))
```

The transformed string is compared with:

```text
qvldxt
```

The modular inverse of `5 mod 26` is `21`, so the inverse is:

```text
x = (y - 7) * 21 mod 26
```

Applying that inverse to `qvldxt` gives:

```text
higuys
```

## Runtime Scope

- sample executable was not executed
- IDA/Olly/Frida/runtime probe was not used
- analysis used static PE bytes, strings, imports, and local disassembly only
