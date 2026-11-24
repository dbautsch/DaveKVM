// Copyright (c) 2026 Dawid Bautsch
// SPDX-License-Identifier: MIT
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'i18n.js'), 'utf8');
const context = vm.createContext({document: {addEventListener() {}}});
vm.runInContext(source, context);

test('all four languages translate the panel heading', () => {
    const translate = (value, language) => context.translateText(value, language);
    assert.equal(translate('Podgląd na żywo', 'pl'), 'Podgląd na żywo');
    assert.equal(translate('Podgląd na żywo', 'en'), 'Live preview');
    assert.equal(translate('Podgląd na żywo', 'de'), 'Live-Vorschau');
    assert.equal(translate('Podgląd na żywo', 'cs'), 'Živý náhled');
});

test('dynamic messages retain device identifiers', () => {
    assert.equal(context.translateText('Podgląd · video2', 'en'), 'Preview · video2');
    assert.equal(context.translateText('Unknown external device', 'cs'), 'Unknown external device');
    assert.equal(context.translateText('Podgląd na żywo', 'invalid'), 'Podgląd na żywo');
});

test('backend error codes translate in all languages and unknown codes are safe', () => {
    const text = context.backendError('KEYBOARD_BUSY', 'ignored');
    assert.equal(text, 'Klawiatura jest zajęta przez innego użytkownika');
    assert.equal(context.translateText(text, 'en'), 'Keyboard is in use by another user');
    assert.equal(context.translateText(text, 'de'), 'Tastatur wird von einem anderen Benutzer verwendet');
    assert.equal(context.translateText(text, 'cs'), 'Klávesnici používá jiný uživatel');
    assert.equal(context.backendError('toString', 'ignored'), 'Nieoczekiwany błąd');
    assert.equal(context.backendError(null, 'legacy'), 'legacy');
    const codes = vm.runInContext('Object.keys(backendErrorText)', context);
    for (const code of codes) {
        const polish = context.backendError(code, '');
        for (const language of ['en', 'de', 'cs']) {
            assert.notEqual(context.translateText(polish, language), polish, `${code} missing ${language}`);
        }
    }
});

test('HTML contains the current translator and all selectable languages', () => {
    const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
    assert.ok(html.replace(/\r\n/g, '\n').includes(source.replace(/\r\n/g, '\n').trim()));
    for (const language of ['pl', 'en', 'de', 'cs']) {
        assert.ok(html.includes(`value="${language}"`));
    }
});
