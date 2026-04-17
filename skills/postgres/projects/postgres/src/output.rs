use crate::db::QueryTable;
use anyhow::Result;
use comfy_table::{Cell, ContentArrangement, Table, presets::UTF8_FULL};
use serde::Serialize;

pub fn print_json<T: Serialize>(value: &T) -> Result<()> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

pub fn render_table(table: &QueryTable, title: Option<&str>) -> String {
    let mut output = String::new();
    if let Some(title) = title {
        output.push_str(title);
        output.push('\n');
    }

    let mut pretty = Table::new();
    pretty.load_preset(UTF8_FULL);
    pretty.set_content_arrangement(ContentArrangement::Dynamic);
    pretty.set_header(table.columns.iter().map(Cell::new));
    for row in &table.rows {
        pretty.add_row(
            row.iter()
                .map(|value| Cell::new(value.clone().unwrap_or_else(|| "(null)".to_string())))
                .collect::<Vec<_>>(),
        );
    }
    output.push_str(&pretty.to_string());
    output
}
