digraph ETL_DAG {
  // Nodes
  extract_sales [label="Extract Sales DB"];
  extract_inventory [label="Extract Inventory CSV"];
  extract_customer [label="Extract Customer API"];
  enrich_sales [label="Enrich Sales with Customer Data"];
  join_inventory [label="Join Inventory with Sales"];
  generate_summary [label="Generate Daily Summary"];
  load_warehouse [label="Load Summary into Warehouse"];
  purge_stale [label="Purge Stale Data (90 days)"];

  // Edges (dependencies)
  extract_sales -> enrich_sales;
  extract_customer -> enrich_sales;
  enrich_sales -> join_inventory;
  extract_inventory -> join_inventory;
  join_inventory -> generate_summary;
  extract_sales -> generate_summary; // sales data also needed for summary
  extract_inventory -> generate_summary;
  extract_customer -> generate_summary;
  generate_summary -> load_warehouse;
  load_warehouse -> purge_stale;
}

# Result IR
{ "files": [{ "filename": "dag.txt", "satisfies": ["R1","R2","R3","R4","R5","R6","R7","R8"], "evidence": { "path": "execution://body", "section": null, "observed": "digraph ETL_DAG" } }], "reconciliation": [ { "requirement": "R1", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Extract Sales DB" } }, { "requirement": "R2", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Extract Inventory CSV" } }, { "requirement": "R3", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Extract Customer API" } }, { "requirement": "R4", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Enrich Sales with Customer Data" } }, { "requirement": "R5", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Join Inventory with Sales" } }, { "requirement": "R6", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Generate Daily Summary" } }, { "requirement": "R7", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Load Summary into Warehouse" } }, { "requirement": "R8", "status": "satisfied", "evidence": { "path": "execution://body", "section": null, "observed": "Purge Stale Data" } } ], "open_defects": [] }
