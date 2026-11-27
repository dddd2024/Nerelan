# Microsoft MarkItDown 深度研究 — Nerelan 不可信文档、多模态上下文与插件执行边界

> [研究 Issue #1679](https://github.com/dddd2024/Nerelan/issues/1679) · 2026-11-17 · R1 docs-only · pinned upstream ed178952a6672abdfd35b5f9e76a80b6cefc086e

# Microsoft MarkItDown: fixed-source deep audit of untrusted document ingestion, converter plugins and MCP boundary

**Research date** 2026-11-17 · **Class** R1 / docs-only · **Authority** NONE · **Actual tests** NOT RUN
**Upstream** [microsoft/markitdown@ed178952a6672abdfd35b5f9e76a80b6cefc086e](https://github.com/microsoft/markitdown/commit/ed178952a6672abdfd35b5f9e76a80b6cefc086e) (package version 0.1.9 in src/markitdown/__about__.py; fixed main snapshot, not claimed a release)
**Nerelan** [main@6625c3a01c059cffd9f05762df0f67780994b238](https://github.com/dddd2024/Nerelan/commit/6625c3a01c059cffd9f05762df0f67780994b238) · Governance v2.1

## 0. Explicit dedup before study
- [Research hub #1576](https://github.com/dddd2024/Nerelan/issues/1576) carried **40 existing archive comments** at start of this round. GitHub Issues/PR/code queries for MarkItDown and microsoft/markitdown returned **no standalone pinned-source study**.
- Existing Activepieces #1668 and official MCP Registry #1674 focused on connector catalog, PyRIT #1670 on red-teaming, Phoenix #1672 on traces. This is ONE distinct upstream, focusing input conversion + source provenance + plugin load + safe preprocessing.
- The underlying Nerelan owners remain #287 (multimodal intake), #253 (Pack), #303 (workspace trust), #299 (sandbox), #447 (MCP/tool egress), #790 (official MCP runtime), #296 (context efficiency). **Do not create new implementation Issue.**

## 1. Exact source and module findings

| Source | What code really does | Disposition for Nerelan |
|---|---|---|
| [README Security Considerations](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/README.md#L459-L470) | Author explicitly warns all I/O uses current process privileges; generic convert is intentionally permissive; recommend narrow convert method and input sanitization; some OCR/LLM/cloud features can send data remotely | **BORROW_PATTERN P0**: separate trusted ingestion gate from untrusted converter worker; reject same-Host unrestricted file/URL conversion |
| [Core converter API](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_base_converter.py#L5-L105) | DocumentConverter accepts(file_stream, StreamInfo) and convert() returns DocumentConverterResult(markdown, optional title); actual result is flat Markdown and title, NOT source-anchored per-paragraph/per-page proof | **DIRECT_REUSE_CANDIDATE P1**: optional mature converter package inside sandbox after tests; add Nerelan-owned source-span, page/sheet/slide identity and evidence digest wrapper |
| [StreamInfo](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_stream_info.py#L5-L32), [type guesses](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L751-L851) | Frozen optional mimetype/extension/charset/filename/url/local_path; Magika content detection and MIME/extension heuristics; stream position restored between guesses | **BORROW_PATTERN P0**: explainable candidate format and unsupported-format error; MIME/path are input hints, not trust or permission |
| [Priority routing](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L188-L255), [conversion](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L616-L750) | Specific converter priority 0, generic HTML/plain/zip priority 10; stable priority selection; accumulated converter errors allow fallback; normalizes whitespace | **BORROW_PATTERN P1**: deterministic format fallback and explicit malformed/missing dependency status; avoid losing extraction failure evidence when fallback is misleading |
| [Opt-in plugin loader](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L113-L130), [enable_plugins](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L316-L335) | Uses Python entry_points(group="markitdown.plugin") and entry_point.load(), plugin.register_converters(); default enable_plugins false. Catches exceptions but emits full traceback warning | **BORROW_PATTERN P1**: opt-in with versioned converter registry. **REJECT direct load** in trusted Host: Entry Point import executes arbitrary installed Python code, traceback can expose sensitive data; only in isolated worker with exact package digest |
| [URI I/O](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L336-L417), [convert_uri and network](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L481-L615) | Accepts local, file:, data:, http:, https:; file: calls unrestricted convert_local/open; HTTP requests.Session.get(uri,stream=True) without explicit timeout, default redirect handling; entire response iter_content copied into BytesIO, no size cap in this implementation | **REJECT** exposing direct URI API to Agent. Host must stage authorized file bytes or prefetch from allowlisted URLs with pinned redirects, SSRF/DNS checks, time/byte quotas and no secrets |
| [Stream buffering](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L419-L460) | Non-seekable stream copied completely to BytesIO; direct network conversion also fully buffers | **BORROW_PATTERN** byte-stream API only after upper-bound enforcement; **REJECT** default unbounded behavior |
| [ZIP recursive conversion](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_zip_converter.py#L87-L130) | Iterates every archive member, reads entire member to memory via ZipFile.read, recursively calls MarkItDown.convert_stream; unsupported and failed submembers silently skipped | **REJECT for untrusted ZIP** until sandbox max depth, total decompressed bytes, entries, CPU/time and output-token limits; report dropped members and extraction provenance |
| [PDF](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_pdf_converter.py#L495-L589) | Supports text/table extraction via pdfplumber with fallback to pdfminer, copying PDF bytes into BytesIO; useful but page position, OCR coverage and table accuracy should be independently measured | **DIRECT_REUSE_CANDIDATE P1**, not proof-grade citation engine; maintain per-page source reference, fail explicit when scanned/text absent |
| [MCP server](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown-mcp/src/markitdown_mcp/__main__.py#L15-L48), [HTTP](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown-mcp/src/markitdown_mcp/__main__.py#L82-L135) | Tool accepts file/http/https/data URI; default 127.0.0.1, exposes unauthenticated server over nonlocal bind with warning; explicitly says runs with user's privileges and can read files/fetch network; user-facing error messages avoid leaking resolved path/HTTP internal URL | **REJECT default direct MCP server** in Nerelan Host. If ever used, run separate confined subprocess behind #790 with exact allowlist; client-facing error sanitization pattern is good |
| [Image LLM description](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_image_converter.py#L69-L137), [OCR plugin](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown-ocr/src/markitdown_ocr/_plugin.py#L10-L66) | Image model call only if llm_client and llm_model supplied; OCR plugin replaces converters by priority and uses LLM vision; README says no LLM client -> OCR skipped | **DEFER model-assisted ingest** until Magpie metered, explicit Owner data-sharing/grant, offline fallback and measured necessity; never default bill in preprocessing |
| [Audio/transcription](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_audio_converter.py#L23-L102), [external ExifTool](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_exiftool.py#L10-L57) | SpeechRecognition optional; ExifTool executable from explicit/env/well-known path may spawn subprocess for metadata | **DEFER**, treat external binaries and transcription outbound access as additional sandbox/credential boundaries |
| [License / optional dependencies](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/LICENSE), [packaging](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/pyproject.toml) | MIT root/main package, Python >=3.10,<3.15, optional per-format dependencies and 3rd-party plugins; optional [all] adds more surface. Dependents' own licenses must be reviewed | **DIRECT_REUSE_CANDIDATE** for narrow selected converters only; no need to clone whole CLI/MCP/ExIF/OCR suite into Host |

## 2. Comparison with actual Nerelan main
- [context_builder.py](https://github.com/dddd2024/Nerelan/blob/6625c3a01c059cffd9f05762df0f67780994b238/reverse_agent/platform_v1/context_builder.py): deterministic TaskStore+Git metadata context packet, **authority=NONE**, deliberately never reads working tree file contents or evidence files in this process. Don't use MarkItDown to smuggle raw document reading into context_builder; add an upstream separate Owner-gated ingestion stage.
- [capability_registry.py](https://github.com/dddd2024/Nerelan/blob/6625c3a01c059cffd9f05762df0f67780994b238/reverse_agent/platform_v1/capability_registry.py): bounded JSON Pack metadata, does not load third-party code. Keep this guarantee: converters are candidates, not imported into Host by Pack listing.
- [run_store.py](https://github.com/dddd2024/Nerelan/blob/6625c3a01c059cffd9f05762df0f67780994b238/reverse_agent/platform_v1/run_store.py): TaskStore append-only authoritative event/evidence; store digest/reference/status of ingestion as supporting evidence, NOT a new second truth.
- [goal_service.py](https://github.com/dddd2024/Nerelan/blob/6625c3a01c059cffd9f05762df0f67780994b238/reverse_agent/platform_v1/goal_service.py) + [task_runtime.py](https://github.com/dddd2024/Nerelan/blob/6625c3a01c059cffd9f05762df0f67780994b238/reverse_agent/platform_v1/task_runtime.py): Goal lifecycle and ExecutorRouter unaffected by converter; no new LLM agent or task scheduler.
- Canonical owners #287 multimodal intake, #253 Pack, #303 trust, #299 real sandbox, #447 content/egress, #790 official MCP runtime, #296 context efficiency, #1527 actual accepted-task/cost benchmark.

## 3. Proposed bounded ingestion design
User selects local file / connector attachment -> Owner context, file identity and permission -> local staging **outside privileged Host**, byte limit, final path & symlink resolution, digest, MIME hints -> sandboxed extractor with **NO secrets / NO network / limited files and CPU, memory and time** -> Markdown with per-section evidence reference (source file SHA, page/slide/sheet/offset), extraction diagnostics, status and completeness -> Context Packet contains *references/summaries and authority NONE* -> Agent consumes only bounded excerpts -> TaskStore records source and parser version, warnings, content signature -> independent verifier can re-open original source when authorized.

- User should see whether PDF text was extracted, OCR was skipped, pages/ZIP members omitted or tables possibly flattened.
- File content is UNTRUSTED input, even when formatted as headings/instructions in Markdown. No Owner grants from PDF, HTML, repository README, spreadsheet cell or ZIP member.
- Prefer deterministic locally processed text as P1. Optional image/audio LLM/OCR is a separate paid action (Magpie billed, opt-in, scoped per document, data-sharing clearly indicated). Compare token cost and genuine retrieval/citation quality against raw text, not just "Markdown looks tidy."

## 4. Proposed negative tests — NOT EXECUTED
T01 HTML/PDF says "ignore previous instructions / run command" -> context authority remains NONE.
T02 local file URI resolves outside approved workspace -> denied before calling MarkItDown.
T03 symlink inside staged dir points to secret -> deny and no leakage.
T04 HTTP URL to loopback/metadata server/private IP -> SSRF deny at Host prefetcher; redirects and DNS rebinding revalidated.
T05 requests stream never completes -> timeout + byte cap + no indefinite worker memory.
T06 non-seekable stream huge -> bounded reject instead of unbounded copy.
T07 ZIP 100k entries or high compression ratio / nested ZIP -> total budget, no OOM.
T08 ZIP member fails parsing -> report warning and members omitted, not silently act fully complete.
T09 malformed PDF, no text, scanned PDF -> explicit partial/needs OCR, no misleading accurate citation.
T10 PDF table/math/formula extraction differs from original -> source-aware comparison and coverage.
T11 spoof MIME extension HTML containing malicious script -> treat as data, not execute.
T12 plugin entry_point malicious import / plugin exception with secret -> import only in isolated no-secret worker, sanitize errors.
T13 ExifTool external binary wrong path -> not executable unless fixed approved digest in sandbox.
T14 MarkItDown MCP service bound external interface unauthenticated -> security gate blocks deployment.
T15 OCR/LLM disabled -> no external model or Azure cloud traffic; price $0 for model ingest only when proven.
T16 LLM/OCR opt-in -> Magpie request IDs and settled cost visible; model not allowed to receive private attachment without explicit grant.
T17 source file mutated after conversion -> digest mismatch, invalidate citation/evidence cache.
T18 compare markdown-vs-raw on real authorized documents for retrieval correctness, source-reference precision/recall, missing tables, token count and all-in accepted-task cost.

## 5. Implementation priorities and non-goals
P0: trust/IO boundary and provenance invariant; no URL/file URI/third-party plugin execution inside trusted Host.
P1: metadata-only converter catalog + opt-in local document/attachment ingestion in a sandbox; prompt-injection and size limits, file digest, source references and format diagnostics.
P1: user-facing completeness/partial-extraction, cited location, sensitive content policy, retry semantics.
P2: possibly reuse MIT MarkItDown core + narrow office/PDF extras within an isolated worker, only after ABI/security/perf/test license review and real accepted-task A/B.
DEFER: OCR vision/audio/cloud analyzers, new MCP server process, third-party plugin marketplace, video/complex ingestion unless user tasks demand.
ALREADY: TaskStore, GoalService, ExecutorRouter, Pack registry, ContextBuilder authority NONE; keep boundaries.
REJECT: unrestricted convert(uri) exposure, blanket [all] dependencies, trusted in-process entry points, passing any file-derived instructions as trusted Owner directives.

**Verification boundary:** static GitHub fixed-source review only. No local package install, no malicious files processed, no PDFs executed, no model or cloud calls, no CI or independent reviewer, no Nerelan runtime changes. Proposed tests have no measured results.## 6. 逐项深审：是“文件输入能力”，不是“文件读取授权”

### 6.1 选择路径最窄的纯输入函数，而非对 Agent 暴露全能 convert() / convert_uri()

MarkItDown 提供 convert、convert_local、convert_stream、convert_uri、convert_response 族函数。看似只是 API 使用便利，实际上影响安全：convert() 根据字符串自己猜这是本地路径还是 file:/http:/https:/data:；convert_uri 可打开调用进程可读的路径并使用 requests.Session 获取远端内容。这些函数**按进程权限行事**，没有 Nerelan Owner Grant、Project AllowedPath、目标域名/端口许可的概念。

对 Nerelan，可借鉴 convert_stream() 的纯已批准字节流接口，但仍必须由单独的受限 worker 执行，且先验证 staged file size/type/sha256；不能相信文件路径、Content-Type 或一个裸文件描述符就天然安全。对于不可 seek 的流，它把全量数据复制成 BytesIO，必须在 Host 控制的上游先做 byte cap。对于 HTTP 连接，Core 里的 Requests 没有显式 timeout 和 SSRF/redirect-boundary；**不要**把它改成“只允许 http(s) 就安全”，而是要先按 #447 的网络适配器规则过滤 DNS、最终 IP、重定向目标、最大响应大小和总时限，最好将文件以经批准的 ByteStream 交给转换器，彻底不让转换器联网。

### 6.2 Converter 优先级很成熟，但“成功转换”仍可能漏数据

主 [MarkItDown](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L188-L255) 注册 PlainText/HTML/ZIP 为通用优先级 10，DOCX/XLSX/PPTX/PDF 等更具体的转换器优先级 0；[注册/尝试流程](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L616-L749) 保证排序稳定、尝试每个 stream_info guess，收集 convert exception，调用成功就返回经过空白规范化的 Markdown。在工程上有三个可借鉴点：
- 只先载入当前数据类型所需的 parser，避免所有格式都会拖入庞大依赖；
- 当有 MIME、扩展名、Magika 启发式冲突时优先选择真正能处理文件字节的转换器，保存路由原因；
- 记录失败的 parser、最终选择的 parser、版本和警告，使 PDF 中的表格没解析、ZIP 某个成员没能解析都可以追查。

但 ConverterResult 实际主要有 markdown + title，没有完整的 page/slide/sheet/cell provenance，也没有每个 chunk 的原始坐标。Nerelan 不能仅靠“转换成功”就给 Agent 生成看似精确的文件引用；必须保存原文件 digest 和解析器指纹，由附加 extractor/source map 或检查器建立真实页码/工作表定位。做不到时应使用文件级引用和“无法定位具体页码”的提示，不虚构出处。

### 6.3 插件：默认关闭不代表启用之后仍然安全

MarkItDown 的插件允许 PyPI 扩展包通过 Python Entry Point 注册转换器；[源码](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L113-L130) 使用 entry_point.load() 导入 Python 模块。导入和 register_converters() 都是执行任意 Python 代码，不是“只读读取插件清单”。[enable_plugins](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L316-L334) 捕获异常并打印 traceback，虽有利于调试，若插件异常内容包含路径、隐私文本或凭据，就可能泄漏日志。示例 plugin 有 __plugin_interface_version__=1，但本轮**没有证明主入口依据此字段强制拒绝版本不兼容插件**，因此不能宣称存在强版本沙箱。

Nerelan 的正确拆分是：CapabilityRegistry 只声明 MIME 支持、包来源、版本、摘要、风险标签；真实加载发生在 #299/#303 审核后的独立 worker，与 Magpie 密钥、Owner Secret Broker、TaskStore SQL 连接物理隔离。插件 import 失败需返回固定错误种类和去敏诊断，不要将 Python traceback 原文注入 Agent 上下文。

### 6.4 ZIP 和 PDF 是本轮最需要负面测试的文件格式

[ZipConverter](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_zip_converter.py#L87-L130) 遍历 ZIP 内全部成员并对每个成员调用 zipObj.read(entry)，再递归交给父 MarkItDown。该具体实现中没有显式总体 entry count、解压后总 bytes、嵌套深度或 tokens 上限；遇到 UnsupportedFormatException 和 FileConversionException 直接忽略，最后能正常返回一个看似完整的 Markdown。它没有 extractall() 的写盘路径穿越问题，但有内存、CPU 和静默丢失成员问题；不能声称证明了 ZIP 炸弹可真实攻击成功，因为本轮没有运行样本。

[PdfConverter](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_pdf_converter.py#L495-L589) 通过 pdfplumber 处理表格和表单风格内容，失败后尝试 pdfminer，可用于典型文本 PDF。但同样以 BytesIO 复制全文，扫描 PDF 没有完整 OCR 时可能只返回少量文本或空文本，表格/数学排版/图形信息也可能不忠实。对 Nerelan 要实测任务级结论和原文件证据，而不是只评估 Markdown 是否视觉上“顺眼”。

### 6.5 MCP Server 是很好的格式兼容样例，但其默认授权不能沿用

[markitdown-mcp](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown-mcp/src/markitdown_mcp/__main__.py#L19-L48) 的 convert_to_markdown 工具参数只有一个 URI；它创建 MarkItDown 并直接调用 convert_uri。这让 LLM 只要构造 file:// 路径或不安全 URL，就可能让同进程读取原本 LLM 无法直接访问的资源。其 HTTP 模式默认绑定 127.0.0.1，但有 --host 非本地地址时只有警告，源码自承没有 Authentication 且以当前用户权限访问文件和网络。因为标准 MCP 协议并不提供本机文件权限沙箱，所以这是典型的“协议合法，不等于执行安全”。

可借鉴的是它对 HTTPError、requests 网络异常和 OSError 的稳定 ToolError 分类，例如避免把内部 URL 或 resolved path 放到返回给模型的错误字符串。对 Nerelan 需修改为：MCP Tool 的输入只接受由 Host 生成的 approved_attachment_handle 或具体已批准 ByteStream，接口完全不提供裸 file/http URI。即便未来想兼容它的原生接口，也必须在隔离的代理层实现 allowlist、connection and timing policy，而不能只依赖 Prompt 写“不要读秘密”。

### 6.6 内置 AI/云能力并非一律“免费文本提取”

[ImageConverter](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/converters/_image_converter.py#L69-L137) 仅在 llm_client 与 llm_model 都有设置时调用 chat.completions，把图片 base64 提交给模型；[MarkItDown constructor](https://github.com/microsoft/markitdown/blob/ed178952a6672abdfd35b5f9e76a80b6cefc086e/packages/markitdown/src/markitdown/_markitdown.py#L188-L310) 也可配置 Azure Document Intelligence / Content Understanding endpoint。README 还明确 markitdown-ocr 使用 LLM Vision 和额外付费高精度功能。

这意味着 Nerelan 的模型成本优化目标要求将以下两条路径隔离：
- Deterministic conversion：用户授权后在本地离线沙箱里提取文本/基本文档结构；只计算必要的 CPU/内存开销；
- Enriched conversion：确有必要才能发起视觉 OCR/云布局分析/音频转录，不是透明的 preprocessing；必须展示外发数据类别、Owner 授权范围、Magpie 模型绑定、请求 ID 与全部实际费用。

如果某些图像/表格在没有 OCR 的情况下无法提取，应报告 PARTIAL 或 OCR_REQUIRED，不能悄悄把缺失部分当作已经被 Agent 理解。

### 6.7 跟当前 Nerelan ContextBuilder 和长期自动任务如何结合

Nerelan 的 ContextBuilder 设计明确为 **TaskStore+Git 只读元数据重建**，不会直接加载证据文件或当前工作树内容，而且 authority 恒为 NONE。把任意 PDF/HTML/文件夹解析并写进 ContextBuilder 会打破现有的高可靠性与安全边界，也可能使长期任务恢复过程变成不可控的网络文件解析。

推荐上游数据流：
1. User / existing approved Connector 上传附件或者指定项目只读文件；
2. Trusted Host 创建 InputRequest 并检查作用域/Owner grant，给 worker 一个已批准 staging handle；
3. Worker 在无账户 Secret、只读文件范围、无网络、限额内运行解析，输出带 source_digest + converter_version + warning + content_digest 的 Markdown；
4. Host 将其作为 SupportingArtifact（非权限数据）记录在 TaskStore，并提供按需只读片段引用；
5. Agent 只看到必要 chunk 和原文件定位，模型输出不能反向将文件内容提升为 Owner 指令；
6. 独立 verifier 核对原文/解析输出/引用，完成任务验收时不要把模型自己生成的 Markdown 认作事实依据。

对用户体验则必须提供“已提取多少页/工作表/ZIP 成员”、“可能丢失了什么”、“是否经过模型或远端服务”“耗费了什么成本”，而不是只有一个“转换成功”。

## 7. 和此前研究不同的贡献与实施归属

| 已有专项 | 已覆盖内容 | MarkItDown 的真实增量 |
|---|---|---|
| Activepieces #1668 | SaaS Action/Trigger 的工具发现、授权和缓存 | 文件格式 Converter 抽象、MIME 猜测、嵌套 ZIP 解析与原文定位 |
| MCP Registry #1674 | 插件目录和包/来源准入 | MCP Tool 内部的文件与 URL 读取是真实副作用：协议可调用不代表可授权 |
| MCP Python SDK #1653 | 标准 MCP 协议安全与降级 | markitdown-mcp 应用层的 URI 范围和错误消息泄漏风险 |
| PyRIT #1670 | Prompt Injection 的负面实验/评分 | PDF/HTML/ZIP 作为恶意文本输入的具体入口和丢失来源证据风险 |
| Phoenix #1672 | Trace/Result 评分关系 | Markdown 文档 source map 和文档转换质量/花费的独立测量 |

实施 owner 仍为 #287 用户输入、#253 Pack、#303 本机信任、#299 Sandbox、#447 输出/egress、#790 MCP 和 #296 Context Efficiency。研究没有执行权限，也不应开启新的独立运行时 Issue。

## 8. Phase gates 和验收

**M0：Provider-free 受控 fixtures**：用本地生成的 TXT/HTML/PDF/DOCX/XLSX/ZIP，包含已知答案、页/表/元数据和不可信注入文本。冻结样本及预期位置，使用假敏感字段。先核实稳定错误码、容量限制和没有任何 secret/network egress，再验证提取完整度。

**M1：Nerelan 内的只读输入流水线**：保持 ContextBuilder 非文件解析器；由独立已批准 worker 返回源哈希/转换器哈希/位置/警告，TaskStore 存最小摘要和 evidence references，失败重试不重复生成不可信执行权限。

**M2：真实 Agent×Model 比较**：在已授权任务内检验文档转 Markdown 是否改善具体任务的回答正确性、引用定位准确率、工作表/表格漏失率、token 用量、端到端延迟和实际 Magpie 总成本，并单独显示“不支持/部分提取”比例。

**M3：可选扩展**：只有真实需要并证明收益时，才评估 OCR/云文档分析和额外第三方转换插件，固定具体包、依赖、license、数据外发权限、运行时版本和 provider 结算。MCP 接口仍归官方 SDK/Owner #790 管理。

## 9. 审计边界

本轮使用 GitHub 固定 commit 静态阅读 MarkItDown README/License、包版本、Core StreamInfo/Converter/MarkItDown、PDF/ZIP/HTML/IMG/Audio/ExifTool 解析器、样本插件与 OCR 插件、MCP server 和其错误处理测试文件；Nerelan main AGENTS、ContextBuilder、CapabilityRegistry、GoalService、TaskStore、ExecutorRouter 和现有 owner issues。**没有安装 MarkItDown 或 Python 额外依赖，没有运行转换器、执行实际 ZIP/PDF、安全攻击、测试套件、MCP Server、文件读取实验、外网请求、模型/OCR 或 Magpie 账单；未执行 CI/独立审查。**

**最终：BORROW_PATTERN（类型化转换接口、优先级和错误分级）、DIRECT_REUSE_CANDIDATE（MIT 的窄范围 PDF/Office/TXT Worker）、ALREADY_IMPLEMENTED（Host/TaskStore/Context trust）、REJECT（原生无限制 URI/MCP/插件在 Host 执行）、DEFER（高成本 OCR、视频/音频/云和插件市场）。**
