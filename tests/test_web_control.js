// Copyright (c) 2026 Dawid Bautsch
// SPDX-License-Identifier: MIT
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

async function createPanel(initialCookie = '') {
    const elements = new Map();
    const calls = [];
    const timers = new Map();
    const intervals = [];
    let fetchOverride = null;
    let timerId = 0;
    let finishAcquire;
    const acquisition = new Promise(resolve => { finishAcquire = resolve; });
    const defaults = {'#format': 'h264', '#preset': 'ultrafast', '#crf': '12',
        '#bitrate': '8', '#qsv-preset': 'veryfast', '#qsv-mode': 'cbr',
        '#qsv-quality': '18', '#qsv-gop': '30'};
    let cookie = initialCookie;

    function element(selector) {
        if (!elements.has(selector)) {
            elements.set(selector, {
                classList: { toggle() {} },
                addEventListener(type, callback) {
                    const previous = this['on' + type];
                    this['on' + type] = event => { if (previous) previous(event); callback(event); };
                },
                setAttribute() {}, removeAttribute() {}, replaceChildren() {},
                pause() {}, load() {},
                value: defaults[selector] || '', checked: selector === '#qsv-icq',
            });
        }
        return elements.get(selector);
    }

    const document = {
        querySelector: element,
        addEventListener() {},
        hasFocus: () => true,
        hidden: false,
        get cookie() { return cookie; },
        set cookie(value) { cookie = value.split(';', 1)[0]; },
    };
    const context = vm.createContext({
        document,
        window: { addEventListener() {} },
        performance: { now: () => Date.now() },
        URL: { revokeObjectURL() {}, createObjectURL: () => 'blob:test' },
        TextDecoder, Blob,
        fetch: async (url, options) => {
            calls.push(url);
            if (fetchOverride) return fetchOverride(url, options);
            if (url.endsWith('/acquire')) return acquisition;
            return { ok: true, json: async () => url.endsWith('/devices') ? [] : {} };
        },
        setInterval: callback => { intervals.push(callback); return intervals.length; },
        clearInterval() {},
        setTimeout: callback => { const id = ++timerId; timers.set(id, callback); return id; },
        clearTimeout: id => timers.delete(id),
        cancelAnimationFrame() {},
        console,
    });
    const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
    const script = html.match(/<script>([\s\S]*)<\/script>/)[1];
    vm.runInContext(script, context);
    await new Promise(resolve => setImmediate(resolve));

    return {
        calls, context, document, elements, finishAcquire, timers, intervals,
        overrideFetch: callback => { fetchOverride = callback; },
        run: code => vm.runInContext(code, context),
    };
}

test('control cannot start without a playing preview', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); renderControl()");
    assert.equal(panel.elements.get('#keyboard').disabled, true);
    await panel.run('toggle()');
    assert.equal(panel.calls.some(url => url.endsWith('/acquire')), false);
});

test('an acquisition finishing after the preview stops releases its lease', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); previewController = {abort() {}}; previewReady = true; renderControl()");
    assert.equal(panel.elements.get('#keyboard').disabled, false);
    const pending = panel.run('toggle()');
    panel.run('stopPreview()');
    panel.finishAcquire({ ok: true, json: async () => ({ token: 'test-token' }) });
    await pending;
    assert.equal(panel.run('controlToken'), null);
    assert.equal(panel.elements.get('#keyboard').disabled, true);
    assert.equal(panel.calls.filter(url => url.endsWith('/release')).length, 1);
});

test('an acquisition cannot attach to a replacement preview of the same device', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); previewController = {abort() {}}; previewReady = true");
    const pending = panel.run('toggle()');
    panel.run('stopPreview(); previewController = {abort() {}}; previewReady = true');
    panel.finishAcquire({ ok: true, json: async () => ({ token: 'test-token' }) });
    await pending;
    assert.equal(panel.run('controlToken'), null);
    assert.equal(panel.calls.filter(url => url.endsWith('/release')).length, 1);
});

test('a playback error releases active control', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); previewController = {abort() {}}; previewReady = true");
    const pending = panel.run('toggle()');
    panel.finishAcquire({ ok: true, json: async () => ({ token: 'test-token' }) });
    await pending;
    assert.equal(panel.run('controlToken'), 'test-token');
    const video = panel.elements.get('#video');
    video.error = {};
    video.onerror();
    await panel.run('pending');
    assert.equal(panel.run('controlToken'), null);
    assert.equal(panel.elements.get('#keyboard').disabled, true);
    assert.equal(panel.calls.filter(url => url.endsWith('/release')).length, 1);
});

test('a prolonged playback stall releases control', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); previewController = {abort() {}}; previewReady = true");
    const pending = panel.run('toggle()');
    panel.finishAcquire({ ok: true, json: async () => ({ token: 'test-token' }) });
    await pending;
    panel.elements.get('#video').onwaiting();
    assert.equal(panel.timers.size, 1);
    panel.timers.values().next().value();
    await panel.run('pending');
    assert.equal(panel.run('controlToken'), null);
    assert.equal(panel.elements.get('#keyboard').disabled, true);
    assert.equal(panel.calls.filter(url => url.endsWith('/release')).length, 1);
});

test('a brief stall cancels the timeout when playback resumes', async () => {
    const panel = await createPanel();
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); previewController = {abort() {}}; previewReady = true");
    const video = panel.elements.get('#video');
    video.onwaiting();
    assert.equal(panel.timers.size, 1);
    video.onplaying();
    assert.equal(panel.timers.size, 0);
    assert.equal(panel.run('previewReady'), true);
    assert.equal(panel.elements.get('#keyboard').disabled, false);
});

test('raw stream handles headers and image data split across network chunks', async () => {
    const panel = await createPanel();
    const content = Buffer.from('--frame\r\nContent-type: image/jpeg\r\nContent-length: 4\r\n\r\nABCD\r\n');
    const chunks = [content.subarray(0, 13), content.subarray(13, 51), content.subarray(51)];
    panel.overrideFetch(async () => ({
        ok: true,
        body: { getReader: () => ({
            read: async () => chunks.length ? { value: chunks.shift(), done: false } : { done: true },
        }) },
    }));
    panel.run("current = 'remote-video0'; controllableDevices.add('remote-video0'); img = rawImage; previewController = {signal: {aborted: false}, abort() {}}");
    await assert.rejects(panel.run("startRaw('remote-video0',previewController)"), /przerwany/);
    assert.equal(panel.elements.get('#raw-video').src, 'blob:test');
    assert.equal(panel.run('bytesReceived'), content.length);
    panel.elements.get('#raw-video').onload();
    assert.equal(panel.run('previewReady'), true);
    assert.equal(panel.run('framesPresented'), 1);
});

test('settings are applied only when the form is submitted', async () => {
    const panel = await createPanel();
    panel.elements.get('#format').value = 'raw';
    panel.elements.get('#preset').value = 'veryfast';
    panel.elements.get('#crf').value = '18';
    panel.elements.get('#bitrate').value = '4';
    assert.equal(panel.run('applied.format'), 'h264');
    panel.elements.get('#settings').onsubmit({ preventDefault() {} });
    assert.equal(panel.run('applied.format'), 'raw');
    assert.equal(panel.run('applied.preset'), 'veryfast');
    assert.equal(panel.run('applied.bitrate'), 4000);
});

test('overlay reports received data in megabits per second', async () => {
    const panel = await createPanel();
    panel.run("img=rawImage; previewController={}; overlayInput.checked=true; overlayAt=Date.now()-1000; framesPresented=30; bytesReceived=1000000");
    await panel.intervals[0]();
    const text = panel.elements.get('#overlay').textContent;
    assert.match(text, /FPS: 29\.[0-9]|FPS: 30\.0/);
    assert.match(text, /Transfer: (7\.[0-9]+|8\.00) Mb\/s/);
    assert.match(text, /RTT HTTP:/);
    assert.match(text, /Bufor: n\/d/);
});

test('MP4 codec strings match the actual AVC and HEVC initialization data', async () => {
    const panel = await createPanel();
    function box(type, data) {
        const result = Buffer.alloc(data.length + 8);
        result.writeUInt32BE(result.length);
        result.write(type, 4, 'ascii');
        data.copy(result, 8);
        return result;
    }
    const avc = box('moov', box('avcC', Buffer.from('01420028', 'hex')));
    const hevc = box('moov', box('hvcC', Buffer.from('01214000000090000000000078', 'hex')));
    panel.context.avcInit = avc;
    panel.context.hevcInit = hevc;
    assert.equal(panel.run('mimeFromInit(avcInit, false)'), 'video/mp4; codecs="avc1.420028"');
    assert.equal(panel.run('mimeFromInit(hevcInit, true)'), 'video/mp4; codecs="hvc1.1.2.H120.90"');
    assert.equal(panel.run('mimeFromInit(avcInit.subarray(0, 10), false)'), null);
});


test('QSV controls follow the codec and ICQ disables bitrate', async () => {
    const panel = await createPanel();
    const format = panel.elements.get('#format');
    const icq = panel.elements.get('#qsv-icq');
    format.value = 'h264_qsv';
    icq.checked = true;
    format.onchange();
    assert.equal(panel.elements.get('#qsv-profile').value, 'baseline');
    assert.equal(panel.elements.get('#bitrate').disabled, true);
    assert.equal(panel.elements.get('#qsv-quality').disabled, false);
    format.value = 'hevc_qsv';
    format.onchange();
    assert.equal(panel.elements.get('#qsv-profile').value, 'main');
    assert.doesNotMatch(panel.elements.get('#qsv-profile').innerHTML, /baseline|high/);
    icq.checked = false;
    panel.elements.get('#qsv-mode').value = 'cbr';
    icq.onchange();
    assert.equal(panel.elements.get('#bitrate').disabled, false);
    assert.equal(panel.elements.get('#qsv-quality').disabled, true);
});

test('only controls relevant to the chosen codec and rate mode are visible', async () => {
    const panel = await createPanel();
    const format = panel.elements.get('#format');
    const icq = panel.elements.get('#qsv-icq');
    const mode = panel.elements.get('#qsv-mode');
    assert.equal(panel.elements.get('#preset-label').hidden, false);
    assert.equal(panel.elements.get('#qsv-preset-label').hidden, true);
    format.value = 'raw'; format.onchange();
    assert.equal(panel.elements.get('#preset-label').hidden, true);
    assert.equal(panel.elements.get('#crf-label').hidden, true);
    assert.equal(panel.elements.get('#bitrate-label').hidden, true);
    format.value = 'h264_qsv'; format.onchange();
    assert.equal(panel.elements.get('#qsv-preset-label').hidden, false);
    assert.equal(panel.elements.get('#qsv-quality-label').hidden, false);
    assert.equal(panel.elements.get('#qsv-mode-label').hidden, true);
    assert.equal(panel.elements.get('#bitrate-label').hidden, true);
    icq.checked = false; mode.value = 'vbr'; icq.onchange();
    assert.equal(panel.elements.get('#qsv-mode-label').hidden, false);
    assert.equal(panel.elements.get('#qsv-quality-label').hidden, true);
    assert.equal(panel.elements.get('#bitrate-label').hidden, false);
    mode.value = 'cqp'; mode.onchange();
    assert.equal(panel.elements.get('#qsv-quality-label').hidden, false);
    assert.equal(panel.elements.get('#bitrate-label').hidden, true);
});

test('settings and overlay survive a page reload via the cookie', async () => {
    const panel = await createPanel();
    const format = panel.elements.get('#format');
    format.value = 'hevc_qsv'; format.onchange();
    panel.elements.get('#qsv-preset').value = 'medium';
    panel.elements.get('#qsv-quality').value = '14';
    panel.elements.get('#qsv-gop').value = '60';
    panel.elements.get('#show-overlay').checked = true;
    panel.elements.get('#show-overlay').onchange();
    assert.match(panel.document.cookie, /^davekvm_settings=/);
    const reloaded = await createPanel(panel.document.cookie);
    assert.equal(reloaded.elements.get('#format').value, 'hevc_qsv');
    assert.equal(reloaded.elements.get('#qsv-profile').value, 'main');
    assert.equal(reloaded.elements.get('#qsv-quality').value, 14);
    assert.equal(reloaded.elements.get('#show-overlay').checked, true);
    assert.equal(reloaded.elements.get('#overlay').hidden, false);
    assert.equal(reloaded.run('applied.qsvMode'), 'icq');
    assert.equal(reloaded.run('applied.qsvPreset'), 'medium');
    assert.equal(reloaded.run('applied.qsvGop'), 60);
    assert.equal(reloaded.elements.get('#qsv-quality-label').hidden, false);
});

test('malformed or out-of-range cookie values are ignored', async () => {
    const bad = await createPanel('davekvm_settings=%broken');
    assert.equal(bad.run('applied.format'), 'h264');
    const valid = await createPanel();
    valid.elements.get('#format').value = 'h264_qsv';
    valid.elements.get('#format').onchange();
    const entry = JSON.parse(decodeURIComponent(valid.document.cookie.split('=')[1]));
    entry.qsvQuality = 999;
    const invalid = await createPanel('davekvm_settings=' + encodeURIComponent(JSON.stringify(entry)));
    assert.equal(invalid.run('applied.format'), 'h264');
});
