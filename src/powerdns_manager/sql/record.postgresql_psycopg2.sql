-- Create index that is impossible to create otherwise
-- See: http://stackoverflow.com/questions/1578195/django-create-index-non-unique-multiple-column
CREATE INDEX nametype_index ON records(name,type);
