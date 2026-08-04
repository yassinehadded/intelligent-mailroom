-- *************************************************************************--
--                                                                          --
--                                                                          --
-- Model migration script - 2301.0.4 to 2301.1.0                            --
--                                                                          --
--                                                                          --
-- *************************************************************************--


CREATE TABLE IF NOT EXISTS indexing_models_entities
(
    id SERIAL NOT NULL,
    model_id INTEGER NOT NULL,
    entity_id character varying(32),
    keyword character varying(255),
    CONSTRAINT indexing_models_entities_pkey PRIMARY KEY (id)
)
WITH (OIDS=FALSE);

SELECT setval('indexing_models_entities_id_seq', (SELECT max(id)+1 FROM indexing_models_entities), false);

-- Set 'ALL_ENTITIES' keyword for every indexing model in indexing_models_entities
INSERT INTO indexing_models_entities (model_id, keyword) (SELECT models.id as model_id, 'ALL_ENTITIES' as keyword FROM indexing_models as models WHERE models.private = 'false');

UPDATE usergroups_services SET service_id = 'update_delete_attachments' WHERE service_id = 'manage_attachments';

UPDATE usergroups_services set service_id = 'update_resources' WHERE service_id = 'edit_resource';

-- New column for notifications
ALTER TABLE notifications DROP COLUMN IF EXISTS send_as_recap;
ALTER TABLE notifications ADD COLUMN send_as_recap BOOLEAN DEFAULT FALSE;


UPDATE parameters SET param_value_string = '2301.1.0' WHERE id = 'database_version';
