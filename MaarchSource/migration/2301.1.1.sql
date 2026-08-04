-- *************************************************************************--
--                                                                          --
--                                                                          --
-- Model migration script - 2301.1.0 to 2301.1.1                            --
--                                                                          --
--                                                                          --
-- *************************************************************************--

DELETE FROM parameters WHERE id = 'useSectorsForAddresses';

UPDATE parameters SET param_value_string = '2301.1.1' WHERE id = 'database_version';
