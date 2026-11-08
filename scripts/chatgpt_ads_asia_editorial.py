"""Source-verified SXF analysis of ChatGPT Ads September 2026 SEA/Taiwan rollout.
Historical launch date retained; current October coverage is presented separately.
Only the matching signal uses this editorial transformation at scheduled rebuilds.
"""
import json
import re
from html import escape

CANONICAL = "https://sxf.si/signals/chatgpt-ads-expands-to-southeast-asia-and-taiwan-f5b0ef0/"
TITLE = "ChatGPT Ads Expands to Southeast Asia & Taiwan (2026) | SXF"
H1 = "ChatGPT Ads Expands to Southeast Asia and Taiwan: 7 Markets"
DESCRIPTION = "ChatGPT Ads expands to 7 markets: Indonesia, Malaysia, Philippines, Singapore, Thailand, Vietnam and Taiwan. Plans, advertiser access and SXF analysis."
SOURCES = ["https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/","https://openai.com/index/chatgpt-ads-expands-26-new-countries/","https://help.openai.com/en/articles/20001245-ads-manager-availability","https://help.openai.com/en/articles/20001047-ads-in-chatgpt","https://help.openai.com/en/articles/20001207-ads-in-chatgpt-the-basics","https://help.openai.com/en/articles/20001212-creating-ads-for-chatgpt-ads","https://help.openai.com/en/articles/20001409-conversion-measurement","https://openai.com/index/building-chatgpt-ad-stack/","https://openai.com/index/our-approach-to-advertising-and-expanding-access/","https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/"]
KEYWORDS = ["ChatGPT Ads expands to Southeast Asia and Taiwan","ChatGPT ads Southeast Asia 2026","ChatGPT advertising Taiwan","ChatGPT ads Indonesia","ChatGPT ads Malaysia","ChatGPT ads Philippines","ChatGPT ads Singapore","ChatGPT ads Thailand","ChatGPT ads Vietnam","ChatGPT Ads Manager availability","how to advertise on ChatGPT","ChatGPT Free Go ads","OpenAI ads expansion September 2026","ChatGPT advertising privacy"]
FAQ = [["Which seven countries were added to ChatGPT Ads in September 2026?","OpenAI's September 23, 2026 release names Indonesia, Malaysia, the Philippines, Singapore, Thailand, Vietnam and Taiwan."],["When did ChatGPT Ads launch in Southeast Asia and Taiwan?","The seven-market rollout was announced September 23, 2026 and began rolling out from that date. Availability for individual advertisers and eligible users depends on account and regional conditions."],["How many countries have ChatGPT Ads now?","The September 23 announcement stated more than 60 countries. On October 21, 2026, OpenAI announced a further expansion to 89 countries. Use the current Ads Manager country list for self-service account availability."],["Which ChatGPT plans may show ads?","Eligible adults on ChatGPT Free and Go may see ads. Plus, Pro, Business, Enterprise and Edu do not show ads. A reduced-limits ads-free Free option is available where supported."],["Can advertisers read ChatGPT conversations?","No. OpenAI says conversations and memories are not shared with advertisers and user data is not sold. The separate ad-serving system can use conversation context internally to select relevant ads, subject to user controls."],["Do sponsored links change ChatGPT answers?","No. OpenAI says its ad-serving system is separate from response generation, and sponsored placements are clearly labeled and separate from organic answers."],["Can businesses buy ChatGPT Ads in Singapore, Indonesia or Taiwan?","OpenAI lists all seven September launch markets in its current Ads Manager self-service availability reference. The advertiser's billed legal entity and account eligibility must meet the current listed requirements."],["How much do ChatGPT Ads cost?","OpenAI documents impression-based and valid-click buying, with bids and auction outcomes affecting price. There is no universal guaranteed cost per click; check Ads Manager for current conditions."],["Are ChatGPT Ads the same as paid inclusion in an answer?","No. An ad is a separately labeled sponsored placement. Its appearance does not mean the ChatGPT answer was bought, influenced or that the advertiser is endorsed."],["How should a small business test ChatGPT advertising?","SXF recommends starting with a defined audience and country, clear value proposition, landing-page validation, tracking, a capped budget, conversion measurement and scrutiny of qualified outcomes, not just ad clicks."]]
BRIEF = r'''<section class="signal-layout shell">
<article class="signal-brief">
<p class="eyebrow">SXF VERIFIED ADVERTISING BRIEF · UPDATED NOVEMBER 8, 2026</p>
<p class="signal-summary"><strong>OpenAI expanded ChatGPT Ads to seven Asian markets on September 23, 2026:</strong> Indonesia, Malaysia, the Philippines, Singapore, Thailand, Vietnam and Taiwan. The rollout initially took ChatGPT advertising to <strong>more than 60 countries</strong>. A later OpenAI announcement on <strong>October 21</strong> increased the published total to <strong>89 countries</strong>. Ads may appear to eligible adults on the <strong>Free and Go</strong> plans—not Plus, Pro, Business, Enterprise or Edu.</p>
<div class="signal-context"><span>WHAT ADVERTISERS NEED TO KNOW</span><p>Eligible businesses can work with OpenAI's Ads Solutions team, agency or technology partners, or use Ads Manager self-service where the billed legal entity qualifies. Country availability for buying ads is not the same as a guarantee that a specific user will see them.</p></div>
<div class="signal-context"><span>SXF'S CORE ANALYSIS</span><p>ChatGPT advertising is a <strong>conversation-intent channel</strong>, not paid placement inside a generated answer. The strategic challenge is matching useful creative to real decisions while preserving user trust, respecting local market context and proving campaign value beyond click counts.</p></div>
</article>
<aside class="source-card"><span class="source-card-label">PRIMARY REPORT</span><strong>OpenAI · September 23, 2026</strong><p>Original seven-market expansion; November 8 verification incorporates October follow-ups and live product documentation.</p>
<a href="https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/" target="_blank" rel="noopener noreferrer">Read the original OpenAI announcement ↗</a><p><a href="https://openai.com/index/chatgpt-ads-expands-26-new-countries/" target="_blank" rel="noopener noreferrer">October expansion: 89 countries ↗</a></p>
<p><small>Sources verified November 8, 2026 · No independent SXF ad campaign test claimed.</small></p></aside>
</section>'''
BODY = r'''<section class="signal-deep-dive shell sea-ads" data-sxf-chatgpt-ads-sea="2026-11-08" aria-labelledby="sea-ads-overview">
<div class="intel-section-head"><div><p class="eyebrow">SXF / ORIGINAL AD TECH ANALYSIS</p><h2 id="sea-ads-overview">ChatGPT Ads in Southeast Asia and Taiwan: rollout, plans, advertiser access and implications.</h2></div><span>Verified November 8, 2026</span></div>
<p class="sea-intro">If you searched <strong>“ChatGPT Ads expands to Southeast Asia and Taiwan”</strong>, here is the precise answer: on September 23, 2026 OpenAI announced advertising access for <strong>Indonesia, Malaysia, the Philippines, Singapore, Thailand, Vietnam and Taiwan</strong>. The announcement marked the arrival of a conversational advertising product in seven additional markets. It did not mean that advertisers can pay to change ChatGPT's answers or read customers' private messages. This SXF analysis documents the launch, eligibility, privacy architecture, buying mechanics and a practical campaign evaluation method, distinguishing original September details from October changes. <a href="https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/" target="_blank" rel="noopener noreferrer">Official launch statement</a>.</p>
<div class="sea-facts" aria-label="Release facts"><div><span>REGIONAL ANNOUNCEMENT</span><strong>September 23, 2026</strong><small>Seven Southeast Asian and Taiwan markets</small></div><div><span>COUNTRIES ADDED</span><strong>7 markets</strong><small>Indonesia · Malaysia · Philippines · Singapore · Thailand · Vietnam · Taiwan</small></div><div><span>GLOBAL COVERAGE</span><strong>89 countries</strong><small>OpenAI's newer October 21 figure, not September's 60+</small></div><div><span>USER ELIGIBILITY</span><strong>Free + Go</strong><small>Eligible users; paid ad-free plans excluded</small></div></div>
<nav class="sea-toc" aria-label="Contents"><strong>Jump to</strong><a href="#sea-countries">Seven markets</a><a href="#sea-timeline">Dates</a><a href="#sea-plans">Plans</a><a href="#sea-advertisers">Advertisers</a><a href="#sea-cost">Pricing</a><a href="#sea-privacy">Privacy</a><a href="#sea-technology">How it works</a><a href="#sea-sxf">SXF analysis</a><a href="#sea-faq">FAQ</a></nav>

<section id="sea-countries">
<h2>Which Southeast Asian countries and territories received ChatGPT Ads?</h2>
<p>OpenAI's <strong>September 23, 2026</strong> news post names six Southeast Asian countries and Taiwan. The announcement also references earlier Asia-Pacific launches in Australia, New Zealand, Japan, South Korea and India. The seven named additions were a new geographic advertising rollout, not evidence that any individual ChatGPT account automatically began seeing a sponsored card that day. <a href="https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/" target="_blank" rel="noopener noreferrer">Launch list from OpenAI</a>.</p>
<div class="sea-scroll"><table class="sea-table"><thead><tr><th>Market</th><th>September 23 announcement</th><th>What a business should verify</th></tr></thead><tbody>
<tr><th>Indonesia</th><td>Rollout began</td><td>Ads Manager legal-entity eligibility, language and local offer</td></tr>
<tr><th>Malaysia</th><td>Rollout began</td><td>Billing entity, local creative and landing-page fit</td></tr>
<tr><th>Philippines</th><td>Rollout began</td><td>Audience relevance, conversion tracking and platform support</td></tr>
<tr><th>Singapore</th><td>Rollout began</td><td>Competitive bids, qualified leads and business eligibility</td></tr>
<tr><th>Thailand</th><td>Rollout began</td><td>Language, purchase path and advertiser restrictions</td></tr>
<tr><th>Vietnam</th><td>Rollout began</td><td>Local communication and measurable campaign outcomes</td></tr>
<tr><th>Taiwan</th><td>Rollout began</td><td>Correct local targeting and creative clarity</td></tr>
</tbody></table></div>
<p>OpenAI's updated <a href="https://help.openai.com/en/articles/20001245-ads-manager-availability" target="_blank" rel="noopener noreferrer">Ads Manager Availability</a> page lists these seven markets as available for self-service as of SXF's review. The relevant requirement is the country where the <strong>advertising and billed legal entity</strong> is based. Eligibility to open a self-service account, permission to target an audience and the eligibility of a ChatGPT user to see ads are three different things. A campaign must still pass billing, content review and delivery checks.</p>
<h3>Does a regional launch mean ads appear in every conversation?</h3>
<p>No. OpenAI's user documentation describes a gradual rollout to eligible Free and Go accounts. Ad delivery depends on user eligibility, location, relevance, policy and whether an appropriate sponsored placement is available. An advertiser can be active in a country without having an impression in every conversation, and a user may see no ad at all. <a href="https://help.openai.com/en/articles/20001047-ads-in-chatgpt" target="_blank" rel="noopener noreferrer">Official user FAQ</a>.</p>
</section>

<section id="sea-timeline">
<h2>What happened on September 23—and how did the worldwide rollout change?</h2>
<p><strong>Do not confuse a historical headline with the latest published total.</strong> September's announcement said ChatGPT Ads had expanded to more than 60 countries. OpenAI then announced another 26-market expansion on October 21, bringing its published total to <strong>89 countries</strong>. This article keeps the original seven-market date intact while recording the later change so a search result does not appear stale. <a href="https://openai.com/index/chatgpt-ads-expands-26-new-countries/" target="_blank" rel="noopener noreferrer">October 21 OpenAI update</a>.</p>
<div class="sea-scroll"><table class="sea-table"><thead><tr><th>Date</th><th>OpenAI milestone</th><th>How to read it</th></tr></thead><tbody>
<tr><th>February 9, 2026</th><td>U.S. ChatGPT ads testing began</td><td>Start of eligible Free/Go ad tests</td></tr>
<tr><th>August 31, 2026</th><td>Over 40 countries; $1B annualized revenue run rate</td><td>Annualized rate is not the same as $1B collected revenue</td></tr>
<tr><th>September 23, 2026</th><td>Seven Asia markets; more than 60 countries overall</td><td>Original article event and historical coverage count</td></tr>
<tr><th>October 21, 2026</th><td>26 additional countries; total reached 89</td><td>More recent published global count</td></tr>
</tbody></table></div>
<p>OpenAI also said <strong>more than 100,000 advertisers</strong> had used the platform by the October announcement. That is a cumulative advertiser-adoption statement, not the number of businesses advertising on any single day or in any one Southeast Asian country. Neither that number nor the August revenue run rate discloses local campaign return on ad spend. Sources: <a href="https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/" target="_blank" rel="noopener noreferrer">August milestone</a> and <a href="https://openai.com/index/chatgpt-ads-expands-26-new-countries/" target="_blank" rel="noopener noreferrer">October expansion</a>.</p>
</section>

<section id="sea-plans">
<h2>Who sees ChatGPT ads? Free, Go, Plus, Pro and Business plans</h2>
<p>According to OpenAI's current help center, <strong>eligible Free and Go users may see ads</strong>. Plus, Pro, Business, Enterprise and Edu accounts do not see them. Accounts identified as belonging to users under 18 do not receive ads. Eligible Free accounts in supported markets can choose a <strong>no-ads Free option with lower usage limits and reduced tool access</strong>; turning off ad personalization alone is not the same as removing ads. <a href="https://help.openai.com/en/articles/20001047-ads-in-chatgpt" target="_blank" rel="noopener noreferrer">OpenAI's current eligibility and controls</a>.</p>
<div class="sea-scroll"><table class="sea-table"><thead><tr><th>ChatGPT access type</th><th>Ads shown?</th><th>Important nuance</th></tr></thead><tbody>
<tr><th>Free</th><td>May appear</td><td>Eligible account and region; reduced-limits ads-free choice where offered</td></tr>
<tr><th>Go</th><td>May appear</td><td>Eligible account and region; not identical to Plus</td></tr>
<tr><th>Plus or Pro</th><td>No</td><td>Paid ad-free subscriptions</td></tr>
<tr><th>Business, Enterprise or Edu</th><td>No</td><td>Ad-free organizational account types</td></tr>
<tr><th>Account identified as under 18</th><td>No</td><td>Age safeguards apply independently of plan</td></tr>
</tbody></table></div>
<p>Sponsored units are labeled and appear separately from ChatGPT's answer. OpenAI's current documentation also describes a visual multi-image format being tested during image generation; that format is not a reason to infer that September's initial Asian launch offered every creative feature on day one.</p>
</section>

<section id="sea-advertisers">
<h2>How can businesses advertise on ChatGPT in Singapore, Taiwan and Southeast Asia?</h2>
<p>OpenAI's regional announcement identifies its <strong>Ads Solutions team</strong>, agency partners such as dentsu, Havas Media, Omnicom Media, Publicis Groupe and WPP, technology partners, and an <strong>Ads Manager self-service route for eligible businesses</strong>. These are alternative access paths, not a promise that every small advertiser qualifies without account verification. Interested businesses can start from the official <a href="https://ads.openai.com/" target="_blank" rel="noopener noreferrer">Ads Manager entry point</a> and consult the <a href="https://help.openai.com/en/articles/20001245-ads-manager-availability" target="_blank" rel="noopener noreferrer">current country availability</a>.</p>
<ol class="sea-steps">
<li><strong>Confirm the legal advertiser market.</strong> Check where the billed legal entity is established; the advertiser eligibility rule is not simply where a customer lives.</li>
<li><strong>Select a specific objective.</strong> Decide whether you want relevant awareness, qualified visits or measurable conversion actions before drafting creative.</li>
<li><strong>Match market language and intent.</strong> Create clear descriptions of whom a product helps and when, with local currency and landing pages appropriate to each country.</li>
<li><strong>Build honest creative.</strong> Use benefit-focused headlines, an accurate landing page and compliant images. Avoid unsupported claims or copying a competitor's brand.</li>
<li><strong>Set budget and measurement.</strong> Confirm the buying objective, max bid, tracking parameters, eligible conversion events and reporting fields.</li>
<li><strong>Check approval and optimize.</strong> Ads and accounts must pass review; learn from actual qualified conversions rather than assuming a campaign will serve because the country appears on a list.</li>
</ol>
<p>OpenAI's <a href="https://help.openai.com/en/articles/20001212-creating-ads-for-chatgpt-ads" target="_blank" rel="noopener noreferrer">official creative guidance</a> recommends messages tailored to conversational intent. It explicitly distinguishes ChatGPT ad matching from a classic exact-keyword search ad: advertiser-provided context hints help relevance but do not guarantee a particular query placement. Read <a href="/guides/best-ai-agents-for-marketing/">SXF's marketing agent guide</a> for surrounding workflow automation, not as a replacement for OpenAI's platform rules.</p>
<h3>What role does Shopee play in the announcement?</h3>
<p>OpenAI included comments from Shopee executive Peggy Zhu about expanding its OpenAI collaboration across Southeast Asia and Taiwan. That illustrates commerce interest in connecting discovery with relevant services, but it is a <strong>partner statement</strong>, not a published Shopee campaign case study with conversions, incremental sales or audited ROI. SXF does not infer performance metrics from the quotation. <a href="https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/" target="_blank" rel="noopener noreferrer">OpenAI launch note</a>.</p>
</section>

<section id="sea-cost">
<h2>How much do ChatGPT Ads cost? CPM, CPC and measurement</h2>
<p>OpenAI's current advertiser help describes <strong>impression-based and valid-click buying</strong>, with campaign objectives such as views, clicks and supported conversions. Advertisers provide bids and campaign settings; eligibility, relevance and auction outcomes determine whether the sponsored placement is served and the amount charged. This is not a fixed price per lead or a guaranteed cost per ChatGPT answer. <a href="https://help.openai.com/en/articles/20001207-ads-in-chatgpt-the-basics" target="_blank" rel="noopener noreferrer">Official advertiser basics</a>.</p>
<div class="sea-scroll"><table class="sea-table"><thead><tr><th>Metric</th><th>What it measures</th><th>What it does not prove</th></tr></thead><tbody>
<tr><th>Impressions</th><td>Sponsored placements delivered or viewed as defined by reporting</td><td>That a product was noticed or purchased</td></tr>
<tr><th>Clicks / CTR</th><td>Visits and click-through relative to impressions</td><td>That a visitor is qualified or completed a purchase</td></tr>
<tr><th>CPC / CPM</th><td>Cost per valid click or thousand impressions</td><td>A universal guaranteed rate across countries and categories</td></tr>
<tr><th>Conversions</th><td>Configured actions attributed under the platform's measurement rules</td><td>Causal incremental sales without a proper test design</td></tr>
<tr><th>Cost per qualified outcome</th><td>Spend divided by independently verified sales or eligible leads</td><td>Long-term profit unless margins and follow-on value are considered</td></tr>
</tbody></table></div>
<p>Conversion measurement can use the <strong>OpenAI Pixel, Conversions API or both</strong>, subject to applicable consent and privacy requirements. Attribution windows and modeled conversions can affect reporting. For initial analytics comparison, landing pages can retain UTM parameters, but advertisers should distinguish measured attribution from causation. Official sources: <a href="https://help.openai.com/en/articles/20001409-conversion-measurement" target="_blank" rel="noopener noreferrer">conversion measurement</a> and <a href="https://help.openai.com/en/articles/20001207-ads-in-chatgpt-the-basics" target="_blank" rel="noopener noreferrer">buying and reporting</a>.</p>
<div class="sea-note"><strong>SXF cost warning:</strong> Do not quote a fixed “ChatGPT Ads CPM” or promise guaranteed conversions based on the launch story. Compare actual market and account bidding conditions, measure revenue or valid leads, and check the platform's up-to-date reporting definitions.</div>
</section>

<section id="sea-privacy">
<h2>Do ChatGPT Ads expose private conversations or influence answers?</h2>
<p>OpenAI explicitly states that <strong>advertisers do not receive people's ChatGPT conversations, memories, chat histories or personal information</strong>, and that user data is not sold to advertisers. Its advertising systems can, however, process <strong>the current conversation context inside ChatGPT</strong> to find a relevant sponsored placement. When ad personalization is enabled, certain signals from broader experience may inform relevance. This distinction matters: contextual matching inside the ad system is not the same as sharing chat transcripts with the company buying the advertisement. <a href="https://help.openai.com/en/articles/20001047-ads-in-chatgpt" target="_blank" rel="noopener noreferrer">User privacy FAQ</a>.</p>
<p>Advertising does <strong>not</strong> influence ChatGPT's generated answers. An advertisement is a separate, labeled paid placement and does not mean OpenAI endorses that brand. OpenAI's ad-serving engineering post describes a separate retrieval, ranking and auction system running alongside answer generation rather than modifying it. <a href="https://openai.com/index/building-chatgpt-ad-stack/" target="_blank" rel="noopener noreferrer">Technical architecture</a>.</p>
<h3>What can a user control?</h3>
<p>Eligible users can open ChatGPT <strong>Settings → Ads controls</strong> to manage personalization, view ad-related information and clear ads data. On a displayed ad, the menu can offer <em>About this ad</em>, <em>Hide this ad</em> and <em>Report this ad</em>. Turning off personalization does not necessarily eliminate contextual ads. The Free ads-free option reduces message and feature limits where offered; upgrading to an ad-free subscription is another route. OpenAI says ads are not shown in Temporary Chats. <a href="https://help.openai.com/en/articles/20001047-ads-in-chatgpt" target="_blank" rel="noopener noreferrer">Official controls</a>.</p>
<p><strong>SXF trust assessment:</strong> Three boundaries should be verified independently: who may use conversation signals inside the serving system, what advertisers receive, and whether response generation remains separate. The documentation is evidence of OpenAI's stated product design and policies, not an independent SXF security audit. Read the <a href="/guides/ai-agent-security/">SXF AI security guide</a> for broader data-boundary principles.</p>
</section>

<section id="sea-technology">
<h2>How does ChatGPT choose sponsored placements?</h2>
<p>OpenAI's October 21 engineering explanation describes a <strong>separate ads service</strong> that interprets evolving conversational intent, retrieves relevant possible ads, filters for safety and eligibility, assesses relevance and engagement, and passes qualified candidates through an auction. The ad service can return no advertisement when no suitable placement exists. It does not replace or rewrite the answer model's reasoning. <a href="https://openai.com/index/building-chatgpt-ad-stack/" target="_blank" rel="noopener noreferrer">Read OpenAI's ad stack engineering report</a>.</p>
<div class="sea-flow"><div><span>01 / INTENT</span><strong>Understand the user goal</strong><p>A longer conversation can reveal constraints missing in a single search term.</p></div><div><span>02 / ELIGIBILITY</span><strong>Filter by policy and audience</strong><p>Account, location and brand-safety constraints can exclude ads.</p></div><div><span>03 / QUALITY</span><strong>Assess usefulness</strong><p>Creative and landing-page relevance help decide which candidates qualify.</p></div><div><span>04 / AUCTION</span><strong>Select a sponsored unit</strong><p>Bids and quality-adjusted selection determine eligible placements.</p></div><div><span>05 / SEPARATION</span><strong>Show it outside the answer</strong><p>A labeled ad is not part of ChatGPT's organic response.</p></div></div>
<p>The current product format and targeting options can evolve. An advertiser cannot assume that supplying a conversation keyword forces a sponsored placement when a specific phrase is mentioned. OpenAI describes context hints rather than a guaranteed exact-match keyword mechanism. <a href="https://help.openai.com/en/articles/20001212-creating-ads-for-chatgpt-ads" target="_blank" rel="noopener noreferrer">Advertiser creative and targeting guidance</a>.</p>
</section>

<section id="sea-sxf">
<h2>SXF analysis: conversational intent is the opportunity—and the risk</h2>
<p><strong>Our editorial view:</strong> ChatGPT Ads represent a new type of discovery channel because the user's needs may become clearer over multiple conversational turns. A traveler might start with an open-ended destination question and only later mention a family budget, mobility needs or a location. An ad relevant to that refined goal could be useful, while an irrelevant placement could be particularly disruptive because the user is engaged in an advisory dialogue rather than browsing a conventional results page.</p>
<p>For marketers in Indonesia, Malaysia, the Philippines, Singapore, Thailand, Vietnam and Taiwan, the advantage is not merely regional reach. It is the possibility of showing a concrete offer during evaluation, when people compare options and refine requirements. Yet that is a <strong>plausible strategic opportunity</strong>, not measured proof of better conversion rates than Google Search, social networks or retailer media. The original OpenAI announcement does not disclose country-level CPM, cost per acquisition, performance or net incremental sales.</p>
<h3>Original SXF six-check campaign evaluation framework</h3>
<div class="sea-grid"><article><span>01 / INTENT FIT</span><h3>Is this a real decision moment?</h3><p>Choose a clear user goal your offer can solve. Avoid generic ad copy that matches no useful moment.</p></article><article><span>02 / LOCAL RELEVANCE</span><h3>Does the market experience fit?</h3><p>Check language, currency, fulfillment, support availability and region-specific landing pages.</p></article><article><span>03 / MESSAGE TRUTH</span><h3>Can every claim be verified?</h3><p>Use accurate titles, creative and destinations rather than exaggerated outcomes.</p></article><article><span>04 / USER TRUST</span><h3>Could the placement feel intrusive?</h3><p>Respect brand-safety controls, sensitive-topic exclusions and consumer feedback.</p></article><article><span>05 / ECONOMICS</span><h3>What is the cost of a qualified result?</h3><p>Track verified leads, sales, gross margin and total campaign spend—not just CTR.</p></article><article><span>06 / INCREMENTALITY</span><h3>Did advertising cause the improvement?</h3><p>Compare controlled markets, time periods or eligible cohorts where a suitable experimental setup exists.</p></article></div>
<p>This six-check protocol is <strong>an original SXF recommendation</strong>, not a campaign experiment conducted by SXF and not a test of OpenAI's private delivery algorithms. It helps distinguish the platform's claimed relevance features from outcomes that an advertiser must prove with its own data.</p>
<h3>What would a useful pilot look like?</h3>
<p>Consider a hypothetical Singapore-based software company. Rather than targeting vague terms like “best software,” it might run two clearly different creatives focused on a verified buyer use case, use a matching localized landing page and measure qualified demo requests. It should exclude invalid leads, review spend and compare against a meaningful baseline. This is an illustrative research design, not a claim about real ChatGPT ad placements or expected returns.</p>
<p>Compared with classic search ads, conversation-driven selection may respond to evolving user constraints. Compared with influencer or social advertising, relevance may stem more from a stated active need. Neither comparison implies automatic superiority; the result depends on creative quality, inventory, delivery, trust and conversion measurement. For related reading see <a href="/research/google-ai-mode-vs-chatgpt-search/">SXF's AI search comparison</a> and <a href="/guides/best-ai-agents-for-marketing/">AI agents for marketing</a>.</p>
</section>

<section id="sea-faq"><h2>Frequently asked questions about ChatGPT Ads in Southeast Asia and Taiwan</h2>
<h3>Which countries launched ChatGPT Ads in September 2026?</h3><p>Indonesia, Malaysia, the Philippines, Singapore, Thailand, Vietnam and Taiwan.</p>
<h3>When did ChatGPT advertising arrive in these markets?</h3><p>OpenAI announced the rollout on September 23, 2026. Individual advertiser and user eligibility may depend on further conditions.</p>
<h3>Are ChatGPT Ads now available in 60 or 89 countries?</h3><p>More than 60 was the historical September figure. The subsequent October 21, 2026 OpenAI release announced 89 countries in total. The live Ads Manager availability list is the reference for self-service sign-ups.</p>
<h3>Do Free and Go users get advertisements?</h3><p>Eligible adults on Free and Go may see them. Plus, Pro, Business, Enterprise and Edu accounts remain ad-free.</p>
<h3>Do advertisers see my conversations?</h3><p>No. OpenAI says advertisers cannot read your chats, memory or history; the separate ad system may use conversation context internally for relevance.</p>
<h3>Can businesses advertise in Singapore, the Philippines and Taiwan?</h3><p>OpenAI's live Ads Manager country list includes the seven launch markets. Eligibility depends on the advertiser's billed legal entity and completion of required account checks.</p>
<h3>Can I switch off ads in ChatGPT?</h3><p>Eligible Free users may select an ads-free option with reduced usage limits; paid ad-free plans are also available. Disabling personalization alone does not remove contextual ads.</p>
<h3>Can companies pay ChatGPT to change its answers?</h3><p>No. Sponsored placements are separately labeled, and OpenAI says the ads system cannot alter ChatGPT's generated responses.</p>
<h3>What does ChatGPT Ads cost for advertisers?</h3><p>OpenAI supports impression and valid-click buying with bids and auction pricing. Real costs vary by campaign and market; no universal cost per click is guaranteed.</p>
</section>

<section id="sea-sources"><h2>Official sources, latest status and SXF methodology</h2>
<p><strong>Source review: November 8, 2026.</strong> This report retains the original September 23 launch date and uses the October 21 announcement for the more recent 89-market count. OpenAI's official documentation describes its current functionality, user controls and advertiser eligibility. SXF's campaign evaluation framework is editorial analysis, not an independently audited campaign experiment. Availability, prices and ad formats can change.</p>
<ol class="sea-sources">
<li><a href="https://openai.com/index/chatgpt-ads-expands-southeast-asia-taiwan/" target="_blank" rel="noopener noreferrer">OpenAI, September 23 — ChatGPT Ads expands to Southeast Asia and Taiwan</a>. Seven markets, original launch and partner comments.</li>
<li><a href="https://openai.com/index/chatgpt-ads-expands-26-new-countries/" target="_blank" rel="noopener noreferrer">OpenAI, October 21 — Ads expands to 26 more countries</a>. 89-country global count and cumulative advertiser adoption.</li>
<li><a href="https://help.openai.com/en/articles/20001245-ads-manager-availability" target="_blank" rel="noopener noreferrer">OpenAI Help — Ads Manager Availability</a>. Self-service access by billed legal-entity country.</li>
<li><a href="https://help.openai.com/en/articles/20001047-ads-in-chatgpt" target="_blank" rel="noopener noreferrer">OpenAI Help — Ads in ChatGPT</a>. Eligible plans, user privacy, ad settings and age protections.</li>
<li><a href="https://help.openai.com/en/articles/20001207-ads-in-chatgpt-the-basics" target="_blank" rel="noopener noreferrer">OpenAI Help — Ads in ChatGPT: The Basics</a>. Format, billing, targeting and reporting.</li>
<li><a href="https://help.openai.com/en/articles/20001212-creating-ads-for-chatgpt-ads" target="_blank" rel="noopener noreferrer">OpenAI Help — Creating ads for ChatGPT Ads</a>. Context hints and ad copy guidance.</li>
<li><a href="https://help.openai.com/en/articles/20001409-conversion-measurement" target="_blank" rel="noopener noreferrer">OpenAI Help — Conversion Measurement</a>. Pixel, Conversions API and attribution conditions.</li>
<li><a href="https://openai.com/index/building-chatgpt-ad-stack/" target="_blank" rel="noopener noreferrer">OpenAI Engineering, October 21 — Ad-serving architecture</a>. Separate selection and answer generation.</li>
<li><a href="https://openai.com/index/our-approach-to-advertising-and-expanding-access/" target="_blank" rel="noopener noreferrer">OpenAI — Advertising principles</a>. Answer independence, privacy and choice.</li>
<li><a href="https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/" target="_blank" rel="noopener noreferrer">OpenAI, August 31 — Advertising growth milestone</a>. Historical annualized revenue run rate.</li>
</ol>
<p><strong>Related SXF coverage:</strong> <a href="/signals/chatgpt-ads-expands-to-26-new-countries-as-over-100-000-advertisers-ha-74fcf21/">October ChatGPT Ads global expansion</a> · <a href="/guides/best-ai-agents-for-marketing/">AI agents for marketing</a> · <a href="/research/google-ai-mode-vs-chatgpt-search/">Google AI Mode vs ChatGPT Search</a> · <a href="/topics/openai/">OpenAI updates</a> · <a href="/signals/">All SXF signals</a>.</p>
</section>
</section>'''
CSS = r'''<style id="sxf-sea-chatgpt-ads-styles">
.sea-ads-page .sea-ads{margin:34px auto 56px}.sea-ads section{margin:43px 0;max-width:1030px;scroll-margin-top:85px}.sea-ads p,.sea-ads li{line-height:1.82}.sea-ads a{text-decoration:underline;text-underline-offset:3px}.sea-ads section>h2{font-size:clamp(1.42rem,2.35vw,2.04rem);line-height:1.3;margin:0 0 17px}.sea-ads h3{font-size:1.12rem;line-height:1.44;margin:24px 0 10px}.sea-intro{font-size:1.1rem;max-width:940px;line-height:1.85!important;color:#c6d9e9}.sea-facts,.sea-grid,.sea-flow{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:25px 0}.sea-facts>div,.sea-grid>article,.sea-flow>div{padding:19px;border:1px solid rgba(134,190,226,.26);border-radius:16px;background:linear-gradient(135deg,rgba(72,123,164,.16),rgba(8,16,29,.47))}.sea-facts span,.sea-grid span,.sea-flow span{display:block;font-size:.75rem;letter-spacing:.075em;color:#97ebdb;font-weight:800}.sea-facts strong,.sea-flow strong{display:block;color:#eef7ff;font-size:1.05rem;margin:8px 0 5px}.sea-facts small{color:#b4c8d8;line-height:1.5}.sea-grid h3{margin:9px 0}.sea-grid p,.sea-flow p{margin:0}.sea-toc{display:flex;flex-wrap:wrap;gap:9px;padding:19px 20px;border:1px solid rgba(136,187,217,.27);border-radius:16px;background:rgba(29,61,83,.15);margin:23px 0}.sea-toc strong{width:100%;margin-bottom:4px}.sea-toc a{border:1px solid rgba(130,196,213,.27);border-radius:26px;padding:6px 12px;text-decoration:none}.sea-scroll{overflow-x:auto;border:1px solid rgba(140,187,224,.27);border-radius:15px;margin:23px 0}.sea-table{width:100%;min-width:720px;border-collapse:collapse;font-size:.91rem}.sea-table th,.sea-table td{padding:13px 16px;border-bottom:1px solid rgba(143,188,223,.18);text-align:left;vertical-align:top;line-height:1.6}.sea-table thead th{background:#172d42;color:#e5f3ff}.sea-table tbody th{color:#a8efe1}.sea-note{background:rgba(92,175,165,.1);border-left:3px solid #99e8db;border-radius:0 14px 14px 0;padding:20px 22px;margin:23px 0;line-height:1.8}.sea-steps,.sea-sources{padding-left:1.5rem}.sea-steps li,.sea-sources li{margin:12px 0}.sea-ads-page a:focus-visible{outline:2px solid #91eee0;outline-offset:4px}@media(max-width:760px){.sea-facts,.sea-grid,.sea-flow{grid-template-columns:1fr}.sea-table{min-width:600px}.sea-ads section{margin:34px 0}}
</style>'''

def enrich(page: str) -> str:
    marker = 'data-sxf-chatgpt-ads-sea="2026-11-08"'
    if marker in page:
        return page
    required = ['class="intel-page signal-page"',
        '<h1>ChatGPT Ads expands to Southeast Asia and Taiwan</h1>',
        '<section class="signal-layout shell">',
        '<section class="signal-taxonomy shell">',
        '<meta name="twitter:card" content="summary" />']
    if any(s not in page for s in required):
        raise ValueError("ChatGPT Ads base signal template changed")
    page = page.replace('class="intel-page signal-page"',
        'class="intel-page signal-page sea-ads-page"', 1)
    page, n = re.subn(r'<title>.*?</title>', '<title>'+escape(TITLE)+'</title>',
                      page, count=1, flags=re.S)
    if n != 1:
        raise ValueError("Missing title")
    for key, value in [('description', DESCRIPTION), ('og:title', TITLE),
        ('og:description', DESCRIPTION), ('twitter:title', TITLE),
        ('twitter:description', DESCRIPTION)]:
        pat = r'(<meta (?:property|name)="' + re.escape(key) + r'" content=")[^"]*(" />)'
        page, n = re.subn(pat,
            lambda m: m.group(1)+escape(value, quote=True)+m.group(2),
            page, count=1)
        if n != 1:
            raise ValueError("Missing SEO metadata: "+key)
    page = page.replace('<meta name="twitter:card" content="summary" />',
        '<meta property="og:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />'
        '<meta property="og:image:alt" content="SXF analysis of ChatGPT Ads in Southeast Asia and Taiwan" />'
        '<meta name="twitter:card" content="summary_large_image" />'
        '<meta name="twitter:image" content="https://sxf.si/assets/og/sxf-ai-social.webp" />', 1)
    stylesheet = '<link rel="stylesheet" href="/intelligence.css" />'
    if stylesheet not in page:
        raise ValueError("Missing site stylesheet")
    page = page.replace(stylesheet, stylesheet+'\n'+CSS, 1)
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("Missing JSON-LD")
    schema = json.loads(match.group(1))
    g = schema['@graph']
    if len(g) != 3:
        raise ValueError("Unexpected article schema")
    g[0].update(name=TITLE, description=DESCRIPTION,
        breadcrumb={'@id': CANONICAL+'#breadcrumb'})
    g[1].update(headline=H1, description=DESCRIPTION,
        dateModified='2026-11-08', keywords=KEYWORDS, citation=SOURCES,
        isBasedOn=SOURCES[0], about=[
            {'@type':'Thing','name':'ChatGPT Ads'},
            {'@type':'Thing','name':'Southeast Asia advertising'},
            {'@type':'Thing','name':'Taiwan advertising'},
            {'@type':'Organization','name':'OpenAI'}])
    g[2]['itemListElement'].append({'@type':'ListItem','position':4,
        'name':'ChatGPT Ads Southeast Asia and Taiwan','item':CANONICAL})
    g.append({'@type':'FAQPage','@id':CANONICAL+'#faq',
        'mainEntity':[{'@type':'Question','name':q,
            'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]})
    page = page[:match.start()] + '<script type="application/ld+json">' + (
        json.dumps(schema, ensure_ascii=False, separators=(',', ':'))) + (
        '</script>') + page[match.end():]
    page = page.replace('<h1>ChatGPT Ads expands to Southeast Asia and Taiwan</h1>',
        '<h1>'+escape(H1)+'</h1>', 1)
    page, n = re.subn(r'<section class="signal-layout shell">.*?</section>',
        lambda _:BRIEF, page, count=1, flags=re.S)
    if n != 1:
        raise ValueError("Signal brief missing")
    page = page.replace('<section class="signal-taxonomy shell">',
        BODY+'\n<section class="signal-taxonomy shell">', 1)
    if page.count(marker) != 1:
        raise ValueError("Editorial marker missing or duplicated")
    for src in SOURCES:
        if src not in page:
            raise ValueError("Unlinked source: "+src)
    return page
