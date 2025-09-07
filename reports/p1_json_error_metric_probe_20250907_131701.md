# P1-4 JSON Error Metric Probe (20250907_131701)

## *_total candidates (error numerator)
- json_invalid_total                                           : 0
- json_error_total                                             : 0
- http_requests_total{status=~"5.."}                           : 0
- http_server_requests_seconds_count{status=~"5.."}            : 0
- requests_total{code=~"5.."}                                  : 0

## *_total candidates (all requests denominator)
- requests_total                                               : 0
- http_requests_total                                          : 0
- http_server_requests_seconds_count                           : 0

## Note
- 件数>0 のものが候補です。label（status/code/route/instance等）によって式を最適化します。
