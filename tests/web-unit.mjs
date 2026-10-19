import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const ROOT = new URL('../', import.meta.url);

async function page(name) {
  return readFile(new URL(`web/${name}`, ROOT), 'utf8');
}

function inlineScript(html) {
  const matches = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)];
  assert.ok(matches.length, 'page has an inline script');
  return matches.at(-1)[1];
}

function receiverScript(html) {
  return inlineScript(html)
    .replace(/\(function \(\) \{/, '')
    .replace(/\}\)\(\);\s*$/, '');
}

function element(id) {
  const listeners = {};
  return {
    id,
    style: {},
    hidden: false,
    disabled: false,
    checked: id === 'localMute',
    value: id === 'quality' ? '1080p30' : '',
    textContent: '',
    innerHTML: '',
    className: '',
    srcObject: null,
    addEventListener(type, fn) { listeners[type] = fn; },
    dispatch(type, event = {}) { if (listeners[type]) listeners[type](event); },
    querySelector(selector) { return element(`${id} ${selector}`); },
    play() { return Promise.resolve(); },
    focus() {},
  };
}

function baseContext() {
  const elements = new Map();
  const get = (id) => {
    if (!elements.has(id)) elements.set(id, element(id));
    return elements.get(id);
  };
  let timer = 0;
  const documentListeners = {};
  const document = {
    hidden: false,
    body: { prepend() {} },
    documentElement: {},
    fullscreenElement: null,
    webkitFullscreenElement: null,
    getElementById: get,
    createElement(tag) {
      if (tag === 'canvas') {
        const canvas = element('canvas');
        canvas.getContext = () => ({ drawImage() {}, getImageData: () => ({ data: new Uint8ClampedArray(1024) }) });
        return canvas;
      }
      return element(tag);
    },
    addEventListener(type, fn) { documentListeners[type] = fn; },
  };
  const windowListeners = {};
  const context = {
    console,
    Promise,
    Math,
    Date,
    JSON,
    Object,
    Array,
    String,
    Number,
    RegExp,
    Error,
    URLSearchParams,
    Uint8ClampedArray,
    Blob,
    performance: { now: () => Date.now() },
    location: { search: '' },
    screen: { width: 1920, height: 1080 },
    innerWidth: 1920,
    innerHeight: 1080,
    document,
    navigator: {
      userAgent: 'Unit Test TV',
      sendBeacon() { return true; },
      mediaDevices: {},
    },
    sessionStorage: {
      values: new Map(),
      getItem(k) { return this.values.get(k) || null; },
      setItem(k, v) { this.values.set(k, String(v)); },
      removeItem(k) { this.values.delete(k); },
    },
    setTimeout() { return ++timer; },
    clearTimeout() {},
    setInterval() { return ++timer; },
    clearInterval() {},
    requestAnimationFrame() {},
  };
  context.window = {
    TABCAST: { senderToken: 'sender-secret', pairCode: '481205', receiverUrl: 'http://192.0.2.20:8090/', version: '0.1.0' },
    RTCPeerConnection: function () {},
    RTCRtpReceiver: null,
    MediaSource: null,
    addEventListener(type, fn) { windowListeners[type] = fn; },
    open() {},
  };
  context.globalThis = context;
  context.__elements = elements;
  return vm.createContext(context);
}

function makeTrack(kind, label) {
  const listeners = {};
  return {
    kind,
    label,
    contentHint: '',
    stopped: false,
    addEventListener(type, fn) { listeners[type] = fn; },
    stop() {
      if (this.stopped) return;
      this.stopped = true;
      if (listeners.ended) listeners.ended();
    },
    getSettings() { return { width: 1920, height: 1080 }; },
    applyConstraints() { return Promise.resolve(); },
  };
}

function makeStream(label) {
  const video = makeTrack('video', label);
  return {
    video,
    getVideoTracks: () => [video],
    getAudioTracks: () => [],
    getTracks: () => [video],
  };
}

async function settle() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

test('sender authenticates signaling and identifies every message and report', async () => {
  const html = await page('sender.html');
  const context = baseContext();
  const calls = [];
  context.fetch = (url, options = {}) => {
    calls.push({ url, options });
    if (url === '/status' || String(url).startsWith('/poll')) return new Promise(() => {});
    return Promise.resolve({ ok: true, status: 204, json: async () => ({}) });
  };
  context.AudioContext = function () { this.createOscillator = () => ({ frequency: {}, connect() { return this; }, start() {} }); this.createGain = () => ({ gain: {}, connect() { return this; } }); this.close = () => {}; };
  context.RTCPeerConnection = function () { this.getSenders = () => []; this.close = () => {}; };
  context.RTCRtpSender = { getCapabilities: () => ({ codecs: [] }) };
  vm.runInContext(inlineScript(html), context);
  calls.length = 0;

  vm.runInContext("send({type:'bye'}); report({event:'unit'})", context);
  await settle();

  assert.equal(calls.length, 2);
  for (const call of calls) {
    assert.equal(call.options.headers['X-Tabcast-Token'], 'sender-secret');
    const body = JSON.parse(call.options.body);
    assert.match(body.id, /^mac-/);
    assert.equal(body.from, 'sender');
  }
});

test('switching capture does not let the retired track stop the new capture', async () => {
  const html = await page('sender.html');
  const context = baseContext();
  context.fetch = () => new Promise(() => {});
  context.AudioContext = function () { this.createOscillator = () => ({ frequency: {}, connect() { return this; }, start() {} }); this.createGain = () => ({ gain: {}, connect() { return this; } }); this.close = () => {}; };
  context.RTCPeerConnection = function () { this.getSenders = () => []; this.close = () => {}; };
  context.RTCRtpSender = { getCapabilities: () => ({ codecs: [] }) };
  const first = makeStream('Private tab title');
  const second = makeStream('Another private title');
  context.navigator.mediaDevices.getDisplayMedia = async () => first;
  vm.runInContext(inlineScript(html), context);

  vm.runInContext("setTv(true, 'ready')", context);
  await vm.runInContext('start()', context);
  const switchNavigator = { mediaDevices: { getDisplayMedia: async () => second } };
  context.__switchNavigator = switchNavigator;
  context.__second = second;
  await vm.runInContext('switchTab(__switchNavigator)', context);

  assert.equal(vm.runInContext('stream === __second', context), true);
  assert.equal(second.video.stopped, false);
});

test('stopping while a source switch is pending cannot resurrect capture', async () => {
  const html = await page('sender.html');
  const context = baseContext();
  context.fetch = () => new Promise(() => {});
  context.RTCPeerConnection = function () { this.getSenders = () => []; this.close = () => {}; };
  context.RTCRtpSender = { getCapabilities: () => ({ codecs: [] }) };
  const first = makeStream('first');
  const second = makeStream('second');
  let release;
  context.navigator.mediaDevices.getDisplayMedia = async () => first;
  vm.runInContext(inlineScript(html), context);
  vm.runInContext("setTv(true, 'ready')", context);
  await vm.runInContext('start()', context);
  context.__switchNavigator = { mediaDevices: { getDisplayMedia: () => new Promise((resolve) => { release = () => resolve(second); }) } };
  const switching = vm.runInContext('switchTab(__switchNavigator)', context);
  await settle();
  vm.runInContext("stop('user')", context);
  release();
  await switching;

  assert.equal(vm.runInContext('stream', context), null);
  assert.equal(second.video.stopped, true);
});

test('a rejected track replacement after stop cannot restore the old stream', async () => {
  const html = await page('sender.html');
  const context = baseContext();
  context.fetch = () => new Promise(() => {});
  context.RTCPeerConnection = function () { this.getSenders = () => []; this.close = () => {}; };
  context.RTCRtpSender = { getCapabilities: () => ({ codecs: [] }) };
  const first = makeStream('first');
  const second = makeStream('second');
  let rejectReplacement;
  context.navigator.mediaDevices.getDisplayMedia = async () => first;
  vm.runInContext(inlineScript(html), context);
  vm.runInContext("setTv(true, 'ready')", context);
  await vm.runInContext('start()', context);
  context.__replacementPc = {
    getSenders: () => [{ track: { kind: 'video' }, replaceTrack: () => new Promise((resolve, reject) => { rejectReplacement = reject; }) }],
    close() {},
  };
  context.__switchNavigator = { mediaDevices: { getDisplayMedia: async () => second } };
  vm.runInContext('pc=__replacementPc', context);
  const switching = vm.runInContext('switchTab(__switchNavigator)', context);
  await settle();
  vm.runInContext("stop('user')", context);
  rejectReplacement(new Error('replacement failed after stop'));
  await switching;

  assert.equal(vm.runInContext('stream', context), null);
  assert.equal(context.__elements.get('switch').disabled, true);
  assert.equal(second.video.stopped, true);
});

test('sender defaults to browser congestion control and keepalive is explicit opt-in', async () => {
  const source = inlineScript(await page('sender.html'));
  assert.match(source, /OPT\.get\(['"]cc['"]\)\s*===\s*['"]loss['"]/);
  assert.match(source, /OPT\.get\(['"]keepalive['"]\)\s*!==\s*['"]1['"]/);
  assert.doesNotMatch(source, /captur(?:ing|ed|e)[^\n]*\.label/i);
});

test('sender queues remote ICE until the answer is installed', async () => {
  const source = inlineScript(await page('sender.html'));
  assert.match(source, /pendingRemoteCandidates/);
  assert.match(source, /remoteDescription/);
  assert.match(source, /addIceCandidate/);
});

test('receiver stays ES5 and provides an accessible six-digit pairing form', async () => {
  const html = await page('receiver.html');
  const source = inlineScript(html);
  assert.match(html, /<html\s+lang="en"/i);
  assert.match(html, /<form[^>]+id="pairForm"/i);
  assert.match(html, /input[^>]+inputmode="numeric"[^>]+pattern="\[0-9\]\{6\}"/i);
  assert.match(html, /aria-live="polite"/i);
  assert.doesNotMatch(source, /\b(?:const|let)\s+[A-Za-z_$]|\bclass\s+[A-Za-z_$]|\basync\s+function|=>|`|\?\.|\.\.\./);
});

test('receiver authenticates every protected request and identifies messages and reports', async () => {
  const html = await page('receiver.html');
  const context = baseContext();
  const requests = [];
  context.XMLHttpRequest = function () {
    this.headers = {};
    this.open = (method, url) => { this.method = method; this.url = url; };
    this.setRequestHeader = (key, value) => { this.headers[key] = value; };
    this.send = (body) => { this.body = body; requests.push(this); };
  };
  context.RTCPeerConnection = function () {};
  vm.runInContext(receiverScript(html), context);
  requests.length = 0;

  vm.runInContext("token='receiver-secret'; registered=true; send({type:'tv-ready'}); report({event:'unit'}); xhr('GET','/time',null,function(){})", context);

  assert.equal(requests.length, 3);
  for (const request of requests) assert.equal(request.headers['X-Tabcast-Token'], 'receiver-secret');
  for (const request of requests.slice(0, 2)) {
    const body = JSON.parse(request.body);
    assert.match(body.id, /^tv-/);
    assert.equal(body.from, 'tv');
  }
});

test('receiver keeps ICE received before a new offer', async () => {
  const html = await page('receiver.html');
  const context = baseContext();
  context.XMLHttpRequest = function () {
    this.open = () => {};
    this.setRequestHeader = () => {};
    this.send = () => {};
  };
  const added = [];
  context.RTCPeerConnection = function () {
    this.remoteDescription = null;
    this.setRemoteDescription = (sdp) => { this.remoteDescription = sdp; return Promise.resolve(); };
    this.addIceCandidate = (candidate) => { added.push(candidate); return Promise.resolve(); };
    this.createAnswer = () => Promise.resolve({ type: 'answer', sdp: 'answer' });
    this.setLocalDescription = (answer) => { this.localDescription = answer; return Promise.resolve(); };
    this.close = () => {};
    this.getStats = () => Promise.resolve(new Map());
  };
  vm.runInContext(receiverScript(html), context);
  const candidate = { candidate: 'candidate:unit' };
  context.__candidate = candidate;
  await vm.runInContext("pendingCandidates.push(__candidate); onOffer({sdp:{type:'offer',sdp:'offer'}})", context);
  await settle();

  assert.deepEqual(added, [candidate]);
});

test('receiver without WebRTC keeps the unsupported state and ignores offers', async () => {
  const html = await page('receiver.html');
  const context = baseContext();
  const requests = [];
  context.window.RTCPeerConnection = undefined;
  context.XMLHttpRequest = function () {
    this.headers = {};
    this.open = (method, url) => { this.method = method; this.url = url; };
    this.setRequestHeader = (key, value) => { this.headers[key] = value; };
    this.send = (body) => { this.body = body; requests.push(this); };
  };
  vm.runInContext(receiverScript(html), context);

  vm.runInContext("token='receiver-secret'; registered=true; onRegistered(); handle({type:'presence',online:true,id:'mac-1'}); handle({type:'offer',sdp:{type:'offer',sdp:'offer'}})", context);

  assert.match(context.__elements.get('tvState').textContent, /does not support WebRTC/i);
  assert.equal(vm.runInContext('pc', context), null);
  assert.ok(requests.some((request) => request.url === '/report'), 'capabilities are still reported');
});

test('latency page describes its timestamp result as a diagnostic measurement', async () => {
  const html = await page('latency.html');
  assert.match(html, /diagnostic/i);
  assert.doesNotMatch(html, /real end[‑-]to[‑-]end/i);
  assert.match(inlineScript(html), /X-Tabcast-Token/);
});
