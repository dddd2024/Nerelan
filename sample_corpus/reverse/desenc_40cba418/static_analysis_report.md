# desenc_40cba418 纯静态分析报告

## 1. 样本基本信息

| 项目 | 值 |
|------|------|
| 文件路径 | `F:\reverse-agent\local_reverse_samples\desenc_40cba418\sample.exe` |
| SHA256 | `40cba4189a9639da601b9d9b74fd9937c3d03fc93c90f5df12840e8b7763700f` |
| 文件大小 | 200,784 bytes |
| PE类型 | PE32 (i386) |
| 入口点 RVA | 0x23A0 |
| ImageBase | 0x400000 |
| 编译器 | Microsoft Visual C++ (Debug build, MSVCRT) |
| PDB路径 | `C:\Documents and Settings\Administrator\桌面\5\Debug\desenc.pdb` |

## 2. PE Sections

| Section | VA | VirtualSize | RawPtr | RawSize | Characteristics |
|---------|------|------|------|------|------|
| .text | 0x1000 | 0x265C0 | 0x1000 | 0x27000 | CODE|EXEC|READ |
| .rdata | 0x28000 | 0x1A34 | 0x28000 | 0x2000 | INIT_DATA|READ |
| .data | 0x2A000 | 0x59DC | 0x2A000 | 0x4000 | INIT_DATA|READ|WRITE |
| .idata | 0x30000 | 0x851 | 0x2E000 | 0x1000 | INIT_DATA|READ|WRITE |
| .reloc | 0x31000 | 0x10CB | 0x2F000 | 0x2000 | INIT_DATA|DISCARDABLE|READ |

## 3. PE Imports

**仅导入 KERNEL32.dll（59个函数），无 CryptAPI / advapi32.dll 导入。**

完整导入列表：
- GetCommandLineA, GetVersion, ExitProcess, TerminateProcess
- GetCurrentProcess, DebugBreak, GetStdHandle, WriteFile
- InterlockedDecrement, OutputDebugStringA, GetProcAddress, LoadLibraryA
- InterlockedIncrement, GetModuleFileNameA, GetLastError
- GetFileAttributesA, UnhandledExceptionFilter
- FreeEnvironmentStringsA/W, WideCharToMultiByte
- GetEnvironmentStrings/W, SetHandleCount, GetFileType
- GetStartupInfoA, GetModuleHandleA, GetEnvironmentVariableA
- GetVersionExA, HeapDestroy, HeapCreate, HeapFree, VirtualFree
- RtlUnwind, IsBadWritePtr, IsBadReadPtr, HeapValidate
- CloseHandle, GetExitCodeProcess, WaitForSingleObject
- CreateProcessA, SetConsoleCtrlHandler, MultiByteToWideChar
- SetFilePointer, GetCPInfo, GetACP, GetOEMCP
- HeapAlloc, VirtualAlloc, HeapReAlloc
- CompareStringA/W, SetEnvironmentVariableA
- GetStringTypeA/W, ReadFile, FlushFileBuffers
- SetStdHandle, LCMapStringA/W

**关键发现：没有导入任何 CryptAPI 函数（如 CryptEncrypt, CryptDecrypt, CryptImportKey 等），也没有 advapi32.dll。DES 加密是纯软件实现，内嵌在 .text 段的代码中。**

## 4. 关键字符串

### 4.1 程序逻辑相关字符串

| 偏移 | 字符串 | 含义 |
|------|--------|------|
| 0x2840C | `G00d Job!!` | 成功提示（注意是 "G00d" 用零代替 "o"） |
| 0x2841C | `Wrong!!` | 失败提示 |
| 0x28428 | `pause` | 暂停命令 |
| 0x28434 | `give me a string to encrypt:` | 提示用户输入 |
| 0x28458 | `TakeEasy` | **疑似 DES 密钥（8字节）** |
| 0x28464 | `cmd.exe` | 用于 system() 调用 |
| 0x2846C | `command.com` | 备用命令解释器 |

### 4.2 关键词搜索结果

- **"encrypt"**: `give me a string to encrypt:` -- 程序要求用户输入一个字符串进行加密
- **"wrong"**: `Wrong!!` -- 加密结果不匹配时输出
- **"DES"**: 仅出现在 PDB 路径 `desenc.pdb` 和 `HeapDestroy`（误匹配）中
- **"flag"**: 仅出现在 CRT 调试字符串 `flag == 0 || flag == 1` 中（误匹配）
- **"password", "serial", "key", "correct", "success", "please", "enter", "RC4", "Base64", "hash", "XOR", "rotate", "Advapi", "cipher", "CBC", "ECB", "PKCS", "sbox", "Feistel"**: 均未找到匹配

### 4.3 UTF-16LE 字符串

无有意义的 UTF-16LE 字符串（仅 x86 指令误识别的 "Bjjjj" 等）。

## 5. DES 加密常量分析

### 5.1 .rdata 段中发现的完整 DES 查找表

在 `.rdata` 段偏移 0x1C 处开始，发现了**完整的标准 DES 算法查找表**：

| 表名 | 文件偏移 | 大小 |
|------|----------|------|
| DES Initial Permutation (IP) | 0x2801C | 64 bytes |
| DES Final Permutation (FP) | 0x2805C | 64 bytes |
| DES Expansion (E) | 0x2809C | 48 bytes |
| DES Left Shift schedule | 0x28154 | 16 bytes |
| DES PC-1 | 0x280EC | 56 bytes |
| DES PC-2 | 0x28124 | 48 bytes |
| DES S-box 1 (row 0) | 0x28164 | 16 bytes |
| DES S-box 2 (row 0) | 0x281A4 | 16 bytes |
| DES S-box 3 (row 0) | 0x281E4 | 16 bytes |
| DES S-box 4 (row 0) | 0x28224 | 16 bytes |
| DES S-box 5 (row 0) | 0x28264 | 16 bytes |
| DES S-box 6 (row 0) | 0x282A4 | 16 bytes |
| DES S-box 7 (row 0) | 0x282E4 | 16 bytes |
| DES S-box 8 (row 0) | 0x28324 | 16 bytes |

所有 8 个 S-box 的 row 0 均匹配标准 DES 规范。这些表从 0x2801C 延续到约 0x28364，共约 860 字节，包含了完整的 DES S-box（8 x 4 x 16 = 512 字节）。

**结论：程序使用纯软件实现的、符合标准规范的 DES 加密算法。**

### 5.2 .rdata 段其他数据

- 0x28004-0x28008: `39 ae d4 5f` -- 可能是时间戳或 GUID 片段
- 0x2840C-0x28460: 程序逻辑字符串（见上表）
- 0x28464 之后: CRT 调试字符串、运行时错误信息等

### 5.3 .data 段分析

.data 段绝大部分为零，仅有少量非零区域：
- 0x2AA30: `28 70 77 48 7b 4f ff 3d` -- 可能是初始化数据或未初始化的堆管理结构
- 其他零星数据多为 0xFF 填充和指针值

**没有发现额外的硬编码密钥或 IV。**

## 6. 关键特征总结

1. **算法**: 标准 DES（纯软件实现，非 CryptAPI）
2. **密钥**: `TakeEasy`（8字节 ASCII，位于 0x28458），这是 DES 的有效密钥长度
3. **模式**: 可能是 ECB 模式（未发现 IV 相关数据，且 DES ECB 是最简单的模式）
4. **程序流程**:
   - 输出 "give me a string to encrypt:"
   - 读取用户输入（scanf）
   - 用 DES 加密用户输入（密钥 = "TakeEasy"）
   - 比较加密结果
   - 匹配则输出 "G00d Job!!"，不匹配则输出 "Wrong!!"
   - 最后调用 system("pause")
5. **验证方式**: 程序将用户输入加密后与某个预存的密文比较
6. **无外部加密库**: 仅依赖 KERNEL32.dll，DES 完全内联实现
7. **编译信息**: MSVC Debug 版本，源文件名 `desenc`（DES encryption 的缩写）

## 7. 能否纯静态写出 solver 的判断

### 判断：**可以纯静态解题，但需要反汇编 .text 段来提取比较用的密文。**

### 理由：

**已知的：**
- DES 算法是标准实现（所有查找表已确认）
- 密钥是 `TakeEasy`（8字节，硬编码在 .rdata 中）
- 程序逻辑清晰：加密 -> 比较 -> 输出结果

**缺失的：**
- **预存的密文（ciphertext）**：程序将用户输入 DES 加密后与某个预期密文比较。这个预期密文存储在 .text 段的代码中（可能是立即数或对 .rdata/.data 段数据的引用）。从纯字符串分析无法直接看到这个密文，因为它是二进制数据（8字节 DES 密文块）。

**解题路径：**
1. **路径 A（需要反汇编）**: 反汇编入口点 0x23A0 或 main 函数，找到 DES 加密后的比较指令（可能是 `memcmp` 或逐字节 `cmp`），提取目标密文。然后用 Python 的 `pycryptodome` 库用 `DES.new(b"TakeEasy", DES.MODE_ECB)` 解密即可得到 flag。

2. **路径 B（暴力搜索）**: 如果明文是常见 flag 格式（如 `flag{...}`），可以遍历 .text 段中所有 8 字节对齐的数据块，尝试用 `TakeEasy` 作为密钥 DES-ECB 解密，看哪个解密结果是可读的 flag 格式字符串。

3. **路径 C（动态执行）**: 直接运行程序，输入已知字符串，观察输出；或用调试器在比较点下断点获取密文。

### 推荐的纯静态 solver 策略：

由于我们已经知道密钥和算法，最可行的纯静态方法是**路径 B**：扫描整个二进制文件中所有 8 字节序列，用 DES-ECB + 密钥 "TakeEasy" 解密，筛选出符合 flag 格式的结果。这不需要反汇编。

### 风险评估：
- 密钥 "TakeEasy" 的确定性：**高**（紧邻 "give me a string to encrypt:" 和 "cmd.exe" 等程序逻辑字符串）
- DES ECB 模式的确定性：**中高**（无 IV 发现，ECB 是最简单的模式）
- 纯静态可解性：**中**（需要暴力扫描密文位置，或做轻量反汇编）
