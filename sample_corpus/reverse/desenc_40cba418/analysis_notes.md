# desenc_40cba418 Static Analysis Notes

## Sample
- case_id: desenc_40cba418
- sha256: 40cba4189a9639da601b9d9b74fd9937c3d03fc93c90f5df12840e8b7763700f
- size_bytes: 200784
- format: PE32 i386, VC++ Debug build

## Classification
- primary: des_ecb_compare
- secondary: string_encrypt_verify

## Static Evidence
- Prompt: "give me a string to encrypt:"
- Success: "G00d Job!!"
- Failure: "Wrong!!"
- DES key: "TakeEasy" (8 bytes at .rdata offset 0x458)
- Standard DES lookup tables found in .rdata (IP, FP, E, PC-1, PC-2, 8 S-boxes, shift schedule)
- Imports: KERNEL32.dll only (59 functions), no crypto API
- DES implementation is fully inlined in .text segment
- Post-encryption: system("pause")

## Recovered Logic
1. Program prompts for input string
2. Encrypts input with DES-ECB using key "TakeEasy"
3. Compares 8-byte ciphertext block with hardcoded expected ciphertext
4. Outputs "G00d Job!!" on match, "Wrong!!" on mismatch

## Solver Approach
- Key "TakeEasy" is known from static analysis
- DES algorithm is standard
- Need to locate the 8-byte expected ciphertext in the binary
- Approach: scan all 8-byte aligned blocks, decrypt with DES-ECB key "TakeEasy", check for printable results

## Runtime Scope
- sample executable was not executed
- IDA/Olly/Frida/runtime probe was not used
