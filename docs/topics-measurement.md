# SXF Topics measurement contract

The Topics page is a discovery directory, not a Signals feed.

## Events

The route `/topics/` and selected Guides and Research pages load `/assets/topic-navigation.js`.
Clicks on internal destination routes within the Topics content or contextual back-link areas emit a
`sxf:topic-navigation` CustomEvent. When an analytics tag already initialized
`window.dataLayer`, the script also pushes `sxf_topic_navigation`.

Fields: `topic_source` (`topics_hub` or `related_context`), `topic_origin`,
`topic_destination`. Header/footer clicks and fragment-scroll clicks are not counted.

The script sets no cookies, uses no storage, and initiates no network requests.
No events are persisted without an analytics receiver. Configure a receiver and
applicable consent/privacy settings before considering on-site reporting live.

## Measurement dashboard

Search Console: report weekly impressions, clicks, CTR and search terms separately for the
exact URL `/topics/` and the prefix `/topics/*/`. Compare equal 28-day periods after
indexing; allow for lag and seasonality.

On-site: report sessions seeing the Topics directory and sessions with a topic-hub click.
Directory navigation rate = sessions with destination click / sessions viewing directory.
Report `related_context` navigation by source page and destination.
Do not mistake click events for unique users. Exclude menu/footer clicks and anchors.

Quality checks: verify destinations, canonical/indexability, internal link availability,
and whether organic visitors navigate into deeper Guides and Research. Do not upload private
Search Console exports to the public repository.
