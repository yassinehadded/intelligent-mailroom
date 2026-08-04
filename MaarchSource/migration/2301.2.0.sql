-- *************************************************************************--
--                                                                          --
--                                                                          --
-- Model migration script - 2301.1.x to 2301.2.0                            --
--                                                                          --
--                                                                          --
-- *************************************************************************--

UPDATE users SET preferences = preferences - 'outlookPassword' WHERE preferences->>'outlookPassword' IS NOT NULL;

UPDATE actions
SET parameters = CASE
                     WHEN
                         (SELECT param_value_int FROM parameters where id = 'keepDestForRedirection') != '0' THEN
                         parameters::jsonb ||
                             '{"keepCopyForRedirection": false, "keepDestForRedirection:": true, "keepOtherRoleForRedirection": false}'
                     WHEN (SELECT param_value_int FROM parameters where id = 'keepDestForRedirection') = '0' THEN
                         parameters::jsonb ||
                             '{"keepCopyForRedirection": false, "keepDestForRedirection:": false, "keepOtherRoleForRedirection": false}' END
WHERE component = 'redirectAction';

DELETE FROM parameters WHERE id = 'keepDestForRedirection';

UPDATE parameters SET param_value_string = '2301.2.0' WHERE id = 'database_version';
