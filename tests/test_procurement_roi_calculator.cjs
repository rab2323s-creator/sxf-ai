"use strict";
const assert=require("node:assert/strict");
const {estimate}=require("../guides/ai-procurement-negotiation-software/procurement.js");
function close(x,y){assert.ok(Math.abs(x-y)<0.01,x+" != "+y);}
const base=estimate({spend:5000000,accepted:40,price:4,days:30,capital:8,platform:75000,review:20000});
close(base.acceptedSpend,2000000);close(base.priceBenefit,80000);close(base.financingBenefit,13150.68493150685);close(base.costs,95000);close(base.net,-1849.31506849315);
const low=estimate({spend:5000000,accepted:20,price:2,days:20,capital:8,platform:75000,review:20000});
close(low.net,-70616.43835616438);
const up=estimate({spend:5000000,accepted:65,price:6,days:45,capital:8,platform:75000,review:20000});
close(up.net,132054.79452054796);
close(estimate({spend:0,accepted:0,price:0,days:0,capital:0,platform:0,review:0}).net,0);
console.log("PASS: procurement ROI model cases, 0 baseline and sign correctness");