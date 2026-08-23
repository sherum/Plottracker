# TODO

- The Preview panel and the Sidekick's context both strip out segment formatting (italic/bold/etc.) - `/topics/{id}/segments` doesn't join `segment_styles`, and the Sidekick never receives raw segment data. So there's no way today to show real formatting in the Preview, or to point the Sidekick at a specific example passage and have it infer/verify an encoding rule from the passage's actual styling. Both would need segment style data to flow further than it does now.
