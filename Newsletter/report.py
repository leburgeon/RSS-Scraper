import logging
from pathlib import Path

from metrics import (
    get_yesterday_date,
    get_dynamodb_table,
    get_mention_items_for_date,
    create_mentions_dataframe,
    compute_mention_volume,
    compute_sentiment_distribution,
    compute_share_of_voice,
)


logging.basicConfig(level=logging.INFO)


def get_top_3_rows(df, metric_column):
    """Return top 3 rows for a chosen metric column."""
    return df.sort_values(by=metric_column, ascending=False).head(3).copy()


def get_bottom_3_rows(df, metric_column):
    """Return bottom 3 rows for a chosen metric column, excluding zero values."""
    non_zero_df = df[df[metric_column] > 0].copy()
    return non_zero_df.sort_values(by=metric_column, ascending=True).head(3).copy()


def format_percentage_columns(df, percentage_columns):
    """Convert decimal percentage columns into readable percentage strings."""
    formatted_df = df.copy()

    for column in percentage_columns:
        if column in formatted_df.columns:
            formatted_df[column] = (
                formatted_df[column] * 100).round(2).astype(str) + "%"

    return formatted_df


def dataframe_to_html_table(df, title):
    """Convert a DataFrame into a styled HTML table."""
    if df.empty:
        return f"""
        <section class="card">
            <h2>{title}</h2>
            <p>No data available.</p>
        </section>
        """

    table_html = df.to_html(index=False, classes="report-table", border=0)

    return f"""
    <section class="card">
        <h2>{title}</h2>
        {table_html}
    </section>
    """


def build_html_report(
    report_date,
    top_mention_volume_df,
    bottom_mention_volume_df,
    top_sentiment_df,
    bottom_sentiment_df,
    top_share_of_voice_df,
    bottom_share_of_voice_df,
):
    """Build the full HTML report."""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Daily Media Report - {report_date}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 24px;
                background-color: #f7f7f7;
                color: #222;
            }}
            h1 {{
                margin-bottom: 8px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 24px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            }}
            .report-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}
            .report-table th,
            .report-table td {{
                border: 1px solid #dddddd;
                padding: 10px;
                text-align: left;
            }}
            .report-table th {{
                background-color: #f0f0f0;
            }}
        </style>
    </head>
    <body>
        <h1>Daily Media Report</h1>
        <p class="subtitle">Report date: {report_date}</p>

        <div class="grid">
            {dataframe_to_html_table(top_mention_volume_df, "Top 3 Companies by Mention Volume")}
            {dataframe_to_html_table(bottom_mention_volume_df, "Bottom 3 Companies by Mention Volume")}

            {dataframe_to_html_table(top_sentiment_df, "Top 3 Companies by Positive Sentiment")}
            {dataframe_to_html_table(bottom_sentiment_df, "Bottom 3 Companies by Positive Sentiment")}

            {dataframe_to_html_table(top_share_of_voice_df, "Top 3 Companies by Share of Voice")}
            {dataframe_to_html_table(bottom_share_of_voice_df, "Bottom 3 Companies by Share of Voice")}
        </div>
    </body>
    </html>
    """
    return html


def save_html_report(html_content, output_path):
    """Save the HTML report to a file."""
    Path(output_path).write_text(html_content, encoding="utf-8")
    logging.info("Saved HTML report to %s", output_path)


def generate_report_html(table_name, region_name):
    """Run the report pipeline and return the HTML string."""
    report_date = get_yesterday_date()
    logging.info("Generating HTML report for %s", report_date)

    table = get_dynamodb_table(table_name, region_name)
    items = get_mention_items_for_date(table, report_date)

    if not items:
        logging.info("No mention items found for yesterday")
        return f"""
        <html>
            <body>
                <h1>Daily Media Report</h1>
                <p>Report date: {report_date}</p>
                <p>No data available for this date.</p>
            </body>
        </html>
        """

    df = create_mentions_dataframe(items)

    mention_volume_df = compute_mention_volume(df)
    sentiment_distribution_df = compute_sentiment_distribution(df)
    share_of_voice_df = compute_share_of_voice(df)

    top_mention_volume_df = get_top_3_rows(
        mention_volume_df,
        "mention_volume"
    )
    bottom_mention_volume_df = get_bottom_3_rows(
        mention_volume_df,
        "mention_volume"
    )

    top_sentiment_df = get_top_3_rows(
        sentiment_distribution_df,
        "positive_pct"
    )
    bottom_sentiment_df = get_bottom_3_rows(
        sentiment_distribution_df,
        "positive_pct"
    )

    top_share_of_voice_df = get_top_3_rows(
        share_of_voice_df,
        "share_of_voice"
    )
    bottom_share_of_voice_df = get_bottom_3_rows(
        share_of_voice_df,
        "share_of_voice"
    )

    top_sentiment_df = format_percentage_columns(
        top_sentiment_df,
        ["positive_pct", "neutral_pct", "negative_pct"]
    )
    bottom_sentiment_df = format_percentage_columns(
        bottom_sentiment_df,
        ["positive_pct", "neutral_pct", "negative_pct"]
    )
    top_share_of_voice_df = format_percentage_columns(
        top_share_of_voice_df,
        ["share_of_voice"]
    )
    bottom_share_of_voice_df = format_percentage_columns(
        bottom_share_of_voice_df,
        ["share_of_voice"]
    )

    html_report = build_html_report(
        report_date=report_date,
        top_mention_volume_df=top_mention_volume_df,
        bottom_mention_volume_df=bottom_mention_volume_df,
        top_sentiment_df=top_sentiment_df,
        bottom_sentiment_df=bottom_sentiment_df,
        top_share_of_voice_df=top_share_of_voice_df,
        bottom_share_of_voice_df=bottom_share_of_voice_df,
    )

    return html_report


def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Returns the HTML report in the response body.
    """
    table_name = "c22_charlie_media_mvp"
    region_name = "eu-west-2"

    html_report = generate_report_html(table_name, region_name)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html"
        },
        "body": html_report
    }


def main():
    """Local entry point for testing."""
    table_name = "c22_charlie_media_mvp"
    region_name = "eu-west-2"

    html_report = generate_report_html(table_name, region_name)
    save_html_report(html_report, "daily_media_report.html")


if __name__ == "__main__":
    main()
