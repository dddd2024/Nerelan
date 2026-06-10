# seh_52be8d5c Static Analysis Notes

## Sample
- case_id: seh_52be8d5c
- sha256: 52be8d5c485f7c7c3340d42791505b9f55cf4ff63191768c0cc62f30cde4ae07
- size_bytes: 196685
- format: PE32 i386, VC++ Debug build

## Classification
- primary: unknown
- secondary: seh_obfuscation

## Static Evidence
- Prompt: "please input password : "
- Success: "Congratulations! You are right!"
- Failure 1: " Sorry, you are wrong!"
- Failure 2: " Sorry,you are wrong!"
- Wrong path: "What a pity, you found a wrong way."
- Password constant in .data: `\eluxfqvF|Puzzce` (16 bytes at 0x29A30)
- PDB path: C:\Documents and Settings\Administrator\\2\Debug\SEH.pdb
- Imports: KERNEL32.dll only (61 functions), no crypto API
- SEH-related imports: UnhandledExceptionFilter, RtlUnwind, DebugBreak

## Analysis
- Program uses SEH exception handling as control flow obfuscation
- Three distinct execution paths based on password validation
- Password constant `\eluxfqvF|Puzzce` found in .data segment
- Transform algorithm unknown: could be XOR, shift, substitution, or multi-step
- SEH handlers may be part of validation logic or anti-debug trap
- No external crypto imports; transform is pure arithmetic/bitwise

## Why SKIPPED_STATIC_INSUFFICIENT
- Password constant extracted but transform algorithm cannot be determined from strings alone
- SEH control flow obfuscation requires disassembly to trace actual validation path
- The .text segment contains ~150KB of inlined CRT code mixed with validation logic
- Without knowing the exact transform (XOR key, shift amount, substitution table),
  brute-forcing all possibilities against `\eluxfqvF|Puzzce` is not feasible
- Requires disassembly (IDA/Ghidra/radare2) to determine transform parameters

## Runtime Scope
- sample executable was not executed
- IDA/Olly/Frida/runtime probe was not used
