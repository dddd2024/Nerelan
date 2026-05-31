# rc4enc_3480917d Static Analysis Notes

## Sample
- case_id: rc4enc_3480917d
- sha256: 3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f
- size_bytes: 196693
- format: PE32 i386, VC++ Debug build

## Classification
- primary: rc4_compare
- secondary: string_encrypt_verify

## Static Evidence
- Prompt: "please input a correct string to encrypt:"
- Success: "WoW!!!Great!!!You are a genius!!!"
- Failure: "Sorry you are wrong!"
- RC4 key: "WORKER" (6 bytes: 57 4F 52 4B 45 52) at .data 0x29A30
- Non-standard S-box init: filled with 0xCC, first 6 bytes +2 (become 0xCE), then standard KSA
- Target ciphertext: d5 23 a5 22 75 d8 b7 80 (8 bytes at .data 0x29B30)
- Imports: KERNEL32.dll only (59 functions), no crypto API
- RC4 implementation is fully inlined in .text segment

## Recovered Logic
1. Program prompts for input string
2. Initializes RC4 S-box with non-standard preprocessing:
   - Fill S-box with 0xCC
   - S[0..5] += 2 (becomes 0xCE for first 6 bytes matching key length)
   - Execute standard KSA with key "WORKER"
3. Encrypts 8 bytes of user input using modified RC4
4. Compares with hardcoded ciphertext d5 23 a5 22 75 d8 b7 80
5. Match: "WoW!!!" / Mismatch: "Sorry you are wrong!"

## Solver Approach
- RC4 is symmetric: encrypt(key, plaintext) == encrypt(key, ciphertext)
- Use same modified RC4 to "decrypt" the target ciphertext
- The non-standard S-box init must be replicated exactly

## Runtime Scope
- sample executable was not executed
- IDA/Olly/Frida/runtime probe was not used
