-- Runtime grants are now applied per campground by tenant_database.protect_schema.
-- Use provision --grant-runtime --campground SLUG; never grant across every schema.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON public.campground_tenants FROM campground_app;
GRANT SELECT ON public.campground_tenants TO campground_app;
