use anyhow::{Context, Result, bail};
use regex::Regex;
use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct DocsSearchResult {
    pub title: String,
    pub url: String,
    pub snippet: String,
}

pub async fn search(query: &str, limit: usize) -> Result<Vec<DocsSearchResult>> {
    if query.trim().is_empty() {
        bail!("Query must not be empty.");
    }
    if limit == 0 || limit > 20 {
        bail!("Limit must be between 1 and 20.");
    }

    let search_url = std::env::var("DB_DOCS_SEARCH_URL")
        .unwrap_or_else(|_| "https://www.postgresql.org/search/".to_string());
    let max_time = std::env::var("DB_DOCS_SEARCH_MAX_TIME")
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(30);

    let client = reqwest::Client::builder()
        .brotli(true)
        .gzip(true)
        .deflate(true)
        .timeout(std::time::Duration::from_secs(max_time))
        .build()
        .context("Failed to initialize HTTP client")?;

    let response = client
        .get(search_url)
        .query(&[("q", query), ("u", "/docs/current/")])
        .send()
        .await
        .context("Failed to query postgresql.org search endpoint")?
        .error_for_status()
        .context("PostgreSQL docs search request failed")?
        .text()
        .await
        .context("Failed to read PostgreSQL docs search response")?;

    parse_results(&response, limit)
}

fn parse_results(html: &str, limit: usize) -> Result<Vec<DocsSearchResult>> {
    let matcher = Regex::new(
        r#"\d+\.\s*<a href="(https://www\.postgresql\.org/docs/current/[^"]+)">(.+?)</a>.*?<div>(.*?)</div>"#,
    )
    .unwrap();
    let tag_regex = Regex::new(r"<[^>]+>").unwrap();
    let mut results = Vec::new();

    for capture in matcher.captures_iter(html) {
        let url = capture.get(1).map(|m| m.as_str()).unwrap_or_default();
        let title = clean_html(
            tag_regex
                .replace_all(capture.get(2).map(|m| m.as_str()).unwrap_or_default(), "")
                .as_ref(),
        );
        let snippet = clean_html(
            tag_regex
                .replace_all(capture.get(3).map(|m| m.as_str()).unwrap_or_default(), "")
                .as_ref(),
        );
        if title.is_empty()
            || results
                .iter()
                .any(|existing: &DocsSearchResult| existing.url == url)
        {
            continue;
        }
        results.push(DocsSearchResult {
            title,
            url: url.to_string(),
            snippet: if snippet.is_empty() {
                "(no snippet)".to_string()
            } else {
                snippet
            },
        });
        if results.len() >= limit {
            break;
        }
    }

    Ok(results)
}

fn clean_html(value: &str) -> String {
    let value = value
        .replace("&quot;", "\"")
        .replace("&amp;", "&")
        .replace("&#39;", "'");
    value.split_whitespace().collect::<Vec<_>>().join(" ")
}
