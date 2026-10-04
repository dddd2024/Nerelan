import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { PassThrough } from 'node:stream';
import { validateConfiguration, forwardTaskRequest, handleRoute, privateConfiguration } from './trusted-client.mjs';

const token = 'a'.repeat(64);
const frontend = 'http://127.0.0.1:4173';

async function fixture(callback) {
  const server = http.createServer(callback);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const api = `http://127.0.0.1:${server.address().port}`;
  return { server, api, config: validateConfiguration({ frontend_url: frontend, task_api_url: api, capability: token }),
    close: () => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }) };
}
function req(api, extra = {}) {
  return { url: api + '/api/tasks', frameUrl: frontend + '/settings', method: 'GET', headers: {}, ...extra };
}

test('native transport authenticates without changing renderer headers', async () => {
  let authenticated = false; let cookie = false;
  const f = await fixture((request, response) => {
    authenticated = request.headers['x-nerelan-client-capability'] === token && request.headers.origin === frontend;
    cookie = Boolean(request.headers.cookie || request.headers.authorization);
    response.setHeader('content-type', 'application/json'); response.end('{"tasks":[]}');
  });
  try {
    const renderer = req(f.api, { headers: { Cookie: 'renderer-cookie', Authorization: 'renderer-bearer' } });
    const response = await forwardTaskRequest(renderer, f.config);
    assert.equal(response.status, 200); assert.equal(authenticated, true); assert.equal(cookie, false);
    assert.equal(Object.keys(renderer.headers).some(k => k.toLowerCase().includes('capability')), false);
    assert.equal(JSON.stringify(response.headers).includes(token), false);
  } finally { await f.close(); }
});

for (const kind of ['foreign-origin', 'foreign-frame', 'not-api', 'method', 'credentials', 'body-limit']) {
  test(`deny ${kind} before any outbound request`, async () => {
    let calls = 0;
    const f = await fixture((_, response) => { calls++; response.end('{}'); });
    try {
      const value = req(f.api);
      if (kind === 'foreign-origin') value.url = 'http://127.0.0.1:1/api/tasks';
      if (kind === 'foreign-frame') value.frameUrl = 'http://evil.example/';
      if (kind === 'not-api') value.url = f.api + '/other';
      if (kind === 'method') value.method = 'DELETE';
      if (kind === 'credentials') value.url = f.api.replace('http://', 'http://u:p@') + '/api/tasks';
      if (kind === 'body-limit') value.body = Buffer.alloc(256 * 1024 + 1);
      await assert.rejects(forwardTaskRequest(value, f.config)); assert.equal(calls, 0);
    } finally { await f.close(); }
  });
}

test('redirect never sends a capability to the second origin', async () => {
  let leaked = false;
  const destination = await fixture((_, response) => { leaked = true; response.end('{}'); });
  const source = await fixture((_, response) => { response.writeHead(302, { Location: destination.api + '/api/tasks' }); response.end(); });
  try {
    await assert.rejects(forwardTaskRequest(req(source.api), source.config), /client_redirect_denied/);
    await new Promise(resolve => setTimeout(resolve, 25)); assert.equal(leaked, false);
  } finally { await source.close(); await destination.close(); }
});

test('response echo and cookies cannot expose native capability', async () => {
  const f = await fixture((_, response) => { response.end(token); });
  try { await assert.rejects(forwardTaskRequest(req(f.api), f.config), /client_sensitive_response_denied/); }
  finally { await f.close(); }
  const cookies = await fixture((_, response) => { response.setHeader('set-cookie', 'opaque=' + token); response.end('{}'); });
  try { assert.equal('set-cookie' in (await forwardTaskRequest(req(cookies.api), cookies.config)).headers, false); }
  finally { await cookies.close(); }
});

test('slow backend is bounded with a fixed error', async () => {
  const f = await fixture(() => {});
  try { await assert.rejects(forwardTaskRequest(req(f.api), f.config, { timeout: 30 }), /client_transport_timeout/); }
  finally { await f.close(); }
});

test('oversized response is denied', async () => {
  const f = await fixture((_, response) => { response.end(Buffer.alloc(8 * 1024 * 1024 + 1)); });
  try { await assert.rejects(forwardTaskRequest(req(f.api), f.config), /client_response_too_large/); }
  finally { await f.close(); }
});

test('route fulfillment keeps secret out of browser network request', async () => {
  const f = await fixture((_, response) => { response.end('{}'); });
  let response;
  const headers = { Accept: 'application/json' };
  try {
    await handleRoute({ request: () => ({ url: () => f.api + '/api/tasks', method: () => 'GET',
      headers: () => headers, postDataBuffer: () => null, frame: () => ({ url: () => frontend }) }),
      fulfill: async value => { response = value; } }, f.config);
    assert.equal(response.status, 200); assert.deepEqual(headers, { Accept: 'application/json' });
    assert.equal(JSON.stringify(response.headers).includes(token), false);
  } finally { await f.close(); }
});

test('private bootstrap accepts one bounded in-memory packet', async () => {
  const stream = new PassThrough();
  const promise = privateConfiguration(stream);
  stream.write(JSON.stringify({ frontend_url: frontend, task_api_url: 'http://127.0.0.1:8766', capability: token }) + '\n');
  const result = await promise; stream.end();
  assert.equal(result.api, 'http://127.0.0.1:8766'); assert.equal(result.frontend, frontend);
});

for (const kind of ['malformed', 'oversized', 'empty']) {
  test(`private bootstrap ${kind} is sanitized`, async () => {
    const stream = new PassThrough(); const promise = privateConfiguration(stream);
    if (kind === 'malformed') stream.write(token + '\n');
    if (kind === 'oversized') stream.write('x'.repeat(8193));
    stream.end();
    await assert.rejects(promise, error => error.message === 'client_bootstrap_failed' && !error.message.includes(token));
  });
}

test('configuration rejects non-loopback and credential URLs', () => {
  for (const url of ['https://127.0.0.1:4173', 'http://evil.example:4173', 'http://u:p@127.0.0.1:4173', frontend + '?cap=' + token]) {
    assert.throws(() => validateConfiguration({ frontend_url: url, task_api_url: 'http://127.0.0.1:8766', capability: token }), /client_configuration_invalid/);
  }
});
