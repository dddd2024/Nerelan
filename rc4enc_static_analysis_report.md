# rc4enc_3480917d / sample.exe 纯静态分析报告

## 1. 基本信息

| 项目 | 值 |
|------|-----|
| 文件路径 | `F:\reverse-agent\local_reverse_samples\rc4enc_3480917d\sample.exe` |
| 文件大小 | 196,693 bytes |
| SHA256 | `3480917ddedce512f76e97c26df3b3ad12b71b34db472fa8836ba67528bcb09f` |
| 编译器 | Microsoft Visual C++ (Debug build, MSVC 6.0 era) |
| PDB路径 | `C:\Documents and Settings\Administrator\\2019\3\Debug\rc4enc.pdb` |
| ImageBase | 0x00400000 |
| 入口点RVA | 0x1800 |

## 2. PE Sections

| Section | VA | VSize | RawOffset | RawSize |
|---------|-----|-------|-----------|---------|
| .text | 0x1000 | 0x25D70 | 0x1000 | 0x26000 |
| .rdata | 0x27000 | 0x1673 | 0x27000 | 0x2000 |
| .data | 0x29000 | 0x5CBC | 0x29000 | 0x4000 |
| .idata | 0x2F000 | 0x851 | 0x2D000 | 0x1000 |
| .reloc | 0x30000 | 0x10E1 | 0x2E000 | 0x2000 |

## 3. 关键字符串 (ASCII)

### 3.1 程序逻辑相关字符串

| 偏移 | 字符串 |
|------|--------|
| 0x02701C | `WoW!!!Great!!!You are a genius!!!` |
| 0x027044 | `pause` |
| 0x02704C | `Sorry you are wrong!` |
| 0x02706C | `please input a correct string to encrypt:` |
| 0x0270A0 | `cmd.exe` |
| 0x0270A8 | `command.com` |
| 0x0270DC | `COMSPEC` |
| 0x027218 | `PATH` |
| 0x027388 | `user32.dll` |
| 0x027394 | `Microsoft Visual C++ Debug Library` |
| 0x028034 | `MessageBoxA` |
| 0x029A30 | `WORKER` (.data段) |

### 3.2 CRT/运行时字符串（非关键，大量assertion和debug信息）

包含 `_CrtCheckMemory`, `_CrtIsValidHeapPointer`, `Assertion Failed`, `Runtime Error!`, `Detected memory leaks!` 等标准MSVC Debug运行时字符串。

### 3.3 UTF-16LE 字符串

仅发现43条，全部为 `jjjj` 或 `Bjjjj` 等无意义模式（x87 FPU指令的编码伪影），以及 `(null)` 和一些对齐填充。**无有意义的Unicode字符串。**

## 4. 关键词搜索结果

| 关键词 | 匹配字符串 | 说明 |
|--------|-----------|------|
| **flag** | `flag == 0 \|\| flag == 1` (0x027528) | CRT断言中的flag参数，非CTF flag |
| **correct** | `please input a correct string to encrypt:` | 输入提示 |
| **wrong** | `Sorry you are wrong!` | 错误提示 |
| **please** | `please input a correct string to encrypt:` | 输入提示 |
| **input** | `please input a correct string to encrypt:` | 输入提示 |
| **encrypt** | `please input a correct string to encrypt:` | 加密提示 |
| **Crypt** | (子串匹配) | 在 "please input a correct string to **encrypt**" 中 |
| **RC4** | `\2019\3\Debug\rc4enc.pdb` | PDB路径中的文件名 |
| **fail** | 多条CRT assertion信息 | 非关键 |
| **exception** | `UnhandledExceptionFilter` | PE导入函数名 |
| **handler** | `SetConsoleCtrlHandler` | PE导入函数名 |
| **DES/Base64/hash/XOR/rotate/SEH/Advapi** | **无匹配** | 未发现这些密码学关键词 |

**重要发现：** 没有发现 CryptAPI / advapi32.dll 导入。RC4是**纯软件自行实现**的，没有调用Windows加密API。

## 5. PE Imports

### 唯一导入的DLL: KERNEL32.dll

共导入 **59个函数**，全部为标准系统API：

**进程/内存管理：**
- ExitProcess, TerminateProcess, GetCurrentProcess, GetExitCodeProcess
- HeapCreate, HeapDestroy, HeapAlloc, HeapFree, HeapReAlloc, HeapValidate
- VirtualAlloc, VirtualFree

**文件I/O：**
- ReadFile, WriteFile, CreateProcessA, GetFileAttributesA
- SetFilePointer, FlushFileBuffers, GetFileType, CloseHandle

**控制台：**
- GetStdHandle, SetStdHandle, WriteFile, SetConsoleCtrlHandler

**模块/环境：**
- GetModuleHandleA, GetModuleFileNameA, LoadLibraryA, GetProcAddress
- GetCommandLineA, GetEnvironmentStringsA/W, GetEnvironmentVariableA
- GetVersion, GetVersionExA, GetStartupInfoA

**字符串/编码：**
- MultiByteToWideChar, WideCharToMultiByte
- CompareStringA/W, GetStringTypeA/W, LCMapStringA/W
- lstrcat, lstrcmp (通过GetProcAddress延迟加载)

**异常处理：**
- UnhandledExceptionFilter, RtlUnwind

**注意：没有 msvcrt.dll 的显式导入** -- C运行时函数（printf, scanf, strlen, puts, system等）通过静态链接（MSVC Debug CRT）内嵌在.text段中。

## 6. 硬编码常量分析

### 6.1 .data 段关键数据

| 偏移 | 大小 | 内容 | 用途 |
|------|------|------|------|
| 0x29A30 | 6 bytes | `WORKER` (57 4F 52 4B 45 52) | RC4密钥源字符串 |
| 0x29B30 | 8 bytes | `d5 23 a5 22 75 d8 b7 80` | **加密后的密文（目标比较值）** |
| 0x42D23C | 4 bytes | 全局变量 i (RC4状态索引1) | 运行时状态 |
| 0x42D240 | 4 bytes | 全局变量 j (RC4状态索引2) | 运行时状态 |
| 0x42CE3C | 256 bytes | RC4 S-box (初始全0，运行时初始化) | RC4状态数组 |

### 6.2 .rdata 段关键数据

| 偏移 | 内容 | 用途 |
|------|------|------|
| 0x02701C | `WoW!!!Great!!!You are a genius!!!` | 成功提示 |
| 0x02704C | `Sorry you are wrong!` | 失败提示 |
| 0x02706C | `please input a correct string to encrypt:` | 输入提示 |
| 0x027044 | `pause` | system("pause") 参数 |
| 0x027068 | `%s` | scanf/printf 格式串 |

## 7. 程序逻辑逆向分析

### 7.1 函数调用图

```
main (0x1030)
  |-- printf("please input a correct string to encrypt:")
  |-- scanf("%s", input_buf)          // 读取用户输入
  |-- strlen(input_buf)                // 获取输入长度
  |-- encrypt(input_buf, output_buf)   // 0x1410: RC4加密
  |     |-- strlen(input)
  |     |-- init_rc4()                 // 0x1014->0x1190: RC4 KSA初始化
  |     |     |-- printf("WORKER")     // 打印标签
  |     |     |-- loop1: S[i]=(S[i]+2)&0xFF for i=0..5  // 变换S-box
  |     |     |-- loop2: S[i]=S[i]%256 for i=0..0xFF     // 归一化
  |     |     |-- loop3: RC4 KSA with key="WORKER"       // 标准KSA
  |     |-- loop: RC4 PRGA 加密每个字节
  |-- compare loop: output_buf[i] == target[i] for i=0..len
  |     |-- if match: puts("WoW!!!Great!!!You are a genius!!!")
  |     |-- if mismatch: puts("Sorry you are wrong!")
  |-- system("pause")
```

### 7.2 加密算法详解

**Step 1: RC4 初始化 (函数 0x1190)**

1. S-box 数组 `S[256]` 初始化为 0xCC 填充
2. 打印 "WORKER" 标签
3. **Loop 1:** 对 S[0..5]（前6个字节），每个字节 +2：
   - `S[i] = (S[i] + 2) & 0xFF`
   - 初始 S[0..5] = {0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0xCC}
   - 变换后 S[0..5] = {0xCE, 0xCE, 0xCE, 0xCE, 0xCE, 0xCE}
4. **Loop 2:** 对 S[0..255]，每个字节做模256归一化（实际无变化，因为已经是单字节）
5. **Loop 3:** 标准 RC4 KSA，使用密钥 "WORKER" (6字节: 0x57, 0x4F, 0x52, 0x4B, 0x45, 0x52)
   - `j = 0; for i=0..255: j = (j + S[i] + key[i % 6]) & 0xFF; swap(S[i], S[j])`

**Step 2: RC4 加密 (函数 0x1410)**

对输入的每个字节执行标准 RC4 PRGA：
```
i = (i + 1) & 0xFF
j = (j + S[i]) & 0xFF
swap(S[i], S[j])
output[k] = input[k] ^ S[(S[i] + S[j]) & 0xFF]
```

**Step 3: 比较**

将加密结果与 .data 段中的目标密文逐字节比较：
- 目标密文: `d5 23 a5 22 75 d8 b7 80` (8字节, 位于 0x29B30)
- 比较长度 = strlen(用户输入)

### 7.3 关键观察

- RC4 密钥是硬编码的字符串 "WORKER"
- S-box 初始化有一个**非标准的预处理步骤**（前6字节 +2）
- 目标密文只有8字节，说明正确输入长度为8个字符
- 由于 RC4 是对称加密，加密和解密使用相同操作
- 因此：`RC4_decrypt(target_ciphertext) = original_input`

## 8. 能否纯静态写出 solver

### 判断：**可以**

### 理由：

1. **所有关键参数均为硬编码常量：**
   - RC4 密钥: `"WORKER"` (已知)
   - S-box 预处理: 前6字节 +2 (已知)
   - 目标密文: `d5 23 a5 22 75 d8 b7 80` (已知，从 .data 段提取)
   - 输入长度: 8 字节 (由密文长度推断)

2. **算法完全确定：**
   - RC4 是标准对称流密码
   - KSA 和 PRGA 的实现细节已从静态分析中完全还原
   - 唯一的非标准点是 S-box 预处理（+2），已确认

3. **无需运行时信息：**
   - 没有使用外部API获取密钥或配置
   - 没有基于时间的随机性
   - 没有反调试/反分析技巧（仅标准Debug CRT检查）
   - 没有导入 CryptAPI

4. **Solver 算法：**
   ```
   1. 初始化 S[256] = 全0xCC
   2. S[0..5] += 2  (变为 0xCE)
   3. 用密钥 "WORKER" 执行 RC4 KSA
   4. 用同一 RC4 状态对密文 d523a52275d8b780 执行 PRGA
   5. 输出即为 flag
   ```

## 9. 附录：关键代码位置

| 描述 | 文件偏移 | 代码VA |
|------|---------|--------|
| main函数 | 0x1030 | 0x401030 |
| RC4 KSA初始化 | 0x1190 | 0x401190 |
| RC4加密函数 | 0x1410 | 0x401410 |
| RC4 PRGA生成器 | 0x1300 | 0x401300 |
| S-box数组 | 0x42CE3C | 0x42CE3C |
| 密钥"WORKER" | 0x29A30 | 0x429A30 |
| 目标密文 | 0x29B30 | 0x429B30 |
| 全局i索引 | 0x42D23C | 0x42D23C |
| 全局j索引 | 0x42D240 | 0x42D240 |
