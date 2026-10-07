// Trusted native process only. Renderer requests never contain the capability.
import http from 'node:http';
import { pathToFileURL } from 'node:url';

const HEADER = 'X-Nerelan-Client-Capability';
const REQUEST_LIMIT = 256 * 1024;
const RESPONSE_LIMIT = 8 * 1024 * 1024;

function base(value) {
  let url;
  try { url = new URL(value); } catch { throw new Error('client_configuration_invalid'); }
  if (url.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(url.hostname)
      || !url.port || url.username || url.password || url.search || url.hash
      || url.pathname !== '/') throw new Error('client_configuration_invalid');
  return url.origin;
}

export function validateConfiguration(input) {
  if (!input || typeof input !== 'object'
      || typeof input.capability !== 'string' || !/^[a-f0-9]{64}$/.test(input.capability)) {
    throw new Error('client_configuration_invalid');
  }
  const frontend = base(input.frontend_url);
  const api = base(input.task_api_url);
  if (frontend === api) throw new Error('client_configuration_invalid');
  return Object.freeze({ frontend, api, capability: input.capability });
}

export async function forwardTaskRequest(request, config, { timeout = 10000 } = {}) {
  let url, frame;
  try { url = new URL(request.url); frame = new URL(request.frameUrl); }
  catch { throw new Error('client_request_denied'); }
  if (url.origin !== config.api || frame.origin !== config.frontend
      || url.username || url.password || url.hash || !url.pathname.startsWith('/api/')
      || !['GET', 'POST', 'OPTIONS'].includes(request.method)) throw new Error('client_request_denied');
  const body = request.body == null ? Buffer.alloc(0) : Buffer.from(request.body);
  if (body.length > REQUEST_LIMIT) throw new Error('client_request_too_large');
  const type = request.headers?.['content-type'] ?? request.headers?.['Content-Type'];
  if (type != null && (typeof type !== 'string' || type.length > 256 || /[\r\n]/.test(type))) {
    throw new Error('client_request_denied');
  }
  const headers = { Origin: config.frontend, Accept: 'application/json', [HEADER]: config.capability };
  if (type != null) headers['Content-Type'] = type;
  if (body.length) headers['Content-Length'] = String(body.length);
  return new Promise((resolve, reject) => {
    const fail = (code) => reject(new Error(code));
    // Native HTTP does not follow redirects or use proxy environment settings.
    // Pin transport to literal loopback, even for a configured localhost alias.
    const outgoing = http.request({
      hostname: '127.0.0.1', port: Number(url.port), path: url.pathname + url.search,
      method: request.method, headers,
    }, (incoming) => {
      if (incoming.statusCode >= 300 && incoming.statusCode < 400) {
        incoming.destroy(); outgoing.destroy(); fail('client_redirect_denied'); return;
      }
      const chunks = []; let size = 0;
      incoming.on('data', (chunk) => {
        size += chunk.length;
        if (size > RESPONSE_LIMIT) { incoming.destroy(); outgoing.destroy(); fail('client_response_too_large'); }
        else chunks.push(chunk);
      });
      incoming.on('error', () => fail('client_transport_failed'));
      incoming.on('end', () => {
        const result = Buffer.concat(chunks);
        if (result.includes(Buffer.from(config.capability))) { fail('client_sensitive_response_denied'); return; }
        const responseHeaders = {};
        for (const key of ['content-type', 'cache-control', 'content-disposition',
          'access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers', 'vary']) {
          const value = incoming.headers[key];
          if (value != null) {
            const text = Array.isArray(value) ? value.join(', ') : value;
            if (text.includes(config.capability)) { fail('client_sensitive_response_denied'); return; }
            responseHeaders[key] = text;
          }
        }
        resolve({ status: incoming.statusCode, headers: responseHeaders, body: result });
      });
    });
    outgoing.setTimeout(timeout, () => { outgoing.destroy(); fail('client_transport_timeout'); });
    outgoing.on('error', () => fail('client_transport_failed'));
    outgoing.end(body);
  });
}

export async function handleRoute(route, config) {
  try {
    const request = route.request();
    const response = await forwardTaskRequest({
      url: request.url(), method: request.method(), headers: request.headers(),
      body: request.postDataBuffer(), frameUrl: request.frame().url(),
    }, config);
    await route.fulfill(response);
  } catch {
    await route.fulfill({
      status: 502, contentType: 'application/json',
      headers: { 'Access-Control-Allow-Origin': config.frontend, 'Cache-Control': 'no-store' },
      body: JSON.stringify({ error: '本地客户端连接失败，请通过启动器重新打开。', code: 'trusted_client_transport_failed' }),
    });
  }
}

export function privateConfiguration(stream) {
  return new Promise((resolve, reject) => {
    let buffered = ''; let settled = false;
    stream.setEncoding('utf8');
    const cleanup = () => { stream.off('data', receive); stream.off('end', ended); stream.off('error', ended); };
    const ended = () => { if (!settled) { settled = true; cleanup(); reject(new Error('client_bootstrap_failed')); } };
    const receive = (chunk) => {
      buffered += chunk;
      if (Buffer.byteLength(buffered) > 8192) { ended(); return; }
      const newline = buffered.indexOf('\n');
      if (newline < 0) return;
      settled = true; cleanup();
      try { resolve(validateConfiguration(JSON.parse(buffered.slice(0, newline)))); }
      catch { reject(new Error('client_bootstrap_failed')); }
    };
    stream.on('data', receive); stream.once('end', ended); stream.once('error', ended);
  });
}

async function waitFrontend(origin) {
  const until = Date.now() + 30000;
  while (Date.now() < until) {
    const ready = await new Promise((resolve) => {
      const url = new URL(origin);
      const request = http.get({ hostname: '127.0.0.1', port: Number(url.port), path: '/', timeout: 1000 }, (response) => {
        response.resume(); resolve(response.statusCode === 200);
      });
      request.on('timeout', () => { request.destroy(); resolve(false); });
      request.on('error', () => resolve(false));
    });
    if (ready) return;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error('client_frontend_unavailable');
}

async function runClient() {
  let browser;
  let stopped = process.stdin.readableEnded;
  const stopping = new Promise((resolve) => {
    const stop = () => { stopped = true; resolve(); };
    process.stdin.once('end', stop);
    process.once('SIGTERM', stop);
    process.once('SIGINT', stop);
  });
  try {
    const config = await privateConfiguration(process.stdin);
    await waitFrontend(config.frontend);
    if (stopped) return;
    const { chromium } = await import('playwright-core');
    browser = await chromium.launch({ headless: false, ...(process.platform === 'win32' ? { channel: 'msedge' } : {}) });
    if (stopped) return;
    const context = await browser.newContext({ serviceWorkers: 'block' });
    await context.route((url) => url.origin === config.api, (route) => handleRoute(route, config));
    const page = await context.newPage();
    // Closing the supported frontend page can leave Chromium connected with no
    // windows. That page's lifetime, not only the browser connection, bounds
    // this private client session. Observe it before navigation can close it.
    const pageClosed = new Promise((resolve) => page.once('close', resolve));
    await page.goto(config.frontend);
    process.stdout.write(JSON.stringify({ state: 'ready', pid: process.pid }) + '\n');
    await Promise.race([stopping, pageClosed, new Promise((resolve) => browser.once('disconnected', resolve))]);
  } catch {
    // Fixed diagnostics only; never dump private configuration or library errors.
    process.stderr.write('trusted_client_unavailable\n');
    process.exitCode = 1;
  } finally {
    try {
      if (browser) await browser.close().catch(() => {});
    } finally {
      // The host intentionally keeps this private pipe open during a session.
      // On terminal failure/disconnect it must no longer keep Node alive.
      process.stdin.destroy();
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await runClient();
