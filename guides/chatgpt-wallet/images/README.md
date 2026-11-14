# ChatGPT Wallet — image delivery specification

The article HTML already references two image paths. These files are intentionally **not** committed yet.

1. `/guides/chatgpt-wallet/images/chatgpt-wallet-payment-flow.webp`
   - 1600 × 900 (16:9), WebP, ideally below 250 KB.
   - SXF-designed editorial diagram: user shopping request → dot agent selects merchant/cart → exact cart + total reviewed → user security confirmation → network-issued substitute payment credentials → merchant authorization + order fulfillment.
   - Distinguish existing user-approved workflow from future spending-limit delegation; no claim of automatic purchasing today.
   - Dark SXF editorial palette, lime accent, plain English labels. Provide readable type at mobile sizes.

2. `/guides/chatgpt-wallet/images/agentic-commerce-market-shift.webp`
   - 1600 × 900 (16:9), WebP, ideally below 250 KB.
   - SXF analytical two-lane diagram: traditional search → ad/product page → manual checkout versus agent requirement → compare verifiable offers → human-approved wallet payment → merchant fulfillment.
   - Clearly label the agentic path as a market scenario, **not observed market share**. Show merchant inventory, merchant-of-record functions, and card network retaining their roles.

## Integration notes

- Both `<img>` elements and exact URLs are already present in `index.html`.
- Before assets are uploaded the page shows readable, branded fallback panels instead of broken image icons.
- After uploading both assets, update `og:image` and `twitter:image` to the final first image, if it has a good social-crop composition. Then optionally add genuine `ImageObject` entities to the JSON-LD.
- Do not mark an image as a published structured-data image or add it to the sitemap before the actual file exists.
- Preserve the image ALT text and factual distinction between launched capabilities and SXF future scenarios.
