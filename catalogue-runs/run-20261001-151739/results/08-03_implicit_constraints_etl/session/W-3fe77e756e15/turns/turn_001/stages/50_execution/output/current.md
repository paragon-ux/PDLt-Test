digraph ETL_DAG {
    // Nodes
    extract_sales [label="Extract Sales (PostgreSQL)"];
    extract_inventory [label="Extract Inventory (CSV)"];
    extract_customer [label="Extract Customer API (rate‑limited)" ];
    enrich_sales [label="Enrich Sales with Customer Data"];
    join_inventory_sales [label="Join Inventory with Sales (stock‑out risk)"];
    generate_summary [label="Generate Daily Summary"];
    load_warehouse [label="Load Summary into Data Warehouse"];
    purge_stale [label="Purge Stale Data (>90 days)"];

    // Edges (dependencies)
    extract_sales -> enrich_sales;
    extract_customer -> enrich_sales;
    enrich_sales -> join_inventory_sales;
    extract_inventory -> join_inventory_sales;
    join_inventory_sales -> generate_summary;
    extract_sales -> generate_summary; // summary needs raw sales data
    extract_inventory -> generate_summary; // summary needs raw inventory data
    extract_customer -> generate_summary; // summary needs raw customer data
    generate_summary -> load_warehouse;
    load_warehouse -> purge_stale;
}
