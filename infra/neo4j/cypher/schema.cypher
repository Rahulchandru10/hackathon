// Schema constraints and indexes for Project Sentinel Neo4j Graph Database

CREATE CONSTRAINT unique_entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT unique_person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT unique_company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT unique_article_url IF NOT EXISTS FOR (a:Article) REQUIRE a.url IS UNIQUE;
CREATE CONSTRAINT unique_regulator_id IF NOT EXISTS FOR (r:Regulator) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT unique_sanction_id IF NOT EXISTS FOR (s:Sanction) REQUIRE s.id IS UNIQUE;

CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX person_name_index IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX article_published_index IF NOT EXISTS FOR (a:Article) ON (a.published_date);
