# XTAK VEIL APRS artwork provenance (TAK Map i672)

Source: user's archived `xtak-veil-v0.4.0-r50.zip`, `app/static/map-icons/aprs-*.svg`.
Map category resolver: VEIL r50 `app/static/map.js`, function `aprsCategory` (copied verbatim into `tak-map-veil-aprs-i672.js`, operating on a normalized input envelope).
The ten original SVG assets are byte-identical to r50. The VEIL Node Map uses **ten coarse semantic icon classes**, not a full primary/secondary 192-entry APRS atlas. The original table, symbol code, and optional overlay are preserved for future use, though the r50 category function selects primarily by symbol code and weather/object status.

SHA-256 of each original r50 SVG:

- `aprs-aircraft.svg`: `ec4af4b83607e1ce46938decef1081a059e7a13289fcdb5836871b96befe6c34`
- `aprs-base.svg`: `3b3ef2cd0976d7ba955f290d34aebfddd5cc3cdbe7bc0d9f32d824e81d618990`
- `aprs-digipeater.svg`: `c6ead4b0896d7d0c918aac79b9afac98d8764f8f39738288866692d02dd07ebe`
- `aprs-emergency.svg`: `dba77da9be6b2f850f100deffe13227a15e35712cfd9fe0441c046947b271cec`
- `aprs-generic.svg`: `3d515939171c0feed35254689d880ce0853999e72b9bb04eb4eb6b4364b22635`
- `aprs-marine.svg`: `8f8c4b277b41c8b137b99bfdeca7ece12d2105cbee90641440eca87583b157d5`
- `aprs-object.svg`: `5c41ae918353c0187d1a4b4e93ee35b0d8c83d205b7571048117a5b2f3ee98d1`
- `aprs-portable.svg`: `402725e8c9861880d68af16ded0c8e5978cf2e090dbd8a4b1cf19a5060e01049`
- `aprs-vehicle.svg`: `92273569e59e3f2ee6a90a9e185e10ecefdb5dedf5cfd17eae7487bc62b20eda`
- `aprs-weather.svg`: `68e2dccea206e84ee8c4946dfcc4622295a70407bb55dfb2b4a2a820fbbaa213`
