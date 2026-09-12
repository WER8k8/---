--
-- PostgreSQL database dump
--

\restrict vNZQ96NYleXMqRGDy0buUcdP2yeJABX2q8bsTckZwb6NVkoI74D66AWR8ftM9y0

-- Dumped from database version 15.18 (Debian 15.18-1.pgdg12+1)
-- Dumped by pg_dump version 15.18 (Debian 15.18-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ab_test_conversions; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ab_test_conversions (
    id uuid NOT NULL,
    experiment_id uuid NOT NULL,
    variant_id character varying(50) NOT NULL,
    session_id character varying(100) NOT NULL,
    user_id uuid,
    conversion_type character varying(50) NOT NULL,
    conversion_value double precision,
    conversion_data json,
    created_at timestamp without time zone
);


ALTER TABLE public.ab_test_conversions OWNER TO youding_admin;

--
-- Name: COLUMN ab_test_conversions.conversion_type; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_test_conversions.conversion_type IS 'form_submit/click/purchase';


--
-- Name: ab_test_events; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ab_test_events (
    id uuid NOT NULL,
    experiment_id uuid NOT NULL,
    session_id character varying(100) NOT NULL,
    user_id uuid,
    variant_id character varying(50) NOT NULL,
    event_type character varying(50) NOT NULL,
    event_data json,
    page_url character varying(500),
    referrer character varying(500),
    device_type character varying(50),
    browser character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public.ab_test_events OWNER TO youding_admin;

--
-- Name: COLUMN ab_test_events.event_type; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_test_events.event_type IS 'impression/click/conversion/scroll';


--
-- Name: COLUMN ab_test_events.device_type; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_test_events.device_type IS 'desktop/mobile/tablet';


--
-- Name: ab_test_variants; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ab_test_variants (
    id uuid NOT NULL,
    experiment_id uuid NOT NULL,
    variant_id character varying(50) NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    content_config json,
    weight double precision,
    visitors integer,
    conversions integer,
    conversion_rate double precision,
    metrics_data json,
    is_control boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.ab_test_variants OWNER TO youding_admin;

--
-- Name: ab_tests; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ab_tests (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    experiment_type character varying(50),
    target_url character varying(500) NOT NULL,
    status character varying(20),
    variants_config json NOT NULL,
    traffic_percentage double precision,
    primary_metric character varying(100),
    secondary_metrics json,
    min_sample_size integer,
    confidence_level double precision,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    total_visitors integer,
    winner_variant character varying(50),
    statistical_significance double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by uuid
);


ALTER TABLE public.ab_tests OWNER TO youding_admin;

--
-- Name: COLUMN ab_tests.experiment_type; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_tests.experiment_type IS 'page/component/element';


--
-- Name: COLUMN ab_tests.status; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_tests.status IS 'draft/running/paused/completed';


--
-- Name: COLUMN ab_tests.variants_config; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_tests.variants_config IS 'Variant configuration';


--
-- Name: COLUMN ab_tests.primary_metric; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_tests.primary_metric IS 'conversion/click_through/time_on_page';


--
-- Name: COLUMN ab_tests.secondary_metrics; Type: COMMENT; Schema: public; Owner: youding_admin
--

COMMENT ON COLUMN public.ab_tests.secondary_metrics IS 'Secondary metrics list';


--
-- Name: ad_law_keywords; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ad_law_keywords (
    id uuid NOT NULL,
    keyword character varying(100) NOT NULL,
    category character varying(100) NOT NULL,
    severity character varying(20) NOT NULL,
    description text,
    alternative character varying(255),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.ad_law_keywords OWNER TO youding_admin;

--
-- Name: ai_model_configs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ai_model_configs (
    id uuid NOT NULL,
    provider_id uuid NOT NULL,
    model_name character varying(100) NOT NULL,
    model_type character varying(30) NOT NULL,
    temperature character varying(10) NOT NULL,
    max_tokens character varying(10) NOT NULL,
    context_window character varying(10),
    is_active boolean NOT NULL,
    is_default boolean NOT NULL,
    metadata json,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.ai_model_configs OWNER TO youding_admin;

--
-- Name: ai_model_providers; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ai_model_providers (
    id uuid NOT NULL,
    name character varying(50) NOT NULL,
    provider_type character varying(30) NOT NULL,
    api_key character varying(255) NOT NULL,
    base_url character varying(255),
    default_model character varying(100),
    is_active boolean NOT NULL,
    is_default boolean NOT NULL,
    description text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.ai_model_providers OWNER TO youding_admin;

--
-- Name: ai_optimization_logs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ai_optimization_logs (
    id uuid NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(50) NOT NULL,
    optimization_type character varying(50) NOT NULL,
    original_content text,
    optimized_content text,
    model_used character varying(100),
    tokens_used integer,
    score_before double precision,
    score_after double precision,
    created_at timestamp with time zone
);


ALTER TABLE public.ai_optimization_logs OWNER TO youding_admin;

--
-- Name: ai_recommendations; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ai_recommendations (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    product_id uuid NOT NULL,
    score numeric(5,4) NOT NULL,
    reason text,
    algorithm character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public.ai_recommendations OWNER TO youding_admin;

--
-- Name: ai_usage_logs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.ai_usage_logs (
    id uuid NOT NULL,
    provider_id uuid NOT NULL,
    model_name character varying(100) NOT NULL,
    task_type character varying(50) NOT NULL,
    prompt_tokens character varying(10),
    completion_tokens character varying(10),
    total_tokens character varying(10),
    cost character varying(20),
    duration_ms character varying(20),
    success boolean NOT NULL,
    error_message text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.ai_usage_logs OWNER TO youding_admin;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(128) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO youding_admin;

--
-- Name: building_material_specs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.building_material_specs (
    id integer NOT NULL,
    product_id integer NOT NULL,
    spec_key character varying(50) NOT NULL,
    spec_value numeric NOT NULL,
    metric_unit character varying(10) NOT NULL,
    imperial_unit character varying(10),
    imperial_scale_factor numeric,
    trust_badges character varying(50)[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.building_material_specs OWNER TO youding_admin;

--
-- Name: building_material_specs_id_seq; Type: SEQUENCE; Schema: public; Owner: youding_admin
--

CREATE SEQUENCE public.building_material_specs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.building_material_specs_id_seq OWNER TO youding_admin;

--
-- Name: building_material_specs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: youding_admin
--

ALTER SEQUENCE public.building_material_specs_id_seq OWNED BY public.building_material_specs.id;


--
-- Name: case_images; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.case_images (
    id uuid NOT NULL,
    case_id uuid NOT NULL,
    image_url character varying(500) NOT NULL,
    image_alt character varying(255),
    sort_order integer,
    is_active boolean,
    created_at timestamp with time zone
);


ALTER TABLE public.case_images OWNER TO youding_admin;

--
-- Name: case_studies; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.case_studies (
    id uuid NOT NULL,
    project_name character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    client_name character varying(255),
    materials_used character varying(500),
    construction_area character varying(100),
    project_date character varying(50),
    location character varying(255),
    description text,
    cover_image character varying(500),
    status character varying(20),
    sort_order integer,
    view_count integer,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    product_id character varying(36),
    project_address character varying(255)
);


ALTER TABLE public.case_studies OWNER TO youding_admin;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.categories (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    description text,
    parent_id uuid,
    sort_order integer,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.categories OWNER TO youding_admin;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.chat_messages (
    id uuid NOT NULL,
    session_id uuid NOT NULL,
    role character varying(50) NOT NULL,
    content text NOT NULL,
    tokens integer,
    model character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public.chat_messages OWNER TO youding_admin;

--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.chat_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    session_name character varying(255),
    model_used character varying(100),
    total_tokens integer,
    status character varying(50),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.chat_sessions OWNER TO youding_admin;

--
-- Name: compliance_rules; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.compliance_rules (
    id uuid NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_type character varying(50) NOT NULL,
    keywords json NOT NULL,
    severity character varying(20) NOT NULL,
    description text,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.compliance_rules OWNER TO youding_admin;

--
-- Name: compliance_scan_results; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.compliance_scan_results (
    id uuid NOT NULL,
    content_id character varying(36) NOT NULL,
    content_type character varying(50) NOT NULL,
    content_title character varying(255),
    content_text text,
    scan_status character varying(20) NOT NULL,
    total_issues integer,
    high_severity_count integer,
    medium_severity_count integer,
    low_severity_count integer,
    scan_details json,
    suggestions json,
    scanned_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.compliance_scan_results OWNER TO youding_admin;

--
-- Name: compliance_violations; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.compliance_violations (
    id uuid NOT NULL,
    scan_result_id character varying(36),
    rule_id character varying(36),
    rule_name character varying(100),
    rule_type character varying(50),
    severity character varying(20),
    matched_text character varying(255),
    context character varying(500),
    suggestion text,
    is_resolved boolean,
    resolved_at timestamp without time zone,
    created_at timestamp without time zone
);


ALTER TABLE public.compliance_violations OWNER TO youding_admin;

--
-- Name: content_pages; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.content_pages (
    id uuid NOT NULL,
    title character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    content text,
    summary character varying(500),
    page_type character varying(50),
    status character varying(20) NOT NULL,
    author_id uuid,
    view_count integer,
    is_active boolean,
    published_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.content_pages OWNER TO youding_admin;

--
-- Name: content_versions; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.content_versions (
    id uuid NOT NULL,
    page_id uuid NOT NULL,
    version_number integer NOT NULL,
    title character varying(200) NOT NULL,
    content text,
    summary character varying(500),
    change_log character varying(500),
    author_id uuid,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.content_versions OWNER TO youding_admin;

--
-- Name: eeat_article_authors; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.eeat_article_authors (
    id uuid NOT NULL,
    article_id character varying(36) NOT NULL,
    author_id uuid,
    author_type character varying(50),
    role character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public.eeat_article_authors OWNER TO youding_admin;

--
-- Name: eeat_author_certifications; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.eeat_author_certifications (
    id uuid NOT NULL,
    author_id uuid,
    certification_name character varying(200) NOT NULL,
    issuing_body character varying(200),
    issue_date timestamp without time zone,
    expiration_date timestamp without time zone,
    credential_number character varying(100),
    is_valid boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.eeat_author_certifications OWNER TO youding_admin;

--
-- Name: eeat_authors; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.eeat_authors (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    bio text,
    title character varying(100),
    company character varying(100),
    email character varying(100),
    linkedin_url character varying(255),
    twitter_url character varying(255),
    expertise_areas json,
    credentials json,
    is_verified boolean,
    trust_score double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.eeat_authors OWNER TO youding_admin;

--
-- Name: eeat_scores; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.eeat_scores (
    id uuid NOT NULL,
    content_id character varying(36) NOT NULL,
    content_type character varying(50) NOT NULL,
    experience_score double precision,
    expertise_score double precision,
    authoritativeness_score double precision,
    trustworthiness_score double precision,
    overall_score double precision,
    factors json,
    recommendations json,
    evaluated_at timestamp without time zone
);


ALTER TABLE public.eeat_scores OWNER TO youding_admin;

--
-- Name: eeat_trust_signals; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.eeat_trust_signals (
    id uuid NOT NULL,
    content_id character varying(36) NOT NULL,
    signal_type character varying(100) NOT NULL,
    signal_value character varying(500),
    score_impact double precision,
    is_positive boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.eeat_trust_signals OWNER TO youding_admin;

--
-- Name: glossary_terms; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.glossary_terms (
    id uuid NOT NULL,
    zh character varying(200) NOT NULL,
    en character varying(200) NOT NULL,
    ja character varying(200),
    ko character varying(200),
    de character varying(200),
    fr character varying(200),
    es character varying(200),
    pt character varying(200),
    it character varying(200),
    nl character varying(200),
    ru character varying(200),
    ar character varying(200),
    tr character varying(200),
    fa character varying(200),
    he character varying(200),
    th character varying(200),
    vi character varying(200),
    ms character varying(200),
    hi character varying(200),
    id_ba character varying(200),
    tl character varying(200),
    bn character varying(200),
    my character varying(200),
    km character varying(200),
    pl character varying(200),
    cs character varying(200),
    uk character varying(200),
    sv character varying(200),
    sw character varying(200),
    ha character varying(200),
    zu character varying(200),
    am character varying(200),
    category character varying(50),
    status character varying(20),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.glossary_terms OWNER TO youding_admin;

--
-- Name: inquiries; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.inquiries (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    phone character varying(50) NOT NULL,
    email character varying(200),
    product character varying(100),
    message text NOT NULL,
    status character varying(20) NOT NULL,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    wechat character varying(100),
    session_id character varying(64),
    landing_path character varying(500),
    last_click_label character varying(300),
    tenant_id character varying(36),
    assigned_to character varying(36)
);


ALTER TABLE public.inquiries OWNER TO youding_admin;

--
-- Name: international_crawl_logs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.international_crawl_logs (
    id uuid NOT NULL,
    site_id uuid,
    status character varying(20),
    pages_crawled integer,
    inquiries_found integer,
    error_message text,
    duration_seconds integer,
    ip_used character varying(50),
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.international_crawl_logs OWNER TO youding_admin;

--
-- Name: international_inquiries; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.international_inquiries (
    id uuid NOT NULL,
    source_site_id uuid,
    source_url character varying(1000) NOT NULL,
    source_title character varying(500),
    customer_name character varying(200),
    email character varying(200),
    phone character varying(100),
    wechat character varying(100),
    company character varying(300),
    product_interest character varying(500),
    product_model character varying(200),
    quantity character varying(200),
    budget character varying(200),
    message text,
    inquiry_time character varying(100),
    crawled_at timestamp with time zone,
    language character varying(10),
    region character varying(10),
    confidence integer,
    raw_data text,
    status character varying(20),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.international_inquiries OWNER TO youding_admin;

--
-- Name: international_target_sites; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.international_target_sites (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    url character varying(500) NOT NULL,
    region character varying(10) NOT NULL,
    language character varying(10),
    crawl_interval integer,
    last_crawled_at timestamp with time zone,
    status character varying(20),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.international_target_sites OWNER TO youding_admin;

--
-- Name: keyword_ranking_history; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.keyword_ranking_history (
    id integer NOT NULL,
    keyword_ranking_id integer NOT NULL,
    keyword character varying(200) NOT NULL,
    search_engine character varying(50) NOT NULL,
    "position" integer,
    search_volume integer DEFAULT 0,
    checked_at timestamp without time zone NOT NULL
);


ALTER TABLE public.keyword_ranking_history OWNER TO youding_admin;

--
-- Name: keyword_ranking_history_id_seq; Type: SEQUENCE; Schema: public; Owner: youding_admin
--

CREATE SEQUENCE public.keyword_ranking_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.keyword_ranking_history_id_seq OWNER TO youding_admin;

--
-- Name: keyword_ranking_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: youding_admin
--

ALTER SEQUENCE public.keyword_ranking_history_id_seq OWNED BY public.keyword_ranking_history.id;


--
-- Name: keyword_rankings; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.keyword_rankings (
    id integer NOT NULL,
    keyword character varying(200) NOT NULL,
    search_engine character varying(50) DEFAULT 'baidu'::character varying NOT NULL,
    target_url character varying(500) DEFAULT ''::character varying,
    current_position integer,
    previous_position integer,
    best_position integer,
    search_volume integer DEFAULT 0,
    difficulty character varying(20) DEFAULT 'medium'::character varying,
    cpc double precision DEFAULT '0'::double precision,
    is_tracking boolean DEFAULT true,
    category character varying(100) DEFAULT ''::character varying,
    notes character varying(500) DEFAULT ''::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    last_checked_at timestamp without time zone
);


ALTER TABLE public.keyword_rankings OWNER TO youding_admin;

--
-- Name: keyword_rankings_id_seq; Type: SEQUENCE; Schema: public; Owner: youding_admin
--

CREATE SEQUENCE public.keyword_rankings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.keyword_rankings_id_seq OWNER TO youding_admin;

--
-- Name: keyword_rankings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: youding_admin
--

ALTER SEQUENCE public.keyword_rankings_id_seq OWNED BY public.keyword_rankings.id;


--
-- Name: keywords; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.keywords (
    id uuid NOT NULL,
    keyword character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    search_volume integer,
    difficulty character varying(20),
    current_ranking integer,
    target_url character varying(500),
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.keywords OWNER TO youding_admin;

--
-- Name: llms_config; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.llms_config (
    id uuid NOT NULL,
    section character varying(100) NOT NULL,
    content text NOT NULL,
    is_active boolean,
    version character varying(20),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.llms_config OWNER TO youding_admin;

--
-- Name: merchant_im_routing; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.merchant_im_routing (
    id integer NOT NULL,
    merchant_id integer NOT NULL,
    country_code character varying(2) NOT NULL,
    channel_type character varying(20) NOT NULL,
    account_id character varying(100) NOT NULL,
    prefilled_text text,
    is_active boolean,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.merchant_im_routing OWNER TO youding_admin;

--
-- Name: merchant_im_routing_id_seq; Type: SEQUENCE; Schema: public; Owner: youding_admin
--

CREATE SEQUENCE public.merchant_im_routing_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.merchant_im_routing_id_seq OWNER TO youding_admin;

--
-- Name: merchant_im_routing_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: youding_admin
--

ALTER SEQUENCE public.merchant_im_routing_id_seq OWNED BY public.merchant_im_routing.id;


--
-- Name: merchant_profiles; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.merchant_profiles (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    company_name character varying(255) NOT NULL,
    company_address text,
    country character varying(100),
    city character varying(100),
    business_license character varying(255),
    verified boolean,
    verification_documents jsonb,
    contact_person character varying(100),
    contact_email character varying(255),
    contact_phone character varying(50),
    whatsapp_number character varying(50),
    wechat_id character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.merchant_profiles OWNER TO youding_admin;

--
-- Name: news_articles; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.news_articles (
    id uuid NOT NULL,
    title character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    subtitle character varying(255),
    summary text,
    content text NOT NULL,
    cover_image character varying(500),
    category character varying(50) NOT NULL,
    tags character varying(500),
    author character varying(100),
    source character varying(100),
    view_count integer DEFAULT 0,
    is_published boolean DEFAULT false,
    published_at timestamp without time zone,
    sort_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    meta_title character varying(255),
    meta_description character varying(500),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.news_articles OWNER TO youding_admin;

--
-- Name: news_categories; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.news_categories (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    slug character varying(100) NOT NULL,
    description character varying(500),
    sort_order integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.news_categories OWNER TO youding_admin;

--
-- Name: operation_logs; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.operation_logs (
    id uuid NOT NULL,
    user_id uuid,
    action character varying(50) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(50),
    detail text,
    ip_address character varying(45),
    created_at timestamp with time zone
);


ALTER TABLE public.operation_logs OWNER TO youding_admin;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.order_items (
    id uuid NOT NULL,
    order_id uuid NOT NULL,
    product_id uuid NOT NULL,
    quantity integer NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    total_price numeric(10,2) NOT NULL,
    specifications jsonb,
    created_at timestamp without time zone
);


ALTER TABLE public.order_items OWNER TO youding_admin;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.orders (
    id uuid NOT NULL,
    buyer_id uuid NOT NULL,
    merchant_id uuid NOT NULL,
    quote_id uuid,
    order_number character varying(100) NOT NULL,
    total_amount numeric(10,2) NOT NULL,
    currency character varying(10),
    status character varying(50),
    payment_status character varying(50),
    shipping_address text,
    shipping_method character varying(100),
    tracking_number character varying(100),
    estimated_delivery date,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.orders OWNER TO youding_admin;

--
-- Name: payment_channels; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.payment_channels (
    id uuid NOT NULL,
    channel character varying(20) NOT NULL,
    config text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.payment_channels OWNER TO youding_admin;

--
-- Name: payment_orders; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.payment_orders (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    subscription_id uuid,
    order_no character varying(100) NOT NULL,
    amount integer NOT NULL,
    currency character varying(10) NOT NULL,
    channel character varying(20) NOT NULL,
    subject character varying(200) NOT NULL,
    status character varying(20) NOT NULL,
    paid_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.payment_orders OWNER TO youding_admin;

--
-- Name: product_categories; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.product_categories (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    name_i18n jsonb,
    slug character varying(255) NOT NULL,
    parent_id uuid,
    level integer,
    icon_url character varying(500),
    sort_order integer,
    meta_title character varying(255),
    meta_description text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.product_categories OWNER TO youding_admin;

--
-- Name: product_documents; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.product_documents (
    id uuid NOT NULL,
    product_id uuid NOT NULL,
    doc_type character varying(20) NOT NULL,
    file_name character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size integer,
    description character varying(500),
    sort_order integer,
    is_active boolean,
    created_at timestamp with time zone
);


ALTER TABLE public.product_documents OWNER TO youding_admin;

--
-- Name: product_images; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.product_images (
    id uuid NOT NULL,
    product_id uuid NOT NULL,
    image_url character varying(500) NOT NULL,
    alt_text character varying(255),
    sort_order integer,
    is_primary boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.product_images OWNER TO youding_admin;

--
-- Name: products; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.products (
    id uuid NOT NULL,
    category_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    subtitle character varying(300),
    description text,
    technical_params text,
    application_scenarios text,
    advantages text,
    specifications text,
    density character varying(50),
    strength character varying(50),
    thermal_conductivity character varying(50),
    unit_weight character varying(50),
    image_url character varying(500),
    meta_title character varying(200),
    meta_description character varying(500),
    sort_order integer,
    is_active boolean,
    view_count integer,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    fire_rating character varying(20)
);


ALTER TABLE public.products OWNER TO youding_admin;

--
-- Name: quotes; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.quotes (
    id uuid NOT NULL,
    inquiry_id uuid NOT NULL,
    merchant_id uuid NOT NULL,
    total_amount numeric(10,2) NOT NULL,
    currency character varying(10),
    valid_until date,
    payment_terms text,
    delivery_terms text,
    status character varying(50),
    pdf_url character varying(500),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.quotes OWNER TO youding_admin;

--
-- Name: schema_markups; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.schema_markups (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    schema_type character varying(100) NOT NULL,
    content json NOT NULL,
    is_active boolean,
    page_url character varying(500),
    version character varying(20),
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.schema_markups OWNER TO youding_admin;

--
-- Name: schema_templates; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.schema_templates (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    schema_type character varying(100) NOT NULL,
    template json NOT NULL,
    description text,
    category character varying(50),
    is_active boolean,
    created_at timestamp with time zone
);


ALTER TABLE public.schema_templates OWNER TO youding_admin;

--
-- Name: seo_competitors; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.seo_competitors (
    id integer NOT NULL,
    domain character varying(200) NOT NULL,
    name character varying(200) DEFAULT ''::character varying,
    authority_score integer DEFAULT 0,
    backlinks_count integer DEFAULT 0,
    organic_keywords integer DEFAULT 0,
    organic_traffic integer DEFAULT 0,
    is_active boolean DEFAULT true,
    notes character varying(500) DEFAULT ''::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.seo_competitors OWNER TO youding_admin;

--
-- Name: seo_competitors_id_seq; Type: SEQUENCE; Schema: public; Owner: youding_admin
--

CREATE SEQUENCE public.seo_competitors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.seo_competitors_id_seq OWNER TO youding_admin;

--
-- Name: seo_competitors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: youding_admin
--

ALTER SEQUENCE public.seo_competitors_id_seq OWNED BY public.seo_competitors.id;


--
-- Name: seo_metadata; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.seo_metadata (
    id uuid NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id character varying(50) NOT NULL,
    meta_title character varying(200),
    meta_description character varying(500),
    meta_keywords character varying(300),
    canonical_url character varying(500),
    og_title character varying(200),
    og_description character varying(500),
    og_image character varying(500),
    schema_markup text,
    noindex boolean,
    h1_tag character varying(200),
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    entity_type character varying(50),
    entity_id character varying(36)
);


ALTER TABLE public.seo_metadata OWNER TO youding_admin;

--
-- Name: site_audits; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.site_audits (
    id uuid NOT NULL,
    url character varying(500),
    status character varying(20) NOT NULL,
    audit_type character varying(50) NOT NULL,
    score double precision,
    total_issues integer,
    critical_issues integer,
    warning_issues integer,
    report_data text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone
);


ALTER TABLE public.site_audits OWNER TO youding_admin;

--
-- Name: system_config; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.system_config (
    id uuid NOT NULL,
    key character varying(255) NOT NULL,
    value text,
    value_type character varying(50),
    description text,
    is_public boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.system_config OWNER TO youding_admin;

--
-- Name: tenant_invoices; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.tenant_invoices (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    subscription_id uuid,
    amount integer NOT NULL,
    status character varying(20) NOT NULL,
    paid_at timestamp with time zone,
    due_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tenant_invoices OWNER TO youding_admin;

--
-- Name: tenant_plans; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.tenant_plans (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    price_monthly integer NOT NULL,
    price_yearly integer NOT NULL,
    max_users integer NOT NULL,
    max_sites integer NOT NULL,
    max_products integer NOT NULL,
    max_ai_quota integer NOT NULL,
    features text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tenant_plans OWNER TO youding_admin;

--
-- Name: tenant_subscriptions; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.tenant_subscriptions (
    id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    billing_cycle character varying(20) NOT NULL,
    amount integer NOT NULL,
    status character varying(20) NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tenant_subscriptions OWNER TO youding_admin;

--
-- Name: tenants; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.tenants (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    contact_name character varying(100),
    contact_email character varying(200),
    contact_phone character varying(50),
    domain character varying(200) NOT NULL,
    plan_id uuid NOT NULL,
    status character varying(20) NOT NULL,
    trial_ends_at timestamp with time zone,
    subscribed_at timestamp with time zone,
    expires_at timestamp with time zone,
    ai_quota_used integer NOT NULL,
    storage_used integer NOT NULL,
    settings text,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    custom_domains text DEFAULT ''::text
);


ALTER TABLE public.tenants OWNER TO youding_admin;

--
-- Name: translation_records; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.translation_records (
    id uuid NOT NULL,
    task_id uuid,
    source_text text NOT NULL,
    translated_text text,
    source_lang character varying(10) NOT NULL,
    target_lang character varying(10) NOT NULL,
    status character varying(20),
    rating integer,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.translation_records OWNER TO youding_admin;

--
-- Name: translation_tasks; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.translation_tasks (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    source_lang character varying(10) NOT NULL,
    target_lang character varying(10) NOT NULL,
    total_items integer,
    completed_items integer,
    status character varying(20),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.translation_tasks OWNER TO youding_admin;

--
-- Name: user_tenants; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.user_tenants (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    tenant_id uuid NOT NULL,
    role character varying(20),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.user_tenants OWNER TO youding_admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: youding_admin
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    display_name character varying(100),
    role character varying(20) NOT NULL,
    is_active boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE public.users OWNER TO youding_admin;

--
-- Name: building_material_specs id; Type: DEFAULT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.building_material_specs ALTER COLUMN id SET DEFAULT nextval('public.building_material_specs_id_seq'::regclass);


--
-- Name: keyword_ranking_history id; Type: DEFAULT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keyword_ranking_history ALTER COLUMN id SET DEFAULT nextval('public.keyword_ranking_history_id_seq'::regclass);


--
-- Name: keyword_rankings id; Type: DEFAULT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keyword_rankings ALTER COLUMN id SET DEFAULT nextval('public.keyword_rankings_id_seq'::regclass);


--
-- Name: merchant_im_routing id; Type: DEFAULT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.merchant_im_routing ALTER COLUMN id SET DEFAULT nextval('public.merchant_im_routing_id_seq'::regclass);


--
-- Name: seo_competitors id; Type: DEFAULT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.seo_competitors ALTER COLUMN id SET DEFAULT nextval('public.seo_competitors_id_seq'::regclass);


--
-- Data for Name: ab_test_conversions; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ab_test_conversions (id, experiment_id, variant_id, session_id, user_id, conversion_type, conversion_value, conversion_data, created_at) FROM stdin;
\.


--
-- Data for Name: ab_test_events; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ab_test_events (id, experiment_id, session_id, user_id, variant_id, event_type, event_data, page_url, referrer, device_type, browser, created_at) FROM stdin;
\.


--
-- Data for Name: ab_test_variants; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ab_test_variants (id, experiment_id, variant_id, name, description, content_config, weight, visitors, conversions, conversion_rate, metrics_data, is_control, created_at) FROM stdin;
\.


--
-- Data for Name: ab_tests; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ab_tests (id, name, description, experiment_type, target_url, status, variants_config, traffic_percentage, primary_metric, secondary_metrics, min_sample_size, confidence_level, start_date, end_date, total_visitors, winner_variant, statistical_significance, created_at, updated_at, created_by) FROM stdin;
\.


--
-- Data for Name: ad_law_keywords; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ad_law_keywords (id, keyword, category, severity, description, alternative, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ai_model_configs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ai_model_configs (id, provider_id, model_name, model_type, temperature, max_tokens, context_window, is_active, is_default, metadata, created_at, updated_at, sort_order) FROM stdin;
\.


--
-- Data for Name: ai_model_providers; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ai_model_providers (id, name, provider_type, api_key, base_url, default_model, is_active, is_default, description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: ai_optimization_logs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ai_optimization_logs (id, resource_type, resource_id, optimization_type, original_content, optimized_content, model_used, tokens_used, score_before, score_after, created_at) FROM stdin;
\.


--
-- Data for Name: ai_recommendations; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ai_recommendations (id, user_id, product_id, score, reason, algorithm, created_at) FROM stdin;
\.


--
-- Data for Name: ai_usage_logs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.ai_usage_logs (id, provider_id, model_name, task_type, prompt_tokens, completion_tokens, total_tokens, cost, duration_ms, success, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.alembic_version (version_num) FROM stdin;
021_create_im_routing_and_specs
\.


--
-- Data for Name: building_material_specs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.building_material_specs (id, product_id, spec_key, spec_value, metric_unit, imperial_unit, imperial_scale_factor, trust_badges, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: case_images; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.case_images (id, case_id, image_url, image_alt, sort_order, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: case_studies; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.case_studies (id, project_name, slug, client_name, materials_used, construction_area, project_date, location, description, cover_image, status, sort_order, view_count, is_active, created_at, updated_at, product_id, project_address) FROM stdin;
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.categories (id, name, slug, description, parent_id, sort_order, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.chat_messages (id, session_id, role, content, tokens, model, created_at) FROM stdin;
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.chat_sessions (id, user_id, session_name, model_used, total_tokens, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: compliance_rules; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.compliance_rules (id, rule_name, rule_type, keywords, severity, description, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: compliance_scan_results; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.compliance_scan_results (id, content_id, content_type, content_title, content_text, scan_status, total_issues, high_severity_count, medium_severity_count, low_severity_count, scan_details, suggestions, scanned_at, created_at) FROM stdin;
\.


--
-- Data for Name: compliance_violations; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.compliance_violations (id, scan_result_id, rule_id, rule_name, rule_type, severity, matched_text, context, suggestion, is_resolved, resolved_at, created_at) FROM stdin;
\.


--
-- Data for Name: content_pages; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.content_pages (id, title, slug, content, summary, page_type, status, author_id, view_count, is_active, published_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: content_versions; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.content_versions (id, page_id, version_number, title, content, summary, change_log, author_id, created_at) FROM stdin;
\.


--
-- Data for Name: eeat_article_authors; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.eeat_article_authors (id, article_id, author_id, author_type, role, created_at) FROM stdin;
\.


--
-- Data for Name: eeat_author_certifications; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.eeat_author_certifications (id, author_id, certification_name, issuing_body, issue_date, expiration_date, credential_number, is_valid, created_at) FROM stdin;
\.


--
-- Data for Name: eeat_authors; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.eeat_authors (id, name, bio, title, company, email, linkedin_url, twitter_url, expertise_areas, credentials, is_verified, trust_score, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: eeat_scores; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.eeat_scores (id, content_id, content_type, experience_score, expertise_score, authoritativeness_score, trustworthiness_score, overall_score, factors, recommendations, evaluated_at) FROM stdin;
\.


--
-- Data for Name: eeat_trust_signals; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.eeat_trust_signals (id, content_id, signal_type, signal_value, score_impact, is_positive, created_at) FROM stdin;
\.


--
-- Data for Name: glossary_terms; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.glossary_terms (id, zh, en, ja, ko, de, fr, es, pt, it, nl, ru, ar, tr, fa, he, th, vi, ms, hi, id_ba, tl, bn, my, km, pl, cs, uk, sv, sw, ha, zu, am, category, status, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: inquiries; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.inquiries (id, name, phone, email, product, message, status, is_active, created_at, updated_at, wechat, session_id, landing_path, last_click_label, tenant_id, assigned_to) FROM stdin;
\.


--
-- Data for Name: international_crawl_logs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.international_crawl_logs (id, site_id, status, pages_crawled, inquiries_found, error_message, duration_seconds, ip_used, created_at) FROM stdin;
\.


--
-- Data for Name: international_inquiries; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.international_inquiries (id, source_site_id, source_url, source_title, customer_name, email, phone, wechat, company, product_interest, product_model, quantity, budget, message, inquiry_time, crawled_at, language, region, confidence, raw_data, status, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: international_target_sites; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.international_target_sites (id, name, url, region, language, crawl_interval, last_crawled_at, status, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: keyword_ranking_history; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.keyword_ranking_history (id, keyword_ranking_id, keyword, search_engine, "position", search_volume, checked_at) FROM stdin;
\.


--
-- Data for Name: keyword_rankings; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.keyword_rankings (id, keyword, search_engine, target_url, current_position, previous_position, best_position, search_volume, difficulty, cpc, is_tracking, category, notes, created_at, updated_at, last_checked_at) FROM stdin;
\.


--
-- Data for Name: keywords; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.keywords (id, keyword, slug, search_volume, difficulty, current_ranking, target_url, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: llms_config; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.llms_config (id, section, content, is_active, version, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: merchant_im_routing; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.merchant_im_routing (id, merchant_id, country_code, channel_type, account_id, prefilled_text, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: merchant_profiles; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.merchant_profiles (id, user_id, company_name, company_address, country, city, business_license, verified, verification_documents, contact_person, contact_email, contact_phone, whatsapp_number, wechat_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: news_articles; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.news_articles (id, title, slug, subtitle, summary, content, cover_image, category, tags, author, source, view_count, is_published, published_at, sort_order, is_active, meta_title, meta_description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: news_categories; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.news_categories (id, name, slug, description, sort_order, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: operation_logs; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.operation_logs (id, user_id, action, resource_type, resource_id, detail, ip_address, created_at) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.order_items (id, order_id, product_id, quantity, unit_price, total_price, specifications, created_at) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.orders (id, buyer_id, merchant_id, quote_id, order_number, total_amount, currency, status, payment_status, shipping_address, shipping_method, tracking_number, estimated_delivery, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: payment_channels; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.payment_channels (id, channel, config, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: payment_orders; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.payment_orders (id, tenant_id, subscription_id, order_no, amount, currency, channel, subject, status, paid_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: product_categories; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.product_categories (id, name, name_i18n, slug, parent_id, level, icon_url, sort_order, meta_title, meta_description, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: product_documents; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.product_documents (id, product_id, doc_type, file_name, file_path, file_size, description, sort_order, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: product_images; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.product_images (id, product_id, image_url, alt_text, sort_order, is_primary, created_at) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.products (id, category_id, name, slug, subtitle, description, technical_params, application_scenarios, advantages, specifications, density, strength, thermal_conductivity, unit_weight, image_url, meta_title, meta_description, sort_order, is_active, view_count, created_at, updated_at, fire_rating) FROM stdin;
\.


--
-- Data for Name: quotes; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.quotes (id, inquiry_id, merchant_id, total_amount, currency, valid_until, payment_terms, delivery_terms, status, pdf_url, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: schema_markups; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.schema_markups (id, name, schema_type, content, is_active, page_url, version, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: schema_templates; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.schema_templates (id, name, schema_type, template, description, category, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: seo_competitors; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.seo_competitors (id, domain, name, authority_score, backlinks_count, organic_keywords, organic_traffic, is_active, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: seo_metadata; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.seo_metadata (id, resource_type, resource_id, meta_title, meta_description, meta_keywords, canonical_url, og_title, og_description, og_image, schema_markup, noindex, h1_tag, created_at, updated_at, entity_type, entity_id) FROM stdin;
\.


--
-- Data for Name: site_audits; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.site_audits (id, url, status, audit_type, score, total_issues, critical_issues, warning_issues, report_data, started_at, completed_at, created_at) FROM stdin;
\.


--
-- Data for Name: system_config; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.system_config (id, key, value, value_type, description, is_public, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tenant_invoices; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.tenant_invoices (id, tenant_id, subscription_id, amount, status, paid_at, due_at, created_at) FROM stdin;
\.


--
-- Data for Name: tenant_plans; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.tenant_plans (id, name, code, price_monthly, price_yearly, max_users, max_sites, max_products, max_ai_quota, features, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tenant_subscriptions; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.tenant_subscriptions (id, tenant_id, plan_id, billing_cycle, amount, status, started_at, ended_at, created_at) FROM stdin;
\.


--
-- Data for Name: tenants; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.tenants (id, name, contact_name, contact_email, contact_phone, domain, plan_id, status, trial_ends_at, subscribed_at, expires_at, ai_quota_used, storage_used, settings, is_active, created_at, updated_at, custom_domains) FROM stdin;
\.


--
-- Data for Name: translation_records; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.translation_records (id, task_id, source_text, translated_text, source_lang, target_lang, status, rating, created_at) FROM stdin;
\.


--
-- Data for Name: translation_tasks; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.translation_tasks (id, name, source_lang, target_lang, total_items, completed_items, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_tenants; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.user_tenants (id, user_id, tenant_id, role, is_active, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: youding_admin
--

COPY public.users (id, username, email, hashed_password, display_name, role, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Name: building_material_specs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: youding_admin
--

SELECT pg_catalog.setval('public.building_material_specs_id_seq', 1, false);


--
-- Name: keyword_ranking_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: youding_admin
--

SELECT pg_catalog.setval('public.keyword_ranking_history_id_seq', 1, false);


--
-- Name: keyword_rankings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: youding_admin
--

SELECT pg_catalog.setval('public.keyword_rankings_id_seq', 1, false);


--
-- Name: merchant_im_routing_id_seq; Type: SEQUENCE SET; Schema: public; Owner: youding_admin
--

SELECT pg_catalog.setval('public.merchant_im_routing_id_seq', 1, false);


--
-- Name: seo_competitors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: youding_admin
--

SELECT pg_catalog.setval('public.seo_competitors_id_seq', 1, false);


--
-- Name: ab_test_conversions ab_test_conversions_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_conversions
    ADD CONSTRAINT ab_test_conversions_pkey PRIMARY KEY (id);


--
-- Name: ab_test_events ab_test_events_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_pkey PRIMARY KEY (id);


--
-- Name: ab_test_variants ab_test_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_pkey PRIMARY KEY (id);


--
-- Name: ab_tests ab_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_pkey PRIMARY KEY (id);


--
-- Name: ad_law_keywords ad_law_keywords_keyword_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ad_law_keywords
    ADD CONSTRAINT ad_law_keywords_keyword_key UNIQUE (keyword);


--
-- Name: ad_law_keywords ad_law_keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ad_law_keywords
    ADD CONSTRAINT ad_law_keywords_pkey PRIMARY KEY (id);


--
-- Name: ai_model_configs ai_model_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_model_configs
    ADD CONSTRAINT ai_model_configs_pkey PRIMARY KEY (id);


--
-- Name: ai_model_providers ai_model_providers_name_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_model_providers
    ADD CONSTRAINT ai_model_providers_name_key UNIQUE (name);


--
-- Name: ai_model_providers ai_model_providers_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_model_providers
    ADD CONSTRAINT ai_model_providers_pkey PRIMARY KEY (id);


--
-- Name: ai_optimization_logs ai_optimization_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_optimization_logs
    ADD CONSTRAINT ai_optimization_logs_pkey PRIMARY KEY (id);


--
-- Name: ai_recommendations ai_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_recommendations
    ADD CONSTRAINT ai_recommendations_pkey PRIMARY KEY (id);


--
-- Name: ai_usage_logs ai_usage_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_usage_logs
    ADD CONSTRAINT ai_usage_logs_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: building_material_specs building_material_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.building_material_specs
    ADD CONSTRAINT building_material_specs_pkey PRIMARY KEY (id);


--
-- Name: case_images case_images_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.case_images
    ADD CONSTRAINT case_images_pkey PRIMARY KEY (id);


--
-- Name: case_studies case_studies_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.case_studies
    ADD CONSTRAINT case_studies_pkey PRIMARY KEY (id);


--
-- Name: case_studies case_studies_slug_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.case_studies
    ADD CONSTRAINT case_studies_slug_key UNIQUE (slug);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: compliance_rules compliance_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.compliance_rules
    ADD CONSTRAINT compliance_rules_pkey PRIMARY KEY (id);


--
-- Name: compliance_scan_results compliance_scan_results_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.compliance_scan_results
    ADD CONSTRAINT compliance_scan_results_pkey PRIMARY KEY (id);


--
-- Name: compliance_violations compliance_violations_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.compliance_violations
    ADD CONSTRAINT compliance_violations_pkey PRIMARY KEY (id);


--
-- Name: content_pages content_pages_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.content_pages
    ADD CONSTRAINT content_pages_pkey PRIMARY KEY (id);


--
-- Name: content_versions content_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.content_versions
    ADD CONSTRAINT content_versions_pkey PRIMARY KEY (id);


--
-- Name: eeat_article_authors eeat_article_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_article_authors
    ADD CONSTRAINT eeat_article_authors_pkey PRIMARY KEY (id);


--
-- Name: eeat_author_certifications eeat_author_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_author_certifications
    ADD CONSTRAINT eeat_author_certifications_pkey PRIMARY KEY (id);


--
-- Name: eeat_authors eeat_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_authors
    ADD CONSTRAINT eeat_authors_pkey PRIMARY KEY (id);


--
-- Name: eeat_scores eeat_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_scores
    ADD CONSTRAINT eeat_scores_pkey PRIMARY KEY (id);


--
-- Name: eeat_trust_signals eeat_trust_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_trust_signals
    ADD CONSTRAINT eeat_trust_signals_pkey PRIMARY KEY (id);


--
-- Name: glossary_terms glossary_terms_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.glossary_terms
    ADD CONSTRAINT glossary_terms_pkey PRIMARY KEY (id);


--
-- Name: inquiries inquiries_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.inquiries
    ADD CONSTRAINT inquiries_pkey PRIMARY KEY (id);


--
-- Name: international_crawl_logs international_crawl_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.international_crawl_logs
    ADD CONSTRAINT international_crawl_logs_pkey PRIMARY KEY (id);


--
-- Name: international_inquiries international_inquiries_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.international_inquiries
    ADD CONSTRAINT international_inquiries_pkey PRIMARY KEY (id);


--
-- Name: international_target_sites international_target_sites_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.international_target_sites
    ADD CONSTRAINT international_target_sites_pkey PRIMARY KEY (id);


--
-- Name: keyword_ranking_history keyword_ranking_history_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keyword_ranking_history
    ADD CONSTRAINT keyword_ranking_history_pkey PRIMARY KEY (id);


--
-- Name: keyword_rankings keyword_rankings_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keyword_rankings
    ADD CONSTRAINT keyword_rankings_pkey PRIMARY KEY (id);


--
-- Name: keywords keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keywords
    ADD CONSTRAINT keywords_pkey PRIMARY KEY (id);


--
-- Name: llms_config llms_config_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.llms_config
    ADD CONSTRAINT llms_config_pkey PRIMARY KEY (id);


--
-- Name: merchant_im_routing merchant_im_routing_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.merchant_im_routing
    ADD CONSTRAINT merchant_im_routing_pkey PRIMARY KEY (id);


--
-- Name: merchant_profiles merchant_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.merchant_profiles
    ADD CONSTRAINT merchant_profiles_pkey PRIMARY KEY (id);


--
-- Name: merchant_profiles merchant_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.merchant_profiles
    ADD CONSTRAINT merchant_profiles_user_id_key UNIQUE (user_id);


--
-- Name: news_articles news_articles_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_pkey PRIMARY KEY (id);


--
-- Name: news_articles news_articles_slug_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.news_articles
    ADD CONSTRAINT news_articles_slug_key UNIQUE (slug);


--
-- Name: news_categories news_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.news_categories
    ADD CONSTRAINT news_categories_pkey PRIMARY KEY (id);


--
-- Name: news_categories news_categories_slug_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.news_categories
    ADD CONSTRAINT news_categories_slug_key UNIQUE (slug);


--
-- Name: operation_logs operation_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.operation_logs
    ADD CONSTRAINT operation_logs_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_order_number_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_order_number_key UNIQUE (order_number);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payment_channels payment_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.payment_channels
    ADD CONSTRAINT payment_channels_pkey PRIMARY KEY (id);


--
-- Name: payment_orders payment_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.payment_orders
    ADD CONSTRAINT payment_orders_pkey PRIMARY KEY (id);


--
-- Name: product_categories product_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_pkey PRIMARY KEY (id);


--
-- Name: product_categories product_categories_slug_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_slug_key UNIQUE (slug);


--
-- Name: product_documents product_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_documents
    ADD CONSTRAINT product_documents_pkey PRIMARY KEY (id);


--
-- Name: product_images product_images_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_images
    ADD CONSTRAINT product_images_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: quotes quotes_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.quotes
    ADD CONSTRAINT quotes_pkey PRIMARY KEY (id);


--
-- Name: schema_markups schema_markups_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.schema_markups
    ADD CONSTRAINT schema_markups_pkey PRIMARY KEY (id);


--
-- Name: schema_templates schema_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.schema_templates
    ADD CONSTRAINT schema_templates_pkey PRIMARY KEY (id);


--
-- Name: seo_competitors seo_competitors_domain_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.seo_competitors
    ADD CONSTRAINT seo_competitors_domain_key UNIQUE (domain);


--
-- Name: seo_competitors seo_competitors_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.seo_competitors
    ADD CONSTRAINT seo_competitors_pkey PRIMARY KEY (id);


--
-- Name: seo_metadata seo_metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.seo_metadata
    ADD CONSTRAINT seo_metadata_pkey PRIMARY KEY (id);


--
-- Name: site_audits site_audits_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.site_audits
    ADD CONSTRAINT site_audits_pkey PRIMARY KEY (id);


--
-- Name: system_config system_config_key_key; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_key_key UNIQUE (key);


--
-- Name: system_config system_config_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.system_config
    ADD CONSTRAINT system_config_pkey PRIMARY KEY (id);


--
-- Name: tenant_invoices tenant_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_invoices
    ADD CONSTRAINT tenant_invoices_pkey PRIMARY KEY (id);


--
-- Name: tenant_plans tenant_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_plans
    ADD CONSTRAINT tenant_plans_pkey PRIMARY KEY (id);


--
-- Name: tenant_subscriptions tenant_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_subscriptions
    ADD CONSTRAINT tenant_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: translation_records translation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.translation_records
    ADD CONSTRAINT translation_records_pkey PRIMARY KEY (id);


--
-- Name: translation_tasks translation_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.translation_tasks
    ADD CONSTRAINT translation_tasks_pkey PRIMARY KEY (id);


--
-- Name: user_tenants user_tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.user_tenants
    ADD CONSTRAINT user_tenants_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_ai_recommendations_product_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_ai_recommendations_product_id ON public.ai_recommendations USING btree (product_id);


--
-- Name: idx_ai_recommendations_user_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_ai_recommendations_user_id ON public.ai_recommendations USING btree (user_id);


--
-- Name: idx_cases_status_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_cases_status_active ON public.case_studies USING btree (status, is_active);


--
-- Name: idx_chat_messages_session_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_chat_messages_session_id ON public.chat_messages USING btree (session_id);


--
-- Name: idx_chat_sessions_user_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_chat_sessions_user_id ON public.chat_sessions USING btree (user_id);


--
-- Name: idx_content_pages_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_content_pages_slug ON public.content_pages USING btree (slug);


--
-- Name: idx_content_pages_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_content_pages_status ON public.content_pages USING btree (status);


--
-- Name: idx_current_position; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_current_position ON public.keyword_rankings USING btree (current_position);


--
-- Name: idx_domain; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_domain ON public.seo_competitors USING btree (domain);


--
-- Name: idx_history_checked_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_history_checked_at ON public.keyword_ranking_history USING btree (checked_at);


--
-- Name: idx_history_keyword_date; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_history_keyword_date ON public.keyword_ranking_history USING btree (keyword, checked_at);


--
-- Name: idx_inquiries_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_inquiries_status ON public.inquiries USING btree (status);


--
-- Name: idx_inquiries_status_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_inquiries_status_active ON public.inquiries USING btree (status, is_active);


--
-- Name: idx_keyword_search_engine; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_keyword_search_engine ON public.keyword_rankings USING btree (keyword, search_engine);


--
-- Name: idx_merchant_country; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_merchant_country ON public.merchant_im_routing USING btree (merchant_id, country_code);


--
-- Name: idx_merchant_profiles_user_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_merchant_profiles_user_id ON public.merchant_profiles USING btree (user_id);


--
-- Name: idx_merchant_profiles_verified; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_merchant_profiles_verified ON public.merchant_profiles USING btree (verified);


--
-- Name: idx_news_category_published; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_news_category_published ON public.news_articles USING btree (category, is_published);


--
-- Name: idx_order_items_order_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_order_items_order_id ON public.order_items USING btree (order_id);


--
-- Name: idx_orders_buyer_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_orders_buyer_id ON public.orders USING btree (buyer_id);


--
-- Name: idx_orders_merchant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_orders_merchant_id ON public.orders USING btree (merchant_id);


--
-- Name: idx_orders_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_orders_status ON public.orders USING btree (status);


--
-- Name: idx_pages_type_status_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_pages_type_status_active ON public.content_pages USING btree (page_type, status, is_active);


--
-- Name: idx_product_categories_parent_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_product_categories_parent_id ON public.product_categories USING btree (parent_id);


--
-- Name: idx_product_categories_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_product_categories_slug ON public.product_categories USING btree (slug);


--
-- Name: idx_product_images_product_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_product_images_product_id ON public.product_images USING btree (product_id);


--
-- Name: idx_product_spec; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_product_spec ON public.building_material_specs USING btree (product_id, spec_key);


--
-- Name: idx_quotes_inquiry_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_quotes_inquiry_id ON public.quotes USING btree (inquiry_id);


--
-- Name: idx_quotes_merchant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_quotes_merchant_id ON public.quotes USING btree (merchant_id);


--
-- Name: idx_seo_metadata_entity; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_seo_metadata_entity ON public.seo_metadata USING btree (entity_type, entity_id);


--
-- Name: idx_system_config_key; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX idx_system_config_key ON public.system_config USING btree (key);


--
-- Name: ix_ab_test_conversions_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_conversions_created_at ON public.ab_test_conversions USING btree (created_at);


--
-- Name: ix_ab_test_conversions_experiment_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_conversions_experiment_id ON public.ab_test_conversions USING btree (experiment_id);


--
-- Name: ix_ab_test_conversions_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_conversions_id ON public.ab_test_conversions USING btree (id);


--
-- Name: ix_ab_test_conversions_session_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_conversions_session_id ON public.ab_test_conversions USING btree (session_id);


--
-- Name: ix_ab_test_events_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_events_created_at ON public.ab_test_events USING btree (created_at);


--
-- Name: ix_ab_test_events_event_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_events_event_type ON public.ab_test_events USING btree (event_type);


--
-- Name: ix_ab_test_events_experiment_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_events_experiment_id ON public.ab_test_events USING btree (experiment_id);


--
-- Name: ix_ab_test_events_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_events_id ON public.ab_test_events USING btree (id);


--
-- Name: ix_ab_test_events_session_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_events_session_id ON public.ab_test_events USING btree (session_id);


--
-- Name: ix_ab_test_variants_experiment_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_variants_experiment_id ON public.ab_test_variants USING btree (experiment_id);


--
-- Name: ix_ab_test_variants_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_test_variants_id ON public.ab_test_variants USING btree (id);


--
-- Name: ix_ab_tests_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_tests_created_at ON public.ab_tests USING btree (created_at);


--
-- Name: ix_ab_tests_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_tests_id ON public.ab_tests USING btree (id);


--
-- Name: ix_ab_tests_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ab_tests_status ON public.ab_tests USING btree (status);


--
-- Name: ix_ad_law_keywords_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ad_law_keywords_id ON public.ad_law_keywords USING btree (id);


--
-- Name: ix_ai_model_configs_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_configs_is_active ON public.ai_model_configs USING btree (is_active);


--
-- Name: ix_ai_model_configs_is_default; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_configs_is_default ON public.ai_model_configs USING btree (is_default);


--
-- Name: ix_ai_model_configs_model_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_configs_model_type ON public.ai_model_configs USING btree (model_type);


--
-- Name: ix_ai_model_configs_provider_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_configs_provider_id ON public.ai_model_configs USING btree (provider_id);


--
-- Name: ix_ai_model_providers_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_providers_is_active ON public.ai_model_providers USING btree (is_active);


--
-- Name: ix_ai_model_providers_is_default; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_providers_is_default ON public.ai_model_providers USING btree (is_default);


--
-- Name: ix_ai_model_providers_provider_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_model_providers_provider_type ON public.ai_model_providers USING btree (provider_type);


--
-- Name: ix_ai_usage_logs_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_usage_logs_created_at ON public.ai_usage_logs USING btree (created_at);


--
-- Name: ix_ai_usage_logs_model_name; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_usage_logs_model_name ON public.ai_usage_logs USING btree (model_name);


--
-- Name: ix_ai_usage_logs_provider_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_usage_logs_provider_id ON public.ai_usage_logs USING btree (provider_id);


--
-- Name: ix_ai_usage_logs_task_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_ai_usage_logs_task_type ON public.ai_usage_logs USING btree (task_type);


--
-- Name: ix_case_images_case_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_case_images_case_id ON public.case_images USING btree (case_id);


--
-- Name: ix_case_studies_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_case_studies_created_at ON public.case_studies USING btree (created_at);


--
-- Name: ix_case_studies_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_case_studies_is_active ON public.case_studies USING btree (is_active);


--
-- Name: ix_case_studies_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_case_studies_slug ON public.case_studies USING btree (slug);


--
-- Name: ix_case_studies_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_case_studies_status ON public.case_studies USING btree (status);


--
-- Name: ix_categories_name; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_categories_name ON public.categories USING btree (name);


--
-- Name: ix_categories_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_categories_slug ON public.categories USING btree (slug);


--
-- Name: ix_compliance_rules_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_rules_id ON public.compliance_rules USING btree (id);


--
-- Name: ix_compliance_rules_rule_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_rules_rule_type ON public.compliance_rules USING btree (rule_type);


--
-- Name: ix_compliance_scan_results_content_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_scan_results_content_id ON public.compliance_scan_results USING btree (content_id);


--
-- Name: ix_compliance_scan_results_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_scan_results_id ON public.compliance_scan_results USING btree (id);


--
-- Name: ix_compliance_violations_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_violations_id ON public.compliance_violations USING btree (id);


--
-- Name: ix_compliance_violations_rule_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_violations_rule_id ON public.compliance_violations USING btree (rule_id);


--
-- Name: ix_compliance_violations_scan_result_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_compliance_violations_scan_result_id ON public.compliance_violations USING btree (scan_result_id);


--
-- Name: ix_content_pages_author_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_pages_author_id ON public.content_pages USING btree (author_id);


--
-- Name: ix_content_pages_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_pages_created_at ON public.content_pages USING btree (created_at);


--
-- Name: ix_content_pages_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_pages_is_active ON public.content_pages USING btree (is_active);


--
-- Name: ix_content_pages_page_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_pages_page_type ON public.content_pages USING btree (page_type);


--
-- Name: ix_content_pages_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_content_pages_slug ON public.content_pages USING btree (slug);


--
-- Name: ix_content_pages_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_pages_status ON public.content_pages USING btree (status);


--
-- Name: ix_content_versions_page_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_versions_page_id ON public.content_versions USING btree (page_id);


--
-- Name: ix_content_versions_version_number; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_content_versions_version_number ON public.content_versions USING btree (version_number);


--
-- Name: ix_eeat_article_authors_article_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_article_authors_article_id ON public.eeat_article_authors USING btree (article_id);


--
-- Name: ix_eeat_article_authors_author_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_article_authors_author_id ON public.eeat_article_authors USING btree (author_id);


--
-- Name: ix_eeat_article_authors_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_article_authors_id ON public.eeat_article_authors USING btree (id);


--
-- Name: ix_eeat_author_certifications_author_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_author_certifications_author_id ON public.eeat_author_certifications USING btree (author_id);


--
-- Name: ix_eeat_author_certifications_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_author_certifications_id ON public.eeat_author_certifications USING btree (id);


--
-- Name: ix_eeat_authors_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_authors_id ON public.eeat_authors USING btree (id);


--
-- Name: ix_eeat_authors_is_verified; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_authors_is_verified ON public.eeat_authors USING btree (is_verified);


--
-- Name: ix_eeat_authors_name; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_authors_name ON public.eeat_authors USING btree (name);


--
-- Name: ix_eeat_scores_content_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_scores_content_id ON public.eeat_scores USING btree (content_id);


--
-- Name: ix_eeat_scores_content_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_scores_content_type ON public.eeat_scores USING btree (content_type);


--
-- Name: ix_eeat_scores_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_scores_id ON public.eeat_scores USING btree (id);


--
-- Name: ix_eeat_trust_signals_content_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_trust_signals_content_id ON public.eeat_trust_signals USING btree (content_id);


--
-- Name: ix_eeat_trust_signals_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_trust_signals_id ON public.eeat_trust_signals USING btree (id);


--
-- Name: ix_eeat_trust_signals_signal_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_eeat_trust_signals_signal_type ON public.eeat_trust_signals USING btree (signal_type);


--
-- Name: ix_glossary_terms_am; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_am ON public.glossary_terms USING btree (am);


--
-- Name: ix_glossary_terms_ar; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ar ON public.glossary_terms USING btree (ar);


--
-- Name: ix_glossary_terms_bn; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_bn ON public.glossary_terms USING btree (bn);


--
-- Name: ix_glossary_terms_category; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_category ON public.glossary_terms USING btree (category);


--
-- Name: ix_glossary_terms_cs; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_cs ON public.glossary_terms USING btree (cs);


--
-- Name: ix_glossary_terms_de; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_de ON public.glossary_terms USING btree (de);


--
-- Name: ix_glossary_terms_en; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_en ON public.glossary_terms USING btree (en);


--
-- Name: ix_glossary_terms_es; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_es ON public.glossary_terms USING btree (es);


--
-- Name: ix_glossary_terms_fa; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_fa ON public.glossary_terms USING btree (fa);


--
-- Name: ix_glossary_terms_fr; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_fr ON public.glossary_terms USING btree (fr);


--
-- Name: ix_glossary_terms_ha; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ha ON public.glossary_terms USING btree (ha);


--
-- Name: ix_glossary_terms_he; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_he ON public.glossary_terms USING btree (he);


--
-- Name: ix_glossary_terms_hi; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_hi ON public.glossary_terms USING btree (hi);


--
-- Name: ix_glossary_terms_id_ba; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_id_ba ON public.glossary_terms USING btree (id_ba);


--
-- Name: ix_glossary_terms_it; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_it ON public.glossary_terms USING btree (it);


--
-- Name: ix_glossary_terms_ja; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ja ON public.glossary_terms USING btree (ja);


--
-- Name: ix_glossary_terms_km; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_km ON public.glossary_terms USING btree (km);


--
-- Name: ix_glossary_terms_ko; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ko ON public.glossary_terms USING btree (ko);


--
-- Name: ix_glossary_terms_ms; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ms ON public.glossary_terms USING btree (ms);


--
-- Name: ix_glossary_terms_my; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_my ON public.glossary_terms USING btree (my);


--
-- Name: ix_glossary_terms_nl; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_nl ON public.glossary_terms USING btree (nl);


--
-- Name: ix_glossary_terms_pl; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_pl ON public.glossary_terms USING btree (pl);


--
-- Name: ix_glossary_terms_pt; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_pt ON public.glossary_terms USING btree (pt);


--
-- Name: ix_glossary_terms_ru; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_ru ON public.glossary_terms USING btree (ru);


--
-- Name: ix_glossary_terms_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_status ON public.glossary_terms USING btree (status);


--
-- Name: ix_glossary_terms_sv; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_sv ON public.glossary_terms USING btree (sv);


--
-- Name: ix_glossary_terms_sw; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_sw ON public.glossary_terms USING btree (sw);


--
-- Name: ix_glossary_terms_th; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_th ON public.glossary_terms USING btree (th);


--
-- Name: ix_glossary_terms_tl; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_tl ON public.glossary_terms USING btree (tl);


--
-- Name: ix_glossary_terms_tr; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_tr ON public.glossary_terms USING btree (tr);


--
-- Name: ix_glossary_terms_uk; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_uk ON public.glossary_terms USING btree (uk);


--
-- Name: ix_glossary_terms_vi; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_vi ON public.glossary_terms USING btree (vi);


--
-- Name: ix_glossary_terms_zh; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_zh ON public.glossary_terms USING btree (zh);


--
-- Name: ix_glossary_terms_zu; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_glossary_terms_zu ON public.glossary_terms USING btree (zu);


--
-- Name: ix_inquiries_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_inquiries_created_at ON public.inquiries USING btree (created_at);


--
-- Name: ix_inquiries_email; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_inquiries_email ON public.inquiries USING btree (email);


--
-- Name: ix_inquiries_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_inquiries_is_active ON public.inquiries USING btree (is_active);


--
-- Name: ix_inquiries_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_inquiries_status ON public.inquiries USING btree (status);


--
-- Name: ix_inquiries_wechat; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_inquiries_wechat ON public.inquiries USING btree (wechat);


--
-- Name: ix_international_crawl_logs_site_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_crawl_logs_site_id ON public.international_crawl_logs USING btree (site_id);


--
-- Name: ix_international_crawl_logs_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_crawl_logs_status ON public.international_crawl_logs USING btree (status);


--
-- Name: ix_international_inquiries_customer_name; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_customer_name ON public.international_inquiries USING btree (customer_name);


--
-- Name: ix_international_inquiries_email; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_email ON public.international_inquiries USING btree (email);


--
-- Name: ix_international_inquiries_language; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_language ON public.international_inquiries USING btree (language);


--
-- Name: ix_international_inquiries_product_interest; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_product_interest ON public.international_inquiries USING btree (product_interest);


--
-- Name: ix_international_inquiries_region; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_region ON public.international_inquiries USING btree (region);


--
-- Name: ix_international_inquiries_source_site_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_source_site_id ON public.international_inquiries USING btree (source_site_id);


--
-- Name: ix_international_inquiries_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_inquiries_status ON public.international_inquiries USING btree (status);


--
-- Name: ix_international_target_sites_region; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_target_sites_region ON public.international_target_sites USING btree (region);


--
-- Name: ix_international_target_sites_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_international_target_sites_status ON public.international_target_sites USING btree (status);


--
-- Name: ix_keyword_rankings_keyword; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_keyword_rankings_keyword ON public.keyword_rankings USING btree (keyword);


--
-- Name: ix_keywords_keyword; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_keywords_keyword ON public.keywords USING btree (keyword);


--
-- Name: ix_keywords_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_keywords_slug ON public.keywords USING btree (slug);


--
-- Name: ix_news_articles_category; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_category ON public.news_articles USING btree (category);


--
-- Name: ix_news_articles_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_created_at ON public.news_articles USING btree (created_at);


--
-- Name: ix_news_articles_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_is_active ON public.news_articles USING btree (is_active);


--
-- Name: ix_news_articles_is_published; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_is_published ON public.news_articles USING btree (is_published);


--
-- Name: ix_news_articles_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_slug ON public.news_articles USING btree (slug);


--
-- Name: ix_news_articles_title; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_articles_title ON public.news_articles USING btree (title);


--
-- Name: ix_news_categories_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_news_categories_slug ON public.news_categories USING btree (slug);


--
-- Name: ix_operation_logs_user_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_operation_logs_user_id ON public.operation_logs USING btree (user_id);


--
-- Name: ix_payment_channels_channel; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_payment_channels_channel ON public.payment_channels USING btree (channel);


--
-- Name: ix_payment_orders_channel; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_payment_orders_channel ON public.payment_orders USING btree (channel);


--
-- Name: ix_payment_orders_order_no; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_payment_orders_order_no ON public.payment_orders USING btree (order_no);


--
-- Name: ix_payment_orders_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_payment_orders_status ON public.payment_orders USING btree (status);


--
-- Name: ix_payment_orders_subscription_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_payment_orders_subscription_id ON public.payment_orders USING btree (subscription_id);


--
-- Name: ix_payment_orders_tenant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_payment_orders_tenant_id ON public.payment_orders USING btree (tenant_id);


--
-- Name: ix_product_documents_product_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_product_documents_product_id ON public.product_documents USING btree (product_id);


--
-- Name: ix_products_category_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_products_category_id ON public.products USING btree (category_id);


--
-- Name: ix_products_created_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_products_created_at ON public.products USING btree (created_at);


--
-- Name: ix_products_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_products_is_active ON public.products USING btree (is_active);


--
-- Name: ix_products_slug; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_products_slug ON public.products USING btree (slug);


--
-- Name: ix_products_updated_at; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_products_updated_at ON public.products USING btree (updated_at);


--
-- Name: ix_schema_markups_schema_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_schema_markups_schema_type ON public.schema_markups USING btree (schema_type);


--
-- Name: ix_schema_templates_schema_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_schema_templates_schema_type ON public.schema_templates USING btree (schema_type);


--
-- Name: ix_seo_metadata_resource_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_seo_metadata_resource_id ON public.seo_metadata USING btree (resource_id);


--
-- Name: ix_seo_metadata_resource_type; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_seo_metadata_resource_type ON public.seo_metadata USING btree (resource_type);


--
-- Name: ix_tenant_invoices_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_invoices_status ON public.tenant_invoices USING btree (status);


--
-- Name: ix_tenant_invoices_subscription_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_invoices_subscription_id ON public.tenant_invoices USING btree (subscription_id);


--
-- Name: ix_tenant_invoices_tenant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_invoices_tenant_id ON public.tenant_invoices USING btree (tenant_id);


--
-- Name: ix_tenant_plans_code; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_tenant_plans_code ON public.tenant_plans USING btree (code);


--
-- Name: ix_tenant_subscriptions_plan_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_subscriptions_plan_id ON public.tenant_subscriptions USING btree (plan_id);


--
-- Name: ix_tenant_subscriptions_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_subscriptions_status ON public.tenant_subscriptions USING btree (status);


--
-- Name: ix_tenant_subscriptions_tenant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenant_subscriptions_tenant_id ON public.tenant_subscriptions USING btree (tenant_id);


--
-- Name: ix_tenants_domain; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_tenants_domain ON public.tenants USING btree (domain);


--
-- Name: ix_tenants_plan_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenants_plan_id ON public.tenants USING btree (plan_id);


--
-- Name: ix_tenants_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_tenants_status ON public.tenants USING btree (status);


--
-- Name: ix_translation_records_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_translation_records_status ON public.translation_records USING btree (status);


--
-- Name: ix_translation_records_task_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_translation_records_task_id ON public.translation_records USING btree (task_id);


--
-- Name: ix_translation_tasks_status; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_translation_tasks_status ON public.translation_tasks USING btree (status);


--
-- Name: ix_user_tenants_tenant_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_user_tenants_tenant_id ON public.user_tenants USING btree (tenant_id);


--
-- Name: ix_user_tenants_user_id; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_user_tenants_user_id ON public.user_tenants USING btree (user_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_is_active; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_users_is_active ON public.users USING btree (is_active);


--
-- Name: ix_users_role; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE INDEX ix_users_role ON public.users USING btree (role);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: youding_admin
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ab_test_conversions ab_test_conversions_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_conversions
    ADD CONSTRAINT ab_test_conversions_experiment_id_fkey FOREIGN KEY (experiment_id) REFERENCES public.ab_tests(id) ON DELETE CASCADE;


--
-- Name: ab_test_conversions ab_test_conversions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_conversions
    ADD CONSTRAINT ab_test_conversions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ab_test_events ab_test_events_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_experiment_id_fkey FOREIGN KEY (experiment_id) REFERENCES public.ab_tests(id) ON DELETE CASCADE;


--
-- Name: ab_test_events ab_test_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_events
    ADD CONSTRAINT ab_test_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ab_test_variants ab_test_variants_experiment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_test_variants
    ADD CONSTRAINT ab_test_variants_experiment_id_fkey FOREIGN KEY (experiment_id) REFERENCES public.ab_tests(id) ON DELETE CASCADE;


--
-- Name: ab_tests ab_tests_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ab_tests
    ADD CONSTRAINT ab_tests_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: ai_model_configs ai_model_configs_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_model_configs
    ADD CONSTRAINT ai_model_configs_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.ai_model_providers(id);


--
-- Name: ai_recommendations ai_recommendations_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_recommendations
    ADD CONSTRAINT ai_recommendations_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: ai_recommendations ai_recommendations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_recommendations
    ADD CONSTRAINT ai_recommendations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: ai_usage_logs ai_usage_logs_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.ai_usage_logs
    ADD CONSTRAINT ai_usage_logs_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.ai_model_providers(id);


--
-- Name: case_images case_images_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.case_images
    ADD CONSTRAINT case_images_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.case_studies(id) ON DELETE CASCADE;


--
-- Name: categories categories_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.categories(id);


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id);


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: content_versions content_versions_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.content_versions
    ADD CONSTRAINT content_versions_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.content_pages(id);


--
-- Name: eeat_article_authors eeat_article_authors_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_article_authors
    ADD CONSTRAINT eeat_article_authors_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.eeat_authors(id);


--
-- Name: eeat_author_certifications eeat_author_certifications_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.eeat_author_certifications
    ADD CONSTRAINT eeat_author_certifications_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.eeat_authors(id);


--
-- Name: international_crawl_logs international_crawl_logs_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.international_crawl_logs
    ADD CONSTRAINT international_crawl_logs_site_id_fkey FOREIGN KEY (site_id) REFERENCES public.international_target_sites(id);


--
-- Name: international_inquiries international_inquiries_source_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.international_inquiries
    ADD CONSTRAINT international_inquiries_source_site_id_fkey FOREIGN KEY (source_site_id) REFERENCES public.international_target_sites(id);


--
-- Name: keyword_ranking_history keyword_ranking_history_keyword_ranking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.keyword_ranking_history
    ADD CONSTRAINT keyword_ranking_history_keyword_ranking_id_fkey FOREIGN KEY (keyword_ranking_id) REFERENCES public.keyword_rankings(id) ON DELETE CASCADE;


--
-- Name: merchant_profiles merchant_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.merchant_profiles
    ADD CONSTRAINT merchant_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_buyer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_buyer_id_fkey FOREIGN KEY (buyer_id) REFERENCES public.users(id);


--
-- Name: orders orders_merchant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_merchant_id_fkey FOREIGN KEY (merchant_id) REFERENCES public.users(id);


--
-- Name: orders orders_quote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_quote_id_fkey FOREIGN KEY (quote_id) REFERENCES public.quotes(id);


--
-- Name: payment_orders payment_orders_subscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.payment_orders
    ADD CONSTRAINT payment_orders_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES public.tenant_subscriptions(id);


--
-- Name: payment_orders payment_orders_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.payment_orders
    ADD CONSTRAINT payment_orders_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: product_categories product_categories_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_categories
    ADD CONSTRAINT product_categories_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.product_categories(id);


--
-- Name: product_documents product_documents_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_documents
    ADD CONSTRAINT product_documents_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: product_images product_images_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.product_images
    ADD CONSTRAINT product_images_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: quotes quotes_inquiry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.quotes
    ADD CONSTRAINT quotes_inquiry_id_fkey FOREIGN KEY (inquiry_id) REFERENCES public.inquiries(id);


--
-- Name: quotes quotes_merchant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.quotes
    ADD CONSTRAINT quotes_merchant_id_fkey FOREIGN KEY (merchant_id) REFERENCES public.users(id);


--
-- Name: tenant_invoices tenant_invoices_subscription_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_invoices
    ADD CONSTRAINT tenant_invoices_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES public.tenant_subscriptions(id);


--
-- Name: tenant_invoices tenant_invoices_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_invoices
    ADD CONSTRAINT tenant_invoices_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: tenant_subscriptions tenant_subscriptions_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_subscriptions
    ADD CONSTRAINT tenant_subscriptions_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.tenant_plans(id);


--
-- Name: tenant_subscriptions tenant_subscriptions_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenant_subscriptions
    ADD CONSTRAINT tenant_subscriptions_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: tenants tenants_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.tenant_plans(id);


--
-- Name: translation_records translation_records_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.translation_records
    ADD CONSTRAINT translation_records_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.translation_tasks(id);


--
-- Name: user_tenants user_tenants_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.user_tenants
    ADD CONSTRAINT user_tenants_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: user_tenants user_tenants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: youding_admin
--

ALTER TABLE ONLY public.user_tenants
    ADD CONSTRAINT user_tenants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict vNZQ96NYleXMqRGDy0buUcdP2yeJABX2q8bsTckZwb6NVkoI74D66AWR8ftM9y0

