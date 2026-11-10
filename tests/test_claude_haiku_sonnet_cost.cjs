#!/usr/bin/env node
"use strict";
const assert=require("node:assert/strict");
const path=require("node:path");
const fs=require("node:fs");
const root=path.resolve(__dirname,"..");
const {computeHaikuSonnetCost,HAIKU_SONNET_RATES}=require(path.join(root,"assets/claude-haiku-sonnet-cost.js"));
function approx(actual,expected,msg){assert.ok(Math.abs(actual-expected)<0.000001,(msg||"")+" expected "+expected+" received "+actual);}
const simple=computeHaikuSonnetCost({requests:50000,input:2000,output:400});
approx(simple.haiku,20,"Haiku default");
approx(simple.sonnet,400,"Sonnet default");
approx(simple.savings,380,"Savings default");
approx(simple.ratio,20,"Ratio");
assert.equal(simple.longPrompt,false);
const boundary=computeHaikuSonnetCost({requests:1,input:100000,output:1000});
const long=computeHaikuSonnetCost({requests:1,input:100001,output:1000});
assert.equal(boundary.longPrompt,false);
assert.equal(long.longPrompt,true);
approx(boundary.haiku,100000*.1/1e6+1000*.5/1e6);
approx(long.haiku,100001*.5/1e6+1000*2.5/1e6);
const cached=computeHaikuSonnetCost({requests:1000,input:1000,output:0,cacheRead:50,cacheWrite:25});
approx(cached.haiku,1000*(250*.1+500*.01+250*.125)/1e6);
approx(cached.sonnet,1000*(250*2+500*.1+250*2.5)/1e6);
const highCached=computeHaikuSonnetCost({requests:1,input:120000,output:0,cacheRead:100,cacheWrite:0});
approx(highCached.haiku,120000*.05/1e6);
approx(highCached.sonnet,120000*.1/1e6);
assert.equal(HAIKU_SONNET_RATES.sonnet.read,.10);
for(const args of [
{requests:0,input:100,output:5},{requests:1,input:0,output:5},
{requests:1,input:100,output:-1},
{requests:1,input:100,output:0,cacheRead:60,cacheWrite:50},
{requests:1,input:100,output:0,cacheRead:101},
{requests:1,input:1000001,output:0},
{requests:1.5,input:100,output:0},
{requests:1,input:100,output:0,cacheRead:Number.NaN},
])assert.throws(()=>computeHaikuSonnetCost(args));
const code=fs.readFileSync(path.join(root,"assets/claude-haiku-sonnet-cost.js"),"utf8");
for(const bad of ["fetch(","sendBeacon","localStorage","document.cookie"])assert.ok(!code.includes(bad),"No tracking/network: "+bad);
console.log("PASS: Haiku/Sonnet 100K pricing boundary, 5m caching, effective costs, invalid inputs and privacy");
