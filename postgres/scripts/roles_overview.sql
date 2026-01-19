\pset pager off

with roles as (
  select
    r.oid,
    r.rolname,
    r.rolcanlogin,
    r.rolsuper,
    r.rolcreatedb,
    r.rolcreaterole,
    r.rolinherit,
    r.rolreplication,
    r.rolbypassrls,
    r.rolconnlimit,
    r.rolvaliduntil
  from pg_roles r
)
select
  r.rolname as role,
  r.rolcanlogin as can_login,
  r.rolsuper as superuser,
  r.rolcreatedb as createdb,
  r.rolcreaterole as createrole,
  r.rolinherit as inherit,
  r.rolreplication as replication,
  r.rolbypassrls as bypassrls,
  r.rolconnlimit as conn_limit,
  r.rolvaliduntil as valid_until,
  coalesce(string_agg(m.rolname, ', ' order by m.rolname), '') as member_of
from roles r
left join pg_auth_members am on am.member = r.oid
left join pg_roles m on m.oid = am.roleid
group by
  r.rolname,
  r.rolcanlogin,
  r.rolsuper,
  r.rolcreatedb,
  r.rolcreaterole,
  r.rolinherit,
  r.rolreplication,
  r.rolbypassrls,
  r.rolconnlimit,
  r.rolvaliduntil
order by r.rolname;
