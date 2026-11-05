-- POS cloud mirror schema (generated from utils/supabase_sync.py)
-- Safe to run more than once.

create table if not exists public."brands" (
    "id" bigint primary key,
    "name" text,
    "phone" text,
    "telegram" text,
    "facebook" text,
    "address" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."brands" enable row level security;

create table if not exists public."users" (
    "id" bigint primary key,
    "username" text,
    "password" text,
    "role" text,
    "name" text,
    "brand_id" bigint,
    "active" bigint,
    "created_at" timestamp
);
alter table public."users" enable row level security;

create table if not exists public."customers" (
    "id" bigint primary key,
    "name" text,
    "phone" text,
    "address" text,
    "facebook" text,
    "telegram" text,
    "type" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."customers" enable row level security;

create table if not exists public."categories" (
    "id" bigint primary key,
    "name" text,
    "description" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."categories" enable row level security;

create table if not exists public."taste" (
    "id" bigint primary key,
    "name" text,
    "description" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."taste" enable row level security;

create table if not exists public."units" (
    "id" bigint primary key,
    "name" text,
    "description" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."units" enable row level security;

create table if not exists public."products" (
    "id" bigint primary key,
    "code" text,
    "name" text,
    "category_id" bigint,
    "units_id" bigint,
    "price" double precision,
    "created_by" bigint,
    "description" text,
    "is_active" bigint,
    "created_at" timestamp
);
alter table public."products" enable row level security;

create table if not exists public."orders" (
    "id" bigint primary key,
    "order_number" text,
    "customer_id" bigint,
    "order_by" bigint,
    "brand_id" bigint,
    "total_amount" double precision,
    "delivery_fee" double precision,
    "discount" double precision,
    "status" text,
    "payment_method" text,
    "payment_status" text,
    "paid_amount" double precision,
    "pickup_time" text,
    "note" text,
    "created_at" timestamp
);
alter table public."orders" enable row level security;

create table if not exists public."order_items" (
    "id" bigint primary key,
    "order_id" bigint,
    "product_id" bigint,
    "product_name" text,
    "taste" text,
    "unit" text,
    "quantity" double precision,
    "weight" double precision,
    "unit_price" double precision,
    "subtotal" double precision
);
alter table public."order_items" enable row level security;

create table if not exists public."stock" (
    "id" bigint primary key,
    "product_id" bigint,
    "brand_id" bigint,
    "quantity" double precision,
    "updated_at" timestamp
);
alter table public."stock" enable row level security;

create table if not exists public."stock_movements" (
    "id" bigint primary key,
    "product_id" bigint,
    "brand_id" bigint,
    "movement_type" text,
    "quantity" double precision,
    "reason" text,
    "reference_order_id" bigint,
    "created_by" bigint,
    "created_at" timestamp
);
alter table public."stock_movements" enable row level security;

create table if not exists public."stock_transfers" (
    "id" bigint primary key,
    "product_id" bigint,
    "from_brand_id" bigint,
    "to_brand_id" bigint,
    "quantity" double precision,
    "note" text,
    "transferred_by" bigint,
    "transferred_at" timestamp
);
alter table public."stock_transfers" enable row level security;

create table if not exists public."settings" (
    "id" bigint primary key,
    "key" text,
    "value" text,
    "updated_at" timestamp
);
alter table public."settings" enable row level security;

-- RLS is ON with no policies: the publishable/anon key can read nothing.
-- The secret (service_role) key used by the POS bypasses RLS but still needs table grants:
grant usage on schema public to service_role;
grant select, insert, update, delete on all tables in schema public to service_role;

create index if not exists orders_created_at_idx on public.orders (created_at);
create index if not exists order_items_order_id_idx on public.order_items (order_id);
create index if not exists stock_movements_created_at_idx on public.stock_movements (created_at);
