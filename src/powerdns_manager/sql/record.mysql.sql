-- Set engine to INNODB.
-- Alse see: https://docs.djangoproject.com/en/dev/ref/databases/#creating-your-tables
ALTER TABLE records ENGINE=INNODB;

-- Create index that is impossible to create otherwise
-- See: http://stackoverflow.com/questions/1578195/django-create-index-non-unique-multiple-column
CREATE INDEX nametype_index ON records(name,type);
