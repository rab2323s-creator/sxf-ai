#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const script = name => fs.readFileSync(path.join(root, name), 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));

function element(initial = '') {
  return {
    innerHTML: initial, textContent: '', hidden: false, value: '',
    dataset: {}, classList: { add() {}, remove() {} }, events: {},
    addEventListener(name, fn) { this.events[name] = fn; },
    getAttribute(name) { return name === 'href' ? this.href : null; },
    removeAttribute() {},
  };
}

function setup(file, load, predefined = '') {
  const els = new Map();
  const get = id => {
    if (!els.has(id)) els.set(id, element(id === 'signalsFeed' || id === 'feed' ||
      id === 'featured' ? predefined : ''));
    return els.get(id);
  };
  const filter = element();
  filter.dataset.signalFilter = 'Agents';
  filter.dataset.filter = 'Models';
  const doc = {
    getElementById: get,
    querySelectorAll(selector) {
      if (selector === '.signals-filter' || selector === '.filter') return [filter];
      if (selector === '#featured a.featured-story,#feed a.story-card') {
        const anchor = element();
        anchor.href = '/signals/verified-model/';
        return [anchor];
      }
      return [];
    },
  };
  const context = vm.createContext({
    document: doc, window: { location: { origin: 'https://sxf.si' } },
    URL, Date, console,
    fetch: load,
  });
  vm.runInContext(script(file), context, { filename: file });
  return { els, get, filter, context };
}

async function main() {
  const sample = {
    title: 'New architecture for long-horizon workflows',
    summary: 'Agents can orchestrate multi-step model inference.',
    source: 'OpenAI', url: 'https://example.test/release',
    signal_url: 'https://sxf.si/signals/verified-model/',
    published: new Date().toISOString(), category: 'Models',
  };

  const ok = () => Promise.resolve({
    ok: true, json: () => Promise.resolve({ items: [sample] }),
  });
  const signals = setup('signals.js', ok);
  await settle();
  assert.match(signals.get('signalsFeed').innerHTML, /long-horizon workflows/);
  signals.filter.events.click();
  assert.match(signals.get('signalsFeed').innerHTML, /long-horizon workflows/,
    'Agents filter must match summary evidence in public feed');
  signals.get('signalsSearch').value = 'orchestrate';
  signals.get('signalsSearch').events.input();
  assert.match(signals.get('signalsFeed').innerHTML, /long-horizon workflows/,
    'Search must cover the public summary');
  signals.get('signalsSearch').value = 'not-present-anywhere';
  signals.get('signalsSearch').events.input();
  assert.equal(signals.get('signalsFeed').innerHTML, '');

  const broken = () => Promise.reject(new Error('offline'));
  const signalsOffline = setup('signals.js', broken, 'Indexed Signals content');
  await settle();
  signalsOffline.filter.events.click();
  signalsOffline.get('signalsSearch').events.input();
  assert.equal(signalsOffline.get('signalsFeed').innerHTML, 'Indexed Signals content',
    'Never erase the server-rendered Signals list on fetch failure');

  const homepageOffline = setup('app.js', broken, 'Indexed homepage content');
  await settle();
  homepageOffline.filter.events.click();
  assert.equal(homepageOffline.get('featured').innerHTML, 'Indexed homepage content');
  assert.equal(homepageOffline.get('feed').innerHTML, 'Indexed homepage content');
  assert.equal(homepageOffline.get('featured').hidden, false);
  assert.equal(homepageOffline.get('lastUpdated').textContent, 'offline');

  const homepage = setup('app.js', ok);
  await settle();
  assert.match(homepage.get('featured').innerHTML, /long-horizon workflows/);
  assert.equal(homepage.get('storyCount').textContent, 1);
  console.log('PASS: summary search, Agents filter, homepage and offline HTML fallbacks');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
