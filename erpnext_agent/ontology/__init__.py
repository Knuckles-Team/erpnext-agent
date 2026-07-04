"""ERPNext / Frappe ontology contribution (CONCEPT:AU-KG.ontology.package-federation-migration).

Data-only subpackage: it carries ``erpnext.ttl`` (the ``owl:Ontology``
``http://knuckles.team/kg/erpnext`` module — DocTypes, customers, sales orders
and their ERP relationships) which the agent-utilities hub federates in via the
``agent_utilities.ontology_providers`` entry-point. It holds no business logic
and no heavy imports so the hub can resolve it cheaply.
"""
