# PostGIS Runtime Guidance

Use this reference when the task involves spatial tables, coordinates, SRIDs,
radius search, nearest-neighbor lookups, or spatial indexes.

## 1) Prefer PostGIS spatial types for real geospatial workloads
Use PostGIS `geometry` or `geography` columns instead of PostgreSQL's built-in
geometric types when the workload needs SRIDs, accurate measurements, spatial
indexes, or common spatial predicates.

## 2) Choose `geometry` vs `geography` deliberately
- Use `geometry` when you need the broadest spatial-function support or when
  the data belongs to a projected local coordinate system.
- Use `geography` when the data is global lat/lon and the common requirement is
  accurate distance queries in meters.
- `geography` is convenient for meter-based distance work, but it supports a
  smaller function set and is often slower than `geometry`.

For interoperable GPS-style storage, default to SRID `4326` unless a local
projected CRS is clearly required by the application.

## 3) Always declare the SRID
Do not leave spatial columns untyped or SRID-free.

```sql
create table places (
  id bigint generated always as identity primary key,
  name text not null,
  location geometry(point, 4326) not null
);
```

## 4) Use GiST indexes by default
Create a GiST index on spatial columns unless you have a proven reason to use a
different access method.

```sql
create index places_location_gist_idx on places using gist (location);
```

## 5) Transform for accurate local measurements
If the table stores coordinates in `4326`, transform to an appropriate
projected CRS before calculating local distances or areas with `geometry`.
Replace the sample SRID below with a suitable local projected CRS for your
region and measurement needs.

```sql
select st_area(st_transform(boundary, 26910))
from service_areas
where id = $1;
```

If the workload is mostly meters-based radius search on global coordinates,
`geography(point, 4326)` can reduce query-time conversion work because
distance-based geography functions operate in meters.

## 6) Pick the narrowest practical shape type
- `point`: single coordinates such as stores, devices, or events
- `linestring`: routes, paths, or tracked movements
- `polygon`: boundaries, zones, or service areas
- multi-geometry types only when a row genuinely needs multiple shapes

## 7) Match query patterns to the stored type
Radius search from lon/lat input:

```sql
select id, name
from places
where st_dwithin(
  location::geography,
  st_setsrid(st_makepoint($1, $2), 4326)::geography,
  $3
);
```

Intersection query:

```sql
select id
from service_areas
where st_intersects(boundary, st_makeenvelope($1, $2, $3, $4, 4326));
```

Nearest-neighbor lookup:

```sql
select id, name
from places
order by location <-> st_setsrid(st_makepoint($1, $2), 4326)
limit 10;
```

For `geometry(point, 4326)`, nearest-neighbor ordering is based on coordinate
units. If you need meter-based distances, use `geography` or transform to a
projected CRS for the distance calculation you display.

## 8) Parameterize user-supplied coordinates and shapes
Treat lon/lat pairs, WKT, WKB, GeoJSON fragments, and IDs as query parameters.
Do not concatenate user-provided geometry input into SQL strings.

## Official References
- Geometry vs geography FAQ: https://postgis.net/documentation/faq/geometry-or-geography/
- Spatial indexes FAQ: https://postgis.net/documentation/faq/spatial-indexes/
- `ST_SetSRID`: https://postgis.net/docs/ST_SetSRID.html
- `ST_Transform`: https://postgis.net/docs/ST_Transform.html
- `ST_DWithin`: https://postgis.net/docs/ST_DWithin.html
- KNN `<->`: https://postgis.net/docs/manual-3.0/geometry_distance_knn.html
